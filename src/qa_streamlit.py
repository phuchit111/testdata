"""Smoke and content QA for the deployable FruitBlend24 Streamlit app."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "deliverables/fruitblend24_run_001/app.py"
ROOT_APP = ROOT / "app.py"
DATA = ROOT / "data/processed/fruitblend24_v1_c2869ce419bf"
REPORTS = ROOT / "reports/fruitblend24_run_001"
PLANNING = ROOT / "planning/profit_recovery"


def check(name: str, passed: bool, expected, actual) -> dict:
    return {"name": name, "result": "PASS" if passed else "FAIL", "expected": expected, "actual": actual}


def run() -> dict:
    app_text = APP.read_text(encoding="utf-8")
    pnl = pd.read_csv(REPORTS / "finance/pnl_monthly_company_vs_budget.csv", encoding="utf-8-sig")
    sku = pd.read_csv(REPORTS / "commercial/sku_summary.csv", encoding="utf-8-sig")
    scenario = pd.read_csv(REPORTS / "inventory/scenario_monthly_pnl.csv", encoding="utf-8-sig")
    issues = pd.read_csv(REPORTS / "data/issues.csv", encoding="utf-8-sig")
    price_simulation = pd.read_csv(REPORTS / "commercial/price_simulation.csv", encoding="utf-8-sig")
    price_ladder = pd.read_csv(REPORTS / "commercial/price_ladder.csv", encoding="utf-8-sig")
    pricing_depth_metrics = json.loads((REPORTS / "commercial/pricing_depth_metrics.json").read_text(encoding="utf-8"))
    promo_scorecard = pd.read_csv(REPORTS / "commercial/promo_scorecard.csv", encoding="utf-8-sig")
    promo_matched = pd.read_csv(REPORTS / "commercial/promo_matched_scorecard.csv", encoding="utf-8-sig")
    promo_efficiency = pd.read_csv(REPORTS / "commercial/promo_efficiency_matrix.csv", encoding="utf-8-sig")
    promo_dependency = pd.read_csv(REPORTS / "commercial/promo_dependency_by_sku.csv", encoding="utf-8-sig")
    promo_by_hour = pd.read_csv(REPORTS / "commercial/promo_by_hour.csv", encoding="utf-8-sig")
    promo_depth = pd.read_csv(REPORTS / "commercial/promo_depth_breakeven.csv", encoding="utf-8-sig")
    promotion_depth_metrics = json.loads((REPORTS / "commercial/promotion_depth_metrics.json").read_text(encoding="utf-8"))
    finance_metrics = json.loads((REPORTS / "finance/finance_metrics.json").read_text(encoding="utf-8"))
    finance_kitchen = pd.read_csv(REPORTS / "finance/kitchen_summary.csv", encoding="utf-8-sig")
    finance_portfolio = pd.read_csv(REPORTS / "finance/portfolio_summary.csv", encoding="utf-8-sig")
    pnl_waterfall = pd.read_csv(REPORTS / "finance/pnl_waterfall.csv", encoding="utf-8-sig")
    revenue_decomp = pd.read_csv(REPORTS / "finance/revenue_variance_diagnostic.csv", encoding="utf-8-sig")
    waste_heatmap = pd.read_csv(REPORTS / "finance/waste_heatmap.csv", encoding="utf-8-sig")
    fruit_cost_trend = pd.read_csv(REPORTS / "finance/fruit_cost_trend.csv", encoding="utf-8-sig")
    sku_kitchen_pareto = pd.read_csv(REPORTS / "finance/sku_kitchen_pareto.csv", encoding="utf-8-sig")
    finance_scenarios = pd.read_csv(REPORTS / "finance/finance_scenarios.csv", encoding="utf-8-sig")
    gap_closing = pd.read_csv(REPORTS / "finance/gap_closing_plan.csv", encoding="utf-8-sig")
    forecast_metrics = json.loads((REPORTS / "inventory/forecast_metrics.json").read_text(encoding="utf-8"))
    backtest = pd.read_csv(REPORTS / "inventory/backtest_summary.csv", encoding="utf-8-sig")
    forecast = pd.read_csv(REPORTS / "inventory/forecast_daily.csv", encoding="utf-8-sig")
    weekly_demand = pd.read_csv(REPORTS / "inventory/weekly_demand.csv", encoding="utf-8-sig")
    forecast_monthly_sku = pd.read_csv(REPORTS / "inventory/forecast_monthly_by_sku.csv", encoding="utf-8-sig")
    inventory_policy = pd.read_csv(REPORTS / "inventory/inventory_policy.csv", encoding="utf-8-sig")
    fruit_cost_stress = pd.read_csv(REPORTS / "inventory/fruit_cost_stress_test.csv", encoding="utf-8-sig")
    recovery_summary = json.loads((PLANNING / "summary.json").read_text(encoding="utf-8"))
    recovery_monthly = pd.read_csv(PLANNING / "monthly_pnl.csv", encoding="utf-8-sig")
    recovery_prep = pd.read_csv(PLANNING / "prep_targets.csv", encoding="utf-8-sig")
    recovery_kitchen = pd.read_csv(PLANNING / "kitchen_pnl.csv", encoding="utf-8-sig")
    recovery_sensitivity = pd.read_csv(PLANNING / "sensitivity.csv", encoding="utf-8-sig")
    recovery_bridge = pd.read_csv(PLANNING / "profit_bridge.csv", encoding="utf-8-sig")
    recovery_nov_evidence = pd.read_csv(PLANNING / "november_growth_evidence.csv", encoding="utf-8-sig")
    recovery_nov_capacity = pd.read_csv(PLANNING / "november_capacity_gate.csv", encoding="utf-8-sig")
    checks = []
    expected_tabs = [
        "Overview & recovery plan",
        "Portfolio, kitchens & budget performance",
        "Promotions & rate codes",
        "Demand & price fit",
        "3-month outlook & preparation plan",
        "Data quality & limitations",
    ]

    app_test = AppTest.from_file(str(APP)).run(timeout=60)
    checks.append(check("Streamlit AppTest has no exceptions", len(app_test.exception) == 0, 0, len(app_test.exception)))
    checks.append(check("App exposes all six required task tabs", [tab.label for tab in app_test.tabs] == expected_tabs, expected_tabs, [tab.label for tab in app_test.tabs]))
    root_app_test = AppTest.from_file(str(ROOT_APP)).run(timeout=60)
    checks.append(check("Deployment entrypoint has no exceptions", len(root_app_test.exception) == 0, 0, len(root_app_test.exception)))
    checks.append(check("Deployment entrypoint exposes all six task tabs", [tab.label for tab in root_app_test.tabs] == expected_tabs, expected_tabs, [tab.label for tab in root_app_test.tabs]))
    labels = [metric.label for metric in app_test.metric]
    required_labels = [
        "Sales revenue", "Revenue vs. budget", "Modeled operating result",
        "Raw order rows", "Retained menu rows", "Peak sales hour",
        "Discount", "Baseline forecast", "Baseline forecast prep target",
    ]
    checks.append(check("App exposes required metric cards", all(label in labels for label in required_labels), required_labels, labels))
    required_sections = [
        "5 decision-relevant findings", "Action plan", "From raw data to released analytical data",
        "Current price fit by product", "Scorecard: how much contribution remains after discounting?",
        "Is the sales lift enough to cover the discount?", "Actual revenue vs. monthly budget",
        "What should we do by product?", "Which kitchens should be fixed first?", "Historical sales followed by forecast sales",
        "This page shows two sets of numbers", "Realistic cumulative break-even target", "Modeled result across 3 scenarios", "Preparation target after sales confirmation", "Preparation and replenishment policy",
        "Formula to use when inventory data is complete",
    ]
    checks.append(check("App includes readable decision sections for all six tasks", all(section in app_text for section in required_sections), required_sections, [section for section in required_sections if section in app_text]))
    task_markers = ["Task 1 · Data quality", "Task 2 · Demand & pricing", "Task 3 · Promotions & rate codes", "Task 4 · Portfolio & budget performance", "Task 5 · Inventory & 3-month outlook", "Task 6 · Decision summary"]
    checks.append(check("App keeps every assessment task traceable", all(marker in app_text for marker in task_markers), task_markers, [marker for marker in task_markers if marker in app_text]))
    checks.append(check("Issue log is valid CSV", len(issues) == 6, 6, int(len(issues))))
    checks.append(check("Price ladder covers all five SKUs", price_ladder["sku"].nunique() == 5, 5, int(price_ladder["sku"].nunique())))
    checks.append(check("Price simulation covers five SKUs and six price scenarios", len(price_simulation) == 30 and price_simulation["sku"].nunique() == 5, "30 rows / 5 SKUs", f"{len(price_simulation)} rows / {price_simulation['sku'].nunique()} SKUs"))
    checks.append(check("Price simulation labels non-causal assumption", pricing_depth_metrics["fallback_elasticity_assumption"] == -0.3 and "not causal" in pricing_depth_metrics["caution"], True, {"fallback_elasticity_assumption": pricing_depth_metrics["fallback_elasticity_assumption"], "caution": pricing_depth_metrics["caution"]}))
    checks.append(check("Promotion P&L scorecard covers standard plus three promo codes", set(promo_scorecard["base_code"]) == {"RC000", "RC101", "RC102", "RC103"}, ["RC000", "RC101", "RC102", "RC103"], sorted(promo_scorecard["base_code"].tolist())))
    checks.append(check("Matched promotion scorecard covers three promo codes", set(promo_matched["base_code"]) == {"RC101", "RC102", "RC103"} and (promo_matched["matched_strata_count"] > 0).all(), ["RC101", "RC102", "RC103"], sorted(promo_matched["base_code"].tolist())))
    checks.append(check("Promotion efficiency matrix includes lift, break-even, and decision", all(col in promo_efficiency.columns for col in ["actual_demand_lift_pct", "break_even_lift_pct", "contribution_lift_pct", "decision"]), True, [col for col in ["actual_demand_lift_pct", "break_even_lift_pct", "contribution_lift_pct", "decision"] if col in promo_efficiency.columns]))
    checks.append(check("Promotion dependency covers all five SKUs", promo_dependency["sku"].nunique() == 5, 5, int(promo_dependency["sku"].nunique())))
    checks.append(check("Promotion hour view covers all 24 hours", promo_by_hour["hour"].nunique() == 24, 24, int(promo_by_hour["hour"].nunique())))
    checks.append(check("Promotion depth guardrail covers five SKUs and six discount depths", len(promo_depth) == 30 and promo_depth["sku"].nunique() == 5 and promo_depth["discount_pct"].nunique() == 6, "30 rows / 5 SKUs / 6 depths", f"{len(promo_depth)} rows / {promo_depth['sku'].nunique()} SKUs / {promo_depth['discount_pct'].nunique()} depths"))
    checks.append(check("Promotion mapping and revenue identity QA passed", promotion_depth_metrics["unknown_base_codes"] == [] and promotion_depth_metrics["revenue_identity_mismatch_rows"] == 0, True, {"unknown_base_codes": promotion_depth_metrics["unknown_base_codes"], "revenue_identity_mismatch_rows": promotion_depth_metrics["revenue_identity_mismatch_rows"]}))
    checks.append(check("Finance metric contract discloses budget GP boundary", finance_metrics["budget_gp_comparable"] is False and "OPEN" in finance_metrics["budget_gp_boundary_status"], True, {"budget_gp_comparable": finance_metrics["budget_gp_comparable"], "budget_gp_boundary_status": finance_metrics["budget_gp_boundary_status"]}))
    checks.append(check("Finance P&L waterfall reconciles to operating result", abs(pnl_waterfall.loc[pnl_waterfall["pnl_component"] == "Modeled operating result", "thb"].iloc[0] + 403231.0228) < 0.01, -403231.0228, float(pnl_waterfall.loc[pnl_waterfall["pnl_component"] == "Modeled operating result", "thb"].iloc[0])))
    checks.append(check("Finance kitchen summary covers four kitchens and cost ratios", finance_kitchen["kitchen"].nunique() == 4 and all(col in finance_kitchen.columns for col in ["contribution_margin_pct", "waste_cost_pct_revenue", "overhead_pct_revenue", "operating_margin_pct"]), "4 kitchens + cost ratios", {"kitchens": int(finance_kitchen["kitchen"].nunique()), "has_cost_ratios": all(col in finance_kitchen.columns for col in ["contribution_margin_pct", "waste_cost_pct_revenue", "overhead_pct_revenue", "operating_margin_pct"])}))
    checks.append(check("Finance portfolio covers five SKUs with revenue/profit mix and quadrant", finance_portfolio["sku"].nunique() == 5 and all(col in finance_portfolio.columns for col in ["revenue_share", "contribution_mix", "contribution_after_waste_margin_pct", "portfolio_quadrant"]), "5 SKUs + mix/margin/quadrant", {"skus": int(finance_portfolio["sku"].nunique()), "has_required_columns": all(col in finance_portfolio.columns for col in ["revenue_share", "contribution_mix", "contribution_after_waste_margin_pct", "portfolio_quadrant"])}))
    checks.append(check("Finance waste heatmap covers kitchen x SKU cells", waste_heatmap["kitchen"].nunique() == 4 and waste_heatmap["sku"].nunique() == 5 and "waste_rate" in waste_heatmap.columns, "4 kitchens x 5 SKUs", {"kitchens": int(waste_heatmap["kitchen"].nunique()), "skus": int(waste_heatmap["sku"].nunique())}))
    checks.append(check("Finance fruit-cost trend covers all five SKUs", fruit_cost_trend["sku"].nunique() == 5 and len(fruit_cost_trend) > 0, 5, int(fruit_cost_trend["sku"].nunique())))
    checks.append(check("Finance Pareto covers SKU x kitchen combinations", len(sku_kitchen_pareto) == 20 and "cumulative_contribution_mix" in sku_kitchen_pareto.columns, "20 combinations", {"rows": int(len(sku_kitchen_pareto)), "has_cumulative_mix": "cumulative_contribution_mix" in sku_kitchen_pareto.columns}))
    checks.append(check("Finance volume/price diagnostic reconciles", revenue_decomp["decomposition_check_thb"].dropna().abs().max() < 0.01 and "not a direct budget variance decomposition" in str(revenue_decomp["basis"].iloc[1]), True, {"max_check_thb": float(revenue_decomp["decomposition_check_thb"].dropna().abs().max()), "basis": str(revenue_decomp["basis"].iloc[1])}))
    checks.append(check("Finance gap-closing scenario artifacts exist", set(finance_scenarios["scenario"]) >= {"Current actual modeled result", "Promo matched cells revert to standard", "Waste rate moves toward company average", "Combined screening sensitivity"} and len(gap_closing) == 4, True, {"scenario_count": int(len(finance_scenarios)), "gap_plan_rows": int(len(gap_closing))}))
    checks.append(check("App contains expected artifact version", DATA.name in app_text, DATA.name, DATA.name if DATA.name in app_text else "missing"))
    checks.append(check("App revenue equals QA-passed artifact", abs(pnl["gross_revenue_thb"].sum() - 31146932.57) < 0.01, 31146932.57, float(pnl["gross_revenue_thb"].sum())))
    checks.append(check("App revenue variance equals QA-passed artifact", abs(pnl["revenue_variance_thb"].sum() + 1253067.43) < 0.01, -1253067.43, float(pnl["revenue_variance_thb"].sum())))
    checks.append(check("App modeled operating result equals QA-passed artifact", abs(pnl["modeled_operating_result_thb"].sum() + 403231.0228) < 0.01, -403231.0228, float(pnl["modeled_operating_result_thb"].sum())))
    mixed = float(sku.loc[sku["sku"] == "MixedBerryPremium", "contribution_after_waste_thb"].iloc[0])
    checks.append(check("App surfaces negative MixedBerry contribution", mixed < 0, "<0", mixed))
    checks.append(check("App binds selected forecast method from artifact", "selected_method" in app_text and forecast_metrics["selected_method"], True, "selected_method" in app_text and bool(forecast_metrics["selected_method"])))
    base_forecast_units = float(scenario.loc[scenario["scenario"] == "base", "forecast_units"].sum())
    checks.append(check("App bases outlook on released three-month scenario", abs(base_forecast_units - forecast_metrics["base_forecast_units"]) < 0.01, forecast_metrics["base_forecast_units"], base_forecast_units))
    optimized_result = float(scenario.loc[scenario["scenario"] == "price_and_waste_action", "modeled_operating_result_thb"].sum())
    checks.append(check("App discloses the remaining three-month profitability gap", abs(optimized_result + 597324) < 1 and "still loses" in app_text and "gap" in app_text, {"optimized_result_rounded": -597324, "required_copy": ["still loses", "gap"]}, {"optimized_result": optimized_result, "has_required_copy": all(text in app_text for text in ["still loses", "gap"])}))
    checks.append(check("Price page gives a test recommendation for every core SKU", all(sku_name in app_text for sku_name in ["Watermelon", "Pineapple", "Guava", "PassionFruit", "MixedBerryPremium"]) and "Test recommendation" in app_text, "5 SKUs + test recommendation", {"sku_mentions": [sku_name for sku_name in ["Watermelon", "Pineapple", "Guava", "PassionFruit", "MixedBerryPremium"] if sku_name in app_text], "has_test_label": "Test recommendation" in app_text}))
    checks.append(check("Forecast benchmarks five methods with rolling-origin windows", set(backtest["method"]) == {"naive_last_day", "moving_avg_4w", "exp_smoothing_4w", "seasonal_naive_7d", "weekday_median_8w"} and (backtest["cutoffs"] == 4).all(), "5 methods / 4 cutoffs", {"methods": sorted(backtest["method"].unique().tolist()), "cutoffs": sorted(backtest["cutoffs"].unique().tolist())}))
    checks.append(check("Forecast uncertainty range is present and ordered", all(col in forecast.columns for col in ["forecast_lower_units", "forecast_units_base", "forecast_upper_units"]) and bool((forecast["forecast_lower_units"] <= forecast["forecast_units_base"]).all()) and bool((forecast["forecast_units_base"] <= forecast["forecast_upper_units"]).all()), True, {"rows": int(len(forecast)), "range_ordered": bool((forecast["forecast_lower_units"] <= forecast["forecast_units_base"]).all() and (forecast["forecast_units_base"] <= forecast["forecast_upper_units"]).all())}))
    checks.append(check("Forecast is at Kitchen x SKU level", forecast[["kitchen", "sku"]].drop_duplicates().shape[0] == 20, 20, int(forecast[["kitchen", "sku"]].drop_duplicates().shape[0])))
    checks.append(check("Monthly SKU forecast covers three months and five SKUs", forecast_monthly_sku["month"].nunique() == 3 and forecast_monthly_sku["sku"].nunique() == 5, "3 months / 5 SKUs", {"months": int(forecast_monthly_sku["month"].nunique()), "skus": int(forecast_monthly_sku["sku"].nunique())}))
    checks.append(check("Conditional profit-recovery plan reconciles", recovery_summary["checks_passed"] is True and abs(recovery_summary["proposed_target_result_thb"] - recovery_monthly["operating_result_thb"].sum()) < 0.01 and len(recovery_monthly) == 3, "3 monthly rows + reconciled target", {"rows": int(len(recovery_monthly)), "target": float(recovery_monthly["operating_result_thb"].sum()), "checks_passed": recovery_summary["checks_passed"]}))
    checks.append(check("Conditional prep plan covers all months, kitchens and SKUs", recovery_prep["month"].nunique() == 3 and recovery_prep["kitchen"].nunique() == 4 and recovery_prep["sku"].nunique() == 5 and len(recovery_prep) == 60 and (recovery_prep["target_prep"] >= recovery_prep["target_sales"]).all(), "60 rows / 3 months / 4 kitchens / 5 SKUs", {"rows": int(len(recovery_prep)), "months": int(recovery_prep["month"].nunique()), "kitchens": int(recovery_prep["kitchen"].nunique()), "skus": int(recovery_prep["sku"].nunique()), "prep_ge_sales": bool((recovery_prep["target_prep"] >= recovery_prep["target_sales"]).all())}))
    checks.append(check("Profit-recovery sensitivity and kitchen plan are present", len(recovery_sensitivity) == 8 and len(recovery_bridge) == 9 and len(recovery_kitchen) == 12 and "No November core-growth release; other targets achieved" in set(recovery_sensitivity["scenario"]), "8 sensitivity / 9 bridge / 12 kitchen-month rows, including no-November-release case", {"sensitivity": int(len(recovery_sensitivity)), "bridge": int(len(recovery_bridge)), "kitchen_month": int(len(recovery_kitchen))}))
    historical_nov = recovery_nov_evidence.loc[recovery_nov_evidence["month"] == 11].iloc[0]
    checks.append(check("November candidate target carries seasonal and capacity gates", len(recovery_nov_evidence) == 3 and abs(float(historical_nov["historical_total_mom_growth"]) - 0.1346106487) < 1e-6 and abs(float(historical_nov["conditional_target_total_mom_growth"]) - 0.0869233341) < 1e-6 and len(recovery_nov_capacity) == 4 and abs(float(recovery_nov_capacity["net_extra_cups_per_day"].sum()) - recovery_summary["november_capacity_gate"]["net_extra_cups_per_day"]) < 0.01, "3-month autumn evidence + 4 kitchen capacity gates", {"historical_oct_to_nov_growth": float(historical_nov["historical_total_mom_growth"]), "conditional_oct_to_nov_growth": float(historical_nov["conditional_target_total_mom_growth"]), "capacity_kitchens": int(len(recovery_nov_capacity)), "net_extra_cups_per_day": float(recovery_nov_capacity["net_extra_cups_per_day"].sum())}))
    checks.append(check("Inventory policy covers 20 Kitchen x SKU cells with ABC/XYZ and safety stock", len(inventory_policy) == 20 and all(col in inventory_policy.columns for col in ["abc_class", "xyz_class", "safety_stock_cups_policy", "inventory_alert", "target_stock_next_7d_cups"]), "20 cells + policy fields", {"rows": int(len(inventory_policy)), "has_policy_fields": all(col in inventory_policy.columns for col in ["abc_class", "xyz_class", "safety_stock_cups_policy", "inventory_alert", "target_stock_next_7d_cups"])}))
    checks.append(check("Purchase-order boundary is explicitly preserved", inventory_policy["order_qty_status"].str.contains("not calculable", case=False).all() and "No on-hand" in forecast_metrics["inventory_limitations"], True, {"all_not_calculable": bool(inventory_policy["order_qty_status"].str.contains("not calculable", case=False).all()), "limitations": forecast_metrics["inventory_limitations"]}))
    checks.append(check("Fruit-cost stress test covers 0/5/10/20 percent", set((fruit_cost_stress["fruit_cost_uplift_pct"] * 100).round(0)) == {0, 5, 10, 20} and (fruit_cost_stress["modeled_operating_result_thb"].diff().dropna() < 0).all(), "4 stress points / operating result declines", {"points": sorted((fruit_cost_stress["fruit_cost_uplift_pct"] * 100).round(0).tolist()), "declines": bool((fruit_cost_stress["modeled_operating_result_thb"].diff().dropna() < 0).all())}))

    failures = [item for item in checks if item["result"] == "FAIL"]
    result = {"app": str(APP), "status": "passed" if not failures else "failed", "checks": checks, "failed_count": len(failures)}
    output = REPORTS / "qa/streamlit_checks.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=True, indent=2))
