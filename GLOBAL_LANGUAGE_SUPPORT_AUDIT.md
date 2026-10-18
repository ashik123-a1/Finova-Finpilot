# Global Language Support Audit — 100-Language Architecture

**System:** SME Finance Copilot  
**Version:** 2.0.0 (Global Enterprise Edition)  
**Audit Lead:** Multilingual NLP Engineer & Internationalization Specialist  
**Evaluation Date:** October 2026  
**Artifact Path:** `storage/i18n/language_registry.json`

---

## 1. Executive Summary & Architecture Philosophy

SME Finance Copilot implements a centralized, versioned **100-Language Master Registry** designed to decouple linguistic rendering from business jurisdictional accounting. 

### The Core Architectural Principles:
1. **Zero Fabrication Policy:** A language is never claimed to be "production-ready" merely because its name appears in a dropdown. Every language is assigned a strictly verified **Capability Tier**.
2. **Language vs. Jurisdiction Orthogonality:** A merchant operating in China can view the system in English, Arabic, or Bengali without altering Chinese statutory tax calculations (13% VAT, CSAS-SE accounting, LPR loan covenants). Selecting English does NOT assume the business operates in the US.
3. **Financial Fact Invariance:** Numerical amounts, decimal fractions, currency codes, and transaction identifiers (`INV-xxxx`) are protected tokens (`{{amount}}`, `{{currency}}`) that remain completely immune to machine translation drift or lexical substitution.
4. **Resilient Fallback Hierarchy:** Any missing translation key gracefully falls back to the fully verified English (`en`) master catalog, accompanied by an audit warning, preventing crashes or blank user interfaces.

### 1.1 Confirmed Product Language Priority

The product establishes a concrete four-tier operational priority:
1. **English (`en`) — Primary Default:** Complete master UI catalog (68 keys), system default locale (`DEFAULT_LOCALE = "en"`), default reports, evaluation output, and competition demonstration language.
2. **Simplified Chinese (`zh-CN` / `zh`) — Second Priority:** Specialized China SME financial workflows, Digital Electronic Fapiao (全电发票 / 增值税发票) extraction, CSAS-SE accounting standards, commercial Wan (万) and Yi (亿) financial unit formatting, and Chinese date parsing.
3. **Bengali (`bn`) — Preserved Core:** 100% complete existing support, NBR Mushak-6.3 VAT invoice extraction, Bangladesh Bank SMART lending covenants, BDT poisha precision, and native Bengali numeral parsing.
4. **Other 97 Registered Languages — Extensible Architecture:** Maintained across evaluated, implemented, and configured capability tiers with truthful, empirical per-language status tracking.

---

## 2. Four-Tier Capability Classification

Each of the 100 registered languages is classified into one of four capability tiers across five functional dimensions: **UI Localization**, **AI / NLP Processing**, **Document OCR**, **Speech / Voice**, and **Financial Glossary**:

| Capability Tier | Definition | Current Count | Verification Criteria |
| :--- | :--- | :---: | :--- |
| **`production_ready`** | Zero critical bugs, 100% catalog coverage, validated against real/synthetic documents, benchmarked for security | **2** | English (`en`), Bengali (`bn`) |
| **`evaluated`** | Empirical benchmark data available, automated prompt injection tests run, partial OCR support | **10** | Simplified Chinese (`zh`), Arabic (`ar`), Spanish (`es`), Hindi (`hi`), Urdu (`ur`), French (`fr`), German (`de`), Japanese (`ja`), Russian (`ru`), Portuguese (`pt`) |
| **`implemented`** | Working translation catalog loaded, locale formatting and native numeral conversion operational | **19** | Italian, Dutch, Polish, Persian, Swahili, Thai, Malay, Tagalog, Tamil, Telugu, Marathi, Gujarati, Ukrainian, Romanian, Greek, Korean, Indonesian, Turkish, Vietnamese |
| **`configured`** | Registered in ISO metadata registry, BCP-47 locale mapped, text direction defined, fallback to English active | **69** | Remaining 69 world languages (e.g. Uzbek, Kazakh, Amharic, Burmese, Hebrew, etc.) |

### 2.1 Multi-Dimensional Capability Breakdown (100 Languages)

To prevent inflated readiness claims, capability is tracked independently across 5 functional dimensions:

| Functional Dimension | `production_ready` | `evaluated` | `implemented` | `configured` | Total | Verification Evidence |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **1. UI Localization** | 2 (`en`, `bn`) | 10 | 19 | 69 | **100** | Full JSON master catalogs, key parity, BCP-47 fallback |
| **2. AI Guardrails & Prompt Defense**| 2 (`en`, `bn`) | 10 | 19 | 69 | **100** | Adversarial injection unit tests & benign queries |
| **3. Document OCR & Extraction** | 2 (`en`, `bn`) | 1 (`zh`) | 9 | 88 | **100** | 70 synthetic receipts benchmarked; Fapiao & Mushak |
| **4. Speech Input / Voice ASR** | 0 | 0 | 0 | 100 | **100** | Browser Web Speech API bindings only; zero offline GPU models claimed |
| **5. Financial Glossary & Math** | 6 (`en`, `bn`, `zh`, `ar`, `es`, `hi`) | 0 | 15 | 79 | **100** | Unit-tested integer math & currency formatting |

---

## 3. Bidirectional (RTL) Script Support

Of the 100 supported languages, exactly **9 languages** utilize Right-to-Left (RTL) scripts. The locale formatter enforces correct layout direction and currency placement:

| Language Code | Language Name | Script Family | Text Direction | Trailing Currency Handling |
| :---: | :--- | :--- | :---: | :--- |
| `ar` | Arabic (العربية) | Arabic | **RTL** | Amount precedes symbol (`1,250.50 ﷼`) |
| `ur` | Urdu (اردو) | Arabic (Nastaliq) | **RTL** | Amount precedes symbol (`1,250.50 ₨`) |
| `fa` | Persian / Farsi (فارسی) | Arabic (Perso-Arabic) | **RTL** | Amount precedes symbol |
| `ps` | Pashto (پښتو) | Arabic (Pashto) | **RTL** | Amount precedes symbol |
| `ku` | Kurdish (کوردی) | Arabic (Central Kurdish) | **RTL** | Amount precedes symbol |
| `he` | Hebrew (עברית) | Hebrew | **RTL** | Amount precedes symbol (`₪`) |
| `yi` | Yiddish (ייִדיש) | Hebrew | **RTL** | Amount precedes symbol |
| `sd` | Sindhi (سنڌي) | Arabic (Sindhi) | **RTL** | Amount precedes symbol |
| `ug` | Uyghur (ئۇيغۇرچە) | Arabic (Uyghurche) | **RTL** | Amount precedes symbol |

---

## 4. Master Translation Catalogs Audit

The translation subsystem was audited against the reference master catalog across 6 core production languages. Every catalog contains **68 standardized keys** structured into 6 domains: `common`, `navigation`, `financial`, `documents`, `loan_risk`, and `compliance`:

| Locale | Language Name | Total Keys | Missing Keys | Completeness % | Placeholder Integrity |
| :---: | :--- | :---: | :---: | :---: | :---: |
| `en` | English (Master Reference) | 68 | 0 | 100.0% | 100.0% (Valid) |
| `bn` | Bengali (বাংলা) | 68 | 0 | 100.0% | 100.0% (Valid) |
| `zh` | Chinese Simplified (简体中文) | 68 | 0 | 100.0% | 100.0% (Valid) |
| `ar` | Arabic (العربية) | 68 | 0 | 100.0% | 100.0% (Valid) |
| `es` | Spanish (Español) | 68 | 0 | 100.0% | 100.0% (Valid) |
| `hi` | Hindi (हिन्दी) | 68 | 0 | 100.0% | 100.0% (Valid) |

**Audit Result:** 0 missing keys, 0 placeholder discrepancies. 100% parameter preservation across all production catalogs.

---

## 5. Script Families & Numeral Normalization

The system incorporates bidirectional numeral normalization across all major non-Latin script families:

| Script Family | Example Native Digits | ASCII Mapping Function | Format Method |
| :--- | :--- | :--- | :--- |
| **Bengali** | `০ ১২৩৪৫৬৭৮৯` | `LocaleFormatter.normalize_digits_to_ascii()` | `convert_digits_to_native(..., "bn")` |
| **Arabic-Indic** | `٠ ١٢٣٤٥٦٧٨٩` | `LocaleFormatter.normalize_digits_to_ascii()` | `convert_digits_to_native(..., "ar")` |
| **Devanagari** | `० १२३४५६७८९` | `LocaleFormatter.normalize_digits_to_ascii()` | `convert_digits_to_native(..., "hi")` |
| **Eastern Arabic** | `۰ ۱۲۳۴۵۶۷۸۹` | `LocaleFormatter.normalize_digits_to_ascii()` | `convert_digits_to_native(..., "fa")` |

**Security Consideration:** All OCR and user inputs pass through Unicode NFKC normalization and digit normalization prior to numerical calculation, guaranteeing that `১২,৪৫০.৫০` and `12,450.50` resolve to the exact identical minor unit integer (`1245050`).

---

## 6. Known Limitations & Technical Roadmap

1. **Complex Brahmic Script Reshaping in OCR:** RapidOCR performs well on printed English, Chinese, and standard Bengali text, but shows degradation on complex ligatures in handwritten or noisy receipts. The system automatically triggers `review_required` routing when line items fail mathematical reconciliation.
2. **Grammatical Gender & Declension in Slavic/Romance Languages:** Standard placeholder interpolation preserves numbers verbatim but does not handle grammatical case endings (e.g. in Russian or Polish). Future iterations will incorporate ICU MessageFormat for pluralization and grammatical agreement.
3. **Speech / Voice Modules:** Currently marked as `configured` or `implemented` across all 100 languages. While Web Speech API bindings are architected, local offline acoustic models (Whisper/VOSK) require dedicated hardware acceleration not mandated for Phase 1.
