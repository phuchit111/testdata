"""FruitBlend24 Streamlit decision app.

The app reads only QA-passed artifacts from one immutable data version. It
performs display-level filtering only, so the deployed views stay aligned with
the memo, metric contract, and QA files.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st


RUN_ID = "fruitblend24_run_001"
DATA_VERSION = "fruitblend24_v1_c2869ce419bf"
APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parents[1]
DATA_DIR = ROOT / "data/processed" / DATA_VERSION
REPORT_DIR = ROOT / "reports" / RUN_ID


def money(value: float, decimals: int = 0) -> str:
    if pd.isna(value):
        return "n/a"
    return f"฿{value:,.{decimals}f}"


def pct(value: float, decimals: int = 1) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{value * 100:.{decimals}f}%"


MONTH_NAMES = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}
WEEKDAY_NAMES = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}


def month_name(value) -> str:
    timestamp = pd.Timestamp(value)
    return f"{MONTH_NAMES[timestamp.month]} {timestamp.year}"


def apply_theme() -> None:
    """Apply a small, readable visual system without changing the analysis artifacts."""
    st.markdown(
        """
        <style>
        .block-container {max-width: 1220px; padding-top: 2rem; padding-bottom: 3rem;}
        .hero {padding: 1.25rem 1.4rem; border-radius: 1rem; background: linear-gradient(120deg, #f0fdf4 0%, #eff6ff 100%); border: 1px solid #bbf7d0; margin-bottom: 1rem;}
        .hero h2 {margin: 0 0 .4rem 0; color: #14532d;}
        .hero p {margin: 0; font-size: 1.05rem; color: #334155;}
        .eyebrow {font-size: .85rem; font-weight: 700; color: #047857; letter-spacing: .03em;}
        .callout {border-left: 4px solid #f59e0b; background: #fffbeb; padding: .8rem 1rem; border-radius: .4rem; margin: .6rem 0 1rem; color: #713f12;}
        div[data-testid="stMetric"] {background: #ffffff; border: 1px solid #e2e8f0; border-radius: .75rem; padding: .65rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def task_heading(task: str, title: str, question: str) -> None:
    st.caption(task)
    st.subheader(title)
    st.write(question)


def display_table(
    frame: pd.DataFrame,
    columns: list[str],
    labels: dict[str, str],
    *,
    money_columns: tuple[str, ...] = (),
    percent_columns: tuple[str, ...] = (),
    integer_columns: tuple[str, ...] = (),
    date_columns: tuple[str, ...] = (),
    decimal_columns: tuple[str, ...] = (),
    height: int | None = None,
) -> None:
    """Show selected business fields with English labels and readable units."""
    view = frame.loc[:, [column for column in columns if column in frame.columns]].copy()
    for column in money_columns:
        if column in view:
            view[column] = view[column].map(lambda value: money(value, 2) if pd.notna(value) else "n/a")
    for column in percent_columns:
        if column in view:
            view[column] = view[column].map(lambda value: pct(value, 1) if pd.notna(value) else "n/a")
    for column in integer_columns:
        if column in view:
            view[column] = view[column].map(lambda value: f"{value:,.0f}" if pd.notna(value) else "n/a")
    for column in date_columns:
        if column in view:
            view[column] = pd.to_datetime(view[column]).map(month_name)
    for column in decimal_columns:
        if column in view:
            view[column] = view[column].map(lambda value: f"{value:,.1f}" if pd.notna(value) else "n/a")
    kwargs = {"width": "stretch", "hide_index": True}
    if height is not None:
        kwargs["height"] = height
    st.dataframe(view.rename(columns=labels), **kwargs)


def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_data() -> dict[str, pd.DataFrame | dict]:
    data = {
        "sku": load_csv(str(REPORT_DIR / "commercial/sku_summary.csv")),
        "kitchen": load_csv(str(REPORT_DIR / "commercial/kitchen_summary.csv")),
        "platform": load_csv(str(REPORT_DIR / "commercial/platform_summary.csv")),
        "promo": load_csv(str(REPORT_DIR / "commercial/promo_summary.csv")),
        "promo_comparator": load_csv(str(REPORT_DIR / "commercial/promo_comparator_by_stratum.csv")),
        "promo_scorecard": load_csv(str(REPORT_DIR / "commercial/promo_scorecard.csv")),
        "promo_matched_scorecard": load_csv(str(REPORT_DIR / "commercial/promo_matched_scorecard.csv")),
        "promo_efficiency": load_csv(str(REPORT_DIR / "commercial/promo_efficiency_matrix.csv")),
        "promo_by_sku": load_csv(str(REPORT_DIR / "commercial/promo_by_sku.csv")),
        "promo_by_kitchen": load_csv(str(REPORT_DIR / "commercial/promo_by_kitchen.csv")),
        "promo_by_platform": load_csv(str(REPORT_DIR / "commercial/promo_by_platform.csv")),
        "promo_by_hour": load_csv(str(REPORT_DIR / "commercial/promo_by_hour.csv")),
        "promo_by_daypart": load_csv(str(REPORT_DIR / "commercial/promo_by_daypart.csv")),
        "promo_by_segment": load_csv(str(REPORT_DIR / "commercial/promo_by_segment.csv")),
        "promo_dependency": load_csv(str(REPORT_DIR / "commercial/promo_dependency_by_sku.csv")),
        "promo_depth": load_csv(str(REPORT_DIR / "commercial/promo_depth_breakeven.csv")),
        "price_floor": load_csv(str(REPORT_DIR / "commercial/price_floor.csv")),
        "hourly": load_csv(str(REPORT_DIR / "commercial/hourly_demand.csv")),
        "weekday": load_csv(str(REPORT_DIR / "commercial/weekday_demand.csv")),
        "monthly_demand": load_csv(str(REPORT_DIR / "commercial/monthly_demand_value.csv")),
        "hourly_normalized": load_csv(str(REPORT_DIR / "commercial/hourly_demand_normalized.csv")),
        "weekday_normalized": load_csv(str(REPORT_DIR / "commercial/weekday_demand_normalized.csv")),
        "daypart": load_csv(str(REPORT_DIR / "commercial/daypart_summary.csv")),
        "heatmap": load_csv(str(REPORT_DIR / "commercial/demand_heatmap_day_hour.csv")),
        "kitchen_sku": load_csv(str(REPORT_DIR / "commercial/kitchen_sku_demand.csv")),
        "price_ladder": load_csv(str(REPORT_DIR / "commercial/price_ladder.csv")),
        "price_sensitivity": load_csv(str(REPORT_DIR / "commercial/price_sensitivity_directional.csv")),
        "price_simulation": load_csv(str(REPORT_DIR / "commercial/price_simulation.csv")),
        "price_simulation_best": load_csv(str(REPORT_DIR / "commercial/price_simulation_best_by_sku.csv")),
        "daily": load_csv(str(DATA_DIR / "sales_daily.csv")),
        "pnl_company": load_csv(str(REPORT_DIR / "finance/pnl_monthly_company_vs_budget.csv")),
        "pnl_kitchen": load_csv(str(REPORT_DIR / "finance/pnl_monthly_kitchen.csv")),
        "portfolio": load_csv(str(REPORT_DIR / "finance/portfolio_summary.csv")),
        "finance_kitchen": load_csv(str(REPORT_DIR / "finance/kitchen_summary.csv")),
        "pnl_waterfall": load_csv(str(REPORT_DIR / "finance/pnl_waterfall.csv")),
        "revenue_decomp": load_csv(str(REPORT_DIR / "finance/revenue_variance_diagnostic.csv")),
        "waste_heatmap": load_csv(str(REPORT_DIR / "finance/waste_heatmap.csv")),
        "fruit_cost_trend": load_csv(str(REPORT_DIR / "finance/fruit_cost_trend.csv")),
        "sku_kitchen_pareto": load_csv(str(REPORT_DIR / "finance/sku_kitchen_pareto.csv")),
        "finance_scenarios": load_csv(str(REPORT_DIR / "finance/finance_scenarios.csv")),
        "gap_closing": load_csv(str(REPORT_DIR / "finance/gap_closing_plan.csv")),
        "backtest": load_csv(str(REPORT_DIR / "inventory/backtest_summary.csv")),
        "weekly_demand": load_csv(str(REPORT_DIR / "inventory/weekly_demand.csv")),
        "forecast": load_csv(str(REPORT_DIR / "inventory/forecast_daily.csv")),
        "forecast_monthly_sku": load_csv(str(REPORT_DIR / "inventory/forecast_monthly_by_sku.csv")),
        "scenario": load_csv(str(REPORT_DIR / "inventory/scenario_monthly_pnl.csv")),
        "requirements": load_csv(str(REPORT_DIR / "inventory/cup_requirements.csv")),
        "inventory_policy": load_csv(str(REPORT_DIR / "inventory/inventory_policy.csv")),
        "fruit_cost_stress": load_csv(str(REPORT_DIR / "inventory/fruit_cost_stress_test.csv")),
        "recovery_monthly": load_csv(str(ROOT / "planning/profit_recovery/monthly_pnl.csv")),
        "recovery_prep": load_csv(str(ROOT / "planning/profit_recovery/prep_targets.csv")),
        "recovery_kitchen": load_csv(str(ROOT / "planning/profit_recovery/kitchen_pnl.csv")),
        "recovery_sensitivity": load_csv(str(ROOT / "planning/profit_recovery/sensitivity.csv")),
        "recovery_bridge": load_csv(str(ROOT / "planning/profit_recovery/profit_bridge.csv")),
        "recovery_nov_evidence": load_csv(str(ROOT / "planning/profit_recovery/november_growth_evidence.csv")),
        "recovery_nov_capacity": load_csv(str(ROOT / "planning/profit_recovery/november_capacity_gate.csv")),
        "issues": load_csv(str(REPORT_DIR / "data/issues.csv")),
        "audit": load_json(str(REPORT_DIR / "data/audit.json")),
        "data_qa": load_json(str(REPORT_DIR / "qa/checks.json")),
        "qa": load_json(str(REPORT_DIR / "qa/checks_final.json")),
        "manifest": load_json(str(DATA_DIR / "manifest.json")),
        "reconciliation": load_json(str(DATA_DIR / "reconciliation.json")),
        "metrics": load_json(str(REPORT_DIR / "inventory/forecast_metrics.json")),
        "commercial_metrics": load_json(str(REPORT_DIR / "commercial/commercial_metrics.json")),
        "promotion_depth_metrics": load_json(str(REPORT_DIR / "commercial/promotion_depth_metrics.json")),
        "pricing_depth_metrics": load_json(str(REPORT_DIR / "commercial/pricing_depth_metrics.json")),
        "finance_metrics": load_json(str(REPORT_DIR / "finance/finance_metrics.json")),
        "contract": load_json(str(DATA_DIR / "metric_contract.json")),
        "assumptions": load_json(str(REPORT_DIR / "assumptions.json")),
        "readiness": load_json(str(ROOT / "planning/data_readiness.json")),
        "recovery_summary": load_json(str(ROOT / "planning/profit_recovery/summary.json")),
    }
    for key in ["daily", "forecast", "requirements"]:
        data[key]["date"] = pd.to_datetime(data[key]["date"])
    data["weekly_demand"]["week_start"] = pd.to_datetime(data["weekly_demand"]["week_start"])
    data["forecast_monthly_sku"]["month"] = pd.to_datetime(data["forecast_monthly_sku"]["month"])
    data["pnl_company"]["month"] = pd.to_datetime(data["pnl_company"]["month"])
    data["pnl_kitchen"]["month"] = pd.to_datetime(data["pnl_kitchen"]["month"])
    data["scenario"]["month"] = pd.to_datetime(data["scenario"]["month"])
    data["monthly_demand"]["month"] = pd.to_datetime(data["monthly_demand"]["month"])
    return data


def metric_cards(data: dict) -> tuple[float, float, float]:
    pnl = data["pnl_company"]
    revenue = float(pnl["gross_revenue_thb"].sum())
    revenue_variance = float(pnl["revenue_variance_thb"].sum())
    operating = float(pnl["modeled_operating_result_thb"].sum())
    c1, c2, c3 = st.columns(3)
    c1.metric("Sales revenue", money(revenue), "Actual after data screening")
    c2.metric("Revenue vs. budget", money(revenue_variance), pct(revenue_variance / float(pnl["budget_revenue_thb"].sum())))
    c3.metric("Modeled operating result", money(operating), "After waste and fixed overhead")
    return revenue, revenue_variance, operating


def overview(data: dict) -> None:
    task_heading("Task 6 · Decision summary", "Overview & recovery plan", "Start with the overview, then open the evidence on pricing, promotions, products, kitchens, and preparation planning.")
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">FRUITBLEND24 · Synthetic data case study</div>
          <h2>Sales are strong, but post-cost contribution is not enough</h2>
          <p>Revenue is close to target, but discounts, loss-making products, waste, and fixed overhead keep the modeled operating result negative.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    revenue, revenue_variance, operating = metric_cards(data)
    st.caption("Historical period: Sep 2025–Aug 2026 · Forecast plan: Sep–Nov 2026 · Not live data")

    pnl = data["pnl_company"].copy().set_index("month")
    left, right = st.columns((1.1, 0.9))
    with left:
        st.markdown("#### Actual sales vs. monthly target")
        st.line_chart(
            pnl[["gross_revenue_thb", "budget_revenue_thb"]].rename(columns={"gross_revenue_thb": "Actual revenue", "budget_revenue_thb": "Revenue target"}),
            height=280,
        )
    with right:
        st.markdown("#### Where does sales revenue go?")
        waterfall = data["pnl_waterfall"].copy().set_index("pnl_component")
        waterfall.index = [
            "Revenue", "Fruit cost", "Packaging", "Labor", "Platform commission",
            "Contribution before waste", "Waste cost", "Contribution after waste", "Fixed overhead", "Operating result",
        ]
        st.bar_chart(waterfall[["thb"]].rename(columns={"thb": "THB"}), height=280)

    st.markdown("#### 5 decision-relevant findings")
    reconciliation = data["reconciliation"]
    peak_hour = data["hourly"].sort_values("units_sold", ascending=False).iloc[0]
    weekend_revenue_share = float(data["weekday"].loc[data["weekday"]["day_of_week"].isin([5, 6]), "revenue_share"].sum())
    mixed = data["sku"].loc[data["sku"]["sku"] == "MixedBerryPremium"].iloc[0]
    promo = data["promo"].set_index("base_code")
    base_wape = float(data["metrics"]["selected_method_mean_wape"])
    base_outlook = data["scenario"].loc[data["scenario"]["scenario"] == "base"]
    insights = pd.DataFrame([
        ["Data is ready", f"Removed 372 duplicate rows, preventing {money(reconciliation['duplicate_revenue_removed_thb'])} of overstated revenue; excluded 370 non-menu rows", "Use only the 123,655 screened menu rows"],
        ["Demand is time-dependent", f"Peak volume occurs at 22:00 with {peak_hour['units_sold']:,.0f} cups; weekends contribute {pct(weekend_revenue_share)} of revenue", "Add preparation before evenings and weekends; reduce early prep during low-demand periods"],
        ["Promotions consume contribution", f"RC102 contributes {money(promo.loc['RC102', 'contribution_before_waste_per_cup_thb'], 2)}/cup vs. {money(promo.loc['RC000', 'contribution_before_waste_per_cup_thb'], 2)}/cup for standard pricing before waste", "Use standard pricing as the control and run controlled promotion tests"],
        ["Fix MixedBerryPremium before scaling", f"Post-waste contribution is {money(mixed['contribution_after_waste_thb'])}, or {money(mixed['contribution_after_waste_per_cup_thb'], 2)}/cup; waste is {pct(mixed['waste_rate'])}", "Pilot price, portion, and small-batch preparation changes before adding volume"],
        ["The next 3 months still have a gap", f"The base case forecasts {base_outlook['forecast_units'].sum():,.0f} cups and a modeled loss of {money(base_outlook['modeled_operating_result_thb'].sum())}; WAPE is {pct(base_wape)}", "Plan kitchen–SKU preparation and price/waste actions together"],
    ], columns=["Finding", "Numeric evidence", "Recommended action"])
    st.dataframe(insights, width="stretch", hide_index=True)

    st.markdown("#### Where to start")
    card1, card2, card3 = st.columns(3)
    card1.warning("**Product:** MixedBerryPremium\n\nPost-waste contribution is negative and waste is 20.5%; do not accelerate scale-up yet.")
    card2.warning("**Promotions:** RC101–RC103\n\nAll deliver lower contribution per cup than standard pricing; stop blanket use and test selectively.")
    card3.warning("**Kitchens:** BKK_Ladprao and BKK_Sukhumvit\n\nThe modeled operating result is negative; inspect kitchen–SKU pairs and waste first.")

    st.markdown("#### Action plan")
    actions = pd.DataFrame([
        ["Pricing & promotions", "Use RC000 as the control, limit RC101/RC103, and test RC102 only for new users or low-demand periods after passing the contribution-per-cup gate", "Commercial + Growth (proposed)", "Next 2-week campaign cycle", "Contribution/cup, lift vs. control, promotion waste"],
        ["Product", "Run a 4-week MixedBerryPremium pilot: test price/portion and small-batch preparation; do not scale until post-waste contribution is positive", "Category + Kitchen Operations (proposed)", "Start within 1 week; weekly review", "Post-waste contribution/cup > 0; waste below 10% pilot target"],
        ["Preparation planning", f"Use {data['metrics']['selected_method']} for daily kitchen–SKU forecasts, include expected waste in prep targets, and review every 7 days", "Operations + Supply (proposed)", "Daily preparation; weekly review", f"WAPE ≤ {pct(base_wape)}, waste, forecast bias, service level when stockout data is available"],
        ["Kitchen recovery", "Start with Ladprao and Sukhumvit: inspect loss-making or high-waste kitchen–SKU pairs and review pricing, promotions, and batch size", "Kitchen Manager + Commercial (proposed)", "Weekly review meeting", "Operating result, waste cost/revenue, contribution/cup"],
    ], columns=["Area", "Action", "Proposed owner", "Timing", "KPI"])
    st.dataframe(actions, width="stretch", hide_index=True)

    st.markdown("#### Outlook: Sep–Nov 2026")
    scenario_totals = data["scenario"].groupby("scenario_display", as_index=False).agg(
        forecast_units=("forecast_units", "sum"), modeled_operating_result_thb=("modeled_operating_result_thb", "sum")
    )
    scenario_order = ["Base case", "Optimized case", "Downside case"]
    scenario_totals["sort_order"] = scenario_totals["scenario_display"].map({name: index for index, name in enumerate(scenario_order)})
    scenario_totals = scenario_totals.sort_values("sort_order")
    scenario_columns = st.columns(3)
    for column, (_, row) in zip(scenario_columns, scenario_totals.iterrows()):
        scenario_name = {"Base case": "Base case", "Optimized case": "Optimized case", "Downside case": "Downside case"}[row["scenario_display"]]
        column.metric(scenario_name, money(row["modeled_operating_result_thb"]), f"Forecast {row['forecast_units']:,.0f} cups")
    optimized_result = float(scenario_totals.loc[scenario_totals["scenario_display"] == "Optimized case", "modeled_operating_result_thb"].iloc[0])
    base_result = float(scenario_totals.loc[scenario_totals["scenario_display"] == "Base case", "modeled_operating_result_thb"].iloc[0])
    st.markdown(
        f"<div class='callout'><strong>The optimized plan does not yet reach profitability:</strong> Starting from the base case at {money(base_result)}, standard realized pricing and a 25% waste reduction reduce the loss by {money(optimized_result - base_result)}, but a {money(-optimized_result)} gap remains before 3-month break-even. Measure actual results and reassess fixed costs, purchasing costs, and positive-contribution sales.</div>",
        unsafe_allow_html=True,
    )

    with st.expander("Decision logic and limitations"):
        st.markdown("Revenue uses observed post-promotion prices, so discounts are not deducted again. The modeled operating result deducts fruit, packaging, labor, commission, recorded waste, and kitchen fixed overhead; the budget GP boundary is unspecified, so this is not presented as a budget GP variance.")
        st.markdown("Promotion results are observed associations, not proof that promotions caused demand changes. The forecast range is a WAPE-based planning range, not a statistical confidence interval.")

    with st.expander("Source and validation status"):
        qa = data["qa"]
        st.success(f"Calculation artifacts checked: {qa['status']} · Passed {len(qa['checks']) - qa['failed_count']}/{len(qa['checks'])} checks")
        st.write(f"Data version: `{DATA_VERSION}`")
        st.write("Open the “Data quality and limitations” tab for screening, open issues, and check-level QA.")


def demand_pricing(data: dict) -> None:
    task_heading("Task 2 · Demand & pricing", "Demand & price fit", "When do customers buy, and how much headroom does each product have above its pre-waste break-even price?")
    hourly = data["hourly"].copy()
    weekday = data["weekday"].copy()
    weekday["weekday"] = weekday["day_of_week"].map(WEEKDAY_NAMES)
    monthly = data["monthly_demand"].copy()
    peak_hour = hourly.sort_values("units_sold", ascending=False).iloc[0]
    peak_day = weekday.sort_values("units_sold", ascending=False).iloc[0]
    top_platform = data["platform"].sort_values("gross_revenue_thb", ascending=False).iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Peak sales hour", f"{int(peak_hour['hour']):02d}:00", f"{peak_hour['units_sold']:,.0f} cups across history")
    c2.metric("Peak sales day", str(peak_day["weekday"]), f"{peak_day['units_sold']:,.0f} cups across history")
    c3.metric("Top revenue platform", str(top_platform["platform_name"]), money(top_platform["gross_revenue_thb"]))
    st.caption("The hourly and daily totals above cover 12 months, not a single day.")

    st.markdown("#### When do customers buy?")
    left, right = st.columns(2)
    left.markdown("**Total sales by hour**")
    left.bar_chart(hourly.set_index("hour")[["units_sold"]].rename(columns={"units_sold": "Cups"}), height=270)
    right.markdown("**Total sales by weekday**")
    right.bar_chart(weekday.set_index("weekday")[["units_sold"]].rename(columns={"units_sold": "Cups"}), height=270)
    left, right = st.columns(2)
    left.markdown("**Total monthly sales**")
    monthly_cups = monthly.set_index("month")[["units_sold"]].rename(columns={"units_sold": "Cups"})
    left.line_chart(monthly_cups, height=260)
    right.markdown("**Total monthly revenue**")
    right.line_chart(monthly.set_index("month")[["gross_revenue_thb"]].rename(columns={"gross_revenue_thb": "THB"}), height=260)
    st.info("Increase preparation before the evening peak, especially 22:00 and weekends. Do not interpret hours missing from the export as zero sales.")

    with st.expander("Normalized demand and time-of-day detail"):
        normalized_hour = data["hourly_normalized"].copy().set_index("hour")
        normalized_day = data["weekday_normalized"].copy()
        normalized_day["weekday"] = normalized_day["day_of_week"].map(WEEKDAY_NAMES)
        normalized_day = normalized_day.set_index("weekday")
        left, right = st.columns(2)
        left.markdown("**Average cups per active day by hour**")
        left.bar_chart(normalized_hour[["avg_cups_per_active_day"]].rename(columns={"avg_cups_per_active_day": "Average cups"}), height=260)
        right.markdown("**Average cups per active day by weekday**")
        right.bar_chart(normalized_day[["avg_cups_per_active_day"]].rename(columns={"avg_cups_per_active_day": "Average cups"}), height=260)
        daypart = data["daypart"].sort_values("daypart_order").set_index("daypart")
        st.markdown("**Average cups per observed hour by daypart**")
        st.bar_chart(daypart[["avg_cups_per_observed_hour"]].rename(columns={"avg_cups_per_observed_hour": "Average cups"}), height=240)
        st.markdown("**Demand heatmaps: weekday × hour and kitchen × SKU**")
        day_names = list(WEEKDAY_NAMES.values())
        heat = data["heatmap"].copy()
        heat["weekday"] = heat["day_of_week"].map(WEEKDAY_NAMES)
        heat_table = heat.pivot(index="weekday", columns="hour", values="avg_cups_per_active_day").reindex(day_names).round(1)
        st.dataframe(heat_table.style.background_gradient(cmap="YlOrRd").format("{:.1f} cups"), width="stretch")
        kitchen_heat = data["kitchen_sku"].pivot(index="kitchen", columns="sku", values="avg_cups_per_active_day").round(1)
        st.dataframe(kitchen_heat.style.background_gradient(cmap="YlGnBu").format("{:.1f} cups"), width="stretch")

    st.markdown("#### Current price fit by product")
    st.write("This table compares realized customer prices with **pre-waste, pre-fixed-overhead break-even**. It screens price fit; it is not the break-even price for the whole business.")
    price_summary = data["price_floor"].merge(
        data["portfolio"][["sku", "contribution_after_waste_per_cup_thb", "waste_rate", "action_note"]], on="sku", how="left"
    )
    price_summary["headroom_before_waste_thb"] = price_summary["realized_price_thb"] - price_summary["break_even_price_before_waste_thb"]
    price_actions = {
        "Watermelon": "Hold price; test +5% during peak demand and protect availability",
        "Pineapple": "Hold price; test +5% during peak demand and protect availability",
        "Guava": "Hold price; test +5% during peak demand with a control group",
        "PassionFruit": "Hold price; review distribution and waste before testing price",
        "MixedBerryPremium": "Test +5% with portion control and small-batch preparation",
    }
    price_summary["recommendation"] = price_summary["sku"].map(price_actions)
    display_table(
        price_summary.sort_values("contribution_after_waste_per_cup_thb", ascending=False),
        ["sku", "realized_price_thb", "break_even_price_before_waste_thb", "headroom_before_waste_thb", "contribution_before_waste_per_cup_thb", "contribution_after_waste_per_cup_thb", "waste_rate", "recommendation"],
        {"sku": "SKU", "realized_price_thb": "Realized price/cup", "break_even_price_before_waste_thb": "Pre-waste break-even/cup", "headroom_before_waste_thb": "Break-even headroom", "contribution_before_waste_per_cup_thb": "Contribution before waste/cup", "contribution_after_waste_per_cup_thb": "Contribution after waste/cup", "waste_rate": "Waste rate", "recommendation": "Test recommendation"},
        money_columns=("realized_price_thb", "break_even_price_before_waste_thb", "headroom_before_waste_thb", "contribution_before_waste_per_cup_thb", "contribution_after_waste_per_cup_thb"),
        percent_columns=("waste_rate",),
    )
    st.caption("Price recommendations are controlled tests, not immediate price-change instructions, because observed price changes mostly reflect rate codes and other confounding factors.")

    st.markdown("#### Product-level price detail")
    sku_options = data["sku"]["sku"].tolist()
    selected_sku = st.selectbox("Select product", sku_options, index=sku_options.index("MixedBerryPremium") if "MixedBerryPremium" in sku_options else 0)
    sku_row = data["sku"].loc[data["sku"]["sku"] == selected_sku].iloc[0]
    price_row = data["price_floor"].loc[data["price_floor"]["sku"] == selected_sku].iloc[0]
    price_headroom = sku_row["realized_price_thb"] - price_row["break_even_price_before_waste_thb"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Historical sales", f"{sku_row['units_sold']:,.0f} cups")
    c2.metric("Realized price", money(sku_row["realized_price_thb"], 2))
    c3.metric("Pre-waste break-even headroom", money(price_headroom, 2))
    c4.metric("Post-waste contribution/cup", money(sku_row["contribution_after_waste_per_cup_thb"], 2))

    left, right = st.columns(2)
    ladder = data["price_ladder"].loc[data["price_ladder"]["sku"] == selected_sku].sort_values("observed_price_thb")
    with left:
        st.markdown("**Price vs. sales per active hour**")
        st.line_chart(ladder.set_index("observed_price_thb")[["avg_cups_per_active_hour"]].rename(columns={"avg_cups_per_active_hour": "Cups per hour"}), height=250)
    with right:
        st.markdown("**Post-waste contribution scenarios**")
        simulation = data["price_simulation"].loc[data["price_simulation"]["sku"] == selected_sku].sort_values("price_change_pct").copy()
        simulation["price_change_label"] = simulation["price_change_pct"].map(lambda value: pct(value, 0))
        st.line_chart(simulation.set_index("price_change_label")[["projected_contribution_after_waste_thb"]].rename(columns={"projected_contribution_after_waste_thb": "THB"}), height=250)
    with st.expander("Price evidence and statistical limitations"):
        display_table(
            ladder,
            ["observed_price_thb", "units_sold", "active_hours", "avg_cups_per_active_hour", "contribution_per_cup_thb", "promo_families"],
            {"observed_price_thb": "Observed price", "units_sold": "Units sold", "active_hours": "Active hours", "avg_cups_per_active_hour": "Cups/hour", "contribution_per_cup_thb": "Contribution/cup", "promo_families": "Rate-code families"},
            money_columns=("observed_price_thb", "contribution_per_cup_thb"), integer_columns=("units_sold", "active_hours"), decimal_columns=("avg_cups_per_active_hour",),
        )
        sensitivity = data["price_sensitivity"].copy()
        display_table(
            sensitivity,
            ["sku", "price_points", "min_observed_price_thb", "max_observed_price_thb", "price_cv", "pairwise_midpoint_elasticity_median", "pairwise_comparisons", "interpretation"],
            {"sku": "SKU", "price_points": "Observed price points", "min_observed_price_thb": "Minimum price", "max_observed_price_thb": "Maximum price", "price_cv": "Price volatility", "pairwise_midpoint_elasticity_median": "Price sensitivity (directional)", "pairwise_comparisons": "Pairwise comparisons", "interpretation": "Limitations"},
            money_columns=("min_observed_price_thb", "max_observed_price_thb"), percent_columns=("price_cv",), integer_columns=("price_points", "pairwise_comparisons"), decimal_columns=("pairwise_midpoint_elasticity_median",),
        )
        display_table(
            simulation,
            ["price_change_pct", "projected_price_thb", "demand_factor", "projected_units", "projected_contribution_after_waste_thb", "delta_contribution_vs_current_thb", "assumption_source"],
            {"price_change_pct": "Price change", "projected_price_thb": "Scenario price", "demand_factor": "Demand factor", "projected_units": "Scenario units", "projected_contribution_after_waste_thb": "Post-waste contribution", "delta_contribution_vs_current_thb": "Change vs. current", "assumption_source": "Assumption source"},
            money_columns=("projected_price_thb", "projected_contribution_after_waste_thb", "delta_contribution_vs_current_thb"), percent_columns=("price_change_pct",), integer_columns=("projected_units",), decimal_columns=("demand_factor",),
        )
        best = data["price_simulation_best"].loc[data["price_simulation_best"]["sku"] == selected_sku]
        if not best.empty:
            best_row = best.iloc[0]
            st.info(f"The illustrative model gives the highest contribution at a {pct(best_row['price_change_pct'])} price change for {selected_sku}, but it uses an elasticity assumption of {best_row['elasticity_used']:.2f}. Use it only to design a +5% peak-period test, not as evidence for a permanent price change.")


def promotions(data: dict) -> None:
    task_heading("Task 3 · Promotions & rate codes", "Are promotions worth it?", "Review contribution per cup and standard-price comparisons before using discounts to drive volume.")
    metrics = data["promotion_depth_metrics"]
    scorecard = data["promo_scorecard"].copy().sort_values("base_code")
    matched = data["promo_matched_scorecard"].copy().sort_values("base_code")
    decision_map = {"CONTROL / DEFAULT": "Use as control", "OPTIMIZE / TARGET ONLY": "Limit and test selectively"}
    scorecard["decision_display"] = scorecard["decision"].map(decision_map).fillna(scorecard["decision"])
    matched["decision_display"] = matched["decision"].map(decision_map).fillna(matched["decision"])

    st.caption("Revenue is the customer's post-promotion price. Discount cost is shown for impact analysis and is not deducted from revenue again.")
    st.markdown("#### Decision summary for active rate codes")
    promo_actions = pd.DataFrame([
        ["RC000 · Standard", "Keep", "Control baseline: 14.48 THB/cup before waste"],
        ["RC101 · Bundle Deal", "Limit", "Observed lift is below the level required to cover the discount"],
        ["RC102 · Double Day New User", "Redesign and test", "6.90 THB/cup before waste; observed lift has not reached break-even"],
        ["RC103 · Seasonal Push", "Limit", "Observed lift is below the level required to cover the discount"],
    ], columns=["Code and name", "Recommendation", "Reason"])
    st.dataframe(promo_actions, width="stretch", hide_index=True)

    st.markdown("#### Scorecard: how much contribution remains after discounting?")
    display_table(
        scorecard,
        ["base_code", "rate_code_name", "discount_pct", "units_sold", "cups_per_active_hour", "discount_cost_thb", "net_revenue_thb", "contribution_before_waste_per_cup_thb", "contribution_margin_pct", "decision_display"],
        {"base_code": "Code", "rate_code_name": "Name", "discount_pct": "Discount", "units_sold": "Units sold", "cups_per_active_hour": "Cups/hour", "discount_cost_thb": "Discount cost", "net_revenue_thb": "Net revenue", "contribution_before_waste_per_cup_thb": "Contribution before waste/cup", "contribution_margin_pct": "Contribution margin", "decision_display": "Recommendation"},
        money_columns=("discount_cost_thb", "net_revenue_thb", "contribution_before_waste_per_cup_thb"), percent_columns=("discount_pct", "contribution_margin_pct"), integer_columns=("units_sold",), decimal_columns=("cups_per_active_hour",),
    )
    left, right = st.columns(2)
    left.markdown("**Contribution before waste per cup**")
    left.bar_chart(scorecard.set_index("base_code")[["contribution_before_waste_per_cup_thb"]].rename(columns={"contribution_before_waste_per_cup_thb": "THB/cup"}), height=260)
    right.markdown("**Total discount cost**")
    right.bar_chart(scorecard.set_index("base_code")[["discount_cost_thb"]].rename(columns={"discount_cost_thb": "THB"}), height=260)

    st.markdown("#### Is the sales lift enough to cover the discount?")
    if not matched.empty:
        lift = matched.copy()
        display_table(
            lift,
            ["base_code", "rate_code_name", "discount_pct", "promo_cups_per_active_hour", "baseline_cups_per_active_hour", "actual_demand_lift_pct", "break_even_lift_pct", "actual_vs_breakeven_gap_pct", "incremental_contribution_thb", "decision_display"],
            {"base_code": "Code", "rate_code_name": "Name", "discount_pct": "Discount", "promo_cups_per_active_hour": "Promo cups/hour", "baseline_cups_per_active_hour": "Baseline cups/hour", "actual_demand_lift_pct": "Observed lift", "break_even_lift_pct": "Break-even lift", "actual_vs_breakeven_gap_pct": "Gap to break-even", "incremental_contribution_thb": "Incremental contribution vs. baseline", "decision_display": "Recommendation"},
            money_columns=("incremental_contribution_thb",), percent_columns=("discount_pct", "actual_demand_lift_pct", "break_even_lift_pct", "actual_vs_breakeven_gap_pct"), decimal_columns=("promo_cups_per_active_hour", "baseline_cups_per_active_hour"),
        )
        lift_chart = lift.set_index("base_code")[["actual_demand_lift_pct", "break_even_lift_pct"]].mul(100)
        lift_chart.columns = ["Observed lift (%)", "Required break-even lift (%)"]
        st.bar_chart(lift_chart, height=280)
        st.caption(f"Matched across the same SKU × kitchen × platform × weekday × month × hour × daypart for {int(metrics['matched_strata_count']):,} strata. Hours missing from the export are not treated as zero.")

    code_options = scorecard["base_code"].tolist()
    selected_code = st.selectbox("Select promotion code", code_options, index=code_options.index("RC102") if "RC102" in code_options else 0)
    selected = scorecard.set_index("base_code").loc[selected_code]
    selected_match = matched.loc[matched["base_code"] == selected_code]
    p1, p2, p3, p4, p5 = st.columns(5)
    p1.metric("Discount", pct(selected["discount_pct"]))
    p2.metric("Share of total sales", pct(selected["promo_share_cups"]))
    p3.metric("Discount cost", money(selected["discount_cost_thb"]))
    p4.metric("Contribution before waste/cup", money(selected["contribution_before_waste_per_cup_thb"], 2))
    p5.metric("Sales per hour", f"{selected['cups_per_active_hour']:,.1f} cups")
    if not selected_match.empty:
        row = selected_match.iloc[0]
        st.warning(f"{selected_code}: observed lift is {pct(row['actual_demand_lift_pct'])}, but {pct(row['break_even_lift_pct'])} is required to cover the discount. Incremental contribution vs. baseline is {money(row['incremental_contribution_thb'])}; do not scale broadly yet.")

    with st.expander("Promotion test design detail"):
        st.markdown("**Promotion efficiency and dependency**")
        efficiency = data["promo_efficiency"].copy()
        matrix = efficiency.set_index("base_code")[["actual_demand_lift_pct", "contribution_lift_pct"]].mul(100)
        matrix.columns = ["Sales lift (%)", "Contribution lift (%)"]
        st.bar_chart(matrix, height=260)
        display_table(
            efficiency,
            ["base_code", "actual_demand_lift_pct", "break_even_lift_pct", "contribution_lift_pct", "incremental_contribution_thb", "promo_discount_cost_thb", "promo_roi_on_discount", "decision"],
            {"base_code": "Code", "actual_demand_lift_pct": "Observed lift", "break_even_lift_pct": "Break-even lift", "contribution_lift_pct": "Contribution lift", "incremental_contribution_thb": "Incremental contribution vs. baseline", "promo_discount_cost_thb": "Discount cost", "promo_roi_on_discount": "Discount ROI", "decision": "Screening result"},
            money_columns=("incremental_contribution_thb", "promo_discount_cost_thb"), percent_columns=("actual_demand_lift_pct", "break_even_lift_pct", "contribution_lift_pct", "promo_roi_on_discount"),
        )
        dependency = data["promo_dependency"].copy()
        st.markdown("**Share of sales from promotions by product**")
        st.bar_chart(dependency.set_index("sku")[["promo_share_cups"]].mul(100).rename(columns={"promo_share_cups": "% of sales"}), height=240)
        display_table(
            dependency, list(dependency.columns),
            {"sku": "SKU", "promo_units": "Promotion units", "total_units": "Total units", "promo_share_cups": "Promotion share"},
            integer_columns=("promo_units", "total_units"), percent_columns=("promo_share_cups",),
        )

        st.markdown("**Find segments to stop or test further**")
        segment_view = st.selectbox("Break down by", ["SKU", "Kitchen", "Platform", "Hour", "Daypart"])
        segment_specs = {
            "SKU": ("promo_by_sku", "sku"), "Kitchen": ("promo_by_kitchen", "kitchen"),
            "Platform": ("promo_by_platform", "platform_name"), "Hour": ("promo_by_hour", "hour"), "Daypart": ("promo_by_daypart", "daypart"),
        }
        key, label_col = segment_specs[segment_view]
        segment = data[key].copy()
        view_columns = [label_col, "base_code", "matched_strata", "promo_units", "baseline_units", "promo_cups_per_active_hour", "baseline_cups_per_active_hour", "actual_demand_lift_pct", "break_even_lift_pct", "contribution_lift_pct", "incremental_contribution_thb", "decision"]
        display_table(
            segment.sort_values("incremental_contribution_thb"), view_columns,
            {label_col: segment_view, "base_code": "Code", "matched_strata": "Matched strata", "promo_units": "Promotion units", "baseline_units": "Baseline units", "promo_cups_per_active_hour": "Promo cups/hour", "baseline_cups_per_active_hour": "Baseline cups/hour", "actual_demand_lift_pct": "Observed lift", "break_even_lift_pct": "Break-even lift", "contribution_lift_pct": "Contribution lift", "incremental_contribution_thb": "Incremental contribution vs. baseline", "decision": "Screening result"},
            money_columns=("incremental_contribution_thb",), percent_columns=("actual_demand_lift_pct", "break_even_lift_pct", "contribution_lift_pct"), integer_columns=("matched_strata", "promo_units", "baseline_units"), decimal_columns=("promo_cups_per_active_hour", "baseline_cups_per_active_hour"),
            height=360,
        )

        st.markdown("**Maximum discount and required sales lift**")
        depth = data["promo_depth"].copy()
        depth_sku_options = depth["sku"].drop_duplicates().tolist()
        depth_sku = st.selectbox("Select product for discount depth", depth_sku_options, index=depth_sku_options.index("MixedBerryPremium") if "MixedBerryPremium" in depth_sku_options else 0)
        depth_view = depth.loc[depth["sku"] == depth_sku].sort_values("discount_pct").copy()
        depth_chart = depth_view.set_index("discount_pct")[["required_demand_lift_pct"]].mul(100)
        depth_chart.columns = ["Required lift to maintain contribution (%)"]
        st.line_chart(depth_chart, height=260)
        display_table(
            depth_view,
            ["discount_pct", "effective_price_thb", "promo_contribution_per_cup_thb", "contribution_delta_per_cup_thb", "required_demand_lift_pct"],
            {"discount_pct": "Discount", "effective_price_thb": "Post-discount price", "promo_contribution_per_cup_thb": "Promotion contribution/cup", "contribution_delta_per_cup_thb": "Contribution reduction/cup", "required_demand_lift_pct": "Required lift to maintain contribution"},
            money_columns=("effective_price_thb", "promo_contribution_per_cup_thb", "contribution_delta_per_cup_thb"), percent_columns=("discount_pct", "required_demand_lift_pct"),
        )

    st.markdown("#### Rules before scaling promotions")
    st.write("Scale a discount only when incremental contribution vs. the control is positive and observed lift exceeds the level needed to cover the discount. Start with SKU–kitchen–platform–daypart segments that pass the gate, and track waste alongside lift.")
    st.warning("These comparisons are associations in observed data, not causal effects, because there is no randomized customer assignment, cannibalization data, or stockout data. " + metrics["waste_boundary"])


def finance(data: dict) -> None:
    task_heading("Task 4 · Portfolio & budget performance", "Portfolio, kitchens & budget performance", "This P&L combines fruit, packaging, labor, commission, waste, and fixed overhead to identify what should be fixed first.")
    totals = data["finance_metrics"]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Sales revenue", money(totals["historical_revenue_thb"]))
    c2.metric("Revenue vs. target", money(totals["total_revenue_variance_thb"]))
    c3.metric("Contribution before waste", money(totals["historical_contribution_before_waste_thb"]), pct(totals["historical_contribution_margin_pct"]))
    c4.metric("Waste cost", money(totals["historical_waste_cost_thb"]))
    c5.metric("Modeled operating result", money(totals["historical_modeled_operating_result_thb"]), pct(totals["historical_operating_margin_pct"]))

    company = data["pnl_company"]
    st.markdown("#### From revenue to operating result")
    st.info("Revenue is the customer's post-promotion price. Contribution before waste = revenue − fruit cost − packaging − labor − commission. Modeled operating result = contribution before waste − recorded waste − kitchen fixed overhead.")
    waterfall = data["pnl_waterfall"]
    waterfall_chart = waterfall.set_index("pnl_component")[["thb"]].copy()
    waterfall_chart.index = ["Revenue", "Fruit cost", "Packaging", "Labor", "Commission", "Contribution before waste", "Waste cost", "Contribution after waste", "Fixed overhead", "Operating result"]
    st.bar_chart(waterfall_chart.rename(columns={"thb": "THB"}), height=320)
    display_table(
        waterfall,
        ["pnl_component", "thb", "definition"],
        {"pnl_component": "Component", "thb": "Amount", "definition": "Definition"},
        money_columns=("thb",),
    )

    st.markdown("#### Actual revenue vs. monthly budget")
    st.caption("The budget does not define whether GP includes commission, waste, labor, or fixed overhead, so revenue can be compared directly while the GP layer is shown for analysis only.")
    pnl = company.copy().set_index("month")
    chart = pnl[["gross_revenue_thb", "budget_revenue_thb"]].rename(columns={"gross_revenue_thb": "Actual revenue", "budget_revenue_thb": "Revenue target"})
    st.line_chart(chart, height=320)
    monthly_cols = ["month", "gross_revenue_thb", "budget_revenue_thb", "revenue_variance_thb", "revenue_variance_pct", "budget_gross_profit_thb", "product_margin_thb", "contribution_before_waste_thb", "contribution_after_waste_thb", "modeled_operating_result_thb", "budget_gp_boundary_status"]
    display_table(
        company, monthly_cols,
        {"month": "Month", "gross_revenue_thb": "Actual revenue", "budget_revenue_thb": "Revenue target", "revenue_variance_thb": "Variance", "revenue_variance_pct": "Variance (%)", "budget_gross_profit_thb": "Budget GP (boundary open)", "product_margin_thb": "Price less product cost", "contribution_before_waste_thb": "Contribution before waste", "contribution_after_waste_thb": "Contribution after waste", "modeled_operating_result_thb": "Modeled operating result", "budget_gp_boundary_status": "GP comparison status"},
        money_columns=("gross_revenue_thb", "budget_revenue_thb", "revenue_variance_thb", "budget_gross_profit_thb", "product_margin_thb", "contribution_before_waste_thb", "contribution_after_waste_thb", "modeled_operating_result_thb"), percent_columns=("revenue_variance_pct",), date_columns=("month",),
        height=370,
    )

    st.markdown("#### What should we do by product?")
    portfolio = data["portfolio"].copy()
    sku_action_map = {
        "Watermelon": "Protect availability; test price during peak demand", "Pineapple": "Protect availability; test price during peak demand",
        "Guava": "Protect availability; run a controlled price test", "PassionFruit": "Review distribution, waste, and product role",
        "MixedBerryPremium": "Fix price, portion, and preparation before scaling",
    }
    portfolio["action_display"] = portfolio["sku"].map(sku_action_map)
    left, right = st.columns(2)
    with left:
        st.bar_chart(portfolio.set_index("sku")[["contribution_after_waste_thb"]].rename(columns={"contribution_after_waste_thb": "Contribution after waste (THB)"}), height=280)
    with right:
        st.scatter_chart(portfolio, x="units_sold", y="contribution_after_waste_margin_pct", size="gross_revenue_thb", color="sku", x_label="Units sold (cups)", y_label="Contribution-after-waste margin", height=280)
    display_table(
        portfolio.sort_values("contribution_after_waste_thb", ascending=False),
        ["sku", "units_sold", "gross_revenue_thb", "revenue_share", "contribution_after_waste_thb", "contribution_after_waste_per_cup_thb", "contribution_after_waste_margin_pct", "waste_cost_thb", "waste_rate", "action_display"],
        {"sku": "SKU", "units_sold": "Units sold", "gross_revenue_thb": "Revenue", "revenue_share": "Revenue share", "contribution_after_waste_thb": "Contribution after waste", "contribution_after_waste_per_cup_thb": "Contribution/cup", "contribution_after_waste_margin_pct": "Contribution margin", "waste_cost_thb": "Waste cost", "waste_rate": "Waste rate", "action_display": "Recommended action"},
        money_columns=("gross_revenue_thb", "contribution_after_waste_thb", "contribution_after_waste_per_cup_thb", "waste_cost_thb"), percent_columns=("revenue_share", "contribution_after_waste_margin_pct", "waste_rate"), integer_columns=("units_sold",),
    )
    st.caption("Product-level contribution is after waste but before allocating kitchen fixed overhead, so it is not product net profit.")

    st.markdown("#### Which kitchens should be fixed first?")
    kitchen_rollup = data["finance_kitchen"].copy()
    kitchen_action_map = {"BKK_Ladprao": "Fix first: negative result and highest waste", "BKK_Sukhumvit": "Fix second: negative result", "Pattaya_Beach": "Protect positive result and control waste", "Pattaya_Central": "Protect positive result and control waste"}
    kitchen_rollup["action_display"] = kitchen_rollup["kitchen"].map(kitchen_action_map)
    left, right = st.columns(2)
    left.markdown("**Modeled operating result by kitchen**")
    left.bar_chart(kitchen_rollup.set_index("kitchen")[["modeled_operating_result_thb"]].rename(columns={"modeled_operating_result_thb": "THB"}), height=270)
    right.markdown("**Waste cost by kitchen**")
    right.bar_chart(kitchen_rollup.set_index("kitchen")[["waste_cost_thb"]].rename(columns={"waste_cost_thb": "THB"}), height=270)
    display_table(
        kitchen_rollup.sort_values("modeled_operating_result_thb"),
        ["kitchen", "units_sold", "gross_revenue_thb", "contribution_before_waste_thb", "waste_cost_thb", "waste_rate", "fixed_monthly_overhead_thb", "modeled_operating_result_thb", "operating_margin_pct", "action_display"],
        {"kitchen": "Kitchen", "units_sold": "Units sold", "gross_revenue_thb": "Revenue", "contribution_before_waste_thb": "Contribution before waste", "waste_cost_thb": "Waste cost", "waste_rate": "Waste rate", "fixed_monthly_overhead_thb": "Fixed overhead", "modeled_operating_result_thb": "Modeled operating result", "operating_margin_pct": "Operating margin", "action_display": "Priority"},
        money_columns=("gross_revenue_thb", "contribution_before_waste_thb", "waste_cost_thb", "fixed_monthly_overhead_thb", "modeled_operating_result_thb"), percent_columns=("waste_rate", "operating_margin_pct"), integer_columns=("units_sold",),
    )
    kitchen_options = kitchen_rollup["kitchen"].tolist()
    selected_kitchen = st.selectbox("View monthly kitchen trend", kitchen_options, index=kitchen_options.index("BKK_Ladprao") if "BKK_Ladprao" in kitchen_options else 0)
    kitchen = data["pnl_kitchen"].loc[data["pnl_kitchen"]["kitchen"] == selected_kitchen].copy().set_index("month")
    st.line_chart(kitchen[["contribution_after_waste_thb", "modeled_operating_result_thb"]].rename(columns={"contribution_after_waste_thb": "Contribution after waste", "modeled_operating_result_thb": "Modeled operating result"}), height=260)

    with st.expander("Cost, waste, and sensitivity detail"):
        st.markdown("**Sources of month-to-month revenue change**")
        decomp = data["revenue_decomp"].dropna(subset=["prior_month"]).copy()
        if not decomp.empty:
            st.bar_chart(decomp.set_index("month")[["volume_effect_thb", "price_mix_effect_thb"]].rename(columns={"volume_effect_thb": "Volume effect", "price_mix_effect_thb": "Price/mix effect"}), height=250)
            display_table(
                decomp, ["month", "revenue_change_thb", "volume_effect_thb", "price_mix_effect_thb", "decomposition_check_thb", "basis"],
                {"month": "Month", "revenue_change_thb": "Revenue change", "volume_effect_thb": "Volume effect", "price_mix_effect_thb": "Price/mix effect", "decomposition_check_thb": "Check", "basis": "Basis"},
                money_columns=("revenue_change_thb", "volume_effect_thb", "price_mix_effect_thb", "decomposition_check_thb"), date_columns=("month",),
            )
        st.markdown("**Waste by kitchen and SKU**")
        waste = data["waste_heatmap"].copy()
        waste_table = waste.pivot(index="kitchen", columns="sku", values="waste_rate").mul(100).round(1)
        st.dataframe(waste_table.style.background_gradient(cmap="YlOrRd").format("{:.1f}%"), width="stretch")
        display_table(
            waste.sort_values("waste_rate", ascending=False), ["kitchen", "sku", "units_sold", "units_wasted", "waste_rate", "waste_cost_thb", "waste_cost_pct_revenue"],
            {"kitchen": "Kitchen", "sku": "SKU", "units_sold": "Units sold", "units_wasted": "Waste (cups)", "waste_rate": "Waste rate", "waste_cost_thb": "Waste cost", "waste_cost_pct_revenue": "Waste cost/revenue"},
            integer_columns=("units_sold", "units_wasted"), percent_columns=("waste_rate", "waste_cost_pct_revenue"), money_columns=("waste_cost_thb",),
        )
        st.markdown("**Fruit-cost trend and contribution distribution**")
        fruit_cost = data["fruit_cost_trend"].copy()
        st.line_chart(fruit_cost.pivot(index="week_start", columns="sku", values="fruit_cost_per_cup_thb"), height=270)
        pareto = data["sku_kitchen_pareto"].copy()
        display_table(
            pareto.head(12), ["kitchen", "sku", "units_sold", "gross_revenue_thb", "contribution_after_waste_thb", "contribution_mix", "cumulative_contribution_mix", "profit_rank"],
            {"kitchen": "Kitchen", "sku": "SKU", "units_sold": "Units sold", "gross_revenue_thb": "Revenue", "contribution_after_waste_thb": "Contribution after waste", "contribution_mix": "Contribution mix", "cumulative_contribution_mix": "Cumulative share", "profit_rank": "Rank"},
            integer_columns=("units_sold", "profit_rank"), money_columns=("gross_revenue_thb", "contribution_after_waste_thb"), percent_columns=("contribution_mix", "cumulative_contribution_mix"),
        )
        st.markdown("**Operating-result recovery opportunities from historical data**")
        display_table(
            data["gap_closing"], ["gap_or_opportunity", "thb", "basis", "status"],
            {"gap_or_opportunity": "Item", "thb": "Value", "basis": "Basis", "status": "Status"}, money_columns=("thb",),
        )
        display_table(
            data["finance_scenarios"], ["scenario", "modeled_operating_result_thb", "delta_vs_current_thb", "basis", "status"],
            {"scenario": "Scenario", "modeled_operating_result_thb": "Modeled operating result", "delta_vs_current_thb": "Change vs. current", "basis": "Basis", "status": "Status"}, money_columns=("modeled_operating_result_thb", "delta_vs_current_thb"),
        )
        st.caption("This sensitivity analysis screens historical opportunities: promotion results are associations before waste, and waste sensitivity holds waste cost per cup constant. It is not guaranteed savings or a direct bridge to budget GP.")


def forecast_inventory(data: dict) -> None:
    task_heading("Task 5 · Inventory & 3-month outlook", "3-month outlook & preparation plan", "Forecast demand by kitchen–SKU and convert it into a break-even plan and waste-inclusive preparation targets without creating purchase orders from unavailable data.")
    scenario = data["scenario"].copy()
    base = scenario.loc[scenario["scenario"] == "base"]
    requirements = data["requirements"]
    policy = data["inventory_policy"].copy()
    recovery = data["recovery_summary"]
    recovery_monthly = data["recovery_monthly"].copy()
    recovery_prep = data["recovery_prep"].copy()
    recovery_kitchen = data["recovery_kitchen"].copy()
    recovery_sensitivity = data["recovery_sensitivity"].copy()
    recovery_bridge = data["recovery_bridge"].copy()
    recovery_nov_evidence = data["recovery_nov_evidence"].copy()
    recovery_nov_capacity = data["recovery_nov_capacity"].copy()
    baseline_units = float(base["forecast_units"].sum())
    baseline_prep = float(requirements["prep_target_cups_base"].sum())
    target_units = float(recovery_monthly["planned_units"].sum())
    target_prep = float(recovery_monthly["planned_prep"].sum())
    nov_base_units = float(base.loc[pd.to_datetime(base["month"]).dt.month == 11, "forecast_units"].sum())
    nov_target_units = float(recovery_monthly.loc[pd.to_datetime(recovery_monthly["month"]).dt.month == 11, "planned_units"].sum())
    nov_growth_pct = nov_target_units / nov_base_units - 1 if nov_base_units else 0.0
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Baseline forecast", f"{baseline_units:,.0f} cups")
    c2.metric("Planning range", f"{data['metrics']['base_forecast_lower_units']:,.0f}–{data['metrics']['base_forecast_upper_units']:,.0f} cups")
    c3.metric("Baseline forecast prep target", f"{baseline_prep:,.0f} cups")
    c4.metric("Expected waste", f"{requirements['expected_waste_units_base'].sum():,.0f} cups")
    c5.metric("Baseline forecast result", money(base["modeled_operating_result_thb"].sum()))
    st.caption("The planning range is calculated from the selected method's WAPE, not a statistical confidence interval.")
    st.info(
        f"This page shows two sets of numbers: the baseline forecast expects {baseline_units:,.0f} cups sold and {baseline_prep:,.0f} cups prepared without interventions; "
        f"the break-even target expects {target_units:,.0f} cups sold and {target_prep:,.0f} cups prepared assuming planned prices, promotions, waste, costs, and sales targets are achieved. "
        f"November is approximately {pct(nov_growth_pct)} above the baseline forecast, so the two sets should not be treated as one forecast."
    )

    st.markdown("#### Realistic cumulative break-even target")
    st.warning(
        f"This is a management target back-solved from break-even, not a new forecast or profit guarantee: "
        f"if all interventions are delivered, the modeled result is {money(recovery['proposed_target_result_thb'])} over 3 months. "
        f"The first month remains loss-making, and month 3 requires approximately {pct(recovery['final_month_core_growth_needed_for_3m_breakeven'])} more net Watermelon, Pineapple, and Guava sales to reach cumulative break-even."
    )
    nov_evidence = recovery["november_growth_evidence"]
    st.caption(
        f"Although the November target is {pct(nov_growth_pct)} above the November forecast, the management target grows from October to November by "
        f"{pct(nov_evidence['conditional_target_oct_to_nov_total_growth'])}; validate with actual sales before increasing preparation."
    )

    st.markdown("#### Evidence base and November target gate")
    st.info(
        f"Actual 2025 sales grew from October to November by {pct(nov_evidence['historical_oct_to_nov_total_growth'])} across all products "
        f"and {pct(nov_evidence['historical_oct_to_nov_core_growth'])} for Watermelon, Pineapple, and Guava. "
        f"This supports a seasonal assumption only—not a new forecast. {nov_evidence['limitation']}"
    )
    evidence_view = recovery_nov_evidence.copy()
    evidence_view["month_label"] = evidence_view["month"].map(lambda value: MONTH_NAMES[int(value)])
    display_table(
        evidence_view,
        ["month_label", "historical_total_cups_2025", "historical_total_mom_growth", "historical_core_cups_2025", "historical_core_mom_growth", "conditional_target_total_cups_2026", "conditional_target_total_mom_growth", "conditional_target_core_cups_2026", "conditional_target_core_mom_growth"],
        {"month_label": "Month", "historical_total_cups_2025": "Total actual cups 2025", "historical_total_mom_growth": "Total actual MoM", "historical_core_cups_2025": "Core actual cups 2025", "historical_core_mom_growth": "Core actual MoM", "conditional_target_total_cups_2026": "Conditional total target 2026", "conditional_target_total_mom_growth": "Total target MoM", "conditional_target_core_cups_2026": "Conditional core target 2026", "conditional_target_core_mom_growth": "Core target MoM"},
        integer_columns=("historical_total_cups_2025", "historical_core_cups_2025", "conditional_target_total_cups_2026", "conditional_target_core_cups_2026"),
        percent_columns=("historical_total_mom_growth", "historical_core_mom_growth", "conditional_target_total_mom_growth", "conditional_target_core_mom_growth"),
    )
    st.write(
        "Before releasing incremental volume, October tests must measure incremental core cups after cannibalization and show positive contribution after commission/waste; "
        "confirm advertising and extra-shift costs remain within budget; and pass a kitchen-level capacity trial. If any gate fails, reforecast from actuals and do not produce to chase a profit target."
    )
    display_table(
        recovery_nov_capacity,
        ["kitchen", "net_extra_cups_per_day", "extra_core_cups_per_day"],
        {"kitchen": "Kitchen", "net_extra_cups_per_day": "Net extra cups/day", "extra_core_cups_per_day": "Extra core cups/day"},
        decimal_columns=("net_extra_cups_per_day", "extra_core_cups_per_day"),
    )
    st.caption(
        f"Total capacity gate: add {recovery['november_capacity_gate']['net_extra_cups_per_day']:,.1f} net cups/day, "
        f"including {recovery['november_capacity_gate']['extra_core_cups_per_day']:,.1f} extra core cups/day because the plan pauses MixedBerry."
    )
    recovery_monthly["month"] = pd.to_datetime(recovery_monthly["month"])
    display_table(
        recovery_monthly,
        ["month", "planned_units", "planned_prep", "contribution_thb", "fixed_overhead_thb", "implementation_cost_thb", "operating_result_thb", "cumulative_result_thb"],
        {"month": "Month", "planned_units": "Sales target", "planned_prep": "Prep target at target sales", "contribution_thb": "Contribution after waste", "fixed_overhead_thb": "Fixed overhead at target", "implementation_cost_thb": "Implementation budget", "operating_result_thb": "Operating result", "cumulative_result_thb": "Cumulative result"},
        date_columns=("month",), integer_columns=("planned_units", "planned_prep"), money_columns=("contribution_thb", "fixed_overhead_thb", "implementation_cost_thb", "operating_result_thb", "cumulative_result_thb"),
    )
    st.caption("The main conditions are lower waste, fruit cost, and fixed overhead plus net sales after the planned price and promotion changes. If delivery is incomplete, the result returns to negative.")

    st.markdown("#### Historical sales followed by forecast sales")
    history_weekly = data["weekly_demand"].groupby("week_start", as_index=True)["units_sold"].sum().rename("Historical cups")
    future_weekly = data["forecast"].assign(week_start=lambda d: d["date"] - pd.to_timedelta(d["date"].dt.dayofweek, unit="D")).groupby("week_start", as_index=True).agg(
        base_forecast=("forecast_units_base", "sum"), lower=("forecast_lower_units", "sum"), upper=("forecast_upper_units", "sum")
    ).rename(columns={"base_forecast": "Base forecast", "lower": "Planning lower bound", "upper": "Planning upper bound"})
    history_weekly = history_weekly.rename("Historical cups")
    history_chart = pd.concat([history_weekly, future_weekly], axis=1)
    st.line_chart(history_chart, height=280)

    st.markdown("#### Modeled result across 3 scenarios")
    scenario_chart = scenario.pivot(index="month", columns="scenario_display", values="modeled_operating_result_thb")
    scenario_chart = scenario_chart.rename(columns={"Base case": "Base case", "Downside case": "Downside case", "Optimized case": "Optimized case"})
    scenario_chart = scenario_chart.reindex(columns=["Base case", "Optimized case", "Downside case"])
    st.line_chart(scenario_chart, height=280)
    scenario_total = scenario.groupby("scenario_display", as_index=False).agg(
        forecast_units=("forecast_units", "sum"), revenue_thb=("revenue_thb", "sum"), contribution_after_waste_thb=("contribution_after_waste_thb", "sum"), fixed_overhead_thb=("fixed_overhead_thb", "sum"), modeled_operating_result_thb=("modeled_operating_result_thb", "sum")
    )
    scenario_total["scenario_display_name"] = scenario_total["scenario_display"].map({"Base case": "Base case", "Downside case": "Downside case", "Optimized case": "Optimized case"})
    scenario_total["sort_order"] = scenario_total["scenario_display"].map({"Base case": 0, "Optimized case": 1, "Downside case": 2})
    display_table(
        scenario_total.sort_values("sort_order"),
        ["scenario_display_name", "forecast_units", "revenue_thb", "contribution_after_waste_thb", "fixed_overhead_thb", "modeled_operating_result_thb"],
        {"scenario_display_name": "Scenario", "forecast_units": "Forecast units", "revenue_thb": "Revenue", "contribution_after_waste_thb": "Contribution after waste", "fixed_overhead_thb": "Fixed overhead", "modeled_operating_result_thb": "Modeled operating result"},
        integer_columns=("forecast_units",), money_columns=("revenue_thb", "contribution_after_waste_thb", "fixed_overhead_thb", "modeled_operating_result_thb"),
    )
    optimized_result = float(scenario_total.loc[scenario_total["scenario_display"] == "Optimized case", "modeled_operating_result_thb"].iloc[0])
    base_result = float(scenario_total.loc[scenario_total["scenario_display"] == "Base case", "modeled_operating_result_thb"].iloc[0])
    st.warning(f"The optimized case uses standard realized pricing and reduces waste by 25% without assuming a price-driven sales lift. It improves by {money(optimized_result - base_result)} vs. the base case but still loses {money(-optimized_result)} over 3 months. This gap must be closed with real actions not already included in the optimized assumptions.")

    st.markdown("#### Preparation target after sales confirmation")
    st.info("Do not increase preparation immediately to match the growth target. The table below shows demand if planned sales actually occur. Confirm with orders and intraday sales first, then recalculate preparation every 7 days.")
    recovery_prep["month"] = pd.to_datetime(recovery_prep["month"])
    display_table(
        recovery_prep,
        ["month", "kitchen", "sku", "baseline_units", "target_sales", "target_prep", "expected_waste", "waste_rate_target", "target_price", "extra_sales_vs_base", "contribution_per_cup"],
        {"month": "Month", "kitchen": "Kitchen", "sku": "SKU", "baseline_units": "Baseline forecast", "target_sales": "Sales target", "target_prep": "Prep target", "expected_waste": "Expected waste", "waste_rate_target": "Target waste rate", "target_price": "Test target price", "extra_sales_vs_base": "Extra sales vs. baseline", "contribution_per_cup": "Post-waste contribution/cup"},
        date_columns=("month",), integer_columns=("baseline_units", "target_sales", "target_prep", "expected_waste", "extra_sales_vs_base"), percent_columns=("waste_rate_target",), money_columns=("target_price", "contribution_per_cup",), height=420,
    )
    st.caption("This is a modeled cup-preparation target, not a raw-material order quantity, because stock on hand, inbound, lead time, shelf life, and BOM/yield are unavailable.")

    with st.expander("Kitchen results and downside if targets are missed"):
        recovery_kitchen["month"] = pd.to_datetime(recovery_kitchen["month"])
        display_table(
            recovery_kitchen,
            ["month", "kitchen", "target_sales", "target_prep", "contribution_thb", "fixed_overhead_thb", "operating_before_central_implementation_thb"],
            {"month": "Month", "kitchen": "Kitchen", "target_sales": "Sales target", "target_prep": "Prep target", "contribution_thb": "Contribution after waste", "fixed_overhead_thb": "Fixed overhead at target", "operating_before_central_implementation_thb": "Kitchen result before central budget"},
            date_columns=("month",), integer_columns=("target_sales", "target_prep"), money_columns=("contribution_thb", "fixed_overhead_thb", "operating_before_central_implementation_thb",),
        )
        display_table(
            recovery_sensitivity,
            ["scenario", "operating_result_thb", "gap_to_zero_thb"],
            {"scenario": "Scenario", "operating_result_thb": "Total 3-month operating result", "gap_to_zero_thb": "Gap to break-even"},
            money_columns=("operating_result_thb", "gap_to_zero_thb",),
        )
        st.markdown("**Sequential gap-closing bridge**")
        display_table(
            recovery_bridge,
            ["step", "increment_thb", "result_thb"],
            {"step": "Step", "increment_thb": "Increment from prior step", "result_thb": "Cumulative modeled result"},
            money_columns=("increment_thb", "result_thb",),
        )
        st.caption("Each action is calculated sequentially, so row-level savings should not be added again as independent benefits.")

    st.markdown("#### Preparation target: view by product and kitchen")
    sku_monthly = data["forecast_monthly_sku"].pivot(index="month", columns="sku", values="forecast_units")
    st.bar_chart(sku_monthly, height=280)
    st.caption("The forecast model runs at 20 kitchen × SKU pairs; this chart aggregates to product level for readability.")
    col1, col2 = st.columns(2)
    kitchens = ["All"] + sorted(data["forecast"]["kitchen"].unique().tolist())
    skus = ["All"] + sorted(data["forecast"]["sku"].unique().tolist())
    selected_kitchen = col1.selectbox("Select kitchen", kitchens, format_func=lambda option: "All kitchens" if option == "All" else option)
    selected_sku = col2.selectbox("Select SKU", skus, format_func=lambda option: "All SKUs" if option == "All" else option)
    filtered = data["forecast"].copy()
    req = requirements.copy()
    if selected_kitchen != "All":
        filtered = filtered.loc[filtered["kitchen"] == selected_kitchen]
        req = req.loc[req["kitchen"] == selected_kitchen]
    if selected_sku != "All":
        filtered = filtered.loc[filtered["sku"] == selected_sku]
        req = req.loc[req["sku"] == selected_sku]
    daily = filtered.groupby("date", as_index=True)["forecast_units_base"].sum().to_frame("Forecast units (cups)")
    st.line_chart(daily, height=300)
    req["month"] = req["date"].dt.to_period("M").dt.to_timestamp()
    prep_monthly = req.groupby(["month", "kitchen", "sku"], as_index=False).agg(
        forecast_lower_units=("forecast_lower_units", "sum"), forecast_units_base=("forecast_units_base", "sum"), forecast_upper_units=("forecast_upper_units", "sum"), prep_target_cups_lower=("prep_target_cups_lower", "sum"), prep_target_cups_base=("prep_target_cups_base", "sum"), prep_target_cups_upper=("prep_target_cups_upper", "sum"), expected_waste_units_base=("expected_waste_units_base", "sum")
    )
    display_table(
        prep_monthly,
        ["month", "kitchen", "sku", "forecast_lower_units", "forecast_units_base", "forecast_upper_units", "prep_target_cups_lower", "prep_target_cups_base", "prep_target_cups_upper", "expected_waste_units_base"],
        {"month": "Month", "kitchen": "Kitchen", "sku": "SKU", "forecast_lower_units": "Forecast lower bound", "forecast_units_base": "Base forecast units", "forecast_upper_units": "Forecast upper bound", "prep_target_cups_lower": "Lower prep target", "prep_target_cups_base": "Base prep target", "prep_target_cups_upper": "Upper prep target", "expected_waste_units_base": "Expected waste"},
        date_columns=("month",), integer_columns=("forecast_lower_units", "forecast_units_base", "forecast_upper_units", "prep_target_cups_lower", "prep_target_cups_base", "prep_target_cups_upper", "expected_waste_units_base"), height=360,
    )

    st.markdown("#### Preparation and replenishment policy")
    st.write("ABC is based on 3-month post-waste contribution, and XYZ on 12-week demand volatility. Safety stock is a proposed policy at 95% service level (Z = 1.65), reviewed every 7 days; it is not supplier lead time.")
    alert_map = {"green": "Normal", "amber": "High waste", "red": "Negative contribution + high waste"}
    policy["alert_display"] = policy["inventory_alert"].str.lower().map(alert_map).fillna(policy["inventory_alert"])
    display_table(
        policy.sort_values(["inventory_alert", "waste_rate"], ascending=[True, False]),
        ["kitchen", "sku", "forecast_3m_cups", "avg_weekly_demand_cups", "demand_cv", "waste_rate", "contribution_after_waste_per_cup_thb", "abc_class", "xyz_class", "safety_stock_cups_policy", "target_stock_next_7d_cups", "alert_display", "inventory_policy"],
        {"kitchen": "Kitchen", "sku": "SKU", "forecast_3m_cups": "3-month forecast", "avg_weekly_demand_cups": "Average/week", "demand_cv": "Demand volatility", "waste_rate": "Waste rate", "contribution_after_waste_per_cup_thb": "Post-waste contribution/cup", "abc_class": "ABC", "xyz_class": "XYZ", "safety_stock_cups_policy": "Proposed safety stock", "target_stock_next_7d_cups": "7-day target stock", "alert_display": "Status", "inventory_policy": "Policy"},
        integer_columns=("forecast_3m_cups", "avg_weekly_demand_cups", "safety_stock_cups_policy", "target_stock_next_7d_cups"), percent_columns=("demand_cv", "waste_rate"), money_columns=("contribution_after_waste_per_cup_thb",), height=430,
    )
    st.caption("Kitchen–SKU pairs marked “High waste” or “Negative contribution + high waste” should use smaller, more frequent batches. This is a production alert, not an automatic purchase order.")

    with st.expander("Forecast method, cost sensitivity, and ordering scope"):
        st.markdown("**How was the forecast method selected?**")
        st.write(f"`{data['metrics']['selected_method']}` was selected because its mean WAPE across four rolling-origin backtest cutoffs was lowest at {pct(data['metrics']['selected_method_mean_wape'])} across five methods, using data only through 31 Aug 2026.")
        backtest_view = data["backtest"].copy()
        display_table(
            backtest_view, ["method", "cutoffs", "mae", "wape", "bias_pct"],
            {"method": "Method", "cutoffs": "Test cutoffs", "mae": "MAE (cups)", "wape": "WAPE", "bias_pct": "Bias"},
            integer_columns=("cutoffs",), percent_columns=("wape", "bias_pct"), decimal_columns=("mae",),
        )
        st.caption(data["metrics"]["forecast_uncertainty_basis"])
        st.markdown("**Monthly P&L for all scenarios**")
        display_table(
            scenario,
            ["scenario_display", "month", "forecast_units", "revenue_thb", "sold_fruit_cost_thb", "sold_packaging_cost_thb", "sold_labor_cost_thb", "commission_thb", "waste_cost_thb", "contribution_after_waste_thb", "fixed_overhead_thb", "modeled_operating_result_thb", "operating_margin_pct"],
            {"scenario_display": "Scenario", "month": "Month", "forecast_units": "Forecast units", "revenue_thb": "Revenue", "sold_fruit_cost_thb": "Fruit cost", "sold_packaging_cost_thb": "Packaging", "sold_labor_cost_thb": "Labor", "commission_thb": "Commission", "waste_cost_thb": "Waste cost", "contribution_after_waste_thb": "Contribution after waste", "fixed_overhead_thb": "Fixed overhead", "modeled_operating_result_thb": "Modeled operating result", "operating_margin_pct": "Operating margin"},
            date_columns=("month",), integer_columns=("forecast_units",), money_columns=("revenue_thb", "sold_fruit_cost_thb", "sold_packaging_cost_thb", "sold_labor_cost_thb", "commission_thb", "waste_cost_thb", "contribution_after_waste_thb", "fixed_overhead_thb", "modeled_operating_result_thb"), percent_columns=("operating_margin_pct",), height=380,
        )
        st.caption(data["metrics"]["commission_basis"] + " " + data["metrics"]["mixedberry_note"])
        st.markdown("**What if fruit costs increase?**")
        stress = data["fruit_cost_stress"].copy()
        stress["uplift_label"] = stress["fruit_cost_uplift_pct"].map(lambda value: pct(value, 0))
        st.line_chart(stress.set_index("uplift_label")[["modeled_operating_result_thb"]].rename(columns={"modeled_operating_result_thb": "Modeled operating result (THB)"}), height=240)
        display_table(
            stress, ["fruit_cost_uplift_pct", "forecast_units", "revenue_thb", "fruit_cost_thb", "waste_cost_thb", "contribution_after_waste_thb", "fixed_overhead_thb", "modeled_operating_result_thb", "operating_margin_pct"],
            {"fruit_cost_uplift_pct": "Fruit cost increase", "forecast_units": "Forecast units", "revenue_thb": "Revenue", "fruit_cost_thb": "Fruit cost", "waste_cost_thb": "Waste cost", "contribution_after_waste_thb": "Contribution after waste", "fixed_overhead_thb": "Fixed overhead", "modeled_operating_result_thb": "Modeled operating result", "operating_margin_pct": "Operating margin"},
            percent_columns=("fruit_cost_uplift_pct", "operating_margin_pct"), integer_columns=("forecast_units",), money_columns=("revenue_thb", "fruit_cost_thb", "waste_cost_thb", "contribution_after_waste_thb", "fixed_overhead_thb", "modeled_operating_result_thb"),
        )
        st.markdown("**Formula to use when inventory data is complete**")
        st.code("target_stock = forecast_during_review_period + safety_stock\norder_qty = max(0, target_stock - usable_on_hand - usable_inbound + committed_demand)", language="text")
        st.info("Actual order quantities are not calculated because this case lacks stock on hand, inbound, supplier lead time, shelf life, BOM/recipe yield, and stockout flags. Until those data are available, use cup-based prep targets and the safety-stock policy for daily production, and review the forecast weekly when new actuals arrive.")


def data_quality(data: dict) -> None:
    task_heading("Task 1 · Data quality", "Data quality & limitations", "Screen the raw data before making decisions so revenue, demand, promotions, and P&L are not distorted by duplicates or non-menu items.")
    readiness = data["readiness"]
    raw = readiness["raw_orders"]
    candidate = readiness["candidate_preparation"]
    waste = readiness["waste"]
    reconciliation = data["reconciliation"]
    audit = data["audit"]
    checks = audit["checks"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Raw order rows", f"{checks['raw_order_rows']:,}")
    c2.metric("Retained menu rows", f"{checks['retained_candidate_menu_rows']:,}")
    c3.metric("Revenue after screening", money(reconciliation["retained_menu_revenue_thb"]))

    st.markdown("#### From raw data to released analytical data")
    st.markdown(
        f"<div class='callout'><strong>{reconciliation['raw_rows']:,} raw rows</strong> → removed {reconciliation['duplicate_excess_rows_removed']:,} duplicate rows → excluded {reconciliation['non_menu_rows_excluded']:,} non-menu rows → <strong>{reconciliation['retained_menu_rows']:,} menu rows</strong> retained for analysis</div>",
        unsafe_allow_html=True,
    )
    st.caption(f"Without duplicate removal, revenue would be overstated by approximately {money(reconciliation['duplicate_revenue_removed_thb'])}.")

    st.markdown("#### Checks and handling")
    screening = pd.DataFrame([
        ["Missing values", "No missing values found in 9 raw order fields", "No imputation required for order fields"],
        ["Exact duplicate rows", f"{raw['exact_duplicate_excess_rows']:,} excess rows with {money(reconciliation['duplicate_revenue_removed_thb'])} revenue", "Removed excess rows and retained the audit trail"],
        ["Date, time, and units", f"Invalid dates: {raw['invalid_dates']}; invalid hours: {raw['invalid_hours']}; non-positive units: {raw['nonpositive_units']}", "No such records enter the released dataset"],
        ["Price and revenue", f"Price × units mismatches: {raw['revenue_identity_mismatch_rows_over_001_thb']}; discount formula mismatches: {candidate['price_discount_formula_mismatch_rows_over_001_thb']}", "Keep observed post-promotion prices and do not deduct discounts twice"],
        ["Product/code mapping", f"Unknown base codes: {len(candidate['unknown_base_codes'])}; SKU suffix mismatches: {candidate['sku_suffix_mismatch_rows']}", "Use only the 5 mapped core products; exclude 370 non-menu rows"],
        ["Cost completeness", f"{candidate['missing_exact_week_fruit_cost_rows']} sales rows and {waste['missing_estimated_waste_cost_rows']} waste rows require proxies", "Expose assumptions and never replace missing costs with zero"],
        ["Extreme values", "Do not remove valid rows only because sales or prices are high", "Keep peaks and seasonality; remove only malformed or unmapped records"],
    ], columns=["Check", "Evidence", "Handling"])
    st.dataframe(screening, width="stretch", hide_index=True)

    st.markdown("#### Pre- and post-screening reconciliation")
    bridge = pd.DataFrame([
        ["Raw export", reconciliation["raw_rows"], reconciliation["raw_units"], reconciliation["raw_revenue_thb"]],
        ["Less duplicate excess", -reconciliation["duplicate_excess_rows_removed"], -reconciliation["duplicate_units_removed"], -reconciliation["duplicate_revenue_removed_thb"]],
        ["Less non-menu rows", -reconciliation["non_menu_rows_excluded"], -reconciliation["non_menu_units_excluded"], -reconciliation["non_menu_revenue_excluded_thb"]],
        ["Released menu data", reconciliation["retained_menu_rows"], reconciliation["retained_menu_units"], reconciliation["retained_menu_revenue_thb"]],
    ], columns=["Bridge", "Rows", "Units", "Revenue (THB)"])
    bridge["Bridge"] = ["Raw data", "Less duplicate excess", "Less non-menu rows", "Released menu data"]
    display_table(
        bridge, ["Bridge", "Rows", "Units", "Revenue (THB)"],
        {"Bridge": "Step", "Rows": "Rows", "Units": "Units", "Revenue (THB)": "Revenue"}, integer_columns=("Rows", "Units"), money_columns=("Revenue (THB)",),
    )

    st.markdown("#### Open issues to monitor")
    issues = data["issues"].copy()
    issues["severity_display"] = issues["severity"].map({"high": "High", "medium": "Medium", "low": "Low"}).fillna(issues["severity"])
    issues["status_display"] = issues["status"].map({"released": "Released", "assumed": "Assumed", "open": "Open"}).fillna(issues["status"])
    display_table(
        issues, ["issue_id", "severity_display", "status_display", "issue", "impact", "recommended_action", "evidence"],
        {"issue_id": "ID", "severity_display": "Severity", "status_display": "Status", "issue": "Issue", "impact": "Impact", "recommended_action": "Recommended action", "evidence": "Evidence"},
        height=330,
    )

    st.markdown("#### Validation status")
    release_qa = data["data_qa"]
    st.success(f"Data-release QA: {release_qa['status']} · Passed {len(release_qa['checks']) - release_qa['failed_count']}/{len(release_qa['checks'])} checks")
    qa_df = pd.DataFrame(data["qa"]["checks"])
    qa_columns = [column for column in ["name", "result", "expected", "actual", "owner", "impact"] if column in qa_df]
    st.dataframe(qa_df[qa_columns].astype(str).rename(columns={"name": "Check", "result": "Result", "expected": "Expected", "actual": "Actual", "owner": "Original owner", "impact": "Impact"}), width="stretch", hide_index=True, height=360)
    st.caption("Source files are read-only and proxies are explicitly identified. Remaining limitations include the budget GP boundary, waste coverage, and unavailable inventory-control data.")


def main() -> None:
    st.set_page_config(page_title="FruitBlend24 | Decision Dashboard", page_icon="🥤", layout="wide", initial_sidebar_state="collapsed")
    apply_theme()
    data = load_data()
    st.title("FruitBlend24 · Decision Dashboard")
    st.caption("Turn sales, pricing, promotion, cost, and waste data into decision support · Synthetic data case study · Data version " + DATA_VERSION)
    st.sidebar.header("How to use this dashboard")
    st.sidebar.write("Start with the overview to understand the problem, then open the tab that answers your question. Every number links back to a QA-passed artifact.")
    st.sidebar.markdown("**Recommended path**\n\n1. Overview & recovery plan\n2. Portfolio, kitchens & budget performance\n3. Promotions & rate codes\n4. Demand & price fit\n5. 3-month outlook & preparation plan\n6. Data quality & limitations")
    tabs = st.tabs(["Overview & recovery plan", "Portfolio, kitchens & budget performance", "Promotions & rate codes", "Demand & price fit", "3-month outlook & preparation plan", "Data quality & limitations"])
    with tabs[0]:
        overview(data)
    with tabs[1]:
        finance(data)
    with tabs[2]:
        promotions(data)
    with tabs[3]:
        demand_pricing(data)
    with tabs[4]:
        forecast_inventory(data)
    with tabs[5]:
        data_quality(data)
    st.divider()
    st.caption("Scope: synthetic FruitBlend24 case study. Detailed assumptions and QA are stored under reports/fruitblend24_run_001 and data/processed/fruitblend24_v1_c2869ce419bf.")


if __name__ == "__main__":
    main()
