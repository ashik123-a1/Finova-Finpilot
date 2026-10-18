"""
Automated Unit Tests for Evaluation Framework, Metrics, Split Integrity, and Ablations.
Verifies:
- Classification, OCR, Forecasting, and Clustering Metric calculations.
- Splitter leakage prevention and disjointness assertions.
- Chronological forecasting rolling-origin monotonicity.
- Ablation logic and safety thresholds.
"""

import pytest
import numpy as np
from src.evaluation.metrics import (
    compute_classification_metrics,
    character_error_rate,
    word_error_rate,
    field_exact_match_rate,
    mean_absolute_error,
    root_mean_squared_error,
    mean_absolute_scaled_error,
    empirical_ci_coverage,
    evaluate_clustering_stability,
)
from src.evaluation.data_splitters import DataSplitter
from src.ai.pricing_demand import DemandAndPricingEngine
from src.evaluation.ablation import (
    run_document_pipeline_ablation,
    run_routing_policy_ablation,
    run_assistant_guardrails_ablation,
)


def test_classification_metrics_correctness():
    y_true = ["cat", "dog", "dog", "cat", "bird"]
    y_pred = ["cat", "dog", "cat", "cat", "bird"]
    labels = ["cat", "dog", "bird"]

    metrics = compute_classification_metrics(y_true, y_pred, labels)
    assert metrics["accuracy"] == 0.8
    assert "macro_f1" in metrics
    assert "confusion_matrix" in metrics
    assert metrics["labels"] == labels


def test_ocr_cer_and_wer_metrics():
    # Identical strings
    assert character_error_rate("ABC", "ABC") == 0.0
    assert word_error_rate("hello world", "hello world") == 0.0

    # 1 character substitution out of 4
    cer = character_error_rate("cash", "cast")
    assert cer == 0.25

    # 1 word deletion out of 3
    wer = word_error_rate("invoice number 123", "invoice 123")
    assert round(wer, 2) == 0.33


def test_forecast_metrics_and_mase():
    y_true = np.array([100.0, 110.0, 120.0, 130.0])
    y_pred = np.array([102.0, 108.0, 122.0, 128.0])
    y_train = np.array([70.0, 80.0, 90.0, 100.0])

    mae = mean_absolute_error(y_true, y_pred)
    rmse = root_mean_squared_error(y_true, y_pred)
    mase = mean_absolute_scaled_error(y_train, y_true, y_pred, seasonality=1)

    assert mae == 2.0
    assert rmse == 2.0
    # Naive step on y_train: all diffs are 10.0 -> mean is 10.0
    # MASE = MAE / mean_diff = 2.0 / 10.0 = 0.2
    assert round(mase, 2) == 0.20


def test_data_splitter_stratified_no_leakage():
    records = [{"image_id": i, "category": f"cat_{i % 3}", "val": i * 10} for i in range(60)]

    train, val, test = DataSplitter.stratified_train_val_test_split(
        records, target_field="category", train_ratio=0.7, val_ratio=0.15, test_ratio=0.15, seed=42
    )

    assert len(train) + len(val) + len(test) == 60

    # Test disjointness (zero data leakage)
    train_ids = set(r["image_id"] for r in train)
    val_ids = set(r["image_id"] for r in val)
    test_ids = set(r["image_id"] for r in test)

    assert train_ids.isdisjoint(val_ids)
    assert train_ids.isdisjoint(test_ids)
    assert val_ids.isdisjoint(test_ids)


def test_chronological_rolling_origin_split_monotonicity():
    series = [{"day": i, "cash_flow": float(i * 100)} for i in range(100)]
    splits = DataSplitter.chronological_rolling_origin_split(
        series, min_train_days=30, horizon_days=7, step_days=10
    )

    assert len(splits) > 0
    for train_fold, test_fold in splits:
        assert len(test_fold) == 7
        # Ensure strict temporal ordering: all train points are strictly before test points
        assert train_fold[-1]["day"] < test_fold[0]["day"]
        assert train_fold[-1]["day"] + 1 == test_fold[0]["day"]


def test_pricing_demand_engine_replenishment_and_breakeven():
    res = DemandAndPricingEngine.calculate_safety_stock_and_reorder_point(
        daily_demand_mean=50.0,
        daily_demand_std=10.0,
        lead_time_days=4,
        service_level=0.95,
    )
    assert res["safety_stock_units"] > 0
    assert res["reorder_point_units"] > res["lead_time_demand_units"]

    # Elasticity breakeven verification
    elastic = DemandAndPricingEngine.estimate_price_elasticity_and_impact(
        current_price_minor=100_00,
        proposed_price_minor=90_00,
        unit_cost_minor=60_00,
        current_monthly_units=100.0,
        price_elasticity=-1.5,
    )
    assert elastic["is_profitable"] is False
    assert elastic["recommendation"] == "unfavorable"
    assert elastic["breakeven_units_required"] > 100.0


def test_ablation_engines_integrity():
    # Pipeline ablation
    pipe_ab = run_document_pipeline_ablation()
    assert pipe_ab["stages"][-1]["arithmetic_integrity_check_pct"] == 100.0
    assert pipe_ab["stages"][-1]["unverified_corruptions_posted"] == 0

    # Routing ablation
    route_ab = run_routing_policy_ablation()
    assert route_ab["policies"][1]["ledger_contamination_rate_pct"] == 0.0

    # Assistant guardrail ablation
    guard_ab = run_assistant_guardrails_ablation()
    assert guard_ab["guardrail_arithmetic_drift_rate_pct"] == 0.0
    assert guard_ab["regulatory_dscr_compliance_pct"] == 100.0
