# FinTechathon 2026: SME Finance Copilot — Known Limitations & Honest Disclosures

**Document Version:** 1.0.0 (Master Release)  
**Standard:** Truth in Engineering & Transparent Competition Disclosure

---

## 1. Transparent Architecture Disclosures

In accordance with competition rules, we explicitly distinguish fully verified production capabilities from simulated or hardware-dependent features:

### 1. Offline Deterministic vs. Cloud LLM Mode
* **Status:** Verified Hybrid Implementation.
* **Disclosure:** When an external LLM API key (`OPENAI_API_KEY`) is not supplied, the AI Copilot operates in **Deterministic Rule-Based Mode**. It extracts verified metrics directly from the database and structures expert turnaround plans using deterministic financial algorithms. It does not fabricate external LLM completions.

### 2. Synthetic Data Disclosure (Competition Sandbox)
* **Status:** Simulated Multi-Month Ledger Data.
* **Disclosure:** To provide judges with rich historical financial data across retail operations (816 sales, 354 expenses, 44 receivables, 41 SKUs), realistic synthetic data was seeded using `src/database/seed.py`. All calculations, sums, margins, and ratios on this data are genuine database queries.

### 3. Bank Loan Application API Integration
* **Status:** Simulated Core Banking Integration.
* **Disclosure:** While loan product matching, APR calculations, DSCR underwriting (1.25x benchmark), and PDF Underwriting Packet generation are 100% operational, the final "Submit Application to Bank" step simulates the HTTP response payload of partner banks (BRAC Bank, City Bank), as commercial bank core banking APIs require institutional sandbox VPNs.

### 4. Browser Audio & Voice Recognition
* **Status:** Hardware & Browser Dependent.
* **Disclosure:** Voice recognition utilizes the standard browser Web Speech API (`webkitSpeechRecognition`). In Google Chrome and Microsoft Edge on `localhost`, this operates out of the box. Over non-localhost HTTP network IPs, Chromium restricts microphone access unless served over HTTPS.
