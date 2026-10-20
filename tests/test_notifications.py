"""
Automated Test Suite for Persistent Notifications Database System.
Verifies notification persistence, unread counter calculation, single mark read,
mark all read, user/tenant isolation, and deduplication.
"""

import pytest
from fastapi.testclient import TestClient
from src.database.models import User, Notification
from src.core.security import hash_password, create_token
from src.config import settings
from src.api.routes.notifications import create_persistent_notification


def test_notification_creation_and_deduplication(test_client: TestClient, db_session):
    """Verifies that notifications are stored persistently and respect deduplication keys."""
    user = User(
        email="notif_test@domain.com",
        hashed_password=hash_password("Pass123!"),
        full_name="Notif User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    token = create_token(user.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create first notification
    notif1 = create_persistent_notification(
        db=db_session,
        user_id=user.id,
        title="OCR Invoice Processed",
        message="Invoice #1002 scanned and awaiting ledger review.",
        notification_type="ocr_review",
        severity="warning",
        dedup_key="ocr_inv_1002",
    )
    assert notif1 is not None
    assert notif1.id is not None
    assert notif1.is_read is False

    # 2. Attempt duplicate creation with same dedup_key
    notif2 = create_persistent_notification(
        db=db_session,
        user_id=user.id,
        title="OCR Invoice Processed (Duplicate)",
        message="Same invoice scanned again.",
        notification_type="ocr_review",
        severity="warning",
        dedup_key="ocr_inv_1002",
    )
    # Deduplication ensures same notification is returned and no new record is inserted
    assert notif2.id == notif1.id
    total_count = db_session.query(Notification).filter_by(user_id=user.id).count()
    assert total_count == 1


def test_unread_count_calculation(test_client: TestClient, db_session):
    """Verifies unread counter calculation matches actual unread database records."""
    user = User(
        email="unread_counter@domain.com",
        hashed_password=hash_password("Pass123!"),
        full_name="Counter User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    token = create_token(user.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}

    # Initially 0 unread
    resp0 = test_client.get("/api/notifications/unread-count", headers=headers)
    assert resp0.status_code == 200
    assert resp0.json()["unread_count"] == 0

    # Add 2 unread notifications
    create_persistent_notification(db_session, user.id, "Alert 1", "Msg 1")
    create_persistent_notification(db_session, user.id, "Alert 2", "Msg 2")

    resp2 = test_client.get("/api/notifications/unread-count", headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["unread_count"] == 2


def test_mark_single_read_and_user_isolation(test_client: TestClient, db_session):
    """Verifies that marking read updates status, and users cannot modify other users' notifications."""
    u1 = User(email="user1_notif@test.com", hashed_password=hash_password("Pass123!"), full_name="User One")
    u2 = User(email="user2_notif@test.com", hashed_password=hash_password("Pass123!"), full_name="User Two")
    db_session.add_all([u1, u2])
    db_session.commit()

    token1 = create_token(u1.id, settings.SECRET_KEY)
    token2 = create_token(u2.id, settings.SECRET_KEY)

    n1 = create_persistent_notification(db_session, u1.id, "User 1 Alert", "Message for user 1")
    n2 = create_persistent_notification(db_session, u2.id, "User 2 Alert", "Message for user 2")

    # User 1 attempts to mark User 2's notification as read -> 403 Forbidden
    resp_hack = test_client.patch(
        f"/api/notifications/{n2.id}/read",
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert resp_hack.status_code == 403
    assert "Unauthorized to access this notification" in resp_hack.json()["detail"]

    # User 1 marks own notification as read -> 200 OK
    resp_ok = test_client.patch(
        f"/api/notifications/{n1.id}/read",
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert resp_ok.status_code == 200
    assert resp_ok.json()["is_read"] is True

    # Verify DB update
    db_session.refresh(n1)
    assert n1.is_read is True
    assert n1.read_at is not None


def test_mark_all_read(test_client: TestClient, db_session):
    """Verifies atomic mark-all-read updates all unread notifications for the caller only."""
    u1 = User(email="markall1@test.com", hashed_password=hash_password("Pass123!"), full_name="User All 1")
    u2 = User(email="markall2@test.com", hashed_password=hash_password("Pass123!"), full_name="User All 2")
    db_session.add_all([u1, u2])
    db_session.commit()

    token1 = create_token(u1.id, settings.SECRET_KEY)
    token2 = create_token(u2.id, settings.SECRET_KEY)

    # 3 notifications for User 1, 1 for User 2
    create_persistent_notification(db_session, u1.id, "U1 A", "Msg A")
    create_persistent_notification(db_session, u1.id, "U1 B", "Msg B")
    create_persistent_notification(db_session, u1.id, "U1 C", "Msg C")
    n_u2 = create_persistent_notification(db_session, u2.id, "U2 A", "Msg for U2")

    # User 1 marks all read
    resp = test_client.post("/api/notifications/mark-all-read", headers={"Authorization": f"Bearer {token1}"})
    assert resp.status_code == 200
    assert resp.json()["marked_count"] == 3

    # User 1 unread count is now 0
    u1_count = test_client.get("/api/notifications/unread-count", headers={"Authorization": f"Bearer {token1}"}).json()
    assert u1_count["unread_count"] == 0

    # User 2 notification is still unread
    u2_count = test_client.get("/api/notifications/unread-count", headers={"Authorization": f"Bearer {token2}"}).json()
    assert u2_count["unread_count"] == 1


def test_notifications_filter_unread_only(test_client: TestClient, db_session):
    """Verifies unread_only query parameter filters correctly."""
    user = User(email="filter_notifs@test.com", hashed_password=hash_password("Pass123!"), full_name="Filter User")
    db_session.add(user)
    db_session.commit()

    token = create_token(user.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}

    n_unread = create_persistent_notification(db_session, user.id, "Unread One", "Still unread")
    n_read = create_persistent_notification(db_session, user.id, "Read One", "Already read")
    n_read.is_read = True
    db_session.commit()

    # All
    resp_all = test_client.get("/api/notifications", headers=headers)
    assert resp_all.status_code == 200
    assert len(resp_all.json()) == 2

    # Unread only
    resp_unread = test_client.get("/api/notifications?unread_only=true", headers=headers)
    assert resp_unread.status_code == 200
    unread_items = resp_unread.json()
    assert len(unread_items) == 1
    assert unread_items[0]["id"] == n_unread.id
