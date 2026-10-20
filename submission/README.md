# FinTechathon 2026 — Finova Finpilot: SME Finance Copilot (Topic E)

**Competition:** FinTechathon 2026 — International Track  
**Topic:** Topic E — SME Finance Copilot  
**Theme:** AI as an Autonomous Financial Participant  
**Submission Status:** Production Ready & Independently Verified (224/224 Tests Passed)  
**Primary Repository:** [https://github.com/ashik123-a1/Finova-Finpilot](https://github.com/ashik123-a1/Finova-Finpilot)

---

## 1. Executive Summary

**Finova Finpilot** is a local-first autonomous financial operating system built for micro, small, and medium enterprises. It combines deterministic zero-float accounting, institutional credit underwriting (DSCR modeling), grounded RAG conversational intelligence, and an autonomous voice HUD with consequential action safeguards.

---

## 2. Quick Evaluation Links

* **1-Click Launch (Windows):** Run `start.bat` (Starts on `http://127.0.0.1:8050`)
* **Local Installation Manual:** [`docs/INSTRUCTION_BOOK.md`](../docs/INSTRUCTION_BOOK.md)
* **Canonical Test Catalogue (TC-01..TC-50):** [`docs/TESTING.md`](../docs/TESTING.md)
* **System Architecture:** [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md)
* **Visual Directory Tree:** [`docs/PROJECT_STRUCTURE.md`](../docs/PROJECT_STRUCTURE.md)
* **10-Step Live Demo Script:** [`submission/demo_script.md`](demo_script.md)
* **5-Minute Presentation Script:** [`submission/presentation_script.md`](presentation_script.md)
* **Full Release Audit Report:** [`reports/release_audit.md`](../reports/release_audit.md)
* **Deliverables Checklist:** [`submission/deliverables_checklist.md`](deliverables_checklist.md)

---

## 3. Pre-Configured Demo Credentials

Navigate to `http://127.0.0.1:8050/login` and use **1-Click Demo Login** or manually enter:

| Persona | Email | Password | Role Description |
| :--- | :--- | :--- | :--- |
| **Business Owner** | `demo_owner@smefinance.local` | `DemoPass123!` | Complete enterprise control, loss recovery, loans |
| **Store Manager** | `demo_manager@smefinance.local` | `DemoPass123!` | Inventory reorders, sales operations |
| **Senior Accountant** | `demo_accountant@smefinance.local` | `DemoPass123!` | General ledger, OCR reviews, CSV/PDF reports |
| **Super Admin** | `super_admin@smefinance.local` | `DemoPass123!` | Platform Admin Portal (`/app/admin`) |

---

## 4. Key Verification Metrics

* **Automated Regression Suite:** 224 / 224 tests passed (100% pass rate in ~20s).
* **Database Ledger Integrity:** Integer minor-unit math ($1,525,400.00 revenue, $4,868,176.68 expenses, -$3,342,776.68 loss).
* **Disaster Recovery:** Verified SQLite WAL backup snapshot (`23.46 MB`, 163,054 records) in `var/backups/`.
* **Zero Cloud Lock-In:** Operates 100% locally with offline edge deterministic synthesis.
