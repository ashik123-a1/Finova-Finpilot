"""
Configuration Module for SME Finance Copilot.
Loads environment variables safely and provides strongly typed settings.
"""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory of the Project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if present
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


class Settings:
    """Application settings with defaults suitable for local development."""

    def __init__(self) -> None:
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        self.APP_NAME: str = os.getenv("APP_NAME", "SME Finance Copilot")
        self.DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

        # Server
        self.HOST: str = os.getenv("HOST", "127.0.0.1")
        self.PORT: int = int(os.getenv("PORT", "8000"))

        # Database
        # Default: SQLite file in the root of the project
        default_db_url = f"sqlite:///{BASE_DIR / 'sme_finance.db'}"
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", default_db_url)
        self.DB_ECHO: bool = os.getenv("DB_ECHO", "false").lower() in ("true", "1", "yes")

        # Security
        self.SECRET_KEY: str = os.getenv(
            "SECRET_KEY", "sme_copilot_dev_secret_key_change_in_production_32bytes_minimum"
        )
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
        )

        # Storage Directories
        self.STORAGE_DIR: Path = BASE_DIR / os.getenv("STORAGE_DIR", "storage")
        self.DOCUMENTS_STORAGE_PATH: Path = (
            BASE_DIR / os.getenv("DOCUMENTS_STORAGE_PATH", "storage/documents")
        )
        self.SYNTHETIC_DATA_PATH: Path = (
            BASE_DIR / os.getenv("SYNTHETIC_DATA_PATH", "storage/synthetic_data")
        )
        self.MODEL_REGISTRY_PATH: Path = (
            BASE_DIR / os.getenv("MODEL_REGISTRY_PATH", "storage/model_registry")
        )

        # Language & Localization Priority (English First, China Second)
        self.DEFAULT_LOCALE: str = os.getenv("DEFAULT_LOCALE", "en")
        self.DEFAULT_COUNTRY: str = os.getenv("DEFAULT_COUNTRY", "CN")

        # Currency & Precision
        self.DEFAULT_CURRENCY: str = os.getenv("DEFAULT_CURRENCY", "BDT")
        self.DEFAULT_MINOR_UNIT_MULTIPLIER: int = int(
            os.getenv("DEFAULT_MINOR_UNIT_MULTIPLIER", "100")
        )  # 100 for BDT/USD (Poisha/Cents)

        # Upload limits (Default: 10 MB)
        self.MAX_UPLOAD_SIZE_BYTES: int = int(
            os.getenv("MAX_UPLOAD_SIZE_BYTES", str(10 * 1024 * 1024))
        )

        # Generative LLM & Copilot Configuration (Configurable Provider: deterministic, openai, ollama, custom)
        self.LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "deterministic").lower()
        self.LLM_API_KEY: str = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
        self.LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self.LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
        self.LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "8.0"))

        # Ensure directories exist
        self.DOCUMENTS_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
        self.SYNTHETIC_DATA_PATH.mkdir(parents=True, exist_ok=True)
        self.MODEL_REGISTRY_PATH.mkdir(parents=True, exist_ok=True)


settings = Settings()
