"""
Creates ultra-realistic high-contrast test document images in 'ashik/' folder
formatted in clear linear sections so RapidOCR extracts:
- Document Type Classification (100% confidence)
- Invoice Number
- Date
- Counterparty / Vendor / Customer / Payee
- Line Items, Subtotal, Tax/VAT, and Total Amount
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ASHIK_DIR = Path("ashik")
ASHIK_DIR.mkdir(parents=True, exist_ok=True)

# Select standard TrueType fonts
try:
    font_title = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 22)
    font_heading = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 16)
    font_bold = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 14)
    font_body = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 14)
    font_small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 12)
except Exception:
    font_title = font_heading = font_bold = font_body = font_small = ImageFont.load_default()


def create_purchase_invoice():
    w, h = 650, 800
    img = Image.new("RGB", (w, h), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Top border / Header
    draw.rectangle([(0, 0), (w, 12)], fill=(14, 116, 144))
    draw.text((35, 25), "TAX INVOICE / PURCHASE CHALLAN (MUSHAK 6.3)", fill=(14, 116, 144), font=font_title)
    draw.text((35, 55), "National Board of Revenue Commercial Procurement Invoice", fill=(100, 116, 139), font=font_small)

    draw.line([(35, 80), (w - 35, 80)], fill=(203, 213, 225), width=2)

    # Supplier Info (Linear layout)
    y = 95
    draw.text((35, y), "Supplier / Vendor: Bengal Packaging Industries Ltd", fill=(15, 23, 42), font=font_heading)
    y += 25
    draw.text((35, y), "BIN: 001928374-0101 | Industrial Estate, Tejgaon, Dhaka", fill=(100, 116, 139), font=font_small)
    y += 28

    # Metadata
    draw.text((35, y), "Invoice No: INV-2026-9812", fill=(15, 23, 42), font=font_bold)
    draw.text((320, y), "Date: 2026-10-15", fill=(15, 23, 42), font=font_bold)
    y += 25
    draw.text((35, y), "Buyer / Customer: Bismillah Store (Main Branch, Road 27 Dhanmondi)", fill=(15, 23, 42), font=font_body)
    draw.text((320, y + 22), "Payment Terms: 30 Days Credit (বাকিতে ক্রয়)", fill=(14, 116, 144), font=font_bold)
    y += 50

    draw.line([(35, y), (w - 35, y)], fill=(203, 213, 225), width=2)
    y += 15

    # Table Header
    draw.rectangle([(35, y), (w - 35, y + 30)], fill=(241, 245, 249))
    draw.text((45, y + 6), "Item Description", fill=(30, 41, 59), font=font_bold)
    draw.text((340, y + 6), "Qty", fill=(30, 41, 59), font=font_bold)
    draw.text((420, y + 6), "Rate", fill=(30, 41, 59), font=font_bold)
    draw.text((520, y + 6), "Total (BDT)", fill=(30, 41, 59), font=font_bold)
    y += 40

    # Items
    items = [
        ("Eco Kraft Paper Bags 5000 pcs", "5000", "4.50", "22,500.00"),
        ("Heavy Duty Corrugated Carton Boxes", "100", "30.00", "3,000.00"),
    ]
    for desc, qty, rate, tot in items:
        draw.text((45, y), desc, fill=(15, 23, 42), font=font_body)
        draw.text((345, y), qty, fill=(15, 23, 42), font=font_body)
        draw.text((420, y), f"Tk {rate}", fill=(15, 23, 42), font=font_body)
        draw.text((520, y), f"Tk {tot}", fill=(15, 23, 42), font=font_body)
        y += 30

    draw.line([(35, y + 10), (w - 35, y + 10)], fill=(226, 232, 240), width=1)
    y += 25

    # Totals
    draw.text((360, y), "Subtotal:", fill=(71, 85, 105), font=font_body)
    draw.text((520, y), "Tk 25,500.00", fill=(15, 23, 42), font=font_body)
    y += 26

    draw.text((360, y), "VAT (15%):", fill=(71, 85, 105), font=font_body)
    draw.text((520, y), "Tk 3,825.00", fill=(15, 23, 42), font=font_body)
    y += 30

    draw.rectangle([(340, y), (w - 35, y + 42)], fill=(240, 253, 250))
    draw.text((350, y + 10), "Total Consideration:", fill=(13, 148, 136), font=font_heading)
    draw.text((500, y + 10), "BDT 29,325.00", fill=(13, 148, 136), font=font_heading)

    y += 90
    draw.text((35, y), "Classification: Purchase Invoice | General Ledger: Accounts Payable & Inventory Restock", fill=(100, 116, 139), font=font_small)

    out_path = ASHIK_DIR / "1_Purchase_Invoice_Bengal_Packaging.png"
    img.save(out_path, "PNG")
    print(f"Created: {out_path}")


def create_sales_receipt():
    w, h = 550, 750
    img = Image.new("RGB", (w, h), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Header
    draw.rectangle([(0, 0), (w, 12)], fill=(16, 185, 129))
    draw.text((w // 2 - 110, 25), "BISMILLAH STORE", fill=(15, 23, 42), font=font_title)
    draw.text((w // 2 - 130, 55), "RETAIL SALES RECEIPT / ক্যাশ মেমো", fill=(16, 185, 129), font=font_heading)
    draw.text((w // 2 - 95, 80), "Road 27, Dhanmondi, Dhaka", fill=(100, 116, 139), font=font_small)

    draw.line([(30, 105), (w - 30, 105)], fill=(203, 213, 225), width=2)

    y = 120
    draw.text((30, y), "Customer Name: Md. Rahim Ullah", fill=(15, 23, 42), font=font_heading)
    y += 25
    draw.text((30, y), "Receipt No: INV-2026-4401", fill=(15, 23, 42), font=font_bold)
    draw.text((320, y), "Date: 2026-10-18", fill=(15, 23, 42), font=font_bold)
    y += 25
    draw.text((30, y), "Payment Method: bKash Mobile Banking (TRX-9988220)", fill=(217, 70, 239), font=font_bold)
    y += 35

    draw.line([(30, y), (w - 30, y)], fill=(203, 213, 225), width=2)
    y += 15

    # Table Header
    draw.rectangle([(30, y), (w - 30, y + 30)], fill=(241, 245, 249))
    draw.text((40, y + 6), "Item Description", fill=(30, 41, 59), font=font_bold)
    draw.text((310, y + 6), "Qty", fill=(30, 41, 59), font=font_bold)
    draw.text((410, y + 6), "Total (BDT)", fill=(30, 41, 59), font=font_bold)
    y += 40

    items = [
        ("Miniket Rice 25kg Premium", "1", "1,850.00"),
        ("Teer Pure Soybean Oil 5L", "1", "870.00"),
        ("Fresh Refined White Sugar 5kg", "1", "680.00"),
    ]
    for desc, qty, tot in items:
        draw.text((40, y), desc, fill=(15, 23, 42), font=font_body)
        draw.text((315, y), qty, fill=(15, 23, 42), font=font_body)
        draw.text((410, y), f"Tk {tot}", fill=(15, 23, 42), font=font_body)
        y += 30

    draw.line([(30, y + 10), (w - 30, y + 10)], fill=(226, 232, 240), width=1)
    y += 25

    draw.text((270, y), "Subtotal:", fill=(71, 85, 105), font=font_body)
    draw.text((410, y), "Tk 3,400.00", fill=(15, 23, 42), font=font_body)
    y += 25

    draw.text((270, y), "Discount (5%):", fill=(71, 85, 105), font=font_body)
    draw.text((410, y), "Tk 170.00", fill=(225, 29, 72), font=font_body)
    y += 30

    draw.rectangle([(250, y), (w - 30, y + 42)], fill=(236, 253, 245))
    draw.text((260, y + 10), "Total Payable:", fill=(5, 150, 105), font=font_heading)
    draw.text((395, y + 10), "BDT 3,230.00", fill=(5, 150, 105), font=font_heading)

    y += 85
    draw.text((w // 2 - 95, y), "Thank You For Shopping With Us!", fill=(100, 116, 139), font=font_bold)
    draw.text((30, y + 25), "Classification: Sales Receipt | General Ledger: +Revenue & +Cash Inflow", fill=(148, 163, 184), font=font_small)

    out_path = ASHIK_DIR / "2_Sales_Receipt_POS_Bismillah_Store.png"
    img.save(out_path, "PNG")
    print(f"Created: {out_path}")


def create_expense_receipt():
    w, h = 600, 750
    img = Image.new("RGB", (w, h), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Top banner
    draw.rectangle([(0, 0), (w, 12)], fill=(217, 119, 6))
    draw.text((35, 25), "COMMERCIAL UTILITY EXPENSE VOUCHER", fill=(217, 119, 6), font=font_title)
    draw.text((35, 55), "Dhaka Electric Supply Company (DESCO Commercial Electricity)", fill=(100, 116, 139), font=font_small)

    draw.line([(35, 80), (w - 35, 80)], fill=(203, 213, 225), width=2)

    y = 95
    draw.text((35, y), "Payee / Billing Company: DESCO Electricity Supply", fill=(15, 23, 42), font=font_heading)
    y += 25
    draw.text((35, y), "Tariff: Commercial E | Meter No: 8819-2041-09", fill=(100, 116, 139), font=font_small)
    y += 25

    draw.text((35, y), "Bill No: BILL-8819-2041-09", fill=(15, 23, 42), font=font_bold)
    draw.text((320, y), "Date: 2026-10-10", fill=(15, 23, 42), font=font_bold)
    y += 25
    draw.text((35, y), "Consumer / Account: Bismillah Store Main Branch", fill=(15, 23, 42), font=font_body)
    draw.text((320, y), "Expense Category: Utilities (বাণিজ্যিক বিদ্যুৎ)", fill=(217, 119, 6), font=font_bold)
    y += 45

    draw.line([(35, y), (w - 35, y)], fill=(203, 213, 225), width=2)
    y += 15

    # Expense breakdown
    draw.rectangle([(35, y), (w - 35, y + 30)], fill=(241, 245, 249))
    draw.text((45, y + 6), "Expense Particulars", fill=(30, 41, 59), font=font_bold)
    draw.text((460, y + 6), "Amount (BDT)", fill=(30, 41, 59), font=font_bold)
    y += 40

    charges = [
        ("Energy Charge (1,420 kWh consumed)", "14,910.00"),
        ("Commercial Demand & Minimum Charge", "1,200.00"),
        ("Govt VAT & Supplementary Duty (5%)", "805.50"),
    ]
    for desc, amt in charges:
        draw.text((45, y), desc, fill=(15, 23, 42), font=font_body)
        draw.text((460, y), f"Tk {amt}", fill=(15, 23, 42), font=font_body)
        y += 30

    draw.line([(35, y + 10), (w - 35, y + 10)], fill=(203, 213, 225), width=1)
    y += 25

    draw.rectangle([(290, y), (w - 35, y + 42)], fill=(254, 243, 199))
    draw.text((305, y + 10), "Total Net Bill:", fill=(180, 83, 9), font=font_heading)
    draw.text((450, y + 10), "BDT 16,915.50", fill=(180, 83, 9), font=font_heading)

    y += 90
    draw.text((35, y), "Classification: Expense Receipt | General Ledger: Deducts from Net Profit as OPEX", fill=(100, 116, 139), font=font_small)

    out_path = ASHIK_DIR / "3_Expense_Receipt_DESCO_Electricity.png"
    img.save(out_path, "PNG")
    print(f"Created: {out_path}")


def create_payment_receipt():
    w, h = 650, 750
    img = Image.new("RGB", (w, h), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Top border
    draw.rectangle([(0, 0), (w, 12)], fill=(99, 102, 241))
    draw.text((35, 25), "SME LOAN DISBURSEMENT ADVICE / PAYMENT RECEIPT", fill=(99, 102, 241), font=font_title)
    draw.text((35, 55), "BRAC Bank Small & Medium Enterprise Banking Division", fill=(100, 116, 139), font=font_small)

    draw.line([(35, 80), (w - 35, 80)], fill=(203, 213, 225), width=2)

    y = 95
    draw.text((35, y), "Financing Bank / Payer: BRAC Bank SME Banking", fill=(15, 23, 42), font=font_heading)
    y += 25
    draw.text((35, y), "Facility Sanction Reference: SME-LN-800K-2026", fill=(100, 116, 139), font=font_small)
    y += 25

    draw.text((35, y), "Receipt Ref: SME-LN-800K-2026", fill=(15, 23, 42), font=font_bold)
    draw.text((340, y), "Date: 2026-10-12", fill=(15, 23, 42), font=font_bold)
    y += 25
    draw.text((35, y), "Borrower Beneficiary: Bismillah Store (Current A/C: 1501-2099-4400-01)", fill=(15, 23, 42), font=font_body)
    draw.text((340, y + 20), "Payment Method: Bank Transfer (BEFTN)", fill=(99, 102, 241), font=font_bold)
    y += 50

    draw.line([(35, y), (w - 35, y)], fill=(203, 213, 225), width=2)
    y += 15

    # Breakdown
    draw.rectangle([(35, y), (w - 35, y + 30)], fill=(241, 245, 249))
    draw.text((45, y + 6), "Transaction Particulars", fill=(30, 41, 59), font=font_bold)
    draw.text((490, y + 6), "Amount (BDT)", fill=(30, 41, 59), font=font_bold)
    y += 40

    terms = [
        ("Working Capital Term Loan Facility (24 Months)", "800,000.00"),
        ("Monthly Repayment Installment (EMI)", "37,458.00"),
    ]
    for desc, amt in terms:
        draw.text((45, y), desc, fill=(15, 23, 42), font=font_body)
        draw.text((490, y), f"Tk {amt}", fill=(15, 23, 42), font=font_body)
        y += 30

    draw.line([(35, y + 10), (w - 35, y + 10)], fill=(203, 213, 225), width=1)
    y += 25

    draw.rectangle([(290, y), (w - 35, y + 42)], fill=(238, 242, 255))
    draw.text((305, y + 10), "Total Disbursed:", fill=(67, 56, 202), font=font_heading)
    draw.text((465, y + 10), "BDT 800,000.00", fill=(67, 56, 202), font=font_heading)

    y += 90
    draw.text((35, y), "Classification: Payment Receipt | General Ledger: Cash Flow Liquidity Movement & Loan Liability", fill=(100, 116, 139), font=font_small)

    out_path = ASHIK_DIR / "4_Payment_Receipt_BRAC_Bank_Loan.png"
    img.save(out_path, "PNG")
    print(f"Created: {out_path}")


def create_readme():
    content = """# Ashik Test Data Suite — 4 Financial Document Types

এই ফোল্ডারের ফাইলগুলো দিয়ে আপনি সরাসরি **SME Finance Copilot** এর Document Capture & Gated Review Gateway টেস্ট করতে পারবেন।

---

### 1. Purchase Invoice (ক্রয় চালান)
- **ফাইল:** `1_Purchase_Invoice_Bengal_Packaging.png`
- **ডকুমেন্টের ধরন:** Purchase Invoice (ক্রয় চালান)
- **সরবরাহকারী (Supplier):** `Bengal Packaging Industries Ltd`
- **মোট টাকার অংক:** `৳ 29,325.00`
- **লেজার প্রভাব:** পণ্য ইনভেন্টরি স্টক বৃদ্ধি পাবে এবং সাপ্লায়ারের বাকি (Accounts Payable) রেজিস্টার হবে।

---

### 2. Sales Receipt (বিক্রয় মেমো)
- **ফাইল:** `2_Sales_Receipt_POS_Bismillah_Store.png`
- **ডকুমেন্টের ধরন:** Sales Receipt (ক্যাশ মেমো)
- **ক্রেতা (Customer):** `Md. Rahim Ullah`
- **মোট বিক্রয়:** `৳ 3,230.00` (bKash Payment)
- **লেজার প্রভাব:** বিক্রয় আয় (Operating Revenue) এবং ক্যাশ/ব্যাংক ব্যালেন্সে বৃদ্ধি পাবে।

---

### 3. Expense Receipt (খরচ ভাউচার / বিল)
- **ফাইল:** `3_Expense_Receipt_DESCO_Electricity.png`
- **ডকুমেন্টের ধরন:** Expense Receipt (বাণিজ্যিক বিদ্যুৎ বিল)
- **প্রাপক (Payee):** `DESCO Electricity Supply`
- **মোট বিল:** `৳ 16,915.50`
- **লেজার প্রভাব:** চলতি মাসের নেট প্রফিট থেকে OPEX ইউটিলিটি খরচ বাদ যাবে।

---

### 4. Payment Receipt (ব্যাংক লেনদেন / ঋণ প্রাপ্তি রসিদ)
- **ফাইল:** `4_Payment_Receipt_BRAC_Bank_Loan.png`
- **ডকুমেন্টের ধরন:** Payment Receipt (ব্যাংক লোন রসিদ)
- **ব্যাংক (Payer):** `BRAC Bank SME Banking`
- **মোট জমা:** `৳ 800,000.00`
- **লেজার প্রভাব:** ক্যাশ ফ্লোতে ওয়ার্কিং ক্যাপিটাল ইনপুট হবে এবং ২৪ মাসের ইএমআই দায় রেজিস্টার হবে।

---

### আপনি যেভাবে টেস্ট করবেন:
1. ব্রাউজারে `https://able-grip-ton-bicycle.trycloudflare.com/app/documents` খুলুন।
2. **"Drop invoice or click to browse"** বক্সে গিয়ে এই `ashik` ফোল্ডার থেকে যেকোনো ফাইল সিলেক্ট করুন।
3. ওসিআর স্ক্যান শেষে স্বয়ংক্রিয়ভাবে **Human Review & Reconciliation Gateway** পপআপ খুলবে।
4. ক্লাসিফিকেশন ড্রপডাউনে ধরন পরিবর্তন করে দেখুন—UI সাথে সাথে বদলে যাবে!
5. **"Approve & Post to General Ledger"** দিলে ডাটাবেজে সঠিক লেজারে জমা হয়ে যাবে।
"""
    out_path = ASHIK_DIR / "README_TEST_GUIDE.md"
    out_path.write_text(content, encoding="utf-8")
    print(f"Created: {out_path}")


if __name__ == "__main__":
    create_purchase_invoice()
    create_sales_receipt()
    create_expense_receipt()
    create_payment_receipt()
    create_readme()
