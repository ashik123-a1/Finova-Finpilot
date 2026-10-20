import re

def update_file(path, replacements):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    c = 0
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            c += 1
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Updated {path}: {c}/{len(replacements)} replaced.")

# 1. loans.html
update_file("src/web/templates/app/loans.html", [
    ('Debt Capacity Underwriting Calculator', '{{ _(\'loans.title\') }}'),
    ('Requested Loan Principal', '{{ _(\'loans.loan_amount\') }}'),
    ('Loan Tenure (Months)', '{{ _(\'loans.tenure_months\') }}'),
    ('Expected Annual Interest Rate (%)', '{{ _(\'loans.interest_rate\') }}'),
    ('Monthly Debt Service (EMI)', '{{ _(\'loans.monthly_emi\') }}'),
    ('DSCR Coverage Metric', '{{ _(\'loans.dscr_ratio\') }}'),
    ('Approval Probability', '{{ _(\'loans.approval_probability\') }}'),
    ('Export Loan Packet (PDF)', '{{ _(\'loans.export_packet\') }}'),
    ('Commercial Bank Product Suitability Matrix', '{{ _(\'loans.bank_matching\') }}'),
])

# 2. forecast.html
update_file("src/web/templates/app/forecast.html", [
    ('Estimated Runway (Months)', '{{ _(\'forecast.runway_months\') }}'),
    ('Projected Operating Inflows', '{{ _(\'forecast.inflows\') }}'),
    ('Projected Operating Outflows', '{{ _(\'forecast.outflows\') }}'),
    ('Forecast Horizon (Days)', '{{ _(\'forecast.horizon_days\') }}'),
    ('Confidence Interval', '{{ _(\'forecast.confidence_level\') }}'),
    ('Generate AI Forecast', '{{ _(\'forecast.generate_forecast\') }}'),
    ('Export Projection CSV', '{{ _(\'forecast.export_csv\') }}'),
])

# 3. documents.html
update_file("src/web/templates/app/documents.html", [
    ('Upload Receipt or Invoice', '{{ _(\'documents.upload_title\') }}'),
    ('Drag and drop files here, or browse', '{{ _(\'documents.drag_drop\') }}'),
    ('Supported formats: PNG, JPG, PDF', '{{ _(\'documents.supported_formats\') }}'),
    ('Verified Documents Staging', '{{ _(\'documents.verified_documents\') }}'),
    ('OCR Confidence Score', '{{ _(\'documents.ocr_confidence\') }}'),
    ('Human Review Required', '{{ _(\'documents.human_review\') }}'),
    ('Approve & Post to Ledger', '{{ _(\'documents.post_to_ledger\') }}'),
])

# 4. inventory.html
update_file("src/web/templates/app/inventory.html", [
    ('Add New Product SKU', '{{ _(\'inventory.add_product\') }}'),
    ('SKU Code', '{{ _(\'inventory.sku\') }}'),
    ('Product Name', '{{ _(\'inventory.product_name\') }}'),
    ('Category', '{{ _(\'inventory.category\') }}'),
    ('Unit Purchase Cost', '{{ _(\'inventory.purchase_cost\') }}'),
    ('Unit Selling Price', '{{ _(\'inventory.selling_price\') }}'),
    ('Current Stock Quantity', '{{ _(\'inventory.current_stock\') }}'),
    ('Reorder Threshold', '{{ _(\'inventory.reorder_level\') }}'),
    ('Total Inventory Valuation', '{{ _(\'inventory.total_valuation\') }}'),
    ('Low Stock Alert', '{{ _(\'inventory.low_stock_warning\') }}'),
    ('Stock In / Out Movement', '{{ _(\'inventory.stock_movement\') }}'),
])

# 5. customers.html
update_file("src/web/templates/app/customers.html", [
    ('Add Customer', '{{ _(\'customers.add_customer\') }}'),
    ('Customer Name', '{{ _(\'customers.customer_name\') }}'),
    ('Phone Number', '{{ _(\'customers.phone\') }}'),
    ('Outstanding Receivables (Due)', '{{ _(\'customers.outstanding_due\') }}'),
    ('Credit Limit', '{{ _(\'customers.credit_limit\') }}'),
    ('RFM Segment', '{{ _(\'customers.rfm_segment\') }}'),
    ('Polite Payment Reminder', '{{ _(\'customers.payment_reminder\') }}'),
    ('Draft WhatsApp Notice', '{{ _(\'customers.send_whatsapp\') }}'),
    ('Draft SMS Reminder', '{{ _(\'customers.send_sms\') }}'),
    ('Overdue Receivables Aging', '{{ _(\'customers.overdue_invoices\') }}'),
])

# 6. simulations.html
update_file("src/web/templates/app/simulations.html", [
    ('Break-Even Volume Analysis', '{{ _(\'simulations.break_even\') }}'),
    ('Price Elasticity & Margin Test', '{{ _(\'simulations.pricing_calculator\') }}'),
    ('Capital Investment ROI', '{{ _(\'simulations.roi_analysis\') }}'),
    ('Sensitivity Parameters', '{{ _(\'simulations.sensitivity_test\') }}'),
    ('Run Business Simulation', '{{ _(\'simulations.run_simulation\') }}'),
    ('Projected Impact on Net Cash', '{{ _(\'simulations.projected_impact\') }}'),
])

# 7. audit.html
update_file("src/web/templates/app/audit.html", [
    ('Security Audit Trail', '{{ _(\'audit.security_logs\') }}'),
    ('Cryptographic Hash Chain', '{{ _(\'audit.tamper_detection\') }}'),
    ('SHA-256 Block Hash', '{{ _(\'audit.hash_chain\') }}'),
    ('Verify Ledger Integrity', '{{ _(\'audit.verify_integrity\') }}'),
    ('Chain Intact • No Alterations', '{{ _(\'audit.intact_badge\') }}'),
])

# 8. settings.html
update_file("src/web/templates/app/settings.html", [
    ('General Workspace Settings', '{{ _(\'settings.general_settings\') }}'),
    ('Business & Legal Entity', '{{ _(\'settings.business_profile\') }}'),
    ('Accounting Currency', '{{ _(\'settings.currency_settings\') }}'),
    ('Language & Locale Preference', '{{ _(\'settings.language_preference\') }}'),
    ('Local Database Telemetry', '{{ _(\'settings.db_telemetry\') }}'),
    ('Export Encrypted Backup', '{{ _(\'settings.backup_export\') }}'),
])

# 9. notifications.html
update_file("src/web/templates/app/notifications.html", [
    ('All Notifications', '{{ _(\'notifications.all_alerts\') }}'),
    ('Mark All as Read', '{{ _(\'notifications.mark_all_read\') }}'),
    ('Unread Alerts', '{{ _(\'notifications.unread\') }}'),
    ('System Notices', '{{ _(\'notifications.system_notices\') }}'),
    ('Receivables Reminders', '{{ _(\'notifications.receivables_reminders\') }}'),
    ('Low Stock Alerts', '{{ _(\'notifications.low_stock_alerts\') }}'),
])

print("All internal pages updated with translation tags!")
