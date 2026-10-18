"""
Integration Test Suite for SME Finance Copilot Backend API.
Tests all 8 prioritized workflows:
1. Health and subsystem status endpoints (/health, /api/health, /).
2. Business and shop management with multi-tenant isolation.
3. Sales and expense retrieval with date range filtering and pagination.
4. Cash-flow forecasting with ML autoregression and statistical fallback.
5. Financing-option comparison and explainable loan risk assessment.
6. Document upload, OCR routing, human-review gating, and duplicate-post prevention.
7. Inventory and receivables financial summaries.
8. Audit logging and sanitized error responses without stack traces.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone, timedelta
import pytest
from PIL import Image

from src.core.security import create_token
from src.config import settings
from src.database.models import (
    Sale,
    SaleItem,
    Expense,
    Product,
    Receivable,
    Customer,
    CashMovement,
    DemoBank,
    LoanProduct,
    utc_now,
)
from src.documents.schemas import DocumentReviewConfirmation, DocumentType


@pytest.fixture
def auth_headers(seeded_shop_context):
    """Provides authorization headers for User 1 and User 2."""
    user1 = seeded_shop_context["user1"]
    user2 = seeded_shop_context["user2"]
    token1 = create_token(user1.id, settings.SECRET_KEY)
    token2 = create_token(user2.id, settings.SECRET_KEY)
    return {
        "user1": {"Authorization": f"Bearer {token1}"},
        "user2": {"Authorization": f"Bearer {token2}"},
    }


def _create_mock_receipt_image_bytes() -> bytes:
    """Generates a small valid PNG receipt image in memory."""
    img = Image.new("RGB", (200, 100), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ==============================================================================
# 1. Health and Status Endpoints
# ==============================================================================

def test_health_and_root_endpoints(test_client):
    """Verifies that root and health endpoints return healthy status and schema details."""
    # Root
    resp = test_client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "online"
    assert data["app"] == settings.APP_NAME

    # Health
    resp = test_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True
    assert data["tables_count"] > 10

    # API-prefixed health alias
    resp2 = test_client.get("/api/health")
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "healthy"


# ==============================================================================
# 2. Business and Shop Management with Isolation
# ==============================================================================

def test_business_and_shop_endpoints_isolation(test_client, seeded_shop_context, auth_headers):
    """Verifies user can only list shops and businesses they own or belong to."""
    b1 = seeded_shop_context["business1"]
    b2 = seeded_shop_context["business2"]
    s1 = seeded_shop_context["shop1"]
    s2 = seeded_shop_context["shop2"]

    h1 = auth_headers["user1"]
    h2 = auth_headers["user2"]

    # User 1 lists businesses
    resp = test_client.get("/api/business/list", headers=h1)
    assert resp.status_code == 200
    biz_list = resp.json()
    biz_ids = [b["id"] for b in biz_list]
    assert b1.id in biz_ids
    assert b2.id not in biz_ids  # Isolation: cannot see Business 2

    # User 1 lists shops for Business 1
    resp = test_client.get(f"/api/business/{b1.id}/shops", headers=h1)
    assert resp.status_code == 200
    shop_ids = [s["id"] for s in resp.json()]
    assert s1.id in shop_ids

    # User 1 attempts cross-tenant access to Business 2 shops -> 403
    resp = test_client.get(f"/api/business/{b2.id}/shops", headers=h1)
    assert resp.status_code == 403

    # User 1 accesses Shop 1 details
    resp = test_client.get(f"/api/business/shops/{s1.id}", headers=h1)
    assert resp.status_code == 200
    assert resp.json()["name"] == s1.name

    # User 1 attempts cross-tenant access to Shop 2 details -> 403
    resp = test_client.get(f"/api/business/shops/{s2.id}", headers=h1)
    assert resp.status_code == 403


# ==============================================================================
# 3. Financial Summary Dashboard
# ==============================================================================

def test_financial_summary_endpoint(test_client, db_session, seeded_shop_context, auth_headers):
    """Verifies aggregated financial metrics, profit-loss, cash balance, and isolation."""
    s1 = seeded_shop_context["shop1"]
    s2 = seeded_shop_context["shop2"]
    b1 = seeded_shop_context["business1"]
    h1 = auth_headers["user1"]

    # Seed sales and expenses for Shop 1
    sale = Sale(
        business_id=b1.id,
        shop_id=s1.id,
        invoice_number="INV-SUMMARY-1",
        sale_date=utc_now(),
        subtotal_minor=100000,
        tax_minor=5000,
        discount_minor=0,
        total_amount_minor=105000,
        paid_amount_minor=105000,
        payment_status="paid",
        payment_method="cash",
    )
    expense = Expense(
        business_id=b1.id,
        shop_id=s1.id,
        expense_category="rent",
        expense_date=utc_now(),
        amount_minor=35000,
        payment_method="cash",
    )
    product = Product(
        business_id=b1.id,
        shop_id=s1.id,
        sku="TEST-SKU-1",
        name="Test Item",
        category="general",
        current_stock=20,
        min_stock_alert=5,
        cost_price_minor=3000,
        selling_price_minor=5000,
    )
    db_session.add_all([sale, expense, product])
    db_session.flush()

    # Query financial summary for Shop 1
    resp = test_client.get(f"/api/finance/summary?shop_id={s1.id}", headers=h1)
    assert resp.status_code == 200
    data = resp.json()
    assert data["shop_id"] == s1.id
    assert data["revenue"]["total_minor"] == 105000
    assert data["expenses"]["total_minor"] == 35000
    assert data["profitability"]["net_profit_minor"] == 70000
    assert data["inventory"]["total_skus"] >= 1
    assert data["inventory"]["valuation_minor"] == 20 * 3000

    # Cross-tenant query to Shop 2 summary with User 1 token -> 403
    resp2 = test_client.get(f"/api/finance/summary?shop_id={s2.id}", headers=h1)
    assert resp2.status_code == 403


# ==============================================================================
# 4. Sales and Expenses Retrieval with Filtering and Pagination
# ==============================================================================

def test_sales_and_expenses_filtering_and_pagination(test_client, db_session, seeded_shop_context, auth_headers):
    """Verifies pagination, date range filtering, and payment method filters."""
    s1 = seeded_shop_context["shop1"]
    b1 = seeded_shop_context["business1"]
    h1 = auth_headers["user1"]

    base_date = datetime(2026, 3, 1, 10, 0, 0)
    for i in range(5):
        s = Sale(
            business_id=b1.id,
            shop_id=s1.id,
            invoice_number=f"INV-PAGE-{i+1}",
            sale_date=base_date + timedelta(days=i),
            subtotal_minor=10000 * (i + 1),
            tax_minor=0,
            discount_minor=0,
            total_amount_minor=10000 * (i + 1),
            paid_amount_minor=10000 * (i + 1),
            payment_status="paid",
            payment_method="cash" if i % 2 == 0 else "card",
        )
        db_session.add(s)

    db_session.add(Expense(
        business_id=b1.id,
        shop_id=s1.id,
        expense_category="utilities",
        expense_date=base_date,
        amount_minor=12000,
        payment_method="bank_transfer",
    ))
    db_session.flush()

    # Pagination: page 1, limit 2
    resp = test_client.get(f"/api/finance/sales?shop_id={s1.id}&page=1&limit=2", headers=h1)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["sales"]) == 2
    assert data["total_count"] == 5
    assert data["total_pages"] == 3

    # Date filter: only 2026-03-02 to 2026-03-03
    resp_date = test_client.get(
        f"/api/finance/sales?shop_id={s1.id}&start_date=2026-03-02&end_date=2026-03-03",
        headers=h1,
    )
    assert resp_date.status_code == 200
    assert resp_date.json()["total_count"] == 2

    # Expenses query with category filter
    resp_exp = test_client.get(f"/api/finance/expenses?shop_id={s1.id}&category=utilities", headers=h1)
    assert resp_exp.status_code == 200
    assert len(resp_exp.json()["expenses"]) == 1
    assert resp_exp.json()["expenses"][0]["amount_minor"] == 12000


# ==============================================================================
# 5. Cash-Flow Forecasting Endpoint
# ==============================================================================

def test_cash_flow_forecasting(test_client, db_session, seeded_shop_context, auth_headers):
    """Verifies forecast generation with historical cash movements and database persistence."""
    s1 = seeded_shop_context["shop1"]
    b1 = seeded_shop_context["business1"]
    h1 = auth_headers["user1"]

    base_date = datetime(2026, 2, 1, 12, 0, 0)
    for i in range(20):
        cm_in = CashMovement(
            business_id=b1.id,
            shop_id=s1.id,
            movement_type="inflow",
            source_type="sale",
            amount_minor=50000 + i * 1000,
            running_balance_minor=100000 + i * 1000,
            movement_date=base_date + timedelta(days=i),
        )
        cm_out = CashMovement(
            business_id=b1.id,
            shop_id=s1.id,
            movement_type="outflow",
            source_type="expense",
            amount_minor=30000,
            running_balance_minor=100000 + i * 1000 - 30000,
            movement_date=base_date + timedelta(days=i),
        )
        db_session.add_all([cm_in, cm_out])
    db_session.flush()

    # Generate forecast
    payload = {
        "shop_id": s1.id,
        "horizon_days": 14,
        "method": "auto",
    }
    resp = test_client.post("/api/finance/forecast", json=payload, headers=h1)
    assert resp.status_code == 200
    data = resp.json()
    assert data["shop_id"] == s1.id
    assert data["horizon_days"] == 14
    assert len(data["point_forecast_minor"]) == 14
    assert len(data["lower_bound_80_minor"]) == 14
    assert len(data["upper_bound_80_minor"]) == 14

    # Verify latest forecast can be retrieved via GET
    resp_get = test_client.get(f"/api/finance/forecast?shop_id={s1.id}", headers=h1)
    assert resp_get.status_code == 200
    assert resp_get.json()["horizon_days"] == 14


# ==============================================================================
# 6. Loan Risk Assessment & Loan Products
# ==============================================================================

def test_loan_risk_and_comparison_endpoints(test_client, db_session, seeded_shop_context, auth_headers):
    """Verifies transparent loan risk calculation, EMI comparison, and loan product catalog."""
    s1 = seeded_shop_context["shop1"]
    h1 = auth_headers["user1"]

    # 1. Comparison endpoint
    cmp_payload = {
        "principal_minor": 50000000,
        "annual_interest_rate_pct": 9.0,
        "tenure_months": 12,
        "processing_fee_bps": 100,
    }
    resp = test_client.post("/api/finance/loan-comparison", json=cmp_payload)
    assert resp.status_code == 200
    cmp_data = resp.json()
    assert "reducing_monthly_emi" in cmp_data
    assert "flat_monthly_installment" in cmp_data
    assert "effective_apr_reducing" in cmp_data

    # 2. Risk assessment endpoint
    risk_payload = {
        "shop_id": s1.id,
        "requested_amount_minor": 30000000,
        "tenure_months": 12,
        "annual_interest_rate_pct": 9.0,
        "processing_fee_bps": 100,
        "monthly_revenue_minor": 50000000,
        "monthly_expenses_minor": 20000000,
    }
    resp_risk = test_client.post("/api/finance/loan-risk-assessment", json=risk_payload, headers=h1)
    assert resp_risk.status_code == 200
    risk_data = resp_risk.json()
    assert risk_data["recommendation_status"] in ("eligible", "borderline", "ineligible")
    assert risk_data["dscr_ratio"] > 1.0
    assert risk_data["is_synthetic_demo"] is True

    # 3. Loan products catalog
    # Seed a demo bank and product if needed
    bank = DemoBank(name="Integration Demo Bank", code="IDB_TEST", is_synthetic=True)
    db_session.add(bank)
    db_session.flush()
    prod = LoanProduct(
        bank_id=bank.id,
        name="SME Working Capital Loan",
        min_amount_minor=1000000,
        max_amount_minor=100000000,
        min_tenure_months=6,
        max_tenure_months=24,
        annual_interest_rate_bps=900,
        interest_calc_type="reducing_balance",
        processing_fee_bps=100,
        is_synthetic=True,
    )
    db_session.add(prod)
    db_session.flush()

    resp_prods = test_client.get("/api/finance/loan-products", headers=h1)
    assert resp_prods.status_code == 200
    prods = resp_prods.json()
    assert len(prods) >= 1
    assert prods[0]["regulatory_disclaimer"] is not None


# ==============================================================================
# 7. Inventory and Receivables Summaries
# ==============================================================================

def test_inventory_and_receivables_summaries(test_client, db_session, seeded_shop_context, auth_headers):
    """Verifies stock valuation, aging buckets, and low stock alert generation."""
    s1 = seeded_shop_context["shop1"]
    b1 = seeded_shop_context["business1"]
    h1 = auth_headers["user1"]

    # Seed products with low stock
    p1 = Product(
        business_id=b1.id,
        shop_id=s1.id,
        sku="SKU-LOW-1",
        name="Low Stock Sugar",
        category="groceries",
        current_stock=2,
        min_stock_alert=10,
        cost_price_minor=5000,
        selling_price_minor=7000,
    )
    db_session.add(p1)

    # Seed a customer and a sale for receivables linkage
    cust = Customer(
        business_id=b1.id,
        shop_id=s1.id,
        name="Credit Customer",
    )
    db_session.add(cust)
    db_session.flush()

    sale_rec = Sale(
        business_id=b1.id,
        shop_id=s1.id,
        customer_id=cust.id,
        invoice_number="INV-REC-TEST",
        sale_date=utc_now(),
        subtotal_minor=35000,
        tax_minor=0,
        discount_minor=0,
        total_amount_minor=35000,
        paid_amount_minor=0,
        payment_status="unpaid",
        payment_method="credit",
    )
    db_session.add(sale_rec)
    db_session.flush()

    # Seed overdue and current receivables
    now = utc_now()
    r1 = Receivable(
        business_id=b1.id,
        shop_id=s1.id,
        sale_id=sale_rec.id,
        customer_id=cust.id,
        total_amount_minor=20000,
        outstanding_amount_minor=20000,
        due_date=now - timedelta(days=45),  # 45 days overdue
        status="pending",
    )
    r2 = Receivable(
        business_id=b1.id,
        shop_id=s1.id,
        sale_id=sale_rec.id,
        customer_id=cust.id,
        total_amount_minor=15000,
        outstanding_amount_minor=15000,
        due_date=now + timedelta(days=10),  # Not overdue
        status="pending",
    )
    db_session.add_all([r1, r2])
    db_session.flush()

    # Inventory summary
    resp_inv = test_client.get(f"/api/finance/inventory-summary?shop_id={s1.id}", headers=h1)
    assert resp_inv.status_code == 200
    inv_data = resp_inv.json()
    assert inv_data["low_stock_items_count"] >= 1
    assert len(inv_data["low_stock_alerts"]) >= 1

    # Receivables summary
    resp_rec = test_client.get(f"/api/finance/receivables-summary?shop_id={s1.id}", headers=h1)
    assert resp_rec.status_code == 200
    rec_data = resp_rec.json()
    assert rec_data["overdue_count"] >= 1
    assert rec_data["aging_buckets"]["overdue_31_60_days_minor"] == 20000


# ==============================================================================
# 8. Document Upload, Quarantine Review, and Idempotent Ledger Post
# ==============================================================================

def test_document_pipeline_e2e_api(test_client, seeded_shop_context, auth_headers):
    """
    End-to-end API test:
    1. Upload receipt image -> OCR and form routing result.
    2. Inspect document via GET /api/documents/{id}.
    3. Verify cross-shop isolation denies other shop owners.
    4. Confirm and post to financial ledger via POST /api/documents/confirm-post.
    5. Attempt duplicate post -> rejected with 409 Conflict.
    """
    s1 = seeded_shop_context["shop1"]
    s2 = seeded_shop_context["shop2"]
    h1 = auth_headers["user1"]
    h2 = auth_headers["user2"]

    image_bytes = _create_mock_receipt_image_bytes()

    # 1. Upload
    files = {"file": ("grocery_receipt.png", image_bytes, "image/png")}
    data = {"shop_id": str(s1.id)}
    resp_up = test_client.post("/api/documents/upload", data=data, files=files, headers=h1)
    assert resp_up.status_code == 200
    routing = resp_up.json()
    doc_id = routing["document_id"]
    assert doc_id > 0

    # 2. Inspect document details
    resp_doc = test_client.get(f"/api/documents/{doc_id}", headers=h1)
    assert resp_doc.status_code == 200
    doc_detail = resp_doc.json()
    assert doc_detail["id"] == doc_id
    assert doc_detail["is_posted"] is False

    # 3. Cross-shop isolation check: User 2 cannot inspect User 1's document -> 403
    resp_cross = test_client.get(f"/api/documents/{doc_id}", headers=h2)
    assert resp_cross.status_code == 403

    # 4. Human review confirmation & post to ledger
    confirm_payload = {
        "document_id": doc_id,
        "confirmed_doc_type": "sales_receipt",
        "final_values": {
            "subtotal_minor": 50000,
            "tax_minor": 2500,
            "discount_minor": 0,
            "total_amount_minor": 52500,
            "paid_amount_minor": 52500,
            "payment_method": "cash",
            "invoice_number": f"VERIFIED-{doc_id}",
            "customer_name": "Walk-in Customer",
            "items": [
                {
                    "description": "Vegetables",
                    "quantity": 2,
                    "unit_price_minor": 25000,
                    "line_total_minor": 50000,
                }
            ],
        },
        "decision_action": "approve_and_post",
        "reviewer_notes": "All values verified against physical receipt.",
    }

    resp_post = test_client.post("/api/documents/confirm-post", json=confirm_payload, headers=h1)
    assert resp_post.status_code == 200
    assert resp_post.json()["status"] == "posted"

    # 5. Duplicate post attempt -> 409 Conflict
    resp_dup = test_client.post("/api/documents/confirm-post", json=confirm_payload, headers=h1)
    assert resp_dup.status_code == 409
    assert "already been posted" in resp_dup.json()["detail"].lower()


# ==============================================================================
# 9. Document Upload Validation (Size Limit and MIME Type)
# ==============================================================================

def test_document_upload_validation(test_client, seeded_shop_context, auth_headers):
    """Verifies that invalid MIME types and oversized files are rejected cleanly."""
    s1 = seeded_shop_context["shop1"]
    h1 = auth_headers["user1"]

    # Disallowed MIME type
    bad_file = {"file": ("script.exe", b"fake binary data", "application/x-msdownload")}
    resp_bad = test_client.post(
        "/api/documents/upload",
        data={"shop_id": str(s1.id)},
        files=bad_file,
        headers=h1,
    )
    assert resp_bad.status_code == 400
    assert "unsupported file type" in resp_bad.json()["detail"].lower()

    # Oversized file (> 10MB)
    huge_bytes = b"0" * (10 * 1024 * 1024 + 100)
    huge_file = {"file": ("huge.png", huge_bytes, "image/png")}
    resp_huge = test_client.post(
        "/api/documents/upload",
        data={"shop_id": str(s1.id)},
        files=huge_file,
        headers=h1,
    )
    assert resp_huge.status_code == 413
    assert "exceeds maximum allowed upload size" in resp_huge.json()["detail"].lower()


# ==============================================================================
# 10. Audit Logging and Security Isolation
# ==============================================================================

def test_audit_logs_and_sanitized_errors(test_client, seeded_shop_context, auth_headers):
    """Verifies audit logging endpoint, tenant isolation on logs, and error responses without stack traces."""
    s1 = seeded_shop_context["shop1"]
    s2 = seeded_shop_context["shop2"]
    h1 = auth_headers["user1"]

    # User 1 queries Shop 1 audit logs
    resp = test_client.get(f"/api/audit/logs?shop_id={s1.id}", headers=h1)
    assert resp.status_code == 200
    data = resp.json()
    assert "logs" in data
    assert data["shop_id"] == s1.id

    # User 1 attempts to query Shop 2 audit logs -> 403 Forbidden
    resp_cross = test_client.get(f"/api/audit/logs?shop_id={s2.id}", headers=h1)
    assert resp_cross.status_code == 403
    assert resp_cross.json()["error_code"] == "SHOP_ACCESS_DENIED"
    # Ensure error response contains no Python traceback / source code leakage
    assert "Traceback" not in resp_cross.text
    assert ".py" not in resp_cross.text
