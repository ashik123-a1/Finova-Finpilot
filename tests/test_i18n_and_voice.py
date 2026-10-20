"""
Comprehensive Test Suite for Multilingual Localization, Business Currency Separation, and Voice AI.
Tests the 5-tier language resolution hierarchy, API endpoints, role-gated currency updates,
audit logging, locale-aware currency formatting, multilingual RAG copilot, and Voice AI.
"""

from __future__ import annotations

import json
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from src.database.models import User, Business, Shop, BusinessMembership, AuditLog
from src.core.security import create_token
from src.config import settings
from src.i18n.translator import I18nService, t
from src.i18n.formatters import LocaleFormatter
from src.ai.voice_service import VoiceService
from src.ai.rag_service import RagService
from src.core.money import Money


# ============================================================================
# 1. LANGUAGE RESOLUTION HIERARCHY TESTS
# ============================================================================

def test_language_resolution_query_param_priority(test_client, seeded_shop_context, db_session):
    """Tier 1: URL query param (?lang=bn) has top priority, overriding DB user preference and cookie."""
    user1 = seeded_shop_context["user1"]
    shop1 = seeded_shop_context["shop1"]
    user1.preferred_language = "en"
    db_session.commit()

    token = create_token(user1.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}
    cookies = {"sme_lang": "zh"}

    # Request with ?lang=bn
    response = test_client.get(f"/app/dashboard?shop_id={shop1.id}&lang=bn", headers=headers, cookies=cookies)
    assert response.status_code == 200
    # Must contain Bengali localized text
    assert "ড্যাশবোর্ড" in response.text
    assert 'lang="bn"' in response.text


def test_language_resolution_db_user_preference(test_client, seeded_shop_context, db_session):
    """Tier 2: Authenticated user's preferred_language in DB overrides cookie and Accept-Language header."""
    user1 = seeded_shop_context["user1"]
    shop1 = seeded_shop_context["shop1"]
    user1.preferred_language = "zh"
    db_session.commit()

    token = create_token(user1.id, settings.SECRET_KEY)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept-Language": "bn,en;q=0.8",
    }
    cookies = {"sme_lang": "en"}

    # No ?lang query param provided
    response = test_client.get(f"/app/dashboard?shop_id={shop1.id}", headers=headers, cookies=cookies)
    assert response.status_code == 200
    # Must use user1's DB preference: zh
    assert "控制台仪表盘" in response.text
    assert 'lang="zh"' in response.text


def test_language_resolution_cookie_priority(test_client, seeded_shop_context):
    """Tier 3: sme_lang cookie overrides Accept-Language header when no query param or DB preference."""
    headers = {
        "Accept-Language": "en-US,en;q=0.9",
    }
    cookies = {"sme_lang": "bn"}

    # Public or unauthenticated request with cookie
    response = test_client.get("/login", headers=headers, cookies=cookies)
    assert response.status_code == 200
    assert 'lang="bn"' in response.text


def test_language_resolution_accept_language_header(test_client):
    """Tier 4: Accept-Language header is respected when no query, DB user, or cookie is present."""
    headers = {
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    response = test_client.get("/login", headers=headers)
    assert response.status_code == 200
    assert 'lang="zh"' in response.text


def test_language_resolution_default_fallback(test_client):
    """Tier 5: Default fallback to English when no language hints or invalid languages are given."""
    headers = {
        "Accept-Language": "xx-YY,zz;q=0.1",
    }
    response = test_client.get("/login", headers=headers)
    assert response.status_code == 200
    assert 'lang="en"' in response.text


# ============================================================================
# 2. API ENDPOINTS: /api/i18n/set-language & /api/i18n/suggested-currency
# ============================================================================

def test_api_set_language_authenticated(test_client, seeded_shop_context, db_session):
    """POST /api/i18n/set-language updates DB preferred_language and sets sme_lang cookie."""
    user1 = seeded_shop_context["user1"]
    token = create_token(user1.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}

    res = test_client.post(
        "/api/i18n/set-language",
        json={"language": "bn"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["language"] == "bn"
    assert "sme_lang" in res.cookies
    assert res.cookies["sme_lang"] == "bn"

    # Verify DB was updated
    db_session.refresh(user1)
    assert user1.preferred_language == "bn"


def test_api_set_language_unauthenticated(test_client):
    """POST /api/i18n/set-language sets sme_lang cookie even when unauthenticated."""
    res = test_client.post(
        "/api/i18n/set-language",
        json={"language": "zh"},
    )
    assert res.status_code == 200
    assert res.cookies["sme_lang"] == "zh"


def test_api_set_language_unsupported_rejection(test_client):
    """POST /api/i18n/set-language rejects unsupported locale codes."""
    res = test_client.post(
        "/api/i18n/set-language",
        json={"language": "klingon"},
    )
    assert res.status_code == 400
    assert "Unsupported language" in res.json()["detail"]


def test_api_suggested_currency(test_client):
    """GET /api/i18n/suggested-currency returns regional currency recommendations."""
    res_en = test_client.get("/api/i18n/suggested-currency?locale=en")
    assert res_en.status_code == 200
    assert res_en.json()["suggested_currency"] == "USD"

    res_bn = test_client.get("/api/i18n/suggested-currency?locale=bn")
    assert res_bn.status_code == 200
    assert res_bn.json()["suggested_currency"] == "BDT"

    res_zh = test_client.get("/api/i18n/suggested-currency?locale=zh")
    assert res_zh.status_code == 200
    assert res_zh.json()["suggested_currency"] == "CNY"


# ============================================================================
# 3. API ENDPOINT: /api/i18n/set-currency & ROLE PERMISSIONS & AUDIT LOGGING
# ============================================================================

def test_api_set_currency_owner_success(test_client, seeded_shop_context, db_session):
    """POST /api/i18n/set-currency allows Owner to update business accounting currency and writes audit log."""
    user1 = seeded_shop_context["user1"]
    b1 = seeded_shop_context["business1"]
    b1.currency = "USD"
    db_session.commit()

    token = create_token(user1.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}

    res = test_client.post(
        "/api/i18n/set-currency",
        json={"business_id": b1.id, "currency": "BDT"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["currency"] == "BDT"

    # Verify DB business currency updated
    db_session.refresh(b1)
    assert b1.currency == "BDT"

    # Verify AuditLog entry was recorded
    audit = db_session.query(AuditLog).filter(
        AuditLog.business_id == b1.id,
        AuditLog.action == "currency_changed",
    ).first()
    assert audit is not None
    assert audit.user_id == user1.id
    new_vals = json.loads(audit.new_values_json) if isinstance(audit.new_values_json, str) else audit.new_values_json
    assert new_vals["currency"] == "BDT"


def test_api_set_currency_viewer_forbidden(test_client, seeded_shop_context, db_session):
    """POST /api/i18n/set-currency forbids non-admin/owner roles (e.g. viewer)."""
    b1 = seeded_shop_context["business1"]
    # Create viewer user
    viewer = User(
        email="viewer@example.com",
        hashed_password="hash",
        full_name="Viewer User",
        is_active=True,
    )
    db_session.add(viewer)
    db_session.flush()

    m_viewer = BusinessMembership(user_id=viewer.id, business_id=b1.id, role_code="viewer")
    db_session.add(m_viewer)
    db_session.commit()

    token = create_token(viewer.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}

    res = test_client.post(
        "/api/i18n/set-currency",
        json={"business_id": b1.id, "currency": "EUR"},
        headers=headers,
    )
    assert res.status_code == 403
    assert "Forbidden" in res.json()["detail"] or "Only business owners" in res.json()["detail"]


def test_api_set_currency_invalid_currency_code(test_client, seeded_shop_context):
    """POST /api/i18n/set-currency rejects invalid currency codes."""
    user1 = seeded_shop_context["user1"]
    b1 = seeded_shop_context["business1"]
    token = create_token(user1.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}

    res = test_client.post(
        "/api/i18n/set-currency",
        json={"business_id": b1.id, "currency": "BITCOIN"},
        headers=headers,
    )
    assert res.status_code == 400
    assert "Unsupported currency" in res.json()["detail"]


# ============================================================================
# 4. DECOUPLING: LANGUAGE VS BUSINESS CURRENCY & ZERO-FLOAT LOSS FORMATTING
# ============================================================================

def test_language_change_does_not_mutate_business_currency(test_client, seeded_shop_context, db_session):
    """CRITICAL: Changing interface language must NEVER modify or overwrite business.currency."""
    user1 = seeded_shop_context["user1"]
    b1 = seeded_shop_context["business1"]
    b1.currency = "USD"
    db_session.commit()

    token = create_token(user1.id, settings.SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}

    # User changes language to Bengali
    res1 = test_client.post("/api/i18n/set-language", json={"language": "bn"}, headers=headers)
    assert res1.status_code == 200

    db_session.refresh(b1)
    assert b1.currency == "USD", "Changing language to bn must NOT change business currency!"

    # User changes language to Chinese
    res2 = test_client.post("/api/i18n/set-language", json={"language": "zh"}, headers=headers)
    assert res2.status_code == 200

    db_session.refresh(b1)
    assert b1.currency == "USD", "Changing language to zh must NOT change business currency!"


def test_locale_formatter_financial_precision():
    """Verify LocaleFormatter precision across minor units and currencies."""
    # 12,345.67 USD in English
    formatted_en = LocaleFormatter.format_currency(1234567, "USD", "en")
    assert "$ 12,345.67" in formatted_en or "$12,345.67" in formatted_en

    # 12,345.67 USD in Bengali (preserves USD symbol or currency code, formats accurately)
    formatted_bn = LocaleFormatter.format_currency(1234567, "USD", "bn")
    assert "$" in formatted_bn or "USD" in formatted_bn

    # 50,000.00 BDT in Bengali
    formatted_bdt = LocaleFormatter.format_currency(5000000, "BDT", "bn")
    assert "৳" in formatted_bdt or "BDT" in formatted_bdt

    # 88,888.88 CNY in Chinese
    formatted_cny = LocaleFormatter.format_currency(8888888, "CNY", "zh")
    assert "¥" in formatted_cny or "CNY" in formatted_cny


# ============================================================================
# 5. MULTILINGUAL RAG COPILOT GROUNDING & FACT PRESERVATION
# ============================================================================

def test_multilingual_rag_pipeline_preserves_currency(seeded_shop_context, db_session):
    """RAG copilot responds in the query/user's language while grounding in business accounting currency."""
    shop1 = seeded_shop_context["shop1"]
    b1 = seeded_shop_context["business1"]
    b1.currency = "USD"
    db_session.commit()

    # Query in Bengali
    query_bn = "আমার বর্তমান নগদ উদ্বৃত্ত এবং আর্থিক অবস্থা কী?"
    resp_bn = RagService.generate_grounded_response(
        session=db_session,
        query=query_bn,
        business_id=b1.id,
        shop_id=shop1.id,
        user_role="owner",
        preferred_locale="bn",
    )
    assert resp_bn is not None
    # Must use business accounting currency ($/USD) rather than blindly switching to BDT
    assert "$" in resp_bn["answer"] or "USD" in resp_bn["answer"] or "ডলার" in resp_bn["answer"]
    assert "verified_metrics" in resp_bn

    # Query in Chinese
    query_zh = "请分析我们当前的现金流状况和净利润。"
    resp_zh = RagService.generate_grounded_response(
        session=db_session,
        query=query_zh,
        business_id=b1.id,
        shop_id=shop1.id,
        user_role="owner",
        preferred_locale="zh",
    )
    assert resp_zh is not None
    assert "$" in resp_zh["answer"] or "USD" in resp_zh["answer"] or "美元" in resp_zh["answer"]


# ============================================================================
# 6. MULTILINGUAL VOICE AI SERVICE & SPOKEN CURRENCY SEPARATION
# ============================================================================

def test_voice_ai_multilingual_spoken_currency_separation(seeded_shop_context, db_session):
    """Voice AI speaks the workspace's accounting currency (USD/BDT/CNY) regardless of query language."""
    shop1 = seeded_shop_context["shop1"]
    b1 = seeded_shop_context["business1"]
    user1 = seeded_shop_context["user1"]

    # Scenario A: Business currency is USD, user speaks in Bengali
    b1.currency = "USD"
    db_session.commit()

    res_bn = VoiceService.process_voice_command(
        session=db_session,
        transcript="আজ কত টাকা বিক্রি হয়েছে এবং লাভ কত?",
        user_id=user1.id,
        user_role="owner",
        business_id=b1.id,
        shop_id=shop1.id,
        locale="bn",
    )
    assert res_bn["status"] == "success"
    # Spoken currency in Bengali for USD must be "ডলার" (dollars)
    assert "ডলার" in res_bn["spoken_response"] or "$" in res_bn["spoken_response"]
    assert "বিক্রয়" in res_bn["spoken_response"] or "প্রফিট" in res_bn["spoken_response"]

    # Scenario B: Business currency is BDT, user speaks in English
    b1.currency = "BDT"
    db_session.commit()

    res_en = VoiceService.process_voice_command(
        session=db_session,
        transcript="How much did my shop earn today?",
        user_id=user1.id,
        user_role="owner",
        business_id=b1.id,
        shop_id=shop1.id,
        locale="en",
    )
    assert res_en["status"] == "success"
    # Spoken currency in English for BDT must be "Taka" or "BDT"
    assert "taka" in res_en["spoken_response"].lower() or "bdt" in res_en["spoken_response"].lower()

    # Scenario C: Business currency is CNY, user speaks in Chinese
    b1.currency = "CNY"
    db_session.commit()

    res_zh = VoiceService.process_voice_command(
        session=db_session,
        transcript="今天商店赚了多少钱，利润是多少？",
        user_id=user1.id,
        user_role="owner",
        business_id=b1.id,
        shop_id=shop1.id,
        locale="zh",
    )
    assert res_zh["status"] == "success"
    # Spoken currency in Chinese for CNY must be "元" (yuan)
    assert "元" in res_zh["spoken_response"] or "CNY" in res_zh["spoken_response"]


def test_landing_page_defaults_to_english_even_with_headers_or_cookies(test_client: TestClient):
    """Verifies that the public landing page strictly defaults to English ('en') regardless of cookies or Accept-Language headers."""
    # Scenario A: Visitor with Bengali cookie and Accept-Language header visits /landing without query param
    resp = test_client.get(
        "/landing",
        headers={"Accept-Language": "bn-BD,bn;q=0.9"},
        cookies={"sme_lang": "bn"},
    )
    assert resp.status_code == 200
    assert 'lang="en"' in resp.text
    # Check for English landing page heading / content
    assert "FINOVA" in resp.text
    assert "FINPILOT" in resp.text

    # Scenario B: Visitor with Chinese cookie visits root /
    resp_root = test_client.get(
        "/",
        headers={"Accept": "text/html", "Accept-Language": "zh-CN,zh;q=0.9"},
        cookies={"sme_lang": "zh"},
    )
    assert resp_root.status_code == 200
    assert 'lang="en"' in resp_root.text

    # Scenario C: Visitor explicitly requests Bengali via query parameter ?lang=bn
    resp_bn = test_client.get("/landing?lang=bn")
    assert resp_bn.status_code == 200
    assert 'lang="bn"' in resp_bn.text


def test_voice_ai_wake_word_hi_ashik_and_stop_ashik(test_client: TestClient):
    """Verifies that 'Hi Ashik' acts as an active hands-free wake word and greeting, and 'stop ashik' deactivates."""
    # 1. Status endpoint includes 'Hi Ashik'
    status_resp = test_client.get("/api/voice/status")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert "Hi Ashik" in data["wake_words"]
    assert "Stop Ashik" in data["stop_words"]

    # 2. Command with 'Hi Ashik'
    cmd_resp = test_client.post("/api/voice/command", json={"text": "Hi Ashik", "locale": "en"})
    assert cmd_resp.status_code == 200
    res_data = cmd_resp.json()
    assert res_data["status"] == "success"
    assert res_data["intent"] == "WAKE_WORD_GREETING"
    assert "Hi Ashik" in res_data["spoken_response"]
    assert "Hi Ashik" in res_data["text_response"]

    # 3. Bengali greeting with 'হাই আশিক'
    cmd_bn = test_client.post("/api/voice/command", json={"text": "হাই আশিক", "locale": "bn"})
    assert cmd_bn.status_code == 200
    assert cmd_bn.json()["status"] == "success"
    assert "হাই আশিক" in cmd_bn.json()["spoken_response"]

    # 4. Stop command with 'stop ashik'
    stop_resp = test_client.post("/api/voice/command", json={"text": "stop ashik", "locale": "en"})
    assert stop_resp.status_code == 200
    assert stop_resp.json()["intent"] == "CONTROL_STOP_COPILOT"
    assert "deactivated" in stop_resp.json()["spoken_response"].lower()

    # 5. Verify all locale files have "Hi Ashik" for wake_word_badge
    import glob
    for p in glob.glob("src/i18n/locales/*.json"):
        with open(p, "r", encoding="utf-8") as f:
            cat = json.load(f)
        assert cat.get("voice", {}).get("wake_word_badge") == '"Hi Ashik"', f"Failed in {p}"

