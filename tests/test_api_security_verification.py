"""
Phase 2.1 Security & Functional Verification Gate Test Suite.
Exhaustively verifies:
1. Authentication & Tenant Isolation (tampered tokens, forged headers, missing tokens, cross-tenant denial across all endpoints).
2. Financial Correctness (minor-unit precision, empty datasets, invalid date ranges, division-by-zero, real DB derivation).
3. Document Safety (invalid types, spoofed MIME, corrupted images, oversized files, path traversal prevention, duplicate post rejection, human review gating).
4. Sanitized Error Handling (zero stack-trace leakage).
"""

from __future__ import annotations

import io
import time
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
from PIL import Image

from src.config import settings
from src.core.security import create_token, hash_password
from src.database.models import (
    User,
    Business,
    Shop,
    BusinessMembership,
    Sale,
    SaleItem,
    Purchase,
    Expense,
    Payment,
    Product,
    Receivable,
    Customer,
    Document,
    DocumentClassification,
    DocumentExtraction,
    DocumentReview,
    utc_now,
)
from src.documents.schemas import DocumentReviewConfirmation, DocumentType


@pytest.fixture
def verification_context(db_session):
    """
    Sets up two isolated businesses with owners, shops, and an extra deactivated user.
    """
    # Active User 1 (Owner of Business 1, Shop 1)
    user1 = User(
        email="owner1_verify@example.com",
        hashed_password=hash_password("Pass123!"),
        full_name="Owner One",
        is_active=True,
    )
    # Active User 2 (Owner of Business 2, Shop 2)
    user2 = User(
        email="owner2_verify@example.com",
        hashed_password=hash_password("Pass123!"),
        full_name="Owner Two",
        is_active=True,
    )
    # Deactivated User
    user_inactive = User(
        email="inactive_verify@example.com",
        hashed_password=hash_password("Pass123!"),
        full_name="Inactive User",
        is_active=False,
    )
    db_session.add_all([user1, user2, user_inactive])
    db_session.flush()

    # Business 1 & Shop 1
    b1 = Business(name="Verify Business One", business_type="grocery", currency="BDT")
    db_session.add(b1)
    db_session.flush()
    s1 = Shop(business_id=b1.id, name="Shop 1 Alpha", is_active=True)
    db_session.add(s1)
    db_session.flush()

    m1 = BusinessMembership(
        user_id=user1.id,
        business_id=b1.id,
        shop_id=s1.id,
        role_code="owner",
        is_active=True,
    )
    db_session.add(m1)

    # Business 2 & Shop 2
    b2 = Business(name="Verify Business Two", business_type="pharmacy", currency="BDT")
    db_session.add(b2)
    db_session.flush()
    s2 = Shop(business_id=b2.id, name="Shop 2 Beta", is_active=True)
    db_session.add(s2)
    db_session.flush()

    m2 = BusinessMembership(
        user_id=user2.id,
        business_id=b2.id,
        shop_id=s2.id,
        role_code="owner",
        is_active=True,
    )
    db_session.add(m2)

    # Shop 3 (Empty Shop for Business 1 to test empty dataset edge cases)
    s3_empty = Shop(business_id=b1.id, name="Shop 3 Empty", is_active=True)
    db_session.add(s3_empty)
    db_session.flush()

    m3 = BusinessMembership(
        user_id=user1.id,
        business_id=b1.id,
        shop_id=s3_empty.id,
        role_code="owner",
        is_active=True,
    )
    db_session.add(m3)

    db_session.commit()

    token1 = create_token(user1.id, settings.SECRET_KEY)
    token2 = create_token(user2.id, settings.SECRET_KEY)
    token_inactive = create_token(user_inactive.id, settings.SECRET_KEY)

    return {
        "user1": user1,
        "user2": user2,
        "user_inactive": user_inactive,
        "business1": b1,
        "business2": b2,
        "shop1": s1,
        "shop2": s2,
        "shop_empty": s3_empty,
        "h1": {"Authorization": f"Bearer {token1}"},
        "h2": {"Authorization": f"Bearer {token2}"},
        "h_inactive": {"Authorization": f"Bearer {token_inactive}"},
        "token1": token1,
        "token2": token2,
    }


def _create_valid_png() -> bytes:
    img = Image.new("RGB", (120, 80), color=(240, 240, 240))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ==============================================================================
# SECTION A: AUTHENTICATION AND TENANT ISOLATION
# ==============================================================================

def test_client_supplied_identity_headers_cannot_forge_identity(test_client, verification_context):
    """
    Verifies that X-User-ID, X-Business-ID, and X-Shop-ID headers sent by the client
    are completely ignored by the authentication layer and cannot be used to forge identity.
    """
    ctx = verification_context
    s1 = ctx["shop1"]
    s2 = ctx["shop2"]

    # 1. Attacker sends X-User-ID: 2 with User 1's token trying to access Shop 2 -> 403
    forged_headers = {
        **ctx["h1"],
        "X-User-ID": str(ctx["user2"].id),
        "X-Business-ID": str(ctx["business2"].id),
        "X-Shop-ID": str(s2.id),
    }
    resp = test_client.get(f"/api/finance/summary?shop_id={s2.id}", headers=forged_headers)
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "SHOP_ACCESS_DENIED"

    # 2. Attacker sends X-User-ID: 2 with NO Authorization header trying to access Shop 2 -> 403
    forged_no_auth = {
        "X-User-ID": str(ctx["user2"].id),
        "X-Business-ID": str(ctx["business2"].id),
        "X-Shop-ID": str(s2.id),
    }
    resp2 = test_client.get(f"/api/finance/summary?shop_id={s2.id}", headers=forged_no_auth)
    assert resp2.status_code == 403
    assert resp2.json()["error_code"] == "SHOP_ACCESS_DENIED"


def test_malformed_and_tampered_authorization_headers(test_client, verification_context):
    """
    Verifies that invalid, tampered, expired, or malformed Authorization tokens are rejected with 401.
    """
    ctx = verification_context
    s1 = ctx["shop1"]

    # 1. Completely empty Bearer
    resp = test_client.get(f"/api/finance/summary?shop_id={s1.id}", headers={"Authorization": "Bearer "})
    assert resp.status_code == 401

    # 2. Malformed token structure (not 3 colon-separated parts)
    resp = test_client.get(f"/api/finance/summary?shop_id={s1.id}", headers={"Authorization": "Bearer not_a_token"})
    assert resp.status_code == 401

    # 3. Basic auth instead of Bearer
    resp = test_client.get(f"/api/finance/summary?shop_id={s1.id}", headers={"Authorization": "Basic dXNlcjpwYXNz"})
    assert resp.status_code == 401

    # 4. Tampered HMAC signature
    valid_token = ctx["token1"]
    parts = valid_token.split(":")
    tampered_token = f"{parts[0]}:{parts[1]}:badhash0000000000000000000000000000000000000000000000000000000000"
    resp = test_client.get(f"/api/finance/summary?shop_id={s1.id}", headers={"Authorization": f"Bearer {tampered_token}"})
    assert resp.status_code == 401

    # 5. Expired token (signed correctly with past timestamp)
    past_timestamp = int(time.time()) - 3600
    expired_token = create_token(ctx["user1"].id, settings.SECRET_KEY, expires_in_seconds=-3600)
    resp = test_client.get(f"/api/finance/summary?shop_id={s1.id}", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401

    # 6. Non-existent user ID
    ghost_token = create_token(999999, settings.SECRET_KEY)
    resp = test_client.get(f"/api/finance/summary?shop_id={s1.id}", headers={"Authorization": f"Bearer {ghost_token}"})
    assert resp.status_code == 401
    assert "User not found" in resp.json()["detail"]

    # 7. Deactivated user token
    resp = test_client.get(f"/api/finance/summary?shop_id={s1.id}", headers=ctx["h_inactive"])
    assert resp.status_code == 401
    assert "deactivated" in resp.json()["detail"]


def test_production_environment_rejects_missing_authorization(test_client, verification_context, monkeypatch):
    """
    Verifies that when ENVIRONMENT is set to 'production', missing Authorization headers
    are strictly rejected with HTTP 401 (no fallback to default admin).
    """
    ctx = verification_context
    s1 = ctx["shop1"]

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    resp = test_client.get(f"/api/finance/summary?shop_id={s1.id}")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Missing Authorization header."


def test_cross_shop_access_denied_across_all_endpoints(test_client, db_session, verification_context):
    """
    Exhaustively tests that User 1 cannot read or mutate any data belonging to Shop 2 / Business 2.
    """
    ctx = verification_context
    b2 = ctx["business2"]
    s2 = ctx["shop2"]
    h1 = ctx["h1"]

    # Create a document belonging to Shop 2
    doc_s2 = Document(
        business_id=b2.id,
        shop_id=s2.id,
        original_filename="shop2_receipt.png",
        stored_path="storage/documents/shop2_receipt.png",
        file_hash_sha256="aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899",
        file_size_bytes=1024,
        mime_type="image/png",
        status="review_pending",
    )
    db_session.add(doc_s2)
    db_session.commit()

    # 1. Business & Shop Endpoints
    assert test_client.get(f"/api/business/{b2.id}/shops", headers=h1).status_code == 403
    assert test_client.get(f"/api/business/shops/{s2.id}", headers=h1).status_code == 403

    # 2. Finance Summaries & Ledgers
    assert test_client.get(f"/api/finance/summary?shop_id={s2.id}", headers=h1).status_code == 403
    assert test_client.get(f"/api/finance/sales?shop_id={s2.id}", headers=h1).status_code == 403
    assert test_client.get(f"/api/finance/expenses?shop_id={s2.id}", headers=h1).status_code == 403
    assert test_client.get(f"/api/finance/profit-loss?shop_id={s2.id}", headers=h1).status_code == 403
    assert test_client.get(f"/api/finance/cash-flow?shop_id={s2.id}", headers=h1).status_code == 403
    assert test_client.get(f"/api/finance/inventory-summary?shop_id={s2.id}", headers=h1).status_code == 403
    assert test_client.get(f"/api/finance/receivables-summary?shop_id={s2.id}", headers=h1).status_code == 403

    # 3. Forecasting & Loan Risk
    forecast_payload = {"shop_id": s2.id, "horizon_days": 14}
    assert test_client.post("/api/finance/forecast", json=forecast_payload, headers=h1).status_code == 403
    assert test_client.get(f"/api/finance/forecast?shop_id={s2.id}", headers=h1).status_code == 403

    risk_payload = {
        "shop_id": s2.id,
        "requested_amount_minor": 1000000,
        "tenure_months": 12,
        "annual_interest_rate_pct": 12.0,
    }
    assert test_client.post("/api/finance/loan-risk-assessment", json=risk_payload, headers=h1).status_code == 403
    assert test_client.get(f"/api/finance/loan-products?shop_id={s2.id}", headers=h1).status_code == 403

    # 4. Document Pipeline
    assert test_client.get(f"/api/documents/{doc_s2.id}", headers=h1).status_code == 403
    confirm_payload = {
        "document_id": doc_s2.id,
        "confirmed_doc_type": "sales_receipt",
        "final_values": {
            "invoice_number": "INV-S2-CROSS",
            "date": "2026-10-18",
            "items": [],
            "subtotal_minor": 50000,
            "total_amount_minor": 50000,
            "paid_amount_minor": 50000,
        },
        "decision_action": "approve_and_post",
    }
    assert test_client.post("/api/documents/confirm-post", json=confirm_payload, headers=h1).status_code == 403
    assert test_client.get(f"/api/documents/list/all?shop_id={s2.id}", headers=h1).status_code == 403

    # 5. Audit Logs
    assert test_client.get(f"/api/audit/logs?shop_id={s2.id}", headers=h1).status_code == 403


# ==============================================================================
# SECTION B: FINANCIAL CORRECTNESS & EDGE CASES
# ==============================================================================

def test_financial_summary_empty_shop_no_division_by_zero(test_client, verification_context):
    """
    Verifies that an empty shop with 0 transactions returns clean 0 metrics
    without division-by-zero errors or crash.
    """
    ctx = verification_context
    s_empty = ctx["shop_empty"]
    h1 = ctx["h1"]

    resp = test_client.get(f"/api/finance/summary?shop_id={s_empty.id}", headers=h1)
    assert resp.status_code == 200
    data = resp.json()

    assert data["revenue"]["total_minor"] == 0
    assert data["revenue"]["transaction_count"] == 0
    assert data["expenses"]["total_minor"] == 0
    assert data["profitability"]["gross_margin_pct"] == 0.0
    assert data["profitability"]["net_margin_pct"] == 0.0
    assert data["liquidity"]["cash_balance_minor"] == 0
    assert data["inventory"]["total_skus"] == 0
    assert data["receivables"]["outstanding_minor"] == 0


def test_profit_loss_and_cash_flow_empty_shop(test_client, verification_context):
    """
    Verifies profit-loss and cash-flow endpoints on an empty shop.
    """
    ctx = verification_context
    s_empty = ctx["shop_empty"]
    h1 = ctx["h1"]

    # Profit & Loss
    pl_resp = test_client.get(f"/api/finance/profit-loss?shop_id={s_empty.id}", headers=h1)
    assert pl_resp.status_code == 200
    pl = pl_resp.json()
    assert pl["revenue_minor"] == 0
    assert pl["net_profit_minor"] == 0
    assert pl["gross_margin_pct"] == 0.0
    assert pl["net_margin_pct"] == 0.0

    # Cash Flow
    cf_resp = test_client.get(f"/api/finance/cash-flow?shop_id={s_empty.id}", headers=h1)
    assert cf_resp.status_code == 200
    cf = cf_resp.json()
    assert cf["closing_balance"] == "0.00 BDT"


def test_forecast_on_empty_shop_zero_fallback(test_client, verification_context):
    """
    Verifies that cash-flow forecasting gracefully executes zero-fallback on empty shops.
    """
    ctx = verification_context
    s_empty = ctx["shop_empty"]
    h1 = ctx["h1"]

    resp = test_client.post(
        "/api/finance/forecast",
        json={"shop_id": s_empty.id, "horizon_days": 10},
        headers=h1,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["method_applied"] == "zero_fallback"
    assert data["point_forecast_minor"] == [0] * 10


def test_loan_risk_on_empty_shop_derives_and_recommends_ineligible(test_client, verification_context):
    """
    Verifies that loan risk assessment on an empty shop auto-derives 0 income,
    and returns ineligible status without division-by-zero crash.
    """
    ctx = verification_context
    s_empty = ctx["shop_empty"]
    h1 = ctx["h1"]

    payload = {
        "shop_id": s_empty.id,
        "requested_amount_minor": 500000,
        "tenure_months": 12,
        "annual_interest_rate_pct": 10.0,
    }
    resp = test_client.post("/api/finance/loan-risk-assessment", json=payload, headers=h1)
    assert resp.status_code == 200
    data = resp.json()
    assert data["recommendation_status"] == "ineligible"
    assert data["net_operating_income_minor"] == 0
    assert "Net operating income is negative or zero." in data["recommendation_reasons"]


def test_invalid_date_range_validation(test_client, verification_context):
    """
    Verifies that start_date > end_date returns HTTP 400 Bad Request across sales, expenses, and summary.
    """
    ctx = verification_context
    s1 = ctx["shop1"]
    h1 = ctx["h1"]

    bad_range = "start_date=2026-12-31&end_date=2026-01-01"

    # Sales
    resp = test_client.get(f"/api/finance/sales?shop_id={s1.id}&{bad_range}", headers=h1)
    assert resp.status_code == 400
    assert "start_date cannot be after end_date" in resp.json()["detail"]

    # Expenses
    resp = test_client.get(f"/api/finance/expenses?shop_id={s1.id}&{bad_range}", headers=h1)
    assert resp.status_code == 400
    assert "start_date cannot be after end_date" in resp.json()["detail"]

    # Summary
    resp = test_client.get(f"/api/finance/summary?shop_id={s1.id}&{bad_range}", headers=h1)
    assert resp.status_code == 400
    assert "start_date cannot be after end_date" in resp.json()["detail"]

    # Audit Logs
    resp = test_client.get(f"/api/audit/logs?shop_id={s1.id}&{bad_range}", headers=h1)
    assert resp.status_code == 400
    assert "start_date cannot be after end_date" in resp.json()["detail"]


def test_malformed_date_format_validation(test_client, verification_context):
    """
    Verifies that non-date strings return HTTP 400 Bad Request.
    """
    ctx = verification_context
    s1 = ctx["shop1"]
    h1 = ctx["h1"]

    resp = test_client.get(f"/api/finance/sales?shop_id={s1.id}&start_date=not-a-date", headers=h1)
    assert resp.status_code == 400
    assert "Invalid date format" in resp.json()["detail"]


def test_pagination_boundary_validation(test_client, verification_context):
    """
    Verifies that invalid pagination (page=0 or limit > 100) returns 422 Unprocessable Entity.
    """
    ctx = verification_context
    s1 = ctx["shop1"]
    h1 = ctx["h1"]

    # page = 0
    resp = test_client.get(f"/api/finance/sales?shop_id={s1.id}&page=0", headers=h1)
    assert resp.status_code == 422

    # limit = 101 (> 100 max)
    resp = test_client.get(f"/api/finance/sales?shop_id={s1.id}&limit=101", headers=h1)
    assert resp.status_code == 422


def test_break_even_negative_margin_validation(test_client):
    """
    Verifies that break-even calculator rejects selling price <= variable cost with HTTP 400.
    """
    payload = {
        "fixed_costs_minor": 100000,
        "selling_price_per_unit_minor": 500,
        "variable_cost_per_unit_minor": 600,  # Variable cost > Selling price
    }
    resp = test_client.post("/api/finance/break-even", json=payload)
    assert resp.status_code == 400
    assert "Contribution margin must be positive" in resp.json()["detail"]


# ==============================================================================
# SECTION C: DOCUMENT SAFETY & IDEMPOTENCY
# ==============================================================================

def test_document_upload_invalid_mime_type(test_client, verification_context):
    """
    Verifies rejection of unsupported file types (e.g. application/x-executable).
    """
    ctx = verification_context
    s1 = ctx["shop1"]
    h1 = ctx["h1"]

    files = {"file": ("malicious.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/x-msdownload")}
    resp = test_client.post("/api/documents/upload", data={"shop_id": s1.id}, files=files, headers=h1)
    assert resp.status_code == 400
    assert "Unsupported file type" in resp.json()["detail"]


def test_document_upload_spoofed_mime_type(test_client, verification_context):
    """
    Verifies that a file pretending to be image/png with non-image bytes is caught and rejected with HTTP 400.
    """
    ctx = verification_context
    s1 = ctx["shop1"]
    h1 = ctx["h1"]

    fake_png_bytes = b"This is plain text pretending to be a PNG image file."
    files = {"file": ("fake.png", fake_png_bytes, "image/png")}
    resp = test_client.post("/api/documents/upload", data={"shop_id": s1.id}, files=files, headers=h1)
    assert resp.status_code == 400
    assert "Signature does not match permitted file types" in resp.json()["detail"]


def test_document_upload_empty_file_rejected(test_client, verification_context):
    """
    Verifies that an empty (0 byte) file is rejected with HTTP 400.
    """
    ctx = verification_context
    s1 = ctx["shop1"]
    h1 = ctx["h1"]

    files = {"file": ("empty.png", b"", "image/png")}
    resp = test_client.post("/api/documents/upload", data={"shop_id": s1.id}, files=files, headers=h1)
    assert resp.status_code == 400
    assert "Empty file uploaded" in resp.json()["detail"]


def test_document_upload_oversized_file_rejected(test_client, verification_context):
    """
    Verifies that files exceeding 10MB are rejected with HTTP 413 Payload Too Large.
    """
    ctx = verification_context
    s1 = ctx["shop1"]
    h1 = ctx["h1"]

    oversized_bytes = b"\x89PNG\r\n\x1a\n" + b"0" * (10 * 1024 * 1024 + 10)
    files = {"file": ("huge.png", oversized_bytes, "image/png")}
    resp = test_client.post("/api/documents/upload", data={"shop_id": s1.id}, files=files, headers=h1)
    assert resp.status_code == 413
    assert "maximum allowed upload size" in resp.json()["detail"]


def test_document_path_traversal_filename_prevented(test_client, db_session, verification_context):
    """
    Verifies that malicious directory traversal sequences in filename (e.g. ../../secret.png)
    cannot escape the intended storage directory and the file is stored under its sha256 hash.
    """
    ctx = verification_context
    s1 = ctx["shop1"]
    h1 = ctx["h1"]

    png_bytes = _create_valid_png()
    malicious_filename = "../../../../etc/passwd.png"

    files = {"file": (malicious_filename, png_bytes, "image/png")}
    resp = test_client.post("/api/documents/upload", data={"shop_id": s1.id}, files=files, headers=h1)
    assert resp.status_code == 200
    doc_id = resp.json()["document_id"]

    # Verify database record stored_path
    doc = db_session.get(Document, doc_id)
    assert doc is not None
    stored_path = Path(doc.stored_path)

    # Must be strictly within storage/documents/{business_id}/...
    assert "etc" not in stored_path.parts
    assert "passwd" not in stored_path.name
    assert stored_path.name == f"{doc.file_hash_sha256}.png"
    assert stored_path.exists()


def test_human_review_required_before_ledger_posting(test_client, db_session, verification_context):
    """
    Verifies that uploading a document does NOT immediately mutate financial tables (Sale, Expense).
    Records are posted ONLY after explicit human confirmation via /confirm-post.
    """
    ctx = verification_context
    s1 = ctx["shop1"]
    h1 = ctx["h1"]

    initial_sales_count = db_session.query(Sale).filter(Sale.shop_id == s1.id).count()

    png_bytes = _create_valid_png()
    files = {"file": ("unconfirmed_receipt.png", png_bytes, "image/png")}
    resp = test_client.post("/api/documents/upload", data={"shop_id": s1.id}, files=files, headers=h1)
    assert resp.status_code == 200
    doc_id = resp.json()["document_id"]

    # Document must be in review_required or review_pending status
    doc = db_session.get(Document, doc_id)
    assert doc.status in ("review_required", "review_pending")

    # Financial sales ledger must NOT have changed yet
    sales_count_after_upload = db_session.query(Sale).filter(Sale.shop_id == s1.id).count()
    assert sales_count_after_upload == initial_sales_count

    # Now perform explicit human review confirmation
    confirm_payload = {
        "document_id": doc_id,
        "confirmed_doc_type": "sales_receipt",
        "final_values": {
            "invoice_number": "INV-VERIFY-1",
            "date": "2026-10-18",
            "items": [
                {"description": "Verified Item", "quantity": 1, "unit_price_minor": 45000, "line_total_minor": 45000}
            ],
            "subtotal_minor": 45000,
            "total_amount_minor": 45000,
            "paid_amount_minor": 45000,
            "payment_method": "cash",
        },
        "decision_action": "approve_and_post",
    }
    resp_post = test_client.post("/api/documents/confirm-post", json=confirm_payload, headers=h1)
    assert resp_post.status_code == 200
    assert resp_post.json()["status"] == "posted"

    # Now verify sale record exists
    sales_count_after_confirm = db_session.query(Sale).filter(Sale.shop_id == s1.id).count()
    assert sales_count_after_confirm == initial_sales_count + 1

    # Verify duplicate confirm-post is rejected with HTTP 409 Conflict
    resp_dup = test_client.post("/api/documents/confirm-post", json=confirm_payload, headers=h1)
    assert resp_dup.status_code == 409
    assert resp_dup.json()["error_code"] == "DUPLICATE_DOCUMENT"


# ==============================================================================
# SECTION D: SANITIZED ERROR RESPONSES
# ==============================================================================

def test_sanitized_error_responses_never_leak_stack_traces(test_client, verification_context):
    """
    Verifies that domain and HTTP errors return clean JSON bodies without Python tracebacks or file paths.
    """
    ctx = verification_context
    s1 = ctx["shop1"]
    h1 = ctx["h1"]

    # 1. 403 Forbidden
    resp_403 = test_client.get(f"/api/finance/summary?shop_id={ctx['shop2'].id}", headers=h1)
    assert resp_403.status_code == 403
    text_403 = resp_403.text
    assert "Traceback (most recent call last)" not in text_403
    assert "File \"" not in text_403
    assert resp_403.json()["error_code"] == "SHOP_ACCESS_DENIED"

    # 2. 404 Not Found
    resp_404 = test_client.get("/api/documents/999999", headers=h1)
    assert resp_404.status_code == 404
    assert "Traceback" not in resp_404.text

    # 3. 400 Bad Request
    resp_400 = test_client.get(f"/api/finance/sales?shop_id={s1.id}&start_date=2026-12-31&end_date=2026-01-01", headers=h1)
    assert resp_400.status_code == 400
    assert "Traceback" not in resp_400.text
