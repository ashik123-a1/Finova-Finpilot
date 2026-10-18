"""
Test Suite for Web UI and Portal Template Endpoints.
Verifies that all marketing and authenticated application screens render HTTP 200
with correct HTML structure, language parameters, and static assets.
"""

import pytest
from fastapi.testclient import TestClient


def test_landing_page_renders(test_client: TestClient):
    resp = test_client.get("/landing")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "SME" in resp.text
    assert "FINANCE" in resp.text
    assert "Autonomous" in resp.text


def test_root_content_negotiation(test_client: TestClient):
    # API / test client default -> JSON
    json_resp = test_client.get("/")
    assert json_resp.status_code == 200
    assert json_resp.headers["content-type"].startswith("application/json")
    assert json_resp.json()["status"] == "online"

    # Browser Accept header -> HTML
    html_resp = test_client.get("/", headers={"Accept": "text/html,application/xhtml+xml"})
    assert html_resp.status_code == 200
    assert "text/html" in html_resp.headers["content-type"]
    assert "SME" in html_resp.text


def test_login_and_register_pages(test_client: TestClient):
    resp = test_client.get("/login")
    assert resp.status_code == 200
    assert "1-Click Quick Demo Login" in resp.text
    assert "Store Owner" in resp.text

    resp = test_client.get("/register")
    assert resp.status_code == 200
    assert "Onboard Your Business" in resp.text


def test_app_redirect_to_dashboard(test_client: TestClient):
    resp = test_client.get("/app", follow_redirects=False)
    assert resp.status_code in [302, 307]
    assert resp.headers["location"] == "/app/dashboard"


def test_portal_views_render_successfully(test_client: TestClient):
    endpoints = [
        ("/app/dashboard", "Executive Financial Dashboard"),
        ("/app/finance", "Financial Ledgers"),
        ("/app/forecast", "Cash-Flow Forecasting"),
        ("/app/documents", "Document Capture"),
        ("/app/loans", "SME Loan Underwriting"),
        ("/app/inventory", "Inventory Valuation"),
        ("/app/customers", "Customer Management"),
        ("/app/simulations", "Business Decision Intelligence"),
        ("/app/copilot", "Autonomous Financial AI Copilot"),
        ("/app/audit", "Security Audit"),
        ("/app/settings", "Organization Settings"),
    ]

    for path, expected_title in endpoints:
        resp = test_client.get(path)
        assert resp.status_code == 200, f"Failed on path {path}: {resp.status_code}"
        assert "text/html" in resp.headers["content-type"]
        assert expected_title in resp.text, f"Title {expected_title} not found in {path}"


def test_multilingual_language_switch_in_web(test_client: TestClient):
    # Chinese request
    resp = test_client.get("/app/dashboard?lang=zh")
    assert resp.status_code == 200
    assert '<html lang="zh"' in resp.text

    # Bengali request
    resp = test_client.get("/app/dashboard?lang=bn")
    assert resp.status_code == 200
    assert '<html lang="bn"' in resp.text


def test_static_assets_served(test_client: TestClient):
    resp = test_client.get("/static/css/theme.css")
    assert resp.status_code == 200
    assert "lg-primary" in resp.text

    resp = test_client.get("/static/js/app.js")
    assert resp.status_code == 200
    assert "showToast" in resp.text
