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
    """Extracts and verifies session user from Authorization header."""
    if not authorization:
        # For development / initial testing, allow default demo admin if header absent
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
    try:
        return enforce_shop_isolation(user.id, shop_id, memberships)
    except ShopAccessDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
