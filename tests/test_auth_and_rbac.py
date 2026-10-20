"""
Automated Test Suite for Authentication, Public Registration, 
Selectable Demo Personas, and Platform Super Admin RBAC Authorization.
"""

import pytest
from fastapi.testclient import TestClient
from src.database.models import User, Business, Shop, BusinessMembership
from src.core.security import hash_password, create_token
from src.config import settings


def test_public_registration_success(test_client: TestClient, db_session):
    """Verifies that public registration transactionally provisions user, workspace, and owner role."""
    payload = {
        "full_name": "Rahim Khan",
        "email": "rahim.khan@dhakafresh.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "business_name": "Dhaka Fresh Market",
        "business_type": "retail",
        "currency": "BDT",
        "shop_name": "Gulshan Flagship",
    }
    resp = test_client.post("/api/auth/register", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["email"] == "rahim.khan@dhakafresh.com"
    assert data["role_code"] == "owner"
    assert data["redirect_url"] == "/app/onboarding"
    assert "token" in data
    assert data["business_id"] is not None
    assert data["shop_id"] is not None

    # Check cookies
    cookies = resp.cookies
    assert "sme_auth_token" in cookies
    assert cookies["sme_role"] == "owner"

    # Verify DB persistence
    u = db_session.query(User).filter_by(email="rahim.khan@dhakafresh.com").first()
    assert u is not None
    assert u.full_name == "Rahim Khan"

    b = db_session.query(Business).filter_by(id=data["business_id"]).first()
    assert b is not None
    assert b.name == "Dhaka Fresh Market"
    assert b.currency == "BDT"

    m = db_session.query(BusinessMembership).filter_by(user_id=u.id).first()
    assert m is not None
    assert m.role_code == "owner"


def test_public_registration_prohibits_super_admin(test_client: TestClient):
    """Ensures public registration strictly rejects any attempt to self-assign super_admin privileges."""
    payload = {
        "full_name": "Rogue Attacker",
        "email": "rogue@attacker.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "business_name": "Rogue Corp",
        "role": "super_admin",
    }
    resp = test_client.post("/api/auth/register", json=payload)
    assert resp.status_code == 403
    assert "Super Admin cannot be created via public registration" in resp.json()["detail"]


def test_public_registration_duplicate_email(test_client: TestClient):
    """Ensures duplicate email registration is rejected with 400 Bad Request."""
    payload = {
        "full_name": "First User",
        "email": "duplicate@test.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "business_name": "First Corp",
    }
    resp1 = test_client.post("/api/auth/register", json=payload)
    assert resp1.status_code == 200

    resp2 = test_client.post("/api/auth/register", json=payload)
    assert resp2.status_code == 400
    assert "already registered" in resp2.json()["detail"]


def test_public_registration_validation_errors(test_client: TestClient):
    """Tests password mismatch and minimum length validation."""
    # Mismatch
    resp_mismatch = test_client.post("/api/auth/register", json={
        "full_name": "Test User",
        "email": "mismatch@test.com",
        "password": "Password123!",
        "confirm_password": "DifferentPassword123!",
        "business_name": "Mismatch Corp",
    })
    assert resp_mismatch.status_code == 400
    assert "Passwords do not match" in resp_mismatch.json()["detail"]

    # Short password
    resp_short = test_client.post("/api/auth/register", json={
        "full_name": "Test User",
        "email": "short@test.com",
        "password": "123",
        "confirm_password": "123",
        "business_name": "Short Corp",
    })
    assert resp_short.status_code in [400, 422]


def test_standard_login_flow(test_client: TestClient, db_session):
    """Verifies credential validation and session cookie setting on login."""
    # Register user
    u = User(
        email="loginuser@company.com",
        hashed_password=hash_password("SecurePass123!"),
        full_name="Login Test User",
        is_active=True
    )
    db_session.add(u)
    db_session.flush()

    b = Business(name="Login Business", business_type="services")
    db_session.add(b)
    db_session.flush()

    m = BusinessMembership(user_id=u.id, business_id=b.id, role_code="owner")
    db_session.add(m)
    db_session.commit()

    # Success
    resp = test_client.post("/api/auth/login", json={
        "email": "loginuser@company.com",
        "password": "SecurePass123!"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "loginuser@company.com"
    assert data["role_code"] == "owner"
    assert "token" in data
    assert resp.cookies.get("sme_auth_token") is not None

    # Invalid password
    resp_bad_pw = test_client.post("/api/auth/login", json={
        "email": "loginuser@company.com",
        "password": "WrongPassword!"
    })
    assert resp_bad_pw.status_code == 401

    # Non-existent user
    resp_bad_user = test_client.post("/api/auth/login", json={
        "email": "nonexistent@company.com",
        "password": "WrongPassword!"
    })
    assert resp_bad_user.status_code == 401


def test_selectable_demo_login_all_personas(test_client: TestClient):
    """Verifies that all 7 canonical demo personas can be authenticated via 1-click demo login."""
    personas = [
        ("owner", "owner", "/app/dashboard"),
        ("manager", "manager", "/app/dashboard"),
        ("accountant", "accountant", "/app/dashboard"),
        ("sales", "sales", "/app/dashboard"),
        ("inventory", "inventory", "/app/dashboard"),
        ("auditor", "auditor", "/app/dashboard"),
        ("super_admin", "super_admin", "/app/admin"),
    ]

    for persona_key, expected_role, expected_redirect in personas:
        resp = test_client.post("/api/auth/demo-login", json={"persona": persona_key})
        assert resp.status_code == 200, f"Demo login failed for persona '{persona_key}': {resp.text}"
        data = resp.json()
        assert data["role_code"] == expected_role, f"Expected role '{expected_role}', got '{data['role_code']}'"
        assert data["redirect_url"] == expected_redirect, f"Expected redirect '{expected_redirect}', got '{data['redirect_url']}'"
        assert "token" in data
        assert resp.cookies.get("sme_auth_token") is not None
        assert resp.cookies.get("sme_role") == expected_role


def test_demo_login_unknown_persona(test_client: TestClient):
    """Rejects unknown persona requests with 400 Bad Request."""
    resp = test_client.post("/api/auth/demo-login", json={"persona": "hacker_overlord"})
    assert resp.status_code == 400
    assert "Unknown demo persona" in resp.json()["detail"]


def test_super_admin_rbac_protection(test_client: TestClient, db_session):
    """Verifies strict RBAC: non-superadmin users are denied access to /api/admin/overview with 403."""
    # 1. Unauthenticated request
    resp_unauth = test_client.get("/api/admin/overview")
    assert resp_unauth.status_code in [401, 403]

    # 2. Business Owner accessing Admin endpoint -> 403 Forbidden
    owner_login = test_client.post("/api/auth/demo-login", json={"persona": "owner"})
    owner_token = owner_login.json()["token"]

    resp_forbidden = test_client.get(
        "/api/admin/overview",
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert resp_forbidden.status_code == 403
    assert "Platform Super Admin privileges are required" in resp_forbidden.json()["detail"]

    # 3. Super Admin accessing Admin endpoint -> 200 OK
    admin_login = test_client.post("/api/auth/demo-login", json={"persona": "super_admin"})
    admin_token = admin_login.json()["token"]

    resp_admin = test_client.get(
        "/api/admin/overview",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp_admin.status_code == 200
    admin_data = resp_admin.json()
    assert admin_data["status"] == "online"
    assert "telemetry" in admin_data
    assert "workspaces" in admin_data
    assert "users" in admin_data
    assert "recent_audits" in admin_data


def test_auth_me_and_logout(test_client: TestClient):
    """Tests /api/auth/me profile inspection and /api/auth/logout cookie clearing."""
    login_resp = test_client.post("/api/auth/demo-login", json={"persona": "manager"})
    token = login_resp.json()["token"]

    me_resp = test_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["role_code"] == "manager"
    assert me_data["is_super_admin"] is False
    assert "permissions" in me_data

    # Logout
    logout_resp = test_client.post("/api/auth/logout")
    assert logout_resp.status_code == 200
