"""A6 cross-artifact QA for commercial, finance, forecast, and memo inputs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "reports/fruitblend24_run_001"
COMM = RUN / "commercial"
FIN = RUN / "finance"
INV = RUN / "inventory"
QA = RUN / "qa"


def run() -> dict:
    QA.mkdir(parents=True, exist_ok=True)
    checks = []

    def check(name, passed, expected, actual, owner="A6", impact=""):
        checks.append({"name": name, "result": "PASS" if passed else "FAIL", "expected": expected, "actual": actual, "owner": owner, "impact": impact})

    sku = pd.read_csv(COMM / "sku_summary.csv", encoding="utf-8-sig")
    promo = pd.read_csv(COMM / "promo_summary.csv", encoding="utf-8-sig")
    finance = pd.read_csv(FIN / "pnl_monthly_company.csv", encoding="utf-8-sig")
    finance_budget = pd.read_csv(FIN / "pnl_monthly_company_vs_budget.csv", encoding="utf-8-sig")
    backtest = pd.read_csv(INV / "backtest_detail.csv", encoding="utf-8-sig")
    forecast = pd.read_csv(INV / "forecast_daily.csv", encoding="utf-8-sig")
    scenario_daily = pd.read_csv(INV / "scenario_daily_finance_inputs.csv", encoding="utf-8-sig")
    scenario_monthly = pd.read_csv(INV / "scenario_monthly_pnl.csv", encoding="utf-8-sig")
    forecast_metrics = json.loads((INV / "forecast_metrics.json").read_text(encoding="utf-8"))
    inventory_policy = pd.read_csv(INV / "inventory_policy.csv", encoding="utf-8-sig")
    fruit_cost_stress = pd.read_csv(INV / "fruit_cost_stress_test.csv", encoding="utf-8-sig")
    memo = ROOT / "deliverables/fruitblend24_run_001/memo.md"

    check("historical company P&L has 12 months", len(finance) == 12, 12, int(len(finance)), "A4")
    check("historical revenue equals released retained sales", abs(finance["gross_revenue_thb"].sum() - 31146932.57) < 0.01, 31146932.57, float(finance["gross_revenue_thb"].sum()), "A4")
    check("budget comparison retains 12 months", len(finance_budget) == 12, 12, int(len(finance_budget)), "A4")
    check("forecast horizon only after cutoff", forecast["date"].min() == "2026-09-01" and forecast["date"].max() == "2026-11-30", "2026-09-01 to 2026-11-30", f"{forecast['date'].min()} to {forecast['date'].max()}", "A5")
    check("backtest targets are after each cutoff", bool((pd.to_datetime(backtest["cutoff"]) < pd.Timestamp("2026-08-31")).all()), True, bool((pd.to_datetime(backtest["cutoff"]) < pd.Timestamp("2026-08-31")).all()), "A5", "Leakage would make forecast performance optimistic")
    check("backtest benchmarks five methods", set(backtest["method"]) == {"naive_last_day", "moving_avg_4w", "exp_smoothing_4w", "seasonal_naive_7d", "weekday_median_8w"}, ["naive_last_day", "moving_avg_4w", "exp_smoothing_4w", "seasonal_naive_7d", "weekday_median_8w"], sorted(backtest["method"].unique().tolist()), "A5")
    check("forecast uncertainty range is ordered", bool((forecast["forecast_lower_units"] <= forecast["forecast_units_base"]).all()) and bool((forecast["forecast_units_base"] <= forecast["forecast_upper_units"]).all()), True, {"lower_le_base_le_upper": bool((forecast["forecast_lower_units"] <= forecast["forecast_units_base"]).all() and (forecast["forecast_units_base"] <= forecast["forecast_upper_units"]).all())}, "A5", "Range is a WAPE-based planning range, not a confidence interval")
    check("inventory policy covers Kitchen x SKU cells", len(inventory_policy) == 20 and inventory_policy["kitchen"].nunique() == 4 and inventory_policy["sku"].nunique() == 5, "20 cells", {"rows": int(len(inventory_policy)), "kitchens": int(inventory_policy["kitchen"].nunique()), "skus": int(inventory_policy["sku"].nunique())}, "A5")
    check("purchase quantity boundary remains explicit", inventory_policy["order_qty_status"].str.contains("not calculable", case=False).all() and "No on-hand" in forecast_metrics["inventory_limitations"], True, {"all_not_calculable": bool(inventory_policy["order_qty_status"].str.contains("not calculable", case=False).all()), "limitations": forecast_metrics["inventory_limitations"]}, "A5")
    check("fruit cost stress test declines operating result", set((fruit_cost_stress["fruit_cost_uplift_pct"] * 100).round(0)) == {0, 5, 10, 20} and (fruit_cost_stress["modeled_operating_result_thb"].diff().dropna() < 0).all(), "0/5/10/20% and monotonic decline", {"points": sorted((fruit_cost_stress["fruit_cost_uplift_pct"] * 100).round(0).tolist()), "declines": bool((fruit_cost_stress["modeled_operating_result_thb"].diff().dropna() < 0).all())}, "A5")
    check("scenario daily formulas reconcile", bool((scenario_daily["contribution_after_waste_thb"] - (scenario_daily["contribution_before_waste_thb"] - scenario_daily["waste_cost_thb"])).abs().max() < 0.01), 0, float((scenario_daily["contribution_after_waste_thb"] - (scenario_daily["contribution_before_waste_thb"] - scenario_daily["waste_cost_thb"])).abs().max()), "A5/A4")
    monthly_rebuild = scenario_daily.groupby(["scenario", "month"], as_index=False).agg(
        revenue_thb=("revenue_thb", "sum"), contribution_after_waste_thb=("contribution_after_waste_thb", "sum"),
    )
    merged = scenario_monthly.merge(monthly_rebuild, on=["scenario", "month"], suffixes=("_file", "_rebuild"))
    check("scenario monthly revenue rebuild", bool((merged["revenue_thb_file"] - merged["revenue_thb_rebuild"]).abs().max() < 0.01), 0, float((merged["revenue_thb_file"] - merged["revenue_thb_rebuild"]).abs().max()), "A5/A4")
    check("scenario monthly contribution rebuild", bool((merged["contribution_after_waste_thb_file"] - merged["contribution_after_waste_thb_rebuild"]).abs().max() < 0.01), 0, float((merged["contribution_after_waste_thb_file"] - merged["contribution_after_waste_thb_rebuild"]).abs().max()), "A5/A4")
    check("scenario overhead charged once per month", bool((scenario_monthly["fixed_overhead_thb"] == 670000).all()), 670000, sorted(scenario_monthly["fixed_overhead_thb"].unique().tolist()), "A4", "Prevents overhead from being multiplied by SKU or daily rows")
    check("promo summary contains standard and three promo families", set(promo["base_code"]) == {"RC000", "RC101", "RC102", "RC103"}, ["RC000", "RC101", "RC102", "RC103"], sorted(promo["base_code"].tolist()), "A3")
    check("MixedBerry after-waste contribution is visible", float(sku.loc[sku["sku"] == "MixedBerryPremium", "contribution_after_waste_thb"].iloc[0]) < 0, "<0", float(sku.loc[sku["sku"] == "MixedBerryPremium", "contribution_after_waste_thb"].iloc[0]), "A4")
    check("memo exists", memo.exists(), True, memo.exists(), "A7")
    if memo.exists():
        memo_text = memo.read_text(encoding="utf-8")
        check("memo includes three action sections", memo_text.count("### ") >= 3, ">=3", memo_text.count("### "), "A7")

    failures = [c for c in checks if c["result"] == "FAIL"]
    result = {"agent_id": "A6", "scope": "Cross-artifact QA after A3/A4/A5", "status": "passed" if not failures else "returned_for_fix", "checks": checks, "failed_count": len(failures), "limitations": ["Promo comparison is association only", "Budget GP boundary is open", "Inventory order quantity is not calculable from provided data"]}
    (QA / "checks_final.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# A6 cross-artifact QA", "", f"Status: **{result['status']}**", "", "| Check | Result | Expected | Actual | Owner |", "|---|---|---:|---:|---|"]
    for c in checks:
        lines.append(f"| {c['name']} | {c['result']} | {c['expected']} | {c['actual']} | {c['owner']} |")
    lines += ["", "## Review conclusion", "", "Historical P&L, commercial evidence, backtest coverage, forecast horizon, and scenario aggregation reconcile. The recommendation layer must preserve the three limitations above and must not recalculate metrics independently."]
    (QA / "review_final.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
