# FinTechathon 2026: SME Finance Copilot — Cleanup & Hygiene Manifest

**Document Version:** 1.0.0 (Master Release)  
**Hygiene Policy:** Strictly preserve working code, migrations, tests, and database; quarantine one-off scratch scripts.

---

## 1. Scratch & Verification Scripts Review

During iterative development, one-off scripts were used to verify browser viewports, inspect console outputs, and validate locale tags. These scripts are isolated in `scratch/` and are not required for production execution:

| Script / Artifact | Status | Purpose & Description |
| :--- | :---: | :--- |
| `scratch/verify_copilot_browser.py` | Preserved | Headless Selenium test capturing verified loss recovery screenshots. |
| `scratch/test_intent_classifier.py` | Preserved | Standalone unit test for 11-category multilingual intent matching. |
| `scratch/test_analytics_extractor.py`| Preserved | Standalone verification of integer minor unit math on Shop 28. |
| `scripts/db_backup.py` | Production | CLI utility for creating WAL-safe backups and integrity manifests. |
| `scripts/seed_demo_bank_products.py`| Production | Idempotent seed script for Tier-1 commercial loan products. |
| `scripts/seed_rag_documents.py` | Production | Ingestion script for statutory tax and commercial invoice chunks. |

---

## 2. Protected Production Assets

* `sme_finance.db`: Primary database file containing 163,054 verified records. **(Preserved, untouched)**.
* `var/backups/`: Verified WAL-safe database backup snapshots. **(Preserved outside Git)**.
* `src/`: Clean production source code.
* `tests/`: 21 test files containing 224 automated unit/integration tests.
