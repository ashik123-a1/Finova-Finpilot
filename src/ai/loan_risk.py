"""
Transparent Loan Matching and Risk Evaluation Policy Engine.
Compares loan products from demo banks, calculates installments, audits DSCR,
and provides transparent eligibility recommendations without opaque 'black-box' scoring.
Explicitly marked as synthetic demo data.
"""

from __future__ import annotations

from typing import Dict, Any, List
from src.finance.calculator import FinancialCalculator


class TransparentLoanRiskEngine:
    """Evaluates SME creditworthiness using explainable financial policy rules."""

    MIN_DSCR_HEALTHY = 1.25
    MIN_DSCR_BORDERLINE = 1.05
    MAX_EMI_TO_NET_INCOME_RATIO = 0.40  # Proposed debt service should not exceed 40% of net income

    @classmethod
    def evaluate_loan_scenario(
        cls,
        monthly_revenue_minor: int,
        monthly_expenses_minor: int,
        existing_monthly_debt_minor: int,
        requested_amount_minor: int,
        tenure_months: int,
        annual_interest_rate_pct: float,
        processing_fee_bps: int = 100,
    ) -> Dict[str, Any]:
        """
        Evaluates loan eligibility with transparent ratios and full EMI breakdown.
        """
        # Calculate monthly net operating income
        net_operating_income_minor = monthly_revenue_minor - monthly_expenses_minor

        # Calculate loan terms
        comparison = FinancialCalculator.calculate_loan_comparison(
            principal_minor=requested_amount_minor,
            annual_interest_rate_pct=annual_interest_rate_pct,
            tenure_months=tenure_months,
            processing_fee_bps=processing_fee_bps,
        )

        proposed_monthly_emi = comparison.reducing_monthly_emi_minor
        total_monthly_debt_service = existing_monthly_debt_minor + proposed_monthly_emi

        # Compute DSCR
        dscr = FinancialCalculator.calculate_dscr(
            monthly_net_operating_income_minor=net_operating_income_minor,
            monthly_debt_service_minor=total_monthly_debt_service,
        )

        # Debt-to-income ratio
        emi_to_income_ratio = (
            round(proposed_monthly_emi / net_operating_income_minor, 4)
            if net_operating_income_minor > 0
            else float("inf")
        )

        # Determine Recommendation
        reasons = []
        if net_operating_income_minor <= 0:
            status = "ineligible"
            reasons.append("Net operating income is negative or zero.")
        elif dscr >= cls.MIN_DSCR_HEALTHY and emi_to_income_ratio <= cls.MAX_EMI_TO_NET_INCOME_RATIO:
            status = "eligible"
            reasons.append(
                f"DSCR of {dscr:.2f} meets healthy threshold (>= {cls.MIN_DSCR_HEALTHY})."
            )
            reasons.append(
                f"Proposed EMI represents {emi_to_income_ratio * 100:.1f}% of net operating income (<= {cls.MAX_EMI_TO_NET_INCOME_RATIO * 100:.0f}%)."
            )
        elif dscr >= cls.MIN_DSCR_BORDERLINE:
            status = "borderline"
            reasons.append(
                f"DSCR of {dscr:.2f} is in borderline range ({cls.MIN_DSCR_BORDERLINE} - {cls.MIN_DSCR_HEALTHY}). Collateral or longer tenure advised."
            )
        else:
            status = "ineligible"
            reasons.append(
                f"DSCR of {dscr:.2f} is insufficient to service total debt obligations."
            )

        # Maximum borrowing capacity (safe principal at 1.25 DSCR)
        max_safe_emi = int(round(net_operating_income_minor / cls.MIN_DSCR_HEALTHY)) - existing_monthly_debt_minor
        max_safe_borrowing_minor = max(0, int(round(max_safe_emi * tenure_months * 0.85)))

        return {
            "requested_amount_minor": requested_amount_minor,
            "tenure_months": tenure_months,
            "monthly_emi_minor": proposed_monthly_emi,
            "total_interest_minor": comparison.reducing_total_interest_minor,
            "total_payment_minor": comparison.reducing_total_payment_minor,
            "processing_fee_minor": comparison.processing_fee_minor,
            "net_operating_income_minor": net_operating_income_minor,
            "dscr_ratio": dscr if dscr != float("inf") else 999.0,
            "emi_to_income_ratio": emi_to_income_ratio if emi_to_income_ratio != float("inf") else 999.0,
            "recommendation_status": status,
            "recommendation_reasons": reasons,
            "max_safe_borrowing_minor": max_safe_borrowing_minor,
            "is_synthetic_demo": True,
            "regulatory_disclaimer": "Simulated evaluation only. Not an actual loan offer or commitment.",
        }
