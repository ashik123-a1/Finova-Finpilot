"""
Business and Shop Management API Routes.
Provides multi-tenant shop listing, business profile retrieval, and shop metadata with isolation.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.database.connection import get_db
from src.database.models import User, Business, Shop, BusinessMembership, WorkspaceInvitation, AuditLog
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

