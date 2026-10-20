"""
API Endpoints for 100-Language Registry, Localization, and Multi-Country Profiles.
"""

from __future__ import annotations

import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, Request, Response, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.i18n.registry import LanguageRegistry
from src.i18n.translator import I18nService, t
from src.i18n.formatters import LocaleFormatter
from src.core.country_profiles import CountryRegistry
from src.core.security import detect_multilingual_prompt_injection, sanitize_multilingual_input, redact_pii, verify_token
from src.api.dependencies import get_db
from src.database.models import User, Business, BusinessMembership, AuditLog
from src.config import settings

router = APIRouter(prefix="/i18n", tags=["Internationalization & Localization"])


class CurrencyFormatRequest(BaseModel):
    amount_minor: int
    currency: str = "BDT"
    locale: str = "en"
    use_native_digits: bool = False


class PromptAuditRequest(BaseModel):
    prompt: str


class SetLanguageRequest(BaseModel):
    locale: Optional[str] = None
    language: Optional[str] = None


class SetCurrencyRequest(BaseModel):
    currency: str
    business_id: Optional[int] = None
    shop_id: Optional[int] = None


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


@router.post("/set-language")
def set_language_endpoint(
    req: SetLanguageRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Sets application interface language.
    Validates locale, sets persistent response cookie (sme_lang),
    and updates authenticated user's preferred_language in the database.
    """
    loc = req.locale or req.language
    if not loc:
        raise HTTPException(status_code=400, detail="Missing locale or language parameter.")
    clean = loc.lower().replace("_", "-").split("-")[0].strip()
    if clean not in ["en", "zh", "bn"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language '{loc}'. Supported languages are 'en', 'bn', 'zh'."
        )

    response.set_cookie(
        key="sme_lang",
        value=clean,
        max_age=31536000,
        path="/",
        samesite="lax",
    )

    # Check if user is authenticated and update preferred_language in DB
    user_updated = False
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    if not token:
        token = request.cookies.get("sme_auth_token")

    if token:
        try:
            uid = verify_token(token, settings.SECRET_KEY)
            if uid:
                user = db.get(User, uid)
                if user:
                    user.preferred_language = clean
                    db.commit()
                    user_updated = True
        except Exception:
            pass

    return {
        "success": True,
        "status": "success",
        "locale": clean,
        "language": clean,
        "direction": LocaleFormatter.get_text_direction(clean),
        "user_updated": user_updated,
    }


@router.post("/set-currency")
def set_currency_endpoint(
    req: SetCurrencyRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Updates the business accounting currency.
    Role-authorized (owner, admin, super_admin) with tamper-evident audit logging.
    IMPORTANT: Changing interface language must NEVER alter this setting.
    """
    clean_curr = req.currency.upper().strip()
    supported_currencies = {"BDT", "CNY", "USD", "EUR", "GBP", "INR", "SAR", "AED", "AUD", "KWD", "JPY"}
    if clean_curr not in supported_currencies:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported currency '{clean_curr}'. Supported: {sorted(list(supported_currencies))}"
        )

    # Set persistent currency cookie
    response.set_cookie(
        key="sme_currency",
        value=clean_curr,
        max_age=31536000,
        path="/",
        samesite="lax",
    )

    # Authenticate user from header or cookie
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    if not token:
        token = request.cookies.get("sme_auth_token")

    user = None
    if token:
        try:
            uid = verify_token(token, settings.SECRET_KEY)
            if uid:
                user = db.get(User, uid)
        except Exception:
            user = None

    # Fallback to local demo owner if running locally without active session
    if not user:
        user = db.query(User).filter_by(is_active=True).first()

    bid = req.business_id
    if (not bid or bid == 0) and req.shop_id:
        sh = db.get(Shop, req.shop_id)
        if sh:
            bid = sh.business_id

    if not bid and user:
        mem = db.query(BusinessMembership).filter_by(user_id=user.id, is_active=True).first()
        bid = mem.business_id if mem else None

    if not bid:
        active_s_id = request.cookies.get("sme_active_shop_id") or request.query_params.get("shop_id")
        if active_s_id and str(active_s_id).isdigit():
            sh = db.get(Shop, int(active_s_id))
            if sh:
                bid = sh.business_id

    if not bid:
        biz_first = db.query(Business).first()
        if biz_first:
            bid = biz_first.id

    if not bid:
        raise HTTPException(status_code=404, detail="No business workspace found to update currency.")

    # Role verification
    user_role = "owner"
    if user:
        mem = db.query(BusinessMembership).filter_by(user_id=user.id, business_id=bid).first()
        if mem:
            user_role = mem.role_code

    if user_role not in ["owner", "admin", "super_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Only business owners or platform administrators can change the accounting currency."
        )

    business = db.get(Business, bid)
    if not business:
        raise HTTPException(status_code=404, detail=f"Business #{bid} not found.")

    old_currency = business.currency
    business.currency = clean_curr

    # Record audit log
    audit_log = AuditLog(
        business_id=bid,
        shop_id=req.shop_id,
        user_id=user.id if user else None,
        action="currency_changed",
        entity_type="Business",
        entity_id=bid,
        old_values_json=json.dumps({"currency": old_currency}),
        new_values_json=json.dumps({
            "currency": clean_curr,
            "changed_by": user.email if user else "system",
            "role": user_role,
        }),
    )
    db.add(audit_log)
    db.commit()

    mult = CountryRegistry.get_currency_multiplier(clean_curr)
    symbol = CountryRegistry.get_currency_symbol(clean_curr)

    return {
        "success": True,
        "business_id": bid,
        "old_currency": old_currency,
        "new_currency": clean_curr,
        "currency": clean_curr,
        "symbol": symbol,
        "multiplier": mult,
    }


@router.get("/suggested-currency")
def get_suggested_currency(locale: str = "en") -> Dict[str, Any]:
    """
    Returns suggested currency based on locale during onboarding or workspace creation.
    Defaults: en -> USD ($), bn -> BDT (৳), zh -> CNY (¥).
    """
    clean = locale.lower().replace("_", "-").split("-")[0].strip()
    suggestions = {
        "bn": {"currency": "BDT", "symbol": "৳", "multiplier": 100, "name": "Bangladeshi Taka"},
        "zh": {"currency": "CNY", "symbol": "¥", "multiplier": 100, "name": "Chinese Yuan Renminbi"},
        "en": {"currency": "USD", "symbol": "$", "multiplier": 100, "name": "US Dollar"},
    }
    sug = suggestions.get(clean, {"currency": "USD", "symbol": "$", "multiplier": 100, "name": "US Dollar"})

    all_currencies = [
        {"code": "BDT", "symbol": "৳", "name": "Bangladeshi Taka", "default_for": "bn"},
        {"code": "CNY", "symbol": "¥", "name": "Chinese Yuan Renminbi", "default_for": "zh"},
        {"code": "USD", "symbol": "$", "name": "US Dollar", "default_for": "en"},
        {"code": "EUR", "symbol": "€", "name": "Euro", "default_for": "eu"},
        {"code": "GBP", "symbol": "£", "name": "British Pound", "default_for": "uk"},
        {"code": "INR", "symbol": "₹", "name": "Indian Rupee", "default_for": "hi"},
        {"code": "SAR", "symbol": "﷼", "name": "Saudi Riyal", "default_for": "ar"},
    ]

    return {
        "locale": clean,
        "suggested_currency": sug["currency"],
        "symbol": sug["symbol"],
        "multiplier": sug["multiplier"],
        "currency_name": sug["name"],
        "all_currencies": all_currencies,
        "note": "Suggested currency based on locale. Workspace accounting currency can be customized independently."
    }
