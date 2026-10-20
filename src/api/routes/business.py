"""
Business and Shop Management API Routes.
Provides multi-tenant shop listing, business profile retrieval, and shop metadata with isolation.
"""

import json
import secrets
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.database.connection import get_db
from src.database.models import (
    User,
    Business,
    Shop,
    BusinessMembership,
    WorkspaceInvitation,
    AuditLog,
    Payment,
    Customer,
    Product,
)
from src.api.dependencies import get_current_user, verify_shop_access_dependency
from src.core.exceptions import ShopAccessDeniedError

router = APIRouter(prefix="/business", tags=["Business & Shops"])


class ShopResponse(BaseModel):
    id: int
    business_id: int
    name: str
    branch_code: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class BusinessResponse(BaseModel):
    id: int
    name: str
    business_type: str
    currency: str
    user_role: str
    shops: List[ShopResponse]

    class Config:
        from_attributes = True


@router.get("/list", response_model=List[BusinessResponse])
def list_user_businesses(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns all businesses and accessible shops for the authenticated user.
    Enforces multi-tenant shop isolation based on active memberships.
    """
    memberships = (
        db.query(BusinessMembership)
        .filter_by(user_id=user.id, is_active=True)
        .all()
    )
    if not memberships:
        return []

    # Map memberships by business_id
    business_roles: Dict[int, str] = {}
    business_allowed_shops: Dict[int, Optional[set]] = {}

    for m in memberships:
        business_roles[m.business_id] = m.role_code
        if m.business_id not in business_allowed_shops:
            business_allowed_shops[m.business_id] = set() if m.shop_id else None
        elif business_allowed_shops[m.business_id] is not None:
            if m.shop_id is None:
                business_allowed_shops[m.business_id] = None  # Full access
            else:
                business_allowed_shops[m.business_id].add(m.shop_id)

    results = []
    for biz_id, role in business_roles.items():
        biz = db.get(Business, biz_id)
        if not biz:
            continue

        all_shops = db.query(Shop).filter_by(business_id=biz.id, is_active=True).all()
        allowed_shop_set = business_allowed_shops.get(biz_id)

        if allowed_shop_set is None:
            accessible_shops = all_shops
        else:
            accessible_shops = [s for s in all_shops if s.id in allowed_shop_set]

        results.append(
            BusinessResponse(
                id=biz.id,
                name=biz.name,
                business_type=biz.business_type,
                currency=biz.currency,
                user_role=role,
                shops=[
                    ShopResponse(
                        id=s.id,
                        business_id=s.business_id,
                        name=s.name,
                        branch_code=s.branch_code,
                        address=s.address,
                        city=s.city,
                        is_active=s.is_active,
                    )
                    for s in accessible_shops
                ],
            )
        )

    return results


# ==============================================================================
# Multi-Step Business Onboarding Wizard API (Phase 3)
# ==============================================================================

class OnboardingStatusResponse(BaseModel):
    has_business: bool
    business_id: Optional[int] = None
    business_name: Optional[str] = None
    business_type: Optional[str] = "retail"
    country: Optional[str] = "BD"
    currency: Optional[str] = "BDT"
    language: Optional[str] = "en"
    shop_id: Optional[int] = None
    shop_name: Optional[str] = None
    branch_code: Optional[str] = "BR-01"
    is_multibranch: bool = False
    sales_operation: str = "counter_pos"
    monthly_revenue_range: str = "100k_500k"
    main_products: str = ""
    employee_count: str = "1_5"
    record_keeping_method: str = "excel"
    financial_starter_path: str = "opening_cash"
    opening_cash: float = 50000.0
    goals_cashflow: bool = True
    goals_profit: bool = True
    goals_overdue: bool = True
    goals_stock: bool = True
    goals_summary: bool = True
    runway_alert_days: int = 30


class OnboardingCompleteRequest(BaseModel):
    business_name: str
    business_type: str = "retail"
    country: str = "BD"
    currency: str = "BDT"
    language: str = "en"
    shop_name: str = "Main Branch"
    branch_code: Optional[str] = "BR-01"
    is_multibranch: bool = False
    sales_operation: str = "counter_pos"
    monthly_revenue_range: Optional[str] = "100k_500k"
    main_products: Optional[str] = None
    employee_count: Optional[str] = "1_5"
    record_keeping_method: Optional[str] = "excel"
    financial_starter_path: str = "opening_cash"
    opening_cash: Optional[float] = 0.0
    customer_name: Optional[str] = None
    customer_balance: Optional[float] = 0.0
    seed_demo_data: bool = False
    goals_cashflow: bool = True
    goals_profit: bool = True
    goals_overdue: bool = True
    goals_stock: bool = True
    goals_summary: bool = True
    runway_alert_days: int = 30


@router.get("/onboarding-status", response_model=OnboardingStatusResponse)
def get_onboarding_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns current workspace onboarding progress and entity details for the user.
    Allows resuming the setup wizard without duplicating workspaces or branches.
    """
    membership = (
        db.query(BusinessMembership)
        .filter_by(user_id=user.id, is_active=True)
        .order_by(BusinessMembership.id.asc())
        .first()
    )
    if not membership:
        return OnboardingStatusResponse(
            has_business=False,
            business_name="My New Business",
            business_type="retail",
            currency="BDT",
            country="BD",
            language="en",
            shop_name="Main Branch",
            branch_code="BR-01",
        )

    biz = db.get(Business, membership.business_id)
    shop = db.get(Shop, membership.shop_id) if membership.shop_id else None
    if not shop and biz:
        shop = db.query(Shop).filter_by(business_id=biz.id).first()

    return OnboardingStatusResponse(
        has_business=True,
        business_id=biz.id if biz else None,
        business_name=biz.name if biz else "My Business",
        business_type=biz.business_type if biz else "retail",
        country=shop.city if shop and shop.city else "BD",
        currency=biz.currency if biz else "BDT",
        language="en",
        shop_id=shop.id if shop else None,
        shop_name=shop.name if shop else "Main Branch",
        branch_code=shop.branch_code if shop and shop.branch_code else "BR-01",
        is_multibranch=False,
        sales_operation="counter_pos",
        monthly_revenue_range="100k_500k",
        main_products="",
        employee_count="1_5",
        record_keeping_method="excel",
        financial_starter_path="opening_cash",
        opening_cash=50000.0,
        goals_cashflow=True,
        goals_profit=True,
        goals_overdue=True,
        goals_stock=True,
        goals_summary=True,
        runway_alert_days=30,
    )


@router.post("/onboarding")
def complete_onboarding(
    req: OnboardingCompleteRequest,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Completes or updates the multi-step business onboarding setup.
    Guarantees idempotency: updates existing workspace and shop without creating duplicates on resume.
    Initializes opening cash balances, initial customers, or starter inventory if selected.
    """
    membership = (
        db.query(BusinessMembership)
        .filter_by(user_id=user.id, is_active=True)
        .order_by(BusinessMembership.id.asc())
        .first()
    )

    clean_biz_name = req.business_name.strip()
    clean_biz_type = req.business_type.lower().strip()
    clean_curr = req.currency.upper().strip()
    clean_shop_name = req.shop_name.strip()
    clean_branch_code = (req.branch_code or "BR-01").strip()
    clean_country = req.country.strip()

    if membership:
        biz = db.get(Business, membership.business_id)
        if not biz:
            biz = Business(name=clean_biz_name, business_type=clean_biz_type, currency=clean_curr, is_synthetic=False)
            db.add(biz)
            db.flush()
            membership.business_id = biz.id

        biz.name = clean_biz_name
        biz.business_type = clean_biz_type
        biz.currency = clean_curr

        shop = db.get(Shop, membership.shop_id) if membership.shop_id else None
        if not shop:
            shop = db.query(Shop).filter_by(business_id=biz.id).first()
        if not shop:
            shop = Shop(
                business_id=biz.id,
                name=clean_shop_name,
                branch_code=clean_branch_code,
                city=clean_country,
                is_active=True,
                is_synthetic=False,
            )
            db.add(shop)
            db.flush()
            membership.shop_id = shop.id
        else:
            shop.name = clean_shop_name
            shop.branch_code = clean_branch_code
            shop.city = clean_country
    else:
        biz = Business(
            name=clean_biz_name,
            business_type=clean_biz_type,
            currency=clean_curr,
            is_synthetic=False,
        )
        db.add(biz)
        db.flush()

        shop = Shop(
            business_id=biz.id,
            name=clean_shop_name,
            branch_code=clean_branch_code,
            city=clean_country,
            is_active=True,
            is_synthetic=False,
        )
        db.add(shop)
        db.flush()

        membership = BusinessMembership(
            user_id=user.id,
            business_id=biz.id,
            shop_id=shop.id,
            role_code="owner",
            is_active=True,
        )
        db.add(membership)
        db.flush()

    # Starter financial entries based on selected pathway
    if req.financial_starter_path == "opening_cash" and (req.opening_cash or 0) > 0:
        opening_minor = int(round(req.opening_cash * 100))
        existing_payment = db.query(Payment).filter_by(
            shop_id=shop.id,
            reference_type="opening_balance"
        ).first()
        if not existing_payment:
            payment = Payment(
                business_id=biz.id,
                shop_id=shop.id,
                payment_type="customer_inflow",
                reference_type="opening_balance",
                amount_minor=opening_minor,
                payment_method="cash",
                notes="Initial cash drawer liquidity established during workspace onboarding.",
                created_by=user.id,
                is_synthetic=False,
            )
            db.add(payment)

    elif req.financial_starter_path == "customer_balance" and req.customer_name:
        cust_name = req.customer_name.strip()
        balance_minor = int(round((req.customer_balance or 0.0) * 100))
        existing_cust = db.query(Customer).filter_by(shop_id=shop.id, name=cust_name).first()
        if not existing_cust:
            cust = Customer(
                business_id=biz.id,
                shop_id=shop.id,
                name=cust_name,
                balance_minor=balance_minor,
                segment="regular",
                is_synthetic=False,
            )
            db.add(cust)

    if req.seed_demo_data or req.financial_starter_path == "clean_or_demo":
        existing_prod = db.query(Product).filter_by(shop_id=shop.id).first()
        if not existing_prod:
            sample_items = [
                ("SKU-BASMATI-5KG", "Premium Basmati Rice 5kg", "Grains & Rice", 48000, 62000, 45),
                ("SKU-OIL-SOYA-2L", "Fortified Soybean Cooking Oil 2L", "Edible Oils", 31000, 38000, 60),
                ("SKU-FLOUR-ATTA-2K", "Whole Wheat Atta Flour 2kg", "Flour & Bakery", 11500, 14500, 80),
                ("SKU-LENTIL-MASUR-1K", "Red Masur Lentils 1kg", "Pulses & Legumes", 12500, 15500, 50),
            ]
            for sku, name, cat, cost_min, sell_min, stock in sample_items:
                p = Product(
                    business_id=biz.id,
                    shop_id=shop.id,
                    sku=sku,
                    name=name,
                    category=cat,
                    cost_price_minor=cost_min,
                    selling_price_minor=sell_min,
                    current_stock=stock,
                    min_stock_alert=10,
                    is_active=True,
                    is_synthetic=False,
                )
                db.add(p)

    # Dispatch welcome notification
    from src.api.routes.notifications import create_persistent_notification
    create_persistent_notification(
        db=db,
        user_id=user.id,
        business_id=biz.id,
        shop_id=shop.id,
        title="Workspace Onboarding Completed",
        message=f"Welcome to SME Finance Copilot! {biz.name} ({shop.name}) is fully configured with {biz.currency} currency standards.",
        notification_type="system",
        severity="success",
        action_url="/app/dashboard",
        dedup_key=f"onboarding_welcome_{user.id}_{biz.id}"
    )

    # Record Audit Log
    audit = AuditLog(
        business_id=biz.id,
        shop_id=shop.id,
        user_id=user.id,
        action="ONBOARDING_COMPLETED",
        entity_type="business",
        entity_id=biz.id,
        new_values_json=json.dumps({
            "business_name": biz.name,
            "currency": biz.currency,
            "language": req.language or "en",
            "shop_name": shop.name,
            "branch_code": shop.branch_code,
            "starter_path": req.financial_starter_path,
        }),
    )
    db.add(audit)

    # Persist preferred language to user profile and cookie
    clean_lang = (req.language or "en").lower().split("-")[0].strip()
    if clean_lang in ["en", "bn", "zh"]:
        user.preferred_language = clean_lang
        response.set_cookie(key="sme_lang", value=clean_lang, max_age=31536000, path="/", samesite="lax")

    db.commit()

    # Set active cookies
    response.set_cookie(key="sme_active_business_id", value=str(biz.id), max_age=86400, path="/", httponly=False, samesite="lax")
    response.set_cookie(key="sme_active_shop_id", value=str(shop.id), max_age=86400, path="/", httponly=False, samesite="lax")

    return {
        "status": "success",
        "message": "Workspace onboarding completed successfully.",
        "business_id": biz.id,
        "shop_id": shop.id,
        "redirect_url": "/app/dashboard",
    }


@router.get("/{business_id}/shops", response_model=List[ShopResponse])
def list_business_shops(
    business_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lists shops for a specific business accessible to the authenticated user.
    """
    memberships = (
        db.query(BusinessMembership)
        .filter_by(user_id=user.id, business_id=business_id, is_active=True)
        .all()
    )
    if not memberships:
        raise ShopAccessDeniedError(
            f"Security Alert: Access denied to business {business_id}. User {user.id} has no active membership."
        )

    all_shops = db.query(Shop).filter_by(business_id=business_id, is_active=True).all()

    # Check if user has global business access or specific shop access
    allowed_shop_ids = {m.shop_id for m in memberships}
    if None in allowed_shop_ids:
        accessible_shops = all_shops
    else:
        accessible_shops = [s for s in all_shops if s.id in allowed_shop_ids]

    return [
        ShopResponse(
            id=s.id,
            business_id=s.business_id,
            name=s.name,
            branch_code=s.branch_code,
            address=s.address,
            city=s.city,
            is_active=s.is_active,
        )
        for s in accessible_shops
    ]


@router.get("/shops/{shop_id}", response_model=ShopResponse)
def get_shop_details(
    shop_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves metadata for a single shop after validating isolation access.
    """
    verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)
    shop = db.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found.")

    return ShopResponse(
        id=shop.id,
        business_id=shop.business_id,
        name=shop.name,
        branch_code=shop.branch_code,
        address=shop.address,
        city=shop.city,
        is_active=shop.is_active,
    )


# ==============================================================================
# Workspace Staff Invitations & Membership Control (Phase 1 & 2)
# ==============================================================================

class InviteStaffRequest(BaseModel):
    email: str
    role_code: str = "staff"  # manager, accountant, sales, inventory, auditor
    shop_id: Optional[int] = None


class InvitationResponse(BaseModel):
    id: int
    business_id: int
    shop_id: Optional[int] = None
    email: str
    role_code: str
    status: str
    invitation_token: str
    expires_at: str
    created_at: str


@router.post("/{business_id}/invitations", response_model=InvitationResponse)
def create_workspace_invitation(
    business_id: int,
    req: InviteStaffRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Issues an invitation to join the business workspace.
    Requires 'owner' or 'manager' membership.
    Non-owners cannot invite owners or super-admins.
    """
    membership = (
        db.query(BusinessMembership)
        .filter_by(user_id=user.id, business_id=business_id, is_active=True)
        .first()
    )
    if not membership or membership.role_code not in ["owner", "manager", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only workspace owners and managers can issue team invitations."
        )

    # Prevent privilege escalation
    target_role = req.role_code.lower().strip()
    if target_role in ["owner", "super_admin"] and membership.role_code != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only the workspace owner can invite another owner."
        )

    clean_email = req.email.strip().lower()
    token = secrets.token_urlsafe(24)
    expires = datetime.now(timezone.utc) + timedelta(days=7)

    inv = WorkspaceInvitation(
        business_id=business_id,
        shop_id=req.shop_id,
        email=clean_email,
        role_code=target_role,
        invitation_token=token,
        invited_by_user_id=user.id,
        status="pending",
        expires_at=expires,
    )
    db.add(inv)

    audit = AuditLog(
        business_id=business_id,
        shop_id=req.shop_id,
        user_id=user.id,
        action="INVITATION_CREATED",
        entity_type="workspace_invitation",
        entity_id=inv.id,
    )
    db.add(audit)
    db.commit()

    return InvitationResponse(
        id=inv.id,
        business_id=inv.business_id,
        shop_id=inv.shop_id,
        email=inv.email,
        role_code=inv.role_code,
        status=inv.status,
        invitation_token=inv.invitation_token,
        expires_at=inv.expires_at.isoformat(),
        created_at=inv.created_at.isoformat(),
    )


@router.get("/{business_id}/invitations", response_model=List[InvitationResponse])
def list_workspace_invitations(
    business_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lists all invitations for the business. Requires owner or manager membership.
    """
    membership = (
        db.query(BusinessMembership)
        .filter_by(user_id=user.id, business_id=business_id, is_active=True)
        .first()
    )
    if not membership or membership.role_code not in ["owner", "manager", "accountant", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Insufficient permissions to view workspace invitations."
        )

    invitations = (
        db.query(WorkspaceInvitation)
        .filter_by(business_id=business_id)
        .order_by(WorkspaceInvitation.id.desc())
        .all()
    )
    return [
        InvitationResponse(
            id=i.id,
            business_id=i.business_id,
            shop_id=i.shop_id,
            email=i.email,
            role_code=i.role_code,
            status=i.status,
            invitation_token=i.invitation_token,
            expires_at=i.expires_at.isoformat(),
            created_at=i.created_at.isoformat(),
        )
        for i in invitations
    ]


@router.post("/invitations/{token}/accept")
def accept_workspace_invitation(
    token: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Accepts an invitation, adding the user to the workspace with the invited role.
    """
    inv = db.query(WorkspaceInvitation).filter_by(invitation_token=token, status="pending").first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found or already accepted.")

    # Timezone-safe check
    expiry = inv.expires_at
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if expiry < datetime.now(timezone.utc):
        inv.status = "expired"
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation has expired.")

    # Check if user is already a member
    existing = (
        db.query(BusinessMembership)
        .filter_by(user_id=user.id, business_id=inv.business_id)
        .first()
    )
    if existing:
        existing.role_code = inv.role_code
        existing.shop_id = inv.shop_id
        existing.is_active = True
    else:
        new_membership = BusinessMembership(
            user_id=user.id,
            business_id=inv.business_id,
            shop_id=inv.shop_id,
            role_code=inv.role_code,
            is_active=True,
        )
        db.add(new_membership)

    inv.status = "accepted"
    db.commit()

    return {
        "status": "success",
        "message": f"Successfully joined business workspace as {inv.role_code}.",
        "business_id": inv.business_id,
        "role_code": inv.role_code,
    }


@router.delete("/{business_id}/invitations/{invitation_id}")
def revoke_workspace_invitation(
    business_id: int,
    invitation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Revokes an active invitation.
    """
    membership = (
        db.query(BusinessMembership)
        .filter_by(user_id=user.id, business_id=business_id, is_active=True)
        .first()
    )
    if not membership or membership.role_code not in ["owner", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only owners and managers can revoke invitations."
        )

    inv = db.query(WorkspaceInvitation).filter_by(id=invitation_id, business_id=business_id).first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found.")

    inv.status = "revoked"
    db.commit()
    return {"status": "success", "message": "Invitation revoked."}

