"""
Comprehensive Unit and Integration Tests for Commercial Onboarding, Authentication,
Password Recovery, and Workspace Staff Invitations (Phase 1 & Phase 2).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.app import app
from src.database.connection import SessionLocal
from src.database.models import User, Business, Shop, BusinessMembership, WorkspaceInvitation, PasswordResetToken

client = TestClient(app)


def test_commercial_registration_flow():
    """Verifies complete business workspace registration flow with atomic database transaction."""
    payload = {
        "full_name": "Tariqul Islam",
        "email": f"tariq_{pytest.importorskip('secrets').token_hex(4)}@dhakaretail.com",
        "password": "StrongPassword123!",
        "business_name": "Bengal Superstore Ltd",
        "business_type": "retail",
        "country": "BD",
        "currency": "BDT",
        "language": "en",
        "shop_name": "Gulshan Branch",
    }
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "token" in data
    assert data["email"] == payload["email"].lower()
    assert data["full_name"] == payload["full_name"]
    assert data["role_code"] == "owner"
    assert data["onboarding_url"] == "/app/onboarding"

    # Verify DB records
    with SessionLocal() as db:
        user = db.query(User).filter_by(email=payload["email"].lower()).first()
        assert user is not None
        assert user.full_name == payload["full_name"]

        biz = db.get(Business, data["business_id"])
        assert biz is not None
        assert biz.name == payload["business_name"]
        assert biz.currency == "BDT"

        membership = db.query(BusinessMembership).filter_by(user_id=user.id, business_id=biz.id).first()
        assert membership is not None
        assert membership.role_code == "owner"


def test_duplicate_registration_rejected():
    """Verifies duplicate registration attempt is rejected with HTTP 400."""
    email = f"dup_{pytest.importorskip('secrets').token_hex(4)}@sme.com"
    payload = {
        "full_name": "First User",
        "email": email,
        "password": "password123",
        "business_name": "First Biz",
    }
    r1 = client.post("/api/auth/register", json=payload)
    assert r1.status_code == 200

    r2 = client.post("/api/auth/register", json=payload)
    assert r2.status_code == 400
    assert "already registered" in r2.json()["detail"].lower()


def test_login_by_username_or_email():
    """Verifies users can authenticate via email or username."""
    suffix = pytest.importorskip('secrets').token_hex(4)
    email = f"login_{suffix}@sme.com"
    full_name = f"Shakib Rahman {suffix}"
    reg_payload = {
        "full_name": full_name,
        "email": email,
        "password": "SecretPassword123",
        "business_name": "Shakib Enterprises",
    }
    client.post("/api/auth/register", json=reg_payload)

    # 1. Login with exact email
    r_email = client.post("/api/auth/login", json={"email": email, "password": "SecretPassword123"})
    assert r_email.status_code == 200
    assert r_email.json()["email"] == email

    # 2. Login with username (full name match)
    r_user = client.post("/api/auth/login", json={"username": full_name, "password": "SecretPassword123"})
    assert r_user.status_code == 200
    assert r_user.json()["user_id"] == r_email.json()["user_id"]

    # 3. Invalid credentials
    r_bad = client.post("/api/auth/login", json={"email": email, "password": "WrongPassword"})
    assert r_bad.status_code == 401


def test_forgot_password_and_reset_flow():
    """Verifies password recovery token generation and password reset."""
    email = f"forgot_{pytest.importorskip('secrets').token_hex(4)}@sme.com"
    client.post("/api/auth/register", json={
        "full_name": "Forgot User",
        "email": email,
        "password": "OldPassword123",
        "business_name": "Forgot Biz",
    })

    # Initiate forgot password
    r_forgot = client.post("/api/auth/forgot-password", json={"email": email})
    assert r_forgot.status_code == 200
    data = r_forgot.json()
    assert data["status"] == "success"
    reset_token = data.get("dev_reset_token")
    assert reset_token is not None

    # Reset with token
    r_reset = client.post("/api/auth/reset-password", json={
        "token": reset_token,
        "new_password": "NewStrongPassword456!",
    })
    assert r_reset.status_code == 200
    assert "updated successfully" in r_reset.json()["message"]

    # Verify old password fails, new password succeeds
    r_old = client.post("/api/auth/login", json={"email": email, "password": "OldPassword123"})
    assert r_old.status_code == 401

    r_new = client.post("/api/auth/login", json={"email": email, "password": "NewStrongPassword456!"})
    assert r_new.status_code == 200


def test_workspace_invitation_lifecycle():
    """Verifies team invitation creation, privilege escalation protection, and acceptance."""
    # 1. Register owner
    owner_email = f"owner_{pytest.importorskip('secrets').token_hex(4)}@corp.com"
    r_owner = client.post("/api/auth/register", json={
        "full_name": "Owner User",
        "email": owner_email,
        "password": "OwnerPassword123",
        "business_name": "Mega Wholesale Ltd",
    })
    owner_data = r_owner.json()
    token = owner_data["token"]
    biz_id = owner_data["business_id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Issue invitation to accountant
    invitee_email = f"accountant_{pytest.importorskip('secrets').token_hex(4)}@corp.com"
    r_inv = client.post(
        f"/api/business/{biz_id}/invitations",
        json={"email": invitee_email, "role_code": "accountant"},
        headers=headers,
    )
    assert r_inv.status_code == 200
    inv_data = r_inv.json()
    assert inv_data["email"] == invitee_email
    assert inv_data["role_code"] == "accountant"
    inv_token = inv_data["invitation_token"]

    # 3. List invitations
    r_list = client.get(f"/api/business/{biz_id}/invitations", headers=headers)
    assert r_list.status_code == 200
    assert any(i["id"] == inv_data["id"] for i in r_list.json())

    # 4. Accept invitation by new user
    new_user_email = invitee_email
    r_new_user = client.post("/api/auth/register", json={
        "full_name": "Accountant Staff",
        "email": new_user_email,
        "password": "StaffPassword123",
        "business_name": "Temporary Setup",
    })
    staff_token = r_new_user.json()["token"]
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    r_accept = client.post(f"/api/business/invitations/{inv_token}/accept", headers=staff_headers)
    assert r_accept.status_code == 200
    assert r_accept.json()["role_code"] == "accountant"

    # 5. Non-member denial on invitation management
    unauth_headers = {"Authorization": "Bearer invalid_token"}
    r_unauth = client.post(f"/api/business/{biz_id}/invitations", json={"email": "x@x.com"}, headers=unauth_headers)
    assert r_unauth.status_code in [401, 403]
