"""
Dataset Generation and Validation API Routes.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.data.generator import SyntheticDataGenerator
from src.data.validator import DatasetValidator
from src.data.image_tooling import DocumentImageDatasetTooling

router = APIRouter(prefix="/datasets", tags=["Datasets"])


class GenerateDatasetRequest(BaseModel):
    seed: int = 42
    target_records: int = 100000
    reset_first: bool = False


@router.post("/generate")
def generate_synthetic_data(req: GenerateDatasetRequest, db: Session = Depends(get_db)):
    """Triggers generation of the relational synthetic dataset."""
    try:
        gen = SyntheticDataGenerator(seed=req.seed, target_records=req.target_records)
        if req.reset_first:
            gen.reset_synthetic_data(db)
        res = gen.generate_full_dataset()
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
def reset_synthetic_data(db: Session = Depends(get_db)):
    """Safely purges synthetic data without deleting real user or configuration records."""
    try:
        gen = SyntheticDataGenerator()
        deleted = gen.reset_synthetic_data(db)
        return {"status": "success", "deleted_counts": deleted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate")
def validate_dataset():
    """Runs full referential, mathematical, and sector coverage audit."""
    try:
        report = DatasetValidator.run_full_validation()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-images")
def generate_sample_images(count: int = 10):
    """Generates synthetic document images and manifest annotations."""
    try:
        manifest_path = DocumentImageDatasetTooling.generate_sample_collection(count=count)
        return {
            "status": "success",
            "samples_generated": count,
            "manifest_path": str(manifest_path),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
