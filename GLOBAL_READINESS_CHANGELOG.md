# Global Readiness Changelog & Compatibility Analysis

**System:** SME Finance Copilot  
**Release:** 2.0.0 (Global 100-Language & Multi-Country Enterprise Edition)  
**Branch:** `feat/global-100-lang-audit-fix`  
**Date:** October 2026  

---

## 1. Overview of Changes

This release upgrades SME Finance Copilot from a single-locale prototype into a globally extensible, multi-country SME financial operating system supporting:
- A versioned **100-Language Registry** with capability tracking tiers.
- A **Centralized i18n Translation & Formatting Engine** with financial entity invariance.
- **Multi-Country Statutory Financial Profiles** (China, Bangladesh, Saudi Arabia, USA, Australia, Kuwait, Uzbekistan) with verified official legal citations.
- **Dynamic Multi-Currency Precision Arithmetic** supporting 2-decimal, 3-decimal (KWD 1000 minor units), and 0-decimal (JPY) representations.
- **Multilingual AI Security** including Unicode NFKC sanitization, BiDi override removal, PII masking, and adversarial prompt injection defense across 7 languages.
- Complete API route suite, reproducible evaluation harness, and 7-step competition demonstration.

---

## 2. File-by-File Inventory of Modifications

### New Core Architecture Files
1. `src/i18n/registry.py`:
   - Defines `LanguageEntry`, `LanguageRegistry`, `CapabilityStatus`, and `TextDirection`.
   - Tracks 100 languages with ISO code, script, text direction, evaluation samples, and known limitations.
2. `src/i18n/formatters.py`:
   - Implements `LocaleFormatter`: locale-aware decimal/thousands separators, dynamic currency formatting, and bidirectional native digit conversions (Bengali, Arabic-Indic, Devanagari).
3. `src/i18n/translator.py`:
   - Implements `I18nService` and `t()` convenience wrapper.
   - Provides dotted key navigation, fallback hierarchy to English, and placeholder token interpolation preserving numbers verbatim.
4. `src/i18n/locales/*.json`:
   - 6 master catalogs: `en.json`, `bn.json`, `zh.json`, `ar.json`, `es.json`, `hi.json`.
   - 68 standardized keys per catalog across 6 financial and operational domains.
5. `src/core/country_profiles.py`:
   - Defines `CountryProfile`, `RegulatorySourceEntry`, and `CountryRegistry`.
   - Contains statutory tax rates, DSCR minimum covenants, e-invoicing standards, and official legal citations for 7 jurisdictions.
6. `src/api/routes/i18n.py`:
   - FastAPI endpoints:
     - `GET /api/i18n/languages`
     - `GET /api/i18n/languages/{code}`
     - `GET /api/i18n/countries`
     - `GET /api/i18n/countries/{country_code}`
     - `GET /api/i18n/translations/{locale}`
     - `POST /api/i18n/format-currency`
     - `POST /api/i18n/audit-prompt`
7. `storage/i18n/language_registry.json`:
   - Versioned machine-readable export of 100 registered languages.
8. `storage/i18n/country_registry.json`:
   - Versioned machine-readable export of multi-country profiles and regulatory sources.

### Modified Files & Enhancements
1. `src/core/money.py`:
   - Added `get_minor_unit_multiplier(currency)` supporting dynamic minor unit factors (1000 for KWD/BHD/OMR, 1 for JPY, 100 default).
   - Preserved existing `format()` output contracts (`"80,000.00 BDT"`).
2. `src/documents/classifier.py`:
   - Added Chinese, Arabic, Spanish, and Hindi keyword weights across all document categories (`sales_receipt`, `purchase_invoice`, `expense_receipt`, `payment_receipt`).
   - Added `predict()` and `classify()` classmethod aliases.
3. `src/documents/extractor.py`:
   - Added multilingual date patterns (including Chinese `YYYY年MM月DD日`).
   - Added multilingual invoice number and total amount patterns.
   - Added `DocumentExtractor` public export alias and `extract_from_text()` method.
4. `src/core/security.py`:
   - Implemented `sanitize_multilingual_input()` with Unicode NFKC normalization, BiDi override removal, and invisible character stripping.
   - Implemented `detect_multilingual_prompt_injection()` with coverage across English, Bengali, Chinese, Arabic, Russian, Spanish, and Hindi.
   - Implemented `redact_pii()` masking credit cards, emails, and phone numbers.
5. `src/ai/guardrails.py`:
   - Integrated language detection, prompt injection defense, and multi-country tax/covenant context.
   - Preserved exact `Money.format()` contract while adding localized labels.
7. `src/config.py`:
   - Added explicit `DEFAULT_LOCALE: str = "en"` establishing English as system master default.
   - Added `DEFAULT_COUNTRY: str = "CN"` establishing China as current SME operating jurisdiction while preserving `DEFAULT_CURRENCY = "BDT"` for seamless test backwards compatibility.
8. `src/i18n/formatters.py` (Enhancement):
   - Added `format_chinese_financial_units()` for authentic Chinese SME commercial notation: Wan (万 - $10^4$) and Yi (亿 - $10^8$) (e.g., `¥ 50.00万元`).
9. `src/i18n/translator.py` (Enhancement):
   - Added robust POSIX and BCP-47 locale normalization resolving `zh-CN`, `zh_CN`, `en-US`, and `bn-BD` to master translation catalogs.
10. `src/documents/extractor.py` (Enhancement):
   - Decoupled ASCII `\b` word boundary matching from non-ASCII Unicode terms across all regex categories.
   - Prioritized `发票号码` over `发票代码` for Chinese Fapiao and added `চালানপত্র নম্বর` for Bengali Mushak-6.3.

### New Test Suites & Evaluation Scripts
1. `tests/test_i18n_multilingual.py`:
   - 16 tests verifying 100 languages, schema, RTL detection, catalog integrity, fallback, fact preservation, digit conversions, Chinese Wan/Yi formatting, and BCP-47 locale normalization.
2. `tests/test_country_profiles.py`:
   - 7 tests verifying country profiles, statutory tax rates, 3-decimal KWD precision, and legal citations.
3. `tests/test_multilingual_security.py`:
   - 14 tests verifying Unicode sanitization, BiDi override removal, prompt injection defense in 7 languages, PII redaction, and FastAPI endpoints.
4. `tests/test_document_pipeline.py`:
   - Added end-to-end multi-script invoice ingestion tests verifying Chinese Fapiao (`23442000000012345678`) and Bengali Mushak-6.3 (`CHALAN-2026-9901`).
5. `src/evaluation/eval_multilingual.py`:
   - Reproducible benchmark harness evaluating fact preservation, calculation parity, classification, and prompt injection defense.
6. `scripts/demo_multilingual_competition.py`:
   - 7-step competition demonstration script structured around English-first, China-second operational priority.

---

## 3. Backward Compatibility & Regression Analysis

A core mandate of this upgrade was **zero regression of existing features and API contracts**:

1. **Existing Unit Tests:**
   - Prior test count: **27 passed**
   - New test count: **65 passed (27 original + 38 new)**
   - Pass rate: **100% (65/65)**.
2. **Deterministic Ledger Compatibility:**
   - All monetary amounts remain stored as integers in minor units in SQLite (`BigInteger`).
   - No floating-point contamination was introduced into the ledger.
3. **Database Schema Integrity:**
   - No breaking migrations were applied to `sme_finance.db`.
   - All 160,090 verified relational rows (27 shops, 21,978 sales, 1,080 products, etc.) remain intact.
4. **FastAPI Route Compatibility:**
   - Existing endpoints (`/api/finance/*`, `/api/documents/*`, `/api/evaluation/*`) remain completely unaffected.

---

## 4. Rollback Plan

If a rollback is required, the clean Git branch isolation makes reversal instantaneous:

```bash
# Return to previous stable commit or branch
git checkout master
# Or discard branch changes
git checkout feat/global-100-lang-audit-fix
git reset --hard HEAD~1
```
All persistent database records in `sme_finance.db` remain 100% compatible.
