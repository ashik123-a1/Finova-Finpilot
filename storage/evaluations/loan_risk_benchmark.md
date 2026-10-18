# Loan Matching & Underwriting Policy Audit Report
**Validation Framework:** Independent Hand-Verified Boundary Test Cases  
**Passed Cases:** 5 / 5 (100.0%)  
**Underwriting Policy:** Transparent Deterministic Rules (DSCR, DTI, Capacity)  

> [!IMPORTANT]
> **Competition Evidence & Regulatory Note:** The SME Finance Copilot implements transparent deterministic affordability underwriting rules. It intentionally does NOT claim black-box real-world credit default prediction without certified historical credit bureau datasets.

## 1. Hand-Verified Test Scenarios

| Case ID | Scenario | DSCR | Status (Actual / Expected) | Pass / Fail |
| :--- | :--- | :---: | :---: | :---: |
| **CASE-01-HEALTHY** | Healthy grocery shop with strong cash surplus and low debt. | `4.67` | `eligible` / `eligible` | `PASSED` |
| **CASE-02-BORDERLINE-DSCR** | Clothing retailer near DSCR boundary (DSCR ~ 1.15). | `1.22` | `borderline` / `borderline` | `PASSED` |
| **CASE-03-INSUFFICIENT-CASHFLOW** | Restaurant requesting loan exceeding its debt service capacity. | `0.49` | `ineligible` / `ineligible` | `PASSED` |
| **CASE-04-NEGATIVE-OPERATING-INCOME** | Loss-making business with monthly expenses exceeding revenue. | `-1.14` | `ineligible` / `ineligible` | `PASSED` |
| **CASE-05-ZERO-EXISTING-DEBT** | First-time borrower with zero existing debt obligation. | `5.72` | `eligible` / `eligible` | `PASSED` |