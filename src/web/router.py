"""
Web Application Router for SME Finance Copilot.
Renders Jinja2 HTML templates for public marketing and authenticated app portal screens.
Integrates with multi-shop context, language preferences, and signed HMAC authentication.
"""

from __future__ import annotations

import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Optional
import json
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2 import pass_context

from src.config import settings
from src.database.connection import SessionLocal
from src.database.models import User, Business, Shop, BusinessMembership
from src.core.security import verify_token
from src.i18n.translator import I18nService
from src.i18n.registry import LanguageRegistry
from src.i18n.formatters import LocaleFormatter
from src.core.country_profiles import CountryRegistry

logger = logging.getLogger("sme_finance_copilot.web")

# Templates directory
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Register context-aware i18n translation filter into Jinja2 environment
@pass_context
def _t(context, key: str, locale: Optional[str] = None, **kwargs) -> str:
    if not locale:
        locale = context.get("current_lang", "en")
    return I18nService.translate(key, locale=locale, **kwargs)

@pass_context
def _format_currency(context, amount_minor: int, currency: Optional[str] = None, use_native_digits: bool = False) -> str:
    locale = context.get("current_lang", "en")
    if not currency:
        biz = context.get("business", {})
        currency = biz.get("currency") if isinstance(biz, dict) else getattr(biz, "currency", "BDT")
    mult = CountryRegistry.get_currency_multiplier(currency or "BDT")
    return LocaleFormatter.format_currency(
        amount_minor=amount_minor,
        currency=currency or "BDT",
        locale=locale,
        minor_multiplier=mult,
        use_native_digits=use_native_digits,
    )

templates.env.globals["_"] = _t
templates.env.filters["_"] = _t
templates.env.filters["t"] = _t
templates.env.globals["format_currency"] = _format_currency
templates.env.filters["format_currency"] = _format_currency
templates.env.globals["app_name"] = settings.APP_NAME
templates.env.globals["environment"] = settings.ENVIRONMENT
templates.env.globals["default_currency"] = settings.DEFAULT_CURRENCY

router = APIRouter(tags=["Web UI Pages"], include_in_schema=False)


@contextmanager
def _get_db_context():
    from src.database.connection import get_db, SessionLocal
    try:
        from src.api.app import app
        override = app.dependency_overrides.get(get_db)
        if override:
            gen = override()
            db = next(gen)
            try:
                yield db
            finally:
                pass
            return
    except Exception:
        pass
    with SessionLocal() as db:
        yield db


def get_web_context(request: Request, is_landing: bool = False) -> dict:
    """
    Extracts current user session, shop context, active language, and shop list.
    Gracefully defaults to demo context when running in local development mode.
    Multi-tier language resolution:
    1. Landing Page default: Strictly 'en' unless explicit ?lang= query param is provided.
    2. Query param (?lang=bn)
    3. User profile preference in DB (user.preferred_language)
    4. Session / Cookie (sme_lang=bn)
    5. HTTP Accept-Language header
    6. Default 'en'
    """
    # 1. Resolve token from Authorization header or cookie
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    if not token:
        token = request.cookies.get("sme_auth_token")

    user_info = None
    active_shop_id = request.query_params.get("shop_id") or request.cookies.get("sme_active_shop_id")
    active_business_id = request.query_params.get("business_id") or request.cookies.get("sme_active_business_id")
    active_role = request.cookies.get("sme_role") or "owner"
    user_preferred_lang = None

    if token:
        try:
            uid = verify_token(token, settings.SECRET_KEY)
            if uid:
                with _get_db_context() as db:
                    u = db.query(User).filter_by(id=uid).first()
                    if u and u.preferred_language:
                        user_preferred_lang = u.preferred_language
                    mem = db.query(BusinessMembership).filter_by(user_id=uid, is_active=True).first()
                    resolved_role = mem.role_code if mem else active_role
                    resolved_bid = mem.business_id if mem else (int(active_business_id) if active_business_id else None)
                    resolved_name = u.full_name if u else f"User #{uid}"
                    resolved_email = u.email if u else "user@domain.com"
                    user_info = {
                        "user_id": uid,
                        "username": u.email.split("@")[0] if u else f"user_{uid}",
                        "full_name": resolved_name,
                        "email": resolved_email,
                        "role": resolved_role,
                        "business_id": resolved_bid,
                        "token": token,
                        "preferred_language": user_preferred_lang or "en",
                    }
        except Exception:
            user_info = None

    # Language resolution hierarchy:
    # 1. Landing Page default: Strictly 'en' unless explicit ?lang= query param is provided
    # 2. Query parameter (?lang=bn)
    # 3. User profile preference in DB (user.preferred_language)
    # 4. Session / Cookie (sme_lang=bn)
    # 5. HTTP Accept-Language header
    # 6. Default 'en'
    query_lang = request.query_params.get("lang")
    cookie_lang = request.cookies.get("sme_lang")
    header_lang = request.headers.get("accept-language", "")

    req_path = getattr(request, "url", None) and getattr(request.url, "path", "")
    if is_landing or req_path in ["/", "/landing"]:
        if query_lang:
            chosen_lang = query_lang
        else:
            chosen_lang = "en"
    elif query_lang:
        chosen_lang = query_lang
    elif user_preferred_lang and user_preferred_lang != "en":
        chosen_lang = user_preferred_lang
    elif cookie_lang:
        chosen_lang = cookie_lang
    elif user_preferred_lang:
        chosen_lang = user_preferred_lang
    elif header_lang:
        hl = header_lang.lower()
        if "bn" in hl:
            chosen_lang = "bn"
        elif "zh" in hl:
            chosen_lang = "zh"
        else:
            chosen_lang = "en"
    else:
        chosen_lang = "en"

    clean_lang = chosen_lang.lower().replace("_", "-").split("-")[0].strip()
    if clean_lang not in ["en", "zh", "bn"]:
        clean_lang = "en"

    # If language was resolved and user is authenticated, sync to user preference in DB
    if user_info and user_info.get("user_id"):
        try:
            with _get_db_context() as db:
                db_u = db.query(User).filter_by(id=user_info["user_id"]).first()
                if db_u and db_u.preferred_language != clean_lang:
                    db_u.preferred_language = clean_lang
                    db.commit()
            user_info["preferred_language"] = clean_lang
        except Exception:
            pass

    # Fallback to local demo user for immediate out-of-the-box exploration
    if not user_info:
        user_info = {
            "user_id": 1,
            "username": f"demo_{active_role}",
            "full_name": f"Ashikur Rahman ({active_role.title()})",
            "email": f"{active_role}@smedemo.com",
            "role": active_role,
            "business_id": int(active_business_id) if active_business_id else 19,
            "is_demo": True,
            "preferred_language": clean_lang,
        }

    # Fetch shops from database for shop switcher dropdown
    shops_data = []
    business_data = None
    try:
        with _get_db_context() as db:
            b = None
            if active_business_id:
                try:
                    b = db.query(Business).filter(Business.id == int(active_business_id)).first()
                except Exception:
                    b = None
            if not b and active_shop_id and str(active_shop_id).isdigit():
                try:
                    sh = db.get(Shop, int(active_shop_id))
                    if sh and sh.business_id:
                        b = db.get(Business, sh.business_id)
                except Exception:
                    b = None
            if not b:
                b = db.query(Business).first()

            # Check explicit currency cookie / query
            cookie_currency = request.query_params.get("currency") or request.cookies.get("sme_currency")
            if cookie_currency and cookie_currency.upper() in ["BDT", "CNY", "USD", "EUR", "GBP", "INR", "SAR", "AED", "AUD", "JPY"]:
                if b and b.currency != cookie_currency.upper():
                    b.currency = cookie_currency.upper()
                    try:
                        db.commit()
                    except Exception:
                        pass

            if b:
                active_business_id = str(b.id)
                user_info["business_id"] = b.id
                business_data = {
                    "id": b.id,
                    "name": b.name,
                    "tax_identifier": b.tax_id or "BIN-99281-002",
                    "currency": b.currency,
                }
                shops = db.query(Shop).filter(Shop.business_id == b.id).all()
                for s in shops:
                    shops_data.append({
                        "id": s.id,
                        "name": s.name,
                        "address": s.address or "Dhaka, Bangladesh",
                        "is_active": s.is_active,
                    })
                if shops:
                    valid_ids = [str(s.id) for s in shops]
                    if not active_shop_id or active_shop_id not in valid_ids:
                        active_shop_id = str(shops[0].id)
    except Exception as e:
        logger.debug("Could not query DB for shop switcher: %s", e)

    if not business_data:
        cookie_currency = request.query_params.get("currency") or request.cookies.get("sme_currency")
        business_data = {
            "id": int(active_business_id or 19),
            "name": "Bismillah Store (Synthetic)",
            "tax_identifier": "BIN-99281-002",
            "currency": cookie_currency.upper() if cookie_currency else settings.DEFAULT_CURRENCY,
            "is_synthetic": True,
        }
    if not active_shop_id:
        active_shop_id = "28"

    active_shop_int = int(active_shop_id) if str(active_shop_id).isdigit() else 28
    active_shop_obj = next((s for s in shops_data if s["id"] == active_shop_int), None)
    active_shop_name = active_shop_obj["name"] if active_shop_obj else f"Shop #{active_shop_int}"

    I18nService.reload_catalogs()
    locale_catalog = I18nService._CATALOGS.get(clean_lang, I18nService._CATALOGS.get("en", {}))

    return {
        "request": request,
        "current_user": user_info,
        "business": business_data,
        "shops": shops_data,
        "active_shop_id": active_shop_int,
        "active_shop_name": active_shop_name,
        "is_synthetic": business_data.get("is_synthetic", True),
        "current_lang": clean_lang,
        "current_currency": business_data.get("currency", "BDT"),
        "translations_json": json.dumps(locale_catalog, ensure_ascii=False),
        "available_languages": [
            {"code": "en", "name": "English", "native": "English", "flag": "🇬🇧"},
            {"code": "zh", "name": "Simplified Chinese", "native": "简体中文", "flag": "🇨🇳"},
            {"code": "bn", "name": "Bengali", "native": "বাংলা", "flag": "🇧🇩"},
        ],
    }


def render_template(template_name: str, ctx: dict, status_code: int = 200) -> HTMLResponse:
    """
    Renders an HTML template while stamping the resolved language into the browser
    cookie (sme_lang). This guarantees persistent localization across reloads and navigations.
    """
    resp = templates.TemplateResponse(template_name, ctx, status_code=status_code)
    current_lang = ctx.get("current_lang", "en")
    resp.set_cookie(
        key="sme_lang",
        value=current_lang,
        max_age=31536000,
        path="/",
        samesite="lax",
    )
    return resp


# ==============================================================================
# Public Marketing & Auth Pages
# ==============================================================================

@router.get("/landing", response_class=HTMLResponse)
def landing_page(request: Request):
    """Marketing Landing Page showcasing SME Finance Copilot capabilities."""
    ctx = get_web_context(request, is_landing=True)
    return render_template("landing.html", ctx)


@router.get("/how-it-works", response_class=HTMLResponse)
def how_it_works_page(request: Request):
    """Comprehensive Operator Guide & Interactive System Workflow."""
    ctx = get_web_context(request)
    return render_template("how_it_works.html", ctx)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Sign-in screen with 1-click Quick Demo Role Switcher."""
    ctx = get_web_context(request)
    return render_template("login.html", ctx)


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    """Registration and shop onboarding screen."""
    ctx = get_web_context(request)
    return render_template("register.html", ctx)


@router.get("/logout")
def logout():
    """Clears authentication cookies and redirects to landing page."""
    resp = RedirectResponse(url="/landing", status_code=status.HTTP_302_FOUND)
    resp.delete_cookie("sme_auth_token")
    return resp


# ==============================================================================
# Authenticated App Portal Pages
# ==============================================================================

@router.get("/app", response_class=HTMLResponse)
def app_root(request: Request):
    """Default redirect to main KPI dashboard."""
    return RedirectResponse(url="/app/dashboard", status_code=status.HTTP_302_FOUND)


@router.get("/app/dashboard", response_class=HTMLResponse)
def dashboard_view(request: Request):
    """Main Executive Financial & Cash-Flow Dashboard."""
    ctx = get_web_context(request)
    ctx["active_page"] = "dashboard"
    return render_template("app/dashboard.html", ctx)


@router.get("/app/finance", response_class=HTMLResponse)
def finance_view(request: Request):
    """P&L Statements, Sales Ledger, and Expense Ledgers with date filters."""
    ctx = get_web_context(request)
    ctx["active_page"] = "finance"
    return render_template("app/finance.html", ctx)


@router.get("/app/reports", response_class=HTMLResponse)
def reports_view(request: Request):
    """Central Business Intelligence Report Center with live previews, CSV/PDF exports, and database backups."""
    ctx = get_web_context(request)
    ctx["active_page"] = "reports"
    return render_template("app/reports.html", ctx)


@router.get("/app/forecast", response_class=HTMLResponse)
def forecast_view(request: Request):
    """ARIMA/GBDT Cash-Flow Forecasting with 95% confidence intervals and runway."""
    ctx = get_web_context(request)
    ctx["active_page"] = "forecast"
    return render_template("app/forecast.html", ctx)


@router.get("/app/documents", response_class=HTMLResponse)
def documents_view(request: Request):
    """Document Capture, OCR Extraction, and Human Review Gateway."""
    ctx = get_web_context(request)
    ctx["active_page"] = "documents"
    return render_template("app/documents.html", ctx)


@router.get("/app/loans", response_class=HTMLResponse)
def loans_view(request: Request):
    """SME Financing Options, DSCR Suitability, and Bank Comparison Matrix."""
    ctx = get_web_context(request)
    ctx["active_page"] = "loans"
    return render_template("app/loans.html", ctx)


@router.get("/app/inventory", response_class=HTMLResponse)
def inventory_view(request: Request):
    """Inventory Valuation, Low Stock Warnings, and Receivables Aging."""
    ctx = get_web_context(request)
    ctx["active_page"] = "inventory"
    return render_template("app/inventory.html", ctx)


@router.get("/app/customers", response_class=HTMLResponse)
def customers_view(request: Request):
    """Customer Directory, RFM Segmentation, and Polite Payment Reminders."""
    ctx = get_web_context(request)
    ctx["active_page"] = "customers"
    return render_template("app/customers.html", ctx)


@router.get("/app/simulations", response_class=HTMLResponse)
def simulations_view(request: Request):
    """What-if Business Decision Simulations: Break-even, Pricing, and Capex ROI."""
    ctx = get_web_context(request)
    ctx["active_page"] = "simulations"
    return render_template("app/simulations.html", ctx)


@router.get("/app/copilot", response_class=HTMLResponse)
def copilot_view(request: Request):
    """Real-time Financial AI Copilot Conversational Assistant."""
    ctx = get_web_context(request)
    ctx["active_page"] = "copilot"
    return render_template("app/copilot.html", ctx)


@router.get("/app/voice", response_class=HTMLResponse)
def voice_view(request: Request):
    """Futuristic Cyber-Fintech Real-Time Voice Assistant HUD Console."""
    ctx = get_web_context(request)
    ctx["active_page"] = "voice"
    return render_template("app/voice.html", ctx)


@router.get("/app/audit", response_class=HTMLResponse)
def audit_view(request: Request):
    """Tamper-Evident Audit Trails, Multi-Tenant Status, and Model Registry."""
    ctx = get_web_context(request)
    ctx["active_page"] = "audit"
    return render_template("app/audit.html", ctx)


@router.get("/app/settings", response_class=HTMLResponse)
def settings_view(request: Request):
    """Business Profile, Shop Settings, User Permissions, and Local DB Info."""
    ctx = get_web_context(request)
    ctx["active_page"] = "settings"
    return render_template("app/settings.html", ctx)


@router.get("/app/onboarding", response_class=HTMLResponse)
def onboarding_view(request: Request):
    """Progressive 4-Step Commercial Workspace Onboarding Wizard."""
    ctx = get_web_context(request)
    ctx["active_page"] = "onboarding"
    return render_template("app/onboarding.html", ctx)


@router.get("/app/admin", response_class=HTMLResponse)
def admin_view(request: Request):
    """Platform Super Admin Dashboard for Platform Telemetry and Multi-Tenant Oversight."""
    ctx = get_web_context(request)
    current_user = ctx.get("current_user", {})
    if current_user.get("role") != "super_admin":
        logger.warning(
            "Unauthorized access to /app/admin by user %s (role=%s)",
            current_user.get("user_id"),
            current_user.get("role")
        )
        return RedirectResponse(
            url="/app/dashboard?denied=super_admin_required",
            status_code=status.HTTP_302_FOUND
        )
    ctx["active_page"] = "admin"
    return render_template("app/admin.html", ctx)


@router.get("/app/notifications", response_class=HTMLResponse)
def notifications_view(request: Request):
    """Persistent Notification Center with unread badges, filter tabs, and mark-as-read."""
    ctx = get_web_context(request)
    ctx["active_page"] = "notifications"
    return render_template("app/notifications.html", ctx)


