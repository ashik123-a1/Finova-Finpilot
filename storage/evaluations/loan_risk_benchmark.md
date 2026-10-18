# Transparent Loan Matching & Risk Policy Benchmark Report
**Audit Status:** `12/12 Passed` (100.0%)  
**Regulatory References:**  
- Bangladesh Bank Master Circular on SME Financing (BRPD Circular No. 04 / 2019)
- Microcredit Regulatory Authority (MRA) Rules 2010 (Section 24)

## 1. Hand-Verified Boundary Test Vector Results
| Case ID | Scenario Description | DSCR | Monthly EMI | Decision | Math Verified | Passed |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `CASE-01-HEALTHY` | Healthy grocery shop with strong cash surplus and low debt. | 4.67x | ৳22,842.37 | `ELIGIBLE` | ✅ Exact | **✅ PASSED** |
| `CASE-02-BORDERLINE-DSCR` | Clothing retailer near DSCR boundary (DSCR ~ 1.15). | 1.22x | ৳32,463.23 | `BORDERLINE` | ✅ Exact | **✅ PASSED** |
| `CASE-03-INSUFFICIENT-CASHFLOW` | Restaurant requesting loan exceeding its debt service capacity. | 0.49x | ৳45,684.74 | `INELIGIBLE` | ✅ Exact | **✅ PASSED** |
| `CASE-04-NEGATIVE-OPERATING-INCOME` | Loss-making business with monthly expenses exceeding revenue. | -1.14x | ৳17,490.30 | `INELIGIBLE` | ✅ Exact | **✅ PASSED** |
| `CASE-05-ZERO-EXISTING-DEBT` | First-time borrower with zero existing debt obligation. | 5.72x | ৳26,235.44 | `ELIGIBLE` | ✅ Exact | **✅ PASSED** |
| `CASE-06-ZERO-INCOME-SHUTDOWN` | Complete business stoppage with zero revenue. | -1.46x | ৳8,745.15 | `INELIGIBLE` | ✅ Exact | **✅ PASSED** |
| `CASE-07-ZERO-INTEREST-LOAN` | Promotional or Islamic Qard Hasan (0% interest) loan. | 7.50x | ৳10,000.00 | `ELIGIBLE` | ✅ Exact | **✅ PASSED** |
| `CASE-08-EXCESSIVE-DEBT-SERVICE-RATIO` | Proposed EMI exceeds 40% of net surplus despite positive DSCR. | 1.03x | ৳17,490.30 | `INELIGIBLE` | ✅ Exact | **✅ PASSED** |
| `CASE-09-LARGE-SCALE-CAPITAL-EXPANSION` | Large scale corporate SME loan: 10 Crore BDT (100M BDT). | 1.92x | ৳3,156,753.74 | `ELIGIBLE` | ✅ Exact | **✅ PASSED** |
| `CASE-10-MICRO-LOAN-QUICK-REPAY` | Micro-merchant inventory loan: 50k BDT for 6 months. | 3.48x | ৳8,627.42 | `ELIGIBLE` | ✅ Exact | **✅ PASSED** |
| `CASE-11-FLAT-VS-REDUCING-COMPARISON` | Verifies flat rate penalty math and effective APR calculation. | 8.67x | ৳23,072.46 | `ELIGIBLE` | ✅ Exact | **✅ PASSED** |
| `CASE-12-SUB-UNIT-DSCR-REJECTION` | Slight deficit: DSCR = 1.02 (<1.05 threshold) triggers clear rejection. | 1.02x | ৳24,006.44 | `INELIGIBLE` | ✅ Exact | **✅ PASSED** |

## 2. Policy Determinism & Fair Lending Audit
- **Zero Floating-Point Drift:** All calculations use integer minor units (Poisha) with `ROUND_HALF_UP` bankers rounding.
- **Zero Black-Box Scoring:** Underwriting decisions are 100% explainable by deterministic DSCR, debt capacity, and affordability constraints.
- **Reducing vs. Flat Rate Transparency:** The engine explicitly flags hidden APR penalties in flat-rate loan schemes (often ~1.8x stated nominal rate).

> [!WARNING]
> **Competition Evidence Disclosure:** Simulated loan products and eligibility decisions represent transparent policy verification, not verified bank commitments. No real-world loan default database exists in this repository.
