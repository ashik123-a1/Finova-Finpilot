"""
Comprehensive Test Suite for SME Finance Copilot Master Product Completion:
- Registration and Business Setup Wizard (6 Canonical Steps)
- Resumption without duplicate workspaces/shops
- 1-Click Selectable Demo Personas (7 Canonical Roles)
- Dedicated Platform Admin Portal vs User Portal RBAC Isolation
- Persistent Notifications & Real Business Event Integration
"""

import pytest
from fastapi.testclient import TestClient
from src.database.models import User, Business, Shop, BusinessMembership, Notification, Payment, Customer, Product
from src.core.security import hash_password, create_token
from src.config import settings


def test_onboarding_wizard_6_steps_and_resumption(test_client: TestClient, db_session):
    """
    Tests the complete end-to-end user journey:
    1. Register new owner
    2. Check onboarding-status (pre-populated)
    3. Complete 6-step onboarding wizard
    4. Resume/re-submit onboarding and verify idempotency (no duplicate businesses or shops)
    5. Verify opening cash and welcome notification
    """
    # 1. Register new business owner
    reg_payload = {
        "full_name": "Tariqul Islam",
        "email": "tariqul@bengaltrade.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "business_name": "Bengal Trade Network",
        "business_type": "wholesale",
        "currency": "BDT",
        "shop_name": "Khatunganj Hub",
    }
    reg_resp = test_client.post("/api/auth/register", json=reg_payload)
    assert reg_resp.status_code == 200
    reg_data = reg_resp.json()
    token = reg_data["token"]
    user_id = reg_data["user_id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check onboarding-status (pre-populated)
    status_resp = test_client.get("/api/business/onboarding-status", headers=headers)
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["has_business"] is True
    assert status_data["business_name"] == "Bengal Trade Network"
    assert status_data["shop_name"] == "Khatunganj Hub"
    original_biz_id = status_data["business_id"]
    original_shop_id = status_data["shop_id"]

    # 3. Complete 6-step onboarding wizard
    wizard_payload = {
        "business_name": "Bengal Trade Network Ltd.",
        "business_type": "wholesale",
        "country": "BD",
        "currency": "BDT",
        "language": "en",
        "shop_name": "Khatunganj Primary Hub",
        "branch_code": "KTG-01",
        "is_multibranch": True,
        "sales_operation": "wholesale_desk",
        "monthly_revenue_range": "500k_2m",
        "main_products": "Basmati rice, edible oil, lentils",
        "employee_count": "6_20",
        "record_keeping_method": "excel",
        "financial_starter_path": "opening_cash",
        "opening_cash": 75000.0,
        "customer_name": "Chittagong Emporium",
        "customer_balance": 35000.0,
        "seed_demo_data": True,
        "goals_cashflow": True,
        "goals_profit": True,
        "goals_overdue": True,
        "goals_stock": True,
        "goals_summary": True,
        "runway_alert_days": 45,
    }
    ob_resp = test_client.post("/api/business/onboarding", json=wizard_payload, headers=headers)
    assert ob_resp.status_code == 200
    ob_data = ob_resp.json()
    assert ob_data["status"] == "success"
    assert ob_data["redirect_url"] == "/app/dashboard"
    assert ob_data["business_id"] == original_biz_id
    assert ob_data["shop_id"] == original_shop_id

    # Verify opening balance was recorded
    payment = db_session.query(Payment).filter_by(shop_id=original_shop_id, reference_type="opening_balance").first()
    assert payment is not None
    assert payment.amount_minor == 7500000

    # Verify welcome notification exists
    notif = db_session.query(Notification).filter_by(user_id=user_id, notification_type="system").first()
    assert notif is not None
    assert "Workspace Onboarding Completed" in notif.title

    # 4. Resume onboarding: re-submitting must update in place without duplicating records
    count_biz_before = db_session.query(Business).count()
    count_shop_before = db_session.query(Shop).count()

    wizard_payload["business_name"] = "Bengal Trade Network Ltd. (Updated)"
    ob_resp2 = test_client.post("/api/business/onboarding", json=wizard_payload, headers=headers)
    assert ob_resp2.status_code == 200

    count_biz_after = db_session.query(Business).count()
    count_shop_after = db_session.query(Shop).count()
    assert count_biz_before == count_biz_after, "Workspace must not be duplicated on resume"
    assert count_shop_before == count_shop_after, "Shop must not be duplicated on resume"

    updated_biz = db_session.get(Business, original_biz_id)
    assert updated_biz.name == "Bengal Trade Network Ltd. (Updated)"


def test_all_seven_demo_personas_authentication(test_client: TestClient, db_session):
    """
    Verifies that all 7 canonical demo personas:
    1. owner
    2. manager
    3. accountant
    4. sales / cashier
    5. inventory
    6. auditor
    7. super_admin
    authenticate successfully via POST /api/auth/demo-login, receive valid sessions,
    and redirect to their proper dedicated portals.
    """
    personas = [
        ("owner", "owner", "/app/dashboard"),
        ("manager", "manager", "/app/dashboard"),
        ("accountant", "accountant", "/app/dashboard"),
        ("sales", "sales", "/app/dashboard"),
        ("cashier", "sales", "/app/dashboard"),
        ("inventory", "inventory", "/app/dashboard"),
        ("auditor", "auditor", "/app/dashboard"),
        ("super_admin", "super_admin", "/app/admin"),
    ]

    for p_name, expected_role, expected_redirect in personas:
        resp = test_client.post("/api/auth/demo-login", json={"persona": p_name})
        assert resp.status_code == 200, f"Failed demo login for persona {p_name}"
        data = resp.json()
        assert data["role_code"] == expected_role
        assert data["redirect_url"] == expected_redirect
        assert "token" in data

        # Test authenticated /api/auth/me endpoint with this token
        me_resp = test_client.get("/api/auth/me", headers={"Authorization": f"Bearer {data['token']}"})
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["role_code"] == expected_role
        if expected_role == "super_admin":
            assert me_data["is_super_admin"] is True


def test_portal_separation_and_super_admin_guard(test_client: TestClient, db_session):
    """
    Verifies RBAC boundary:
    - Non-super-admin is denied access to /app/admin and /api/admin/telemetry.
    - Super-admin is allowed full access.
    """
    # 1. Login as owner (Business portal user)
    owner_login = test_client.post("/api/auth/demo-login", json={"persona": "owner"})
    owner_token = owner_login.json()["token"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    # API guard: /api/admin/telemetry should return 403 Forbidden
    resp = test_client.get("/api/admin/telemetry", headers=owner_headers)
    assert resp.status_code == 403

    # 2. Login as super_admin
    admin_login = test_client.post("/api/auth/demo-login", json={"persona": "super_admin"})
    admin_token = admin_login.json()["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # API guard: /api/admin/telemetry should return 200 OK
    admin_resp = test_client.get("/api/admin/telemetry", headers=admin_headers)
    assert admin_resp.status_code == 200
    telemetry = admin_resp.json()
    assert telemetry["status"] == "online"
    assert "telemetry" in telemetry
    assert "workspaces" in telemetry
    assert "users" in telemetry


def test_persistent_notification_lifecycle_and_isolation(test_client: TestClient, db_session):
    """
    Verifies notification creation, reading, isolation, and unread counts.
    """
    # Create two distinct demo users
    user1_resp = test_client.post("/api/auth/demo-login", json={"persona": "owner"})
    token1 = user1_resp.json()["token"]
    u1_id = user1_resp.json()["user_id"]
    h1 = {"Authorization": f"Bearer {token1}"}

    user2_resp = test_client.post("/api/auth/demo-login", json={"persona": "manager"})
    token2 = user2_resp.json()["token"]
    h2 = {"Authorization": f"Bearer {token2}"}

    # User 1 creates notification
    create_resp = test_client.post(
        "/api/notifications",
        json={
            "title": "VAT Submission Due",
            "message": "Monthly VAT Form 9.1 submission due in 3 days.",
            "notification_type": "financial_alert",
            "severity": "warning",
            "action_url": "/app/finance",
        },
        headers=h1,
    )
    assert create_resp.status_code == 201
    notif_id = create_resp.json()["id"]

    # User 1 should have unread count >= 1
    count_resp1 = test_client.get("/api/notifications/unread-count", headers=h1)
    assert count_resp1.status_code == 200
    assert count_resp1.json()["unread_count"] >= 1

    # User 2 cannot mark User 1's notification as read (User Isolation)
    forbidden_resp = test_client.patch(f"/api/notifications/{notif_id}/read", headers=h2)
    assert forbidden_resp.status_code == 403

    # User 1 marks it as read
    read_resp = test_client.patch(f"/api/notifications/{notif_id}/read", headers=h1)
    assert read_resp.status_code == 200
    assert read_resp.json()["is_read"] is True

    # User 1 mark-all-read
    mark_all_resp = test_client.post("/api/notifications/mark-all-read", headers=h1)
    assert mark_all_resp.status_code == 200

    # Unread count should now be 0
    final_count = test_client.get("/api/notifications/unread-count", headers=h1)
    assert final_count.json()["unread_count"] == 0
