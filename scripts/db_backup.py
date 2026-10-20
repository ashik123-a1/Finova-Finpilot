#!/usr/bin/env python3
"""
Database Backup CLI Utility for SME Finance Copilot.
Usage:
    python scripts/db_backup.py --backup [--comment "Manual backup"]
    python scripts/db_backup.py --list
    python scripts/db_backup.py --verify <backup_filename>
    python scripts/db_backup.py --test-restore <backup_filename>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.database.backup_service import DatabaseBackupService


def main() -> None:
    parser = argparse.ArgumentParser(description="SME Finance Copilot Database Backup Utility")
    parser.add_argument("--backup", action="store_true", help="Create a new WAL-safe SQLite backup")
    parser.add_argument("--comment", type=str, default="CLI manual backup", help="Comment for backup manifest")
    parser.add_argument("--list", action="store_true", help="List all available backups")
    parser.add_argument("--verify", type=str, help="Verify a specific backup file in var/backups/")
    parser.add_argument("--test-restore", type=str, help="Test restore a backup into an isolated sandbox")

    args = parser.parse_args()

    if args.backup:
        print("[*] Initiating WAL-safe database backup...")
        try:
            manifest = DatabaseBackupService.create_backup(comment=args.comment)
            print(f"[+] Backup successfully created:")
            print(f"    File:     {manifest['backup_filename']}")
            print(f"    Size:     {manifest['file_size_formatted']}")
            print(f"    SHA256:   {manifest['sha256']}")
            print(f"    Status:   {manifest['integrity_status']}")
            print(f"    Tables:   {manifest['tables_count']} tables, {manifest['total_records']} total records")
            sys.exit(0)
        except Exception as e:
            print(f"[-] Backup failed: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.list:
        backups = DatabaseBackupService.list_backups()
        if not backups:
            print("[*] No backups found in var/backups/.")
            sys.exit(0)
        print(f"[*] Found {len(backups)} backups:")
        for b in backups:
            status = "VALID" if b.get("is_verified") else "INVALID"
            print(f"  - {b.get('backup_filename')} | {b.get('created_at')} | {b.get('file_size_formatted')} | [{status}]")
        sys.exit(0)

    elif args.verify:
        backup_path = DatabaseBackupService.get_backup_dir() / args.verify
        print(f"[*] Verifying {backup_path.name}...")
        res = DatabaseBackupService.verify_backup_file(backup_path)
        if res["is_valid"]:
            print(f"[+] Backup is VALID. {res['tables_count']} tables, integrity: {res['integrity_status']}")
            sys.exit(0)
        else:
            print(f"[-] Backup verification FAILED: {res.get('errors')}", file=sys.stderr)
            sys.exit(1)

    elif args.test_restore:
        print(f"[*] Testing isolated restore of {args.test_restore}...")
        try:
            res = DatabaseBackupService.test_restore_to_isolated_database(args.test_restore)
            if res["restore_test_status"] == "success":
                print(f"[+] Isolated restore test SUCCESSFUL!")
                print(f"    Verified {res['tables_count']} tables.")
                print(f"    Active database remained strictly untouched: {res['active_database_untouched']}")
                sys.exit(0)
            else:
                print(f"[-] Isolated restore test FAILED.", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            print(f"[-] Isolated restore error: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
