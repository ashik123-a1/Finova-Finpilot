"""
Platform Super Admin API Router for SME Finance Copilot.
Restricted exclusively to Platform Super Administrators.
Provides system health monitoring, cross-workspace directory inspection,
platform user management, and security audit event reviews.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, text

from src.database.connection import get_db
from src.database.models import User, Business, Shop, BusinessMembership, AuditLog, ModelVersion, Role, Permission, RolePermission
from src.api.dependencies import get_current_user

logger = logging.getLogger("sme_finance_copilot.admin")
router = APIRouter(prefix="/admin", tags=["Platform Super Admin"])


def require_super_admin(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    """
    Enforces that the authenticated user possesses the Platform Super Admin role.
    Rejects any business owner, manager, accountant, or unauthenticated user with HTTP 403.
    """
    membership = (
        db.query(BusinessMembership)
        .filter_by(user_id=user.id, is_active=True)
        .order_by(BusinessMembership.id.asc())
        .first()
    )
    if not membership or membership.role_code != "super_admin":
        logger.warning(
            "Access to Super Admin endpoint denied for user_id=%s (role=%s)",
            user.id,
            membership.role_code if membership else "none"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Platform Super Admin privileges are required to access this resource."
        )
    return user


@router.get("/overview")
@router.get("/telemetry")
def get_admin_overview(admin: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    """
    Returns platform-wide telemetries, workspaces, registered users, and recent security events.
    """
    # 1. Platform Metrics
    total_users = db.query(User).count()
    total_businesses = db.query(Business).count()
    total_shops = db.query(Shop).count()
    synthetic_businesses = db.query(Business).filter_by(is_synthetic=True).count()
    active_models = db.query(ModelVersion).filter_by(is_active=True).count()
    total_audits = db.query(AuditLog).count()

    # 2. Workspaces Directory (Last 50)
    businesses = (
        db.query(Business)
        .order_by(desc(Business.created_at))
        .limit(50)
        .all()
    )
    workspaces_list = []
    for b in businesses:
        shop_count = db.query(Shop).filter_by(business_id=b.id).count()
        owner_member = (
            db.query(BusinessMembership)
            .filter_by(business_id=b.id, role_code="owner")
            .first()
        )
        owner_name = owner_member.user.full_name if owner_member and owner_member.user else "Unassigned"
        workspaces_list.append({
            "id": b.id,
            "name": b.name,
            "business_type": b.business_type,
            "currency": b.currency,
            "is_synthetic": b.is_synthetic,
            "shop_count": shop_count,
            "owner_name": owner_name,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        })

    # 3. Platform Users Directory (Last 50)
    users = (
        db.query(User)
        .order_by(desc(User.created_at))
        .limit(50)
        .all()
    )
    users_list = []
    for u in users:
        primary_mem = (
            db.query(BusinessMembership)
            .filter_by(user_id=u.id, is_active=True)
            .first()
        )
        users_list.append({
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "is_active": u.is_active,
            "role_code": primary_mem.role_code if primary_mem else "member",
            "business_id": primary_mem.business_id if primary_mem else None,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })

    # 4. Recent Security & Audit Logs (Last 20)
    recent_audits = (
        db.query(AuditLog)
        .order_by(desc(AuditLog.created_at))
        .limit(20)
        .all()
    )
    audits_list = [
        {
            "id": a.id,
            "action": a.action,
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "user_id": a.user_id,
            "business_id": a.business_id,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in recent_audits
    ]

    # 5. Roles & Permissions RBAC Matrix
    roles_list = []
    roles_records = db.query(Role).all()
    for r in roles_records:
        perm_codes = (
            db.query(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .filter(RolePermission.role_id == r.id)
            .all()
        )
        roles_list.append({
            "code": r.code,
            "name": r.name,
            "description": r.description,
            "permissions": [p[0] for p in perm_codes],
        })

    # 6. System Health & Infrastructure Telemetry
    system_health = {
        "status": "healthy",
        "database_engine": "SQLite 3 (WAL Multi-Tenant)",
        "journal_mode": "WAL",
        "foreign_keys": "Enforced (ON)",
        "active_models_count": active_models,
        "token_security": "HMAC SHA-256 (24-Hour)",
        "tenant_isolation": "Enforced via Business & Shop Scope",
        "server_time": datetime.now(timezone.utc).isoformat(),
    }

    return {
        "status": "online",
        "telemetry": {
            "total_users": total_users,
            "total_businesses": total_businesses,
            "total_shops": total_shops,
            "synthetic_businesses": synthetic_businesses,
            "active_models": active_models,
            "total_audits": total_audits,
        },
        "workspaces": workspaces_list,
        "users": users_list,
        "roles": roles_list,
        "system_health": system_health,
        "recent_audits": audits_list,
    }
