# SME Finance Copilot — Global 100-Language & Localization Evaluation Report
**Evaluation Timestamp:** 2026-10-18T04:26:31.134599+00:00 | **Languages Registered:** 100

## 1. 100-Language Registry & Capability Breakdown
- **Total Registered Languages:** 100
- **Text Directions:** 91 LTR (Left-to-Right), 9 RTL (Right-to-Left: Arabic, Urdu, Persian, Hebrew, Sindhi, Uyghur, Yiddish, Pashto, Kurdish)
- **Capability Tiers:**
  - `configured`: 69 languages
  - `evaluated`: 10 languages
  - `implemented`: 19 languages
  - `production_ready`: 2 languages

## 2. Multilingual Financial Fact Preservation (N=30 Test Executions)
| Language | Samples Tested | Samples Preserved | Fact Preservation Rate |
| :--- | :---: | :---: | :---: |
| **EN** | 5 | 5 | **100.0%** |
| **BN** | 5 | 5 | **100.0%** |
| **ZH** | 5 | 5 | **100.0%** |
| **AR** | 5 | 5 | **100.0%** |
| **ES** | 5 | 5 | **100.0%** |
| **HI** | 5 | 5 | **100.0%** |

> [!NOTE]
> **Fact Invariance Guarantee:** Financial amounts, currency symbols, invoice IDs, and transaction dates are token-interpolated AFTER catalog translation, mathematically preventing numerical corruption.

## 3. Cross-Language Financial Calculation Parity
- **Parity Verification Status:** `PASSED (100% BIT-EXACT)`
- **Invariant Verified:** Switching interface language (EN $\leftrightarrow$ BN $\leftrightarrow$ ZH $\leftrightarrow$ AR $\leftrightarrow$ ES $\leftrightarrow$ HI) causes **0 cents / 0 poisha** change in revenue, cogs, or net operating profit.

## 4. Multilingual Document Classification Benchmark (N=24 Multi-Script Samples)
- **Total Evaluated Documents:** 24 (EN, BN, ZH, AR, ES, HI)
- **Accuracy:** **100.0%** (24/24)

## 5. Multilingual Adversarial Prompt Injection Defense (N=18 Test Vectors)
- **Total Attack & Benign Prompts:** 18 across 7 languages
- **Defense Accuracy:** **100.0%** (18/18)
- **Attack Vectors Blocked:** Instruction overrides, unauthorized loan approval triggers, database formatting, and security check bypasses in English, Bengali, Chinese, Arabic, Russian, Spanish, and Hindi.

