import sqlite3

conn = sqlite3.connect("sme_finance.db")
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print(f"Total tables: {len(tables)}")
for i, t in enumerate(tables, 1):
    print(f"  {i}. {t}")
conn.close()
