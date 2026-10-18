"""
Automated Test Suite for Live SME Dashboard KPIs & Daily Financial Stream.
Verifies dynamic metric binding, Chart.js stream generation, distinct figures across shops,
empty-state handling, cookie authentication, and strict multi-tenant authorization.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
import pytest

from src.config import settings
from src.core.security import create_token
from src.database.models import Sale, Expense, CashMovement, Product, Shop, BusinessMembership, utc_now


@pytest.fixture
def auth_headers(seeded_shop_context):
    """Provides authorization headers and tokens for User 1 and User 2."""
    user1 = seeded_shop_context["user1"]
    user2 = seeded_shop_context["user2"]
    token1 = create_token(user1.id, settings.SECRET_KEY)
    token2 = create_token(user2.id, settings.SECRET_KEY)
    return {
        "user1": {"Authorization": f"Bearer {token1}"},
        "user2": {"Authorization": f"Bearer {token2}"},
        "token1": token1,
        "token2": token2,
    }


def test_dashboard_summary_kpis_and_trailing_metrics(test_client, db_session, seeded_shop_context, auth_headers):
    """
    Verifies that /api/finance/summary returns trailing 30-day KPIs, cash runway,
    DSCR ratio, synthetic data flag, and active currency formatting.
    """
    s1 = seeded_shop_context["shop1"]
    b1 = seeded_shop_context["business1"]
    h1 = auth_headers["user1"]
    now = datetime.now(timezone.utc)

    # Seed sales and expenses for Shop 1
    sale = Sale(
        business_id=b1.id,
        shop_id=s1.id,
        invoice_number="INV-2026-LIVE-01",
        subtotal_minor=100000,
        tax_minor=0,
        discount_minor=0,
        total_amount_minor=100000,
        payment_method="cash",
        payment_status="paid",
        sale_date=now - timedelta(days=5),
    )
    expense = Expense(
        business_id=b1.id,
        shop_id=s1.id,
        expense_category="utilities",
        description="Electric bill",
        amount_minor=30000,
        payment_method="cash",
        expense_date=now - timedelta(days=4),
    )
    # Seed cash movement for positive balance
    cash_in = CashMovement(
        business_id=b1.id,
        shop_id=s1.id,
        movement_type="inflow",
        source_type="owner_equity",
        amount_minor=200000,
        running_balance_minor=200000,
        notes="Capital injection",
        movement_date=now - timedelta(days=6),
    )
    db_session.add_all([sale, expense, cash_in])
    db_session.flush()

    resp = test_client.get(f"/api/finance/summary?shop_id={s1.id}", headers=h1)
    assert resp.status_code == 200
    data = resp.json()

    assert data["shop_id"] == s1.id
    assert data["currency"] == "BDT"
    assert data["has_data"] is True
    assert "is_synthetic" in data

    # Verify trailing 30-day metrics
    t30 = data["trailing_30d"]
    assert t30["sales_minor"] == 100000
    assert "1,000.00" in t30["sales_formatted"]
    assert t30["expenses_minor"] == 30000
    assert t30["net_profit_minor"] == 70000
    assert t30["sales_growth_pct"] == 100.0  # From 0 in previous 30 days to 100000

    # Verify runway & DSCR blocks
    assert "runway" in data
    assert data["runway"]["days"] >= 0
    assert "Days" in data["runway"]["formatted"]

    assert "dscr" in data
    assert "x" in data["dscr"]["formatted"]
    assert data["dscr"]["status"] in ["eligible", "marginal", "ineligible"]


def test_dashboard_kpis_different_shops_distinct_figures(test_client, db_session, seeded_shop_context, auth_headers):
    """
    Verifies that two different shops return distinct KPI numbers and margins,
    proving the dashboard does not serve static hardcoded figures.
    """
    s1 = seeded_shop_context["shop1"]
    b1 = seeded_shop_context["business1"]
    s2 = seeded_shop_context["shop2"]
    b2 = seeded_shop_context["business2"]
    h1 = auth_headers["user1"]
    h2 = auth_headers["user2"]
    now = datetime.now(timezone.utc)

    # Shop 1: 150,000 revenue, 40,000 expenses
    sale1 = Sale(
        business_id=b1.id,
        shop_id=s1.id,
        invoice_number="INV-S1-001",
        total_amount_minor=150000,
        payment_method="cash",
        payment_status="paid",
        sale_date=now - timedelta(days=2),
    )
    exp1 = Expense(
        business_id=b1.id,
        shop_id=s1.id,
        expense_category="rent",
        amount_minor=40000,
        payment_method="bank_transfer",
        expense_date=now - timedelta(days=2),
    )

    # Shop 2: 500,000 revenue, 120,000 expenses
    sale2 = Sale(
        business_id=b2.id,
        shop_id=s2.id,
        invoice_number="INV-S2-001",
        total_amount_minor=500000,
        payment_method="card",
        payment_status="paid",
        sale_date=now - timedelta(days=1),
    )
    exp2 = Expense(
        business_id=b2.id,
        shop_id=s2.id,
        expense_category="supplies",
        amount_minor=120000,
        payment_method="card",
        expense_date=now - timedelta(days=1),
    )

    db_session.add_all([sale1, exp1, sale2, exp2])
    db_session.flush()

    res1 = test_client.get(f"/api/finance/summary?shop_id={s1.id}", headers=h1)
    res2 = test_client.get(f"/api/finance/summary?shop_id={s2.id}", headers=h2)

    assert res1.status_code == 200
    assert res2.status_code == 200

    d1 = res1.json()
    d2 = res2.json()

    # Assert distinct figures
    assert d1["trailing_30d"]["sales_minor"] == 150000
    assert d2["trailing_30d"]["sales_minor"] == 500000
    assert d1["trailing_30d"]["sales_minor"] != d2["trailing_30d"]["sales_minor"]

    assert d1["trailing_30d"]["expenses_minor"] == 40000
    assert d2["trailing_30d"]["expenses_minor"] == 120000
    assert d1["trailing_30d"]["expenses_minor"] != d2["trailing_30d"]["expenses_minor"]

    assert d1["profitability"]["net_profit_minor"] == 110000
    assert d2["profitability"]["net_profit_minor"] == 380000
    assert d1["profitability"]["net_profit_minor"] != d2["profitability"]["net_profit_minor"]


def test_daily_stream_endpoint_structure_and_values(test_client, db_session, seeded_shop_context, auth_headers):
    """
    Verifies that /api/finance/daily-stream generates a valid 30-day time series
    matching actual database transactions.
    """
    s1 = seeded_shop_context["shop1"]
    b1 = seeded_shop_context["business1"]
    h1 = auth_headers["user1"]
    now = datetime.now(timezone.utc)

    # Seed 2 sales on consecutive days
    s_date1 = now - timedelta(days=2)
    s_date2 = now - timedelta(days=1)
    sale1 = Sale(
        business_id=b1.id,
        shop_id=s1.id,
        invoice_number="INV-DS-01",
        total_amount_minor=60000,
        payment_method="cash",
        sale_date=s_date1,
    )
    sale2 = Sale(
        business_id=b1.id,
        shop_id=s1.id,
        invoice_number="INV-DS-02",
        total_amount_minor=40000,
        payment_method="cash",
        sale_date=s_date2,
    )
    exp = Expense(
        business_id=b1.id,
        shop_id=s1.id,
        expense_category="maintenance",
        amount_minor=25000,
        payment_method="cash",
        expense_date=s_date1,
    )
    db_session.add_all([sale1, sale2, exp])
    db_session.flush()

    resp = test_client.get(f"/api/finance/daily-stream?shop_id={s1.id}&days=30", headers=h1)
    assert resp.status_code == 200
    stream = resp.json()

    assert stream["shop_id"] == s1.id
    assert stream["days"] == 30
    assert len(stream["labels"]) == 30
    assert len(stream["dates"]) == 30
    assert len(stream["revenue_major"]) == 30
    assert len(stream["expenses_major"]) == 30

    assert stream["total_revenue_major"] == 1000.0  # (60,000 + 40,000) / 100
    assert stream["total_expenses_major"] == 250.0   # 25,000 / 100
    assert stream["is_empty"] is False


def test_daily_stream_different_shops_distinct_charts(test_client, db_session, seeded_shop_context, auth_headers):
    """
    Verifies that daily-stream charts are distinct for different shops.
    """
    s1 = seeded_shop_context["shop1"]
    b1 = seeded_shop_context["business1"]
    s2 = seeded_shop_context["shop2"]
    b2 = seeded_shop_context["business2"]
    h1 = auth_headers["user1"]
    h2 = auth_headers["user2"]
    now = datetime.now(timezone.utc)

    sale1 = Sale(business_id=b1.id, shop_id=s1.id, invoice_number="INV-DIFF-S1", total_amount_minor=80000, sale_date=now - timedelta(days=1))
    sale2 = Sale(business_id=b2.id, shop_id=s2.id, invoice_number="INV-DIFF-S2", total_amount_minor=350000, sale_date=now - timedelta(days=1))
    db_session.add_all([sale1, sale2])
    db_session.flush()

    res1 = test_client.get(f"/api/finance/daily-stream?shop_id={s1.id}&days=30", headers=h1)
    res2 = test_client.get(f"/api/finance/daily-stream?shop_id={s2.id}&days=30", headers=h2)

    assert res1.status_code == 200
    assert res2.status_code == 200

    stream1 = res1.json()
    stream2 = res2.json()

    assert stream1["total_revenue_major"] == 800.0
    assert stream2["total_revenue_major"] == 3500.0
    assert stream1["total_revenue_major"] != stream2["total_revenue_major"]


def test_daily_stream_empty_shop(test_client, db_session, seeded_shop_context, auth_headers):
    """
    Verifies that an empty shop returns is_empty=True with zeroed series and no server errors.
    """
    b1 = seeded_shop_context["business1"]
    u1 = seeded_shop_context["user1"]
    h1 = auth_headers["user1"]

    # Create empty shop
    empty_shop = Shop(business_id=b1.id, name="Shop Brand New Empty")
    db_session.add(empty_shop)
    db_session.flush()

    m = BusinessMembership(user_id=u1.id, business_id=b1.id, shop_id=empty_shop.id, role_code="owner")
    db_session.add(m)
    db_session.flush()

    resp = test_client.get(f"/api/finance/daily-stream?shop_id={empty_shop.id}&days=30", headers=h1)
    assert resp.status_code == 200
    data = resp.json()

    assert data["is_empty"] is True
    assert data["total_revenue_major"] == 0.0
    assert data["total_expenses_major"] == 0.0
    assert len(data["revenue_major"]) == 30
    assert all(r == 0.0 for r in data["revenue_major"])


def test_daily_stream_cross_shop_access_forbidden(test_client, seeded_shop_context, auth_headers):
    """
    Verifies that User 1 cannot access Shop 2's daily financial stream (HTTP 403).
    """
    s2 = seeded_shop_context["shop2"]
    h1 = auth_headers["user1"]

    resp = test_client.get(f"/api/finance/daily-stream?shop_id={s2.id}", headers=h1)
    assert resp.status_code == 403


def test_cookie_authentication_supported_on_finance_endpoints(test_client, seeded_shop_context, auth_headers):
    """
    Verifies that browser requests authenticating via sme_auth_token cookie succeed
    even without an explicit Authorization header.
    """
    s1 = seeded_shop_context["shop1"]
    token1 = auth_headers["token1"]

    # In production, require valid token (cookie or header)
    test_client.cookies.set("sme_auth_token", token1)
    resp = test_client.get(f"/api/finance/summary?shop_id={s1.id}")
    test_client.cookies.clear()

    assert resp.status_code == 200
    assert resp.json()["shop_id"] == s1.id


def test_production_environment_rejects_unauthenticated_daily_stream(test_client, seeded_shop_context, monkeypatch):
    """
    Verifies that when ENVIRONMENT is production, missing credentials on daily-stream
    return 401 with standard security exception.
    """
    s1 = seeded_shop_context["shop1"]
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    resp = test_client.get(f"/api/finance/daily-stream?shop_id={s1.id}")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Missing Authorization header."
