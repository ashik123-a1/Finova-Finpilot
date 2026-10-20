"""
Deterministic Financial Calculations and Ledger API Routes.
Provides financial summaries, ledger retrieval (sales/expenses), cash-flow forecasting,
explainable loan risk assessments, and inventory/receivable analytics with shop isolation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, and_

from src.database.connection import get_db
from src.database.models import (
    User,
    Shop,
    Business,
    Sale,
    SaleItem,
    Purchase,
    Expense,
    Payment,
    Receivable,
    Product,
    CashMovement,
    DemoBank,
    LoanProduct,
    LoanRule,
    LoanScenario,
    LoanApplication,
    Forecast,
    AuditLog,
    Document,
    BusinessMembership,
    utc_now,
)
from src.api.dependencies import get_current_user, verify_shop_access_dependency
from src.finance.calculator import FinancialCalculator
from src.ai.forecaster import CashFlowForecaster
from src.ai.loan_risk import TransparentLoanRiskEngine
from src.finance.pdf_packet import generate_loan_packet_pdf
from src.database.repository import AuditRepository
from src.core.money import Money

router = APIRouter(prefix="/finance", tags=["Finance"])


# ==============================================================================
# Helper functions
# ==============================================================================

def _parse_date_safe(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    cleaned = date_str.strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(cleaned)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD or ISO-8601.",
        )


def _make_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if isinstance(dt, str):
        dt = _parse_date_safe(dt)
    if dt and dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


# ==============================================================================
# Request & Response Schemas
# ==============================================================================

class LoanComparisonRequest(BaseModel):
    principal_minor: int = Field(..., gt=0, description="Principal amount in minor units")
    annual_interest_rate_pct: float = Field(..., ge=0, description="Annual interest rate percentage")
    tenure_months: int = Field(..., gt=0, description="Loan duration in months")
    processing_fee_bps: int = Field(100, ge=0, description="Processing fee in basis points (100 bps = 1.00%)")


class LoanRiskRequest(BaseModel):
    shop_id: int
    requested_amount_minor: int = Field(..., gt=0)
    tenure_months: int = Field(..., gt=0)
    annual_interest_rate_pct: float = Field(..., ge=0)
    processing_fee_bps: int = Field(100, ge=0)
    existing_monthly_debt_minor: int = Field(0, ge=0)
    monthly_revenue_minor: Optional[int] = None
    monthly_expenses_minor: Optional[int] = None


class BreakEvenRequest(BaseModel):
    fixed_costs_minor: int = Field(..., ge=0)
    selling_price_per_unit_minor: int = Field(..., gt=0)
    variable_cost_per_unit_minor: int = Field(..., ge=0)


class ForecastRequest(BaseModel):
    shop_id: int
    horizon_days: int = Field(30, ge=7, le=90)
    method: str = Field("auto", description="Forecasting method: 'auto', 'ml_ridge', or 'moving_average'")


class LoanPacketGenerateRequest(BaseModel):
    shop_id: int
    requested_amount_minor: int = Field(..., gt=0, description="Principal amount in minor units")
    tenure_months: int = Field(..., gt=0, description="Loan tenure in months")
    annual_interest_rate_pct: float = Field(..., ge=0, description="Annual interest rate percentage")
    loan_purpose: str = Field("working_capital", description="Loan purpose code: working_capital, equipment, branch, refinance")
    selected_product_id: Optional[int] = Field(None, description="Optional ID of chosen loan product")
    existing_monthly_debt_minor: int = Field(0, ge=0, description="Existing monthly debt obligations")
    monthly_noi_minor: Optional[int] = Field(None, description="Optional user-specified or modeled monthly NOI")


# ==============================================================================
# 1. Financial Health Summary Dashboard
# ==============================================================================

@router.get("/summary")
def get_financial_summary(
    shop_id: Optional[int] = Query(None, description="Shop ID for multi-tenant query"),
    start_date: Optional[str] = Query(None, description="Optional start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Optional end date (YYYY-MM-DD)"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns an aggregated financial health dashboard for a shop:
    Revenue, COGS, Operating Expenses, Gross & Net Profit, Cash Balance,
    Inventory Valuation, Outstanding Receivables, and Document Review Queue.
    Supports optional date-range filtering.
    """
    if shop_id is None:
        membership = (
            db.query(BusinessMembership)
            .filter(BusinessMembership.user_id == user.id, BusinessMembership.is_active == True)
            .first()
        )
        if membership and membership.shop_id:
            shop_id = membership.shop_id
        elif membership and membership.business_id:
            first_shop = db.query(Shop).filter(Shop.business_id == membership.business_id, Shop.is_active == True).first()
            if first_shop:
                shop_id = first_shop.id
    if shop_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shop ID is required.")

    verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)
    shop = db.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found.")

    s_dt = _parse_date_safe(start_date) if start_date else None
    e_dt = _parse_date_safe(end_date) if end_date else None
    if s_dt and e_dt and s_dt > e_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date range: start_date cannot be after end_date.",
        )

    # 1. Sales & Revenue
    sales_q = db.query(Sale).filter(Sale.shop_id == shop_id)
    if s_dt:
        sales_q = sales_q.filter(Sale.sale_date >= s_dt)
    if e_dt:
        sales_q = sales_q.filter(Sale.sale_date <= e_dt + timedelta(days=1))
    sales_total = (
        sales_q.with_entities(func.coalesce(func.sum(Sale.total_amount_minor), 0)).scalar()
    ) or 0
    sales_count = sales_q.count()

    # 2. Purchases & COGS
    purchases_q = db.query(Purchase).filter(Purchase.shop_id == shop_id)
    if s_dt:
        purchases_q = purchases_q.filter(Purchase.purchase_date >= s_dt)
    if e_dt:
        purchases_q = purchases_q.filter(Purchase.purchase_date <= e_dt + timedelta(days=1))
    cogs_total = (
        purchases_q.with_entities(func.coalesce(func.sum(Purchase.total_amount_minor), 0)).scalar()
    ) or 0

    # 3. Operating Expenses
    expenses_q = db.query(Expense).filter(Expense.shop_id == shop_id)
    if s_dt:
        expenses_q = expenses_q.filter(Expense.expense_date >= s_dt)
    if e_dt:
        expenses_q = expenses_q.filter(Expense.expense_date <= e_dt + timedelta(days=1))
    expenses_total = (
        expenses_q.with_entities(func.coalesce(func.sum(Expense.amount_minor), 0)).scalar()
    ) or 0
    expenses_count = expenses_q.count()

    # 4. Deterministic Profit & Loss
    gross_profit_minor = sales_total - cogs_total
    net_profit_minor = gross_profit_minor - expenses_total
    gross_margin_pct = round((gross_profit_minor / sales_total) * 100, 2) if sales_total > 0 else 0.0
    net_margin_pct = round((net_profit_minor / sales_total) * 100, 2) if sales_total > 0 else 0.0

    # 5. Cash Flow & Net Balance
    pay_in_q = db.query(Payment).filter(
        Payment.shop_id == shop_id,
        Payment.payment_type.in_(["customer_inflow", "loan_disbursement"]),
    )
    pay_out_q = db.query(Payment).filter(
        Payment.shop_id == shop_id,
        Payment.payment_type.in_(["supplier_outflow", "expense_outflow", "loan_repayment"]),
    )
    if s_dt:
        pay_in_q = pay_in_q.filter(Payment.payment_date >= s_dt)
        pay_out_q = pay_out_q.filter(Payment.payment_date >= s_dt)
    if e_dt:
        pay_in_q = pay_in_q.filter(Payment.payment_date <= e_dt + timedelta(days=1))
        pay_out_q = pay_out_q.filter(Payment.payment_date <= e_dt + timedelta(days=1))

    payment_inflows = pay_in_q.with_entities(func.coalesce(func.sum(Payment.amount_minor), 0)).scalar() or 0
    payment_outflows = pay_out_q.with_entities(func.coalesce(func.sum(Payment.amount_minor), 0)).scalar() or 0

    if payment_inflows == 0 and payment_outflows == 0:
        # Fallback to CashMovement if Payment table is empty
        cm_in_q = db.query(CashMovement).filter(
            CashMovement.shop_id == shop_id,
            CashMovement.movement_type == "inflow",
        )
        cm_out_q = db.query(CashMovement).filter(
            CashMovement.shop_id == shop_id,
            CashMovement.movement_type == "outflow",
        )
        if s_dt:
            cm_in_q = cm_in_q.filter(CashMovement.movement_date >= s_dt)
            cm_out_q = cm_out_q.filter(CashMovement.movement_date >= s_dt)
        if e_dt:
            cm_in_q = cm_in_q.filter(CashMovement.movement_date <= e_dt + timedelta(days=1))
            cm_out_q = cm_out_q.filter(CashMovement.movement_date <= e_dt + timedelta(days=1))

        cm_inflows = cm_in_q.with_entities(func.coalesce(func.sum(CashMovement.amount_minor), 0)).scalar() or 0
        cm_outflows = cm_out_q.with_entities(func.coalesce(func.sum(CashMovement.amount_minor), 0)).scalar() or 0
        net_cash_flow_minor = cm_inflows - cm_outflows
        current_cash_balance_minor = net_cash_flow_minor
    else:
        net_cash_flow_minor = payment_inflows - payment_outflows
        current_cash_balance_minor = net_cash_flow_minor

    # 6. Inventory Valuation
    products = db.query(Product).filter(Product.shop_id == shop_id).all()
    inventory_valuation_minor = sum(p.current_stock * p.cost_price_minor for p in products if p.current_stock > 0)
    low_stock_count = sum(1 for p in products if p.current_stock <= p.min_stock_alert)

    # 7. Receivables
    receivables_total = (
        db.query(func.coalesce(func.sum(Receivable.outstanding_amount_minor), 0))
        .filter(Receivable.shop_id == shop_id, Receivable.status.in_(["pending", "partial"]))
        .scalar()
    ) or 0
    receivables_count = (
        db.query(Receivable)
        .filter(Receivable.shop_id == shop_id, Receivable.status.in_(["pending", "partial"]))
        .count()
    )

    # 8. Pending Document Reviews
    pending_documents_count = (
        db.query(Document)
        .filter(Document.shop_id == shop_id, Document.status.in_(["uploaded", "review_pending", "quarantined"]))
        .count()
    )

    currency = shop.business.currency if shop.business else "BDT"

    # 9. Trailing 30-day and previous 30-day calculations
    max_sale_dt = db.query(func.max(Sale.sale_date)).filter(Sale.shop_id == shop_id).scalar()
    max_exp_dt = db.query(func.max(Expense.expense_date)).filter(Expense.shop_id == shop_id).scalar()
    anchor_candidates = [_make_naive_utc(d) for d in [max_sale_dt, max_exp_dt] if d is not None]

    if anchor_candidates:
        anchor_dt = max(anchor_candidates)
    else:
        anchor_dt = datetime.now(timezone.utc).replace(tzinfo=None)

    t30_start = anchor_dt - timedelta(days=30)
    p30_start = anchor_dt - timedelta(days=60)

    # Trailing 30-day sales
    t30_sales_minor = (
        db.query(func.coalesce(func.sum(Sale.total_amount_minor), 0))
        .filter(Sale.shop_id == shop_id, Sale.sale_date >= t30_start, Sale.sale_date <= anchor_dt)
        .scalar()
    ) or 0
    t30_sales_count = (
        db.query(Sale)
        .filter(Sale.shop_id == shop_id, Sale.sale_date >= t30_start, Sale.sale_date <= anchor_dt)
        .count()
    )

    # Previous 30-day sales
    p30_sales_minor = (
        db.query(func.coalesce(func.sum(Sale.total_amount_minor), 0))
        .filter(Sale.shop_id == shop_id, Sale.sale_date >= p30_start, Sale.sale_date < t30_start)
        .scalar()
    ) or 0

    if p30_sales_minor > 0:
        sales_growth_pct = round(((t30_sales_minor - p30_sales_minor) / p30_sales_minor) * 100, 1)
    elif t30_sales_minor > 0:
        sales_growth_pct = 100.0
    else:
        sales_growth_pct = 0.0

    # Trailing 30-day expenses
    t30_expenses_minor = (
        db.query(func.coalesce(func.sum(Expense.amount_minor), 0))
        .filter(Expense.shop_id == shop_id, Expense.expense_date >= t30_start, Expense.expense_date <= anchor_dt)
        .scalar()
    ) or 0
    t30_expenses_count = (
        db.query(Expense)
        .filter(Expense.shop_id == shop_id, Expense.expense_date >= t30_start, Expense.expense_date <= anchor_dt)
        .count()
    )

    t30_net_profit_minor = t30_sales_minor - t30_expenses_minor
    t30_net_margin_pct = round((t30_net_profit_minor / t30_sales_minor) * 100, 1) if t30_sales_minor > 0 else 0.0

    # 10. Cash Runway calculation
    daily_burn_minor = max(1, t30_expenses_minor // 30) if t30_expenses_minor > 0 else 0
    if daily_burn_minor > 0 and current_cash_balance_minor > 0:
        runway_days = min(999, max(0, current_cash_balance_minor // daily_burn_minor))
    elif current_cash_balance_minor > 0:
        runway_days = 999
    else:
        runway_days = 0

    if runway_days >= 60:
        runway_status = "safe"
    elif runway_days >= 30:
        runway_status = "warning"
    else:
        runway_status = "critical"
        if daily_burn_minor > 0 and user:
            try:
                from src.api.routes.notifications import create_persistent_notification
                create_persistent_notification(
                    db=db,
                    user_id=user.id,
                    title="Critical Cash Runway Alert",
                    message=f"Cash runway for Shop #{shop.id} is projected at {runway_days} days. Daily burn is {daily_burn_minor / 100:,.2f} {currency}. Immediate working capital review advised.",
                    notification_type="cash_warning",
                    severity="critical",
                    business_id=shop.business_id,
                    shop_id=shop.id,
                    action_url="/app/forecast",
                    dedup_key=f"cash_runway_{shop.id}_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
                )
            except Exception:
                pass

    # 11. DSCR Calculation
    latest_scenario = (
        db.query(LoanScenario)
        .filter(LoanScenario.shop_id == shop_id)
        .order_by(desc(LoanScenario.id))
        .first()
    )
    if latest_scenario and latest_scenario.dscr_ratio is not None:
        dscr_val = round(latest_scenario.dscr_ratio, 2)
        dscr_status = latest_scenario.recommendation_status or ("eligible" if dscr_val >= 1.25 else "borderline")
    else:
        monthly_noi = max(0, t30_net_profit_minor)
        benchmark_debt_service = 3750000  # 37,500 BDT benchmark
        dscr_val = round(monthly_noi / benchmark_debt_service, 2) if benchmark_debt_service > 0 else 2.0
        dscr_status = "eligible" if dscr_val >= 1.25 else ("marginal" if dscr_val >= 1.0 else "ineligible")

    if dscr_val >= 1.25:
        dscr_label = "Bank Loan Pre-Qualified"
    elif dscr_val >= 1.0:
        dscr_label = "Conditional / Collateral Needed"
    else:
        dscr_label = "Insufficient Coverage"

    is_synthetic = bool(
        getattr(shop, "is_synthetic", False) or 
        (shop.business and getattr(shop.business, "is_synthetic", False))
    )
    has_data = bool(sales_count > 0 or expenses_count > 0)

    return {
        "shop_id": shop_id,
        "shop_name": shop.name,
        "currency": currency,
        "revenue": {
            "total_minor": sales_total,
            "formatted": Money.from_minor(sales_total, currency).format(),
            "transaction_count": sales_count,
        },
        "cogs": {
            "total_minor": cogs_total,
            "formatted": Money.from_minor(cogs_total, currency).format(),
        },
        "expenses": {
            "total_minor": expenses_total,
            "formatted": Money.from_minor(expenses_total, currency).format(),
            "count": expenses_count,
        },
        "profitability": {
            "gross_profit_minor": gross_profit_minor,
            "gross_profit_formatted": Money.from_minor(gross_profit_minor, currency).format(),
            "gross_margin_pct": gross_margin_pct,
            "net_profit_minor": net_profit_minor,
            "net_profit_formatted": Money.from_minor(net_profit_minor, currency).format(),
            "net_margin_pct": net_margin_pct,
        },
        "liquidity": {
            "net_cash_flow_minor": net_cash_flow_minor,
            "net_cash_flow_formatted": Money.from_minor(net_cash_flow_minor, currency).format(),
            "cash_balance_minor": current_cash_balance_minor,
            "cash_balance_formatted": Money.from_minor(current_cash_balance_minor, currency).format(),
        },
        "inventory": {
            "total_skus": len(products),
            "valuation_minor": inventory_valuation_minor,
            "valuation_formatted": Money.from_minor(inventory_valuation_minor, currency).format(),
            "low_stock_alerts": low_stock_count,
        },
        "receivables": {
            "outstanding_minor": receivables_total,
            "outstanding_formatted": Money.from_minor(receivables_total, currency).format(),
            "pending_count": receivables_count,
        },
        "pending_document_reviews": pending_documents_count,
        "is_synthetic": is_synthetic,
        "has_data": has_data,
        "trailing_30d": {
            "sales_minor": t30_sales_minor,
            "sales_formatted": Money.from_minor(t30_sales_minor, currency).format(),
            "sales_growth_pct": sales_growth_pct,
            "expenses_minor": t30_expenses_minor,
            "expenses_formatted": Money.from_minor(t30_expenses_minor, currency).format(),
            "net_profit_minor": t30_net_profit_minor,
            "net_profit_formatted": Money.from_minor(t30_net_profit_minor, currency).format(),
            "net_margin_pct": t30_net_margin_pct,
            "runway_days": runway_days,
            "runway_status": runway_status,
            "daily_burn_minor": daily_burn_minor,
            "daily_burn_formatted": Money.from_minor(daily_burn_minor, currency).format(),
            "dscr_ratio": dscr_val,
            "dscr_formatted": f"{dscr_val:.2f}x",
            "dscr_status": dscr_status,
            "dscr_label": dscr_label,
            "anchor_date": anchor_dt.strftime("%Y-%m-%d"),
        },
        "runway": {
            "days": runway_days,
            "formatted": f"{runway_days} Days" if runway_days < 999 else "999+ Days",
            "status": runway_status,
            "daily_burn_minor": daily_burn_minor,
            "daily_burn_formatted": Money.from_minor(daily_burn_minor, currency).format(),
        },
        "dscr": {
            "ratio": dscr_val,
            "formatted": f"{dscr_val:.2f}x",
            "status": dscr_status,
            "label": dscr_label,
        },
    }


# ==============================================================================
# 1.1 Daily Financial Stream for Live Charts
# ==============================================================================

@router.get("/daily-stream")
def get_daily_financial_stream(
    shop_id: Optional[int] = Query(None, description="Shop ID for multi-tenant query"),
    days: int = Query(30, ge=7, le=90, description="Trailing number of days to stream"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns daily chronological revenue and expense stream for Chart.js rendering.
    Enforces tenant authorization and shop isolation.
    """
    if shop_id is None:
        membership = (
            db.query(BusinessMembership)
            .filter(BusinessMembership.user_id == user.id, BusinessMembership.is_active == True)
            .first()
        )
        if membership and membership.shop_id:
            shop_id = membership.shop_id
        elif membership and membership.business_id:
            first_shop = db.query(Shop).filter(Shop.business_id == membership.business_id, Shop.is_active == True).first()
            if first_shop:
                shop_id = first_shop.id
    if shop_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shop ID is required.")

    verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)
    shop = db.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found.")

    currency = shop.business.currency if shop.business else "BDT"
    is_synthetic = bool(
        getattr(shop, "is_synthetic", False) or 
        (shop.business and getattr(shop.business, "is_synthetic", False))
    )

    max_sale_dt = db.query(func.max(Sale.sale_date)).filter(Sale.shop_id == shop_id).scalar()
    max_exp_dt = db.query(func.max(Expense.expense_date)).filter(Expense.shop_id == shop_id).scalar()
    anchor_candidates = [_make_naive_utc(d) for d in [max_sale_dt, max_exp_dt] if d is not None]

    if not anchor_candidates:
        today = datetime.now(timezone.utc).date()
        labels = []
        dates = []
        revenue_major = []
        expenses_major = []
        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            dates.append(d.strftime("%Y-%m-%d"))
            labels.append(d.strftime("%b %d"))
            revenue_major.append(0.0)
            expenses_major.append(0.0)
        return {
            "shop_id": shop_id,
            "shop_name": shop.name,
            "currency": currency,
            "days": days,
            "start_date": dates[0],
            "end_date": dates[-1],
            "labels": labels,
            "dates": dates,
            "revenue_major": revenue_major,
            "expenses_major": expenses_major,
            "total_revenue_major": 0.0,
            "total_expenses_major": 0.0,
            "is_synthetic": is_synthetic,
            "is_empty": True,
        }

    anchor_dt = max(anchor_candidates)
    end_date = anchor_dt.date()
    start_date = end_date - timedelta(days=days - 1)

    s_dt = datetime.combine(start_date, datetime.min.time())
    e_dt = datetime.combine(end_date, datetime.max.time())

    daily_sales = (
        db.query(
            func.date(Sale.sale_date).label("d"),
            func.coalesce(func.sum(Sale.total_amount_minor), 0).label("tot"),
        )
        .filter(Sale.shop_id == shop_id, Sale.sale_date >= s_dt, Sale.sale_date <= e_dt)
        .group_by(func.date(Sale.sale_date))
        .all()
    )
    sales_map = {str(r.d): r.tot for r in daily_sales}

    daily_expenses = (
        db.query(
            func.date(Expense.expense_date).label("d"),
            func.coalesce(func.sum(Expense.amount_minor), 0).label("tot"),
        )
        .filter(Expense.shop_id == shop_id, Expense.expense_date >= s_dt, Expense.expense_date <= e_dt)
        .group_by(func.date(Expense.expense_date))
        .all()
    )
    expenses_map = {str(r.d): r.tot for r in daily_expenses}

    labels = []
    dates = []
    revenue_major = []
    expenses_major = []
    curr = start_date
    while curr <= end_date:
        d_str = curr.strftime("%Y-%m-%d")
        dates.append(d_str)
        labels.append(curr.strftime("%b %d"))
        rev_minor = sales_map.get(d_str, 0)
        exp_minor = expenses_map.get(d_str, 0)
        revenue_major.append(round(rev_minor / 100.0, 2))
        expenses_major.append(round(exp_minor / 100.0, 2))
        curr += timedelta(days=1)

    tot_rev = sum(revenue_major)
    tot_exp = sum(expenses_major)

    return {
        "shop_id": shop_id,
        "shop_name": shop.name,
        "currency": currency,
        "days": days,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "labels": labels,
        "dates": dates,
        "revenue_major": revenue_major,
        "expenses_major": expenses_major,
        "total_revenue_major": round(tot_rev, 2),
        "total_expenses_major": round(tot_exp, 2),
        "is_synthetic": is_synthetic,
        "is_empty": (tot_rev == 0 and tot_exp == 0),
    }


# ==============================================================================
# 2. Sales Ledger with Filtering and Pagination
# ==============================================================================

@router.get("/sales")
def list_sales(
    shop_id: Optional[int] = Query(None, description="Shop ID for multi-tenant query"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    payment_method: Optional[str] = Query(None, description="cash, card, mobile_money, bank_transfer"),
    payment_status: Optional[str] = Query(None, description="paid, partial, unpaid"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves filtered and paginated sales transaction ledger for a shop.
    Supports date range filtering, payment method/status filtering, and line item extraction.
    """
    if shop_id is None:
        membership = (
            db.query(BusinessMembership)
            .filter(BusinessMembership.user_id == user.id, BusinessMembership.is_active == True)
            .first()
        )
        if membership and membership.shop_id:
            shop_id = membership.shop_id
        elif membership and membership.business_id:
            first_shop = db.query(Shop).filter(Shop.business_id == membership.business_id, Shop.is_active == True).first()
            if first_shop:
                shop_id = first_shop.id
    if shop_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shop ID is required.")

    verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)

    s_dt = _parse_date_safe(start_date) if start_date else None
    e_dt = _parse_date_safe(end_date) if end_date else None
    if s_dt and e_dt and s_dt > e_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date range: start_date cannot be after end_date.",
        )

    query = db.query(Sale).filter(Sale.shop_id == shop_id)

    if s_dt:
        query = query.filter(Sale.sale_date >= s_dt)

    if e_dt:
        # Include entire end date day
        query = query.filter(Sale.sale_date <= e_dt + timedelta(days=1))

    if payment_method:
        query = query.filter(Sale.payment_method == payment_method)

    if payment_status:
        query = query.filter(Sale.payment_status == payment_status)

    total_count = query.count()
    offset = (page - 1) * limit
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1

    records = (
        query.order_by(desc(Sale.sale_date), desc(Sale.id))
        .offset(offset)
        .limit(limit)
        .all()
    )

    sales_out = []
    for s in records:
        items = [
            {
                "id": it.id,
                "description": it.item_description,
                "quantity": it.quantity,
                "unit_price_minor": it.unit_price_minor,
                "discount_minor": it.discount_minor,
                "line_total_minor": it.line_total_minor,
                "line_total_formatted": Money.from_minor(it.line_total_minor).format(),
            }
            for it in s.items
        ]
        sales_out.append({
            "id": s.id,
            "invoice_number": s.invoice_number,
            "sale_date": s.sale_date.isoformat() if s.sale_date else "",
            "customer_id": s.customer_id,
            "subtotal_minor": s.subtotal_minor,
            "discount_minor": s.discount_minor,
            "tax_minor": s.tax_minor,
            "total_amount_minor": s.total_amount_minor,
            "paid_amount_minor": s.paid_amount_minor,
            "total_amount_formatted": Money.from_minor(s.total_amount_minor).format(),
            "payment_status": s.payment_status,
            "payment_method": s.payment_method,
            "document_id": s.document_id,
            "items_count": len(items),
            "items": items,
        })

    return {
        "shop_id": shop_id,
        "page": page,
        "limit": limit,
        "total_count": total_count,
        "total_pages": total_pages,
        "sales": sales_out,
    }


# ==============================================================================
# 3. Expense Ledger with Filtering and Pagination
# ==============================================================================

@router.get("/expenses")
def list_expenses(
    shop_id: int = Query(...),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="rent, utilities, salaries, inventory, marketing, transport, other"),
    payment_method: Optional[str] = Query(None, description="cash, card, mobile_money, bank_transfer"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves filtered and paginated expense records for a shop.
    """
    verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)

    s_dt = _parse_date_safe(start_date) if start_date else None
    e_dt = _parse_date_safe(end_date) if end_date else None
    if s_dt and e_dt and s_dt > e_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date range: start_date cannot be after end_date.",
        )

    query = db.query(Expense).filter(Expense.shop_id == shop_id)

    if s_dt:
        query = query.filter(Expense.expense_date >= s_dt)

    if e_dt:
        query = query.filter(Expense.expense_date <= e_dt + timedelta(days=1))

    if category:
        query = query.filter(Expense.expense_category == category)

    if payment_method:
        query = query.filter(Expense.payment_method == payment_method)

    total_count = query.count()
    offset = (page - 1) * limit
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1

    records = (
        query.order_by(desc(Expense.expense_date), desc(Expense.id))
        .offset(offset)
        .limit(limit)
        .all()
    )

    expenses_out = [
        {
            "id": e.id,
            "expense_category": e.expense_category,
            "expense_date": e.expense_date.isoformat() if e.expense_date else "",
            "amount_minor": e.amount_minor,
            "amount_formatted": Money.from_minor(e.amount_minor).format(),
            "payment_method": e.payment_method,
            "payee": e.payee,
            "description": e.description,
            "document_id": e.document_id,
        }
        for e in records
    ]

    return {
        "shop_id": shop_id,
        "page": page,
        "limit": limit,
        "total_count": total_count,
        "total_pages": total_pages,
        "expenses": expenses_out,
    }


# ==============================================================================
# 4. Cash Flow Forecasting
# ==============================================================================

@router.post("/forecast")
def generate_cash_flow_forecast(
    req: ForecastRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Executes cash-flow forecasting using historical cash movements and sales/expense series.
    Uses ML Ridge Autoregressive forecasting when sufficient historical points exist;
    falls back cleanly to statistical baseline moving average otherwise.
    Stores the generated forecast run in the database and records an audit log.
    """
    verify_shop_access_dependency(shop_id=req.shop_id, user=user, db=db)
    shop = db.get(Shop, req.shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found.")

    # Gather chronological daily series
    cm_records = (
        db.query(CashMovement)
        .filter(CashMovement.shop_id == req.shop_id)
        .order_by(CashMovement.movement_date.asc())
        .all()
    )

    daily_net_map: Dict[str, int] = {}
    if cm_records:
        for cm in cm_records:
            d_str = cm.movement_date.strftime("%Y-%m-%d")
            delta = cm.amount_minor if cm.movement_type == "inflow" else -cm.amount_minor
            daily_net_map[d_str] = daily_net_map.get(d_str, 0) + delta
    else:
        # Fall back to sales vs expenses if CashMovement not populated
        sales = db.query(Sale.sale_date, Sale.total_amount_minor).filter(Sale.shop_id == req.shop_id).all()
        for s_date, s_amt in sales:
            if s_date:
                d_str = s_date.strftime("%Y-%m-%d")
                daily_net_map[d_str] = daily_net_map.get(d_str, 0) + s_amt
        expenses = db.query(Expense.expense_date, Expense.amount_minor).filter(Expense.shop_id == req.shop_id).all()
        for e_date, e_amt in expenses:
            if e_date:
                d_str = e_date.strftime("%Y-%m-%d")
                daily_net_map[d_str] = daily_net_map.get(d_str, 0) - e_amt

    # Sort chronological daily net cash list
    sorted_days = sorted(daily_net_map.keys())
    historical_series = [daily_net_map[d] for d in sorted_days]

    # Forecast execution
    if req.method == "moving_average" or len(historical_series) < 12:
        forecast_res = CashFlowForecaster.statistical_baseline_forecast(
            historical_net_cash_minor=historical_series,
            horizon_days=req.horizon_days,
        )
    else:
        forecast_res = CashFlowForecaster.ml_lagged_forecast(
            historical_daily_series=historical_series,
            horizon_days=req.horizon_days,
        )

    # Persist in Forecast table
    now = utc_now()
    forecast_rec = Forecast(
        business_id=shop.business_id,
        shop_id=shop.id,
        target_metric="daily_cashflow",
        forecast_date_start=now,
        forecast_date_end=now + timedelta(days=req.horizon_days),
        predictions_json=json.dumps(forecast_res["point_forecast_minor"]),
        lower_bound_json=json.dumps(forecast_res["lower_bound_80_minor"]),
        upper_bound_json=json.dumps(forecast_res["upper_bound_80_minor"]),
        is_synthetic=False,
    )
    db.add(forecast_rec)

    # Audit log
    AuditRepository(db).log_action(
        action="run_cashflow_forecast",
        entity_type="forecast",
        entity_id=None,
        business_id=shop.business_id,
        shop_id=shop.id,
        user_id=user.id,
        new_values=json.dumps({
            "horizon_days": req.horizon_days,
            "method": forecast_res["method"],
            "historical_points": len(historical_series),
        }),
    )
    db.commit()

    currency = shop.business.currency if shop.business else "BDT"

    return {
        "shop_id": req.shop_id,
        "horizon_days": req.horizon_days,
        "method_applied": forecast_res["method"],
        "historical_data_points": len(historical_series),
        "point_forecast_minor": forecast_res["point_forecast_minor"],
        "lower_bound_80_minor": forecast_res["lower_bound_80_minor"],
        "upper_bound_80_minor": forecast_res["upper_bound_80_minor"],
        "point_forecast_formatted": [
            Money.from_minor(val, currency).format() for val in forecast_res["point_forecast_minor"]
        ],
        "created_at": now.isoformat(),
    }


@router.get("/forecast")
def get_latest_forecast(
    shop_id: int = Query(...),
    target_metric: str = Query("daily_cashflow"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves the most recent saved forecast for a shop.
    """
    verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)
    rec = (
        db.query(Forecast)
        .filter(Forecast.shop_id == shop_id, Forecast.target_metric == target_metric)
        .order_by(desc(Forecast.id))
        .first()
    )
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No forecast found for shop {shop_id} and metric '{target_metric}'.",
        )

    points = json.loads(rec.predictions_json) if rec.predictions_json else []
    lower = json.loads(rec.lower_bound_json) if rec.lower_bound_json else []
    upper = json.loads(rec.upper_bound_json) if rec.upper_bound_json else []

    return {
        "id": rec.id,
        "shop_id": rec.shop_id,
        "target_metric": rec.target_metric,
        "forecast_date_start": rec.forecast_date_start.isoformat(),
        "forecast_date_end": rec.forecast_date_end.isoformat(),
        "horizon_days": len(points),
        "point_forecast_minor": points,
        "lower_bound_80_minor": lower,
        "upper_bound_80_minor": upper,
        "created_at": rec.created_at.isoformat(),
    }


# ==============================================================================
# 5. Loan Risk & Financing Assessment
# ==============================================================================

@router.post("/loan-risk-assessment")
def assess_loan_risk(
    req: LoanRiskRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Evaluates SME creditworthiness using explainable financial policy rules.
    Audits Debt Service Coverage Ratio (DSCR), debt-to-income limits, and max safe borrowing capacity.
    Automatically computes trailing 30-day revenue and expenses if not explicitly supplied.
    """
    verify_shop_access_dependency(shop_id=req.shop_id, user=user, db=db)
    shop = db.get(Shop, req.shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found.")

    # Auto-compute monthly revenue if omitted
    monthly_rev = req.monthly_revenue_minor
    if monthly_rev is None:
        total_rev = (
            db.query(func.coalesce(func.sum(Sale.total_amount_minor), 0))
            .filter(Sale.shop_id == req.shop_id)
            .scalar()
        ) or 0
        sale_days = max(1, db.query(Sale.sale_date).filter(Sale.shop_id == req.shop_id).distinct().count())
        daily_rev = total_rev / sale_days if sale_days > 0 else 0
        monthly_rev = int(round(daily_rev * 30))

    # Auto-compute monthly expenses if omitted
    monthly_exp = req.monthly_expenses_minor
    if monthly_exp is None:
        total_exp = (
            db.query(func.coalesce(func.sum(Expense.amount_minor), 0))
            .filter(Expense.shop_id == req.shop_id)
            .scalar()
        ) or 0
        exp_days = max(1, db.query(Expense.expense_date).filter(Expense.shop_id == req.shop_id).distinct().count())
        daily_exp = total_exp / exp_days if exp_days > 0 else 0
        monthly_exp = int(round(daily_exp * 30))

    eval_result = TransparentLoanRiskEngine.evaluate_loan_scenario(
        monthly_revenue_minor=monthly_rev,
        monthly_expenses_minor=monthly_exp,
        existing_monthly_debt_minor=req.existing_monthly_debt_minor,
        requested_amount_minor=req.requested_amount_minor,
        tenure_months=req.tenure_months,
        annual_interest_rate_pct=req.annual_interest_rate_pct,
        processing_fee_bps=req.processing_fee_bps,
    )

    # Log evaluation in audit repository
    AuditRepository(db).log_action(
        action="evaluate_loan_risk",
        entity_type="loan_evaluation",
        entity_id=None,
        business_id=shop.business_id,
        shop_id=shop.id,
        user_id=user.id,
        new_values=json.dumps({
            "requested_amount_minor": req.requested_amount_minor,
            "recommendation_status": eval_result["recommendation_status"],
            "dscr_ratio": eval_result["dscr_ratio"],
        }),
    )
    db.commit()

    currency = shop.business.currency if shop.business else "BDT"

    return {
        **eval_result,
        "requested_amount_formatted": Money.from_minor(req.requested_amount_minor, currency).format(),
        "monthly_emi_formatted": Money.from_minor(eval_result["monthly_emi_minor"], currency).format(),
        "total_interest_formatted": Money.from_minor(eval_result["total_interest_minor"], currency).format(),
        "total_payment_formatted": Money.from_minor(eval_result["total_payment_minor"], currency).format(),
        "max_safe_borrowing_formatted": Money.from_minor(eval_result["max_safe_borrowing_minor"], currency).format(),
    }


@router.get("/loan-products")
def list_loan_products(
    shop_id: Optional[int] = Query(None),
    requested_amount_minor: Optional[int] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lists demo loan offerings from participating demo partner banks.
    Explicitly marked as synthetic demo data for competition evaluation.
    """
    if shop_id:
        verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)

    query = db.query(LoanProduct).join(DemoBank)
    if requested_amount_minor:
        query = query.filter(
            and_(
                LoanProduct.min_amount_minor <= requested_amount_minor,
                LoanProduct.max_amount_minor >= requested_amount_minor,
            )
        )

    products = query.order_by(LoanProduct.annual_interest_rate_bps.asc()).all()
    return [
        {
            "id": p.id,
            "bank_name": p.bank.name if p.bank else "Demo Bank",
            "bank_code": p.bank.code if p.bank else "DEMO",
            "product_name": p.name,
            "min_amount_minor": p.min_amount_minor,
            "max_amount_minor": p.max_amount_minor,
            "min_tenure_months": p.min_tenure_months,
            "max_tenure_months": p.max_tenure_months,
            "annual_interest_rate_pct": p.annual_interest_rate_bps / 100.0,
            "interest_calc_type": p.interest_calc_type,
            "processing_fee_pct": p.processing_fee_bps / 100.0,
            "is_synthetic": p.is_synthetic,
            "regulatory_disclaimer": "Simulated catalog only. Not an actual loan offer or commitment.",
        }
        for p in products
    ]


# ==============================================================================
# 6. Inventory & Receivables Summaries
# ==============================================================================

@router.get("/inventory-summary")
def get_inventory_summary(
    shop_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Calculates stock levels, total stock valuation, margin potential, and low-stock alerts.
    """
    verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)
    shop = db.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found.")

    products = db.query(Product).filter(Product.shop_id == shop_id).all()
    total_cost_minor = sum(p.current_stock * p.cost_price_minor for p in products if p.current_stock > 0)
    total_retail_minor = sum(p.current_stock * p.selling_price_minor for p in products if p.current_stock > 0)
    potential_margin_minor = total_retail_minor - total_cost_minor

    low_stock = [p for p in products if p.current_stock <= p.min_stock_alert]
    low_stock_sorted = sorted(low_stock, key=lambda x: (x.current_stock / max(1, x.min_stock_alert)))[:10]

    currency = shop.business.currency if shop.business else "BDT"

    return {
        "shop_id": shop_id,
        "total_skus": len(products),
        "total_units_in_stock": sum(p.current_stock for p in products),
        "total_cost_minor": total_cost_minor,
        "total_cost_formatted": Money.from_minor(total_cost_minor, currency).format(),
        "total_retail_minor": total_retail_minor,
        "total_retail_formatted": Money.from_minor(total_retail_minor, currency).format(),
        "potential_margin_minor": potential_margin_minor,
        "potential_margin_formatted": Money.from_minor(potential_margin_minor, currency).format(),
        "low_stock_items_count": len(low_stock),
        "low_stock_alerts": [
            {
                "product_id": p.id,
                "sku": p.sku,
                "name": p.name,
                "current_stock": p.current_stock,
                "min_stock_alert": p.min_stock_alert,
                "cost_price_minor": p.cost_price_minor,
            }
            for p in low_stock_sorted
        ],
    }


@router.get("/receivables-summary")
def get_receivables_summary(
    shop_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Calculates outstanding receivables, overdue amounts, and aging buckets (0-30, 31-60, 61-90, 90+ days).
    """
    verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)
    shop = db.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found.")

    receivables = (
        db.query(Receivable)
        .filter(Receivable.shop_id == shop_id, Receivable.status.in_(["pending", "partial"]))
        .all()
    )

    now_naive = _make_naive_utc(utc_now())

    bucket_0_30 = 0
    bucket_31_60 = 0
    bucket_61_90 = 0
    bucket_90_plus = 0
    overdue_count = 0
    total_outstanding_minor = 0

    for r in receivables:
        amt = r.outstanding_amount_minor
        total_outstanding_minor += amt

        due_date_naive = _make_naive_utc(r.due_date)
        if due_date_naive and due_date_naive < now_naive:
            overdue_count += 1
            days_overdue = (now_naive - due_date_naive).days
            if days_overdue <= 30:
                bucket_0_30 += amt
            elif days_overdue <= 60:
                bucket_31_60 += amt
            elif days_overdue <= 90:
                bucket_61_90 += amt
            else:
                bucket_90_plus += amt
        else:
            bucket_0_30 += amt

    currency = shop.business.currency if shop.business else "BDT"

    return {
        "shop_id": shop_id,
        "total_receivables_count": len(receivables),
        "total_outstanding_minor": total_outstanding_minor,
        "total_outstanding_formatted": Money.from_minor(total_outstanding_minor, currency).format(),
        "overdue_count": overdue_count,
        "aging_buckets": {
            "current_or_0_30_days_minor": bucket_0_30,
            "current_or_0_30_days_formatted": Money.from_minor(bucket_0_30, currency).format(),
            "overdue_31_60_days_minor": bucket_31_60,
            "overdue_31_60_days_formatted": Money.from_minor(bucket_31_60, currency).format(),
            "overdue_61_90_days_minor": bucket_61_90,
            "overdue_61_90_days_formatted": Money.from_minor(bucket_61_90, currency).format(),
            "overdue_90_plus_days_minor": bucket_90_plus,
            "overdue_90_plus_days_formatted": Money.from_minor(bucket_90_plus, currency).format(),
        },
    }


# ==============================================================================
# 7. Existing Calculations (Preserved)
# ==============================================================================

@router.get("/profit-loss")
def get_profit_and_loss(
    shop_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Calculates deterministic Profit & Loss statement from database ledger."""
    verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)

    sales = db.query(Sale.total_amount_minor).filter_by(shop_id=shop_id).all()
    purchases = db.query(Purchase.total_amount_minor).filter_by(shop_id=shop_id).all()
    expenses = db.query(Expense.amount_minor).filter_by(shop_id=shop_id).all()

    sales_minor = [s[0] for s in sales]
    cogs_minor = [p[0] for p in purchases]
    exp_minor = [e[0] for e in expenses]

    pl = FinancialCalculator.calculate_profit_and_loss(
        sales_minor=sales_minor,
        cogs_minor=cogs_minor,
        operating_expenses_minor=exp_minor,
    )

    return {
        "revenue": Money.from_minor(pl.revenue_minor).format(),
        "revenue_minor": pl.revenue_minor,
        "cogs": Money.from_minor(pl.cogs_minor).format(),
        "cogs_minor": pl.cogs_minor,
        "gross_profit": Money.from_minor(pl.gross_profit_minor).format(),
        "gross_profit_minor": pl.gross_profit_minor,
        "operating_expenses": Money.from_minor(pl.operating_expenses_minor).format(),
        "operating_expenses_minor": pl.operating_expenses_minor,
        "net_profit": Money.from_minor(pl.net_profit_minor).format(),
        "net_profit_minor": pl.net_profit_minor,
        "gross_margin_pct": pl.gross_margin_pct,
        "net_margin_pct": pl.net_margin_pct,
    }


@router.get("/cash-flow")
def get_cash_flow(
    shop_id: int,
    opening_balance_minor: int = 0,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Calculates deterministic Cash Flow from recorded payment transactions."""
    verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)

    inflow_records = (
        db.query(Payment.amount_minor)
        .filter(Payment.shop_id == shop_id, Payment.payment_type.in_(["customer_inflow", "loan_disbursement"]))
        .all()
    )
    outflow_records = (
        db.query(Payment.amount_minor)
        .filter(Payment.shop_id == shop_id, Payment.payment_type.in_(["supplier_outflow", "expense_outflow", "loan_repayment"]))
        .all()
    )

    inflows = [r[0] for r in inflow_records]
    outflows = [r[0] for r in outflow_records]

    # Graceful fallback to CashMovement if Payment table is empty
    if not inflows and not outflows:
        cm_inflows = [r[0] for r in db.query(CashMovement.amount_minor).filter(CashMovement.shop_id == shop_id, CashMovement.movement_type == "inflow").all()]
        cm_outflows = [r[0] for r in db.query(CashMovement.amount_minor).filter(CashMovement.shop_id == shop_id, CashMovement.movement_type == "outflow").all()]
        if cm_inflows or cm_outflows:
            inflows = cm_inflows
            outflows = cm_outflows

    cf = FinancialCalculator.calculate_cash_flow(
        opening_balance_minor=opening_balance_minor,
        inflows_minor=inflows,
        outflows_minor=outflows,
    )

    return {
        "opening_balance": Money.from_minor(cf.opening_balance_minor).format(),
        "total_inflows": Money.from_minor(cf.cash_inflows_minor).format(),
        "total_outflows": Money.from_minor(cf.cash_outflows_minor).format(),
        "net_cash_flow": Money.from_minor(cf.net_cash_flow_minor).format(),
        "closing_balance": Money.from_minor(cf.closing_balance_minor).format(),
        "closing_balance_minor": cf.closing_balance_minor,
    }


@router.post("/loan-comparison")
def compare_loans(req: LoanComparisonRequest):
    """Compares Reducing Balance EMI vs Flat Rate with hidden APR transparency."""
    try:
        res = FinancialCalculator.calculate_loan_comparison(
            principal_minor=req.principal_minor,
            annual_interest_rate_pct=req.annual_interest_rate_pct,
            tenure_months=req.tenure_months,
            processing_fee_bps=req.processing_fee_bps,
        )
        return {
            "loan_amount": Money.from_minor(res.loan_amount_minor).format(),
            "tenure_months": res.tenure_months,
            "reducing_monthly_emi": Money.from_minor(res.reducing_monthly_emi_minor).format(),
            "reducing_total_interest": Money.from_minor(res.reducing_total_interest_minor).format(),
            "reducing_total_payment": Money.from_minor(res.reducing_total_payment_minor).format(),
            "flat_monthly_installment": Money.from_minor(res.flat_monthly_installment_minor).format(),
            "flat_total_interest": Money.from_minor(res.flat_total_interest_minor).format(),
            "flat_total_payment": Money.from_minor(res.flat_total_payment_minor).format(),
            "flat_rate_penalty": Money.from_minor(res.flat_rate_penalty_minor).format(),
            "effective_apr_reducing": f"{res.effective_apr_reducing_pct:.2f}%",
            "effective_apr_flat": f"{res.effective_apr_flat_pct:.2f}%",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/break-even")
def calculate_break_even(req: BreakEvenRequest):
    """Calculates contribution margin, break-even unit sales, and break-even revenue."""
    try:
        res = FinancialCalculator.calculate_break_even(
            fixed_costs_minor=req.fixed_costs_minor,
            selling_price_per_unit_minor=req.selling_price_per_unit_minor,
            variable_cost_per_unit_minor=req.variable_cost_per_unit_minor,
        )
        return {
            "fixed_costs": Money.from_minor(res.fixed_costs_minor).format(),
            "contribution_margin_per_unit": Money.from_minor(res.contribution_margin_per_unit_minor).format(),
            "contribution_margin_ratio": f"{res.contribution_margin_ratio * 100:.2f}%",
            "break_even_units": res.break_even_units,
            "break_even_revenue": Money.from_minor(res.break_even_revenue_minor).format(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================================================
# 7. Reactive SME Loan & DSCR Underwriting Engine & Institutional Dossier
# ==============================================================================

@router.get("/loan-underwriting-data")
def get_loan_underwriting_data(
    shop_id: Optional[int] = Query(None),
    principal_minor: int = Query(80000000, gt=0),
    tenure_months: int = Query(24, gt=0),
    annual_interest_rate_pct: float = Query(11.5, ge=0),
    loan_purpose: str = Query("working_capital"),
    existing_monthly_debt_minor: int = Query(0, ge=0),
    monthly_noi_minor: Optional[int] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Computes real-time reactive underwriting metrics:
    Trailing 30-day NOI, debt capacity, reducing balance EMI, projected DSCR,
    and live eligibility matches for all commercial SME bank products.
    """
    if shop_id is None:
        membership = (
            db.query(BusinessMembership)
            .filter(BusinessMembership.user_id == user.id, BusinessMembership.is_active == True)
            .first()
        )
        if membership and membership.shop_id:
            shop_id = membership.shop_id
        elif membership and membership.business_id:
            first_shop = db.query(Shop).filter(Shop.business_id == membership.business_id, Shop.is_active == True).first()
            if first_shop:
                shop_id = first_shop.id
        else:
            shop_id = 28  # Fallback to demo main branch

    verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)
    shop = db.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found.")

    business = shop.business or db.query(Business).filter_by(id=shop.business_id).first()
    currency = business.currency if business else "BDT"

    # 1. Historical operating cash flow & sufficiency audit
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    trailing_start = now - timedelta(days=30)

    sales_30d = (
        db.query(func.coalesce(func.sum(Sale.total_amount_minor), 0))
        .filter(Sale.shop_id == shop_id, Sale.sale_date >= trailing_start)
        .scalar()
    ) or 0
    sales_cnt = db.query(Sale).filter(Sale.shop_id == shop_id).count()

    exp_30d = (
        db.query(func.coalesce(func.sum(Expense.amount_minor), 0))
        .filter(Expense.shop_id == shop_id, Expense.expense_date >= trailing_start)
        .scalar()
    ) or 0

    has_sufficient_data = sales_cnt > 0

    # Determine Net Operating Income (NOI)
    # If explicitly supplied or modeled by user: respect user value
    # Else if historical sales exist: calculate trailing NOI
    # Else fallback to standard demo baseline (250,000 BDT) with clear notation
    if monthly_noi_minor is not None:
        effective_noi_minor = monthly_noi_minor
        is_modeled_noi = True
    elif sales_30d > 0:
        effective_noi_minor = max(0, sales_30d - exp_30d)
        if effective_noi_minor == 0 and sales_30d > 0:
            effective_noi_minor = 25000000  # Fallback to standard baseline if expenses exactly matched
        is_modeled_noi = False
    else:
        effective_noi_minor = 25000000  # ৳ 250,000 demo baseline
        is_modeled_noi = True

    # 2. Financial calculation: Reducing Balance EMI
    try:
        loan_comp = FinancialCalculator.calculate_loan_comparison(
            principal_minor=principal_minor,
            annual_interest_rate_pct=annual_interest_rate_pct,
            tenure_months=tenure_months,
            processing_fee_bps=100,
        )
        monthly_emi_minor = loan_comp.reducing_monthly_emi_minor
        total_interest_minor = loan_comp.reducing_total_interest_minor
        total_payment_minor = loan_comp.reducing_total_payment_minor
        processing_fee_minor = loan_comp.processing_fee_minor
    except Exception:
        # Edge-case fallback (zero-interest or division protection)
        monthly_emi_minor = principal_minor // max(1, tenure_months)
        total_interest_minor = 0
        total_payment_minor = principal_minor
        processing_fee_minor = principal_minor // 100

    # 3. DSCR and DTI calculations with zero guards
    total_monthly_debt_service = existing_monthly_debt_minor + monthly_emi_minor
    if total_monthly_debt_service > 0 and effective_noi_minor > 0:
        dscr = round(effective_noi_minor / total_monthly_debt_service, 2)
        dti = round((total_monthly_debt_service / effective_noi_minor) * 100, 1)
    elif effective_noi_minor <= 0:
        dscr = 0.0
        dti = 999.0
    else:
        dscr = 999.0
        dti = 0.0

    # 4. Underwriting Suitability Verdict
    if effective_noi_minor <= 0:
        suitability_verdict = "INSUFFICIENT NOI"
        suitability_badge_class = "bg-rose-500/20 text-rose-400 border-rose-500/40"
        verdict_rationale = "Net Operating Income is zero or negative. Underwriting covenants require positive operational cash flow."
    elif dscr >= 1.50 and dti <= 40.0:
        suitability_verdict = "PRIME APPROVAL"
        suitability_badge_class = "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
        verdict_rationale = f"DSCR of {dscr:.2f}x strongly exceeds healthy threshold (>= 1.25x). Proposed debt service is well within prudent cash flow capacity."
    elif dscr >= 1.20:
        suitability_verdict = "CONDITIONAL APPROVAL"
        suitability_badge_class = "bg-amber-500/20 text-amber-300 border-amber-500/40"
        verdict_rationale = f"DSCR of {dscr:.2f}x meets baseline coverage but provides narrow buffer against demand volatility. Collateral or longer tenure advised."
    else:
        suitability_verdict = "HIGH DEBT RISK"
        suitability_badge_class = "bg-rose-500/20 text-rose-400 border-rose-500/40"
        verdict_rationale = f"Projected DSCR of {dscr:.2f}x fails minimum regulatory covenant (1.25x). High probability of repayment strain."

    # 5. Dynamic Bank Products Matching
    raw_products = db.query(LoanProduct).join(DemoBank).order_by(LoanProduct.annual_interest_rate_bps.asc()).all()
    evaluated_products = []

    for p in raw_products:
        crit = {}
        if p.eligibility_criteria_json:
            try:
                crit = json.loads(p.eligibility_criteria_json)
            except Exception:
                crit = {}

        min_dscr = crit.get("min_dscr", 1.25)
        collateral = crit.get("collateral", "Corporate / Personal Guarantee")
        disbursement = crit.get("disbursement", "48 Hours Rapid")
        supported_purposes = crit.get("supported_purposes", ["working_capital", "equipment", "branch", "refinance"])
        required_docs = crit.get("required_docs", ["Trade License", "Bank Statement", "NID"])

        # Evaluate match
        if principal_minor > p.max_amount_minor:
            m_status = "EXCEEDS FACILITY"
            m_badge = "bg-rose-500/20 text-rose-400 border-rose-500/30"
            m_reason = f"Requested principal exceeds facility ceiling of {Money.from_minor(p.max_amount_minor, currency).format()}"
        elif principal_minor < p.min_amount_minor:
            m_status = "BELOW MINIMUM"
            m_badge = "bg-amber-500/20 text-amber-300 border-amber-500/30"
            m_reason = f"Requested principal is below facility minimum of {Money.from_minor(p.min_amount_minor, currency).format()}"
        elif tenure_months < p.min_tenure_months or tenure_months > p.max_tenure_months:
            m_status = "TENURE MISMATCH"
            m_badge = "bg-amber-500/20 text-amber-300 border-amber-500/30"
            m_reason = f"Facility tenure must be between {p.min_tenure_months} and {p.max_tenure_months} months"
        elif supported_purposes and loan_purpose not in supported_purposes:
            m_status = "PURPOSE INELIGIBLE"
            m_badge = "bg-amber-500/20 text-amber-300 border-amber-500/30"
            m_reason = f"Product is designated for {', '.join(supported_purposes).replace('_', ' ')}"
        elif dscr < min_dscr:
            m_status = "INSUFFICIENT DSCR"
            m_badge = "bg-rose-500/20 text-rose-400 border-rose-500/30"
            m_reason = f"Projected DSCR ({dscr:.2f}x) does not satisfy product threshold of {min_dscr:.2f}x"
        else:
            m_status = "MATCHED"
            m_badge = "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
            m_reason = f"Pre-screened and compliant with bank covenants (DSCR >= {min_dscr:.2f}x, amount & tenure within policy)"

        evaluated_products.append({
            "id": p.id,
            "bank_id": p.bank_id,
            "bank_name": p.bank.name if p.bank else "Demo Bank",
            "bank_code": p.bank.code if p.bank else "DEMO",
            "product_name": p.name,
            "annual_interest_rate_pct": p.annual_interest_rate_bps / 100.0,
            "min_amount_minor": p.min_amount_minor,
            "max_amount_minor": p.max_amount_minor,
            "max_amount_formatted": Money.from_minor(p.max_amount_minor, currency).format(),
            "min_tenure_months": p.min_tenure_months,
            "max_tenure_months": p.max_tenure_months,
            "min_dscr": min_dscr,
            "collateral": collateral,
            "disbursement": disbursement,
            "supported_purposes": supported_purposes,
            "required_docs": required_docs,
            "match_status": m_status,
            "match_badge_class": m_badge,
            "match_reason": m_reason,
            "is_synthetic": True,
        })

    return {
        "shop_id": shop.id,
        "shop_name": shop.name,
        "business_name": business.name if business else "Demo Business",
        "currency": currency,
        "has_sufficient_data": has_sufficient_data,
        "is_modeled_noi": is_modeled_noi,
        "monthly_noi_minor": effective_noi_minor,
        "monthly_noi_formatted": Money.from_minor(effective_noi_minor, currency).format(),
        "existing_monthly_debt_minor": existing_monthly_debt_minor,
        "existing_monthly_debt_formatted": Money.from_minor(existing_monthly_debt_minor, currency).format(),
        "total_monthly_debt_service_minor": total_monthly_debt_service,
        "total_monthly_debt_service_formatted": Money.from_minor(total_monthly_debt_service, currency).format(),
        "calculated_terms": {
            "requested_principal_minor": principal_minor,
            "requested_principal_formatted": Money.from_minor(principal_minor, currency).format(),
            "tenure_months": tenure_months,
            "annual_interest_rate_pct": annual_interest_rate_pct,
            "monthly_emi_minor": monthly_emi_minor,
            "monthly_emi_formatted": Money.from_minor(monthly_emi_minor, currency).format(),
            "total_interest_minor": total_interest_minor,
            "total_interest_formatted": Money.from_minor(total_interest_minor, currency).format(),
            "total_payment_minor": total_payment_minor,
            "total_payment_formatted": Money.from_minor(total_payment_minor, currency).format(),
            "processing_fee_minor": processing_fee_minor,
            "processing_fee_formatted": Money.from_minor(processing_fee_minor, currency).format(),
            "projected_dscr": dscr,
            "projected_dscr_formatted": f"{dscr:.2f}x",
            "dti_pct": dti,
            "dti_formatted": f"{dti:.1f}%",
            "suitability_verdict": suitability_verdict,
            "suitability_badge_class": suitability_badge_class,
            "verdict_rationale": verdict_rationale,
        },
        "products": evaluated_products,
        "is_synthetic": True,
        "simulation_disclaimer": "Simulated demonstration catalog pre-screened against Bangladesh Bank & China SME covenants. Not a binding credit commitment.",
    }


@router.post("/loan-packet/generate")
def generate_loan_packet(
    req: LoanPacketGenerateRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Asynchronously compiles an institutional SME Loan Underwriting Dossier:
    - Performs server-side underwriting validation
    - Enforces idempotency / 15s duplicate request protection
    - Persists formal LoanApplication record with status='demo_assessed'
    - Persists formal LoanScenario record
    - Writes immutable tamper-evident AuditLog entry
    - Returns structured packet payload for modal rendering and PDF streaming
    """
    verify_shop_access_dependency(shop_id=req.shop_id, user=user, db=db)
    shop = db.get(Shop, req.shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found.")

    business = shop.business or db.query(Business).filter_by(id=shop.business_id).first()
    currency = business.currency if business else "BDT"

    # Idempotency / Duplicate request debounce (15-second window)
    fifteen_sec_ago = utc_now() - timedelta(seconds=15)
    recent_app = (
        db.query(LoanApplication)
        .filter(
            LoanApplication.shop_id == req.shop_id,
            LoanApplication.requested_amount_minor == req.requested_amount_minor,
            LoanApplication.tenure_months == req.tenure_months,
            LoanApplication.created_at >= fifteen_sec_ago,
        )
        .order_by(desc(LoanApplication.created_at))
        .first()
    )
    if recent_app and recent_app.evaluation_notes:
        try:
            cached_packet = json.loads(recent_app.evaluation_notes)
            return cached_packet
        except Exception:
            pass

    # 1. Determine Effective Operating Income
    if req.monthly_noi_minor is not None:
        effective_noi_minor = req.monthly_noi_minor
    else:
        sales_30d = (
            db.query(func.coalesce(func.sum(Sale.total_amount_minor), 0))
            .filter(Sale.shop_id == req.shop_id, Sale.sale_date >= utc_now() - timedelta(days=30))
            .scalar()
        ) or 0
        exp_30d = (
            db.query(func.coalesce(func.sum(Expense.amount_minor), 0))
            .filter(Expense.shop_id == req.shop_id, Expense.expense_date >= utc_now() - timedelta(days=30))
            .scalar()
        ) or 0
        effective_noi_minor = max(0, sales_30d - exp_30d) if sales_30d > 0 else 25000000

    # 2. Financial calculation
    try:
        loan_comp = FinancialCalculator.calculate_loan_comparison(
            principal_minor=req.requested_amount_minor,
            annual_interest_rate_pct=req.annual_interest_rate_pct,
            tenure_months=req.tenure_months,
            processing_fee_bps=100,
        )
        emi_minor = loan_comp.reducing_monthly_emi_minor
        total_interest_minor = loan_comp.reducing_total_interest_minor
        total_payment_minor = loan_comp.reducing_total_payment_minor
        fee_minor = loan_comp.processing_fee_minor
    except Exception:
        emi_minor = req.requested_amount_minor // max(1, req.tenure_months)
        total_interest_minor = 0
        total_payment_minor = req.requested_amount_minor
        fee_minor = req.requested_amount_minor // 100

    total_monthly_debt_service = req.existing_monthly_debt_minor + emi_minor
    if total_monthly_debt_service > 0 and effective_noi_minor > 0:
        dscr = round(effective_noi_minor / total_monthly_debt_service, 2)
        dti = round((total_monthly_debt_service / effective_noi_minor) * 100, 1)
    elif effective_noi_minor <= 0:
        dscr = 0.0
        dti = 999.0
    else:
        dscr = 999.0
        dti = 0.0

    if effective_noi_minor <= 0:
        suitability_verdict = "INSUFFICIENT NOI"
        verdict_badge_class = "bg-rose-500/20 text-rose-400 border-rose-500/40"
        verdict_rationale = "Operating income is currently insufficient to service debt."
    elif dscr >= 1.50 and dti <= 40.0:
        suitability_verdict = "PRIME APPROVAL"
        verdict_badge_class = "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
        verdict_rationale = f"DSCR of {dscr:.2f}x strongly exceeds healthy benchmark (>= 1.25x)."
    elif dscr >= 1.20:
        suitability_verdict = "CONDITIONAL APPROVAL"
        verdict_badge_class = "bg-amber-500/20 text-amber-300 border-amber-500/40"
        verdict_rationale = f"DSCR of {dscr:.2f}x meets baseline coverage. Prudent collateral recommended."
    else:
        suitability_verdict = "HIGH DEBT RISK"
        verdict_badge_class = "bg-rose-500/20 text-rose-400 border-rose-500/40"
        verdict_rationale = f"Projected DSCR of {dscr:.2f}x is below standard regulatory threshold of 1.25x."

    # 3. Evaluate bank products
    products = db.query(LoanProduct).join(DemoBank).all()
    bank_matches = []
    chosen_product = None

    purpose_map = {
        "working_capital": "Working Capital & Inventory Expansion",
        "equipment": "Retail POS Hardware & Store Renovation",
        "branch": "Opening New Retail Branch",
        "refinance": "Debt Consolidation & Restructuring",
    }
    purpose_label = purpose_map.get(req.loan_purpose, req.loan_purpose.replace("_", " ").title())

    for p in products:
        crit = json.loads(p.eligibility_criteria_json) if p.eligibility_criteria_json else {}
        min_d = crit.get("min_dscr", 1.25)
        sup_p = crit.get("supported_purposes", ["working_capital", "equipment", "branch", "refinance"])
        coll = crit.get("collateral", "Floating Charge")
        disb = crit.get("disbursement", "48 Hours Rapid")

        if req.requested_amount_minor > p.max_amount_minor:
            m_stat = "EXCEEDS FACILITY"
        elif req.requested_amount_minor < p.min_amount_minor:
            m_stat = "BELOW MINIMUM"
        elif req.tenure_months < p.min_tenure_months or req.tenure_months > p.max_tenure_months:
            m_stat = "TENURE MISMATCH"
        elif sup_p and req.loan_purpose not in sup_p:
            m_stat = "PURPOSE INELIGIBLE"
        elif dscr < min_d:
            m_stat = "INSUFFICIENT DSCR"
        else:
            m_stat = "MATCHED"

        bm_item = {
            "product_id": p.id,
            "bank_id": p.bank_id,
            "bank_name": p.bank.name if p.bank else "Demo Bank",
            "product_name": p.name,
            "max_amount_formatted": Money.from_minor(p.max_amount_minor, currency).format(),
            "annual_interest_rate_pct": p.annual_interest_rate_bps / 100.0,
            "min_dscr": min_d,
            "match_status": m_stat,
            "collateral": coll,
            "disbursement": disb,
        }
        bank_matches.append(bm_item)

        if req.selected_product_id and p.id == req.selected_product_id:
            chosen_product = p
        elif chosen_product is None and m_stat == "MATCHED":
            chosen_product = p

    if not chosen_product and products:
        chosen_product = products[0]

    # Generate formal application reference
    timestamp_sec = int(datetime.now(timezone.utc).timestamp())
    app_number = f"SME-PKT-{shop.id}-{timestamp_sec}"

    # Stress testing sensitivity matrix
    # Stress 1: +100 bps rate hike
    comp_s1 = FinancialCalculator.calculate_loan_comparison(
        principal_minor=req.requested_amount_minor,
        annual_interest_rate_pct=req.annual_interest_rate_pct + 1.0,
        tenure_months=req.tenure_months,
        processing_fee_bps=100,
    )
    s1_dscr = round(effective_noi_minor / (req.existing_monthly_debt_minor + comp_s1.reducing_monthly_emi_minor), 2) if (req.existing_monthly_debt_minor + comp_s1.reducing_monthly_emi_minor) > 0 else 0.0

    # Stress 2: -15% Revenue drop on NOI
    s2_noi = int(effective_noi_minor * 0.85)
    s2_dscr = round(s2_noi / total_monthly_debt_service, 2) if total_monthly_debt_service > 0 else 0.0

    stress_tests = [
        {
            "scenario": "Baseline Scenario (Requested Terms)",
            "rate": f"{req.annual_interest_rate_pct:.2f}%",
            "noi_impact": "None (Current NOI)",
            "monthly_emi_formatted": Money.from_minor(emi_minor, currency).format(),
            "projected_dscr": f"{dscr:.2f}x",
            "verdict": suitability_verdict,
        },
        {
            "scenario": "Rate Shock (+100 bps Interest Spike)",
            "rate": f"{req.annual_interest_rate_pct + 1.0:.2f}%",
            "noi_impact": "Unchanged",
            "monthly_emi_formatted": Money.from_minor(comp_s1.reducing_monthly_emi_minor, currency).format(),
            "projected_dscr": f"{s1_dscr:.2f}x",
            "verdict": "SUSTAINABLE" if s1_dscr >= 1.25 else ("TIGHT" if s1_dscr >= 1.05 else "VULNERABLE"),
        },
        {
            "scenario": "Revenue Shock (-15% Sales Contraction)",
            "rate": f"{req.annual_interest_rate_pct:.2f}%",
            "noi_impact": "-15% Operating Margin",
            "monthly_emi_formatted": Money.from_minor(emi_minor, currency).format(),
            "projected_dscr": f"{s2_dscr:.2f}x",
            "verdict": "SUSTAINABLE" if s2_dscr >= 1.25 else ("TIGHT" if s2_dscr >= 1.05 else "DEFICIT RISK"),
        },
    ]

    # Required Documents Checklist
    doc_checklist = [
        "Certified Copy of Valid Municipal Trade License (2025-2026)",
        "Consecutive 12-Month Audited or E-Banking Transaction Statements",
        "Proprietor / Director National ID (Smart NID) & Biometric Verification",
        "e-TIN Certificate & Income Tax Return Acknowledgement Receipt",
        "Commercial Rental / Tenancy Deed Agreement for Operating Premises",
        "Current Physical Inventory Stock Register & Supplier Payables Schedule",
    ]

    packet_data = {
        "application_number": app_number,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_at_formatted": datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC"),
        "business_name": business.name if business else "Demo Business",
        "shop_name": shop.name,
        "currency": currency,
        "tax_id": business.tax_id if business and business.tax_id else "BIN-99281-002",
        "loan_purpose": req.loan_purpose,
        "loan_purpose_label": purpose_label,
        "recommended_product": {
            "product_name": chosen_product.name if chosen_product else "SME Loan",
            "bank_name": chosen_product.bank.name if (chosen_product and chosen_product.bank) else "BRAC Bank Ltd. (Demo)",
            "annual_interest_rate_pct": (chosen_product.annual_interest_rate_bps / 100.0) if chosen_product else req.annual_interest_rate_pct,
        },
        "loan_terms": {
            "principal_minor": req.requested_amount_minor,
            "principal_formatted": Money.from_minor(req.requested_amount_minor, currency).format(),
            "tenure_months": req.tenure_months,
            "annual_interest_rate_pct": req.annual_interest_rate_pct,
            "monthly_emi_minor": emi_minor,
            "monthly_emi_formatted": Money.from_minor(emi_minor, currency).format(),
            "total_interest_minor": total_interest_minor,
            "total_interest_formatted": Money.from_minor(total_interest_minor, currency).format(),
            "total_payment_minor": total_payment_minor,
            "total_payment_formatted": Money.from_minor(total_payment_minor, currency).format(),
            "processing_fee_minor": fee_minor,
            "processing_fee_formatted": Money.from_minor(fee_minor, currency).format(),
        },
        "dscr_analysis": {
            "net_operating_income_minor": effective_noi_minor,
            "net_operating_income_formatted": Money.from_minor(effective_noi_minor, currency).format(),
            "existing_debt_minor": req.existing_monthly_debt_minor,
            "existing_debt_formatted": Money.from_minor(req.existing_monthly_debt_minor, currency).format(),
            "total_debt_service_minor": total_monthly_debt_service,
            "total_debt_service_formatted": Money.from_minor(total_monthly_debt_service, currency).format(),
            "projected_dscr": dscr,
            "projected_dscr_formatted": f"{dscr:.2f}x",
            "dti_pct": dti,
            "dti_formatted": f"{dti:.1f}%",
            "verdict_badge": suitability_verdict,
            "verdict_badge_class": verdict_badge_class,
            "verdict_rationale": verdict_rationale,
        },
        "stress_tests": stress_tests,
        "bank_matches": bank_matches,
        "required_documents": doc_checklist,
        "is_synthetic": True,
        "disclaimer": (
            "DEMO SIMULATION NOTICE: This underwriting packet is generated by SME Finance Copilot for credit assessment demonstration. "
            "It is not a legally binding credit commitment or loan contract from any financial institution."
        ),
        "download_url": f"/api/finance/loan-packet/{app_number}/download",
    }

    # Persist in LoanApplication table
    new_app = LoanApplication(
        business_id=shop.business_id,
        shop_id=shop.id,
        bank_id=chosen_product.bank_id if chosen_product else 1,
        product_id=chosen_product.id if chosen_product else 1,
        applicant_user_id=user.id,
        application_number=app_number,
        requested_amount_minor=req.requested_amount_minor,
        approved_amount_minor=req.requested_amount_minor if dscr >= 1.25 else 0,
        tenure_months=req.tenure_months,
        status="demo_assessed",
        evaluation_notes=json.dumps(packet_data),
        is_synthetic=True,
    )
    db.add(new_app)

    # Persist in LoanScenario table
    new_scenario = LoanScenario(
        business_id=shop.business_id,
        shop_id=shop.id,
        product_id=chosen_product.id if chosen_product else 1,
        requested_amount_minor=req.requested_amount_minor,
        tenure_months=req.tenure_months,
        calculated_emi_minor=emi_minor,
        total_interest_minor=total_interest_minor,
        total_payment_minor=total_payment_minor,
        dscr_ratio=dscr,
        recommendation_status="eligible" if dscr >= 1.25 else ("borderline" if dscr >= 1.05 else "ineligible"),
        rationale=verdict_rationale,
        is_synthetic=True,
    )
    db.add(new_scenario)

    # Immutable Audit Log
    AuditRepository(db).log_action(
        action="generate_loan_packet",
        entity_type="loan_application",
        entity_id=None,
        business_id=shop.business_id,
        shop_id=shop.id,
        user_id=user.id,
        new_values=json.dumps({
            "application_number": app_number,
            "requested_principal_minor": req.requested_amount_minor,
            "tenure_months": req.tenure_months,
            "dscr_ratio": dscr,
            "suitability_verdict": suitability_verdict,
        }),
    )

    db.commit()
    db.refresh(new_app)
    packet_data["id"] = new_app.id

    return packet_data


@router.get("/loan-packet/{application_number}/download")
def download_loan_packet_pdf(
    application_number: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Renders and streams an institutional GAAP underwriting dossier PDF.
    Enforces strict multi-tenant authorization before streaming.
    """
    app = (
        db.query(LoanApplication)
        .filter(LoanApplication.application_number == application_number)
        .first()
    )
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan underwriting packet '{application_number}' not found.",
        )

    # Enforce shop isolation
    verify_shop_access_dependency(shop_id=app.shop_id, user=user, db=db)

    # Reconstruct or parse packet data
    if app.evaluation_notes:
        try:
            packet_data = json.loads(app.evaluation_notes)
        except Exception:
            packet_data = {}
    else:
        packet_data = {}

    if not packet_data:
        shop = db.get(Shop, app.shop_id)
        business = shop.business if shop else None
        currency = business.currency if business else "BDT"
        packet_data = {
            "application_number": app.application_number,
            "generated_at_formatted": app.created_at.strftime("%d %b %Y, %H:%M UTC"),
            "business_name": business.name if business else "Demo Business",
            "shop_name": shop.name if shop else "Main Shop",
            "currency": currency,
            "tax_id": business.tax_id if business and business.tax_id else "BIN-99281-002",
            "loan_terms": {
                "principal_minor": app.requested_amount_minor,
                "principal_formatted": Money.from_minor(app.requested_amount_minor, currency).format(),
                "tenure_months": app.tenure_months,
                "annual_interest_rate_pct": 11.5,
                "monthly_emi_formatted": "৳ 37,458",
                "total_interest_formatted": "৳ 99,000",
                "total_payment_formatted": "৳ 899,000",
                "processing_fee_formatted": "৳ 8,000",
            },
            "dscr_analysis": {
                "net_operating_income_minor": 25000000,
                "net_operating_income_formatted": "৳ 250,000.00",
                "total_debt_service_formatted": "৳ 37,458.00",
                "projected_dscr": 6.67,
                "projected_dscr_formatted": "6.67x",
                "dti_formatted": "15.0%",
                "verdict_badge": "PRIME APPROVAL",
            },
            "bank_matches": [],
            "required_documents": [
                "Valid Trade License",
                "12-Month Bank Statement",
                "Smart NID",
                "TIN Certificate",
            ],
            "disclaimer": "DEMO UNDERWRITING PACKET: For evaluation purposes only.",
        }

    pdf_bytes = generate_loan_packet_pdf(packet_data)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="Loan_Packet_{application_number}.pdf"',
            "Content-Type": "application/pdf",
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )


@router.get("/loan-applications")
def list_loan_applications(
    shop_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists saved demo loan underwriting dossiers for the active shop."""
    if shop_id:
        verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)
        query = db.query(LoanApplication).filter(LoanApplication.shop_id == shop_id)
    else:
        # User's accessible shops
        membership = db.query(BusinessMembership).filter_by(user_id=user.id, is_active=True).first()
        if membership and membership.shop_id:
            query = db.query(LoanApplication).filter(LoanApplication.shop_id == membership.shop_id)
        elif membership and membership.business_id:
            query = db.query(LoanApplication).filter(LoanApplication.business_id == membership.business_id)
        else:
            query = db.query(LoanApplication)

    apps = query.order_by(desc(LoanApplication.created_at)).limit(limit).all()

    results = []
    for a in apps:
        shop = db.get(Shop, a.shop_id)
        currency = shop.business.currency if (shop and shop.business) else "BDT"
        results.append({
            "id": a.id,
            "application_number": a.application_number,
            "shop_id": a.shop_id,
            "shop_name": shop.name if shop else f"Shop #{a.shop_id}",
            "requested_amount_minor": a.requested_amount_minor,
            "requested_amount_formatted": Money.from_minor(a.requested_amount_minor, currency).format(),
            "tenure_months": a.tenure_months,
            "status": a.status,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "download_url": f"/api/finance/loan-packet/{a.application_number}/download",
            "is_synthetic": a.is_synthetic,
        })
    return results
