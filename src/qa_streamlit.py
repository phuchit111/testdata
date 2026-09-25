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
    checks = []
    expected_tabs = [
        "Task 1 · Data Trust & Definitions",
        "Task 2 · Sales, Price & Menu",
        "Task 3 · Platform & Campaign Control",
        "Task 4 · Portfolio, Kitchen & Budget",
        "Task 5 · Forecast-to-Kitchen Handoff",
        "Task 6 · E-Commerce Action Center",
    ]

    app_test = AppTest.from_file(str(APP)).run(timeout=60)
    checks.append(check("Streamlit AppTest has no exceptions", len(app_test.exception) == 0, 0, len(app_test.exception)))
    checks.append(check("App exposes all six required task tabs", [tab.label for tab in app_test.tabs] == expected_tabs, expected_tabs, [tab.label for tab in app_test.tabs]))
    root_app_test = AppTest.from_file(str(ROOT_APP)).run(timeout=60)
    checks.append(check("Deployment entrypoint has no exceptions", len(root_app_test.exception) == 0, 0, len(root_app_test.exception)))
    checks.append(check("Deployment entrypoint exposes all six task tabs", [tab.label for tab in root_app_test.tabs] == expected_tabs, expected_tabs, [tab.label for tab in root_app_test.tabs]))
    labels = [metric.label for metric in app_test.metric]
    required_labels = [
        "รายได้จากการขาย", "รายได้เทียบงบ", "ผลดำเนินงานตามแบบจำลอง",
        "แถวรายการขายดิบ", "แถวเมนูที่ใช้วิเคราะห์", "ช่วงเวลาที่ขายสูงสุด",
        "ส่วนลด", "Forecast ฐาน · 3 เดือน", "เป้าเตรียม · 3 เดือน",
    ]
    checks.append(check("App exposes required metric cards", all(label in labels for label in required_labels), required_labels, labels))
    required_sections = [
        "5 ข้อค้นพบเพื่อเลือก Action", "Action ที่เสนอสำหรับรอบถัดไป", "Platform mix และเงินเหลือก่อน Waste",
        "ราคาแต่ละ SKU เหมาะกับเงินเหลือหรือไม่?", "เงินเหลือที่คงเหลือหลังส่วนลด (ก่อน Waste)",
        "ยอดขายเพิ่มพอคุ้มส่วนลดหรือไม่?", "รายได้จริงเทียบงบรายเดือน",
        "SKU ใดควรแก้หรือคงไว้?", "Kitchen × SKU ที่ต้องส่งต่อให้ Operations", "ภาพรวม Forecast และเป้าเตรียมที่ปล่อย",
        "Demand ต่อเนื่อง: ใช้ช่วงละ 7 วันเต็ม", "เช็กฤดูกาลกับช่วงเดียวกันปีก่อน", "ผลตามแบบจำลอง 3 สถานการณ์ที่ตรวจสอบได้",
        "ช่องว่างสู่กำไร: แสดง hurdle ไม่สร้างเป้าขายย้อนกลับ", "เป้าเตรียมที่ปล่อย: เลือกครัวและ SKU", "นโยบายเตรียมและ buffer กำลังผลิต 7 วัน",
        "จากข้อมูลดิบสู่ข้อมูลวิเคราะห์ที่เผยแพร่",
    ]
    checks.append(check("App includes readable decision sections for all six tasks", all(section in app_text for section in required_sections), required_sections, [section for section in required_sections if section in app_text]))
    task_markers = ["Task 1 · Data quality", "Task 2 · Demand & pricing", "Task 3 · Promotions & rate codes", "Task 4 · Portfolio & budget performance", "Task 5 · Inventory & 3-month outlook", "Task 6 · Present findings"]
    checks.append(check("App keeps every assessment task traceable", all(marker in app_text for marker in task_markers), task_markers, [marker for marker in task_markers if marker in app_text]))
    required_selectboxes = ["เลือก Platform สำหรับดู Demand", "เลือก SKU", "เลือก rate code", "เลือกครัว", "เลือก SKU สำหรับเป้าเตรียม"]
    selectbox_labels = [widget.label for widget in app_test.selectbox]
    checks.append(check("App exposes E-Commerce drill-down controls", all(label in selectbox_labels for label in required_selectboxes), required_selectboxes, selectbox_labels))
    interactive_results: dict[str, object]
    try:
        interactive_app = AppTest.from_file(str(APP)).run(timeout=60)
        for key, value in [("sales_platform", "LINE MAN"), ("campaign_rate_code", "RC101"), ("forecast_kitchen", "BKK_Ladprao")]:
            widget = next(item for item in interactive_app.selectbox if item.key == key)
            widget.set_value(value).run(timeout=60)
        interactive_results = {
            key: next(item for item in interactive_app.selectbox if item.key == key).value
            for key in ["sales_platform", "campaign_rate_code", "forecast_kitchen"]
        }
        interactive_passed = len(interactive_app.exception) == 0 and interactive_results == {
            "sales_platform": "LINE MAN", "campaign_rate_code": "RC101", "forecast_kitchen": "BKK_Ladprao",
        }
    except Exception as error:  # pragma: no cover - preserves a QA result when UI interaction breaks.
        interactive_results = {"error": str(error)}
        interactive_passed = False
    checks.append(check("E-Commerce drill-down controls rerun without exceptions", interactive_passed, {"sales_platform": "LINE MAN", "campaign_rate_code": "RC101", "forecast_kitchen": "BKK_Ladprao"}, interactive_results))
    scope_copy = [
        "historical association", "ไม่ใช่ causal", "ของเสียไม่มี tag platform/rate code",
        "ไม่ใช่ GP variance", "ไม่ใช่ statistical confidence interval", "ไม่ใช่จำนวนสั่งซื้อจริง",
    ]
    checks.append(check("App displays E-Commerce scope guardrails", all(text in app_text for text in scope_copy), scope_copy, [text for text in scope_copy if text in app_text]))
    removed_scope_conflicts = ["Protect availability", "Discount ROI", "service level when stockout data is available", "Confirm with orders and intraday sales"]
    checks.append(check("App removes unsupported operational claims", not any(text in app_text for text in removed_scope_conflicts), removed_scope_conflicts, [text for text in removed_scope_conflicts if text in app_text]))
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
    expected_gap = float(forecast_metrics["profitability_gap"]["remaining_gap_to_break_even_thb"])
    checks.append(check("App discloses the remaining three-month profitability gap without fabricating a target", abs(optimized_result + expected_gap) < 0.01 and "ยังติดลบ" in app_text and "hurdle" in app_text and "planning/profit_recovery" not in app_text, {"optimized_result": -expected_gap, "required_copy": ["ยังติดลบ", "hurdle"], "no_reverse_engineered_target_dependency": True}, {"optimized_result": optimized_result, "has_required_copy": all(text in app_text for text in ["ยังติดลบ", "hurdle"]), "has_reverse_engineered_target_dependency": "planning/profit_recovery" in app_text}))
    checks.append(check("Price page gives a test recommendation for every core SKU", all(sku_name in app_text for sku_name in ["Watermelon", "Pineapple", "Guava", "PassionFruit", "MixedBerryPremium"]) and "ข้อเสนอการทดสอบ" in app_text, "5 SKUs + test recommendation", {"sku_mentions": [sku_name for sku_name in ["Watermelon", "Pineapple", "Guava", "PassionFruit", "MixedBerryPremium"] if sku_name in app_text], "has_test_label": "ข้อเสนอการทดสอบ" in app_text}))
    checks.append(check("Forecast benchmarks six methods with pooled rolling-origin WAPE", set(backtest["method"]) == {"naive_last_day", "moving_avg_4w", "exp_smoothing_4w", "seasonal_naive_7d", "weekday_median_8w", "level_weekday_blend"} and (backtest["cutoffs"] == 4).all() and forecast_metrics["selected_method"] == "level_weekday_blend", "6 methods / 4 cutoffs / weekday-shaped winner", {"methods": sorted(backtest["method"].unique().tolist()), "cutoffs": sorted(backtest["cutoffs"].unique().tolist()), "selected": forecast_metrics["selected_method"]}))
    checks.append(check("Forecast metadata distinguishes pooled and macro WAPE", "selected_method_pooled_wape" in forecast_metrics and "selected_method_macro_wape" in forecast_metrics and "selected_method_mean_wape" not in forecast_metrics, "explicit pooled + macro keys; no ambiguous mean key", {key: forecast_metrics.get(key) for key in ["selected_method_pooled_wape", "selected_method_macro_wape", "selected_method_mean_wape"]}))
    checks.append(check("Task 5 charts do not stack non-additive series", app_text.count("stack=False") >= 4, ">=4 grouped chart calls", app_text.count("stack=False")))
    checks.append(check("Weekly demand artifact labels incomplete weeks", {"days_observed", "is_complete_week"}.issubset(weekly_demand.columns) and (~weekly_demand["is_complete_week"]).any(), "completeness fields + partial weeks visible", {"columns_present": sorted({"days_observed", "is_complete_week"} & set(weekly_demand.columns)), "partial_rows": int((~weekly_demand["is_complete_week"]).sum()) if "is_complete_week" in weekly_demand else None}))
    checks.append(check("Task 5 uses stable scenario codes and like-for-like seasonality copy", 'groupby("scenario", as_index=False)' in app_text and "ราคา RC000 + ลด Waste 25%" in app_text and "เทียบเฉพาะ SKU ที่มีทั้งสองช่วง" in app_text, True, {"stable_scenario_group": 'groupby("scenario", as_index=False)' in app_text, "rc000_label": "ราคา RC000 + ลด Waste 25%" in app_text, "common_sku_copy": "เทียบเฉพาะ SKU ที่มีทั้งสองช่วง" in app_text}))
    superseded_note = (ROOT / "planning/profit_recovery/README.md").read_text(encoding="utf-8")
    checks.append(check("Retired reverse-engineered recovery artifacts are marked superseded", "Superseded" in superseded_note and "Do not use" in superseded_note, True, "Superseded" in superseded_note and "Do not use" in superseded_note))
    checks.append(check("Forecast uncertainty range is present and ordered", all(col in forecast.columns for col in ["forecast_lower_units", "forecast_units_base", "forecast_upper_units"]) and bool((forecast["forecast_lower_units"] <= forecast["forecast_units_base"]).all()) and bool((forecast["forecast_units_base"] <= forecast["forecast_upper_units"]).all()), True, {"rows": int(len(forecast)), "range_ordered": bool((forecast["forecast_lower_units"] <= forecast["forecast_units_base"]).all() and (forecast["forecast_units_base"] <= forecast["forecast_upper_units"]).all())}))
    checks.append(check("Forecast is at Kitchen x SKU level", forecast[["kitchen", "sku"]].drop_duplicates().shape[0] == 20, 20, int(forecast[["kitchen", "sku"]].drop_duplicates().shape[0])))
    checks.append(check("Monthly SKU forecast covers three months and five SKUs", forecast_monthly_sku["month"].nunique() == 3 and forecast_monthly_sku["sku"].nunique() == 5, "3 months / 5 SKUs", {"months": int(forecast_monthly_sku["month"].nunique()), "skus": int(forecast_monthly_sku["sku"].nunique())}))
    daily_shape = forecast.groupby(["kitchen", "sku"])["forecast_units_base"].nunique()
    checks.append(check("Selected forecast preserves weekday shape", int(daily_shape.min()) > 1, "more than one daily value in every Kitchen x SKU series", {"min_unique_daily_values": int(daily_shape.min()), "max_unique_daily_values": int(daily_shape.max())}))
    implied_waste_rate = inventory_policy["expected_waste_3m_cups"] / (inventory_policy["forecast_3m_cups"] + inventory_policy["expected_waste_3m_cups"])
    waste_reconciliation_error = float((implied_waste_rate - inventory_policy["waste_rate"]).abs().max())
    checks.append(check("Kitchen x SKU waste rates reconcile forecast, prep and policy", waste_reconciliation_error < 1e-10, "max error < 1e-10", waste_reconciliation_error))
    checks.append(check("Inventory policy covers 20 cells with trend-aware XYZ and capacity buffers", len(inventory_policy) == 20 and all(col in inventory_policy.columns for col in ["abc_class", "xyz_class", "recent_12w_trend_pct", "demand_pattern", "demand_buffer_7d_cups_policy", "planning_ceiling_next_7d_cups", "inventory_alert_rank"]) and set(inventory_policy.loc[inventory_policy["sku"] == "MixedBerryPremium", "xyz_class"]) == {"Z"}, "20 cells + trend-aware policy fields + MixedBerry=Z", {"rows": int(len(inventory_policy)), "mixedberry_xyz": sorted(inventory_policy.loc[inventory_policy["sku"] == "MixedBerryPremium", "xyz_class"].unique().tolist())}))
    checks.append(check("Purchase-order boundary is explicitly preserved", inventory_policy["order_qty_status"].str.contains("not calculable", case=False).all() and "No on-hand" in forecast_metrics["inventory_limitations"], True, {"all_not_calculable": bool(inventory_policy["order_qty_status"].str.contains("not calculable", case=False).all()), "limitations": forecast_metrics["inventory_limitations"]}))
    checks.append(check("Fruit-cost stress test covers 0/5/10/20 percent", set((fruit_cost_stress["fruit_cost_uplift_pct"] * 100).round(0)) == {0, 5, 10, 20} and (fruit_cost_stress["modeled_operating_result_thb"].diff().dropna() < 0).all(), "4 stress points / operating result declines", {"points": sorted((fruit_cost_stress["fruit_cost_uplift_pct"] * 100).round(0).tolist()), "declines": bool((fruit_cost_stress["modeled_operating_result_thb"].diff().dropna() < 0).all())}))

    failures = [item for item in checks if item["result"] == "FAIL"]
    result = {"app": str(APP), "status": "passed" if not failures else "failed", "checks": checks, "failed_count": len(failures)}
    output = REPORTS / "qa/streamlit_checks.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=True, indent=2))
