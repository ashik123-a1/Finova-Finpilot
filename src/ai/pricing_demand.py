"""
Demand Estimation, Inventory Safety Stock, and Price Elasticity Optimization Engine.
Provides deterministic operations-research calculations for reorder points, safety stock,
and price sensitivity analysis.
"""

from __future__ import annotations

import math
from typing import Dict, Any, Tuple
from decimal import Decimal, ROUND_HALF_UP


class DemandAndPricingEngine:
    """Calculates inventory replenishment policies and price change impacts."""

    # Standard Z-scores for target service levels (cycle service level)
    SERVICE_LEVEL_Z = {
        0.80: 0.8416,
        0.85: 1.0364,
        0.90: 1.2816,
        0.95: 1.6449,
        0.98: 2.0537,
        0.99: 2.3263,
    }

    @classmethod
    def calculate_safety_stock_and_reorder_point(
        cls,
        daily_demand_mean: float,
        daily_demand_std: float,
        lead_time_days: int = 7,
        service_level: float = 0.95,
        annual_demand_units: float = 1000.0,
        order_cost_minor: int = 50_00,       # 50.00 BDT per order placement
        holding_cost_annual_minor: int = 10_00, # 10.00 BDT per unit per year
    ) -> Dict[str, Any]:
        """
        Calculates Safety Stock (SS), Reorder Point (ROP), and Economic Order Quantity (EOQ).
        """
        if daily_demand_mean < 0 or lead_time_days <= 0:
            raise ValueError("Demand mean and lead time must be non-negative.")

        # Find closest z-score
        z = cls.SERVICE_LEVEL_Z.get(service_level, 1.6449)

        # Safety Stock = z * sqrt(LeadTime) * DemandStd
        safety_stock = math.ceil(z * math.sqrt(lead_time_days) * daily_demand_std)

        # Lead time demand = LeadTime * DemandMean
        lead_time_demand = math.ceil(lead_time_days * daily_demand_mean)

        # Reorder Point = LeadTimeDemand + SafetyStock
        reorder_point = lead_time_demand + safety_stock

        # Economic Order Quantity (EOQ) = sqrt(2 * D * S / H)
        if holding_cost_annual_minor > 0 and annual_demand_units > 0:
            eoq = math.ceil(
                math.sqrt((2.0 * annual_demand_units * order_cost_minor) / holding_cost_annual_minor)
            )
        else:
            eoq = math.ceil(daily_demand_mean * 14)  # 2-week supply heuristic

        return {
            "daily_demand_mean": daily_demand_mean,
            "daily_demand_std": daily_demand_std,
            "lead_time_days": lead_time_days,
            "service_level": service_level,
            "z_score": z,
            "lead_time_demand_units": lead_time_demand,
            "safety_stock_units": safety_stock,
            "reorder_point_units": reorder_point,
            "economic_order_quantity_units": eoq,
            "stockout_risk_pct": round((1.0 - service_level) * 100, 2),
        }

    @classmethod
    def estimate_price_elasticity_and_impact(
        cls,
        current_price_minor: int,
        proposed_price_minor: int,
        unit_cost_minor: int,
        current_monthly_units: float,
        price_elasticity: float = -1.5,
    ) -> Dict[str, Any]:
        """
        Estimates volume, revenue, and gross profit change from proposed price adjustment.
        % Delta Q = Elasticity * % Delta P
        """
        if current_price_minor <= 0 or proposed_price_minor <= 0:
            raise ValueError("Prices must be strictly positive.")

        price_change_pct = (proposed_price_minor - current_price_minor) / current_price_minor
        projected_volume_change_pct = price_elasticity * price_change_pct
        projected_units = max(0.0, current_monthly_units * (1.0 + projected_volume_change_pct))

        # Current financials
        current_revenue = int(round(current_monthly_units * current_price_minor))
        current_cost = int(round(current_monthly_units * unit_cost_minor))
        current_gross_profit = current_revenue - current_cost

        # Projected financials
        projected_revenue = int(round(projected_units * proposed_price_minor))
        projected_cost = int(round(projected_units * unit_cost_minor))
        projected_gross_profit = projected_revenue - projected_cost

        profit_delta_minor = projected_gross_profit - current_gross_profit
        is_profitable = profit_delta_minor > 0

        # Required volume change to break even on price cut
        current_unit_margin = current_price_minor - unit_cost_minor
        proposed_unit_margin = proposed_price_minor - unit_cost_minor

        if proposed_unit_margin > 0 and current_unit_margin > 0:
            breakeven_volume_factor = current_unit_margin / proposed_unit_margin
            breakeven_units = round(current_monthly_units * breakeven_volume_factor, 1)
        else:
            breakeven_units = float("inf")

        recommendation = "favorable" if is_profitable else "unfavorable"
        risk_warning = None
        if proposed_price_minor < current_price_minor and not is_profitable:
            risk_warning = (
                f"Margin erosion risk: The {abs(price_change_pct)*100:.1f}% price cut requires selling at least "
                f"{breakeven_units:.0f} units (vs current {current_monthly_units:.0f}) to avoid profit loss."
            )

        return {
            "current_price_minor": current_price_minor,
            "proposed_price_minor": proposed_price_minor,
            "unit_cost_minor": unit_cost_minor,
            "price_change_pct": round(price_change_pct * 100, 2),
            "current_monthly_units": current_monthly_units,
            "projected_monthly_units": round(projected_units, 1),
            "current_gross_profit_minor": current_gross_profit,
            "projected_gross_profit_minor": projected_gross_profit,
            "profit_delta_minor": profit_delta_minor,
            "is_profitable": is_profitable,
            "recommendation": recommendation,
            "breakeven_units_required": breakeven_units,
            "risk_warning": risk_warning,
        }
