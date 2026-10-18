# Cash-Flow Forecasting Benchmark Report (Rolling-Origin Backtest)
**Evaluation Horizon:** 14 days ahead  
**Validation Strategy:** Chronological Rolling-Origin Backtesting (Zero Future Leakage)  
**Total Backtest Folds Evaluated:** 216 folds across 9 SME sectors  

## 1. Overall Model Comparison

| Model Architecture | MAE (BDT) | RMSE (BDT) | MASE | 80% CI Empirical Coverage | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Naive Persistence (t)** | ৳ 14,541.51 | ৳ 17,128.61 | **1.003** | N/A | `Naive Baseline` |
| **Seasonal Naive (t-7)** | ৳ 14,473.82 | ৳ 17,572.02 | **0.993** | N/A | `Naive Baseline` |
| **7-Day Rolling Moving Average** | ৳ 11,148.68 | ৳ 13,449.36 | **0.769** | 66.9% | `Statistical Baseline` |
| **Autoregressive Ridge Regression** | ৳ 10,730.29 | ৳ 12,938.65 | **0.740** | 73.6% | `Machine Learning` |

> [!NOTE]
> **MASE Interpretation:** A Mean Absolute Scaled Error (MASE) < 1.0 indicates that the model produces smaller forecast errors than an in-sample naive persistence forecast.

## 2. Forecast MAE Breakdown by SME Industry Sector (BDT)

| Sector | Naive Persistence | 7-Day Moving Avg | Ridge Regression ML |
| :--- | :---: | :---: | :---: |
| **Grocery** | ৳ 14,540.04 | ৳ 10,942.16 | **৳ 10,599.47** |
| **Clothing** | ৳ 14,757.46 | ৳ 10,795.87 | **৳ 10,513.97** |
| **Restaurant** | ৳ 14,745.82 | ৳ 10,756.02 | **৳ 10,536.45** |
| **Pharmacy** | ৳ 13,627.62 | ৳ 10,754.32 | **৳ 10,573.95** |
| **Electronics** | ৳ 15,023.85 | ৳ 11,532.18 | **৳ 10,773.11** |
| **Wholesale** | ৳ 15,139.21 | ৳ 12,468.34 | **৳ 11,824.96** |
| **Manufacturing** | ৳ 15,049.44 | ৳ 11,520.39 | **৳ 10,849.04** |
| **Service** | ৳ 14,996.63 | ৳ 11,248.85 | **৳ 10,732.30** |
| **Online_seller** | ৳ 12,993.46 | ৳ 10,319.96 | **৳ 10,169.36** |