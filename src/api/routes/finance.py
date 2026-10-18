"""
Deterministic Financial Calculations and Ledger API Routes.
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from src.database.connection import get_db
from src.database.models import User, Sale, Purchase, Expense, Payment, Receivable
from src.api.dependencies import get_current_user, verify_shop_access_dependency
from src.finance.calculator import FinancialCalculator
from src.core.money import Money

router = APIRouter(prefix="/finance", tags=["Finance"])


class LoanComparisonRequest(BaseModel):
    principal_minor: int
    annual_interest_rate_pct: float
    tenure_months: int
    processing_fee_bps: int = 100


class BreakEvenRequest(BaseModel):
    fixed_costs_minor: int
    selling_price_per_unit_minor: int
    variable_cost_per_unit_minor: int


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
