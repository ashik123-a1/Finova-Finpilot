"""
Model Registry and AI Evaluation API Routes.
"""

from __future__ import annotations

import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.database.connection import get_db
from src.database.models import ModelVersion, EvaluationRun
from src.ai.registry import ModelRegistry

router = APIRouter(prefix="/models", tags=["Model Registry"])


@router.get("/active")
def list_active_models(db: Session = Depends(get_db)):
    """Lists all active baseline and fine-tuned AI models registered in the copilot."""
    stmt = select(ModelVersion).where(ModelVersion.is_active == True)
    models = db.scalars(stmt).all()
    return [
        {
            "id": m.id,
            "task_name": m.task_name,
            "model_name": m.model_name,
            "version": m.version,
            "architecture": m.architecture_description,
            "feature_schema": json.loads(m.feature_schema_json) if m.feature_schema_json else {},
            "hyperparameters": json.loads(m.hyperparameters_json) if m.hyperparameters_json else {},
        }
        for m in models
    ]


@router.get("/evaluations")
def list_evaluation_runs(db: Session = Depends(get_db)):
    """Lists verified evaluation metrics and benchmarks across models."""
    runs = db.query(EvaluationRun).order_by(EvaluationRun.id.desc()).limit(20).all()
    return [
        {
            "id": r.id,
            "model_version_id": r.model_version_id,
            "dataset_id": r.dataset_id,
            "timestamp": r.run_timestamp.isoformat(),
            "metrics": json.loads(r.metrics_json),
            "is_synthetic_benchmark": r.is_synthetic_benchmark,
            "notes": r.notes,
        }
        for r in runs
    ]
