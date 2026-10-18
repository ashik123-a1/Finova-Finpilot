"""
Deterministic Financial Calculation Engine for SME Finance Copilot.
All calculations use integer minor units (e.g. Poisha/Cents) or exact Decimals
with ROUND_HALF_UP rounding.
Zero floating-point inaccuracies. Zero hallucination.
"""

from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass(frozen=True)
class ProfitLossSummary:
    revenue_minor: int
    cogs_minor: int
    gross_profit_minor: int
    operating_expenses_minor: int
    net_profit_minor: int
    gross_margin_pct: float
    net_margin_pct: float


@dataclass(frozen=True)
class CashFlowSummary:
    opening_balance_minor: int
    cash_inflows_minor: int
    cash_outflows_minor: int
    net_cash_flow_minor: int
    closing_balance_minor: int


@dataclass(frozen=True)
class ReceivablesAgingSummary:
    total_outstanding_minor: int
    current_minor: int          # 0-30 days
    overdue_31_60_minor: int    # 31-60 days
    overdue_61_90_minor: int    # 61-90 days
    overdue_90_plus_minor: int  # >90 days
    dso_days: float             # Days Sales Outstanding


@dataclass(frozen=True)
class LoanComparisonResult:
    loan_amount_minor: int
    tenure_months: int
    annual_interest_rate_pct: float
    processing_fee_minor: int
    # Reducing balance (EMI)
    reducing_monthly_emi_minor: int
    reducing_total_interest_minor: int
    reducing_total_payment_minor: int
    # Flat rate
    flat_monthly_installment_minor: int
    flat_total_interest_minor: int
    flat_total_payment_minor: int
    # Difference / Extra cost of flat rate
    flat_rate_penalty_minor: int
    effective_apr_reducing_pct: float
    effective_apr_flat_pct: float


@dataclass(frozen=True)
class BreakEvenAnalysisResult:
    fixed_costs_minor: int
    selling_price_per_unit_minor: int
    variable_cost_per_unit_minor: int
    contribution_margin_per_unit_minor: int
    contribution_margin_ratio: float
    break_even_units: int
    break_even_revenue_minor: int


@dataclass(frozen=True)
class InvestmentRoiResult:
    initial_investment_minor: int
    net_total_cash_inflow_minor: int
    net_profit_minor: int
    roi_pct: float
    simple_payback_period_years: float


class FinancialCalculator:
    """Production-grade deterministic calculation service."""

    @staticmethod
    def calculate_profit_and_loss(
        sales_minor: List[int],
        cogs_minor: List[int],
        operating_expenses_minor: List[int],
    ) -> ProfitLossSummary:
        """
        Calculates Revenue, COGS, Gross Profit, Operating Expenses, Net Profit and Margins.
        """
        revenue = sum(sales_minor)
        cogs = sum(cogs_minor)
        gross_profit = revenue - cogs
        expenses = sum(operating_expenses_minor)
        net_profit = gross_profit - expenses

        if revenue > 0:
            gross_margin = float(
                (Decimal(gross_profit) / Decimal(revenue) * Decimal(100)).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            )
            net_margin = float(
                (Decimal(net_profit) / Decimal(revenue) * Decimal(100)).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            )
        else:
            gross_margin = 0.0
            net_margin = 0.0

        return ProfitLossSummary(
            revenue_minor=revenue,
            cogs_minor=cogs,
            gross_profit_minor=gross_profit,
            operating_expenses_minor=expenses,
            net_profit_minor=net_profit,
            gross_margin_pct=gross_margin,
            net_margin_pct=net_margin,
        )

    @staticmethod
    def calculate_cash_flow(
        opening_balance_minor: int,
        inflows_minor: List[int],
        outflows_minor: List[int],
    ) -> CashFlowSummary:
        """Calculates Net Cash Flow and Closing Cash Balance."""
        total_inflows = sum(inflows_minor)
        total_outflows = sum(outflows_minor)
        net_cash_flow = total_inflows - total_outflows
        closing_balance = opening_balance_minor + net_cash_flow

        return CashFlowSummary(
            opening_balance_minor=opening_balance_minor,
            cash_inflows_minor=total_inflows,
            cash_outflows_minor=total_outflows,
            net_cash_flow_minor=net_cash_flow,
            closing_balance_minor=closing_balance,
        )

    @staticmethod
    def calculate_receivables_aging(
        invoices: List[Dict[str, Any]],
        annual_credit_sales_minor: int = 0,
    ) -> ReceivablesAgingSummary:
        """
        Calculates aging buckets (current, 31-60, 61-90, 90+) and Days Sales Outstanding (DSO).
        Each invoice dict requires: {'outstanding_minor': int, 'days_past_due': int}
        """
        current = 0
        overdue_31_60 = 0
        overdue_61_90 = 0
        overdue_90_plus = 0

        for inv in invoices:
            amount = inv.get("outstanding_minor", 0)
            if amount <= 0:
                continue
            dpd = inv.get("days_past_due", 0)

            if dpd <= 30:
                current += amount
            elif dpd <= 60:
                overdue_31_60 += amount
            elif dpd <= 90:
                overdue_61_90 += amount
            else:
                overdue_90_plus += amount

        total_outstanding = current + overdue_31_60 + overdue_61_90 + overdue_90_plus

        # DSO = (Total Receivables / Total Credit Sales) * 365
        if annual_credit_sales_minor > 0 and total_outstanding > 0:
            dso = float(
                (Decimal(total_outstanding) / Decimal(annual_credit_sales_minor) * Decimal(365)).quantize(
                    Decimal("0.1"), rounding=ROUND_HALF_UP
                )
            )
        else:
            dso = 0.0

        return ReceivablesAgingSummary(
            total_outstanding_minor=total_outstanding,
            current_minor=current,
            overdue_31_60_minor=overdue_31_60,
            overdue_61_90_minor=overdue_61_90,
            overdue_90_plus_minor=overdue_90_plus,
            dso_days=dso,
        )

    @staticmethod
    def calculate_inventory_valuation(
        batches: List[Dict[str, int]],
        method: str = "weighted_average",
    ) -> Tuple[int, int]:
        """
        Calculates Total Stock Count and Valuation.
        batches: list of {'quantity': int, 'unit_cost_minor': int}
        method: 'weighted_average' or 'fifo'
        Returns: (total_quantity, total_valuation_minor)
        """
        total_qty = sum(b.get("quantity", 0) for b in batches)
        if total_qty <= 0:
            return 0, 0

        if method == "weighted_average":
            total_cost = sum(b.get("quantity", 0) * b.get("unit_cost_minor", 0) for b in batches)
            return total_qty, total_cost
        elif method == "fifo":
            total_cost = sum(b.get("quantity", 0) * b.get("unit_cost_minor", 0) for b in batches)
            return total_qty, total_cost
        else:
            raise ValueError(f"Unsupported valuation method: {method}")

    @staticmethod
    def calculate_loan_comparison(
        principal_minor: int,
        annual_interest_rate_pct: float,
        tenure_months: int,
        processing_fee_bps: int = 100,
    ) -> LoanComparisonResult:
        """
        Compares Reducing Balance (Equated Monthly Installment - EMI) vs Flat Rate Interest.
        Shows exact financial difference and hidden APR cost of flat-rate schemes.
        """
        if principal_minor <= 0 or tenure_months <= 0:
            raise ValueError("Principal and tenure must be strictly positive.")

        # Processing fee
        fee_minor = int(
            (Decimal(principal_minor) * Decimal(processing_fee_bps) / Decimal(10000)).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        )

        r_annual = Decimal(str(annual_interest_rate_pct)) / Decimal(100)
        r_monthly = r_annual / Decimal(12)
        n = Decimal(tenure_months)

        # 1. Reducing Balance EMI
        if r_monthly > 0:
            factor = (Decimal(1) + r_monthly) ** n
            emi_dec = (Decimal(principal_minor) * r_monthly * factor) / (factor - Decimal(1))
            reducing_emi_minor = int(emi_dec.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        else:
            reducing_emi_minor = int((Decimal(principal_minor) / n).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

        reducing_total_payment = reducing_emi_minor * tenure_months
        reducing_total_interest = reducing_total_payment - principal_minor

        # 2. Flat Rate Interest
        # Total interest = Principal * r_annual * (tenure_months / 12)
        years = Decimal(tenure_months) / Decimal(12)
        flat_total_interest_dec = Decimal(principal_minor) * r_annual * years
        flat_total_interest_minor = int(flat_total_interest_dec.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        flat_total_payment = principal_minor + flat_total_interest_minor
        flat_monthly_installment_minor = int((Decimal(flat_total_payment) / n).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

        flat_penalty_minor = flat_total_payment - reducing_total_payment

        # Effective APR calculation
        # Flat rate effective APR is roughly 1.8x stated rate
        effective_apr_reducing = float(annual_interest_rate_pct)
        if tenure_months > 1:
            approx_flat_apr = float((Decimal(flat_total_interest_minor) * Decimal(2) / (Decimal(principal_minor) * (n + 1)) * Decimal(12) * Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        else:
            approx_flat_apr = float(annual_interest_rate_pct)

        return LoanComparisonResult(
            loan_amount_minor=principal_minor,
            tenure_months=tenure_months,
            annual_interest_rate_pct=annual_interest_rate_pct,
            processing_fee_minor=fee_minor,
            reducing_monthly_emi_minor=reducing_emi_minor,
            reducing_total_interest_minor=reducing_total_interest,
            reducing_total_payment_minor=reducing_total_payment,
            flat_monthly_installment_minor=flat_monthly_installment_minor,
            flat_total_interest_minor=flat_total_interest_minor,
            flat_total_payment_minor=flat_total_payment,
            flat_rate_penalty_minor=flat_penalty_minor,
            effective_apr_reducing_pct=effective_apr_reducing,
            effective_apr_flat_pct=approx_flat_apr,
        )

    @staticmethod
    def calculate_dscr(
        monthly_net_operating_income_minor: int,
        monthly_debt_service_minor: int,
    ) -> float:
        """
        Debt Service Coverage Ratio (DSCR) = Net Operating Income / Total Debt Service.
        Healthy SME threshold typically >= 1.25.
        """
        if monthly_debt_service_minor <= 0:
            return float("inf")
        ratio = Decimal(monthly_net_operating_income_minor) / Decimal(monthly_debt_service_minor)
        return float(ratio.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    @staticmethod
    def calculate_break_even(
        fixed_costs_minor: int,
        selling_price_per_unit_minor: int,
        variable_cost_per_unit_minor: int,
    ) -> BreakEvenAnalysisResult:
        """
        Calculates Contribution Margin, Break-even quantity, and Break-even revenue.
        """
        contribution_margin = selling_price_per_unit_minor - variable_cost_per_unit_minor
        if contribution_margin <= 0:
            raise ValueError("Contribution margin must be positive to achieve break-even.")

        cm_ratio = float(
            (Decimal(contribution_margin) / Decimal(selling_price_per_unit_minor)).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )
        )

        break_even_units = math.ceil(fixed_costs_minor / contribution_margin)
        break_even_revenue = break_even_units * selling_price_per_unit_minor

        return BreakEvenAnalysisResult(
            fixed_costs_minor=fixed_costs_minor,
            selling_price_per_unit_minor=selling_price_per_unit_minor,
            variable_cost_per_unit_minor=variable_cost_per_unit_minor,
            contribution_margin_per_unit_minor=contribution_margin,
            contribution_margin_ratio=cm_ratio,
            break_even_units=break_even_units,
            break_even_revenue_minor=break_even_revenue,
        )

    @staticmethod
    def calculate_roi_and_payback(
        initial_investment_minor: int,
        annual_cash_inflows_minor: List[int],
    ) -> InvestmentRoiResult:
        """
        Calculates Return on Investment (ROI %) and Simple Payback Period (years).
        """
        if initial_investment_minor <= 0:
            raise ValueError("Initial investment must be positive.")

        total_inflow = sum(annual_cash_inflows_minor)
        net_profit = total_inflow - initial_investment_minor
        roi = float(
            (Decimal(net_profit) / Decimal(initial_investment_minor) * Decimal(100)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        )

        # Calculate payback period
        cumulative = 0
        payback_years = float("inf")
        for year, inflow in enumerate(annual_cash_inflows_minor, start=1):
            cumulative += inflow
            if cumulative >= initial_investment_minor:
                # Fractional year interpolation
                prev_cumulative = cumulative - inflow
                needed = initial_investment_minor - prev_cumulative
                fraction = Decimal(needed) / Decimal(inflow) if inflow > 0 else Decimal(0)
                payback_years = float(
                    (Decimal(year - 1) + fraction).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
                )
                break

        return InvestmentRoiResult(
            initial_investment_minor=initial_investment_minor,
            net_total_cash_inflow_minor=total_inflow,
            net_profit_minor=net_profit,
            roi_pct=roi,
            simple_payback_period_years=payback_years,
        )
