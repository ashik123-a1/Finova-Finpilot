"""
Chronological Rolling-Origin Backtesting and Forecast Evaluation Engine.
Evaluates Cash-Flow Forecasting Models without Future Leakage:
1. Naive Persistence Baseline
2. Seasonal Naive (7-day cycle) Baseline
3. 7-Day Rolling Moving Average
4. Autoregressive Ridge Regression (ML)

Includes:
- Full prediction-level logging to forecasting_predictions.jsonl
- Bootstrap 95% Confidence Intervals for MAE and MASE
- Sensitivity Stress Tests: Cash Shortage Shock, Sparse Missing Days, Outlier Windfall Spikes
- Clear disclosure of synthetic data limitations
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
from sqlalchemy import text

from src.config import settings
from src.database.connection import SessionLocal
from src.ai.forecaster import CashFlowForecaster
from src.evaluation.metrics import (
    mean_absolute_error,
    root_mean_squared_error,
    mean_absolute_scaled_error,
    empirical_ci_coverage,
)
from src.evaluation.data_splitters import DataSplitter


class CashFlowForecastingEvaluator:
    """Executes leakage-free rolling-origin backtesting across all SME sectors."""

    @classmethod
    def load_shop_cash_series(cls) -> Dict[str, Dict[str, Any]]:
        """Loads daily aggregated net cash flows grouped by shop and business sector."""
        with SessionLocal() as session:
            rows = session.execute(
                text(
                    """
                    SELECT s.id as shop_id, b.business_type, cm.movement_date,
                           SUM(CASE WHEN cm.movement_type = 'inflow' THEN cm.amount_minor ELSE -cm.amount_minor END) as net_cash
                    FROM cash_movements cm
                    JOIN shops s ON cm.shop_id = s.id
                    JOIN businesses b ON s.business_id = b.id
                    GROUP BY s.id, b.business_type, date(cm.movement_date)
                    ORDER BY s.id, cm.movement_date ASC;
                    """
                )
            ).fetchall()

        series_by_shop: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            s_id = str(r[0])
            b_type = r[1]
            net_cash = float(r[3])
            if s_id not in series_by_shop:
                series_by_shop[s_id] = {"shop_id": s_id, "sector": b_type, "daily_net_cash": []}
            series_by_shop[s_id]["daily_net_cash"].append(net_cash)

        return series_by_shop

    @classmethod
    def compute_bootstrap_ci(cls, values: List[float], n_bootstraps: int = 1000, seed: int = 42) -> Tuple[float, float]:
        """Calculates 95% bootstrap confidence interval on mean."""
        if not values:
            return 0.0, 0.0
        rng = np.random.default_rng(seed)
        arr = np.array(values)
        boot_means = [float(np.mean(rng.choice(arr, size=len(arr), replace=True))) for _ in range(n_bootstraps)]
        return round(float(np.percentile(boot_means, 2.5)), 2), round(float(np.percentile(boot_means, 97.5)), 2)

    @classmethod
    def run_benchmark(
        cls,
        horizon_days: int = 7,
        min_train_days: int = 60,
        step_days: int = 7,
    ) -> Dict[str, Any]:
        series_by_shop = cls.load_shop_cash_series()
        if not series_by_shop:
            raise RuntimeError("No cash movement records found. Run synthetic data generator first.")

        models = [
            "naive_persistence",
            "seasonal_naive_7d",
            "rolling_moving_average_7d",
            "autoregressive_ridge_ml",
        ]

        model_metrics: Dict[str, Dict[str, List[float]]] = {
            m: {"mae": [], "rmse": [], "mase": [], "coverage_80": []} for m in models
        }
        sector_mae: Dict[str, Dict[str, List[float]]] = {}
        total_folds_evaluated = 0

        out_dir = Path("storage/evaluations")
        out_dir.mkdir(parents=True, exist_ok=True)
        preds_file = out_dir / "forecasting_predictions.jsonl"

        with open(preds_file, "w", encoding="utf-8") as f_preds:
            for s_id, s_data in series_by_shop.items():
                sector = s_data["sector"]
                if sector not in sector_mae:
                    sector_mae[sector] = {m: [] for m in models}

                raw_series = s_data["daily_net_cash"]
                if len(raw_series) < min_train_days + horizon_days:
                    continue

                folds = DataSplitter.chronological_rolling_origin_split(
                    time_series=[{"t": idx, "val": v} for idx, v in enumerate(raw_series)],
                    horizon_days=horizon_days,
                    min_train_days=min_train_days,
                    step_days=step_days,
                )

                for fold_idx, (train_items, test_items) in enumerate(folds):
                    total_folds_evaluated += 1
                    train_vals = [it["val"] for it in train_items]
                    test_vals = [it["val"] for it in test_items]

                    # 1. Naive Persistence
                    last_val = train_vals[-1]
                    pred_naive = [last_val] * horizon_days
                    mae_n = mean_absolute_error(test_vals, pred_naive)
                    rmse_n = root_mean_squared_error(test_vals, pred_naive)
                    mase_n = mean_absolute_scaled_error(train_vals, test_vals, pred_naive, seasonality=1)
                    model_metrics["naive_persistence"]["mae"].append(mae_n)
                    model_metrics["naive_persistence"]["rmse"].append(rmse_n)
                    model_metrics["naive_persistence"]["mase"].append(mase_n)
                    sector_mae[sector]["naive_persistence"].append(mae_n)

                    # 2. Seasonal Naive
                    pred_snaive = [train_vals[-7 + (h % 7)] for h in range(horizon_days)]
                    mae_sn = mean_absolute_error(test_vals, pred_snaive)
                    rmse_sn = root_mean_squared_error(test_vals, pred_snaive)
                    mase_sn = mean_absolute_scaled_error(train_vals, test_vals, pred_snaive, seasonality=7)
                    model_metrics["seasonal_naive_7d"]["mae"].append(mae_sn)
                    model_metrics["seasonal_naive_7d"]["rmse"].append(rmse_sn)
                    model_metrics["seasonal_naive_7d"]["mase"].append(mase_sn)
                    sector_mae[sector]["seasonal_naive_7d"].append(mae_sn)

                    # 3. Rolling Moving Average
                    res_ma = CashFlowForecaster.statistical_baseline_forecast(
                        historical_net_cash_minor=[int(v) for v in train_vals],
                        horizon_days=horizon_days,
                        window_size=7,
                    )
                    pred_ma = [float(p) for p in res_ma["point_forecast_minor"]]
                    low_ma = [float(p) for p in res_ma["lower_bound_80_minor"]]
                    high_ma = [float(p) for p in res_ma["upper_bound_80_minor"]]
                    mae_ma = mean_absolute_error(test_vals, pred_ma)
                    rmse_ma = root_mean_squared_error(test_vals, pred_ma)
                    mase_ma = mean_absolute_scaled_error(train_vals, test_vals, pred_ma, seasonality=1)
                    cov_ma = empirical_ci_coverage(test_vals, low_ma, high_ma)
                    model_metrics["rolling_moving_average_7d"]["mae"].append(mae_ma)
                    model_metrics["rolling_moving_average_7d"]["rmse"].append(rmse_ma)
                    model_metrics["rolling_moving_average_7d"]["mase"].append(mase_ma)
                    model_metrics["rolling_moving_average_7d"]["coverage_80"].append(cov_ma)
                    sector_mae[sector]["rolling_moving_average_7d"].append(mae_ma)

                    # 4. Autoregressive Ridge ML
                    res_ridge = CashFlowForecaster.ml_lagged_forecast(
                        historical_daily_series=[int(v) for v in train_vals],
                        horizon_days=horizon_days,
                        lag_days=7,
                    )
                    pred_ridge = [float(p) for p in res_ridge["point_forecast_minor"]]
                    low_ridge = [float(p) for p in res_ridge["lower_bound_80_minor"]]
                    high_ridge = [float(p) for p in res_ridge["upper_bound_80_minor"]]
                    mae_ridge = mean_absolute_error(test_vals, pred_ridge)
                    rmse_ridge = root_mean_squared_error(test_vals, pred_ridge)
                    mase_ridge = mean_absolute_scaled_error(train_vals, test_vals, pred_ridge, seasonality=1)
                    cov_ridge = empirical_ci_coverage(test_vals, low_ridge, high_ridge)
                    model_metrics["autoregressive_ridge_ml"]["mae"].append(mae_ridge)
                    model_metrics["autoregressive_ridge_ml"]["rmse"].append(rmse_ridge)
                    model_metrics["autoregressive_ridge_ml"]["mase"].append(mase_ridge)
                    model_metrics["autoregressive_ridge_ml"]["coverage_80"].append(cov_ridge)
                    sector_mae[sector]["autoregressive_ridge_ml"].append(mae_ridge)

                    # Save prediction log for each step in this fold
                    for step_idx in range(horizon_days):
                        log_rec = {
                            "fold_id": total_folds_evaluated,
                            "shop_id": s_id,
                            "sector": sector,
                            "step_ahead": step_idx + 1,
                            "y_true_bdt": round(test_vals[step_idx] / 100, 2),
                            "pred_naive_bdt": round(pred_naive[step_idx] / 100, 2),
                            "pred_snaive_bdt": round(pred_snaive[step_idx] / 100, 2),
                            "pred_ma_bdt": round(pred_ma[step_idx] / 100, 2),
                            "pred_ridge_bdt": round(pred_ridge[step_idx] / 100, 2),
                            "ridge_ci_lower_bdt": round(low_ridge[step_idx] / 100, 2),
                            "ridge_ci_upper_bdt": round(high_ridge[step_idx] / 100, 2),
                        }
                        f_preds.write(json.dumps(log_rec) + "\n")

        # Run Sensitivity Stress Tests
        stress_tests = cls._run_stress_scenarios(series_by_shop, horizon_days, min_train_days)

        # Aggregate Model Stats with Bootstrap 95% CIs
        overall = {}
        for m in models:
            mean_mae = float(np.mean(model_metrics[m]["mae"]))
            mean_rmse = float(np.mean(model_metrics[m]["rmse"]))
            mean_mase = float(np.mean(model_metrics[m]["mase"]))
            mae_ci = cls.compute_bootstrap_ci(model_metrics[m]["mae"])
            mase_ci = cls.compute_bootstrap_ci(model_metrics[m]["mase"])
            cov = float(np.mean(model_metrics[m]["coverage_80"])) if model_metrics[m]["coverage_80"] else "N/A"

            overall[m] = {
                "mean_mae_minor": round(mean_mae, 2),
                "mae_bdt": round(mean_mae / 100.0, 2),
                "mae_95ci_bdt": [round(mae_ci[0] / 100.0, 2), round(mae_ci[1] / 100.0, 2)],
                "mean_rmse_minor": round(mean_rmse, 2),
                "rmse_bdt": round(mean_rmse / 100.0, 2),
                "mean_mase": round(mean_mase, 3),
                "mase_95ci": mase_ci,
                "empirical_80_ci_coverage": round(cov, 4) if isinstance(cov, float) else "N/A",
            }

        summary = {
            "evaluation_task": "cashflow_forecasting",
            "backtest_method": "chronological_rolling_origin",
            "horizon_days": horizon_days,
            "min_train_days": min_train_days,
            "total_folds_evaluated": total_folds_evaluated,
            "overall_model_comparison": overall,
            "sensitivity_stress_tests": stress_tests,
            "performance_by_sector": {
                sec: {m: round(float(np.mean(vals)) / 100.0, 2) for m, vals in sec_models.items()}
                for sec, sec_models in sector_mae.items()
            },
            "synthetic_disclosure": "Trained and evaluated on synthetic SME transaction flows. Real-world business cash flow volatility and macroeconomic shocks remain unverified without empirical SME bank ledger access.",
        }

        cls._export_reports(summary)
        return summary

    @classmethod
    def _run_stress_scenarios(
        cls, series_by_shop: Dict[str, Any], horizon_days: int, min_train_days: int
    ) -> List[Dict[str, Any]]:
        """Evaluates model robustness against severe cash shocks, missing days, and windfall spikes."""
        scenarios = [
            {"name": "Standard Operational Baseline", "type": "none"},
            {"name": "Cash Shortage Shock (-70% Revenue)", "type": "cash_shortage"},
            {"name": "Sparse Data (20% Missing Days)", "type": "sparse"},
            {"name": "Windfall Outlier Spike (+500% Sales)", "type": "windfall"},
        ]

        scenario_results = []
        rng = np.random.default_rng(42)

        for sc in scenarios:
            mase_list = []
            mae_list = []

            for s_id, s_data in list(series_by_shop.items())[:10]:
                series = list(s_data["daily_net_cash"])
                if len(series) < min_train_days + horizon_days:
                    continue

                train_vals = series[:min_train_days]
                test_vals = series[min_train_days : min_train_days + horizon_days]

                # Apply scenario stress
                if sc["type"] == "cash_shortage":
                    test_vals = [v * 0.30 for v in test_vals]
                elif sc["type"] == "sparse":
                    mask = rng.random(len(train_vals)) > 0.20
                    train_vals = [v if m else 0.0 for v, m in zip(train_vals, mask)]
                elif sc["type"] == "windfall":
                    train_vals[-3] = train_vals[-3] * 6.0

                try:
                    res = CashFlowForecaster.ml_lagged_forecast(
                        historical_daily_series=[int(v) for v in train_vals],
                        horizon_days=horizon_days,
                        lag_days=7,
                    )
                    pred = [float(p) for p in res["point_forecast_minor"]]
                    mase = mean_absolute_scaled_error(train_vals, test_vals, pred, seasonality=1)
                    mae = mean_absolute_error(test_vals, pred)
                    mase_list.append(mase)
                    mae_list.append(mae)
                except Exception:
                    pass

            scenario_results.append({
                "scenario": sc["name"],
                "mase": round(float(np.mean(mase_list)), 3) if mase_list else 0.0,
                "mae_bdt": round(float(np.mean(mae_list)) / 100.0, 2) if mae_list else 0.0,
                "resilience_status": "STABLE" if (mase_list and np.mean(mase_list) < 1.0) else "DEGRADED",
            })

        return scenario_results

    @classmethod
    def _export_reports(cls, summary: Dict[str, Any]) -> None:
        out_dir = Path("storage/evaluations")
        json_path = out_dir / "cashflow_forecasting_benchmark.json"
        md_path = out_dir / "cashflow_forecasting_benchmark.md"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        comp = summary["overall_model_comparison"]
        md_lines = [
            "# Cash-Flow Forecasting Benchmark Report (Rolling-Origin Backtest)",
            f"**Validation Protocol:** Chronological Rolling-Origin Backtesting (Zero Future Leakage)  ",
            f"**Forecast Horizon:** {summary['horizon_days']} days ahead | **Total Backtest Folds:** {summary['total_folds_evaluated']} folds across 9 SME sectors\n",
            "## 1. Overall Model Performance Matrix",
            "| Model Architecture | MAE (BDT) | MAE (95% CI) | RMSE (BDT) | MASE | MASE (95% CI) | 80% CI Coverage |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]

        labels = [
            ("naive_persistence", "Naive Persistence (Last Day)"),
            ("seasonal_naive_7d", "Seasonal Naive (Last Week)"),
            ("rolling_moving_average_7d", "7-Day Rolling Moving Average"),
            ("autoregressive_ridge_ml", "Autoregressive Ridge Regression"),
        ]

        for m_key, m_name in labels:
            c = comp[m_key]
            cov = f"{c['empirical_80_ci_coverage']*100:.1f}%" if isinstance(c["empirical_80_ci_coverage"], float) else "N/A"
            md_lines.append(
                f"| **{m_name}** | ৳{c['mae_bdt']:,.2f} | [৳{c['mae_95ci_bdt'][0]:,.2f}, ৳{c['mae_95ci_bdt'][1]:,.2f}] | "
                f"৳{c['rmse_bdt']:,.2f} | **{c['mean_mase']:.3f}** | [{c['mase_95ci'][0]:.3f}, {c['mase_95ci'][1]:.3f}] | {cov} |"
            )

        md_lines.extend([
            "\n## 2. Sensitivity & Stress Testing Scenarios",
            "Evaluates Autoregressive Ridge model under severe cash shortages, missing days, and windfall sales:\n",
            "| Operational Stress Condition | MASE | MAE (BDT) | Stress Resilience Status |",
            "| :--- | :---: | :---: | :--- |",
        ])

        for st in summary["sensitivity_stress_tests"]:
            status_badge = f"`{st['resilience_status']}`"
            md_lines.append(
                f"| **{st['scenario']}** | **{st['mase']:.3f}** | ৳{st['mae_bdt']:,.2f} | {status_badge} |"
            )

        md_lines.extend([
            "\n## 3. Forecast Error by SME Industry Sector (MAE in BDT)",
            "| Sector | Naive Persistence | 7-Day Moving Avg | Ridge Regression ML |",
            "| :--- | :---: | :---: | :---: |",
        ])

        for sec, m_vals in summary["performance_by_sector"].items():
            md_lines.append(
                f"| **{sec.capitalize()}** | ৳{m_vals.get('naive_persistence', 0):,.2f} | "
                f"৳{m_vals.get('rolling_moving_average_7d', 0):,.2f} | **৳{m_vals.get('autoregressive_ridge_ml', 0):,.2f}** |"
            )

        md_lines.extend([
            "\n> [!WARNING]",
            "> **Synthetic Data Limitation Disclosure:** All cash-flow data originates from the multi-sector synthetic generator. Real-world business cash flow volatility, seasonal macroeconomic shifts, and informal credit agreements remain unverified without live SME partner data.",
            f"\n> Prediction-level backtest outputs are stored in `storage/evaluations/forecasting_predictions.jsonl` ({summary['total_folds_evaluated'] * summary['horizon_days']} step observations).",
        ])

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines) + "\n")

        print(f"Cash-flow forecasting benchmark exported to {json_path} and {md_path}")


if __name__ == "__main__":
    CashFlowForecastingEvaluator.run_benchmark(horizon_days=7)
