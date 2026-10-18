import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database.connection import engine, SessionLocal
from src.database.migrations.runner import apply_migrations
from src.ai.registry import ModelRegistry

if __name__ == "__main__":
    print("Applying versioned database migrations...")
    applied = apply_migrations(engine)
    print(f"Migrations applied: {applied if applied else 'Already up to date'}")

    print("Initializing Model Registry baseline records...")
    with SessionLocal() as s:
        ModelRegistry.initialize_default_model_registry(s)
        s.commit()
    print("Database initialization complete.")
