"""
Business and Shop Management API Routes.
Provides multi-tenant shop listing, business profile retrieval, and shop metadata with isolation.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.database.connection import get_db
from src.database.models import User, Business, Shop, BusinessMembership
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
