"""
Seed & Enhance Demo Bank Products and Underwriting Rules.
Ensures BRAC Bank, City Bank, Eastern Bank, and others have complete
eligibility criteria, DSCR thresholds, collateral details, and loan rules in the database.
100% idempotent.
"""

import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.database.connection import SessionLocal
from src.database.models import DemoBank, LoanProduct, LoanRule

def seed_demo_bank_products():
    db = SessionLocal()
    try:
        # 1. Ensure BRAC Bank Ltd exists
        brac = db.query(DemoBank).filter_by(code="DEMO_BRAC").first()
        if not brac:
            brac = DemoBank(
                name="BRAC Bank Ltd. (Demo)",
                code="DEMO_BRAC",
                contact_info="16221, Gulshan-1, Dhaka, Bangladesh",
                is_synthetic=True
            )
            db.add(brac)
            db.flush()
            print("Created Demo Bank: BRAC Bank Ltd.")

        # Ensure BRAC Bank products exist
        brac_prods = [
            (
                "Anonya SME Prothom",
                100_000_00,       # Min ৳ 100,000
                2_500_000_00,     # Max ৳ 2,500,000
                12, 36,           # 12 - 36 months
                1150,             # 11.50% p.a.
                "reducing_balance",
                100,              # 1.00% fee
                {
                    "min_dscr": 1.25,
                    "collateral": "Unsecured up to 15L, Stock Hypothecation above 15L",
                    "disbursement": "48 Hours Rapid",
                    "supported_purposes": ["working_capital", "branch", "refinance"],
                    "required_docs": ["Trade License", "12-Month Bank Statement", "National ID / Smart NID", "TIN Certificate", "Shop Tenancy Agreement"]
                }
            ),
            (
                "Anonnya Rin Equipment & Store",
                200_000_00,       # Min ৳ 200,000
                5_000_000_00,     # Max ৳ 5,000,000
                12, 60,           # 12 - 60 months
                1075,             # 10.75% p.a.
                "reducing_balance",
                100,
                {
                    "min_dscr": 1.30,
                    "collateral": "Machinery / Equipment Mortgage",
                    "disbursement": "5 Working Days",
                    "supported_purposes": ["equipment", "branch"],
                    "required_docs": ["Trade License", "Pro-forma Equipment Invoice", "12-Month Bank Statement", "Tax Clearance"]
                }
            )
        ]
        for name, min_a, max_a, min_t, max_t, rate, calc, fee, crit in brac_prods:
            p = db.query(LoanProduct).filter_by(bank_id=brac.id, name=name).first()
            if not p:
                p = LoanProduct(
                    bank_id=brac.id,
                    name=name,
                    min_amount_minor=min_a,
                    max_amount_minor=max_a,
                    min_tenure_months=min_t,
                    max_tenure_months=max_t,
                    annual_interest_rate_bps=rate,
                    interest_calc_type=calc,
                    processing_fee_bps=fee,
                    eligibility_criteria_json=json.dumps(crit),
                    is_synthetic=True
                )
                db.add(p)
                db.flush()
                print(f"Created Product: {name} for BRAC Bank")
            else:
                p.eligibility_criteria_json = json.dumps(crit)
                p.min_amount_minor = min_a
                p.max_amount_minor = max_a
                p.annual_interest_rate_bps = rate

        # 2. Enhance existing products for all banks
        all_products = db.query(LoanProduct).all()
        for p in all_products:
            crit = {}
            if p.eligibility_criteria_json:
                try:
                    crit = json.loads(p.eligibility_criteria_json)
                except Exception:
                    crit = {}

            if "City" in (p.bank.name if p.bank else ""):
                if "Working Capital" in p.name or "City Tara" in p.name:
                    p.name = "City Tara SME Credit"
                    p.max_amount_minor = 5_000_000_00
                    p.annual_interest_rate_bps = 1050  # 10.50%
                    crit = {
                        "min_dscr": 1.30,
                        "collateral": "Hypothecation of Book Debts & Stock",
                        "disbursement": "48 Hours Rapid",
                        "supported_purposes": ["working_capital", "refinance"],
                        "required_docs": ["Valid Trade License", "6-Month Bank Statement", "NID of Proprietor", "BIN / VAT Registration"]
                    }
                elif "Seasonal" in p.name or "Micro" in p.name:
                    crit = {
                        "min_dscr": 1.20,
                        "collateral": "Personal Guarantee of Proprietor",
                        "disbursement": "24 Hours Express",
                        "supported_purposes": ["working_capital"],
                        "required_docs": ["Trade License", "Shop Utility Bill", "NID"]
                    }
                elif "Equipment" in p.name:
                    crit = {
                        "min_dscr": 1.25,
                        "collateral": "Equipment Lien",
                        "disbursement": "3-5 Business Days",
                        "supported_purposes": ["equipment", "branch"],
                        "required_docs": ["Trade License", "Equipment Quotation", "12-Month Bank Statement"]
                    }
            elif "Eastern" in (p.bank.name if p.bank else ""):
                if "Working Capital" in p.name or "Overdraft" in p.name or "Shurjo" in p.name:
                    p.name = "EBL Shurjo Overdraft"
                    p.max_amount_minor = 3_000_000_00
                    p.annual_interest_rate_bps = 1100  # 11.00%
                    crit = {
                        "min_dscr": 1.20,
                        "collateral": "Revolving Floating Charge on Inventory",
                        "disbursement": "3 Business Days",
                        "supported_purposes": ["working_capital", "refinance"],
                        "required_docs": ["Trade License", "Audited Financials or 12M Statements", "TIN Certificate", "Lease Deed"]
                    }
                else:
                    crit = {
                        "min_dscr": 1.25,
                        "collateral": "Corporate / Personal Guarantee",
                        "disbursement": "48 Hours Rapid",
                        "supported_purposes": ["working_capital", "equipment", "branch"],
                        "required_docs": ["Trade License", "Bank Statement", "NID"]
                    }
            else:
                # Default criteria
                if not crit:
                    crit = {
                        "min_dscr": 1.25,
                        "collateral": "Hypothecation of Moveable Assets",
                        "disbursement": "3-5 Business Days",
                        "supported_purposes": ["working_capital", "equipment", "branch", "refinance"],
                        "required_docs": ["Trade License", "12-Month Bank Statement", "NID", "TIN"]
                    }

            p.eligibility_criteria_json = json.dumps(crit)

            # Ensure a LoanRule exists for this product
            rule = db.query(LoanRule).filter_by(product_id=p.id).first()
            if not rule:
                rule = LoanRule(
                    product_id=p.id,
                    rule_name=f"{p.name} Underwriting Rule",
                    rule_condition_json=json.dumps({
                        "min_tenure": p.min_tenure_months,
                        "max_tenure": p.max_tenure_months,
                        "min_amount_minor": p.min_amount_minor,
                        "max_amount_minor": p.max_amount_minor,
                        "required_dscr": crit.get("min_dscr", 1.25)
                    }),
                    min_credit_score=600,
                    max_dscr_threshold=crit.get("min_dscr", 1.25),
                    is_synthetic=True
                )
                db.add(rule)
            else:
                rule.max_dscr_threshold = crit.get("min_dscr", 1.25)

        db.commit()
        print(f"Successfully configured {len(all_products)} loan products with rich criteria and rules!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_bank_products()
