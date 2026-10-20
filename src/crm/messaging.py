"""
SME Finance Copilot - Multi-Channel CRM Messaging Service.
Handles polite due reminders, VIP promotions, and campaign notifications across
WhatsApp, SMS, and Telegram with strict distinction between automated API delivery
and external app handoffs (wa.me, sms:, t.me).
"""

from __future__ import annotations

import logging
import os
import re
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import requests
from sqlalchemy.orm import Session

from src.database.models import Customer, CustomerCommunication, Shop, Business

logger = logging.getLogger("sme.crm.messaging")


def clean_phone_number(raw_phone: Optional[str]) -> str:
    """Strips formatting, spaces, dashes, and normalizes phone numbers."""
    if not raw_phone:
        return ""
    cleaned = re.sub(r"[^\d+]", "", raw_phone.strip())
    # If starts with '01', assume Bangladesh domestic number and add '+88'
    if cleaned.startswith("01") and len(cleaned) == 11:
        cleaned = "+88" + cleaned
    elif cleaned.startswith("8801") and len(cleaned) == 13:
        cleaned = "+" + cleaned
    return cleaned


def clean_phone_for_wa(clean_phone: str) -> str:
    """Strips leading '+' for WhatsApp wa.me links."""
    return clean_phone.lstrip("+")


def build_reminder_template(
    template_type: str,
    customer_name: str,
    shop_name: str,
    total_due_formatted: str,
    currency: str = "BDT",
    invoice_list: Optional[List[str]] = None,
    custom_text: Optional[str] = None,
) -> str:
    """
    Builds culturally appropriate, polite, and explainable payment reminder messages.
    Supports English friendly, Bengali polite, and Formal business styles.
    """
    if template_type == "custom" and custom_text:
        return custom_text

    inv_details = ""
    if invoice_list and len(invoice_list) > 0:
        inv_str = ", ".join(invoice_list[:3])
        if len(invoice_list) > 3:
            inv_str += f" and {len(invoice_list) - 3} more"
        inv_details = f" (Invoice(s): {inv_str})"

    if template_type == "bn_friendly":
        return (
            f"শ্রদ্ধেয় {customer_name},\n\n"
            f"{shop_name}-এর পক্ষ থেকে আন্তরিক শুভেচ্ছা।\n"
            f"আপনার অ্যাকাউন্টে {total_due_formatted}-এর একটি বকেয়া ব্যালেন্স{inv_details} রয়েছে। "
            f"ব্যবসার হিসাব ও লেনদেন নিয়মিত রাখতে অনুগ্রহপূর্বক সুবিধাজনক সময়ে পরিশোধের ব্যবস্থা করলে বিশেষভাবে উপকৃত হব।\n\n"
            f"যে কোনো তথ্য বা সহযোগিতার জন্য আমাদের সাথে সরাসরি যোগাযোগ করুন। ধন্যবাদ ও শুভকামনা।"
        )
    elif template_type == "en_formal":
        return (
            f"Dear {customer_name},\n\n"
            f"This is an official statement from {shop_name}.\n"
            f"Our accounting ledger indicates an outstanding trade balance of {total_due_formatted}{inv_details}. "
            f"Kindly review your invoices and arrange settlement at your earliest convenience to maintain an uninterrupted credit facility.\n\n"
            f"For ledger statements or payment confirmation, please contact our accounts desk.\n"
            f"Sincerely,\nFinance Department, {shop_name}"
        )
    else:  # en_friendly (default)
        return (
            f"Dear {customer_name},\n\n"
            f"Warm greetings from {shop_name}!\n"
            f"This is a gentle courtesy reminder regarding your outstanding balance of {total_due_formatted}{inv_details}. "
            f"We appreciate your continued partnership and kindly request settlement when convenient.\n\n"
            f"Please reach out if you have questions or require updated payment details. Have a wonderful day!"
        )


def build_campaign_template(
    template_text: str,
    customer_name: str,
    shop_name: str,
    discount_text: str,
    expiry_text: Optional[str] = None,
) -> str:
    """Substitutes variables into a promotional campaign template."""
    body = template_text.replace("{name}", customer_name)
    body = body.replace("{customer_name}", customer_name)
    body = body.replace("{shop_name}", shop_name)
    body = body.replace("{discount}", discount_text)
    if expiry_text:
        body = body.replace("{expiry}", expiry_text)
    return body


class MessagingDispatcher:
    """
    Central dispatcher for customer communications with explicit delivery tracking.
    Never misrepresents a manual handoff URL as an automated delivery.
    """

    @classmethod
    def send_or_prepare_message(
        cls,
        db: Session,
        shop_id: int,
        business_id: int,
        customer_id: int,
        channel: str,  # 'whatsapp', 'sms', 'telegram'
        message_body: str,
        message_type: str = "payment_reminder",  # 'payment_reminder', 'campaign_offer', 'receipt'
        sent_by_user_id: Optional[int] = None,
        recipient_override: Optional[str] = None,
        bypass_consent_check: bool = False,
    ) -> Dict[str, Any]:
        """
        Dispatches or generates handoff links for the specified channel,
        validates customer consent, and records communication history in the database.
        """
        customer = db.query(Customer).filter_by(id=customer_id, shop_id=shop_id).first()
        if not customer:
            raise ValueError(f"Customer #{customer_id} not found in Shop #{shop_id}.")

        # Check messaging consent unless explicitly overridden
        if not bypass_consent_check and not customer.messaging_consent:
            return {
                "success": False,
                "error": "Customer has not granted messaging consent. Explicit consent required before dispatch.",
                "consent_required": True,
                "status": "consent_required",
            }

        target_phone = recipient_override or customer.whatsapp_number or customer.phone
        cleaned_phone = clean_phone_number(target_phone)

        # 1. WhatsApp Dispatch / Handoff
        if channel == "whatsapp":
            wa_token = os.getenv("WHATSAPP_API_TOKEN")
            wa_phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

            if wa_token and wa_phone_id and cleaned_phone:
                # Attempt live WhatsApp Cloud API
                try:
                    url = f"https://graph.facebook.com/v18.0/{wa_phone_id}/messages"
                    headers = {
                        "Authorization": f"Bearer {wa_token}",
                        "Content-Type": "application/json",
                    }
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": clean_phone_for_wa(cleaned_phone),
                        "type": "text",
                        "text": {"body": message_body},
                    }
                    resp = requests.post(url, json=payload, headers=headers, timeout=10)
                    if resp.status_code in (200, 201):
                        data = resp.json()
                        wamid = data.get("messages", [{}])[0].get("id", "LIVE_API_SENT")
                        comm = cls._record_comm(
                            db=db,
                            customer=customer,
                            channel="whatsapp",
                            recipient=cleaned_phone,
                            body=message_body,
                            m_type=message_type,
                            status="provider_accepted",
                            provider_id=wamid,
                            user_id=sent_by_user_id,
                        )
                        return {
                            "success": True,
                            "mode": "api_delivered",
                            "status": "provider_accepted",
                            "communication_id": comm.id,
                            "provider_message_id": wamid,
                            "recipient": cleaned_phone,
                            "handoff_url": None,
                            "message": "Message successfully dispatched via WhatsApp Cloud API.",
                        }
                    else:
                        logger.warning("WhatsApp API error: %s", resp.text)
                except Exception as e:
                    logger.error("Exception during WhatsApp API call: %s", e)

            # Fallback to direct wa.me handoff URL
            wa_number = clean_phone_for_wa(cleaned_phone)
            encoded_text = urllib.parse.quote(message_body)
            handoff_url = f"https://wa.me/{wa_number}?text={encoded_text}" if wa_number else None

            comm = cls._record_comm(
                db=db,
                customer=customer,
                channel="whatsapp",
                recipient=cleaned_phone or "NO_PHONE",
                body=message_body,
                m_type=message_type,
                status="awaiting_user_action",
                provider_id=None,
                user_id=sent_by_user_id,
            )

            return {
                "success": True,
                "mode": "manual_handoff",
                "status": "awaiting_user_action",
                "communication_id": comm.id,
                "recipient": cleaned_phone,
                "handoff_url": handoff_url,
                "message": (
                    "WhatsApp draft generated. Click the link to open WhatsApp Web or Desktop to review and send. "
                    "Notice: External action required; not marked as automatically delivered."
                ),
            }

        # 2. SMS Dispatch / Handoff
        elif channel == "sms":
            twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
            twilio_auth = os.getenv("TWILIO_AUTH_TOKEN")
            twilio_from = os.getenv("TWILIO_FROM_NUMBER")

            if twilio_sid and twilio_auth and twilio_from and cleaned_phone:
                try:
                    url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
                    resp = requests.post(
                        url,
                        data={"To": cleaned_phone, "From": twilio_from, "Body": message_body},
                        auth=(twilio_sid, twilio_auth),
                        timeout=10,
                    )
                    if resp.status_code in (200, 201):
                        data = resp.json()
                        sid = data.get("sid", "TWILIO_SENT")
                        comm = cls._record_comm(
                            db=db,
                            customer=customer,
                            channel="sms",
                            recipient=cleaned_phone,
                            body=message_body,
                            m_type=message_type,
                            status="provider_accepted",
                            provider_id=sid,
                            user_id=sent_by_user_id,
                        )
                        return {
                            "success": True,
                            "mode": "api_delivered",
                            "status": "provider_accepted",
                            "communication_id": comm.id,
                            "provider_message_id": sid,
                            "recipient": cleaned_phone,
                            "handoff_url": None,
                            "message": "SMS dispatched via Twilio gateway.",
                        }
                    else:
                        logger.warning("Twilio API error: %s", resp.text)
                except Exception as e:
                    logger.error("Exception during Twilio SMS call: %s", e)

            # Fallback to mobile SMS URI
            encoded_text = urllib.parse.quote(message_body)
            handoff_url = f"sms:{cleaned_phone}?body={encoded_text}" if cleaned_phone else None

            comm = cls._record_comm(
                db=db,
                customer=customer,
                channel="sms",
                recipient=cleaned_phone or "NO_PHONE",
                body=message_body,
                m_type=message_type,
                status="awaiting_user_action",
                provider_id=None,
                user_id=sent_by_user_id,
            )

            return {
                "success": True,
                "mode": "manual_handoff",
                "status": "awaiting_user_action",
                "communication_id": comm.id,
                "recipient": cleaned_phone,
                "handoff_url": handoff_url,
                "message": (
                    "SMS draft created. Use mobile messaging or your SMS gateway to dispatch. "
                    "Notice: External action required; not marked as automatically delivered."
                ),
            }

        # 3. Telegram Dispatch / Handoff
        elif channel == "telegram":
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            handle = customer.telegram_handle or ""
            target_chat = handle.lstrip("@")

            # Check if handle is numeric chat ID and token exists
            if bot_token and target_chat.isdigit():
                try:
                    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    resp = requests.post(
                        url,
                        json={"chat_id": int(target_chat), "text": message_body},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        mid = str(data.get("result", {}).get("message_id", "TELEGRAM_SENT"))
                        comm = cls._record_comm(
                            db=db,
                            customer=customer,
                            channel="telegram",
                            recipient=target_chat,
                            body=message_body,
                            m_type=message_type,
                            status="provider_accepted",
                            provider_id=mid,
                            user_id=sent_by_user_id,
                        )
                        return {
                            "success": True,
                            "mode": "api_delivered",
                            "status": "provider_accepted",
                            "communication_id": comm.id,
                            "provider_message_id": mid,
                            "recipient": target_chat,
                            "handoff_url": None,
                            "message": "Message dispatched via Telegram Bot API.",
                        }
                except Exception as e:
                    logger.error("Exception during Telegram API call: %s", e)

            # Fallback to Telegram web/desktop handoff
            clean_handle = handle.lstrip("@").strip()
            handoff_url = f"https://t.me/{clean_handle}" if clean_handle else None

            comm = cls._record_comm(
                db=db,
                customer=customer,
                channel="telegram",
                recipient=handle or "NO_HANDLE",
                body=message_body,
                m_type=message_type,
                status="awaiting_user_action",
                provider_id=None,
                user_id=sent_by_user_id,
            )

            return {
                "success": True,
                "mode": "manual_handoff",
                "status": "awaiting_user_action",
                "communication_id": comm.id,
                "recipient": handle,
                "handoff_url": handoff_url,
                "message": (
                    "Telegram draft prepared. Click link to open conversation in Telegram. "
                    "Notice: External action required; not marked as automatically delivered."
                ),
            }

        else:
            raise ValueError(f"Unsupported communication channel: '{channel}'")

    @classmethod
    def _record_comm(
        cls,
        db: Session,
        customer: Customer,
        channel: str,
        recipient: str,
        body: str,
        m_type: str,
        status: str,
        provider_id: Optional[str] = None,
        error_msg: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> CustomerCommunication:
        """Persists communication log record with timestamps and status."""
        comm = CustomerCommunication(
            business_id=customer.business_id,
            shop_id=customer.shop_id,
            customer_id=customer.id,
            channel=channel,
            recipient_contact=recipient,
            message_body=body,
            message_type=m_type,
            status=status,
            provider_message_id=provider_id,
            error_message=error_msg,
            sent_by_user_id=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(comm)
        db.commit()
        db.refresh(comm)
        return comm
