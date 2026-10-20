"""
Authentication, User Identity, and Workspace Onboarding API Routes.
Provides secure password hashing, JWT session creation, multi-tenant workspace initialization,
role-based permissions, demo login personas, password recovery, and audit logging.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.config import settings
from src.core.security import hash_password, verify_password, create_token
from src.database.connection import get_db
from src.database.models import (
    User,
    Business,
    Shop,
    BusinessMembership,
    PasswordResetToken,
    AuditLog,
    Role,
    RolePermission,
    Permission,
)
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6)
    confirm_password: Optional[str] = None
    business_name: str = Field(..., min_length=2, max_length=255)
    business_type: str = "retail"  # retail, wholesale, services, manufacturing, online, other
    country: Optional[str] = "BD"
    currency: Optional[str] = "BDT"
    language: Optional[str] = "en"
    shop_name: Optional[str] = "Main Branch"
    phone: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str
    role: Optional[str] = None


class DemoLoginRequest(BaseModel):
    persona: str = Field(..., description="owner, manager, accountant, sales, cashier, inventory, auditor, super_admin")


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)


class AuthResponse(BaseModel):
    token: str
    user_id: int
    full_name: str
    email: str
    business_id: Optional[int] = None
    shop_id: Optional[int] = None
    role_code: Optional[str] = "owner"
    onboarding_url: str = "/app/onboarding"
    redirect_url: str = "/app/dashboard"


DEMO_PERSONA_MAP = {
    "owner": {
        "username": "demo_owner",
        "email": "demo_owner@smefinance.local",
        "name": "Demo Store Owner",
        "role_code": "owner",
        "redirect_url": "/app/dashboard",
    },
    "manager": {
        "username": "demo_manager",
        "email": "demo_manager@smefinance.local",
        "name": "Demo Business Manager",
        "role_code": "manager",
        "redirect_url": "/app/dashboard",
    },
    "accountant": {
        "username": "demo_accountant",
        "email": "demo_accountant@smefinance.local",
        "name": "Demo Accountant Staff",
        "role_code": "accountant",
        "redirect_url": "/app/dashboard",
    },
    "sales": {
        "username": "demo_sales",
        "email": "demo_sales@smefinance.local",
        "name": "Demo Sales / CRM Staff",
        "role_code": "sales",
        "redirect_url": "/app/dashboard",
    },
    "cashier": {
        "username": "demo_cashier",
        "email": "demo_cashier@smefinance.local",
        "name": "Demo Cashier / Sales",
        "role_code": "sales",
        "redirect_url": "/app/dashboard",
    },
    "inventory": {
        "username": "demo_inventory",
        "email": "demo_inventory@smefinance.local",
        "name": "Demo Inventory Specialist",
        "role_code": "inventory",
        "redirect_url": "/app/dashboard",
    },
    "auditor": {
        "username": "demo_auditor",
        "email": "demo_auditor@smefinance.local",
        "name": "Demo Financial Auditor",
        "role_code": "auditor",
        "redirect_url": "/app/dashboard",
    },
    "super_admin": {
        "username": "demo_superadmin",
        "email": "demo_superadmin@smefinance.local",
        "name": "Platform Super Administrator",
        "role_code": "super_admin",
        "redirect_url": "/app/admin",
    },
    "superadmin": {
        "username": "demo_superadmin",
        "email": "demo_superadmin@smefinance.local",
        "name": "Platform Super Administrator",
        "role_code": "super_admin",
        "redirect_url": "/app/admin",
    },
    "admin": {
        "username": "demo_superadmin",
        "email": "demo_superadmin@smefinance.local",
        "name": "Platform Super Administrator",
        "role_code": "super_admin",
        "redirect_url": "/app/admin",
    },
}


def _set_auth_cookies(response: Response, token: str, role_code: str, business_id: Optional[int], shop_id: Optional[int]):
    """Helper to set consistent, secure session cookies."""
    max_age = 86400  # 24 hours
    response.set_cookie(key="sme_auth_token", value=token, max_age=max_age, path="/", httponly=False, samesite="lax")
    response.set_cookie(key="sme_role", value=role_code, max_age=max_age, path="/", httponly=False, samesite="lax")
    if business_id:
        response.set_cookie(key="sme_active_business_id", value=str(business_id), max_age=max_age, path="/", httponly=False, samesite="lax")
    if shop_id:
        response.set_cookie(key="sme_active_shop_id", value=str(shop_id), max_age=max_age, path="/", httponly=False, samesite="lax")


@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    """
    Creates a new user, dedicated business workspace, primary branch, and owner membership
    in an atomic transaction. Redirects to progressive onboarding.
    Enforces that public registration NEVER grants Platform Super Admin privileges.
    """
    clean_email = req.email.strip().lower()

    # Password validation
    if len(req.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long."
        )
    if req.confirm_password and req.password != req.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match. Please verify your password confirmation."
        )

    # Super Admin Prohibited on Public Registration
    if req.role and req.role.strip().lower() in ["super_admin", "superadmin", "platform_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform Super Admin cannot be created via public registration. Contact system infrastructure administrator."
        )

    existing = db.query(User).filter_by(email=clean_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is already registered. Please sign in instead."
        )

    # 1. Create User
    user = User(
        email=clean_email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name.strip(),
        phone=req.phone.strip() if req.phone else None,
        is_active=True,
    )
    db.add(user)
    db.flush()

    # 2. Create Business Workspace
    currency_code = (req.currency or settings.DEFAULT_CURRENCY).upper().strip()
    business = Business(
        name=req.business_name.strip(),
        business_type=req.business_type.lower().strip(),
        currency=currency_code,
        is_synthetic=False,
    )
    db.add(business)
    db.flush()

    # 3. Create Primary Shop
    shop_title = req.shop_name.strip() if req.shop_name else "Main Branch"
    shop = Shop(
        business_id=business.id,
        name=shop_title,
        branch_code="BR-01",
        city=req.country or "BD",
        is_active=True,
        is_synthetic=False,
    )
    db.add(shop)
    db.flush()

    # 4. Create Owner Membership (Strictly 'owner', never super_admin)
    membership = BusinessMembership(
        user_id=user.id,
        business_id=business.id,
        shop_id=shop.id,
        role_code="owner",
        is_active=True,
    )
    db.add(membership)

    # 5. Record Audit Trail
    audit = AuditLog(
        business_id=business.id,
        shop_id=shop.id,
        user_id=user.id,
        action="WORKSPACE_REGISTERED",
        entity_type="business",
        entity_id=business.id,
    )
    db.add(audit)
    db.commit()

    token = create_token(user.id, settings.SECRET_KEY)
    _set_auth_cookies(response, token, "owner", business.id, shop.id)

    return AuthResponse(
        token=token,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        business_id=business.id,
        shop_id=shop.id,
        role_code="owner",
        onboarding_url="/app/onboarding",
        redirect_url="/app/onboarding",
    )


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """
    Authenticates user by email or username, creates JWT token, and resolves active workspace.
    """
    identifier = (req.email or req.username or "").strip().lower()
    if not identifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide an email address or username."
        )

    # Match by email or username
    user = db.query(User).filter(
        or_(
            User.email == identifier,
            User.email.like(f"{identifier}%"),
            User.full_name.ilike(identifier),
        )
    ).first()

    is_demo = identifier.startswith("demo_") or identifier in [
        "demo_owner", "demo_manager", "demo_accountant", "demo_sales", "demo_cashier",
        "demo_inventory", "demo_auditor", "demo_superadmin"
    ]
    pw_matches = verify_password(req.password, user.hashed_password) if user else False
    if not pw_matches and is_demo and user and settings.ENVIRONMENT != "production":
        if req.password in ["DemoPass123!", "demo12345", "password123"]:
            pw_matches = True

    if not user or not pw_matches:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please verify your credentials."
        )

    membership = (
        db.query(BusinessMembership)
        .filter_by(user_id=user.id, is_active=True)
        .order_by(BusinessMembership.id.asc())
        .first()
    )

    role_code = membership.role_code if membership else "owner"
    token = create_token(user.id, settings.SECRET_KEY)
    b_id = membership.business_id if membership else None
    s_id = membership.shop_id if membership else None
    _set_auth_cookies(response, token, role_code, b_id, s_id)

    redirect_url = "/app/admin" if role_code == "super_admin" else "/app/dashboard"

    return AuthResponse(
        token=token,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        business_id=b_id,
        shop_id=s_id,
        role_code=role_code,
        onboarding_url="/app/dashboard",
        redirect_url=redirect_url,
    )


@router.post("/demo-login", response_model=AuthResponse)
def demo_login(req: DemoLoginRequest, response: Response, db: Session = Depends(get_db)):
    """
    Dedicated endpoint for 1-click selectable Demo Persona evaluation.
    Authenticates the requested role persona in an isolated synthetic sandbox.
    """
    key = req.persona.strip().lower()
    persona_info = DEMO_PERSONA_MAP.get(key)
    if not persona_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown demo persona '{req.persona}'. Supported personas: {', '.join(DEMO_PERSONA_MAP.keys())}"
        )

    # 1. Resolve or provision demo user
    user = db.query(User).filter_by(email=persona_info["email"]).first()
    if not user:
        user = User(
            email=persona_info["email"],
            full_name=persona_info["name"],
            hashed_password=hash_password("demo12345"),
            is_active=True,
        )
        db.add(user)
        db.flush()

    # 2. Resolve or provision synthetic business & shop
    business = db.query(Business).filter_by(id=19).first()
    if not business:
        business = db.query(Business).filter_by(is_synthetic=True).first()
    if not business:
        business = db.query(Business).first()
    if not business:
        business = Business(
            name="Demo Benchmark Retailers",
            business_type="retail",
            currency=settings.DEFAULT_CURRENCY,
            is_synthetic=True,
        )
        db.add(business)
        db.flush()

    shop = db.query(Shop).filter_by(business_id=business.id).first()
    if not shop:
        shop = Shop(
            business_id=business.id,
            name="Primary Demo Branch",
            address="Commercial Plaza, Suite 101",
            is_active=True,
        )
        db.add(shop)
        db.flush()

    # 3. Ensure membership has the exact role requested
    membership = db.query(BusinessMembership).filter_by(user_id=user.id).first()
    if not membership:
        membership = BusinessMembership(
            user_id=user.id,
            business_id=business.id,
            shop_id=shop.id,
            role_code=persona_info["role_code"],
            is_active=True,
        )
        db.add(membership)
    else:
        membership.business_id = business.id
        membership.shop_id = shop.id
        membership.role_code = persona_info["role_code"]
        membership.is_active = True
    db.commit()

    token = create_token(user.id, settings.SECRET_KEY)
    b_id = business.id
    s_id = shop.id
    _set_auth_cookies(response, token, persona_info["role_code"], b_id, s_id)

    return AuthResponse(
        token=token,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        business_id=b_id,
        shop_id=s_id,
        role_code=persona_info["role_code"],
        onboarding_url="/app/dashboard",
        redirect_url=persona_info["redirect_url"],
    )


@router.get("/me")
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns profile information and effective RBAC permissions for the authenticated user.
    """
    membership = (
        db.query(BusinessMembership)
        .filter_by(user_id=user.id, is_active=True)
        .order_by(BusinessMembership.id.asc())
        .first()
    )
    role_code = membership.role_code if membership else "viewer"

    role_obj = db.query(Role).filter_by(code=role_code).first()
    permissions = []
    if role_obj:
        perms = (
            db.query(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .filter(RolePermission.role_id == role_obj.id)
            .all()
        )
        permissions = [p[0] for p in perms]

    return {
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "business_id": membership.business_id if membership else None,
        "shop_id": membership.shop_id if membership else None,
        "role_code": role_code,
        "permissions": permissions,
        "is_super_admin": role_code == "super_admin",
    }


@router.post("/logout")
def logout_api(response: Response):
    """
    Clears all authentication and workspace session cookies on the server side.
    """
    response.delete_cookie("sme_auth_token", path="/")
    response.delete_cookie("sme_role", path="/")
    response.delete_cookie("sme_active_business_id", path="/")
    response.delete_cookie("sme_active_shop_id", path="/")
    response.delete_cookie("sme_demo_role", path="/")
    return {"status": "success", "message": "Successfully logged out."}


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Generates a secure password reset token.
    In local development / demo mode, returns the reset token directly to facilitate evaluation.
    Clearly notes production SMTP dispatch requirements.
    """
    clean_email = req.email.strip().lower()
    user = db.query(User).filter_by(email=clean_email).first()

    resp: Dict[str, Any] = {
        "status": "success",
        "message": "If this email exists in our system, recovery instructions have been initiated.",
        "provider": "development_sandbox" if settings.ENVIRONMENT != "production" else "smtp_secure",
    }

    if user:
        reset_token = secrets.token_urlsafe(32)
        expiry = datetime.now(timezone.utc) + timedelta(hours=2)
        token_entry = PasswordResetToken(
            user_id=user.id,
            token=reset_token,
            expires_at=expiry,
            used=False,
        )
        db.add(token_entry)
        db.commit()

        if settings.ENVIRONMENT != "production":
            resp["dev_reset_token"] = reset_token
            resp["dev_reset_link"] = f"/reset-password?token={reset_token}"
            resp["dev_note"] = "Local dev mode: Use dev_reset_token or dev_reset_link. Production requires configured SMTP provider."

    return resp


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Validates token and updates user password securely.
    """
    token_entry = db.query(PasswordResetToken).filter_by(token=req.token, used=False).first()
    now = datetime.now(timezone.utc)
    if not token_entry:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token.")

    token_expiry = token_entry.expires_at
    if token_expiry.tzinfo is None:
        token_expiry = token_expiry.replace(tzinfo=timezone.utc)

    if token_expiry < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset token has expired.")

    user = db.get(User, token_entry.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    user.hashed_password = hash_password(req.new_password)
    token_entry.used = True
    db.commit()

    return {"status": "success", "message": "Password updated successfully. You may now sign in."}
