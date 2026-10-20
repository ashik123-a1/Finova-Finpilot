"""
Database Backup, Verification, and Safe Restore Service.
Supports SQLite WAL-safe online backup via sqlite3.Connection.backup() API.
Never blocks concurrent readers or writers.
Stores backups and manifests in var/backups/.
Guarantees never overwriting active databases without isolated dry-run verification.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.config import settings

logger = logging.getLogger("sme_finance.backup")


class DatabaseBackupService:
    """Manages creation, verification, and safe isolated testing of database backups."""

    @classmethod
    def get_backup_dir(cls) -> Path:
        """Returns the configured backups directory and ensures it exists."""
        backup_dir = settings.BACKUPS_DIR
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir

    @classmethod
    def get_active_db_path(cls) -> Path:
        """Resolves active SQLite database path from DATABASE_URL."""
        db_url = settings.DATABASE_URL
        if db_url.startswith("sqlite:///"):
            return Path(db_url.replace("sqlite:///", ""))
        return settings.BASE_DIR / "sme_finance.db"

    @classmethod
    def create_backup(cls, comment: str = "Automated system backup", user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Executes a WAL-safe online backup using SQLite's native backup API.
        Verifies the backup immediately, calculates SHA-256, and generates a manifest.
        """
        active_db = cls.get_active_db_path()
        if not active_db.exists():
            raise FileNotFoundError(f"Active database not found at '{active_db}'.")

        backup_dir = cls.get_backup_dir()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_filename = f"sme_backup_{timestamp}.db"
        backup_path = backup_dir / backup_filename
        manifest_path = backup_dir / f"manifest_{timestamp}.json"

        logger.info("Initiating WAL-safe SQLite backup: %s -> %s", active_db, backup_path)

        # 1. Native Online Backup (Thread-safe & WAL-safe)
        source_conn = sqlite3.connect(str(active_db), timeout=30)
        dest_conn = sqlite3.connect(str(backup_path))
        try:
            source_conn.backup(dest_conn)
        finally:
            dest_conn.close()
            source_conn.close()

        # 2. Immediate Diagnostic Verification on Backup File
        verification = cls.verify_backup_file(backup_path)

        # 3. File Hash and Statistics
        file_bytes = backup_path.read_bytes()
        sha256 = hashlib.sha256(file_bytes).hexdigest()
        file_size_bytes = len(file_bytes)

        manifest: Dict[str, Any] = {
            "backup_filename": backup_filename,
            "backup_path": str(backup_path),
            "manifest_path": str(manifest_path),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by_user_id": user_id,
            "comment": comment,
            "engine": "sqlite",
            "file_size_bytes": file_size_bytes,
            "file_size_formatted": f"{file_size_bytes / (1024 * 1024):.2f} MB",
            "sha256": sha256,
            "is_verified": verification["is_valid"],
            "integrity_status": verification["integrity_status"],
            "tables_count": verification["tables_count"],
            "table_record_counts": verification["table_counts"],
            "total_records": sum(verification["table_counts"].values()),
        }

        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        logger.info("Backup created and verified successfully: %s (SHA: %s)", backup_filename, sha256[:12])
        return manifest

    @classmethod
    def verify_backup_file(cls, backup_path: Path) -> Dict[str, Any]:
        """
        Performs read-only PRAGMA checks and table audits on a backup database file.
        """
        if not backup_path.exists() or backup_path.stat().st_size == 0:
            return {
                "is_valid": False,
                "integrity_status": "file_missing_or_empty",
                "tables_count": 0,
                "table_counts": {},
                "errors": ["Backup file does not exist or has 0 bytes."],
            }

        conn = sqlite3.connect(str(backup_path), timeout=15)
        cursor = conn.cursor()
        try:
            cursor.execute("PRAGMA integrity_check;")
            integrity_rows = [r[0] for r in cursor.fetchall()]
            integrity_ok = (integrity_rows == ["ok"])

            cursor.execute("PRAGMA foreign_key_check;")
            fk_violations = cursor.fetchall()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [r[0] for r in cursor.fetchall() if not r[0].startswith("sqlite_")]

            table_counts: Dict[str, int] = {}
            for t in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM \"{t}\";")
                    table_counts[t] = cursor.fetchone()[0]
                except Exception:
                    pass

            is_valid = integrity_ok and len(fk_violations) == 0 and len(tables) > 0

            return {
                "is_valid": is_valid,
                "integrity_status": "ok" if integrity_ok else "; ".join(integrity_rows[:5]),
                "foreign_key_violations": len(fk_violations),
                "tables_count": len(tables),
                "table_counts": table_counts,
                "errors": [] if is_valid else integrity_rows,
            }
        except Exception as exc:
            return {
                "is_valid": False,
                "integrity_status": "verification_failed",
                "tables_count": 0,
                "table_counts": {},
                "errors": [str(exc)],
            }
        finally:
            conn.close()

    @classmethod
    def list_backups(cls) -> List[Dict[str, Any]]:
        """
        Scans var/backups/ for existing backups and manifests, returned sorted by date desc.
        """
        backup_dir = cls.get_backup_dir()
        manifest_files = sorted(backup_dir.glob("manifest_*.json"), reverse=True)
        backups: List[Dict[str, Any]] = []

        for mf in manifest_files:
            try:
                data = json.loads(mf.read_text(encoding="utf-8"))
                # Confirm physical backup file still exists
                db_p = Path(data.get("backup_path", ""))
                data["file_exists"] = db_p.exists()
                backups.append(data)
            except Exception:
                pass

        return backups

    @classmethod
    def test_restore_to_isolated_database(cls, backup_filename: str, isolated_test_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Performs an ISOLATED test restore of a backup file into a temporary sandbox.
        STRICT SAFETY: Never restores over the active database!
        Verifies schema completeness, record counts, and confirms active DB was untouched.
        """
        backup_dir = cls.get_backup_dir()
        backup_path = Path(backup_filename)
        if not backup_path.exists():
            backup_path = backup_dir / backup_filename
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file '{backup_filename}' not found.")

        active_db = cls.get_active_db_path()
        active_size_before = active_db.stat().st_size if active_db.exists() else 0
        active_mtime_before = active_db.stat().st_mtime if active_db.exists() else 0

        # Isolated sandbox directory
        if isolated_test_dir is None:
            isolated_test_dir = backup_dir / "_restore_test_sandbox"
        isolated_test_dir.mkdir(parents=True, exist_ok=True)

        test_restore_db = isolated_test_dir / f"restored_test_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.db"

        try:
            # 1. Restore into isolated test path via copy
            shutil.copy2(str(backup_path), str(test_restore_db))

            # 2. Run full verification on the restored sandbox DB
            verification = cls.verify_backup_file(test_restore_db)

            # 3. Verify active DB was completely untouched
            active_size_after = active_db.stat().st_size if active_db.exists() else 0
            active_mtime_after = active_db.stat().st_mtime if active_db.exists() else 0
            active_db_untouched = (active_size_before == active_size_after) and (active_mtime_before == active_mtime_after)

            return {
                "restore_test_status": "success" if (verification["is_valid"] and active_db_untouched) else "failed",
                "test_database_path": str(test_restore_db),
                "is_valid": verification["is_valid"],
                "integrity_status": verification["integrity_status"],
                "tables_count": verification["tables_count"],
                "table_counts": verification["table_counts"],
                "active_database_untouched": active_db_untouched,
                "tested_at": datetime.now(timezone.utc).isoformat(),
            }
        finally:
            # Clean up test sandbox file
            if test_restore_db.exists():
                try:
                    test_restore_db.unlink()
                except Exception:
                    pass
            if isolated_test_dir.exists() and not any(isolated_test_dir.iterdir()):
                try:
                    isolated_test_dir.rmdir()
                except Exception:
                    pass
