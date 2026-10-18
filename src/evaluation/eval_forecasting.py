"""
Chronological Rolling-Origin Backtesting and Forecast Evaluation Engine.
Evaluates Cash-Flow Forecasting Models without Future Leakage:
1. Naive Persistence Baseline
2. Seasonal Naive (7-day cycle) Baseline
3. 7-Day Rolling Moving Average
4. Autoregressive Ridge Regression (ML)
Computes MAE, RMSE, MASE, and empirical 80% Confidence Interval Coverage.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
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
        """
        Loads daily aggregated net cash flows grouped by shop and business sector.
        """
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
    def run_benchmark(
        cls,
        horizon_days: int = 14,
        min_train_days: int = 60,
        step_days: int = 14,
    ) -> Dict[str, Any]:
        """
        Executes rolling-origin backtest on all shops across all models.
        """
        series_by_shop = cls.load_shop_cash_series()
        if not series_by_shop:
            raise RuntimeError("No cash movement records found. Run synthetic data generator first.")

        models = [
            "naive_persistence",
            "seasonal_naive_7d",
            "rolling_moving_average_7d",
            "autoregressive_ridge_ml",
        ]

        # Metric accumulators
        model_metrics: Dict[str, Dict[str, List[float]]] = {
            m: {"mae": [], "rmse": [], "mase": [], "coverage_80": []} for m in models
        }
        sector_mae: Dict[str, Dict[str, List[float]]] = {}

        total_folds_evaluated = 0
        actual_vs_predicted_examples: Dict[str, Any] = {}

        for s_id, s_data in series_by_shop.items():
            sector = s_data["sector"]
            if sector not in sector_mae:
                sector_mae[sector] = {m: [] for m in models}

            raw_series = s_data["daily_net_cash"]
            if len(raw_series) < min_train_days + horizon_days:
                continue

            # Generate rolling-origin folds
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

                # Model 1: Naive Persistence (last observed value)
                last_val = train_vals[-1]
                pred_naive = [last_val] * horizon_days
                mae_n = mean_absolute_error(test_vals, pred_naive)
                rmse_n = root_mean_squared_error(test_vals, pred_naive)
                mase_n = mean_absolute_scaled_error(train_vals, test_vals, pred_naive, seasonality=1)
                model_metrics["naive_persistence"]["mae"].append(mae_n)
                model_metrics["naive_persistence"]["rmse"].append(rmse_n)
                model_metrics["naive_persistence"]["mase"].append(mase_n)
                sector_mae[sector]["naive_persistence"].append(mae_n)

                # Model 2: Seasonal Naive (7-day cycle)
                pred_snaive = [train_vals[-7 + (h % 7)] for h in range(horizon_days)]
                mae_sn = mean_absolute_error(test_vals, pred_snaive)
                rmse_sn = root_mean_squared_error(test_vals, pred_snaive)
                mase_sn = mean_absolute_scaled_error(train_vals, test_vals, pred_snaive, seasonality=7)
                model_metrics["seasonal_naive_7d"]["mae"].append(mae_sn)
                model_metrics["seasonal_naive_7d"]["rmse"].append(rmse_sn)
                model_metrics["seasonal_naive_7d"]["mase"].append(mase_sn)
                sector_mae[sector]["seasonal_naive_7d"].append(mae_sn)

                # Model 3: Rolling Moving Average
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

                # Model 4: Autoregressive Ridge Regression
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

                # Save one illustrative fold example for competition visualization
                if "sample_plot" not in actual_vs_predicted_examples:
                    actual_vs_predicted_examples["sample_plot"] = {
                        "shop_id": s_id,
                        "sector": sector,
                        "horizon_days": horizon_days,
                        "actual_test_series": [round(v / 100, 2) for v in test_vals],  # Major units (BDT)
                        "naive_pred": [round(v / 100, 2) for v in pred_naive],
                        "moving_avg_pred": [round(v / 100, 2) for v in pred_ma],
                        "ridge_pred": [round(v / 100, 2) for v in pred_ridge],
                        "ridge_ci_lower_80": [round(v / 100, 2) for v in low_ridge],
                        "ridge_ci_upper_80": [round(v / 100, 2) for v in high_ridge],
                    }

        # Aggregate metrics
        summary = {
            "evaluation_task": "cashflow_forecasting",
            "backtest_method": "chronological_rolling_origin",
            "horizon_days": horizon_days,
            "min_train_days": min_train_days,
            "total_folds_evaluated": total_folds_evaluated,
            "overall_model_comparison": {
                m: {
                    "mean_mae_minor": round(float(np.mean(model_metrics[m]["mae"])), 2),
                    "mean_rmse_minor": round(float(np.mean(model_metrics[m]["rmse"])), 2),
                    "mean_mase": round(float(np.mean(model_metrics[m]["mase"])), 4),
                    "empirical_80_ci_coverage": (
                        round(float(np.mean(model_metrics[m]["coverage_80"])), 4)
                        if model_metrics[m]["coverage_80"]
                        else "N/A"
                    ),
                }
                for m in models
            },
            "performance_by_sector": {
                sec: {
                    m: round(float(np.mean(vals)), 2)
                    for m, vals in sec_models.items()
                }
                for sec, sec_models in sector_mae.items()
            },
            "visualization_sample": actual_vs_predicted_examples.get("sample_plot", {}),
        }

        cls._export_reports(summary)
        return summary

    @classmethod
    def _export_reports(cls, summary: Dict[str, Any]) -> None:
        out_dir = settings.STORAGE_DIR / "evaluations"
        out_dir.mkdir(parents=True, exist_ok=True)

        json_path = out_dir / "cashflow_forecasting_benchmark.json"
        json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

        comp = summary["overall_model_comparison"]
        md = [
            "# Cash-Flow Forecasting Benchmark Report (Rolling-Origin Backtest)",
            f"**Evaluation Horizon:** {summary['horizon_days']} days ahead  ",
            f"**Validation Strategy:** Chronological Rolling-Origin Backtesting (Zero Future Leakage)  ",
            f"**Total Backtest Folds Evaluated:** {summary['total_folds_evaluated']} folds across 9 SME sectors  ",
            "",
            "## 1. Overall Model Comparison",
            "",
            "| Model Architecture | MAE (BDT) | RMSE (BDT) | MASE | 80% CI Empirical Coverage | Status |",
            "| :--- | :---: | :---: | :---: | :---: | :---: |",
        ]

        labels = {
            "naive_persistence": ("Naive Persistence (t)", "Naive Baseline"),
            "seasonal_naive_7d": ("Seasonal Naive (t-7)", "Naive Baseline"),
            "rolling_moving_average_7d": ("7-Day Rolling Moving Average", "Statistical Baseline"),
            "autoregressive_ridge_ml": ("Autoregressive Ridge Regression", "Machine Learning"),
        }

        for m, (name, status) in labels.items():
            res = comp[m]
            mae_bdt = res["mean_mae_minor"] / 100
            rmse_bdt = res["mean_rmse_minor"] / 100
            cov_str = f"{res['empirical_80_ci_coverage']*100:.1f}%" if isinstance(res["empirical_80_ci_coverage"], float) else "N/A"
            md.append(
                f"| **{name}** | ৳ {mae_bdt:,.2f} | ৳ {rmse_bdt:,.2f} | **{res['mean_mase']:.3f}** | {cov_str} | `{status}` |"
            )

        md.append("")
        md.append("> [!NOTE]")
        md.append("> **MASE Interpretation:** A Mean Absolute Scaled Error (MASE) < 1.0 indicates that the model produces smaller forecast errors than an in-sample naive persistence forecast.")
        md.append("")
        md.append("## 2. Forecast MAE Breakdown by SME Industry Sector (BDT)")
        md.append("")
        md.append("| Sector | Naive Persistence | 7-Day Moving Avg | Ridge Regression ML |")
        md.append("| :--- | :---: | :---: | :---: |")

        for sec, sec_res in summary["performance_by_sector"].items():
            n_bdt = sec_res.get("naive_persistence", 0) / 100
            ma_bdt = sec_res.get("rolling_moving_average_7d", 0) / 100
            r_bdt = sec_res.get("autoregressive_ridge_ml", 0) / 100
            md.append(f"| **{sec.capitalize()}** | ৳ {n_bdt:,.2f} | ৳ {ma_bdt:,.2f} | **৳ {r_bdt:,.2f}** |")

        md_path = out_dir / "cashflow_forecasting_benchmark.md"
        md_path.write_text("\n".join(md), encoding="utf-8")
        print(f"Cash-flow forecasting benchmark exported to {json_path} and {md_path}")


if __name__ == "__main__":
    CashFlowForecastingEvaluator.run_benchmark(horizon_days=14)
