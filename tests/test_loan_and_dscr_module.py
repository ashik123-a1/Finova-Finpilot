"""
Comprehensive Test Suite for SME Loan & DSCR Underwriting Module.
Tests financial precision, edge cases, bank product matching, dossier generation,
ReportLab PDF streaming, and multi-tenant isolation.
"""

from __future__ import annotations

import json
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from src.finance.calculator import FinancialCalculator
from src.database.models import (
    DemoBank,
    LoanProduct,
    LoanApplication,
    LoanScenario,
    AuditLog,
)
from src.core.security import create_token
from src.config import settings


def test_loan_calculator_emi_precision():
    """Tests deterministic reducing-balance EMI calculations vs zero-interest schemes."""
    # Standard 11.5% loan: 800,000 BDT over 24 months
    res = FinancialCalculator.calculate_loan_comparison(
        principal_minor=80000000,
        annual_interest_rate_pct=11.5,
        tenure_months=24,
        processing_fee_bps=100,
    )
    assert res.reducing_monthly_emi_minor == 3747225  # ~37,472.25 BDT
    assert res.reducing_total_payment_minor == 3747225 * 24
    assert res.reducing_total_interest_minor == (3747225 * 24) - 80000000
    assert res.processing_fee_minor == 800000

    # Zero-interest loan: 600,000 BDT over 12 months (0% promotional scheme)
    res_zero = FinancialCalculator.calculate_loan_comparison(
        principal_minor=60000000,
        annual_interest_rate_pct=0.0,
        tenure_months=12,
        processing_fee_bps=0,
    )
    assert res_zero.reducing_monthly_emi_minor == 5000000  # Exactly 50,000 BDT/month
    assert res_zero.reducing_total_interest_minor == 0
    assert res_zero.reducing_total_payment_minor == 60000000

    # Negative and zero inputs must raise ValueError
    with pytest.raises(ValueError):
        FinancialCalculator.calculate_loan_comparison(
            principal_minor=-100,
            annual_interest_rate_pct=10.0,
            tenure_months=12,
        )
    with pytest.raises(ValueError):
        FinancialCalculator.calculate_loan_comparison(
            principal_minor=100000,
            annual_interest_rate_pct=10.0,
            tenure_months=0,
        )


def test_loan_calculator_dscr_guards():
    """Tests DSCR calculation edge cases, zero debt, and zero NOI guards."""
    # Healthy coverage: 250,000 NOI vs 37,472 debt service
    dscr = FinancialCalculator.calculate_dscr(
        monthly_net_operating_income_minor=25000000,
        monthly_debt_service_minor=3747225,
    )
    assert dscr == 6.67

    # Zero debt service: returns infinity
    dscr_zero_debt = FinancialCalculator.calculate_dscr(
        monthly_net_operating_income_minor=25000000,
        monthly_debt_service_minor=0,
    )
    assert dscr_zero_debt == float("inf")

    # Tight coverage: 50,000 NOI vs 40,000 debt service
    dscr_tight = FinancialCalculator.calculate_dscr(
        monthly_net_operating_income_minor=5000000,
        monthly_debt_service_minor=4000000,
    )
    assert dscr_tight == 1.25


@pytest.fixture
def seeded_bank_products(db_session):
    """Seeds test demo bank products with strict criteria."""
    bank = DemoBank(name="BRAC Bank Test", code="TEST_BRAC", is_synthetic=True)
    db_session.add(bank)
    db_session.flush()

    p1 = LoanProduct(
        bank_id=bank.id,
        name="Anonya SME Term Loan",
        min_amount_minor=10000000,    # 100k BDT
        max_amount_minor=250000000,   # 2.5M BDT
        min_tenure_months=12,
        max_tenure_months=36,
        annual_interest_rate_bps=1150,  # 11.5%
        interest_calc_type="reducing_balance",
        processing_fee_bps=100,
        eligibility_criteria_json=json.dumps({
            "min_dscr": 1.25,
            "supported_purposes": ["working_capital", "branch"],
            "collateral": "Stock Hypothecation",
            "disbursement": "48h Rapid",
        }),
        is_synthetic=True,
    )
    p2 = LoanProduct(
        bank_id=bank.id,
        name="Micro Seasonal Advance",
        min_amount_minor=5000000,     # 50k BDT
        max_amount_minor=50000000,    # 500k BDT
        min_tenure_months=3,
        max_tenure_months=12,
        annual_interest_rate_bps=1050,  # 10.5%
        interest_calc_type="reducing_balance",
        processing_fee_bps=100,
        eligibility_criteria_json=json.dumps({
            "min_dscr": 1.20,
            "supported_purposes": ["working_capital"],
            "collateral": "Personal Guarantee",
            "disbursement": "24h Express",
        }),
        is_synthetic=True,
    )
    db_session.add_all([p1, p2])
    db_session.commit()
    return bank, p1, p2


def test_loan_underwriting_data_endpoint(test_client, seeded_shop_context, seeded_bank_products, db_session):
    """Tests GET /api/finance/loan-underwriting-data with reactive calculation and bank matching."""
    user1 = seeded_shop_context["user1"]
    shop1 = seeded_shop_context["shop1"]
    token = create_token(user1.id, settings.SECRET_KEY)

    headers = {"Authorization": f"Bearer {token}"}

    # Query within bounds
    res = test_client.get(
        f"/api/finance/loan-underwriting-data?shop_id={shop1.id}&principal_minor=80000000&tenure_months=24&annual_interest_rate_pct=11.5&loan_purpose=working_capital&monthly_noi_minor=25000000",
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["shop_id"] == shop1.id
    assert data["calculated_terms"]["suitability_verdict"] == "PRIME APPROVAL"
    assert data["calculated_terms"]["projected_dscr"] == 6.67

    # Check product match results
    products = data["products"]
    anonya = next((p for p in products if p["product_name"] == "Anonya SME Term Loan"), None)
    micro = next((p for p in products if p["product_name"] == "Micro Seasonal Advance"), None)

    assert anonya is not None
    assert anonya["match_status"] == "MATCHED"

    # Micro advance max facility is 500k, our request is 800k -> EXCEEDS FACILITY
    assert micro is not None
    assert micro["match_status"] == "EXCEEDS FACILITY"


def test_loan_underwriting_purpose_and_dscr_rejections(test_client, seeded_shop_context, seeded_bank_products):
    """Tests bank product rejection when loan purpose is unsupported or DSCR is below policy."""
    user1 = seeded_shop_context["user1"]
    shop1 = seeded_shop_context["shop1"]
    token = create_token(user1.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Purpose mismatch: "equipment" is not supported by Anonya or Micro Advance
    res = test_client.get(
        f"/api/finance/loan-underwriting-data?shop_id={shop1.id}&principal_minor=80000000&tenure_months=24&annual_interest_rate_pct=11.5&loan_purpose=equipment&monthly_noi_minor=25000000",
        headers=headers,
    )
    assert res.status_code == 200
    anonya = next((p for p in res.json()["products"] if p["product_name"] == "Anonya SME Term Loan"), None)
    assert anonya["match_status"] == "PURPOSE INELIGIBLE"

    # 2. Insufficient DSCR: NOI is low (10,000 BDT) vs 37,472 EMI -> DSCR 0.27x
    res_low_dscr = test_client.get(
        f"/api/finance/loan-underwriting-data?shop_id={shop1.id}&principal_minor=80000000&tenure_months=24&annual_interest_rate_pct=11.5&loan_purpose=working_capital&monthly_noi_minor=1000000",
        headers=headers,
    )
    assert res_low_dscr.status_code == 200
    anonya_low = next((p for p in res_low_dscr.json()["products"] if p["product_name"] == "Anonya SME Term Loan"), None)
    assert anonya_low["match_status"] == "INSUFFICIENT DSCR"
    assert res_low_dscr.json()["calculated_terms"]["suitability_verdict"] == "HIGH DEBT RISK"


def test_loan_packet_generation_and_persistence(test_client, seeded_shop_context, seeded_bank_products, db_session):
    """Tests POST /api/finance/loan-packet/generate, database persistence, and debounce protection."""
    user1 = seeded_shop_context["user1"]
    shop1 = seeded_shop_context["shop1"]
    token = create_token(user1.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "shop_id": shop1.id,
        "requested_amount_minor": 80000000,
        "tenure_months": 24,
        "annual_interest_rate_pct": 11.5,
        "loan_purpose": "working_capital",
        "existing_monthly_debt_minor": 0,
        "monthly_noi_minor": 25000000,
    }

    res = test_client.post("/api/finance/loan-packet/generate", json=payload, headers=headers)
    assert res.status_code == 200
    packet = res.json()

    app_num = packet["application_number"]
    assert app_num.startswith(f"SME-PKT-{shop1.id}-")
    assert packet["is_synthetic"] is True
    assert "download_url" in packet
    assert len(packet["stress_tests"]) == 3
    assert len(packet["required_documents"]) >= 4

    # Verify database persistence in loan_applications table
    saved_app = db_session.query(LoanApplication).filter_by(application_number=app_num).first()
    assert saved_app is not None
    assert saved_app.shop_id == shop1.id
    assert saved_app.status == "demo_assessed"
    assert saved_app.is_synthetic is True

    # Verify persistence in loan_scenarios table
    saved_scenario = db_session.query(LoanScenario).filter_by(shop_id=shop1.id).first()
    assert saved_scenario is not None
    assert saved_scenario.requested_amount_minor == 80000000

    # Verify AuditLog recorded
    audit_entry = db_session.query(AuditLog).filter_by(action="generate_loan_packet", shop_id=shop1.id).first()
    assert audit_entry is not None

    # Idempotency / Debounce test: repeat request immediately (within 15s)
    res_repeat = test_client.post("/api/finance/loan-packet/generate", json=payload, headers=headers)
    assert res_repeat.status_code == 200
    assert res_repeat.json()["application_number"] == app_num


def test_loan_packet_pdf_download(test_client, seeded_shop_context, seeded_bank_products, db_session):
    """Tests GET /api/finance/loan-packet/{application_number}/download returns ReportLab PDF."""
    user1 = seeded_shop_context["user1"]
    shop1 = seeded_shop_context["shop1"]
    token = create_token(user1.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}

    # Generate packet first
    gen_res = test_client.post(
        "/api/finance/loan-packet/generate",
        json={
            "shop_id": shop1.id,
            "requested_amount_minor": 50000000,
            "tenure_months": 12,
            "annual_interest_rate_pct": 10.5,
            "loan_purpose": "working_capital",
            "monthly_noi_minor": 20000000,
        },
        headers=headers,
    )
    app_num = gen_res.json()["application_number"]

    # Download PDF
    dl_res = test_client.get(f"/api/finance/loan-packet/{app_num}/download", headers=headers)
    assert dl_res.status_code == 200
    assert dl_res.headers["content-type"] == "application/pdf"
    assert f'filename="Loan_Packet_{app_num}.pdf"' in dl_res.headers["content-disposition"]
    assert dl_res.content.startswith(b"%PDF-")
    assert len(dl_res.content) > 1000

    # Non-existent application number returns 404
    dl_404 = test_client.get("/api/finance/loan-packet/NON_EXISTENT_REF/download", headers=headers)
    assert dl_404.status_code == 404


def test_multi_tenant_isolation(test_client, seeded_shop_context, seeded_bank_products):
    """Tests that User 2 cannot access or download Shop 1's loan underwriting dossiers."""
    user1 = seeded_shop_context["user1"]
    user2 = seeded_shop_context["user2"]
    shop1 = seeded_shop_context["shop1"]
    shop2 = seeded_shop_context["shop2"]

    token1 = create_token(user1.id, settings.SECRET_KEY)
    token2 = create_token(user2.id, settings.SECRET_KEY)

    # User 1 generates packet for Shop 1
    gen_res = test_client.post(
        "/api/finance/loan-packet/generate",
        json={
            "shop_id": shop1.id,
            "requested_amount_minor": 75000000,
            "tenure_months": 24,
            "annual_interest_rate_pct": 11.0,
            "loan_purpose": "working_capital",
            "monthly_noi_minor": 30000000,
        },
        headers={"Authorization": f"Bearer {token1}"},
    )
    app_num = gen_res.json()["application_number"]

    # User 2 attempts to download User 1's Shop 1 dossier -> 403 Forbidden
    unauthorized_dl = test_client.get(
        f"/api/finance/loan-packet/{app_num}/download",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert unauthorized_dl.status_code == 403

    # User 2 attempts to query underwriting data for Shop 1 -> 403 Forbidden
    unauthorized_data = test_client.get(
        f"/api/finance/loan-underwriting-data?shop_id={shop1.id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert unauthorized_data.status_code == 403
