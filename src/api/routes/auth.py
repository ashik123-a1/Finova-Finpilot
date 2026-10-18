"""
Authentication and User Identity API Routes.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.config import settings
from src.core.security import hash_password, verify_password, create_token
from src.database.connection import get_db
from src.database.models import User, Business, Shop, BusinessMembership

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    phone: Optional[str] = None
    business_name: str
    business_type: str = "grocery"
    shop_name: str = "Main Branch"


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user_id: int
    full_name: str
    email: str
    business_id: Optional[int] = None
    shop_id: Optional[int] = None


@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter_by(email=req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered.")

    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        phone=req.phone,
        is_active=True,
    )
    db.add(user)
    db.flush()

    business = Business(
        name=req.business_name,
        business_type=req.business_type,
        currency=settings.DEFAULT_CURRENCY,
    )
    db.add(business)
    db.flush()

    shop = Shop(
        business_id=business.id,
        name=req.shop_name,
        is_active=True,
    )
    db.add(shop)
    db.flush()

    membership = BusinessMembership(
        user_id=user.id,
        business_id=business.id,
        shop_id=shop.id,
        role_code="owner",
        is_active=True,
    )
    db.add(membership)
    db.commit()

    token = create_token(user.id, settings.SECRET_KEY)
    return AuthResponse(
        token=token,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        business_id=business.id,
        shop_id=shop.id,
    )


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    membership = db.query(BusinessMembership).filter_by(user_id=user.id, is_active=True).first()
    token = create_token(user.id, settings.SECRET_KEY)

    return AuthResponse(
        token=token,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        business_id=membership.business_id if membership else None,
        shop_id=membership.shop_id if membership else None,
    )
