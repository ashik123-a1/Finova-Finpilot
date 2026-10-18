"""
Web Application Router for SME Finance Copilot.
Renders Jinja2 HTML templates for public marketing and authenticated app portal screens.
Integrates with multi-shop context, language preferences, and signed HMAC authentication.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.config import settings
from src.database.connection import SessionLocal
from src.database.models import User, Business, Shop
from src.core.security import verify_token
from src.i18n.translator import I18nService
from src.i18n.registry import LanguageRegistry
from src.core.country_profiles import CountryRegistry

logger = logging.getLogger("sme_finance_copilot.web")

# Templates directory
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Register i18n translation filter into Jinja2 environment
def _t(key: str, locale: str = "en", **kwargs) -> str:
    return I18nService.translate(key, locale=locale, **kwargs)

templates.env.globals["_"] = _t
templates.env.globals["app_name"] = settings.APP_NAME
templates.env.globals["environment"] = settings.ENVIRONMENT
templates.env.globals["default_currency"] = settings.DEFAULT_CURRENCY

router = APIRouter(tags=["Web UI Pages"], include_in_schema=False)


def get_web_context(request: Request) -> dict:
    """
    Extracts current user session, shop context, active language, and shop list.
    Gracefully defaults to demo context when running in local development mode.
    """
    # 1. Resolve language preference from query param, cookie, or default
    lang = request.query_params.get("lang") or request.cookies.get("sme_lang") or "en"
    clean_lang = lang.lower().split("-")[0].strip()
    if clean_lang not in ["en", "zh", "bn"]:
        clean_lang = "en"

    # 2. Resolve token from Authorization header or cookie
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    if not token:
        token = request.cookies.get("sme_auth_token")

    user_info = None
    active_shop_id = request.cookies.get("sme_active_shop_id")
    active_business_id = request.cookies.get("sme_active_business_id")
    active_role = request.cookies.get("sme_role") or "owner"

    if token:
        try:
            uid = verify_token(token, settings.SECRET_KEY)
            if uid:
                user_info = {
                    "user_id": uid,
                    "username": f"user_{uid}",
                    "email": "owner@dhakaretail.com",
                    "role": active_role,
                    "business_id": int(active_business_id) if active_business_id else None,
                    "token": token,
                }
        except Exception:
            user_info = None

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
        }

    # Fetch shops from database for shop switcher dropdown
    shops_data = []
    business_data = None
    try:
        with SessionLocal() as db:
            b = None
            if active_business_id:
                try:
                    b = db.query(Business).filter(Business.id == int(active_business_id)).first()
                except Exception:
                    b = None
            if not b:
                b = db.query(Business).first()

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
        business_data = {
            "id": int(active_business_id or 19),
            "name": "Bismillah Store (Synthetic)",
            "tax_identifier": "BIN-99281-002",
            "currency": settings.DEFAULT_CURRENCY,
            "is_synthetic": True,
        }
    if not active_shop_id:
        active_shop_id = "28"

    active_shop_int = int(active_shop_id) if active_shop_id.isdigit() else 28
    active_shop_obj = next((s for s in shops_data if s["id"] == active_shop_int), None)
    active_shop_name = active_shop_obj["name"] if active_shop_obj else f"Shop #{active_shop_int}"

    return {
        "request": request,
        "current_user": user_info,
        "business": business_data,
        "shops": shops_data,
        "active_shop_id": active_shop_int,
        "active_shop_name": active_shop_name,
        "is_synthetic": business_data.get("is_synthetic", True),
        "current_lang": clean_lang,
        "available_languages": [
            {"code": "en", "name": "English", "native": "English", "flag": "🇬🇧"},
            {"code": "zh", "name": "Simplified Chinese", "native": "简体中文", "flag": "🇨🇳"},
            {"code": "bn", "name": "Bengali", "native": "বাংলা", "flag": "🇧🇩"},
        ],
    }


# ==============================================================================
# Public Marketing & Auth Pages
# ==============================================================================

@router.get("/landing", response_class=HTMLResponse)
def landing_page(request: Request):
    """Marketing Landing Page showcasing SME Finance Copilot capabilities."""
    ctx = get_web_context(request)
    return templates.TemplateResponse("landing.html", ctx)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Sign-in screen with 1-click Quick Demo Role Switcher."""
    ctx = get_web_context(request)
    return templates.TemplateResponse("login.html", ctx)


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    """Registration and shop onboarding screen."""
    ctx = get_web_context(request)
    return templates.TemplateResponse("register.html", ctx)


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
    return templates.TemplateResponse("app/dashboard.html", ctx)


@router.get("/app/finance", response_class=HTMLResponse)
def finance_view(request: Request):
    """P&L Statements, Sales Ledger, and Expense Ledgers with date filters."""
    ctx = get_web_context(request)
    ctx["active_page"] = "finance"
    return templates.TemplateResponse("app/finance.html", ctx)


@router.get("/app/forecast", response_class=HTMLResponse)
def forecast_view(request: Request):
    """ARIMA/GBDT Cash-Flow Forecasting with 95% confidence intervals and runway."""
    ctx = get_web_context(request)
    ctx["active_page"] = "forecast"
    return templates.TemplateResponse("app/forecast.html", ctx)


@router.get("/app/documents", response_class=HTMLResponse)
def documents_view(request: Request):
    """Document Capture, OCR Extraction, and Human Review Gateway."""
    ctx = get_web_context(request)
    ctx["active_page"] = "documents"
    return templates.TemplateResponse("app/documents.html", ctx)


@router.get("/app/loans", response_class=HTMLResponse)
def loans_view(request: Request):
    """SME Financing Options, DSCR Suitability, and Bank Comparison Matrix."""
    ctx = get_web_context(request)
    ctx["active_page"] = "loans"
    return templates.TemplateResponse("app/loans.html", ctx)


@router.get("/app/inventory", response_class=HTMLResponse)
def inventory_view(request: Request):
    """Inventory Valuation, Low Stock Warnings, and Receivables Aging."""
    ctx = get_web_context(request)
    ctx["active_page"] = "inventory"
    return templates.TemplateResponse("app/inventory.html", ctx)


@router.get("/app/copilot", response_class=HTMLResponse)
def copilot_view(request: Request):
    """Real-time Financial AI Copilot Conversational Assistant."""
    ctx = get_web_context(request)
    ctx["active_page"] = "copilot"
    return templates.TemplateResponse("app/copilot.html", ctx)


@router.get("/app/audit", response_class=HTMLResponse)
def audit_view(request: Request):
    """Tamper-Evident Audit Trails, Multi-Tenant Status, and Model Registry."""
    ctx = get_web_context(request)
    ctx["active_page"] = "audit"
    return templates.TemplateResponse("app/audit.html", ctx)


@router.get("/app/customers", response_class=HTMLResponse)
def customers_view(request: Request):
    """Customer Directory, RFM Segmentation, and Polite Payment Reminders."""
    ctx = get_web_context(request)
    ctx["active_page"] = "customers"
    return templates.TemplateResponse("app/customers.html", ctx)


@router.get("/app/simulations", response_class=HTMLResponse)
def simulations_view(request: Request):
    """What-if Business Decision Simulations: Break-even, Pricing, and Capex ROI."""
    ctx = get_web_context(request)
    ctx["active_page"] = "simulations"
    return templates.TemplateResponse("app/simulations.html", ctx)


@router.get("/app/settings", response_class=HTMLResponse)
def settings_view(request: Request):
    """Business Profile, Shop Settings, User Permissions, and Local DB Info."""
    ctx = get_web_context(request)
    ctx["active_page"] = "settings"
    return templates.TemplateResponse("app/settings.html", ctx)


@router.get("/app/onboarding", response_class=HTMLResponse)
def onboarding_view(request: Request):
    """Progressive 4-Step Commercial Workspace Onboarding Wizard."""
    ctx = get_web_context(request)
    ctx["active_page"] = "onboarding"
    return templates.TemplateResponse("app/onboarding.html", ctx)

