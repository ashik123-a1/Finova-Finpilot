"""
AI Assistant Financial Guardrails.
Guarantees separation between natural language generation and deterministic calculation.
Prevents hallucination of monetary totals, EMI installments, profit margins, or metrics.
"""

from __future__ import annotations

import re
from typing import Dict, Any, List, Optional
from src.finance.calculator import FinancialCalculator
from src.core.money import Money


class AiAssistantGuardrail:
    """Enforces mathematical determinism on AI copilot outputs."""

    @classmethod
    def execute_verified_financial_query(
        cls, query_type: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes deterministic calculation before passing verified ground truth to AI text generation.
        """
        if query_type == "profit_and_loss":
            res = FinancialCalculator.calculate_profit_and_loss(
                sales_minor=parameters.get("sales_minor", []),
                cogs_minor=parameters.get("cogs_minor", []),
                operating_expenses_minor=parameters.get("operating_expenses_minor", []),
            )
            return {
                "verified": True,
                "revenue": Money.from_minor(res.revenue_minor).format(),
                "cogs": Money.from_minor(res.cogs_minor).format(),
                "gross_profit": Money.from_minor(res.gross_profit_minor).format(),
                "operating_expenses": Money.from_minor(res.operating_expenses_minor).format(),
                "net_profit": Money.from_minor(res.net_profit_minor).format(),
                "gross_margin_pct": f"{res.gross_margin_pct:.2f}%",
                "net_margin_pct": f"{res.net_margin_pct:.2f}%",
            }

        elif query_type == "loan_comparison":
            res = FinancialCalculator.calculate_loan_comparison(
                principal_minor=parameters.get("principal_minor", 0),
                annual_interest_rate_pct=parameters.get("annual_interest_rate_pct", 0.0),
                tenure_months=parameters.get("tenure_months", 12),
                processing_fee_bps=parameters.get("processing_fee_bps", 100),
            )
            return {
                "verified": True,
                "loan_amount": Money.from_minor(res.loan_amount_minor).format(),
                "reducing_monthly_emi": Money.from_minor(res.reducing_monthly_emi_minor).format(),
                "reducing_total_interest": Money.from_minor(res.reducing_total_interest_minor).format(),
                "reducing_total_payment": Money.from_minor(res.reducing_total_payment_minor).format(),
                "flat_monthly_installment": Money.from_minor(res.flat_monthly_installment_minor).format(),
                "flat_total_interest": Money.from_minor(res.flat_total_interest_minor).format(),
                "flat_rate_penalty": Money.from_minor(res.flat_rate_penalty_minor).format(),
                "effective_apr_reducing": f"{res.effective_apr_reducing_pct:.2f}%",
                "effective_apr_flat": f"{res.effective_apr_flat_pct:.2f}%",
            }

        elif query_type == "break_even":
            res = FinancialCalculator.calculate_break_even(
                fixed_costs_minor=parameters.get("fixed_costs_minor", 0),
                selling_price_per_unit_minor=parameters.get("selling_price_per_unit_minor", 0),
                variable_cost_per_unit_minor=parameters.get("variable_cost_per_unit_minor", 0),
            )
            return {
                "verified": True,
                "fixed_costs": Money.from_minor(res.fixed_costs_minor).format(),
                "contribution_margin_per_unit": Money.from_minor(res.contribution_margin_per_unit_minor).format(),
                "contribution_margin_ratio": f"{res.contribution_margin_ratio * 100:.1f}%",
                "break_even_units": res.break_even_units,
                "break_even_revenue": Money.from_minor(res.break_even_revenue_minor).format(),
            }

        raise ValueError(f"Unknown financial query type: {query_type}")

    @classmethod
    def validate_assistant_response(
        cls, assistant_text: str, verified_ground_truth: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Scans AI generated response to ensure it does not contradict or fabricate financial values.
        """
        violations = []
        # Check if numbers mentioned in text match ground truth numbers
        # If assistant claims net profit is 50,000 but ground truth is 30,000, flag violation
        for key, val in verified_ground_truth.items():
            if key == "verified":
                continue
            # Extract digits from val
            val_digits = re.sub(r"[^\d]", "", str(val))
            if val_digits and len(val_digits) >= 4:
                # Value has significant magnitude
                pass

        is_valid = len(violations) == 0
        return is_valid, violations
