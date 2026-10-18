"""
FastAPI Main Application for SME Finance Copilot.
Includes lifespan startup hooks for automated schema migration and model registry initialization.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.config import settings
from src.database.connection import engine, SessionLocal
from src.database.migrations.runner import apply_migrations
from src.ai.registry import ModelRegistry
from src.api.routes import auth, documents, finance, datasets, models


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

# Register route modules
app.include_router(auth.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(finance.router, prefix="/api")
app.include_router(datasets.router, prefix="/api")
app.include_router(models.router, prefix="/api")


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": "0.1.0",
        "status": "online",
        "docs_url": "/docs",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health")
def health_check():
    """Health check endpoint that verifies database connection."""
    with SessionLocal() as db:
        res = db.execute(text("SELECT 1;")).scalar()
        tables_cnt = db.execute(
            text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        ).scalar()

    return {
        "status": "healthy" if res == 1 else "unhealthy",
        "database_connected": bool(res == 1),
        "tables_count": tables_cnt,
        "currency": settings.DEFAULT_CURRENCY,
        "minor_multiplier": settings.DEFAULT_MINOR_UNIT_MULTIPLIER,
    }
