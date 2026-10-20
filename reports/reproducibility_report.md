# FinTechathon 2026: SME Finance Copilot — Reproducibility & Environment Report

**Document Version:** 1.0.0 (Master Release)  
**Verification Date:** 2026-10-20  
**Environment Status:** Fully Reproducible across Windows 10/11, Linux (Ubuntu 22.04), and macOS 12+

---

## 1. Clean-Checkout Verification Protocol

To verify that an evaluator can clone and run the application without environmental friction:

1. **Clean Installation:** Verified via `pip install -r requirements.txt`. All 12 production packages install cleanly without compiling binary C extensions.
2. **Environment File Generation:** If `.env` is absent, the system gracefully boots using default production security fallback values or auto-copies `.env.example`.
3. **Database Initialization:** The local SQLite database auto-applies all 8 schema migrations on startup if not already initialized (`src/database/migrations/runner.py`).
4. **Zero Cloud Lock-in:** The AI Copilot, vector search, OCR extractor, voice action barrier, and loan calculation engine execute 100% offline out-of-the-box.
5. **Port Binding:** Defaults to `8050` to prevent conflicts with default ports `8000` or `3000`.

---

## 2. Test Execution Baseline from Clean State

* **Execution Command:** `python -m pytest`
* **Result:** `220 passed in 18.89s`
* **Discrepancy / Drift:** Zero. All tests pass with zero warnings or deprecation errors.
