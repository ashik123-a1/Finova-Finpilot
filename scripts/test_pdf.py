import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.finance.pdf_packet import generate_loan_packet_pdf

sample = {
    'application_number': 'DEMO-LN-20261020-TEST',
    'generated_at_formatted': '20 Oct 2026, 04:30 UTC',
    'business_name': 'Bismillah Store (Synthetic)',
    'shop_name': 'Main Branch',
    'currency': 'BDT',
    'tax_id': 'BIN-99281-002',
    'loan_purpose_label': 'Working Capital Expansion',
    'loan_terms': {
        'principal_formatted': '800,000 BDT',
        'tenure_months': 24,
        'annual_interest_rate_pct': 11.5,
        'monthly_emi_formatted': '37,472 BDT',
        'total_interest_formatted': '99,334 BDT',
        'processing_fee_formatted': '8,000 BDT',
        'total_payment_formatted': '899,334 BDT'
    },
    'dscr_analysis': {
        'revenue_formatted': '350,000 BDT / mo',
        'expenses_formatted': '100,000 BDT / mo',
        'net_operating_income_minor': 25000000,
        'net_operating_income_formatted': '250,000 BDT / mo',
        'existing_debt_formatted': '0.00 BDT / mo',
        'total_debt_service_formatted': '37,472 BDT / mo',
        'projected_dscr_formatted': '6.67x',
        'verdict_badge': 'PRIME APPROVAL',
        'dti_formatted': '15.0%',
        'dti_pct': 15.0
    },
    'bank_matches': [
        {'bank_name': 'BRAC Bank Ltd.', 'product_name': 'Anonya SME Prothom', 'max_amount_formatted': '2,500,000 BDT', 'annual_interest_rate_pct': 11.5, 'min_dscr': 1.25, 'match_status': 'MATCHED'},
        {'bank_name': 'City SME Bank', 'product_name': 'City Tara SME Credit', 'max_amount_formatted': '5,000,000 BDT', 'annual_interest_rate_pct': 10.5, 'min_dscr': 1.30, 'match_status': 'MATCHED'}
    ]
}

pdf = generate_loan_packet_pdf(sample)
print(f"SUCCESS! PDF Generated: {len(pdf)} bytes, Header: {pdf[:5]}")
