"""
Deterministic Financial Calculations and Ledger API Routes.
Provides financial summaries, ledger retrieval (sales/expenses), cash-flow forecasting,
explainable loan risk assessments, and inventory/receivable analytics with shop isolation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, and_

from src.database.connection import get_db
from src.database.models import (
    User,
    Shop,
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
    Forecast,
    AuditLog,
    Document,
    utc_now,
)
from src.api.dependencies import get_current_user, verify_shop_access_dependency
from src.finance.calculator import FinancialCalculator
from src.ai.forecaster import CashFlowForecaster
from src.ai.loan_risk import TransparentLoanRiskEngine
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


# ==============================================================================
# 1. Financial Health Summary Dashboard
# ==============================================================================

@router.get("/summary")
def get_financial_summary(
    shop_id: int = Query(..., description="Shop ID for multi-tenant query"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns an aggregated financial health dashboard for a shop:
    Revenue, COGS, Operating Expenses, Gross & Net Profit, Cash Balance,
    Inventory Valuation, Outstanding Receivables, and Document Review Queue.
    """
    verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)
    shop = db.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found.")

    # 1. Sales & Revenue
    sales_total = (
        db.query(func.coalesce(func.sum(Sale.total_amount_minor), 0))
        .filter(Sale.shop_id == shop_id)
        .scalar()
    ) or 0
    sales_count = db.query(Sale).filter(Sale.shop_id == shop_id).count()

    # 2. Purchases & COGS
    cogs_total = (
        db.query(func.coalesce(func.sum(Purchase.total_amount_minor), 0))
        .filter(Purchase.shop_id == shop_id)
        .scalar()
    ) or 0

    # 3. Operating Expenses
    expenses_total = (
        db.query(func.coalesce(func.sum(Expense.amount_minor), 0))
        .filter(Expense.shop_id == shop_id)
        .scalar()
    ) or 0
    expenses_count = db.query(Expense).filter(Expense.shop_id == shop_id).count()

    # 4. Deterministic Profit & Loss
    gross_profit_minor = sales_total - cogs_total
    net_profit_minor = gross_profit_minor - expenses_total
    gross_margin_pct = round((gross_profit_minor / sales_total) * 100, 2) if sales_total > 0 else 0.0
    net_margin_pct = round((net_profit_minor / sales_total) * 100, 2) if sales_total > 0 else 0.0

    # 5. Cash Flow & Net Balance
    payment_inflows = (
        db.query(func.coalesce(func.sum(Payment.amount_minor), 0))
        .filter(Payment.shop_id == shop_id, Payment.payment_type.in_(["customer_inflow", "loan_disbursement"]))
        .scalar()
    ) or 0
    payment_outflows = (
        db.query(func.coalesce(func.sum(Payment.amount_minor), 0))
        .filter(Payment.shop_id == shop_id, Payment.payment_type.in_(["supplier_outflow", "expense_outflow", "loan_repayment"]))
        .scalar()
    ) or 0

    if payment_inflows == 0 and payment_outflows == 0:
        # Fallback to CashMovement if Payment table is empty
        cm_inflows = (
            db.query(func.coalesce(func.sum(CashMovement.amount_minor), 0))
            .filter(CashMovement.shop_id == shop_id, CashMovement.movement_type == "inflow")
            .scalar()
        ) or 0
        cm_outflows = (
            db.query(func.coalesce(func.sum(CashMovement.amount_minor), 0))
            .filter(CashMovement.shop_id == shop_id, CashMovement.movement_type == "outflow")
            .scalar()
        ) or 0
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
    }


# ==============================================================================
# 2. Sales Ledger with Filtering and Pagination
# ==============================================================================

@router.get("/sales")
def list_sales(
    shop_id: int = Query(...),
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
    verify_shop_access_dependency(shop_id=shop_id, user=user, db=db)

    query = db.query(Sale).filter(Sale.shop_id == shop_id)

    if start_date:
        s_dt = _parse_date_safe(start_date)
        if s_dt:
            query = query.filter(Sale.sale_date >= s_dt)

    if end_date:
        e_dt = _parse_date_safe(end_date)
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

    query = db.query(Expense).filter(Expense.shop_id == shop_id)

    if start_date:
        s_dt = _parse_date_safe(start_date)
        if s_dt:
            query = query.filter(Expense.expense_date >= s_dt)

    if end_date:
        e_dt = _parse_date_safe(end_date)
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
