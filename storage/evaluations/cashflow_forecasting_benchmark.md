# Cash-Flow Forecasting Benchmark Report (Rolling-Origin Backtest)
**Validation Protocol:** Chronological Rolling-Origin Backtesting (Zero Future Leakage)  
**Forecast Horizon:** 7 days ahead | **Total Backtest Folds:** 459 folds across 9 SME sectors

## 1. Overall Model Performance Matrix
| Model Architecture | MAE (BDT) | MAE (95% CI) | RMSE (BDT) | MASE | MASE (95% CI) | 80% CI Coverage |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Naive Persistence (Last Day)** | ৳14,469.30 | [৳13,976.83, ৳14,984.23] | ৳16,910.44 | **0.998** | [0.960, 1.040] | N/A |
| **Seasonal Naive (Last Week)** | ৳14,428.53 | [৳14,084.69, ৳14,782.17] | ৳17,337.73 | **0.989** | [0.960, 1.010] | N/A |
| **7-Day Rolling Moving Average** | ৳11,183.69 | [৳10,920.45, ৳11,453.14] | ৳13,288.90 | **0.770** | [0.750, 0.790] | 67.8% |
| **Autoregressive Ridge Regression** | ৳10,793.82 | [৳10,545.34, ৳11,061.45] | ৳12,835.38 | **0.743** | [0.730, 0.760] | 73.5% |

## 2. Sensitivity & Stress Testing Scenarios
Evaluates Autoregressive Ridge model under severe cash shortages, missing days, and windfall sales:

| Operational Stress Condition | MASE | MAE (BDT) | Stress Resilience Status |
| :--- | :---: | :---: | :--- |
| **Standard Operational Baseline** | **0.626** | ৳9,285.51 | `STABLE` |
| **Cash Shortage Shock (-70% Revenue)** | **0.332** | ৳4,992.12 | `STABLE` |
| **Sparse Data (20% Missing Days)** | **0.700** | ৳8,871.85 | `STABLE` |
| **Windfall Outlier Spike (+500% Sales)** | **0.723** | ৳12,013.89 | `STABLE` |

## 3. Forecast Error by SME Industry Sector (MAE in BDT)
| Sector | Naive Persistence | 7-Day Moving Avg | Ridge Regression ML |
| :--- | :---: | :---: | :---: |
| **Grocery** | ৳14,882.22 | ৳10,924.82 | **৳11,021.31** |
| **Clothing** | ৳15,561.12 | ৳11,490.95 | **৳10,734.90** |
| **Restaurant** | ৳14,640.93 | ৳11,141.04 | **৳10,727.84** |
| **Pharmacy** | ৳13,935.62 | ৳11,252.98 | **৳10,633.72** |
| **Electronics** | ৳14,693.06 | ৳11,199.32 | **৳10,885.06** |
| **Wholesale** | ৳14,740.12 | ৳11,961.82 | **৳11,660.41** |
| **Manufacturing** | ৳14,666.70 | ৳11,799.34 | **৳10,803.61** |
| **Service** | ৳13,328.85 | ৳10,686.69 | **৳10,632.15** |
| **Online_seller** | ৳13,775.07 | ৳10,196.21 | **৳10,045.37** |

> [!WARNING]
> **Synthetic Data Limitation Disclosure:** All cash-flow data originates from the multi-sector synthetic generator. Real-world business cash flow volatility, seasonal macroeconomic shifts, and informal credit agreements remain unverified without live SME partner data.

> Prediction-level backtest outputs are stored in `storage/evaluations/forecasting_predictions.jsonl` (3213 step observations).
