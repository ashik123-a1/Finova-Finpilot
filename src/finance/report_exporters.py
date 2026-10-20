"""
Report Exporters for SME Finance Copilot.
Generates production-grade CSV files with Formula Injection Mitigation (Excel/Sheets safe)
and formal ReportLab PDF reports with KPI metric summaries, striped tables, and disclaimers.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Dict, Any, List

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)


class CsvReportExporter:
    """Exports structured report payloads to secure, Excel-compatible CSV files."""

    FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

    @classmethod
    def sanitize_cell(cls, val: Any) -> str:
        """
        Mitigates CSV Formula Injection (DDE attacks).
        Prepends a single quote if string begins with =, +, -, @, tab, or carriage return.
        """
        if val is None:
            return ""
        s = str(val)
        if s and s.startswith(cls.FORMULA_PREFIXES):
            # Prepend single quote to force spreadsheet programs to treat as text
            return f"'{s}"
        return s

    @classmethod
    def export(cls, report_data: Dict[str, Any]) -> bytes:
        """
        Generates UTF-8-SIG encoded CSV bytes with complete report metadata and sanitized rows.
        UTF-8-SIG includes BOM (\ufeff) ensuring Excel natively displays Bengali and Chinese text.
        """
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # 1. Metadata Header Block
        title = report_data.get("title", "Business Report")
        biz_name = report_data.get("business_name", "SME Workspace")
        shop_name = report_data.get("shop_name", "All Shops")
        currency = report_data.get("currency", "BDT")
        start_date = report_data.get("start_date", "")
        end_date = report_data.get("end_date", "")
        gen_time = report_data.get("generated_at_formatted", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
        report_uuid = report_data.get("report_uuid", "")

        writer.writerow(["# FINOVA FINPILOT — AUTONOMOUS FINANCIAL REPORT"])
        writer.writerow(["# Report Title", title])
        writer.writerow(["# Business Name", biz_name])
        writer.writerow(["# Shop / Branch", shop_name])
        writer.writerow(["# Reporting Period", f"{start_date} to {end_date}"])
        writer.writerow(["# Base Currency", currency])
        writer.writerow(["# Generated At", gen_time])
        writer.writerow(["# Reference UUID", report_uuid])

        # Summary KPIs if available
        kpis = report_data.get("summary_kpis", [])
        if kpis:
            kpi_strs = [f"{k['label']}: {k['value']}" for k in kpis]
            writer.writerow(["# Summary KPIs", " | ".join(kpi_strs)])

        disclaimer = report_data.get("disclaimer", "")
        if disclaimer:
            writer.writerow(["# Compliance Note", disclaimer])

        # Empty spacer row
        writer.writerow([])

        # 2. Main Data Table Column Headers
        columns = report_data.get("columns", [])
        writer.writerow([cls.sanitize_cell(c) for c in columns])

        # 3. Main Data Rows
        rows = report_data.get("rows", [])
        for row in rows:
            writer.writerow([cls.sanitize_cell(cell) for cell in row])

        # Return as UTF-8 with BOM
        return output.getvalue().encode("utf-8-sig")


class PdfReportExporter:
    """Renders professional PDF dossiers using ReportLab with clean typography and layout."""

    @classmethod
    def export(cls, report_data: Dict[str, Any]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            leftMargin=30,
            rightMargin=30,
            topMargin=30,
            bottomMargin=30,
        )

        styles = getSampleStyleSheet()

        # Custom Typography
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=colors.HexColor("#0891b2"),  # Cyan-700
            spaceAfter=2,
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#475569"),
            spaceAfter=6,
        )
        meta_label = ParagraphStyle(
            "MetaLabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#1e293b"),
        )
        meta_val = ParagraphStyle(
            "MetaVal",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#0f172a"),
        )
        kpi_label = ParagraphStyle(
            "KpiLabel",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#64748b"),
            alignment=1,
        )
        kpi_val = ParagraphStyle(
            "KpiVal",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0891b2"),
            alignment=1,
        )
        table_hdr = ParagraphStyle(
            "TableHdr",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor("#ffffff"),
            alignment=0,
        )
        table_cell = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#0f172a"),
            alignment=0,
        )
        disclaimer_style = ParagraphStyle(
            "Disclaimer",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#b45309"),
            alignment=0,
        )

        story = []

        # 1. Header Banner
        title = report_data.get("title", "Financial & Operational Report")
        subtitle = report_data.get("subtitle", "Autonomous Intelligence Dossier")
        biz_name = report_data.get("business_name", "SME Workspace")
        shop_name = report_data.get("shop_name", "All Shops")
        currency = report_data.get("currency", "BDT")
        start_date = report_data.get("start_date", "")
        end_date = report_data.get("end_date", "")
        gen_time = report_data.get("generated_at_formatted", datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC"))
        report_uuid = report_data.get("report_uuid", "")

        header_data = [
            [
                Paragraph(f"<b>FINOVA FINPILOT</b> — {title.upper()}", title_style),
                Paragraph(f"<b>Ref ID:</b> {report_uuid}", ParagraphStyle("RightHdr", parent=meta_label, alignment=2)),
            ],
            [
                Paragraph(subtitle, subtitle_style),
                Paragraph(f"<b>Generated:</b> {gen_time}", ParagraphStyle("RightHdr2", parent=meta_val, alignment=2)),
            ],
        ]
        hdr_table = Table(header_data, colWidths=[520, 210])
        hdr_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(hdr_table)

        # Meta Context Line
        meta_line = [
            [
                Paragraph(f"<b>Workspace:</b> {biz_name}", meta_val),
                Paragraph(f"<b>Shop:</b> {shop_name}", meta_val),
                Paragraph(f"<b>Period:</b> {start_date} to {end_date}", meta_val),
                Paragraph(f"<b>Currency:</b> {currency}", meta_val),
            ]
        ]
        meta_table = Table(meta_line, colWidths=[200, 200, 200, 130])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 8))

        # 2. Key Metrics Summary Grid (KPIs)
        kpis = report_data.get("summary_kpis", [])
        if kpis:
            kpi_cols = min(len(kpis), 4)
            col_w = 730 / kpi_cols
            kpi_row = []
            for kpi in kpis[:4]:
                cell_content = [
                    Paragraph(kpi.get("label", "").upper(), kpi_label),
                    Paragraph(f"<b>{kpi.get('value', '')}</b>", kpi_val),
                ]
                kpi_row.append(cell_content)
            kpi_table = Table([kpi_row], colWidths=[col_w] * kpi_cols)
            kpi_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#0891b2")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]))
            story.append(kpi_table)
            story.append(Spacer(1, 8))

        # 3. Main Data Table
        columns = report_data.get("columns", [])
        rows = report_data.get("rows", [])
        if columns and rows:
            num_cols = len(columns)
            col_width = 730 / num_cols

            table_data = []
            # Header Row
            hdr_row = [Paragraph(f"<b>{col}</b>", table_hdr) for col in columns]
            table_data.append(hdr_row)

            # Data Rows (limit to first 120 rows for PDF layout compactness)
            for r_idx, row in enumerate(rows[:120]):
                data_row = []
                for cell in row:
                    data_row.append(Paragraph(str(cell), table_cell))
                table_data.append(data_row)

            main_table = Table(table_data, colWidths=[col_width] * num_cols, repeatRows=1)
            t_style = [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),  # Dark slate header
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("PADDING", (0, 0), (-1, -1), 3),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
            # Striped alternating row backgrounds
            for i in range(1, len(table_data)):
                bg = colors.HexColor("#ffffff") if i % 2 == 1 else colors.HexColor("#f8fafc")
                t_style.append(("BACKGROUND", (0, i), (-1, i), bg))

            main_table.setStyle(TableStyle(t_style))
            story.append(main_table)

        # 4. Disclaimer and Footer
        disclaimer = report_data.get("disclaimer", "")
        if disclaimer:
            story.append(Spacer(1, 8))
            disc_table = Table([[Paragraph(f"<b>NOTE:</b> {disclaimer}", disclaimer_style)]], colWidths=[730])
            disc_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef3c7")),
                ("PADDING", (0, 0), (-1, -1), 4),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#f59e0b")),
            ]))
            story.append(disc_table)

        doc.build(story)
        return buffer.getvalue()
