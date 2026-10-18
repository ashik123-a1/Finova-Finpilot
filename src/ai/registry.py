"""
Model Registry and Evaluation Lifecycle Management.
Tracks model versions, feature schemas, hyperparameters, benchmark evaluation runs,
and explicit model limitations across all AI tasks.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.database.models import ModelVersion, EvaluationRun, Dataset, utc_now


class ModelRegistry:
    """Manages AI model metadata, active production models, and evaluation records."""

    @classmethod
    def register_model_version(
        cls,
        session: Session,
        task_name: str,
        model_name: str,
        version: str,
        architecture_description: str,
        feature_schema: Dict[str, Any],
        hyperparameters: Optional[Dict[str, Any]] = None,
        is_active: bool = True,
    ) -> ModelVersion:
        """Registers a new model version and optionally sets it as active."""
        if is_active:
            # Deactivate previous active models for this task
            stmt = select(ModelVersion).where(
                ModelVersion.task_name == task_name,
                ModelVersion.is_active == True,
            )
            for prev in session.scalars(stmt).all():
                prev.is_active = False

        mv = ModelVersion(
            task_name=task_name,
            model_name=model_name,
            version=version,
            architecture_description=architecture_description,
            feature_schema_json=json.dumps(feature_schema),
            hyperparameters_json=json.dumps(hyperparameters or {}),
            is_active=is_active,
        )
        session.add(mv)
        session.flush()
        return mv

    @classmethod
    def record_evaluation_run(
        cls,
        session: Session,
        model_version_id: int,
        dataset_id: int,
        metrics: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        is_synthetic: bool = True,
    ) -> EvaluationRun:
        """Records an evaluation run with exact measured metrics."""
        ev = EvaluationRun(
            model_version_id=model_version_id,
            dataset_id=dataset_id,
            run_timestamp=utc_now(),
            metrics_json=json.dumps(metrics),
            parameters_json=json.dumps(parameters or {}),
            notes=notes,
            is_synthetic_benchmark=is_synthetic,
        )
        session.add(ev)
        session.flush()
        return ev

    @classmethod
    def get_active_model(cls, session: Session, task_name: str) -> Optional[ModelVersion]:
        """Retrieves currently active model version for a given task."""
        stmt = select(ModelVersion).where(
            ModelVersion.task_name == task_name,
            ModelVersion.is_active == True,
        )
        return session.scalars(stmt).first()

    @classmethod
    def initialize_default_model_registry(cls, session: Session) -> None:
        """Initializes default baseline models across all required task domains."""
        # 1. Document Classification Baseline
        if not cls.get_active_model(session, "document_classification"):
            cls.register_model_version(
                session=session,
                task_name="document_classification",
                model_name="Heuristic-TFIDF-Classifier",
                version="v1.0.0",
                architecture_description="Rule-weighted TF-IDF heuristic classifier covering English and Bengali SME keywords.",
                feature_schema={
                    "inputs": ["raw_ocr_tokens", "text_length", "keyword_hits", "number_density"],
                    "classes": ["sales_receipt", "purchase_invoice", "expense_receipt", "payment_receipt", "unknown"],
                },
                hyperparameters={"confidence_threshold": 0.85, "bengali_weight_boost": 1.2},
                is_active=True,
            )

        # 2. OCR Extraction Baseline
        if not cls.get_active_model(session, "ocr_extraction"):
            cls.register_model_version(
                session=session,
                task_name="ocr_extraction",
                model_name="RapidOCR-Parser-Pipeline",
                version="v1.0.0",
                architecture_description="ONNX-powered RapidOCR with heuristic regex entity extraction and math cross-validation.",
                feature_schema={
                    "inputs": ["document_image_path", "mime_type"],
                    "outputs": ["invoice_number", "date", "subtotal", "tax", "discount", "total", "line_items"],
                },
                hyperparameters={"det_db_thresh": 0.3, "det_db_box_thresh": 0.5},
                is_active=True,
            )

        # 3. Cash Flow Forecasting Baseline
        if not cls.get_active_model(session, "cashflow_forecast"):
            cls.register_model_version(
                session=session,
                task_name="cashflow_forecast",
                model_name="Holt-Winters-Exponential-Smoothing-Baseline",
                version="v1.0.0",
                architecture_description="Triple Exponential Smoothing (Holt-Winters) statistical baseline with 7-day seasonality.",
                feature_schema={
                    "inputs": ["historical_daily_inflows_minor", "historical_daily_outflows_minor"],
                    "horizon_days": 30,
                    "bounds": [80, 95],
                },
                hyperparameters={"trend": "add", "seasonal": "add", "seasonal_periods": 7},
                is_active=True,
            )

        # 4. Loan Matching & Risk Analysis Baseline
        if not cls.get_active_model(session, "loan_risk"):
            cls.register_model_version(
                session=session,
                task_name="loan_risk",
                model_name="Transparent-Rule-DSCR-Evaluator",
                version="v1.0.0",
                architecture_description="Transparent deterministic rule-based policy engine using DSCR, revenue stability, and debt capacity.",
                feature_schema={
                    "inputs": ["monthly_revenue_minor", "monthly_expenses_minor", "existing_debt_service_minor", "requested_amount_minor", "requested_tenure_months"],
                    "outputs": ["calculated_dscr", "max_allowed_emi_minor", "recommendation_status", "risk_tier"],
                },
                hyperparameters={"min_dscr_healthy": 1.25, "max_emi_to_net_income_ratio": 0.40},
                is_active=True,
            )

        # 5. Customer Segmentation Baseline
        if not cls.get_active_model(session, "customer_segmentation"):
            cls.register_model_version(
                session=session,
                task_name="customer_segmentation",
                model_name="RFM-Rule-Segmenter",
                version="v1.0.0",
                architecture_description="Recency, Frequency, Monetary (RFM) rule-based SME customer segmentation.",
                feature_schema={
                    "inputs": ["days_since_last_purchase", "total_purchase_count", "total_spend_minor"],
                    "segments": ["VIP", "Regular", "Occasional", "At-Risk", "Dormant"],
                },
                hyperparameters={"recency_active_days": 30, "recency_dormant_days": 90},
                is_active=True,
            )

        # 6. Demand & Pricing Baseline
        if not cls.get_active_model(session, "demand_pricing"):
            cls.register_model_version(
                session=session,
                task_name="demand_pricing",
                model_name="Safety-Stock-Reorder-Point-Estimator",
                version="v1.0.0",
                architecture_description="Inventory-aware demand forecasting and optimal reorder point calculator.",
                feature_schema={
                    "inputs": ["daily_sales_mean", "daily_sales_std", "lead_time_days", "service_level_z"],
                    "outputs": ["safety_stock", "reorder_point", "suggested_order_qty"],
                },
                hyperparameters={"service_level": 0.95, "default_lead_time_days": 7},
                is_active=True,
            )
        session.flush()
