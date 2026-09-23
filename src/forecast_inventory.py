"""A5 leakage-safe demand forecast, cup requirements, and scenario inputs."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data/processed/fruitblend24_v1_c2869ce419bf"
COMM_DIR = ROOT / "reports/fruitblend24_run_001/commercial"
OUT = ROOT / "reports/fruitblend24_run_001/inventory"

OVERHEAD = {
    "Pattaya_Central": 180000.0,
    "Pattaya_Beach": 150000.0,
    "BKK_Sukhumvit": 200000.0,
    "BKK_Ladprao": 140000.0,
}


def write(df: pd.DataFrame, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / name, index=False, encoding="utf-8-sig")


def history_for_series(daily: pd.DataFrame, kitchen: str, sku: str, cutoff: pd.Timestamp) -> pd.DataFrame:
    return daily.loc[
        (daily["kitchen"] == kitchen)
        & (daily["sku"] == sku)
        & (daily["date"] <= cutoff)
    ].sort_values("date")


def forecast_series(history: pd.DataFrame, future_dates: pd.DatetimeIndex, method: str) -> np.ndarray:
    if history.empty:
        return np.zeros(len(future_dates))
    h = history.copy()
    h["day_of_week"] = h["date"].dt.dayofweek
    fallback = float(h["units_sold"].median())
    if method == "naive_last_day":
        return np.repeat(float(h["units_sold"].iloc[-1]), len(future_dates))
    if method == "seasonal_naive_7d":
        # Repeat the last observed 7-day profile. This preserves weekday
        # structure without using any post-cutoff observations.
        profile = h["units_sold"].tail(7).to_numpy(dtype=float)
        if len(profile) < 7:
            profile = np.resize(profile, 7)
        return np.maximum(np.resize(profile, len(future_dates)), 0)
    if method == "moving_avg_4w":
        return np.repeat(float(h["units_sold"].tail(28).mean()), len(future_dates))
    if method == "exp_smoothing_4w":
        level = float(h["units_sold"].tail(28).ewm(span=14, adjust=False).mean().iloc[-1])
        return np.repeat(level, len(future_dates))
    if method == "weekday_median_8w":
        recent = h.loc[h["date"] >= h["date"].max() - pd.Timedelta(days=55)]
        values = []
        for date in future_dates:
            same_weekday = recent.loc[recent["date"].dt.dayofweek == date.dayofweek, "units_sold"]
            values.append(float(same_weekday.median() if not same_weekday.empty else fallback))
        return np.maximum(values, 0)
    # Fixed training window at the cutoff. No actual values after cutoff enter
    # the estimate, including for later months in the forecast horizon.
    return np.repeat(fallback, len(future_dates))


def evaluate_methods(daily: pd.DataFrame) -> pd.DataFrame:
    cutoffs = [pd.Timestamp("2026-04-30"), pd.Timestamp("2026-05-31"), pd.Timestamp("2026-06-30"), pd.Timestamp("2026-07-31")]
    methods = ["naive_last_day", "moving_avg_4w", "exp_smoothing_4w", "seasonal_naive_7d", "weekday_median_8w"]
    rows = []
    series = daily[["kitchen", "sku", "date"]].drop_duplicates(["kitchen", "sku"]).to_dict("records")
    for cutoff in cutoffs:
        future_dates = pd.date_range(cutoff + pd.Timedelta(days=1), periods=28, freq="D")
        for method in methods:
            for s in series:
                history = history_for_series(daily, s["kitchen"], s["sku"], cutoff)
                target = daily.loc[
                    (daily["kitchen"] == s["kitchen"])
                    & (daily["sku"] == s["sku"])
                    & daily["date"].isin(future_dates),
                    ["date", "units_sold"],
                ].set_index("date")["units_sold"]
                if len(target) != len(future_dates):
                    continue
                pred = pd.Series(forecast_series(history, future_dates, method), index=future_dates)
                actual = target.reindex(future_dates)
                error = pred - actual
                rows.append({
                    "cutoff": cutoff.strftime("%Y-%m-%d"), "method": method, "kitchen": s["kitchen"], "sku": s["sku"],
                    "horizon_days": len(future_dates), "mae": float(error.abs().mean()),
                    "wape": float(error.abs().sum() / actual.abs().sum()) if actual.abs().sum() else np.nan,
                    "bias_pct": float(error.sum() / actual.sum()) if actual.sum() else np.nan,
                    "actual_units": float(actual.sum()), "forecast_units": float(pred.sum()),
                })
    return pd.DataFrame(rows)


def build() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    daily = pd.read_csv(DATA_DIR / "sales_daily.csv", encoding="utf-8-sig")
    daily["date"] = pd.to_datetime(daily["date"])
    daily["month"] = pd.to_datetime(daily["month"])
    daily["day_of_week"] = daily["date"].dt.dayofweek
    daily["week_start"] = daily["date"] - pd.to_timedelta(daily["date"].dt.dayofweek, unit="D")

    weekly = daily.groupby(["week_start", "kitchen", "sku"], as_index=False).agg(
        units_sold=("units_sold", "sum"), units_wasted=("units_wasted", "sum"),
        waste_cost_thb=("waste_cost_thb", "sum"),
    )
    weekly["waste_rate"] = weekly["units_wasted"] / (weekly["units_sold"] + weekly["units_wasted"])
    weekly["series_active"] = True
    write(weekly, "weekly_demand.csv")

    backtest = evaluate_methods(daily)
    method_summary = backtest.groupby("method", as_index=False).agg(
        cutoffs=("cutoff", "nunique"), series_cutoff_windows=("wape", "size"), mae=("mae", "mean"), wape=("wape", "mean"), bias_pct=("bias_pct", "mean"),
    )
    write(backtest, "backtest_detail.csv")
    write(method_summary, "backtest_summary.csv")
    selected_method = str(method_summary.sort_values("wape").iloc[0]["method"])
    selected_wape = float(method_summary.sort_values("wape").iloc[0]["wape"])

    cutoff = pd.Timestamp("2026-08-31")
    future_dates = pd.date_range("2026-09-01", "2026-11-30", freq="D")
    series = daily[["kitchen", "sku"]].drop_duplicates().sort_values(["kitchen", "sku"])
    forecast_rows = []
    for s in series.to_dict("records"):
        history = history_for_series(daily, s["kitchen"], s["sku"], cutoff)
        values = forecast_series(history, future_dates, selected_method)
        for date, units in zip(future_dates, values):
            forecast_rows.append({
                "date": date.strftime("%Y-%m-%d"), "month": date.strftime("%Y-%m-01"), "kitchen": s["kitchen"], "sku": s["sku"],
                "forecast_units_base": float(units), "method": selected_method,
                "coverage_rule": "active SKU window only; historical active windows have complete daily rows; no pre-launch zero fill",
            })
    forecast = pd.DataFrame(forecast_rows)
    forecast["date"] = pd.to_datetime(forecast["date"])
    forecast["month"] = pd.to_datetime(forecast["month"])

    sales = pd.read_csv(DATA_DIR / "sales_clean.csv", encoding="utf-8-sig")
    sales["date"] = pd.to_datetime(sales["date"])
    sales["platform_code"] = sales["platform_code"].astype(str)
    recent_sales = sales.loc[sales["date"] > cutoff - pd.Timedelta(days=56)].copy()
    sku_meta = recent_sales.groupby("sku", as_index=False).agg(
        recent_realized_price_thb=("gross_revenue_thb", lambda s: np.nan),
        units=("units_sold", "sum"), revenue=("gross_revenue_thb", "sum"), commission=("commission_thb", "sum"),
    )
    sku_meta["recent_realized_price_thb"] = recent_sales.groupby("sku")["gross_revenue_thb"].sum().values / recent_sales.groupby("sku")["units_sold"].sum().values
    sku_meta["commission_rate_weighted"] = sku_meta["commission"] / sku_meta["revenue"]
    standard_sales = recent_sales.loc[recent_sales["base_code"] == "RC000"].groupby("sku").agg(std_revenue=("gross_revenue_thb", "sum"), std_units=("units_sold", "sum")).reset_index()
    standard_sales["standard_price_thb"] = standard_sales["std_revenue"] / standard_sales["std_units"]
    sku_meta = sku_meta.merge(standard_sales[["sku", "standard_price_thb"]], on="sku", how="left")

    costs = pd.read_csv(DATA_DIR / "weekly_fruit_cost.csv", encoding="utf-8-sig")
    costs["week_start"] = pd.to_datetime(costs["week_start"])
    recent_cost = costs.loc[costs["week_start"] > pd.Timestamp("2026-08-31") - pd.Timedelta(days=56)].groupby("sku")["fruit_cost_per_cup_thb"].agg(cost_median="median", cost_p90=lambda s: s.quantile(0.9)).reset_index()
    sku_meta = sku_meta.merge(recent_cost, on="sku", how="left")
    sku_meta = sku_meta.merge(daily.loc[daily["date"] > cutoff - pd.Timedelta(days=56)].groupby("sku").agg(recent_waste_units=("units_wasted", "sum"), recent_sold_units=("units_sold", "sum"), recent_waste_cost=("waste_cost_thb", "sum")).reset_index(), on="sku", how="left")
    sku_meta["waste_rate_base"] = sku_meta["recent_waste_units"] / (sku_meta["recent_waste_units"] + sku_meta["recent_sold_units"])
    sku_meta["waste_rate_low"] = sku_meta.groupby("sku")["waste_rate_base"].transform(lambda s: s)
    sku_meta["waste_rate_action"] = sku_meta["waste_rate_base"] * 0.75
    sku_meta["cost_up_pct"] = sku_meta["cost_p90"] / sku_meta["cost_median"] - 1
    assumptions = pd.read_csv(DATA_DIR / "sku_cost_assumptions.csv", encoding="utf-8-sig")
    assumptions = assumptions.loc[assumptions["sku"].isin(series["sku"].unique()), ["sku", "packaging_cost_per_cup_thb", "labor_cost_per_cup_thb"]]
    assumptions["packaging_cost_per_cup_thb"] = pd.to_numeric(assumptions["packaging_cost_per_cup_thb"], errors="coerce")
    assumptions["labor_cost_per_cup_thb"] = pd.to_numeric(assumptions["labor_cost_per_cup_thb"], errors="coerce")
    sku_meta = sku_meta.merge(assumptions, on="sku", how="left")
    forecast = forecast.merge(sku_meta[["sku", "recent_realized_price_thb", "standard_price_thb", "commission_rate_weighted", "cost_median", "cost_p90", "waste_rate_base", "waste_rate_action", "packaging_cost_per_cup_thb", "labor_cost_per_cup_thb"]], on="sku", how="left", validate="many_to_one")
    forecast["standard_price_thb"] = forecast["standard_price_thb"].fillna(forecast["recent_realized_price_thb"])
    forecast["waste_rate_base"] = forecast["waste_rate_base"].fillna(0)
    forecast["waste_rate_action"] = forecast["waste_rate_action"].fillna(forecast["waste_rate_base"] * 0.75)
    forecast["cost_up_pct"] = forecast["cost_p90"] / forecast["cost_median"] - 1
    forecast["cost_up_pct"] = forecast["cost_up_pct"].replace([np.inf, -np.inf], np.nan).fillna(0)
    forecast["forecast_lower_units"] = (forecast["forecast_units_base"] * (1 - selected_wape)).clip(lower=0)
    forecast["forecast_upper_units"] = forecast["forecast_units_base"] * (1 + selected_wape)
    forecast["prep_target_cups_base"] = forecast["forecast_units_base"] / (1 - forecast["waste_rate_base"].clip(upper=0.95))
    forecast["prep_target_cups_lower"] = forecast["forecast_lower_units"] / (1 - forecast["waste_rate_base"].clip(upper=0.95))
    forecast["prep_target_cups_upper"] = forecast["forecast_upper_units"] / (1 - forecast["waste_rate_base"].clip(upper=0.95))
    forecast["expected_waste_units_base"] = forecast["prep_target_cups_base"] - forecast["forecast_units_base"]
    write(forecast, "forecast_daily.csv")

    # Scenario P&L. Each row is still at kitchen x SKU x day so finance can
    # aggregate with the same formula order used for history.
    scenarios = []
    for label in ["base", "downside", "price_and_waste_action"]:
        f = forecast.copy()
        if label == "downside":
            f["units"] = f["forecast_units_base"] * max(0, 1 - selected_wape)
            f["price"] = f["recent_realized_price_thb"]
            f["fruit_cost"] = f["cost_p90"]
            f["waste_rate"] = (f["waste_rate_base"] * 1.25).clip(upper=0.95)
        elif label == "price_and_waste_action":
            f["units"] = f["forecast_units_base"]
            f["price"] = f["standard_price_thb"]
            f["fruit_cost"] = f["cost_median"]
            f["waste_rate"] = f["waste_rate_action"]
        else:
            f["units"] = f["forecast_units_base"]
            f["price"] = f["recent_realized_price_thb"]
            f["fruit_cost"] = f["cost_median"]
            f["waste_rate"] = f["waste_rate_base"]
        f["scenario"] = label
        f["revenue_thb"] = f["units"] * f["price"]
        f["sold_fruit_cost_thb"] = f["units"] * f["fruit_cost"]
        f["sold_packaging_cost_thb"] = f["units"] * f["packaging_cost_per_cup_thb"]
        f["sold_labor_cost_thb"] = f["units"] * f["labor_cost_per_cup_thb"]
        f["commission_thb"] = f["revenue_thb"] * f["commission_rate_weighted"]
        f["product_margin_thb"] = f["revenue_thb"] - f["sold_fruit_cost_thb"] - f["sold_packaging_cost_thb"] - f["sold_labor_cost_thb"]
        f["contribution_before_waste_thb"] = f["product_margin_thb"] - f["commission_thb"]
        f["prep_target_cups"] = f["units"] / (1 - f["waste_rate"].clip(upper=0.95))
        f["expected_waste_units"] = f["prep_target_cups"] - f["units"]
        f["waste_cost_thb"] = f["expected_waste_units"] * (f["fruit_cost"] + f["packaging_cost_per_cup_thb"])
        f["contribution_after_waste_thb"] = f["contribution_before_waste_thb"] - f["waste_cost_thb"]
        scenarios.append(f[["date", "month", "kitchen", "sku", "scenario", "units", "price", "fruit_cost", "packaging_cost_per_cup_thb", "revenue_thb", "sold_fruit_cost_thb", "sold_packaging_cost_thb", "sold_labor_cost_thb", "commission_thb", "product_margin_thb", "contribution_before_waste_thb", "waste_rate", "prep_target_cups", "expected_waste_units", "waste_cost_thb", "contribution_after_waste_thb"]])
    scenario_daily = pd.concat(scenarios, ignore_index=True)
    scenario_daily["month"] = pd.to_datetime(scenario_daily["month"])
    write(scenario_daily, "scenario_daily_finance_inputs.csv")

    scenario_monthly = scenario_daily.groupby(["scenario", "month"], as_index=False).agg(
        forecast_units=("units", "sum"), revenue_thb=("revenue_thb", "sum"), sold_fruit_cost_thb=("sold_fruit_cost_thb", "sum"),
        sold_packaging_cost_thb=("sold_packaging_cost_thb", "sum"), sold_labor_cost_thb=("sold_labor_cost_thb", "sum"), commission_thb=("commission_thb", "sum"),
        product_margin_thb=("product_margin_thb", "sum"), contribution_before_waste_thb=("contribution_before_waste_thb", "sum"), expected_waste_units=("expected_waste_units", "sum"),
        waste_cost_thb=("waste_cost_thb", "sum"), contribution_after_waste_thb=("contribution_after_waste_thb", "sum"), prep_target_cups=("prep_target_cups", "sum"),
    )
    overhead_monthly = pd.DataFrame({"month": pd.to_datetime(["2026-09-01", "2026-10-01", "2026-11-01"]), "fixed_overhead_thb": [sum(OVERHEAD.values())] * 3})
    scenario_monthly = scenario_monthly.merge(overhead_monthly, on="month", how="left", validate="many_to_one")
    scenario_monthly["modeled_operating_result_thb"] = scenario_monthly["contribution_after_waste_thb"] - scenario_monthly["fixed_overhead_thb"]
    scenario_monthly["contribution_after_waste_margin_pct"] = scenario_monthly["contribution_after_waste_thb"] / scenario_monthly["revenue_thb"]
    scenario_monthly["operating_margin_pct"] = scenario_monthly["modeled_operating_result_thb"] / scenario_monthly["revenue_thb"]
    scenario_monthly["scenario_display"] = scenario_monthly["scenario"].map({"base": "Base case", "downside": "Downside case", "price_and_waste_action": "Optimized case"})
    write(scenario_monthly, "scenario_monthly_pnl.csv")

    forecast_monthly_sku = forecast.groupby(["month", "sku"], as_index=False).agg(
        forecast_units=("forecast_units_base", "sum"), lower_units=("forecast_lower_units", "sum"),
        upper_units=("forecast_upper_units", "sum"), prep_target_cups=("prep_target_cups_base", "sum"),
        expected_waste_units=("expected_waste_units_base", "sum"),
    )
    write(forecast_monthly_sku, "forecast_monthly_by_sku.csv")

    # Kitchen x SKU inventory policy. The 95% service level and seven-day
    # review window are operating assumptions, not facts from the workbook.
    recent_weekly = weekly.loc[weekly["week_start"] <= cutoff - pd.Timedelta(days=1)].copy()
    recent_weekly = recent_weekly.sort_values("week_start").groupby(["kitchen", "sku"], group_keys=False).tail(12)
    policy = recent_weekly.groupby(["kitchen", "sku"], as_index=False).agg(
        avg_weekly_demand_cups=("units_sold", "mean"), weekly_std_cups=("units_sold", "std"),
        weeks_observed=("units_sold", "size"),
    )
    policy["weekly_std_cups"] = policy["weekly_std_cups"].fillna(0)
    policy["demand_cv"] = policy["weekly_std_cups"] / policy["avg_weekly_demand_cups"].replace(0, np.nan)
    policy["demand_cv"] = policy["demand_cv"].fillna(0)
    recent_waste = daily.loc[daily["date"] > cutoff - pd.Timedelta(days=56)].groupby(["kitchen", "sku"], as_index=False).agg(
        recent_sold_cups=("units_sold", "sum"), recent_waste_cups=("units_wasted", "sum"), recent_waste_cost_thb=("waste_cost_thb", "sum"),
    )
    recent_waste["waste_rate"] = recent_waste["recent_waste_cups"] / (recent_waste["recent_sold_cups"] + recent_waste["recent_waste_cups"])
    policy = policy.merge(recent_waste, on=["kitchen", "sku"], how="left", validate="one_to_one")
    policy["waste_rate"] = policy["waste_rate"].fillna(0)
    base_daily = scenario_daily.loc[scenario_daily["scenario"] == "base"]
    contribution = base_daily.groupby(["kitchen", "sku"], as_index=False).agg(
        forecast_3m_cups=("units", "sum"), contribution_after_waste_thb=("contribution_after_waste_thb", "sum"),
        expected_waste_3m_cups=("expected_waste_units", "sum"), prep_target_3m_cups=("prep_target_cups", "sum"),
    )
    contribution["contribution_after_waste_per_cup_thb"] = contribution["contribution_after_waste_thb"] / contribution["forecast_3m_cups"].replace(0, np.nan)
    policy = policy.merge(contribution, on=["kitchen", "sku"], how="left", validate="one_to_one")
    policy["next_7d_forecast_cups"] = forecast.loc[forecast["date"] < pd.Timestamp("2026-09-08")].groupby(["kitchen", "sku"])["forecast_units_base"].sum().reindex(pd.MultiIndex.from_frame(policy[["kitchen", "sku"]])).to_numpy()
    policy["next_7d_forecast_cups"] = pd.Series(policy["next_7d_forecast_cups"]).fillna(0).to_numpy()
    policy["abc_class"] = "C"
    positive_total = policy["contribution_after_waste_thb"].clip(lower=0).sum()
    ranked = policy["contribution_after_waste_thb"].clip(lower=0).sort_values(ascending=False)
    cumulative = ranked.cumsum() / positive_total if positive_total else ranked * 0
    abc_map = {}
    for idx, share in cumulative.items():
        abc_map[idx] = "A" if share <= 0.80 or len(abc_map) == 0 else ("B" if share <= 0.95 else "C")
    policy["abc_class"] = policy.index.map(abc_map).fillna("C")
    policy["xyz_class"] = np.select([policy["demand_cv"] <= 0.25, policy["demand_cv"] <= 0.50], ["X", "Y"], default="Z")
    policy["service_level_assumption"] = 0.95
    policy["z_value_assumption"] = 1.65
    policy["review_period_days_assumption"] = 7
    policy["safety_stock_cups_policy"] = policy["z_value_assumption"] * policy["weekly_std_cups"]
    policy["target_stock_next_7d_cups"] = policy["next_7d_forecast_cups"] + policy["safety_stock_cups_policy"]
    company_waste_rate = float(daily["units_wasted"].sum() / (daily["units_sold"].sum() + daily["units_wasted"].sum()))
    policy["waste_flag"] = np.where(policy["waste_rate"] > company_waste_rate, "above company average", "at/below company average")
    policy["inventory_alert"] = np.select(
        [
            (policy["contribution_after_waste_per_cup_thb"] < 0) & (policy["waste_rate"] > company_waste_rate),
            policy["waste_rate"] > company_waste_rate,
            policy["demand_cv"] > 0.50,
        ],
        ["RED: loss + high waste", "AMBER: high waste", "AMBER: volatile demand"],
        default="GREEN: stable policy",
    )
    policy["inventory_policy"] = np.select(
        [policy["abc_class"].eq("A") & policy["xyz_class"].eq("X"), policy["waste_rate"] > company_waste_rate, policy["demand_cv"] > 0.50],
        ["High availability; weekly rolling forecast", "Smaller/more frequent prep; tighten waste controls", "Frequent review; conservative safety stock"],
        default="Weekly rolling forecast with standard buffer",
    )
    policy["order_qty_status"] = "not calculable: on-hand, inbound, supplier lead time, shelf life and BOM/yield not provided"
    policy["policy_basis"] = "95% service-level scenario; 7-day review; Z=1.65; use for prep target, not purchase order"
    write(policy.sort_values(["inventory_alert", "contribution_after_waste_thb"], ascending=[True, False]), "inventory_policy.csv")

    # Fruit-cost stress test: hold base-case demand, prices, waste rate and
    # overhead constant while increasing fruit cost by explicit percentages.
    stress_rows = []
    for uplift in [0.00, 0.05, 0.10, 0.20]:
        f = base_daily.copy()
        f["stressed_fruit_cost_thb"] = f["sold_fruit_cost_thb"] * (1 + uplift)
        f["stressed_waste_cost_thb"] = f["expected_waste_units"] * (f["fruit_cost"] * (1 + uplift) + f["packaging_cost_per_cup_thb"])
        f["stressed_contribution_after_waste_thb"] = f["revenue_thb"] - f["stressed_fruit_cost_thb"] - f["sold_packaging_cost_thb"] - f["sold_labor_cost_thb"] - f["commission_thb"] - f["stressed_waste_cost_thb"]
        row = {
            "fruit_cost_uplift_pct": uplift, "forecast_units": f["units"].sum(), "revenue_thb": f["revenue_thb"].sum(),
            "fruit_cost_thb": f["stressed_fruit_cost_thb"].sum(), "waste_cost_thb": f["stressed_waste_cost_thb"].sum(),
            "contribution_after_waste_thb": f["stressed_contribution_after_waste_thb"].sum(),
            "fixed_overhead_thb": sum(OVERHEAD.values()) * 3,
        }
        row["modeled_operating_result_thb"] = row["contribution_after_waste_thb"] - row["fixed_overhead_thb"]
        row["operating_margin_pct"] = row["modeled_operating_result_thb"] / row["revenue_thb"]
        stress_rows.append(row)
    write(pd.DataFrame(stress_rows), "fruit_cost_stress_test.csv")

    # Requirements are intentionally cup-based. Purchase quantity remains
    # unavailable because on-hand, inbound, BOM/yield, lead time and shelf life
    # are absent from the case.
    requirements = forecast[["date", "month", "kitchen", "sku", "forecast_units_base", "forecast_lower_units", "forecast_upper_units", "waste_rate_base", "prep_target_cups_lower", "prep_target_cups_base", "prep_target_cups_upper", "expected_waste_units_base"]].copy()
    requirements["usable_on_hand_cups"] = np.nan
    requirements["usable_inbound_cups"] = np.nan
    requirements["lead_time_days"] = np.nan
    requirements["review_period_days"] = np.nan
    requirements["safety_stock_cups"] = np.nan
    requirements["order_qty_cups"] = np.nan
    requirements["order_qty_status"] = "not calculable: missing on-hand, inbound, lead time, shelf life, BOM/yield"
    write(requirements, "cup_requirements.csv")

    metrics = {
        "scope": "A5 leakage-safe forecast and inventory policy",
        "data_version": "fruitblend24_v1_c2869ce419bf",
        "cutoff": "2026-08-31",
        "forecast_period": ["2026-09-01", "2026-11-30"],
        "selected_method": selected_method,
        "selected_method_mean_wape": selected_wape,
        "methods_evaluated": sorted(backtest["method"].unique().tolist()),
        "backtest_cutoffs": sorted(backtest["cutoff"].unique().tolist()),
        "coverage_rule": "Fill zero only within each SKU x kitchen active window; observed daily rows cover every date in those active windows. Do not create pre-launch MixedBerryPremium zeros.",
        "forecast_uncertainty_basis": "Lower/upper cup range uses selected-method mean rolling-origin WAPE around each point forecast; it is a planning range, not a statistical confidence interval.",
        "commission_basis": "Recent 56-day SKU-weighted platform commission mix; future platform mix shift is not modeled.",
        "mixedberry_note": "MixedBerryPremium is a recent launch with a shorter active history; no pre-launch zero fill is used, and its forecast carries higher decision risk despite the same error-range framework.",
        "inventory_policy_assumptions": {"service_level": 0.95, "z_value": 1.65, "review_period_days": 7, "abc_basis": "positive contribution after waste", "xyz_basis": "recent 12-week demand CV; X <=25%, Y <=50%, Z >50%"},
        "base_forecast_units": float(forecast["forecast_units_base"].sum()),
        "base_forecast_lower_units": float(forecast["forecast_lower_units"].sum()),
        "base_forecast_upper_units": float(forecast["forecast_upper_units"].sum()),
        "scenario_basis": {
            "base": "selected forecast, recent realized price, recent median fruit cost, recent waste rate",
            "downside": "demand reduced by mean backtest WAPE, fruit cost at recent p90, waste rate 1.25x recent",
            "price_and_waste_action": "same demand, standard-code realized price, recent median cost, waste rate reduced by 25%; no causal demand uplift assumed",
        },
        "inventory_limitations": ["No on-hand", "No inbound", "No lead time", "No shelf life", "No BOM/yield", "No stockout flags"],
    }
    (OUT / "forecast_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
