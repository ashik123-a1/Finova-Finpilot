"""
Reports and Data Export API Router for SME Finance Copilot.
Provides authorized access to business intelligence reports, formula-safe CSV downloads,
professional ReportLab PDF dossiers, persistent report execution history,
authentic database PRAGMA integrity checks, and WAL-safe database backup operations.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.database.connection import get_db
from src.database.models import User, Business, Shop, BusinessMembership, ReportExecution
from src.api.dependencies import get_current_user, verify_shop_access_dependency
from src.finance.reports_service import ReportsService
from src.finance.report_exporters import CsvReportExporter, PdfReportExporter
from src.database.integrity import DatabaseIntegrityService
from src.database.backup_service import DatabaseBackupService
from src.config import settings

router = APIRouter(prefix="/reports", tags=["Reports & Data Exports"])


# ==============================================================================
# Request Models
# ==============================================================================

class ReportGenerateRequest(BaseModel):
    report_type: str = Field(..., description="Report catalog ID (e.g. income_expense, profit_loss, ledger)")
    shop_id: Optional[int] = Field(None, description="Optional shop ID. Omit for entire business workspace")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")


class BackupCreateRequest(BaseModel):
    comment: str = Field("Manual backup from Report Center", description="Audit note for backup manifest")


class BackupVerifyRequest(BaseModel):
    backup_filename: str = Field(..., description="Backup filename in var/backups/")


def _resolve_user_workspace(user: User, db: Session, requested_shop_id: Optional[int] = None) -> tuple[int, Optional[int]]:
    """
    Resolves authorized business_id and verifies shop_id access.
    Guarantees strict multi-tenant isolation.
    """
    if requested_shop_id is not None:
        verify_shop_access_dependency(shop_id=requested_shop_id, user=user, db=db)
        shop = db.get(Shop, requested_shop_id)
        if not shop:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requested shop not found.")
        return shop.business_id, shop.id

    # Fallback to user's primary business membership
    membership = (
        db.query(BusinessMembership)
        .filter(BusinessMembership.user_id == user.id, BusinessMembership.is_active == True)
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to any active business workspace.",
        )

    return membership.business_id, membership.shop_id


# ==============================================================================
# Endpoints
# ==============================================================================

@router.get("/types")
def get_report_types():
    """Returns the catalog of all available report types and categories."""
    return {"catalog": ReportsService.get_catalog()}


@router.post("/preview")
def generate_report_preview(
    req: ReportGenerateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generates report data, summary KPIs, and tabular rows for live UI preview.
    Records report execution metadata in the database.
    """
    biz_id, authorized_shop_id = _resolve_user_workspace(user, db, req.shop_id)
    try:
        report = ReportsService.generate_report(
            session=db,
            report_type=req.report_type,
            business_id=biz_id,
            shop_id=authorized_shop_id,
            start_date=req.start_date,
            end_date=req.end_date,
            user_id=user.id,
            save_execution=True,
            report_format="preview",
        )
        return report
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Report generation error: {exc}")


@router.post("/export/csv")
def export_report_csv(
    req: ReportGenerateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generates report and streams formula-safe, UTF-8-SIG encoded CSV bytes.
    Mitigates spreadsheet injection (DDE attacks) and ensures native Bengali/Chinese rendering in Excel.
    """
    biz_id, authorized_shop_id = _resolve_user_workspace(user, db, req.shop_id)
    try:
        report = ReportsService.generate_report(
            session=db,
            report_type=req.report_type,
            business_id=biz_id,
            shop_id=authorized_shop_id,
            start_date=req.start_date,
            end_date=req.end_date,
            user_id=user.id,
            save_execution=True,
            report_format="csv",
        )
        csv_bytes = CsvReportExporter.export(report)

        # Store a durable local copy in var/exports/{business_id}/
        try:
            export_dir = settings.EXPORTS_DIR / str(biz_id)
            export_dir.mkdir(parents=True, exist_ok=True)
            export_file = export_dir / f"{report['report_uuid']}.csv"
            export_file.write_bytes(csv_bytes)
        except Exception:
            pass

        filename = f"{req.report_type}_{report['start_date']}_to_{report['end_date']}.csv"
        return Response(
            content=csv_bytes,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Report-UUID": report["report_uuid"],
            },
        )
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"CSV export error: {exc}")


@router.post("/export/pdf")
def export_report_pdf(
    req: ReportGenerateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generates formal institutional PDF report using ReportLab.
    Includes business context, key metrics summary grid, styled tabular data, and compliance disclaimers.
    """
    biz_id, authorized_shop_id = _resolve_user_workspace(user, db, req.shop_id)
    try:
        report = ReportsService.generate_report(
            session=db,
            report_type=req.report_type,
            business_id=biz_id,
            shop_id=authorized_shop_id,
            start_date=req.start_date,
            end_date=req.end_date,
            user_id=user.id,
            save_execution=True,
            report_format="pdf",
        )
        pdf_bytes = PdfReportExporter.export(report)

        # Store a durable local copy in var/exports/{business_id}/
        try:
            export_dir = settings.EXPORTS_DIR / str(biz_id)
            export_dir.mkdir(parents=True, exist_ok=True)
            export_file = export_dir / f"{report['report_uuid']}.pdf"
            export_file.write_bytes(pdf_bytes)
        except Exception:
            pass

        filename = f"{req.report_type}_{report['start_date']}_to_{report['end_date']}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Report-UUID": report["report_uuid"],
            },
        )
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"PDF export error: {exc}")


@router.get("/history")
def get_report_history(
    limit: int = Query(25, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves recent report execution records for the authenticated workspace."""
    biz_id, _ = _resolve_user_workspace(user, db, None)
    records = (
        db.query(ReportExecution)
        .filter(ReportExecution.business_id == biz_id)
        .order_by(ReportExecution.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "history": [
            {
                "report_uuid": r.report_uuid,
                "report_type": r.report_type,
                "shop_id": r.shop_id,
                "format": r.format,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "file_size_bytes": r.file_size_bytes,
                "filters": r.filters_json,
                "summary": r.summary_metrics_json,
            }
            for r in records
        ]
    }


@router.get("/integrity")
def get_database_integrity(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Executes real SQLite PRAGMA system diagnostics.
    Never fabricates 100% health; returns true engine status.
    """
    return DatabaseIntegrityService.run_integrity_check(db)


# ==============================================================================
# Safe Backup Endpoints
# ==============================================================================

@router.get("/backups")
def list_database_backups(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists existing database backups and verification status."""
    return {"backups": DatabaseBackupService.list_backups()}


@router.post("/backups/create")
def create_database_backup(
    req: BackupCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Triggers a WAL-safe online backup of the active database.
    Verifies B-tree integrity and writes an immutable metadata manifest.
    """
    try:
        manifest = DatabaseBackupService.create_backup(comment=req.comment, user_id=user.id)
        return {"status": "success", "manifest": manifest}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Backup failed: {exc}")


@router.post("/backups/verify")
def verify_backup(
    req: BackupVerifyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Performs PRAGMA integrity verification on a specific backup file."""
    backup_path = DatabaseBackupService.get_backup_dir() / req.backup_filename
    if not backup_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup file not found.")
    result = DatabaseBackupService.verify_backup_file(backup_path)
    return {"status": "verified" if result["is_valid"] else "invalid", "details": result}


@router.post("/backups/test-restore")
def test_isolated_restore(
    req: BackupVerifyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Executes an ISOLATED test restore in a temporary sandbox.
    Guarantees the active database is never touched or overwritten.
    """
    try:
        result = DatabaseBackupService.test_restore_to_isolated_database(req.backup_filename)
        return result
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Restore test failed: {exc}")
