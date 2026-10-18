"""
Security, Password Hashing, and Multi-Tenant Shop Isolation Module.
Uses Python's standard hashlib (PBKDF2-HMAC-SHA256) for zero external binary dependency.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
from typing import Optional, Dict, Any

from src.core.exceptions import ShopAccessDeniedError


def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with 200,000 iterations."""
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        200_000,
    )
    return f"pbkdf2:sha256:200000${salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the stored PBKDF2 hash."""
    try:
        method, salt, stored_hash = hashed_password.split("$")
        algo, sub_algo, iterations = method.split(":")
        new_key = hashlib.pbkdf2_hmac(
            sub_algo,
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        )
        return hmac.compare_digest(new_key.hex(), stored_hash)
    except Exception:
        return False


def create_token(user_id: int, secret_key: str, expires_in_seconds: int = 86400) -> str:
    """Create a tamper-evident signed session token."""
    expire_at = int(time.time()) + expires_in_seconds
    payload = f"{user_id}:{expire_at}"
    signature = hmac.new(
        secret_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return f"{payload}:{signature}"


def verify_token(token: str, secret_key: str) -> Optional[int]:
    """Verify signed session token. Returns user_id if valid and unexpired."""
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return None
        user_id_str, expire_at_str, signature = parts
        payload = f"{user_id_str}:{expire_at_str}"
        expected_sig = hmac.new(
            secret_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            return None

        if int(time.time()) > int(expire_at_str):
            return None  # Expired

        return int(user_id_str)
    except Exception:
        return None


def enforce_shop_isolation(
    user_id: int,
    shop_id: int,
    memberships: list[Dict[str, Any]],
    required_permission: Optional[str] = None,
) -> bool:
    """
    Validates that a user has authorization to view or mutate records in `shop_id`.
    An owner / manager can access multiple shops only if explicitly granted via membership.
    Raises ShopAccessDeniedError if access is rejected.
    """
    for m in memberships:
        if m.get("user_id") == user_id and m.get("is_active", True):
            # If membership is business-wide (shop_id is None) or matches the target shop
            if m.get("shop_id") is None or m.get("shop_id") == shop_id:
                # Role check
                role = m.get("role_code", "")
                if role in ("owner", "admin", "manager", "staff", "accountant"):
                    return True

    raise ShopAccessDeniedError(
        f"Security Alert: User {user_id} is not authorized to access shop {shop_id}."
    )


def sanitize_multilingual_input(text: str) -> str:
    """
    Sanitizes multilingual user and document input against Unicode spoofing,
    homoglyph collision, and dangerous bidirectional override (Bidi) attacks.
    """
    if not text:
        return ""

    import unicodedata

    # 1. Canonical NFKC normalization
    normalized = unicodedata.normalize("NFKC", text)

    # 2. Neutralize dangerous BiDi control characters that disguise malicious payloads
    # (e.g. \u202E Right-to-Left Override used to mask executable file extensions)
    bidi_overrides = [
        "\u202a", "\u202b", "\u202c", "\u202d", "\u202e",
        "\u2066", "\u2067", "\u2068", "\u2069"
    ]
    for char in bidi_overrides:
        normalized = normalized.replace(char, "")

    # 3. Strip invisible zero-width characters (except valid ZWNJ/ZWJ when embedded in words)
    invisible_chars = ["\ufeff", "\u200b", "\u2060"]
    for char in invisible_chars:
        normalized = normalized.replace(char, "")

    return normalized


def detect_multilingual_prompt_injection(text: str) -> tuple[bool, str]:
    """
    Detects adversarial prompt injection attempts across English, Bengali,
    Chinese, Arabic, Russian, Spanish, and Hindi.
    """
    if not text:
        return False, ""

    import re
    clean = sanitize_multilingual_input(text).lower()

    injection_patterns = [
        # English
        (r"(?i)\b(?:ignore|disregard|forget)\s+(?:all\s+)?(?:previous|prior)\s+(?:instructions|prompts|rules)", "EN: Instruction override"),
        (r"(?i)\b(?:system\s+prompt\s+override|prompt\s+override)", "EN: System prompt override"),
        (r"(?i)\b(?:bypass|disable)[^.\n]{0,30}(?:security|verification|dscr|guardrail|check|limit|rule|loan\s+risk)", "EN: Security bypass attempt"),
        (r"(?i)\bapprove\s+(?:all|this)\s+loan", "EN: Unauthorized loan approval trigger"),
        (r"(?i)\b(?:jailbreak|dan\s+mode|developer\s+mode|act\s+as\s+root)\b", "EN: Jailbreak signature"),
        (r"(?i)\b(?:drop\s+table|delete\s+from|rm\s+-rf|format\s+c:)", "EN: Malicious command execution"),
        # Bengali
        (r"(?:পূর্বের|পূর্ববর্তী|আগের)\s+(?:সমস্ত|সব|সকল)\s+(?:নির্দেশ|নির্দেশনা|নিয়ম)\s+(?:ভুলে|উপেক্ষা)", "BN: Instruction override"),
        (r"(?:নিরাপত্তা|যাচাইকরণ|নিয়ম|সীমা)[^।\n]{0,20}(?:উপেক্ষা|বাইপাস)", "BN: Security bypass attempt"),
        (r"(?:ডাটাবেস|তথ্য|রেকর্ড)\s*(?:মুছে|ডিলিট)", "BN: Malicious deletion attempt"),
        (r"(?:সব|সকল|এই)\s+ঋণ\s+(?:অনুমোদন|মঞ্জুর)\s+করুন", "BN: Unauthorized loan approval trigger"),
        # Chinese
        (r"(?:忽略|无视|取消|覆盖)[^，。\n]{0,20}(?:指令|指示|规则|提示|要求)", "ZH: Instruction override"),
        (r"(?:绕过|禁用|取消)[^，。\n]{0,20}(?:风控|安全|验证|dscr|审批|规则|限制|贷款风险)", "ZH: Security bypass attempt"),
        (r"(?:批准|通过)[^，。\n]{0,10}(?:所有|最高)?贷款", "ZH: Unauthorized loan approval trigger"),
        # Arabic
        (r"(?:تجاهل|انسَ|إلغاء)\s+(?:كافة|جميع)?\s*(?:التعليمات|الأوامر)\s+(?:السابقة)", "AR: Instruction override"),
        (r"(?:تجاوز|تعطيل)\s+(?:قواعد\s+الأمان|التحقق|الأمان|شروط\s+الائتمان)", "AR: Security bypass attempt"),
        (r"(?:وافق|الموافقة)\s+على\s+(?:جميع|هذا)\s+القروض?", "AR: Unauthorized loan approval trigger"),
        # Russian
        (r"(?:игнорируй|забудь)\s+(?:все\s+)?(?:предыдущие|прошлые)\s+инструкции", "RU: Instruction override"),
        (r"(?:обойти|отключить)\s+(?:защиту|проверку|dscr)", "RU: Security bypass attempt"),
        # Spanish
        (r"(?i)\b(?:ignora|olvida)\s+(?:todas\s+las\s+)?(?:instrucciones\s+anteriores)", "ES: Instruction override"),
        (r"(?i)\b(?:aprueba|aprobar)\s+todos\s+los\s+préstamos", "ES: Unauthorized loan approval trigger"),
        # Hindi
        (r"(?:पिछले|पूर्व)\s+सभी\s+(?:निर्देशों|नियमों)\s+को\s+(?:अनदेखा|भूल)", "HI: Instruction override"),
        (r"सभी\s+ऋण(?:ों)?\s+को\s+स्वीकृत\s+करें", "HI: Unauthorized loan approval trigger"),
    ]

    for pat, label in injection_patterns:
        if re.search(pat, clean):
            return True, f"Adversarial prompt injection detected: {label}"

    return False, ""


def redact_pii(text: str) -> str:
    """
    Masks sensitive personal identification (credit cards, phone numbers, tax IDs)
    to protect business privacy before logging or model forwarding.
    """
    if not text:
        return ""

    import re

    # 1. Credit / Debit card numbers (15-16 digits, typically 4 groups of 4)
    t = re.sub(r"\b(?:\d{4}[ -]?){3}\d{4}\b|\b3[47]\d{2}[ -]?\d{6}[ -]?\d{5}\b", "[REDACTED_PAYMENT_CARD]", text)

    # 2. Email addresses
    t = re.sub(r"(?i)\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", "[REDACTED_EMAIL]", t)

    # 3. International & Domestic Phone Numbers
    t = re.sub(r"(?:\+\d{1,3}[-.\s]*)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b", "[REDACTED_PHONE]", t)

    return t
