"""
API Endpoints for 100-Language Registry, Localization, and Multi-Country Profiles.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.i18n.registry import LanguageRegistry
from src.i18n.translator import I18nService, t
from src.i18n.formatters import LocaleFormatter
from src.core.country_profiles import CountryRegistry
from src.core.security import detect_multilingual_prompt_injection, sanitize_multilingual_input, redact_pii

router = APIRouter(prefix="/i18n", tags=["Internationalization & Localization"])


class CurrencyFormatRequest(BaseModel):
    amount_minor: int
    currency: str = "BDT"
    locale: str = "en"
    use_native_digits: bool = False


class PromptAuditRequest(BaseModel):
    prompt: str


@router.get("/languages")
def list_supported_languages(
    status: Optional[str] = None,
    direction: Optional[str] = None
) -> Dict[str, Any]:
    """
    Returns the versioned 100-language master registry with capability tiers.
    """
    languages = LanguageRegistry.get_all()
    if status:
        languages = [l for l in languages if l.ui_status.value == status or l.ai_status.value == status]
    if direction:
        languages = [l for l in languages if l.direction.value == direction]

    return {
        "version": LanguageRegistry.VERSION,
        "total_registered": LanguageRegistry.count(),
        "returned_count": len(languages),
        "languages": [l.to_dict() for l in languages]
    }


@router.get("/languages/{code}")
def get_language_details(code: str) -> Dict[str, Any]:
    """
    Retrieves full capability status and limitations for a specific language code.
    """
    entry = LanguageRegistry.get(code)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Language code '{code}' not found in 100-language registry.")
    return entry.to_dict()


@router.get("/countries")
def list_country_profiles() -> Dict[str, Any]:
    """
    Returns all verified multi-country profiles with statutory tax rates and banking covenants.
    """
    profiles = CountryRegistry.get_all()
    return {
        "version": CountryRegistry.VERSION,
        "total_countries": len(profiles),
        "countries": [p.to_dict() for p in profiles]
    }


@router.get("/countries/{country_code}")
def get_country_profile(country_code: str) -> Dict[str, Any]:
    """
    Retrieves statutory accounting, tax, and loan covenants with official legal sources for a country.
    """
    profile = CountryRegistry.get(country_code)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Country profile '{country_code}' not found.")
    return profile.to_dict()


@router.get("/translations/{locale}")
def get_locale_translations(locale: str) -> Dict[str, Any]:
    """
    Retrieves UI translation strings for the requested locale with fallback audit.
    """
    clean_locale = locale.lower().split("-")[0].strip()
    catalog_audit = I18nService.validate_catalog()
    return {
        "locale": clean_locale,
        "direction": LocaleFormatter.get_text_direction(clean_locale),
        "translations": I18nService._CATALOGS.get(clean_locale, I18nService._CATALOGS.get("en", {})),
        "is_fallback": clean_locale not in I18nService._CATALOGS,
        "catalog_health": catalog_audit.get("results", {}).get(clean_locale, {
            "status": "using_fallback_catalog",
            "completeness_pct": 0.0
        })
    }


@router.post("/format-currency")
def format_currency_endpoint(req: CurrencyFormatRequest) -> Dict[str, Any]:
    """
    Formats monetary minor units into localized string according to jurisdiction rules.
    """
    mult = CountryRegistry.get_currency_multiplier(req.currency)
    formatted = LocaleFormatter.format_currency(
        amount_minor=req.amount_minor,
        currency=req.currency,
        locale=req.locale,
        minor_multiplier=mult,
        use_native_digits=req.use_native_digits
    )
    return {
        "amount_minor": req.amount_minor,
        "currency": req.currency,
        "locale": req.locale,
        "minor_multiplier": mult,
        "formatted_result": formatted,
    }


@router.post("/audit-prompt")
def audit_prompt_endpoint(req: PromptAuditRequest) -> Dict[str, Any]:
    """
    Audits multilingual prompt for adversarial injection attacks and PII leakage.
    """
    sanitized = sanitize_multilingual_input(req.prompt)
    is_inj, alert_msg = detect_multilingual_prompt_injection(sanitized)
    redacted = redact_pii(sanitized)

    return {
        "is_safe": not is_inj,
        "injection_detected": is_inj,
        "alert_message": alert_msg,
        "sanitized_prompt": sanitized,
        "redacted_prompt": redacted,
    }
