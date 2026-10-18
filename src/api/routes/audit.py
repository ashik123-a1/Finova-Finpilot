"""
Audit Log Inspection API Routes.
Provides immutable, tamper-evident audit trails with shop isolation for compliance and security auditing.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from src.database.connection import get_db
from src.database.models import User, AuditLog
from src.api.dependencies import get_current_user, verify_shop_access_dependency

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


class AuditLogItem(BaseModel):
    id: int
    shop_id: Optional[int] = None
    user_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    old_values_json: Optional[str] = None
    new_values_json: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    shop_id: int
    total_count: int
    page: int
    limit: int
    total_pages: int
    logs: List[AuditLogItem]


@router.get("/logs", response_model=AuditLogResponse)
def list_audit_logs(
    shop_id: int = Query(..., description="Shop ID for tenant isolation"),
    action: Optional[str] = Query(None, description="Filter by action code, e.g. post_document, evaluate_loan_risk"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type, e.g. document, sale"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves paginated audit log events for a shop.
    Guarantees that staff/owners can only view audit logs for shops they belong to.
    """
    verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)

    query = db.query(AuditLog).filter(AuditLog.shop_id == shop_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    total_count = query.count()
    offset = (page - 1) * limit
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1

    records = (
        query.order_by(desc(AuditLog.id))
        .offset(offset)
        .limit(limit)
        .all()
    )

    logs_out = [
        AuditLogItem(
            id=r.id,
            shop_id=r.shop_id,
            user_id=r.user_id,
            action=r.action,
            entity_type=r.entity_type,
            entity_id=r.entity_id,
            old_values_json=r.old_values_json,
            new_values_json=r.new_values_json,
            ip_address=r.ip_address,
            created_at=r.created_at.isoformat() if r.created_at else "",
        )
        for r in records
    ]

    return AuditLogResponse(
        shop_id=shop_id,
        total_count=total_count,
        page=page,
        limit=limit,
        total_pages=total_pages,
        logs=logs_out,
    )
