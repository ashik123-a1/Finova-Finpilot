"""
Unit Tests for Model Registry and AI Evaluation Metadata.
"""

from src.ai.registry import ModelRegistry
from src.ai.guardrails import AiAssistantGuardrail
from src.database.models import ModelVersion, Dataset


def test_model_registry_initialization(db_session):
    """Verifies that all baseline tasks are registered."""
    ModelRegistry.initialize_default_model_registry(db_session)

    tasks = [
        "document_classification",
        "ocr_extraction",
        "cashflow_forecast",
        "loan_risk",
        "customer_segmentation",
        "demand_pricing",
    ]
    for task in tasks:
        model = ModelRegistry.get_active_model(db_session, task)
        assert model is not None, f"Active model for task {task} not found."
        assert model.is_active is True
        assert model.version == "v1.0.0"


def test_ai_guardrail_deterministic_calculation():
    """Verifies that AI guardrail executes exact deterministic financial calculations."""
    query_type = "profit_and_loss"
    params = {
        "sales_minor": [50_000_00, 30_000_00],
        "cogs_minor": [25_000_00],
        "operating_expenses_minor": [15_000_00],
    }
    result = AiAssistantGuardrail.execute_verified_financial_query(query_type, params)
    assert result["verified"] is True
    assert result["revenue"] == "80,000.00 BDT"
    assert result["cogs"] == "25,000.00 BDT"
    assert result["net_profit"] == "40,000.00 BDT"
    assert result["net_margin_pct"] == "50.00%"
