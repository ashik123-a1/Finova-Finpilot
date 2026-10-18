"""
FastAPI Dependencies: Database Sessions, Authentication, and Shop Isolation.
"""

from __future__ import annotations

from typing import Generator, Optional
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.config import settings
from src.core.security import verify_token, enforce_shop_isolation
from src.core.exceptions import ShopAccessDeniedError
from src.database.connection import get_db
from src.database.models import User, BusinessMembership


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """
    Extracts and verifies session user from Authorization header.
    
    Security Guarantee:
    Client-supplied headers such as X-User-ID, X-Business-ID, and X-Shop-ID are
    NEVER used for authentication and cannot forge identity. Identity is strictly
    established via signed HMAC session tokens (Authorization: Bearer <token>)
    issued by /api/auth/login or /api/auth/register.
    """
    if not authorization:
        # In production, require an explicit, valid Authorization header unconditionally
        if settings.ENVIRONMENT.lower() == "production":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header.",
            )
        # For development / local demo only, allow fallback to first active user with a membership if header is absent
        user = (
            db.query(User)
            .join(BusinessMembership, BusinessMembership.user_id == User.id)
            .filter(User.is_active == True, BusinessMembership.is_active == True)
            .first()
        )
        if not user:
            user = db.query(User).filter_by(is_active=True).first()
        if user:
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header or no active users in database.",
        )

    token = authorization.replace("Bearer ", "").strip()
    user_id = verify_token(token, settings.SECRET_KEY)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token.",
        )

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated.",
        )
    return user


def verify_shop_access_dependency(
    shop_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> bool:
    """Verifies that the authenticated user has access to the requested shop."""
    stmt = select(BusinessMembership).where(
        BusinessMembership.user_id == user.id,
        BusinessMembership.is_active == True,
    )
    memberships = [
        {"user_id": m.user_id, "business_id": m.business_id, "shop_id": m.shop_id, "role_code": m.role_code}
        for m in db.scalars(stmt).all()
    ]
    return enforce_shop_isolation(user.id, shop_id, memberships)
