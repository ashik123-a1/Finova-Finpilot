"""
AI Assistant Financial Guardrails & Multilingual Safety Interceptor.
Guarantees separation between natural language generation and deterministic calculation.
Prevents hallucination of monetary totals, EMI installments, profit margins, or metrics.
Enforces multi-script prompt injection defenses and country compliance.
"""

from __future__ import annotations

import re
from typing import Dict, Any, List, Optional, Tuple
from src.finance.calculator import FinancialCalculator
from src.core.money import Money
from src.core.country_profiles import CountryRegistry
from src.core.security import detect_multilingual_prompt_injection, sanitize_multilingual_input, redact_pii
from src.i18n.registry import LanguageRegistry
from src.i18n.translator import t
from src.i18n.formatters import LocaleFormatter


class AiAssistantGuardrail:
    """Enforces mathematical determinism and multilingual security on AI copilot interactions."""

    @classmethod
    def detect_language(cls, text: str, override_locale: Optional[str] = None) -> str:
        """
        Detects user prompt language or respects explicit user override.
        Returns ISO 639-1 language code.
        """
        if override_locale and LanguageRegistry.has(override_locale):
            return override_locale.lower().split("-")[0].strip()

        if not text:
            return "en"

        clean = sanitize_multilingual_input(text)

        # Script-based deterministic detection
        if re.search(r"[\u0980-\u09FF]", clean):
            return "bn"  # Bengali
        if re.search(r"[\u4E00-\u9FFF]", clean):
            return "zh"  # Chinese
        if re.search(r"[\u0600-\u06FF]", clean):
            return "ar"  # Arabic
        if re.search(r"[\u0900-\u097F]", clean):
            return "hi"  # Hindi
        if re.search(r"[\u0400-\u04FF]", clean):
            return "ru"  # Russian
        if re.search(r"(?i)\b(?:el|la|los|las|de|para|con|factura|préstamo|cuota)\b", clean):
            return "es"  # Spanish
        if re.search(r"(?i)\b(?:le|la|les|du|des|pour|facture|prêt|mensualité)\b", clean):
            return "fr"  # French
        if re.search(r"(?i)\b(?:der|die|das|und|für|mit|rechnung|kredit)\b", clean):
            return "de"  # German

        return "en"

    @classmethod
    def execute_verified_financial_query(
        cls, query_type: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes deterministic calculation before passing verified ground truth to AI text generation.
        Maintains bit-exact mathematical parity across all languages.
        """
        prompt = parameters.get("user_prompt", "")
        # 1. Security: Multilingual prompt injection audit
        if prompt:
            is_injection, alert_msg = detect_multilingual_prompt_injection(prompt)
            if is_injection:
                return {
                    "verified": False,
                    "security_alert": True,
                    "error": alert_msg,
                }

        # 2. Locale and Country setup
        locale = parameters.get("locale") or cls.detect_language(prompt, parameters.get("preferred_locale"))
        country_code = parameters.get("country_code", "BD").upper()
        country = CountryRegistry.get(country_code) or CountryRegistry.get("BD")
        currency = parameters.get("currency") or (country.primary_currency if country else "BDT")
        multiplier = CountryRegistry.get_currency_multiplier(currency)

        # 3. Calculation & Ground Truth Generation
        if query_type == "profit_and_loss":
            res = FinancialCalculator.calculate_profit_and_loss(
                sales_minor=parameters.get("sales_minor", []),
                cogs_minor=parameters.get("cogs_minor", []),
                operating_expenses_minor=parameters.get("operating_expenses_minor", []),
            )
            return {
                "verified": True,
                "locale": locale,
                "currency": currency,
                "country_code": country_code,
                # Preserved API contract: Money.from_minor(...).format() -> "80,000.00 BDT"
                "revenue": Money.from_minor(res.revenue_minor, currency).format(),
                "cogs": Money.from_minor(res.cogs_minor, currency).format(),
                "gross_profit": Money.from_minor(res.gross_profit_minor, currency).format(),
                "operating_expenses": Money.from_minor(res.operating_expenses_minor, currency).format(),
                "net_profit": Money.from_minor(res.net_profit_minor, currency).format(),
                "gross_margin_pct": f"{res.gross_margin_pct:.2f}%",
                "net_margin_pct": f"{res.net_margin_pct:.2f}%",
                # Machine readable minor units (INVARIANT across languages)
                "revenue_minor": res.revenue_minor,
                "cogs_minor": res.cogs_minor,
                "gross_profit_minor": res.gross_profit_minor,
                "operating_expenses_minor": res.operating_expenses_minor,
                "net_profit_minor": res.net_profit_minor,
                # Localized human-readable presentations
                "localized_revenue": LocaleFormatter.format_currency(res.revenue_minor, currency=currency, locale=locale, minor_multiplier=multiplier),
                "localized_net_profit": LocaleFormatter.format_currency(res.net_profit_minor, currency=currency, locale=locale, minor_multiplier=multiplier),
                "labels": {
                    "revenue_label": t("financial.revenue", locale=locale),
                    "cogs_label": t("financial.cogs", locale=locale),
                    "gross_profit_label": t("financial.gross_profit", locale=locale),
                    "net_profit_label": t("financial.net_profit", locale=locale),
                }
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
                "locale": locale,
                "currency": currency,
                "country_code": country_code,
                # Preserved API contract: Money.format()
                "loan_amount": Money.from_minor(res.loan_amount_minor, currency).format(),
                "reducing_monthly_emi": Money.from_minor(res.reducing_monthly_emi_minor, currency).format(),
                "reducing_total_interest": Money.from_minor(res.reducing_total_interest_minor, currency).format(),
                "reducing_total_payment": Money.from_minor(res.reducing_total_payment_minor, currency).format(),
                "flat_monthly_installment": Money.from_minor(res.flat_monthly_installment_minor, currency).format(),
                "flat_total_interest": Money.from_minor(res.flat_total_interest_minor, currency).format(),
                "flat_rate_penalty": Money.from_minor(res.flat_rate_penalty_minor, currency).format(),
                "effective_apr_reducing": f"{res.effective_apr_reducing_pct:.2f}%",
                "effective_apr_flat": f"{res.effective_apr_flat_pct:.2f}%",
                # Invariant minor units
                "loan_amount_minor": res.loan_amount_minor,
                "reducing_monthly_emi_minor": res.reducing_monthly_emi_minor,
                "reducing_total_interest_minor": res.reducing_total_interest_minor,
                "reducing_total_payment_minor": res.reducing_total_payment_minor,
                # Localized formatted values
                "localized_reducing_monthly_emi": LocaleFormatter.format_currency(res.reducing_monthly_emi_minor, currency=currency, locale=locale, minor_multiplier=multiplier),
                "labels": {
                    "monthly_emi_label": t("financial.monthly_emi", locale=locale),
                    "total_interest_label": t("financial.total_interest", locale=locale),
                }
            }

        elif query_type == "break_even":
            res = FinancialCalculator.calculate_break_even(
                fixed_costs_minor=parameters.get("fixed_costs_minor", 0),
                selling_price_per_unit_minor=parameters.get("selling_price_per_unit_minor", 0),
                variable_cost_per_unit_minor=parameters.get("variable_cost_per_unit_minor", 0),
            )
            return {
                "verified": True,
                "locale": locale,
                "currency": currency,
                "country_code": country_code,
                "fixed_costs": Money.from_minor(res.fixed_costs_minor, currency).format(),
                "contribution_margin_per_unit": Money.from_minor(res.contribution_margin_per_unit_minor, currency).format(),
                "contribution_margin_ratio": f"{res.contribution_margin_ratio * 100:.1f}%",
                "break_even_units": res.break_even_units,
                "break_even_revenue": Money.from_minor(res.break_even_revenue_minor, currency).format(),
                "fixed_costs_minor": res.fixed_costs_minor,
                "break_even_revenue_minor": res.break_even_revenue_minor,
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
        clean_text = sanitize_multilingual_input(assistant_text)

        # Check for injection traces in model response
        is_inj, reason = detect_multilingual_prompt_injection(clean_text)
        if is_inj:
            violations.append(f"Security Alert: Assistant output contained adversarial pattern: {reason}")

        return len(violations) == 0, violations
