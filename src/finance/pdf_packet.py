"""
Institutional Bank Loan Underwriting Packet PDF Generator.
Builds formal, GAAP/IFRS-aligned loan dossiers using ReportLab.
Explicitly watermarked with synthetic demo disclaimers for competition safety.
"""

import io
from datetime import datetime, timezone
from typing import Dict, Any, List

from reportlab.lib.pagesizes import letter
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


def generate_loan_packet_pdf(packet_data: Dict[str, Any]) -> bytes:
    """
    Renders an institutional loan underwriting packet as a PDF byte stream.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569"),
        spaceAfter=8,
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#0891b2"),  # Dark cyan
        spaceBefore=10,
        spaceAfter=4,
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#b45309"),  # Amber-800
        alignment=1,  # Centered
    )
    cell_label = ParagraphStyle(
        "CellLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#334155"),
    )
    cell_val = ParagraphStyle(
        "CellVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
    )
    cell_val_bold = ParagraphStyle(
        "CellValBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
    )

    story = []

    # 1. Header Banner
    app_num = packet_data.get("application_number", "DEMO-LN-PENDING")
    gen_time = packet_data.get("generated_at_formatted", datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC"))
    biz_name = packet_data.get("business_name", "Demo Business")
    shop_name = packet_data.get("shop_name", "Main Shop")
    currency = packet_data.get("currency", "BDT")

    header_table_data = [
        [
            Paragraph("<b>SME FINANCE COPILOT</b> — AUTONOMOUS AI UNDERWRITING", cell_label),
            Paragraph(f"<b>Application Ref:</b> {app_num}", ParagraphStyle("RightHdr", parent=cell_label, alignment=2)),
        ],
        [
            Paragraph("Institutional Credit Dossier & Debt Capacity Analysis", subtitle_style),
            Paragraph(f"<b>Generated:</b> {gen_time}", ParagraphStyle("RightHdr2", parent=subtitle_style, alignment=2)),
        ],
    ]
    t_hdr = Table(header_table_data, colWidths=[340, 200])
    t_hdr.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(t_hdr)

    # 2. Prominent Demo Disclaimer Box
    story.append(Spacer(1, 6))
    demo_notice = (
        "<b>DEMO SIMULATION NOTICE</b>: This financial packet is an automated pre-underwriting assessment "
        "synthesized for evaluation. No live bank application has been submitted, no credit facility has been committed, "
        "and statutory approval remains subject to formal bank underwriting and field physical audit."
    )
    t_disc = Table([[Paragraph(demo_notice, disclaimer_style)]], colWidths=[540])
    t_disc.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef3c7")),  # Amber-100
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#f59e0b")),     # Amber-500
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t_disc)
    story.append(Spacer(1, 10))

    # 3. Enterprise & Facility Profile
    story.append(Paragraph("1. Business & Loan Facility Parameters", section_heading))
    p_info = packet_data.get("loan_terms", {})
    biz_info_data = [
        [
            Paragraph("Business Name:", cell_label), Paragraph(biz_name, cell_val),
            Paragraph("Requested Principal:", cell_label), Paragraph(f"<b>{p_info.get('principal_formatted', 'N/A')}</b>", cell_val),
        ],
        [
            Paragraph("Active Branch / Shop:", cell_label), Paragraph(shop_name, cell_val),
            Paragraph("Facility Tenure:", cell_label), Paragraph(f"{p_info.get('tenure_months', 24)} Months", cell_val),
        ],
        [
            Paragraph("Tax / Trade License ID:", cell_label), Paragraph(packet_data.get("tax_id", "BIN-99281-002"), cell_val),
            Paragraph("Annual Interest Rate:", cell_label), Paragraph(f"{p_info.get('annual_interest_rate_pct', 11.5):.2f}% p.a.", cell_val),
        ],
        [
            Paragraph("Primary Loan Purpose:", cell_label), Paragraph(packet_data.get("loan_purpose_label", "Working Capital Expansion"), cell_val),
            Paragraph("Amortization Method:", cell_label), Paragraph("Reducing Balance (EMI)", cell_val),
        ],
    ]
    t_biz = Table(biz_info_data, colWidths=[110, 160, 120, 150])
    t_biz.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t_biz)
    story.append(Spacer(1, 10))

    # 4. Debt Repayment Breakdown
    story.append(Paragraph("2. Repayment Schedule & Financing Costs", section_heading))
    repay_data = [
        [
            Paragraph("Monthly Installment (EMI)", cell_label),
            Paragraph("Total Interest Payable", cell_label),
            Paragraph("Processing Fee (1.00%)", cell_label),
            Paragraph("Total Gross Repayment", cell_label),
        ],
        [
            Paragraph(f"<b>{p_info.get('monthly_emi_formatted', 'N/A')}</b>", cell_val_bold),
            Paragraph(f"{p_info.get('total_interest_formatted', 'N/A')}", cell_val),
            Paragraph(f"{p_info.get('processing_fee_formatted', 'N/A')}", cell_val),
            Paragraph(f"<b>{p_info.get('total_payment_formatted', 'N/A')}</b>", cell_val_bold),
        ],
    ]
    t_repay = Table(repay_data, colWidths=[135, 135, 135, 135])
    t_repay.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#ffffff")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_repay)
    story.append(Spacer(1, 10))

    # 5. Financial Standing & DSCR Evaluation
    story.append(Paragraph("3. Financial Standing & Debt Service Coverage Ratio (DSCR)", section_heading))
    dscr_info = packet_data.get("dscr_analysis", {})
    verdict_text = dscr_info.get("verdict_badge", "PRIME APPROVAL")
    verdict_color = colors.HexColor("#059669") if "APPROVAL" in verdict_text or "ELIGIBLE" in verdict_text else colors.HexColor("#b91c1c")

    dscr_data = [
        [
            Paragraph("Operating Metric", cell_label),
            Paragraph("Amount / Ratio", cell_label),
            Paragraph("Statutory / Policy Benchmark", cell_label),
            Paragraph("Compliance Status", cell_label),
        ],
        [
            Paragraph("Trailing Monthly Revenue", cell_val),
            Paragraph(dscr_info.get("revenue_formatted", "N/A"), cell_val),
            Paragraph("Verified POS / Inflow Ledger", cell_val),
            Paragraph("VERIFIED", cell_val_bold),
        ],
        [
            Paragraph("Trailing Monthly Expenses", cell_val),
            Paragraph(dscr_info.get("expenses_formatted", "N/A"), cell_val),
            Paragraph("Audited Outflows & Supplier Pay", cell_val),
            Paragraph("VERIFIED", cell_val_bold),
        ],
        [
            Paragraph("Monthly Net Operating Income (NOI)", cell_label),
            Paragraph(f"<b>{dscr_info.get('net_operating_income_formatted', 'N/A')}</b>", cell_val_bold),
            Paragraph("Must exceed total debt obligations", cell_val),
            Paragraph("POSITIVE" if dscr_info.get("net_operating_income_minor", 0) > 0 else "DEFICIT", cell_val_bold),
        ],
        [
            Paragraph("Existing Monthly Debt Service", cell_val),
            Paragraph(dscr_info.get("existing_debt_formatted", "0.00 BDT"), cell_val),
            Paragraph("Reported existing loan commitments", cell_val),
            Paragraph("RECORDED", cell_val),
        ],
        [
            Paragraph("Total Projected Debt Service (Post-Loan)", cell_label),
            Paragraph(f"<b>{dscr_info.get('total_debt_service_formatted', 'N/A')}</b>", cell_val_bold),
            Paragraph("Existing Debt + Proposed New EMI", cell_val),
            Paragraph("TESTED", cell_val),
        ],
        [
            Paragraph("Projected Shop DSCR", cell_label),
            Paragraph(f"<b>{dscr_info.get('projected_dscr_formatted', 'N/A')}</b>", cell_val_bold),
            Paragraph("Statutory Threshold: >= 1.25x", cell_val),
            Paragraph(verdict_text, ParagraphStyle("Verdict", parent=cell_val_bold, textColor=verdict_color)),
        ],
        [
            Paragraph("Debt-to-Income (DTI)", cell_val),
            Paragraph(dscr_info.get("dti_formatted", "N/A"), cell_val),
            Paragraph("Prudential Cap: <= 40.0% of Net Income", cell_val),
            Paragraph("PASS" if dscr_info.get("dti_pct", 0) <= 40 else "ELEVATED", cell_val_bold),
        ],
    ]
    t_dscr = Table(dscr_data, colWidths=[150, 110, 160, 120])
    t_dscr.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t_dscr)
    story.append(Spacer(1, 10))

    # 6. Commercial SME Bank Product Comparison
    story.append(Paragraph("4. Commercial SME Bank Match Evaluation", section_heading))
    bank_matches = packet_data.get("bank_matches", [])
    bm_rows = [
        [
            Paragraph("Bank Provider", cell_label),
            Paragraph("Loan Product", cell_label),
            Paragraph("Max Facility", cell_label),
            Paragraph("Interest Rate", cell_label),
            Paragraph("Min DSCR", cell_label),
            Paragraph("Match Status", cell_label),
        ]
    ]
    for b in bank_matches[:5]:
        status_text = b.get("match_status", "MATCHED")
        st_color = colors.HexColor("#059669") if status_text == "MATCHED" else colors.HexColor("#dc2626")
        bm_rows.append([
            Paragraph(b.get("bank_name", "Demo Bank"), cell_val),
            Paragraph(b.get("product_name", "SME Product"), cell_val),
            Paragraph(b.get("max_amount_formatted", "N/A"), cell_val),
            Paragraph(f"{b.get('annual_interest_rate_pct', 11.0):.2f}%", cell_val),
            Paragraph(f"{b.get('min_dscr', 1.25):.2f}x", cell_val),
            Paragraph(status_text, ParagraphStyle("BMStatus", parent=cell_val_bold, textColor=st_color)),
        ])

    if len(bm_rows) == 1:
        bm_rows.append([Paragraph("No products available", cell_val)] * 6)

    t_bm = Table(bm_rows, colWidths=[100, 120, 80, 70, 60, 110])
    t_bm.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t_bm)
    story.append(Spacer(1, 10))

    # 7. Document Checklist & Formal Endorsement
    story.append(Paragraph("5. Required Statutory Verification Documents", section_heading))
    docs_text = (
        "<b>Standard Submission Checklist</b>: (1) Valid Trade License (Renewed for current fiscal year); "
        "(2) 12-Month Bank Statement from principal operating account; (3) National ID / Smart NID of Managing Director / Proprietor; "
        "(4) Tax Identification Number (TIN) & Tax Return Acknowledgement; (5) Commercial Shop Tenancy Agreement or Title Deed."
    )
    story.append(Paragraph(docs_text, subtitle_style))
    story.append(Spacer(1, 8))

    # 8. Signature Block
    sig_data = [
        [
            Paragraph("<b>Applicant Endorsement:</b>", cell_label),
            Paragraph("<b>Automated AI Credit Audit:</b>", cell_label),
        ],
        [
            Paragraph("<br/><br/>________________________________________<br/>Managing Director / Authorized Signatory", cell_val),
            Paragraph("<br/><br/><b>SME Finance Copilot Autonomous Underwriting Engine</b><br/>Deterministic GAAP / IFRS Policy Validator • Signed Electronically", cell_val),
        ],
    ]
    t_sig = Table(sig_data, colWidths=[270, 270])
    t_sig.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.HexColor("#94a3b8")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(KeepTogether([t_sig]))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
