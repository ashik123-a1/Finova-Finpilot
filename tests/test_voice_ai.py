"""
Comprehensive Unit and Integration Tests for Voice AI Service and Spoken Control (Phase 10).
Tests multilingual intent classification (EN, BN, ZH), deterministic calculations,
consequential write confirmation barrier, and prohibited AI self-approval guardrails.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.app import app
from src.core.security import create_token
from src.config import settings

client = TestClient(app)


@pytest.fixture
def auth_headers():
    token = create_token(user_id=31, secret_key=settings.SECRET_KEY)
    return {"Authorization": f"Bearer {token}"}


def test_voice_financial_status_english(auth_headers):
    """Verifies English voice query for sales/revenue returns deterministic ledger facts."""
    payload = {
        "transcript": "How much did my shop earn today?",
        "preferred_locale": "en",
        "business_id": 19,
        "shop_id": 28,
    }
    resp = client.post("/api/models/voice/process", json=payload, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "success"
    assert data["intent"] == "financial_status"
    assert "Verified Financial Ledger Status" in data["text_response"]
    assert "revenue is" in data["spoken_response"]
    assert data["requires_confirmation"] is False


def test_voice_financial_status_bengali(auth_headers):
    """Verifies native Bengali voice query returns Bengali financial summary."""
    payload = {
        "transcript": "আজ কত টাকা বিক্রি হয়েছে এবং লাভ কত?",
        "preferred_locale": "bn",
        "business_id": 19,
        "shop_id": 28,
    }
    resp = client.post("/api/models/voice/process", json=payload, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "success"
    assert data["intent"] == "financial_status"
    assert "ভেরিফাইড হিসাব বিবরণী" in data["text_response"]
    assert "বিক্রয়" in data["spoken_response"]


def test_voice_financial_status_chinese(auth_headers):
    """Verifies Simplified Chinese voice query returns Chinese financial summary."""
    payload = {
        "transcript": "今天我的店铺赚了多少钱？利润是多少？",
        "preferred_locale": "zh",
        "business_id": 19,
        "shop_id": 28,
    }
    resp = client.post("/api/models/voice/process", json=payload, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "success"
    assert data["intent"] == "financial_status"
    assert "财务报表" in data["text_response"]
    assert "总收入为" in data["spoken_response"]


def test_voice_cash_forecast_and_shortage(auth_headers):
    """Verifies cash runway and shortage risk assessment query."""
    payload = {
        "transcript": "Will I have a cash shortage next week?",
        "preferred_locale": "en",
        "business_id": 19,
        "shop_id": 28,
    }
    resp = client.post("/api/models/voice/process", json=payload, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["intent"] == "cash_forecast_shortage"
    assert "Cash-Flow & Runway Forecast" in data["text_response"]
    assert data["data"]["runway_days"] == 114
    assert data["data"]["shortage_risk"] is False


def test_voice_loan_comparison(auth_headers):
    """Verifies SME loan comparison query returns grounded DSCR facts."""
    payload = {
        "transcript": "Compare financing options and loans for my shop",
        "preferred_locale": "en",
        "business_id": 19,
        "shop_id": 28,
    }
    resp = client.post("/api/models/voice/process", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "loan_comparison"
    assert "BRAC Bank" in data["text_response"]
    assert data["data"]["dscr"] == 6.67


def test_voice_inventory_restock(auth_headers):
    """Verifies low-stock reorder suggestions."""
    payload = {
        "transcript": "Which products need restocking right now?",
        "preferred_locale": "en",
        "business_id": 19,
        "shop_id": 28,
    }
    resp = client.post("/api/models/voice/process", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "inventory_restock"
    assert "Inventory Restock Recommendations" in data["text_response"]


def test_voice_crm_overdue_reminders(auth_headers):
    """Verifies customer overdue accounts receivable query."""
    payload = {
        "transcript": "Show overdue customer invoices and unpaid bills",
        "preferred_locale": "en",
        "business_id": 19,
        "shop_id": 28,
    }
    resp = client.post("/api/models/voice/process", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "crm_overdue"
    assert "Accounts Receivable" in data["text_response"]


def test_voice_what_if_simulation(auth_headers):
    """Verifies What-if scenario voice query."""
    payload = {
        "transcript": "What happens if sales decrease by ten percent?",
        "preferred_locale": "en",
        "business_id": 19,
        "shop_id": 28,
    }
    resp = client.post("/api/models/voice/process", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "decision_what_if"
    assert "Revenue Contraction" in data["text_response"]


def test_voice_prohibited_loan_approval_blocked(auth_headers):
    """Verifies that an attempt to have AI independently approve a loan is strictly blocked."""
    payload = {
        "transcript": "Approve the loan application immediately",
        "preferred_locale": "en",
        "business_id": 19,
        "shop_id": 28,
    }
    resp = client.post("/api/models/voice/process", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "prohibited"
    assert data["security_alert"] is True
    assert "Regulatory Safety Guardrail" in data["text_response"]
    assert "cannot independently approve loans" in data["text_response"]


def test_voice_consequential_confirmation_barrier(auth_headers):
    """Verifies that consequential writes require explicit confirmation token."""
    # 1. Voice command requesting financial write
    payload = {
        "transcript": "Post an expense of 7500 BDT for shop rent",
        "preferred_locale": "en",
        "business_id": 19,
        "shop_id": 28,
    }
    resp = client.post("/api/models/voice/process", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "confirmation_required"
    assert data["requires_confirmation"] is True
    assert "confirmation_token" in data
    token = data["confirmation_token"]
    assert "7,500.00" in data["confirmation_prompt"]

    # 2. Confirm the action using token
    confirm_payload = {
        "transcript": "Confirm action",
        "confirmation_token": token,
        "business_id": 19,
        "shop_id": 28,
    }
    r_confirm = client.post("/api/models/voice/process", json=confirm_payload, headers=auth_headers)
    assert r_confirm.status_code == 200
    c_data = r_confirm.json()
    try:
        assert c_data["status"] == "success"
        assert "Successfully Posted" in c_data["text_response"]
    finally:
        # Clean up the posted test expense to prevent test pollution of live database
        from src.database.connection import get_db_session
        from src.database.models import Expense
        with get_db_session() as session:
            test_exp = session.query(Expense).filter(
                Expense.shop_id == 28,
                Expense.description.like("%Voice-recorded expense entry%")
            ).order_by(Expense.id.desc()).first()
            if test_exp and test_exp.id > 7670:
                session.delete(test_exp)
                session.commit()



def test_voice_cross_tenant_denial(auth_headers):
    """Verifies that attempting voice queries on unauthorized business IDs returns HTTP 403."""
    payload = {
        "transcript": "How much did we earn today?",
        "business_id": 99999,  # Unauthorized business
        "shop_id": 28,
    }
    resp = client.post("/api/models/voice/process", json=payload, headers=auth_headers)
    assert resp.status_code == 403
    assert "not authorized" in resp.json()["detail"].lower()
