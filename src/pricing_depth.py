"""Deeper Task 2 demand and pricing evidence from the released sales table.

This module deliberately labels price sensitivity as directional. The case has
no randomized price assignment, customer IDs, conversion denominator, or
stockout flags, so the price scenarios are decision-support illustrations,
not causal forecasts.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_VERSION = "fruitblend24_v1_c2869ce419bf"
DATA_DIR = ROOT / "data/processed" / DATA_VERSION
OUT = ROOT / "reports/fruitblend24_run_001/commercial"


DAYPARTS = {
    "Late Night": list(range(0, 6)),
    "Morning": list(range(6, 11)),
    "Lunch": list(range(11, 15)),
    "Afternoon": list(range(15, 18)),
    "Dinner": list(range(18, 22)),
    "Late Evening": list(range(22, 24)),
}
DAYPART_ORDER = list(DAYPARTS)


def write(df: pd.DataFrame, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / name, index=False, encoding="utf-8-sig")


def _midpoint_elasticity(p1: float, p2: float, q1: float, q2: float) -> float:
    """Return midpoint elasticity, or NaN when the pair is not meaningful."""
    if min(p1, p2, q1, q2) <= 0 or p1 == p2:
        return np.nan
    return ((q2 - q1) / ((q1 + q2) / 2)) / ((p2 - p1) / ((p1 + p2) / 2))


def build() -> dict:
    sales = pd.read_csv(DATA_DIR / "sales_clean.csv", encoding="utf-8-sig")
    daily = pd.read_csv(DATA_DIR / "sales_daily.csv", encoding="utf-8-sig")
    sku_summary = pd.read_csv(OUT / "sku_summary.csv", encoding="utf-8-sig")
    price_floor = pd.read_csv(OUT / "price_floor.csv", encoding="utf-8-sig")

    sales["date"] = pd.to_datetime(sales["date"])
    sales["hour"] = pd.to_numeric(sales["hour"], errors="coerce").astype(int)
    sales["day_of_week"] = sales["date"].dt.dayofweek
    sales["month"] = sales["date"].dt.to_period("M").dt.to_timestamp()
    sales["is_weekend"] = sales["day_of_week"].isin([5, 6])
    sales["daypart"] = sales["hour"].map({hour: label for label, hours in DAYPARTS.items() for hour in hours})
    sales["date_hour"] = sales["date"].dt.strftime("%Y-%m-%d") + "|" + sales["hour"].astype(str)

    # Demand denominators count active observed dates/hours. This avoids
    # silently treating absent raw export rows as zero demand.
    day_total = sales.groupby("date", as_index=False)["units_sold"].sum().rename(columns={"units_sold": "daily_cups"})
    day_total["day_of_week"] = day_total["date"].dt.dayofweek
    weekday = day_total.groupby("day_of_week", as_index=False).agg(
        total_cups=("daily_cups", "sum"), active_days=("date", "nunique"), avg_cups_per_active_day=("daily_cups", "mean")
    )
    weekday["revenue_share"] = weekday["total_cups"] / weekday["total_cups"].sum()
    write(weekday, "weekday_demand_normalized.csv")

    hourly = sales.groupby("hour", as_index=False).agg(total_cups=("units_sold", "sum"), active_days=("date", "nunique"), active_hours=("date_hour", "nunique"))
    hourly["avg_cups_per_active_day"] = hourly["total_cups"] / hourly["active_days"]
    hourly["avg_cups_per_observed_hour"] = hourly["total_cups"] / hourly["active_hours"]
    write(hourly, "hourly_demand_normalized.csv")

    heat = sales.groupby(["day_of_week", "hour"], as_index=False).agg(total_cups=("units_sold", "sum"), active_days=("date", "nunique"))
    heat["avg_cups_per_active_day"] = heat["total_cups"] / heat["active_days"]
    write(heat, "demand_heatmap_day_hour.csv")

    daypart = sales.groupby("daypart", as_index=False).agg(
        total_cups=("units_sold", "sum"), active_days=("date", "nunique"), active_hours=("date_hour", "nunique"), revenue_thb=("gross_revenue_thb", "sum"), contribution_before_waste_thb=("contribution_before_waste_thb", "sum")
    )
    daypart["avg_cups_per_active_day"] = daypart["total_cups"] / daypart["active_days"]
    daypart["avg_cups_per_observed_hour"] = daypart["total_cups"] / daypart["active_hours"]
    daypart["contribution_per_cup_thb"] = daypart["contribution_before_waste_thb"] / daypart["total_cups"]
    daypart["daypart_order"] = daypart["daypart"].map({name: i for i, name in enumerate(DAYPART_ORDER)})
    write(daypart.sort_values("daypart_order"), "daypart_summary.csv")

    kitchen_sku = sales.groupby(["kitchen", "sku"], as_index=False).agg(
        units_sold=("units_sold", "sum"), gross_revenue_thb=("gross_revenue_thb", "sum"), contribution_before_waste_thb=("contribution_before_waste_thb", "sum"), active_days=("date", "nunique")
    )
    kitchen_sku["avg_cups_per_active_day"] = kitchen_sku["units_sold"] / kitchen_sku["active_days"]
    kitchen_sku["contribution_per_cup_thb"] = kitchen_sku["contribution_before_waste_thb"] / kitchen_sku["units_sold"]
    write(kitchen_sku, "kitchen_sku_demand.csv")

    # Price ladder: observed effective price is the post-rate-code price.
    ladder = sales.groupby(["sku", "observed_price_thb"], as_index=False).agg(
        rows=("source_row_id", "size"), units_sold=("units_sold", "sum"), gross_revenue_thb=("gross_revenue_thb", "sum"), contribution_before_waste_thb=("contribution_before_waste_thb", "sum"), active_days=("date", "nunique"), active_hours=("date_hour", "nunique"), promo_families=("base_code", "nunique")
    )
    ladder["avg_cups_per_active_hour"] = ladder["units_sold"] / ladder["active_hours"]
    ladder["realized_price_thb"] = ladder["gross_revenue_thb"] / ladder["units_sold"]
    ladder["contribution_per_cup_thb"] = ladder["contribution_before_waste_thb"] / ladder["units_sold"]
    write(ladder.sort_values(["sku", "observed_price_thb"]), "price_ladder.csv")

    sensitivity_rows: list[dict] = []
    for sku, group in ladder.groupby("sku"):
        group = group.sort_values("observed_price_thb")
        pairwise = []
        for left, right in zip(group.itertuples(index=False), group.iloc[1:].itertuples(index=False)):
            elasticity = _midpoint_elasticity(left.observed_price_thb, right.observed_price_thb, left.avg_cups_per_active_hour, right.avg_cups_per_active_hour)
            if pd.notna(elasticity):
                pairwise.append(float(elasticity))
        observed_prices = group["observed_price_thb"]
        sensitivity_rows.append({
            "sku": sku,
            "price_points": int(group["observed_price_thb"].nunique()),
            "min_observed_price_thb": float(observed_prices.min()),
            "max_observed_price_thb": float(observed_prices.max()),
            "price_cv": float(observed_prices.std(ddof=0) / observed_prices.mean()) if observed_prices.mean() else np.nan,
            "pairwise_midpoint_elasticity_median": float(np.median(pairwise)) if pairwise else np.nan,
            "pairwise_comparisons": len(pairwise),
            "interpretation": "Directional only; price is confounded with promotions, time, kitchen, platform, and season.",
        })
    sensitivity = pd.DataFrame(sensitivity_rows)
    write(sensitivity, "price_sensitivity_directional.csv")

    # Scenario grid. The observed pairwise values are reported separately, but
    # are too confounded to drive a causal forecast. Use a transparent,
    # conservative -0.30 assumption for test sizing and label it clearly.
    floors = price_floor.set_index("sku")
    skus = sku_summary.set_index("sku")
    scenario_rows: list[dict] = []
    price_changes = [-0.10, -0.05, 0.00, 0.05, 0.10, 0.15]
    for sku, row in skus.iterrows():
        observed = sensitivity.loc[sensitivity["sku"] == sku].iloc[0]
        directional = observed["pairwise_midpoint_elasticity_median"]
        elasticity_used = -0.30
        directional_text = "n/a" if pd.isna(directional) else f"{float(directional):.2f}"
        assumption_source = f"illustrative -0.30 assumption; observed directional median {directional_text} is confounded and non-causal"
        floor = floors.loc[sku]
        base_price = float(row["realized_price_thb"])
        base_units = float(row["units_sold"])
        variable_cost = float(floor["variable_cost_per_cup_before_commission"])
        commission_rate = float(floor["commission_rate_weighted"])
        waste_cost_per_sold_cup = float(row["waste_cost_thb"] / row["units_sold"])
        for price_change in price_changes:
            projected_price = base_price * (1 + price_change)
            demand_factor = max(0.0, 1 + elasticity_used * price_change)
            projected_units = base_units * demand_factor
            projected_revenue = projected_price * projected_units
            projected_contribution_before_waste = projected_revenue - projected_units * variable_cost - projected_revenue * commission_rate
            projected_contribution_after_waste = projected_contribution_before_waste - projected_units * waste_cost_per_sold_cup
            scenario_rows.append({
                "sku": sku,
                "price_change_pct": price_change,
                "projected_price_thb": projected_price,
                "elasticity_used": elasticity_used,
                "assumption_source": assumption_source,
                "demand_factor": demand_factor,
                "projected_units": projected_units,
                "projected_revenue_thb": projected_revenue,
                "projected_contribution_after_waste_thb": projected_contribution_after_waste,
                "delta_contribution_vs_current_thb": projected_contribution_after_waste - float(row["contribution_after_waste_thb"]),
            })
    scenarios = pd.DataFrame(scenario_rows)
    write(scenarios, "price_simulation.csv")
    best = scenarios.loc[scenarios.groupby("sku")["projected_contribution_after_waste_thb"].idxmax()].copy()
    write(best, "price_simulation_best_by_sku.csv")

    metrics = {
        "data_version": DATA_VERSION,
        "scope": "Task 2 normalized demand, directional price sensitivity, and contribution simulation",
        "caution": "Effective price is observed post-promotion price. Historical price variation is not randomized; directional sensitivity is not causal elasticity.",
        "daypart_order": DAYPART_ORDER,
        "price_change_grid": price_changes,
        "fallback_elasticity_assumption": -0.30,
        "heatmap_denominator": "active observed dates for each day-of-week x hour cell",
        "price_simulation_cost_policy": "Keep weighted variable cost, commission rate, and waste cost per sold cup at observed SKU levels; do not forecast overhead in the price decision.",
        "best_scenario_by_sku": best[["sku", "price_change_pct", "projected_price_thb", "projected_units", "projected_contribution_after_waste_thb", "delta_contribution_vs_current_thb", "elasticity_used", "assumption_source"]].to_dict(orient="records"),
    }
    (OUT / "pricing_depth_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
