"""
Non-destructive Database Readiness & Data Quality Audit Script.
Safely inspects sme_finance.db without altering or deleting any records.
"""

import sqlite3
import sys
import os

DB_PATH = "sme_finance.db"

def run_audit():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database file {DB_PATH} does not exist.")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 60)
    print("1. SQLITE PRAGMAS & INTEGRITY CHECK")
    print("=" * 60)

    # 1. Integrity check
    cursor.execute("PRAGMA integrity_check;")
    integrity_result = cursor.fetchall()
    print("PRAGMA integrity_check:", integrity_result)

    # 2. Foreign key check
    cursor.execute("PRAGMA foreign_key_check;")
    fk_violations = cursor.fetchall()
    print("PRAGMA foreign_key_check violations count:", len(fk_violations))
    if fk_violations:
        print("First 10 FK violations:", fk_violations[:10])

    # 3. Journal mode & synchronous
    cursor.execute("PRAGMA journal_mode;")
    journal_mode = cursor.fetchone()[0]
    cursor.execute("PRAGMA synchronous;")
    synchronous = cursor.fetchone()[0]
    cursor.execute("PRAGMA foreign_keys;")
    foreign_keys_enabled = cursor.fetchone()[0]
    print(f"Journal Mode: {journal_mode}, Synchronous: {synchronous}, FK Enforced: {foreign_keys_enabled}")

    print("\n" + "=" * 60)
    print("2. TABLE ROW COUNTS & SCHEMA INVENTORY")
    print("=" * 60)

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [r[0] for r in cursor.fetchall() if not r[0].startswith("sqlite_")]
    print(f"Total User Tables: {len(tables)}")

    total_rows = 0
    table_counts = {}
    for tbl in tables:
        cursor.execute(f"SELECT COUNT(*) FROM [{tbl}];")
        cnt = cursor.fetchone()[0]
        table_counts[tbl] = cnt
        total_rows += cnt
        print(f"  {tbl:<35} : {cnt:>8,} rows")

    print(f"Total Rows in Database: {total_rows:,}")

    print("\n" + "=" * 60)
    print("3. REFERENTIAL INTEGRITY & ORPHAN CHECKS")
    print("=" * 60)

    # Check for orphan sales -> businesses
    cursor.execute("SELECT COUNT(*) FROM sales s LEFT JOIN businesses b ON s.business_id = b.id WHERE b.id IS NULL;")
    orphan_sales = cursor.fetchone()[0]
    print(f"Orphan sales (missing business_id): {orphan_sales}")

    # Check for orphan sale items -> sales
    cursor.execute("SELECT COUNT(*) FROM sale_items si LEFT JOIN sales s ON si.sale_id = s.id WHERE s.id IS NULL;")
    orphan_sale_items = cursor.fetchone()[0]
    print(f"Orphan sale_items (missing sale_id): {orphan_sale_items}")

    # Check for orphan expenses -> businesses
    cursor.execute("SELECT COUNT(*) FROM expenses e LEFT JOIN businesses b ON e.business_id = b.id WHERE b.id IS NULL;")
    orphan_expenses = cursor.fetchone()[0]
    print(f"Orphan expenses (missing business_id): {orphan_expenses}")

    # Check for orphan products -> businesses
    cursor.execute("SELECT COUNT(*) FROM products p LEFT JOIN businesses b ON p.business_id = b.id WHERE b.id IS NULL;")
    orphan_products = cursor.fetchone()[0]
    print(f"Orphan products (missing business_id): {orphan_products}")

    # Check for orphan documents -> businesses
    cursor.execute("SELECT COUNT(*) FROM documents d LEFT JOIN businesses b ON d.business_id = b.id WHERE b.id IS NULL;")
    orphan_docs = cursor.fetchone()[0]
    print(f"Orphan documents (missing business_id): {orphan_docs}")

    # Check for orphan loans -> businesses
    cursor.execute("SELECT COUNT(*) FROM loan_applications l LEFT JOIN businesses b ON l.business_id = b.id WHERE b.id IS NULL;")
    orphan_loans = cursor.fetchone()[0]
    print(f"Orphan loan_applications (missing business_id): {orphan_loans}")

    print("\n" + "=" * 60)
    print("4. BUSINESS & FINANCIAL INTEGRITY CHECKS")
    print("=" * 60)

    # Currencies in businesses
    cursor.execute("SELECT currency, COUNT(*) FROM businesses GROUP BY currency;")
    currencies = cursor.fetchall()
    print("Businesses by Currency:", currencies)

    # Date ranges for sales
    cursor.execute("SELECT MIN(sale_date), MAX(sale_date) FROM sales;")
    min_sale, max_sale = cursor.fetchone()
    print(f"Sales Date Range: {min_sale} to {max_sale}")

    # Date ranges for expenses
    cursor.execute("SELECT MIN(expense_date), MAX(expense_date) FROM expenses;")
    min_exp, max_exp = cursor.fetchone()
    print(f"Expenses Date Range: {min_exp} to {max_exp}")

    # Negative amounts check (sales total_amount_minor should be >= 0)
    cursor.execute("SELECT COUNT(*) FROM sales WHERE total_amount_minor < 0;")
    negative_sales = cursor.fetchone()[0]
    print(f"Sales with negative total_amount_minor: {negative_sales}")

    # Negative amounts check (expenses amount_minor should be >= 0)
    cursor.execute("SELECT COUNT(*) FROM expenses WHERE amount_minor < 0;")
    negative_expenses = cursor.fetchone()[0]
    print(f"Expenses with negative amount_minor: {negative_expenses}")

    # Verify if sales total_amount_minor matches subtotal - discount + tax (integer math)
    cursor.execute("""
        SELECT COUNT(*) FROM sales 
        WHERE total_amount_minor != (subtotal_minor - discount_minor + tax_minor);
    """)
    mismatched_sales_math = cursor.fetchone()[0]
    print(f"Sales where total != subtotal - discount + tax: {mismatched_sales_math}")

    # Check synthetic labeling
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND sql LIKE '%is_synthetic%';")
    tables_with_synthetic_col = [r[0] for r in cursor.fetchall()]
    print(f"Tables with explicit 'is_synthetic' columns: {tables_with_synthetic_col}")

    for t in tables_with_synthetic_col:
        try:
            cursor.execute(f"SELECT is_synthetic, COUNT(*) FROM [{t}] GROUP BY is_synthetic;")
            counts = cursor.fetchall()
            print(f"  [{t}] synthetic breakdown: {counts}")
        except Exception as e:
            pass

    conn.close()
    print("\nAudit completed successfully.")

if __name__ == "__main__":
    run_audit()
