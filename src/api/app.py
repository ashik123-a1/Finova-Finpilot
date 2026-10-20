"""
FastAPI Main Application for SME Finance Copilot.
Includes lifespan startup hooks for automated schema migration and model registry initialization.
Configures multi-tenant shop isolation exception handlers, sanitized error responses,
and CORS middleware for local frontend clients.
"""

from __future__ import annotations

import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy import text

from src.config import settings
from src.database.connection import engine, SessionLocal
from src.database.migrations.runner import apply_migrations
from src.ai.registry import ModelRegistry
from src.core.exceptions import (
    CopilotException,
    ShopAccessDeniedError,
    ResourceNotFoundError,
    DocumentProcessingError,
    DuplicateDocumentError,
    FinancialPrecisionError,
    InconsistentFinancialRecordError,
)
from src.api.routes import (
    auth,
    business,
    documents,
    finance,
    datasets,
    models,
    i18n,
    audit,
    notifications,
    admin,
    crm,
    inventory,
    voice,
    reports,
)
from src.web.router import router as web_router, templates, get_web_context

logger = logging.getLogger("sme_finance_copilot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup and shutdown handler."""
    # 1. Run database migrations
    apply_migrations(engine)

    # 2. Initialize default Model Registry baselines
    with SessionLocal() as session:
        ModelRegistry.initialize_default_model_registry(session)
        session.commit()

    yield
    # Shutdown logic (if any)


app = FastAPI(
    title=settings.APP_NAME,
    description="Local-First Database, Synthetic Data & AI Foundation for SME Finance Copilot",
    version="0.1.0",
    lifespan=lifespan,
)

# Enable CORS for local frontends (Vite / Next.js / Flutter web)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enable HTTP GZip Compression for fast network transmission over tunnels and mobile connections
app.add_middleware(GZipMiddleware, minimum_size=500)


# ==============================================================================
# Global Exception Handlers (Clean, Stack-Trace-Free API Error Responses)
# ==============================================================================

@app.exception_handler(ShopAccessDeniedError)
async def shop_access_denied_handler(request: Request, exc: ShopAccessDeniedError):
    logger.warning("Shop access denied: %s (path: %s)", str(exc), request.url.path)
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": "Forbidden",
            "detail": str(exc),
            "error_code": "SHOP_ACCESS_DENIED",
        },
    )


@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "Not Found",
            "detail": str(exc),
            "error_code": "RESOURCE_NOT_FOUND",
        },
    )


@app.exception_handler(DuplicateDocumentError)
async def duplicate_document_handler(request: Request, exc: DuplicateDocumentError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "Conflict",
            "detail": str(exc),
            "error_code": "DUPLICATE_DOCUMENT",
        },
    )


@app.exception_handler(DocumentProcessingError)
async def document_processing_handler(request: Request, exc: DocumentProcessingError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Document Processing Error",
            "detail": str(exc),
            "error_code": "DOCUMENT_PROCESSING_FAILED",
        },
    )


@app.exception_handler(FinancialPrecisionError)
async def financial_precision_handler(request: Request, exc: FinancialPrecisionError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Financial Precision Violation",
            "detail": str(exc),
            "error_code": "PRECISION_VIOLATION",
        },
    )


@app.exception_handler(InconsistentFinancialRecordError)
async def financial_inconsistency_handler(request: Request, exc: InconsistentFinancialRecordError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Inconsistent Financial Record",
            "detail": str(exc),
            "error_code": "INCONSISTENT_FINANCIAL_RECORD",
        },
    )


@app.exception_handler(CopilotException)
async def generic_copilot_exception_handler(request: Request, exc: CopilotException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Bad Request",
            "detail": str(exc),
            "error_code": "COPILOT_DOMAIN_ERROR",
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Log internal error on server without leaking traceback to API consumers
    logger.error("Unhandled internal exception on %s: %s", request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected server error occurred. Please contact the administrator.",
            "error_code": "INTERNAL_SERVER_ERROR",
        },
    )


# ==============================================================================
# Static Files & Web Router Registration
# ==============================================================================

class CachedStaticFiles(StaticFiles):
    """Static file responder with HTTP browser cache headers for instant repeat page loads."""
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if response.status_code == 200:
            response.headers["Cache-Control"] = "public, max-age=604800, stale-while-revalidate=86400"
        return response


STATIC_DIR = Path(__file__).resolve().parent.parent / "web" / "static"
if STATIC_DIR.exists():
    app.mount("/static", CachedStaticFiles(directory=str(STATIC_DIR)), name="static")

# Web UI HTML Router
app.include_router(web_router)


# ==============================================================================
# API Route Module Registration
# ==============================================================================

app.include_router(auth.router, prefix="/api")
app.include_router(business.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(finance.router, prefix="/api")
app.include_router(datasets.router, prefix="/api")
app.include_router(models.router, prefix="/api")
app.include_router(i18n.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(crm.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(voice.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


# ==============================================================================
# Root & Health Endpoints
# ==============================================================================

@app.get("/")
def root(request: Request):
    """
    Root endpoint supporting both browser HTML requests (Landing Page)
    and automated API status checks.
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept and not accept.startswith("*/*"):
        from src.web.router import render_template
        ctx = get_web_context(request, is_landing=True)
        return render_template("landing.html", ctx)
    return {
        "app": settings.APP_NAME,
        "version": "0.1.0",
        "status": "online",
        "docs_url": "/docs",
        "environment": settings.ENVIRONMENT,
    }


def _get_health_status_dict():
    with SessionLocal() as db:
        res = db.execute(text("SELECT 1;")).scalar()
        tables_cnt = db.execute(
            text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        ).scalar()
        active_models_cnt = db.execute(
            text("SELECT COUNT(*) FROM model_versions WHERE is_active=1;")
        ).scalar()

    return {
        "status": "healthy" if res == 1 else "unhealthy",
        "app": settings.APP_NAME,
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
        "database_connected": bool(res == 1),
        "tables_count": tables_cnt,
        "active_models_count": active_models_cnt,
        "currency": settings.DEFAULT_CURRENCY,
        "minor_multiplier": settings.DEFAULT_MINOR_UNIT_MULTIPLIER,
    }


@app.get("/health")
def health_check():
    """Health check endpoint that verifies database connection and subsystem status."""
    return _get_health_status_dict()


@app.get("/api/health")
def api_health_check():
    """API-prefixed health check endpoint for frontend convenience."""
    return _get_health_status_dict()
