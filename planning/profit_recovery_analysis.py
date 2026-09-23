"""Conditional management targets, kept separate from the released forecasts.

Run: python planning/profit_recovery_analysis.py
All percentage changes below are proposed effective monthly targets, not estimates
of causal effects. Core growth is NET achieved demand after price/promo changes.
"""

from pathlib import Path
import json
import math

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "reports/fruitblend24_run_001/inventory"
SALES_DAILY = ROOT / "data/processed/fruitblend24_v1_c2869ce419bf/sales_daily.csv"
OUT = ROOT / "planning/profit_recovery"
CORE = ["Watermelon", "Pineapple", "Guava"]
OVERHEAD = {
    "Pattaya_Central": 180000.0,
    "Pattaya_Beach": 150000.0,
    "BKK_Sukhumvit": 200000.0,
    "BKK_Ladprao": 140000.0,
}
PARAMETERS = ["standard_price_recovery", "core_price_uplift", "fruit_cost_reduction",
              "overhead_reduction", "core_net_growth", "berry_retention",
              "waste_rate_reduction", "implementation_cost_thb"]
ASSUMPTIONS = pd.DataFrame([
    ["2026-09-01", .50, .015, .00, .05, .00, .50, .10, 20000.],
    ["2026-10-01", 1.0, .050, .05, .15, .10, .00, .20, 10000.],
    # 25.5% core growth is a rounded, operationally usable version of the
    # modeled 25.43% minimum needed for cumulative 3-month break-even.  It
    # produces about +15% total cups in November, rather than the old +23%
    # stretch target, and leaves only a small modeled buffer.
    ["2026-11-01", 1.0, .050, .05, .15, .255, .00, .25, 10000.],
], columns=["month"] + PARAMETERS)


def model(forecast, assumptions, demand_factor=1.0):
    d = forecast.merge(assumptions, on="month", validate="many_to_one")
    core = d.sku.isin(CORE)
    multiplier = 1 + core.astype(float) * d.core_net_growth
    multiplier.loc[d.sku.eq("MixedBerryPremium")] = d.loc[d.sku.eq("MixedBerryPremium"), "berry_retention"]
    d["planned_units"] = d.forecast_units_base * multiplier * demand_factor
    d["planned_price"] = (
        d.recent_realized_price_thb
        + (d.standard_price_thb - d.recent_realized_price_thb) * d.standard_price_recovery
    ) * (1 + core.astype(float) * d.core_price_uplift)
    d["planned_fruit_cost"] = d.cost_median * (1 - d.fruit_cost_reduction)
    d["planned_waste_rate"] = d.waste_rate_base * (1 - d.waste_rate_reduction)
    d["planned_prep"] = d.planned_units / (1 - d.planned_waste_rate)
    d["planned_waste_units"] = d.planned_prep - d.planned_units
    d["revenue_thb"] = d.planned_units * d.planned_price
    d["commission_thb"] = d.revenue_thb * d.commission_rate_weighted
    d["fruit_cost_thb"] = d.planned_units * d.planned_fruit_cost
    d["packaging_thb"] = d.planned_units * d.packaging_cost_per_cup_thb
    d["variable_labor_thb"] = d.planned_units * d.labor_cost_per_cup_thb
    d["waste_cost_thb"] = d.planned_waste_units * (d.planned_fruit_cost + d.packaging_cost_per_cup_thb)
    d["contribution_thb"] = (
        d.revenue_thb - d.commission_thb - d.fruit_cost_thb
        - d.packaging_thb - d.variable_labor_thb - d.waste_cost_thb
    )
    sum_cols = ["forecast_units_base", "planned_units", "planned_prep", "planned_waste_units",
                "revenue_thb", "commission_thb", "fruit_cost_thb", "packaging_thb",
                "variable_labor_thb", "waste_cost_thb", "contribution_thb"]
    monthly = d.groupby("month", as_index=False)[sum_cols].sum().merge(assumptions, on="month")
    monthly["fixed_overhead_thb"] = sum(OVERHEAD.values()) * (1 - monthly.overhead_reduction)
    monthly["operating_result_thb"] = monthly.contribution_thb - monthly.fixed_overhead_thb - monthly.implementation_cost_thb
    monthly["cumulative_result_thb"] = monthly.operating_result_thb.cumsum()
    monthly["status"] = "conditional management target; not released forecast"
    return d, monthly


def reference_assumptions(optimized=False):
    a = ASSUMPTIONS.copy()
    a.loc[:, PARAMETERS] = 0.
    a["berry_retention"] = 1.
    if optimized:
        a["standard_price_recovery"] = 1.
        a["waste_rate_reduction"] = .25
    return a


def total(forecast, assumptions, demand_factor=1.0):
    return float(model(forecast, assumptions, demand_factor)[1].operating_result_thb.sum())


def autumn_evidence(forecast, planned_daily):
    """Make the November target's seasonal basis explicit and reproducible.

    This is deliberately evidence, not a replacement forecast: only one
    comparable autumn (2025) is available and it cannot separate seasonality
    from promotion, platform, or capacity changes.
    """
    history = pd.read_csv(SALES_DAILY, encoding="utf-8-sig")
    history["date"] = pd.to_datetime(history["date"])
    historical = history.loc[
        (history.date >= "2025-09-01") & (history.date < "2025-12-01")
    ].copy()
    historical["month"] = historical.date.dt.month
    historical["is_core"] = historical.sku.isin(CORE)
    historical_total = historical.groupby("month", as_index=False).units_sold.sum().rename(
        columns={"units_sold": "historical_total_cups_2025"}
    )
    historical_core = historical.loc[historical.is_core].groupby("month", as_index=False).units_sold.sum().rename(
        columns={"units_sold": "historical_core_cups_2025"}
    )
    historical_monthly = historical_total.merge(historical_core, on="month", validate="one_to_one")
    historical_monthly["historical_total_mom_growth"] = historical_monthly.historical_total_cups_2025.pct_change()
    historical_monthly["historical_core_mom_growth"] = historical_monthly.historical_core_cups_2025.pct_change()

    forecast_monthly = forecast.copy()
    forecast_monthly["month_number"] = pd.to_datetime(forecast_monthly.month).dt.month
    forecast_total = forecast_monthly.groupby("month_number", as_index=False).forecast_units_base.sum().rename(
        columns={"month_number": "month", "forecast_units_base": "baseline_forecast_total_cups_2026"}
    )
    forecast_core = forecast_monthly.loc[forecast_monthly.sku.isin(CORE)].groupby("month_number", as_index=False).forecast_units_base.sum().rename(
        columns={"month_number": "month", "forecast_units_base": "baseline_forecast_core_cups_2026"}
    )
    forecast_monthly = forecast_total.merge(forecast_core, on="month", validate="one_to_one")

    target_monthly = planned_daily.copy()
    target_monthly["month_number"] = pd.to_datetime(target_monthly.month).dt.month
    target_total = target_monthly.groupby("month_number", as_index=False).planned_units.sum().rename(
        columns={"month_number": "month", "planned_units": "conditional_target_total_cups_2026"}
    )
    target_core = target_monthly.loc[target_monthly.sku.isin(CORE)].groupby("month_number", as_index=False).planned_units.sum().rename(
        columns={"month_number": "month", "planned_units": "conditional_target_core_cups_2026"}
    )
    target_monthly = target_total.merge(target_core, on="month", validate="one_to_one")
    target_monthly["conditional_target_total_mom_growth"] = target_monthly.conditional_target_total_cups_2026.pct_change()
    target_monthly["conditional_target_core_mom_growth"] = target_monthly.conditional_target_core_cups_2026.pct_change()
    return historical_monthly.merge(forecast_monthly, on="month").merge(target_monthly, on="month")


def build():
    f = pd.read_csv(INVENTORY / "forecast_daily.csv", encoding="utf-8-sig")
    released = pd.read_csv(INVENTORY / "scenario_monthly_pnl.csv", encoding="utf-8-sig")
    checks = {}
    # Rebuild both official baselines before evaluating new targets.
    for label, optimized in [("base", False), ("price_and_waste_action", True)]:
        _, rebuilt = model(f, reference_assumptions(optimized))
        original = released.loc[released.scenario.eq(label)].sort_values("month")
        for new_col, old_col in [("operating_result_thb", "modeled_operating_result_thb"),
                                 ("planned_prep", "prep_target_cups"),
                                 ("revenue_thb", "revenue_thb"),
                                 ("waste_cost_thb", "waste_cost_thb")]:
            error = float(np.max(np.abs(rebuilt[new_col].to_numpy() - original[old_col].to_numpy())))
            checks[f"{label}_{new_col}_max_error"] = error
            assert error < .01, (label, new_col, error)

    daily, monthly = model(f, ASSUMPTIONS)
    prep = daily.groupby(["month", "kitchen", "sku"], as_index=False).agg(
        baseline_units=("forecast_units_base", "sum"), target_sales=("planned_units", "sum"),
        target_prep=("planned_prep", "sum"), expected_waste=("planned_waste_units", "sum"),
        waste_rate_target=("planned_waste_rate", "first"), target_price=("planned_price", "first"),
        contribution_thb=("contribution_thb", "sum"),
    )
    prep["days"] = pd.to_datetime(prep.month).dt.days_in_month
    prep["daily_sales_target"] = prep.target_sales / prep.days
    prep["daily_prep_if_demand_confirmed"] = prep.target_prep / prep.days
    prep["extra_sales_vs_base"] = prep.target_sales - prep.baseline_units
    prep["contribution_per_cup"] = prep.contribution_thb / prep.target_sales.replace(0, np.nan)
    prep["basis"] = "conditional target; do not pre-produce unconfirmed growth; no purchase quantity"
    assert len(prep) == 60
    assert np.allclose(prep.target_prep - prep.target_sales, prep.expected_waste)
    assert np.allclose(prep.groupby("month").contribution_thb.sum(), monthly.contribution_thb)
    november_evidence = autumn_evidence(f, daily)
    assert november_evidence.month.tolist() == [9, 10, 11]
    november_capacity = prep.loc[prep.month.eq("2026-11-01")].groupby("kitchen", as_index=False).agg(
        baseline_total_cups=("baseline_units", "sum"),
        conditional_target_total_cups=("target_sales", "sum"),
    )
    november_core_capacity = prep.loc[
        prep.month.eq("2026-11-01") & prep.sku.isin(CORE)
    ].groupby("kitchen", as_index=False).agg(
        baseline_core_cups=("baseline_units", "sum"),
        conditional_target_core_cups=("target_sales", "sum"),
    )
    november_capacity = november_capacity.merge(november_core_capacity, on="kitchen", validate="one_to_one")
    november_capacity["net_extra_cups_per_day"] = (
        november_capacity.conditional_target_total_cups - november_capacity.baseline_total_cups
    ) / 30
    november_capacity["extra_core_cups_per_day"] = (
        november_capacity.conditional_target_core_cups - november_capacity.baseline_core_cups
    ) / 30
    assert np.isclose(november_capacity.net_extra_cups_per_day.sum(), 212.18)
    kitchen = prep.groupby(["month", "kitchen"], as_index=False).agg(
        target_sales=("target_sales", "sum"), target_prep=("target_prep", "sum"),
        contribution_thb=("contribution_thb", "sum"),
    ).merge(ASSUMPTIONS[["month", "overhead_reduction"]], on="month", validate="many_to_one")
    kitchen["fixed_overhead_thb"] = kitchen.kitchen.map(OVERHEAD) * (1 - kitchen.overhead_reduction)
    kitchen["operating_before_central_implementation_thb"] = kitchen.contribution_thb - kitchen.fixed_overhead_thb
    kitchen["basis"] = "same percent overhead-cut target by kitchen; implementation budget held centrally"
    assert np.allclose(kitchen.groupby("month").operating_before_central_implementation_thb.sum()
                       - monthly.implementation_cost_thb.to_numpy(), monthly.operating_result_thb)

    scenarios = []
    variants = [("All proposed targets achieved", ASSUMPTIONS.copy(), 1.0)]
    a = ASSUMPTIONS.copy(); a["core_net_growth"] *= .5
    variants.append(("Only half of incremental core sales achieved", a, 1.0))
    a = ASSUMPTIONS.copy(); a.loc[a.month.eq("2026-11-01"), "core_net_growth"] = 0.
    variants.append(("No November core-growth release; other targets achieved", a, 1.0))
    a = ASSUMPTIONS.copy(); a["overhead_reduction"] = 0.
    variants.append(("No fixed-cost savings achieved", a, 1.0))
    a = ASSUMPTIONS.copy(); a["fruit_cost_reduction"] = 0.
    variants.append(("No procurement savings achieved", a, 1.0))
    a = ASSUMPTIONS.copy(); a["core_price_uplift"] = 0.
    variants.append(("No additional core price uplift achieved", a, 1.0))
    a = ASSUMPTIONS.copy(); a["waste_rate_reduction"] = 0.
    variants.append(("Waste rate stays at baseline", a, 1.0))
    variants.append(("All planned sales 10 percent lower; prep adjusts", ASSUMPTIONS.copy(), .9))
    for name, assumptions, demand_factor in variants:
        profit = total(f, assumptions, demand_factor)
        scenarios.append({"scenario": name, "operating_result_thb": profit, "gap_to_zero_thb": max(0., -profit)})

    # Sequential bridge from base: all interactions recomputed, never additive
    # standalone savings. Effects are attribution-order dependent.
    current = reference_assumptions()
    prior = total(f, current)
    bridge = [{"step": "Released base forecast", "increment_thb": 0., "result_thb": prior}]
    for column in ["standard_price_recovery", "waste_rate_reduction", "berry_retention",
                   "core_price_uplift", "fruit_cost_reduction", "overhead_reduction",
                   "core_net_growth", "implementation_cost_thb"]:
        current[column] = ASSUMPTIONS[column]
        result = total(f, current)
        bridge.append({"step": column, "increment_thb": result - prior, "result_thb": result})
        prior = result
    target_result = total(f, ASSUMPTIONS)
    assert abs(prior - target_result) < .01

    # Solve final-month NET core sales target while all other assumptions hold.
    no_final_growth = ASSUMPTIONS.copy()
    no_final_growth.loc[2, "core_net_growth"] = 0.
    double_final = no_final_growth.copy()
    double_final.loc[2, "core_net_growth"] = 1.
    result_at_zero = total(f, no_final_growth)
    slope = total(f, double_final) - result_at_zero
    required_growth = max(0., -result_at_zero / slope)
    check_threshold = no_final_growth.copy()
    check_threshold.loc[2, "core_net_growth"] = required_growth
    assert abs(total(f, check_threshold)) < .01
    november_core = f.loc[f.month.eq("2026-11-01") & f.sku.isin(CORE), "forecast_units_base"].sum()
    november_history = november_evidence.loc[november_evidence.month.eq(11)].iloc[0]
    summary = {
        "status": "conditional management targets; not a guaranteed profit forecast",
        "case_period": ["2026-09-01", "2026-11-30"], "data_cutoff": "2026-08-31",
        "baseline_result_thb": total(f, reference_assumptions()),
        "released_optimized_result_thb": total(f, reference_assumptions(True)),
        "proposed_target_result_thb": target_result,
        "final_month_core_growth_needed_for_3m_breakeven": required_growth,
        "final_month_extra_core_cups_needed_for_3m_breakeven": math.ceil(november_core * required_growth),
        "final_month_core_growth_needed_for_50000_buffer": max(0., (50000. - result_at_zero) / slope),
        "november_growth_evidence": {
            "historical_period": "2025-09 to 2025-11",
            "historical_oct_to_nov_total_growth": float(november_history.historical_total_mom_growth),
            "historical_oct_to_nov_core_growth": float(november_history.historical_core_mom_growth),
            "conditional_target_oct_to_nov_total_growth": float(november_history.conditional_target_total_mom_growth),
            "conditional_target_oct_to_nov_core_growth": float(november_history.conditional_target_core_mom_growth),
            "limitation": "One historical autumn supports a seasonality hypothesis only; it cannot attribute uplift to seasonality rather than promotion, platform, price, or capacity changes.",
        },
        "november_capacity_gate": {
            "net_extra_cups_per_day": float(november_capacity.net_extra_cups_per_day.sum()),
            "extra_core_cups_per_day": float(november_capacity.extra_core_cups_per_day.sum()),
            "basis": "Candidate output versus the original forecast. Core capacity is higher than net capacity because MixedBerryPremium is paused in the candidate plan.",
        },
        "extra_cost_capacity_before_3m_loss_thb": target_result,
        "total_implementation_budget_thb": float(ASSUMPTIONS.implementation_cost_thb.sum()),
        "checks": checks, "checks_passed": True,
        "constraints": [
            "First month remains loss-making; target is non-negative cumulative 3-month operating result.",
            "Growth is net achieved sales after pricing, promo changes and cannibalization; not elasticity prediction.",
            "No substitution sales from MixedBerry pause are credited; sunk stock and disposal need verification.",
            "Procurement targets refer to usable cost per cup at constant yield and quality, not just supplier price.",
            "Variable labor, packaging, commission and waste are charged on every extra cup.",
            "Overhead cuts must be realized expenses, not deferred bills or reclassified variable labor.",
            "Overhead totals only are known; no evidence yet confirms individual savings or production capacity.",
            "Implementation budget is an assumed cap; include ads, tests, extra shifts and transition stock losses.",
            "Demand stress assumes prep adjusts; fixed prep and lost sales could produce worse losses.",
            "Daily prep targets are averages for capacity planning; update from actual demand before producing.",
            "No inventory on hand, inbound, lead time, shelf life, yield or stockouts; no purchase quantities.",
            "Calendar is the original case horizon; for a later live start load intervening actuals and reforecast.",
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for frame, filename in [(ASSUMPTIONS, "assumptions.csv"), (monthly, "monthly_pnl.csv"),
                            (prep, "prep_targets.csv"), (pd.DataFrame(scenarios), "sensitivity.csv"),
                            (pd.DataFrame(bridge), "profit_bridge.csv"), (kitchen, "kitchen_pnl.csv"),
                            (november_evidence, "november_growth_evidence.csv"),
                            (november_capacity, "november_capacity_gate.csv")]:
        frame.to_csv(OUT / filename, index=False, encoding="utf-8-sig")
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(monthly[["month", "planned_units", "planned_prep", "contribution_thb", "fixed_overhead_thb", "implementation_cost_thb", "operating_result_thb", "cumulative_result_thb"]].round(2).to_string(index=False))
    print(pd.DataFrame(scenarios).round(2).to_string(index=False))
    print(pd.DataFrame(bridge).round(2).to_string(index=False))
    print(json.dumps({key: summary[key] for key in ["proposed_target_result_thb", "final_month_core_growth_needed_for_3m_breakeven", "final_month_extra_core_cups_needed_for_3m_breakeven", "final_month_core_growth_needed_for_50000_buffer", "checks_passed"]}, indent=2))


if __name__ == "__main__":
    build()
