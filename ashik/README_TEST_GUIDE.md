# Document Test Suite — 4 Realistic SME Financial Document Samples (OCR & Review Queue)

> **Evaluator Guide:** This directory contains 4 realistic sample commercial documents (Purchase Invoice, Sales Receipt, Utility Bill, Bank Loan Receipt) designed to test the Smart OCR Document Upload & Human-in-the-Loop Review Queue at \/app/documents\.

---

### বাংলা নির্দেশিকা (Bengali Instructions):
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
