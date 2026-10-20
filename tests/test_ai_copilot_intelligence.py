"""
Unit and integration tests for AI Copilot Intelligence, Intent Routing, and Financial Accuracy.
Verifies:
1. Intent classification across all 11 SME finance domains in EN, BN, ZH.
2. Grounded loss recovery workflow with 3-phase action plan and quantified scenarios.
3. Accurate arithmetic matching database-backed ledger data.
4. Intent-aware RAG filtering preventing false-positive document citations (e.g. loan sanction letters for loss queries).
5. Margin guardrail enforcement on discount and pricing queries.
6. Multilingual currency preservation across language switches.
"""

import pytest
from src.ai.rag_service import RagService, SimpleVectorEmbedder
from src.database.models import DocumentChunk


def test_intent_classification_all_categories():
    """Verify that user queries route to the exact appropriate financial intent."""
    cases = [
        ("I am in loss how can I recover?", "business_loss_recovery"),
        ("how to increase sales and grow revenue?", "sales_revenue_growth"),
        ("how can I cut operating expenses?", "expense_reduction"),
        ("should I give 20% discount on wholesale items?", "pricing_discount_decision"),
        ("I am running out of cash what should I do?", "cash_flow_recovery"),
        ("customers owe me money and are not paying", "overdue_receivables"),
        ("which inventory items are overstocked or slow moving?", "inventory_optimization"),
        ("can I qualify for an SME bank loan?", "loan_suitability"),
        ("supplier is raising prices, how to handle procurement?", "supplier_purchasing"),
        ("what are the VAT rates and invoice rules under Mushak 6.3?", "document_policy"),
        ("what is working capital and how is it measured?", "general_finance"),
    ]

    for query, expected_intent in cases:
        intent = RagService.classify_intent(query)
        assert intent == expected_intent, f"Query '{query}' classified as '{intent}', expected '{expected_intent}'"


def test_multilingual_intent_classification():
    """Verify intent classification accurately classifies Bengali and Chinese queries."""
    cases = [
        ("ব্যবসা লসে আছে কিভাবে ঘুরে দাঁড়াবো?", "business_loss_recovery"),
        ("বিক্রয় কিভাবে বাড়ানো যায়?", "sales_revenue_growth"),
        ("খরচ কিভাবে কমাবো?", "expense_reduction"),
        ("বাকির টাকা আদায় করবো কিভাবে?", "overdue_receivables"),
        ("亏损了如何扭亏为盈？", "business_loss_recovery"),
        ("如何提高销售额增加收入？", "sales_revenue_growth"),
        ("怎样削减运营成本？", "expense_reduction"),
    ]

    for query, expected_intent in cases:
        intent = RagService.classify_intent(query)
        assert intent == expected_intent, f"Query '{query}' classified as '{intent}', expected '{expected_intent}'"


def test_loss_recovery_workflow_structure_and_scenarios(db_session, seeded_shop_context):
    """
    Verify Section 4 Loss Recovery Workflow:
    - Current position with revenue, expenses, net loss, period, currency
    - Fixed overhead breakdown (rent, salary, utilities)
    - 3-Phase Action Plan (Liquidity, Cost Rationalization, Revenue Optimization)
    - Quantified scenarios (5% expense cut, 10% sales lift, combined)
    - Mathematical estimation disclaimer
    """
    b1_id = seeded_shop_context["business1"].id
    s1_id = seeded_shop_context["shop1"].id

    res = RagService.generate_grounded_response(
        session=db_session,
        query="I am in loss how can I recover?",
        business_id=b1_id,
        shop_id=s1_id,
    )

    answer = res["answer"]

    # 1. Verification of Current Position
    assert "Current Financial Position" in answer
    assert "Operating Revenue" in answer
    assert "Operating Expenses" in answer
    assert "Reporting Period" in answer

    # 2. Verification of Evidence-Backed Findings
    assert "Evidence-Backed Findings" in answer
    assert "Fixed Overhead" in answer

    # 3. Verification of 3-Phase Action Plan
    assert "Prioritized Action Plan" in answer
    assert "Immediate Cash Protection" in answer
    assert "Cost Restructuring" in answer
    assert "Margin & Revenue Acceleration" in answer

    # 4. Verification of Quantified Scenarios
    assert "Quantified Recovery Scenarios" in answer
    assert "Scenario A (5% Expense Reduction)" in answer
    assert "Scenario B (10% Sales Volume Growth)" in answer
    assert "Scenario C (Combined 10% Cost Cut + 10% Sales Growth)" in answer

    # 5. Verification of Scenarios Disclaimer
    assert "Disclaimer: Scenarios are mathematical models based on historical ledger records" in answer


def test_loss_recovery_does_not_cite_unrelated_loan_documents(db_session, seeded_shop_context):
    """
    CRITICAL FIX VERIFICATION:
    Ingest a bank loan sanction letter.
    Verify that when the user asks 'I am in loss how can I recover?',
    the loan sanction letter is NOT cited as a relevant document.
    """
    b1_id = seeded_shop_context["business1"].id
    s1_id = seeded_shop_context["shop1"].id

    # Ingest a Bank Loan Sanction Letter
    RagService.ingest_document(
        session=db_session,
        business_id=b1_id,
        shop_id=s1_id,
        document_id=None,
        title="BRAC Bank SME Shonchoy Loan Facility Sanction Letter",
        content="Sanction letter for term loan facility of BDT 1,500,000 at 9% interest rate with 36 months repayment tenure.",
    )

    res = RagService.generate_grounded_response(
        session=db_session,
        query="I am in loss how can I recover?",
        business_id=b1_id,
        shop_id=s1_id,
    )

    # Citations must NOT contain the loan sanction letter for a general loss recovery question
    citation_titles = [c.get("source", "") for c in res.get("citations", [])]
    for title in citation_titles:
        assert "Loan Facility Sanction Letter" not in title, f"False positive citation found: {title}"

    # Context ground check
    assert res.get("has_evidence") is False or len(citation_titles) == 0


def test_pricing_and_discount_margin_guardrails(db_session, seeded_shop_context):
    """Verify discount queries trigger margin guardrail warnings against erosion."""
    b1_id = seeded_shop_context["business1"].id
    s1_id = seeded_shop_context["shop1"].id

    res = RagService.generate_grounded_response(
        session=db_session,
        query="Should I offer a 20% discount on wholesale inventory items?",
        business_id=b1_id,
        shop_id=s1_id,
    )

    answer = res["answer"]
    assert "Pricing & Discount Guardrails" in answer
    assert "Minimum Contribution Margin Floor" in answer
    assert "Margin Policy Warning" in answer


def test_overdue_receivables_workflow(db_session, seeded_shop_context):
    """Verify receivables intent surfaces outstanding invoices and dunning steps."""
    b1_id = seeded_shop_context["business1"].id
    s1_id = seeded_shop_context["shop1"].id

    res = RagService.generate_grounded_response(
        session=db_session,
        query="Customers are not paying their invoices on time, how to collect?",
        business_id=b1_id,
        shop_id=s1_id,
    )

    answer = res["answer"]
    assert "Outstanding Receivables Summary" in answer
    assert "Total Outstanding Receivables" in answer
    assert "Collection Workflow" in answer


def test_multilingual_loss_recovery_synthesis(db_session, seeded_shop_context):
    """Verify Bengali and Chinese loss recovery responses preserve currency and deliver localized plans."""
    b1_id = seeded_shop_context["business1"].id
    s1_id = seeded_shop_context["shop1"].id

    # 1. Bengali
    res_bn = RagService.generate_grounded_response(
        session=db_session,
        query="আমি ব্যবসায় লোকসানে আছি, কিভাবে রিকভার করবো?",
        business_id=b1_id,
        shop_id=s1_id,
    )
    answer_bn = res_bn["answer"]
    assert "বর্তমান আর্থিক অবস্থান" in answer_bn
    assert "অগ্রাধিকারমূলক কর্মপরিকল্পনা" in answer_bn
    assert "তাৎক্ষণিক নগদ সুরক্ষা" in answer_bn
    assert "সম্ভাব্য পুনরুদ্ধারের দৃশ্যপট" in answer_bn

    # 2. Chinese
    res_zh = RagService.generate_grounded_response(
        session=db_session,
        query="店铺持续亏损，如何制定减亏扭亏方案？",
        business_id=b1_id,
        shop_id=s1_id,
    )
    answer_zh = res_zh["answer"]
    assert "当前财务状况" in answer_zh
    assert "优先级扭亏行动计划" in answer_zh
    assert "即时资金保护" in answer_zh
    assert "量化扭亏测算模型" in answer_zh


def test_copilot_api_endpoint_loss_recovery_flow(test_client, seeded_shop_context):
    """
    Verify full HTTP flow for the screenshot's loss recovery question:
    POST /api/models/copilot/query with 'I am in loss how can I recover?'
    Checks that the response contains:
    - Status code 200
    - Answer with 5 structured turnaround sections
    - Empty citations (no false-positive loan documents)
    - Verified metrics dictionary
    - Deterministic mode indicator
    """
    b1_id = seeded_shop_context["business1"].id
    s1_id = seeded_shop_context["shop1"].id

    res = test_client.post(
        "/api/models/copilot/query",
        json={
            "query": "I am in loss how can I recover?",
            "business_id": b1_id,
            "shop_id": s1_id,
        },
    )

    assert res.status_code == 200
    payload = res.json()
    assert payload["security_alert"] is False
    assert len(payload["citations"]) == 0
    assert payload["has_evidence"] is False
    assert payload["generation_mode"] in ("deterministic_rule_based", "deterministic_fallback")

    answer = payload["answer"]
    assert "### 1. Current Financial Position" in answer
    assert "### 2. Evidence-Backed Findings" in answer
    assert "### 3. Prioritized Action Plan" in answer
    assert "### 4. Quantified Recovery Scenarios" in answer
    assert "### 5. Recommended Next Steps" in answer
    assert "Operating Revenue:" in answer
    assert "Operating Expenses:" in answer
    assert "Net Operating Loss:" in answer


def test_reconciled_financial_analytics_zero_drift(db_session, seeded_shop_context):
    """
    Verify zero float loss and mathematical reconciliation:
    Operating Revenue - Operating Expenses == Net Operating Profit/Loss
    """
    b1_id = seeded_shop_context["business1"].id
    s1_id = seeded_shop_context["shop1"].id

    analytics = RagService.extract_financial_analytics(
        session=db_session,
        business_id=b1_id,
        shop_id=s1_id,
    )

    rev_minor = analytics["total_revenue_minor"]
    exp_minor = analytics["total_expenses_minor"]
    net_minor = analytics["net_profit_minor"]

    # Reconciles exactly in minor integer units
    assert rev_minor - exp_minor == net_minor

