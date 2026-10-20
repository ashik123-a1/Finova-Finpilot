"""
SME Finance Copilot - CRM, Customer Directory & Messaging Routes.
Provides full CRUD, dynamic RFM segmentation, receivables aging, polite due reminders,
payment reconciliation, and discount campaign workflows with multi-tenant shop isolation.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, desc, asc

from src.database.connection import get_db
from src.database.models import (
    User,
    Business,
    Shop,
    Customer,
    Sale,
    SaleItem,
    Receivable,
    Payment,
    CashMovement,
    CustomerCommunication,
    DiscountCampaign,
    Product,
    AuditLog,
    Notification,
)
from src.api.dependencies import get_current_user, verify_shop_access_dependency
from src.api.routes.notifications import create_persistent_notification
from src.ai.segmentation import CustomerSegmentationEngine
from src.crm.messaging import (
    MessagingDispatcher,
    build_reminder_template,
    build_campaign_template,
    clean_phone_number,
)

logger = logging.getLogger("sme.crm.routes")

router = APIRouter(prefix="/crm", tags=["Customers & CRM"])


# --- Pydantic Request & Response Schemas ---

class CustomerCreateRequest(BaseModel):
    shop_id: int
    name: str = Field(..., min_length=2, max_length=255)
    phone: str = Field(..., min_length=5, max_length=50)
    email: Optional[str] = None
    address: Optional[str] = None
    credit_limit_minor: int = 0
    opening_balance_minor: int = 0
    whatsapp_number: Optional[str] = None
    telegram_handle: Optional[str] = None
    customer_type: str = "retail"
    messaging_consent: bool = True
    notes: Optional[str] = None


class CustomerUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    credit_limit_minor: Optional[int] = None
    whatsapp_number: Optional[str] = None
    telegram_handle: Optional[str] = None
    customer_type: Optional[str] = None
    messaging_consent: Optional[bool] = None
    notes: Optional[str] = None


class ReminderDraftRequest(BaseModel):
    shop_id: int
    customer_id: int
    template_type: str = "en_friendly"  # 'en_friendly', 'bn_friendly', 'en_formal', 'custom'
    custom_text: Optional[str] = None


class ReminderSendRequest(BaseModel):
    shop_id: int
    customer_id: int
    channel: str = "whatsapp"  # 'whatsapp', 'sms', 'telegram'
    message_body: str
    override_consent: bool = False


class PaymentRecordRequest(BaseModel):
    shop_id: int
    customer_id: int
    amount_minor: int = Field(..., gt=0)
    payment_method: str = "cash"  # 'cash', 'bank_transfer', 'mfs_bkash', 'mfs_nagad', 'card'
    payment_date: Optional[datetime] = None
    notes: Optional[str] = None
    receivable_id: Optional[int] = None


class CampaignCreateRequest(BaseModel):
    shop_id: int
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    target_segment: str = "VIP"  # 'VIP', 'Regular', 'At-Risk', 'Dormant', 'all', 'single'
    target_customer_id: Optional[int] = None
    discount_type: str = "percentage"  # 'percentage', 'fixed'
    discount_value: float = Field(..., gt=0)
    min_purchase_amount_minor: int = 0
    eligible_category: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    channel: str = "whatsapp"
    message_template: str
    confirm_low_margin: bool = False


# --- Helper Functions ---

def _format_currency(amount_minor: int, currency: str = "BDT") -> str:
    symbol = "৳" if currency.upper() in ("BDT", "TAKA") else "$" if currency.upper() == "USD" else currency
    return f"{symbol} {amount_minor / 100:,.2f}"


def _verify_user_shop_access(db: Session, user: User, shop_id: int) -> Shop:
    """Verifies that the user has legitimate access to the given shop."""
    verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)
    shop = db.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail=f"Shop #{shop_id} not found.")
    return shop


# --- CRM Endpoints ---

@router.get("/customers")
def list_customers(
    shop_id: int = Query(...),
    search: Optional[str] = Query(None),
    segment: Optional[str] = Query(None),
    due_filter: Optional[str] = Query("all"),  # 'all', 'has_due', 'settled'
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lists shop customers with real-time RFM loyalty metrics,
    overdue aging buckets, and outstanding balance summaries.
    """
    shop = _verify_user_shop_access(db, user, shop_id)
    business = db.get(Business, shop.business_id)
    currency = business.currency if business else "BDT"

    query = db.query(Customer).filter(Customer.shop_id == shop_id)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Customer.name.ilike(s),
                Customer.phone.ilike(s),
                Customer.email.ilike(s),
                Customer.whatsapp_number.ilike(s),
            )
        )

    all_shop_customers = query.all()

    now = datetime.now(timezone.utc)
    results = []
    vip_count = 0
    regular_count = 0
    at_risk_count = 0
    dormant_count = 0
    occasional_count = 0
    total_receivables_minor = 0
    customers_with_due_count = 0

    for cust in all_shop_customers:
        # 1. Fetch sales telemetry for dynamic RFM
        sales = (
            db.query(Sale)
            .filter(Sale.customer_id == cust.id, Sale.shop_id == shop_id)
            .order_by(desc(Sale.sale_date))
            .all()
        )
        order_count = len(sales)
        total_spent = sum(s.total_amount_minor for s in sales)
        avg_basket = int(total_spent / order_count) if order_count > 0 else 0

        if sales and sales[0].sale_date:
            last_date = sales[0].sale_date
            if last_date.tzinfo is None:
                last_date = last_date.replace(tzinfo=timezone.utc)
            days_since_purchase = max(0, (now - last_date).days)
        elif cust.created_at:
            c_date = cust.created_at
            if c_date.tzinfo is None:
                c_date = c_date.replace(tzinfo=timezone.utc)
            days_since_purchase = max(0, (now - c_date).days)
        else:
            days_since_purchase = 999

        rfm = CustomerSegmentationEngine.segment_customer_rfm(
            days_since_last_purchase=days_since_purchase,
            total_orders_count=order_count,
            total_spent_minor=total_spent,
            avg_basket_minor=avg_basket,
        )
        dyn_segment = rfm["segment"]

        # 2. Fetch outstanding receivables & aging buckets
        open_recs = (
            db.query(Receivable)
            .filter(
                Receivable.customer_id == cust.id,
                Receivable.shop_id == shop_id,
                Receivable.status.in_(["open", "partial", "overdue"]),
                Receivable.outstanding_amount_minor > 0,
            )
            .all()
        )

        cust_due_minor = sum(r.outstanding_amount_minor for r in open_recs)
        if cust_due_minor > 0:
            customers_with_due_count += 1
            total_receivables_minor += cust_due_minor

        # Compute aging for this customer
        aging_0_30 = 0
        aging_31_60 = 0
        aging_61_90 = 0
        aging_90_plus = 0

        for r in open_recs:
            r_due = r.due_date
            if r_due:
                if r_due.tzinfo is None:
                    r_due = r_due.replace(tzinfo=timezone.utc)
                overdue_days = (now - r_due).days
            else:
                overdue_days = 0

            if overdue_days <= 30:
                aging_0_30 += r.outstanding_amount_minor
            elif overdue_days <= 60:
                aging_31_60 += r.outstanding_amount_minor
            elif overdue_days <= 90:
                aging_61_90 += r.outstanding_amount_minor
            else:
                aging_90_plus += r.outstanding_amount_minor

        # Keep cached segment and balance synced if necessary
        if cust.segment != dyn_segment or cust.balance_minor != cust_due_minor:
            cust.segment = dyn_segment
            cust.balance_minor = cust_due_minor
            db.commit()

        # Count segments
        if dyn_segment == "VIP":
            vip_count += 1
        elif dyn_segment == "Regular":
            regular_count += 1
        elif dyn_segment == "At-Risk":
            at_risk_count += 1
        elif dyn_segment == "Dormant":
            dormant_count += 1
        else:
            occasional_count += 1

        # Check due filter
        if due_filter == "has_due" and cust_due_minor <= 0:
            continue
        elif due_filter == "settled" and cust_due_minor > 0:
            continue

        # Check segment filter
        if segment and segment.lower() != "all" and dyn_segment.lower() != segment.lower():
            continue

        results.append(
            {
                "id": cust.id,
                "business_id": cust.business_id,
                "shop_id": cust.shop_id,
                "name": cust.name,
                "phone": cust.phone,
                "email": cust.email,
                "address": cust.address,
                "customer_type": cust.customer_type or "retail",
                "credit_limit_minor": cust.credit_limit_minor or 0,
                "credit_limit_formatted": _format_currency(cust.credit_limit_minor or 0, currency),
                "balance_minor": cust_due_minor,
                "balance_formatted": _format_currency(cust_due_minor, currency),
                "segment": dyn_segment,
                "rfm_strategy": rfm["recommended_strategy"],
                "action_priority": rfm["action_priority"],
                "whatsapp_number": cust.whatsapp_number,
                "telegram_handle": cust.telegram_handle,
                "messaging_consent": bool(cust.messaging_consent),
                "notes": cust.notes,
                "orders_count": order_count,
                "total_spent_minor": total_spent,
                "total_spent_formatted": _format_currency(total_spent, currency),
                "days_since_last_purchase": days_since_purchase,
                "aging_buckets": {
                    "0_30": aging_0_30,
                    "31_60": aging_31_60,
                    "61_90": aging_61_90,
                    "90_plus": aging_90_plus,
                },
                "open_invoices_count": len(open_recs),
            }
        )

    # Sort: highest outstanding due first, then VIPs
    results.sort(key=lambda x: (x["balance_minor"], x["total_spent_minor"]), reverse=True)
    paginated_results = results[offset : offset + limit]

    return {
        "status": "success",
        "total_count": len(results),
        "currency": currency,
        "summary": {
            "total_customers": len(all_shop_customers),
            "vip_count": vip_count,
            "regular_count": regular_count,
            "at_risk_count": at_risk_count,
            "dormant_count": dormant_count,
            "occasional_count": occasional_count,
            "total_receivables_minor": total_receivables_minor,
            "total_receivables_formatted": _format_currency(total_receivables_minor, currency),
            "customers_with_due_count": customers_with_due_count,
        },
        "customers": paginated_results,
    }


@router.post("/customers", status_code=status.HTTP_201_CREATED)
def create_customer(
    req: CustomerCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Creates a new customer profile with uniqueness validations,
    opening receivables setup, audit logging, and notifications.
    """
    shop = _verify_user_shop_access(db, user, req.shop_id)

    # Check duplicate phone in same shop
    clean_phone = clean_phone_number(req.phone)
    existing = (
        db.query(Customer)
        .filter(Customer.shop_id == req.shop_id, Customer.phone == req.phone)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Customer with phone number '{req.phone}' already exists in Shop #{req.shop_id}.",
        )

    customer = Customer(
        business_id=shop.business_id,
        shop_id=shop.id,
        name=req.name.strip(),
        phone=req.phone.strip(),
        email=req.email.strip() if req.email else None,
        address=req.address.strip() if req.address else None,
        credit_limit_minor=max(0, req.credit_limit_minor),
        balance_minor=max(0, req.opening_balance_minor),
        segment="Occasional",
        whatsapp_number=req.whatsapp_number.strip() if req.whatsapp_number else clean_phone,
        telegram_handle=req.telegram_handle.strip() if req.telegram_handle else None,
        customer_type=req.customer_type or "retail",
        opening_balance_minor=max(0, req.opening_balance_minor),
        messaging_consent=req.messaging_consent,
        notes=req.notes.strip() if req.notes else None,
        is_synthetic=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    # If opening balance exists, generate initial Sale and Receivable for ledger reconciliation
    if req.opening_balance_minor > 0:
        now_dt = datetime.now(timezone.utc)
        sale = Sale(
            business_id=shop.business_id,
            shop_id=shop.id,
            invoice_number=f"INV-OPEN-{customer.id}-{int(now_dt.timestamp())}",
            customer_id=customer.id,
            sale_date=now_dt,
            subtotal_minor=req.opening_balance_minor,
            discount_minor=0,
            tax_minor=0,
            total_amount_minor=req.opening_balance_minor,
            paid_amount_minor=0,
            payment_status="unpaid",
            payment_method="credit",
            notes="Opening balance upon customer onboarding",
            is_synthetic=False,
            created_at=now_dt,
            updated_at=now_dt,
        )
        db.add(sale)
        db.commit()
        db.refresh(sale)

        rec = Receivable(
            business_id=shop.business_id,
            shop_id=shop.id,
            sale_id=sale.id,
            customer_id=customer.id,
            due_date=now_dt + timedelta(days=30),
            total_amount_minor=req.opening_balance_minor,
            outstanding_amount_minor=req.opening_balance_minor,
            status="open",
            is_synthetic=False,
            created_at=now_dt,
            updated_at=now_dt,
        )
        db.add(rec)
        db.commit()

    # Audit Log
    audit = AuditLog(
        business_id=shop.business_id,
        shop_id=shop.id,
        user_id=user.id,
        action="CUSTOMER_CREATED",
        entity_type="Customer",
        entity_id=customer.id,
        new_values_json=json.dumps({"name": customer.name, "phone": customer.phone, "credit_limit": customer.credit_limit_minor}),
        created_at=datetime.now(timezone.utc),
    )
    db.add(audit)
    db.commit()

    # Persistent Notification
    create_persistent_notification(
        db=db,
        user_id=user.id,
        business_id=shop.business_id,
        shop_id=shop.id,
        title="New Customer Registered",
        message=f"Customer '{customer.name}' ({customer.phone}) registered under Shop #{shop.id}.",
        notification_type="crm_customer",
        severity="info",
        action_url=f"/customers?shop_id={shop.id}",
    )

    return {
        "status": "success",
        "message": f"Customer '{customer.name}' created successfully.",
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "segment": customer.segment,
            "balance_minor": customer.balance_minor,
            "credit_limit_minor": customer.credit_limit_minor,
        },
    }


@router.get("/customers/{customer_id}")
def get_customer_details(
    customer_id: int,
    shop_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns full customer profile, complete transaction ledger,
    open receivables, and communication history.
    """
    shop = _verify_user_shop_access(db, user, shop_id)
    business = db.get(Business, shop.business_id)
    currency = business.currency if business else "BDT"

    customer = db.query(Customer).filter_by(id=customer_id, shop_id=shop_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found in this shop.")

    # Sales history
    sales = (
        db.query(Sale)
        .filter_by(customer_id=customer.id, shop_id=shop_id)
        .order_by(desc(Sale.sale_date))
        .limit(50)
        .all()
    )

    sales_data = [
        {
            "id": s.id,
            "invoice_number": s.invoice_number,
            "sale_date": s.sale_date.isoformat() if s.sale_date else None,
            "total_amount_minor": s.total_amount_minor,
            "total_amount_formatted": _format_currency(s.total_amount_minor, currency),
            "paid_amount_minor": s.paid_amount_minor,
            "payment_status": s.payment_status,
            "payment_method": s.payment_method,
        }
        for s in sales
    ]

    # Receivables
    recs = (
        db.query(Receivable)
        .filter_by(customer_id=customer.id, shop_id=shop_id)
        .order_by(desc(Receivable.created_at))
        .all()
    )

    now = datetime.now(timezone.utc)
    recs_data = []
    total_due_minor = 0

    for r in recs:
        if r.status in ("open", "partial", "overdue"):
            total_due_minor += r.outstanding_amount_minor

        overdue_days = 0
        if r.due_date:
            due_dt = r.due_date if r.due_date.tzinfo else r.due_date.replace(tzinfo=timezone.utc)
            if now > due_dt:
                overdue_days = (now - due_dt).days

        recs_data.append(
            {
                "id": r.id,
                "sale_id": r.sale_id,
                "due_date": r.due_date.isoformat() if r.due_date else None,
                "overdue_days": overdue_days,
                "total_amount_minor": r.total_amount_minor,
                "outstanding_amount_minor": r.outstanding_amount_minor,
                "outstanding_formatted": _format_currency(r.outstanding_amount_minor, currency),
                "status": r.status,
            }
        )

    # Communications history
    comms = (
        db.query(CustomerCommunication)
        .filter_by(customer_id=customer.id, shop_id=shop_id)
        .order_by(desc(CustomerCommunication.created_at))
        .limit(30)
        .all()
    )

    comms_data = [
        {
            "id": c.id,
            "channel": c.channel,
            "recipient_contact": c.recipient_contact,
            "message_body": c.message_body,
            "message_type": c.message_type,
            "status": c.status,
            "provider_message_id": c.provider_message_id,
            "error_message": c.error_message,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in comms
    ]

    return {
        "status": "success",
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "email": customer.email,
            "address": customer.address,
            "customer_type": customer.customer_type or "retail",
            "credit_limit_minor": customer.credit_limit_minor or 0,
            "credit_limit_formatted": _format_currency(customer.credit_limit_minor or 0, currency),
            "balance_minor": total_due_minor,
            "balance_formatted": _format_currency(total_due_minor, currency),
            "segment": customer.segment,
            "whatsapp_number": customer.whatsapp_number,
            "telegram_handle": customer.telegram_handle,
            "messaging_consent": bool(customer.messaging_consent),
            "notes": customer.notes,
            "created_at": customer.created_at.isoformat() if customer.created_at else None,
        },
        "sales": sales_data,
        "receivables": recs_data,
        "communications": comms_data,
    }


@router.put("/customers/{customer_id}")
def update_customer(
    customer_id: int,
    req: CustomerUpdateRequest,
    shop_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Updates customer profile details and audits the modifications."""
    shop = _verify_user_shop_access(db, user, shop_id)

    customer = db.query(Customer).filter_by(id=customer_id, shop_id=shop_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found in this shop.")

    old_vals = {"name": customer.name, "phone": customer.phone, "credit_limit": customer.credit_limit_minor}

    if req.name is not None:
        customer.name = req.name.strip()
    if req.phone is not None:
        clean_phone = clean_phone_number(req.phone)
        customer.phone = req.phone.strip()
        if not customer.whatsapp_number:
            customer.whatsapp_number = clean_phone
    if req.email is not None:
        customer.email = req.email.strip() if req.email else None
    if req.address is not None:
        customer.address = req.address.strip() if req.address else None
    if req.credit_limit_minor is not None:
        customer.credit_limit_minor = max(0, req.credit_limit_minor)
    if req.whatsapp_number is not None:
        customer.whatsapp_number = req.whatsapp_number.strip() if req.whatsapp_number else None
    if req.telegram_handle is not None:
        customer.telegram_handle = req.telegram_handle.strip() if req.telegram_handle else None
    if req.customer_type is not None:
        customer.customer_type = req.customer_type
    if req.messaging_consent is not None:
        customer.messaging_consent = req.messaging_consent
    if req.notes is not None:
        customer.notes = req.notes.strip() if req.notes else None

    customer.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(customer)

    # Audit Log
    audit = AuditLog(
        business_id=shop.business_id,
        shop_id=shop.id,
        user_id=user.id,
        action="CUSTOMER_UPDATED",
        entity_type="Customer",
        entity_id=customer.id,
        old_values_json=json.dumps(old_vals),
        new_values_json=json.dumps({"name": customer.name, "phone": customer.phone, "credit_limit": customer.credit_limit_minor}),
        created_at=datetime.now(timezone.utc),
    )
    db.add(audit)
    db.commit()

    return {
        "status": "success",
        "message": f"Customer '{customer.name}' updated successfully.",
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "messaging_consent": customer.messaging_consent,
        },
    }


# --- Due Reminders & Messaging Endpoints ---

@router.post("/reminders/draft")
def draft_payment_reminder(
    req: ReminderDraftRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generates culturally tuned, polite payment reminder drafts based on active invoices,
    outstanding balances, and selected tone/language.
    """
    shop = _verify_user_shop_access(db, user, req.shop_id)
    business = db.get(Business, shop.business_id)
    currency = business.currency if business else "BDT"

    customer = db.query(Customer).filter_by(id=req.customer_id, shop_id=req.shop_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")

    open_recs = (
        db.query(Receivable)
        .filter(
            Receivable.customer_id == customer.id,
            Receivable.shop_id == req.shop_id,
            Receivable.status.in_(["open", "partial", "overdue"]),
            Receivable.outstanding_amount_minor > 0,
        )
        .all()
    )

    total_due = sum(r.outstanding_amount_minor for r in open_recs)
    due_formatted = _format_currency(total_due, currency)

    # Invoices list
    sale_ids = [r.sale_id for r in open_recs if r.sale_id]
    invoices = []
    if sale_ids:
        sales = db.query(Sale).filter(Sale.id.in_(sale_ids)).all()
        invoices = [s.invoice_number for s in sales if s.invoice_number]

    body = build_reminder_template(
        template_type=req.template_type,
        customer_name=customer.name,
        shop_name=shop.name,
        total_due_formatted=due_formatted,
        currency=currency,
        invoice_list=invoices,
        custom_text=req.custom_text,
    )

    return {
        "status": "success",
        "customer_id": customer.id,
        "customer_name": customer.name,
        "total_due_minor": total_due,
        "total_due_formatted": due_formatted,
        "phone": customer.phone,
        "whatsapp_number": customer.whatsapp_number or customer.phone,
        "telegram_handle": customer.telegram_handle,
        "messaging_consent": bool(customer.messaging_consent),
        "draft_body": body,
    }


@router.post("/reminders/send")
def send_payment_reminder(
    req: ReminderSendRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Dispatches reminder via Cloud API or prepares manual handoff links (wa.me, sms:, t.me).
    Enforces customer consent validation and persists communication history.
    """
    shop = _verify_user_shop_access(db, user, req.shop_id)

    result = MessagingDispatcher.send_or_prepare_message(
        db=db,
        shop_id=req.shop_id,
        business_id=shop.business_id,
        customer_id=req.customer_id,
        channel=req.channel,
        message_body=req.message_body,
        message_type="payment_reminder",
        sent_by_user_id=user.id,
        bypass_consent_check=req.override_consent,
    )

    if not result.get("success") and result.get("consent_required"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Customer has not granted messaging consent."),
        )

    # Persistent notification of reminder activity
    cust = db.get(Customer, req.customer_id)
    create_persistent_notification(
        db=db,
        user_id=user.id,
        business_id=shop.business_id,
        shop_id=shop.id,
        title="Payment Reminder Generated",
        message=f"Reminder for {cust.name if cust else 'Customer'} prepared via {req.channel.upper()} ({result.get('status')}).",
        notification_type="crm_reminder",
        severity="info",
        action_url=f"/customers?shop_id={shop.id}",
    )

    return result


# --- Payment Settlement Endpoints ---

@router.post("/payments/record", status_code=status.HTTP_201_CREATED)
def record_customer_payment(
    req: PaymentRecordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Records customer debt settlement, reconciles receivables FIFO or targeted,
    updates customer balances, and commits payment and cash movements to ledger.
    """
    shop = _verify_user_shop_access(db, user, req.shop_id)
    business = db.get(Business, shop.business_id)
    currency = business.currency if business else "BDT"

    customer = db.query(Customer).filter_by(id=req.customer_id, shop_id=req.shop_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found in this shop.")

    remaining_payment = req.amount_minor

    # Fetch receivables to settle
    if req.receivable_id:
        target_recs = db.query(Receivable).filter_by(id=req.receivable_id, customer_id=customer.id).all()
    else:
        # FIFO by due_date
        target_recs = (
            db.query(Receivable)
            .filter(
                Receivable.customer_id == customer.id,
                Receivable.shop_id == req.shop_id,
                Receivable.status.in_(["open", "partial", "overdue"]),
                Receivable.outstanding_amount_minor > 0,
            )
            .order_by(asc(Receivable.due_date))
            .all()
        )

    settled_invoices = []
    for rec in target_recs:
        if remaining_payment <= 0:
            break
        alloc = min(remaining_payment, rec.outstanding_amount_minor)
        rec.outstanding_amount_minor -= alloc
        if rec.outstanding_amount_minor == 0:
            rec.status = "paid"
        else:
            rec.status = "partial"
        rec.updated_at = datetime.now(timezone.utc)
        remaining_payment -= alloc
        settled_invoices.append({"receivable_id": rec.id, "amount_settled_minor": alloc, "remaining_due": rec.outstanding_amount_minor})

    # Update customer balance
    new_balance = max(0, (customer.balance_minor or 0) - req.amount_minor)
    customer.balance_minor = new_balance
    customer.updated_at = datetime.now(timezone.utc)

    # Record Payment
    payment_time = req.payment_date or datetime.now(timezone.utc)
    payment = Payment(
        business_id=shop.business_id,
        shop_id=shop.id,
        payment_type="customer_inflow",
        reference_type="customer",
        reference_id=customer.id,
        payment_date=payment_time,
        amount_minor=req.amount_minor,
        payment_method=req.payment_method,
        notes=req.notes or f"Customer payment settlement for {customer.name}",
        document_id=None,
        created_by=user.id,
        is_synthetic=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    # Record CashMovement
    cash_mov = CashMovement(
        business_id=shop.business_id,
        shop_id=shop.id,
        movement_type="inflow",
        source_type="customer_payment",
        source_id=payment.id,
        amount_minor=req.amount_minor,
        running_balance_minor=0,
        movement_date=payment_time,
        notes=f"Settlement payment received from {customer.name} via {req.payment_method}",
        is_synthetic=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(cash_mov)
    db.commit()

    # Audit Log
    audit = AuditLog(
        business_id=shop.business_id,
        shop_id=shop.id,
        user_id=user.id,
        action="CUSTOMER_PAYMENT_RECORDED",
        entity_type="Payment",
        entity_id=payment.id,
        new_values_json=json.dumps({"customer_id": customer.id, "amount": req.amount_minor, "method": req.payment_method}),
        created_at=datetime.now(timezone.utc),
    )
    db.add(audit)
    db.commit()

    # Persistent Notification
    create_persistent_notification(
        db=db,
        user_id=user.id,
        business_id=shop.business_id,
        shop_id=shop.id,
        title="Customer Payment Received",
        message=f"Received {_format_currency(req.amount_minor, currency)} from {customer.name} via {req.payment_method.replace('_', ' ').title()}.",
        notification_type="payment_inflow",
        severity="success",
        action_url=f"/customers?shop_id={shop.id}",
    )

    return {
        "status": "success",
        "message": f"Payment of {_format_currency(req.amount_minor, currency)} successfully posted.",
        "payment_id": payment.id,
        "customer_id": customer.id,
        "new_balance_minor": new_balance,
        "new_balance_formatted": _format_currency(new_balance, currency),
        "settled_allocations": settled_invoices,
    }


# --- VIP & Discount Campaigns Endpoints ---

@router.get("/campaigns")
def list_discount_campaigns(
    shop_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists discount campaigns for the shop."""
    shop = _verify_user_shop_access(db, user, shop_id)
    campaigns = (
        db.query(DiscountCampaign)
        .filter_by(shop_id=shop_id)
        .order_by(desc(DiscountCampaign.created_at))
        .all()
    )

    return {
        "status": "success",
        "campaigns": [
            {
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "target_segment": c.target_segment,
                "discount_type": c.discount_type,
                "discount_value": c.discount_value,
                "min_purchase_amount_minor": c.min_purchase_amount_minor,
                "eligible_category": c.eligible_category,
                "channel": c.channel,
                "status": c.status,
                "recipient_count": c.recipient_count,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in campaigns
        ],
    }


@router.post("/campaigns", status_code=status.HTTP_201_CREATED)
def create_discount_campaign(
    req: CampaignCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Creates a VIP/loyalty discount campaign with strict margin guardrail protection
    preventing unintended negative gross profit contribution.
    """
    shop = _verify_user_shop_access(db, user, req.shop_id)

    # 1. Margin Guardrail Validation
    prod_query = db.query(Product).filter(Product.shop_id == req.shop_id, Product.is_active == True)
    if req.eligible_category:
        prod_query = prod_query.filter(Product.category == req.eligible_category)
    products = prod_query.all()

    if products:
        margins = []
        for p in products:
            if p.selling_price_minor > 0:
                m = (p.selling_price_minor - p.cost_price_minor) / p.selling_price_minor
                margins.append(m)
        avg_catalog_margin = (sum(margins) / len(margins)) * 100 if margins else 25.0
    else:
        avg_catalog_margin = 25.0  # default baseline

    # If percentage discount exceeds average margin, enforce margin warning / confirmation
    if req.discount_type == "percentage" and req.discount_value > avg_catalog_margin and not req.confirm_low_margin:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Margin Guardrail Alert",
                "message": (
                    f"The requested discount ({req.discount_value:.1f}%) exceeds the average gross margin "
                    f"({avg_catalog_margin:.1f}%) for this catalog/category. "
                    f"This promotion could produce negative unit margins. "
                    f"Set confirm_low_margin=True to authorize this clearance or loss-leader offer."
                ),
                "catalog_margin_percent": round(avg_catalog_margin, 1),
                "requested_discount_percent": req.discount_value,
            },
        )

    # 2. Audience count estimation
    cust_query = db.query(Customer).filter(Customer.shop_id == req.shop_id)
    if req.target_segment and req.target_segment.lower() not in ("all", "all_customers"):
        cust_query = cust_query.filter(Customer.segment.ilike(req.target_segment))
    if req.target_customer_id:
        cust_query = cust_query.filter(Customer.id == req.target_customer_id)

    eligible_recipients = cust_query.all()
    consented_count = sum(1 for c in eligible_recipients if c.messaging_consent)

    campaign = DiscountCampaign(
        business_id=shop.business_id,
        shop_id=shop.id,
        title=req.title.strip(),
        description=req.description.strip() if req.description else None,
        target_segment=req.target_segment,
        target_customer_id=req.target_customer_id,
        discount_type=req.discount_type,
        discount_value=req.discount_value,
        min_purchase_amount_minor=req.min_purchase_amount_minor,
        eligible_category=req.eligible_category,
        start_date=req.start_date or datetime.now(timezone.utc),
        end_date=req.end_date,
        channel=req.channel,
        message_template=req.message_template,
        status="active",
        recipient_count=consented_count,
        created_by_user_id=user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    # Audit Log
    audit = AuditLog(
        business_id=shop.business_id,
        shop_id=shop.id,
        user_id=user.id,
        action="DISCOUNT_CAMPAIGN_CREATED",
        entity_type="DiscountCampaign",
        entity_id=campaign.id,
        new_values_json=json.dumps({"title": campaign.title, "segment": campaign.target_segment, "discount": campaign.discount_value}),
        created_at=datetime.now(timezone.utc),
    )
    db.add(audit)
    db.commit()

    # Persistent Notification
    create_persistent_notification(
        db=db,
        user_id=user.id,
        business_id=shop.business_id,
        shop_id=shop.id,
        title="Discount Campaign Launched",
        message=f"Campaign '{campaign.title}' launched for {campaign.target_segment} segment ({consented_count} recipients).",
        notification_type="crm_campaign",
        severity="info",
        action_url=f"/customers?shop_id={shop.id}",
    )

    return {
        "status": "success",
        "message": f"Campaign '{campaign.title}' created.",
        "campaign_id": campaign.id,
        "eligible_customers_count": len(eligible_recipients),
        "consented_recipients_count": consented_count,
        "catalog_margin_percent": round(avg_catalog_margin, 1),
    }


@router.post("/campaigns/{campaign_id}/dispatch")
def dispatch_discount_campaign(
    campaign_id: int,
    shop_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Prepares and dispatches personalized campaign messages to eligible audience members,
    logging communications and tracking external handoffs.
    """
    shop = _verify_user_shop_access(db, user, shop_id)
    campaign = db.query(DiscountCampaign).filter_by(id=campaign_id, shop_id=shop_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")

    cust_query = db.query(Customer).filter(Customer.shop_id == shop_id, Customer.messaging_consent == True)
    if campaign.target_segment and campaign.target_segment.lower() not in ("all", "all_customers"):
        cust_query = cust_query.filter(Customer.segment.ilike(campaign.target_segment))
    if campaign.target_customer_id:
        cust_query = cust_query.filter(Customer.id == campaign.target_customer_id)

    recipients = cust_query.all()
    if not recipients:
        return {
            "status": "success",
            "message": "No eligible customers with messaging consent found for this campaign.",
            "dispatched_count": 0,
        }

    discount_str = f"{campaign.discount_value}% OFF" if campaign.discount_type == "percentage" else f"৳ {campaign.discount_value} OFF"
    expiry_str = campaign.end_date.strftime("%B %d, %Y") if campaign.end_date else "Limited time only"

    dispatched = []
    for cust in recipients:
        body = build_campaign_template(
            template_text=campaign.message_template,
            customer_name=cust.name,
            shop_name=shop.name,
            discount_text=discount_str,
            expiry_text=expiry_str,
        )
        res = MessagingDispatcher.send_or_prepare_message(
            db=db,
            shop_id=shop.id,
            business_id=shop.business_id,
            customer_id=cust.id,
            channel=campaign.channel,
            message_body=body,
            message_type="campaign_offer",
            sent_by_user_id=user.id,
            bypass_consent_check=True,
        )
        dispatched.append({"customer_id": cust.id, "customer_name": cust.name, "result": res})

    campaign.status = "dispatched"
    campaign.recipient_count = len(dispatched)
    campaign.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "status": "success",
        "message": f"Campaign successfully processed for {len(dispatched)} customers.",
        "campaign_id": campaign.id,
        "dispatched_count": len(dispatched),
        "dispatched": dispatched,
    }
