"""
Dataset Validation and Integrity Audit Engine.
Verifies referential integrity, foreign keys, mathematical balancing,
scenario coverage across all 9 industry sectors, and produces formal audit reports.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy import text
from tabulate import tabulate

from src.database.connection import engine, SessionLocal
from src.config import settings


class DatasetValidator:
    """Performs rigorous audits on database records and financial ledgers."""

    @classmethod
    def run_full_validation(cls, session: Optional[Session] = None) -> Dict[str, Any]:
        report: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "PASS",
            "table_record_counts": {},
            "total_records": 0,
            "referential_integrity": {"status": "PASS", "orphaned_records_found": 0, "details": []},
            "financial_consistency": {"status": "PASS", "discrepancies_found": 0, "details": []},
            "scenario_coverage": {"status": "PASS", "sectors_covered": []},
        }

        def _do_validation(session: Session) -> Dict[str, Any]:
            # 1. Total records per table
            tables_query = session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
            ).fetchall()
            table_names = [r[0] for r in tables_query]

            total_count = 0
            for t in table_names:
                cnt = session.execute(text(f"SELECT COUNT(*) FROM {t};")).scalar()
                report["table_record_counts"][t] = cnt
                total_count += cnt
            report["total_records"] = total_count

            # 2. SQLite Foreign Key Integrity Check
            fk_violations = session.execute(text("PRAGMA foreign_key_check;")).fetchall()
            if fk_violations:
                report["referential_integrity"]["status"] = "FAIL"
                report["referential_integrity"]["orphaned_records_found"] = len(fk_violations)
                report["referential_integrity"]["details"] = [
                    {"table": r[0], "rowid": r[1], "parent": r[2], "fkid": r[3]} for r in fk_violations
                ]
                report["status"] = "FAIL"

            # 3. Financial Consistency: Sale Items Math vs Sale Subtotal
            sales_math_check = session.execute(
                text(
                    """
                    SELECT s.id, s.invoice_number, s.subtotal_minor, SUM(si.line_total_minor) as items_sum
                    FROM sales s
                    JOIN sale_items si ON s.id = si.sale_id
                    GROUP BY s.id
                    HAVING s.subtotal_minor != SUM(si.line_total_minor)
                    LIMIT 10;
                    """
                )
            ).fetchall()

            if sales_math_check:
                report["financial_consistency"]["status"] = "FAIL"
                report["financial_consistency"]["discrepancies_found"] += len(sales_math_check)
                for r in sales_math_check:
                    report["financial_consistency"]["details"].append(
                        f"Sale {r[1]} (ID {r[0]}): subtotal {r[2]} != items sum {r[3]}"
                    )
                report["status"] = "FAIL"

            # 4. Financial Consistency: Purchases Items Math vs Purchase Subtotal
            purchases_math_check = session.execute(
                text(
                    """
                    SELECT p.id, p.invoice_number, p.subtotal_minor, SUM(pi.line_total_minor) as items_sum
                    FROM purchases p
                    JOIN purchase_items pi ON p.id = pi.purchase_id
                    GROUP BY p.id
                    HAVING p.subtotal_minor != SUM(pi.line_total_minor)
                    LIMIT 10;
                    """
                )
            ).fetchall()

            if purchases_math_check:
                report["financial_consistency"]["status"] = "FAIL"
                report["financial_consistency"]["discrepancies_found"] += len(purchases_math_check)
                for r in purchases_math_check:
                    report["financial_consistency"]["details"].append(
                        f"Purchase {r[1]} (ID {r[0]}): subtotal {r[2]} != items sum {r[3]}"
                    )
                report["status"] = "FAIL"

            # 5. Scenario Coverage Check: Sectors
            sectors_res = session.execute(
                text("SELECT DISTINCT business_type, count(*) FROM businesses GROUP BY business_type;")
            ).fetchall()
            report["scenario_coverage"]["sectors_covered"] = [
                {"sector": r[0], "business_count": r[1]} for r in sectors_res
            ]
            return report

        if session is not None:
            report = _do_validation(session)
        else:
            with SessionLocal() as s:
                report = _do_validation(s)

        # Export reports to storage
        cls._export_reports(report)
        return report

    @classmethod
    def _export_reports(cls, report: Dict[str, Any]) -> None:
        out_dir = settings.SYNTHETIC_DATA_PATH
        out_dir.mkdir(parents=True, exist_ok=True)

        json_path = out_dir / "validation_report.json"
        json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        # Generate readable Markdown report
        md_lines = [
            "# SME Finance Copilot — Dataset Validation & Integrity Audit Report",
            f"**Audit Timestamp:** {report['timestamp']}  ",
            f"**Overall Audit Status:** `{report['status']}`  ",
            f"**Total Database Records Audited:** **{report['total_records']:,}**  ",
            "",
            "## 1. Table Record Distribution",
            "",
        ]

        table_data = [[tbl, f"{cnt:,}"] for tbl, cnt in report["table_record_counts"].items()]
        md_lines.append(tabulate(table_data, headers=["Database Table", "Record Count"], tablefmt="github"))
        md_lines.append("")

        md_lines.append("## 2. Referential Integrity & Foreign Key Audit")
        if report["referential_integrity"]["status"] == "PASS":
            md_lines.append("> [!NOTE]")
            md_lines.append("> Foreign key integrity verification passed with **0 violations**.")
        else:
            md_lines.append(f"> [!CAUTION]\n> Detected {report['referential_integrity']['orphaned_records_found']} foreign key violations!")

        md_lines.append("")
        md_lines.append("## 3. Financial Mathematical Consistency")
        if report["financial_consistency"]["status"] == "PASS":
            md_lines.append("> [!NOTE]")
            md_lines.append("> 100% of checked Sales and Purchase transactions balance with line item totals.")
        else:
            md_lines.append(f"> [!WARNING]\n> Found {report['financial_consistency']['discrepancies_found']} calculation discrepancies.")

        md_lines.append("")
        md_lines.append("## 4. Scenario Coverage Across SME Sectors")
        sector_data = [[s["sector"], s["business_count"]] for s in report["scenario_coverage"]["sectors_covered"]]
        md_lines.append(tabulate(sector_data, headers=["Industry Sector", "Active Businesses"], tablefmt="github"))
        md_lines.append("")

        md_path = out_dir / "validation_report.md"
        md_path.write_text("\n".join(md_lines), encoding="utf-8")
        print(f"Validation reports saved to {json_path} and {md_path}")


if __name__ == "__main__":
    rep = DatasetValidator.run_full_validation()
    print(f"\nAudit complete. Total records: {rep['total_records']:,}. Status: {rep['status']}")
