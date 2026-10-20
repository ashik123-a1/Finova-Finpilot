"""
Persistent Notifications API Router for SME Finance Copilot.
Provides multi-tenant, user-isolated notification feed, unread counting,
mark-as-read mutations, real business event integration, and deduplication.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.database.connection import get_db, SessionLocal
from src.database.models import Notification, User, utc_now
from src.api.dependencies import get_current_user

logger = logging.getLogger("sme_finance_copilot.notifications")
router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationOut(BaseModel):
    id: int
    user_id: int
    business_id: Optional[int] = None
    shop_id: Optional[int] = None
    title: str
    message: str
    notification_type: str = "info"
    severity: str = "info"
    action_url: Optional[str] = None
    is_read: bool = False
    read_at: Optional[datetime] = None
    created_at: datetime
    dedup_key: Optional[str] = None

    class Config:
        from_attributes = True


class UnreadCountResponse(BaseModel):
    unread_count: int
    user_id: int


class MarkReadResponse(BaseModel):
    status: str = "success"
    notification_id: int
    is_read: bool


class MarkAllReadResponse(BaseModel):
    status: str = "success"
    marked_count: int


class CreateNotificationRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    message: str = Field(..., min_length=2)
    notification_type: str = "info"  # info, warning, action_required, financial_alert, ocr_review, system
    severity: str = "info"  # info, warning, error, success
    action_url: Optional[str] = None
    business_id: Optional[int] = None
    shop_id: Optional[int] = None
    dedup_key: Optional[str] = None


def create_persistent_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: str = "info",
    severity: str = "info",
    action_url: Optional[str] = None,
    business_id: Optional[int] = None,
    shop_id: Optional[int] = None,
    dedup_key: Optional[str] = None,
) -> Optional[Notification]:
    """
    Thread-safe, deduplicated helper for dispatching notifications from background workers,
    OCR gates, and ledger posting routines.
    """
    try:
        if dedup_key:
            existing = (
                db.query(Notification)
                .filter_by(user_id=user_id, dedup_key=dedup_key)
                .first()
            )
            if existing:
                logger.debug("Skipping duplicate notification with dedup_key '%s'", dedup_key)
                return existing

        notif = Notification(
            user_id=user_id,
            business_id=business_id,
            shop_id=shop_id,
            title=title,
            message=message,
            notification_type=notification_type,
            severity=severity,
            action_url=action_url,
            is_read=False,
            dedup_key=dedup_key,
            created_at=utc_now(),
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif
    except Exception as e:
        logger.error("Failed to create notification: %s", e)
        db.rollback()
        return None


@router.get("", response_model=List[NotificationOut])
def list_notifications(
    unread_only: bool = Query(False, description="Filter for unread notifications only"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the authenticated user's notification feed, ordered by creation time descending.
    Enforces user isolation: recipients can only retrieve notifications addressed to them.
    """
    query = db.query(Notification).filter(Notification.user_id == user.id)
    if unread_only:
        query = query.filter(Notification.is_read == False)

    return (
        query.order_by(desc(Notification.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the real-time unread notification count for the authenticated recipient.
    Used by the topbar bell and sidebar badge polling routines.
    """
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user.id, Notification.is_read == False)
        .count()
    )
    return UnreadCountResponse(unread_count=count, user_id=user.id)


@router.patch("/{notification_id}/read", response_model=MarkReadResponse)
def mark_notification_read(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Marks a single notification as read.
    Validates that the notification belongs to the authenticated user (Tenant / User Isolation).
    """
    notif = db.get(Notification, notification_id)
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found."
        )

    if notif.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized to access this notification."
        )

    notif.is_read = True
    notif.read_at = utc_now()
    db.commit()

    return MarkReadResponse(
        status="success",
        notification_id=notif.id,
        is_read=True,
    )


@router.post("/mark-all-read", response_model=MarkAllReadResponse)
def mark_all_notifications_read(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Marks all unread notifications for the authenticated user as read in an atomic transaction.
    """
    now = utc_now()
    updated = (
        db.query(Notification)
        .filter(Notification.user_id == user.id, Notification.is_read == False)
        .update({Notification.is_read: True, Notification.read_at: now}, synchronize_session=False)
    )
    db.commit()

    return MarkAllReadResponse(
        status="success",
        marked_count=updated,
    )


@router.post("", response_model=NotificationOut, status_code=status.HTTP_201_CREATED)
def create_notification_endpoint(
    req: CreateNotificationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Creates a notification for the current user or verified workspace recipient.
    Deduplicates based on dedup_key.
    """
    notif = create_persistent_notification(
        db=db,
        user_id=user.id,
        title=req.title,
        message=req.message,
        notification_type=req.notification_type,
        severity=req.severity,
        action_url=req.action_url,
        business_id=req.business_id,
        shop_id=req.shop_id,
        dedup_key=req.dedup_key,
    )
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not persist notification record."
        )
    return notif
