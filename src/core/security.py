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
