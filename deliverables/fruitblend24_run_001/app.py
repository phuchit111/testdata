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
        return "ไม่มีข้อมูล"
    return f"฿{value:,.{decimals}f}"


def pct(value: float, decimals: int = 1) -> str:
    if pd.isna(value):
        return "ไม่มีข้อมูล"
    return f"{value * 100:.{decimals}f}%"


MONTH_NAMES = {
    1: "ม.ค.", 2: "ก.พ.", 3: "มี.ค.", 4: "เม.ย.", 5: "พ.ค.", 6: "มิ.ย.",
    7: "ก.ค.", 8: "ส.ค.", 9: "ก.ย.", 10: "ต.ค.", 11: "พ.ย.", 12: "ธ.ค.",
}
WEEKDAY_NAMES = {0: "จันทร์", 1: "อังคาร", 2: "พุธ", 3: "พฤหัสบดี", 4: "ศุกร์", 5: "เสาร์", 6: "อาทิตย์"}


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
        div[data-testid="stMetric"] {background: #ffffff; border: 1px solid #e2e8f0; border-radius: .75rem; padding: .65rem; color: #0f172a !important;}
        div[data-testid="stMetric"] [data-testid="stMetricLabel"],
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] *,
        div[data-testid="stMetric"] [data-testid="stMetricValue"],
        div[data-testid="stMetric"] [data-testid="stMetricValue"] > div,
        div[data-testid="stMetric"] [data-testid="stMetricValue"] *,
        div[data-testid="stMetric"] [data-testid="stMetricDelta"] {color: #0f172a !important;}
        div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] > div {font-size: clamp(1.2rem, 2.2vw, 1.9rem) !important; line-height: 1.15; white-space: normal !important; overflow: visible !important; text-overflow: clip !important; overflow-wrap: anywhere;}
        div[data-testid="stMetricLabel"] {white-space: normal !important; overflow: visible !important; text-overflow: clip !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def task_heading(task: str, title: str, question: str, scope: str) -> None:
    st.caption(task)
    st.subheader(title)
    st.write(question)
    st.caption(scope)


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
    """Show selected business fields with readable Thai labels and units."""
    view = frame.loc[:, [column for column in columns if column in frame.columns]].copy()
    for column in money_columns:
        if column in view:
            view[column] = view[column].map(lambda value: money(value, 2) if pd.notna(value) else "ไม่มีข้อมูล")
    for column in percent_columns:
        if column in view:
            view[column] = view[column].map(lambda value: pct(value, 1) if pd.notna(value) else "ไม่มีข้อมูล")
    for column in integer_columns:
        if column in view:
            view[column] = view[column].map(lambda value: f"{value:,.0f}" if pd.notna(value) else "ไม่มีข้อมูล")
    for column in date_columns:
        if column in view:
            view[column] = pd.to_datetime(view[column]).map(month_name)
    for column in decimal_columns:
        if column in view:
            view[column] = view[column].map(lambda value: f"{value:,.1f}" if pd.notna(value) else "ไม่มีข้อมูล")
    kwargs = {"width": "stretch", "hide_index": True}
    if height is not None:
        kwargs["height"] = height
    st.dataframe(view.rename(columns=labels), **kwargs)


def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
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
        "sales_clean": load_csv(str(DATA_DIR / "sales_clean.csv")),
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
    }
    for key in ["daily", "sales_clean", "forecast", "requirements"]:
        data[key]["date"] = pd.to_datetime(data[key]["date"])
    data["requirements"]["month"] = pd.to_datetime(data["requirements"]["month"])
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
    c1.metric("รายได้จากการขาย", money(revenue), "Actual หลังคัดกรองข้อมูล")
    c2.metric("รายได้เทียบงบ", money(revenue_variance), pct(revenue_variance / float(pnl["budget_revenue_thb"].sum())))
    c3.metric("ผลดำเนินงานตามแบบจำลอง", money(operating), "หลัง Waste และ fixed overhead")
    return revenue, revenue_variance, operating


def overview(data: dict) -> None:
    task_heading(
        "Task 6 · Present findings",
        "E-Commerce Action Center",
        "เริ่มจาก 3 การตัดสินใจของรอบนี้ แล้วเปิดหลักฐานเรื่องแคมเปญ ราคา SKU และการส่งแผนให้ครัวตามลำดับ",
        "Actual: ก.ย. 2025–ส.ค. 2026 · Scenario/Forecast: ก.ย.–พ.ย. 2026 · ไม่ใช่ข้อมูลสด",
    )
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">FRUITBLEND24 · E-COMMERCE TRADING REVIEW · SYNTHETIC DATA</div>
          <h2>ยอดขายมี แต่ต้องเลือกยอดขายที่เหลือเงินหลังต้นทุนมากขึ้น</h2>
          <p>รายได้ใกล้เป้า แต่ส่วนลด สินค้าที่เงินเหลือติดลบ ของเสียที่บันทึก และค่าใช้จ่ายคงที่ ทำให้ผลดำเนินงานตามแบบจำลองยังติดลบ</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    revenue, revenue_variance, operating = metric_cards(data)

    st.markdown("#### ภาพรวมช่องทาง (ก่อน Waste)")
    platform = data["platform"].copy().sort_values("gross_revenue_thb", ascending=False)
    display_table(
        platform,
        ["platform_name", "units_sold", "gross_revenue_thb", "revenue_share", "commission_thb", "contribution_before_waste_per_cup_thb"],
        {"platform_name": "Platform", "units_sold": "จำนวนแก้วที่ขาย", "gross_revenue_thb": "รายได้จากการขาย", "revenue_share": "สัดส่วนรายได้", "commission_thb": "ค่าคอมมิชชัน", "contribution_before_waste_per_cup_thb": "เงินเหลือก่อน Waste/แก้ว"},
        integer_columns=("units_sold",), money_columns=("gross_revenue_thb", "commission_thb", "contribution_before_waste_per_cup_thb"), percent_columns=("revenue_share",),
    )
    st.caption("เปรียบเทียบนี้สะท้อน SKU, rate code และต้นทุนที่สังเกตได้ในแต่ละ Platform ไม่ใช่หลักฐานเชิงเหตุและผลว่า Platform หนึ่งดีกว่าอีก Platform")

    pnl = data["pnl_company"].copy().set_index("month")
    left, right = st.columns((1.1, 0.9))
    with left:
        st.markdown("#### รายได้จริงเทียบงบรายเดือน")
        st.line_chart(
            pnl[["gross_revenue_thb", "budget_revenue_thb"]].rename(columns={"gross_revenue_thb": "รายได้จริง", "budget_revenue_thb": "งบรายได้"}),
            height=280,
        )
    with right:
        st.markdown("#### จากรายได้สู่ผลดำเนินงานตามแบบจำลอง")
        waterfall = data["pnl_waterfall"].copy().set_index("pnl_component")
        waterfall.index = [
            "รายได้", "ต้นทุนผลไม้", "บรรจุภัณฑ์", "แรงงาน", "ค่าคอมมิชชัน Platform",
            "เงินเหลือก่อน Waste", "ต้นทุน Waste", "เงินเหลือหลัง Waste", "ค่าใช้จ่ายคงที่", "ผลดำเนินงาน",
        ]
        st.bar_chart(waterfall[["thb"]].rename(columns={"thb": "บาท"}), height=280)

    st.markdown("#### 5 ข้อค้นพบเพื่อเลือก Action")
    reconciliation = data["reconciliation"]
    peak_hour = data["hourly"].sort_values("units_sold", ascending=False).iloc[0]
    weekend_revenue_share = float(data["weekday"].loc[data["weekday"]["day_of_week"].isin([5, 6]), "revenue_share"].sum())
    mixed = data["sku"].loc[data["sku"]["sku"] == "MixedBerryPremium"].iloc[0]
    promo = data["promo"].set_index("base_code")
    base_wape = float(data["metrics"]["selected_method_pooled_wape"])
    base_outlook = data["scenario"].loc[data["scenario"]["scenario"] == "base"]
    insights = pd.DataFrame([
        ["ข้อมูลพร้อมใช้", f"ตัด duplicate 372 แถว และ non-menu 370 แถว; ป้องกันรายได้สูงเกิน {money(reconciliation['duplicate_revenue_removed_thb'])}", "ใช้เฉพาะ released menu data ที่ผ่าน QA"],
        ["Demand ขึ้นกับเวลา", f"ยอดรวมสูงสุดที่ 22:00 คือ {peak_hour['units_sold']:,.0f} แก้ว; เสาร์–อาทิตย์คิดเป็น {pct(weekend_revenue_share)} ของรายได้", "ส่งสัญญาณให้ครัวเพิ่ม batch ก่อนช่วงเย็น/สุดสัปดาห์ และลดการเตรียมล่วงหน้าช่วงต่ำ"],
        ["โปรโมชันลดเงินเหลือ", f"RC102 เหลือ {money(promo.loc['RC102', 'contribution_before_waste_per_cup_thb'], 2)}/แก้ว เทียบ RC000 ที่ {money(promo.loc['RC000', 'contribution_before_waste_per_cup_thb'], 2)}/แก้ว ก่อน Waste", "ใช้ RC000 เป็น control และจำกัดกลุ่มก่อนทดสอบต่อ"],
        ["MixedBerryPremium ต้องแก้ก่อนขยาย", f"เงินเหลือหลัง Waste {money(mixed['contribution_after_waste_thb'])} หรือ {money(mixed['contribution_after_waste_per_cup_thb'], 2)}/แก้ว; Waste {pct(mixed['waste_rate'])}", "ทดสอบราคา/portion และ batch เล็ก โดยวัดผลระดับ Kitchen × SKU"],
        ["แผน 3 เดือนยังมีช่องว่าง", f"Forecast ฐาน {base_outlook['forecast_units'].sum():,.0f} แก้ว และผลตามแบบจำลอง {money(base_outlook['modeled_operating_result_thb'].sum())}; WAPE {pct(base_wape)}", "เชื่อม price/promo action กับ prep target และทบทวนทุกสัปดาห์"],
    ], columns=["ข้อค้นพบ", "หลักฐานเชิงตัวเลข", "Action ที่เสนอ"])
    st.dataframe(insights, width="stretch", hide_index=True)

    st.markdown("#### 3 เรื่องที่ควรเริ่มในรอบนี้")
    card1, card2, card3 = st.columns(3)
    card1.warning("**Campaign:** RC101–RC103\n\nให้ใช้แบบจำกัดกลุ่ม/ทดสอบต่อ ไม่ใช้เป็นส่วนลดกว้าง ๆ จนกว่าจะผ่าน contribution gate")
    card2.warning("**SKU / ราคา:** MixedBerryPremium\n\nเงินเหลือหลัง Waste ติดลบและ Waste 20.5%; ทดสอบราคา/portion ก่อนเพิ่ม volume")
    card3.warning("**Kitchen handoff:** BKK_Ladprao และ BKK_Sukhumvit\n\nผลดำเนินงานตามแบบจำลองติดลบ; ตรวจ Kitchen × SKU ที่มี Waste สูงก่อน")

    st.markdown("#### Action ที่เสนอสำหรับรอบถัดไป")
    actions = pd.DataFrame([
        ["Campaign", "ใช้ RC000 เป็น control; จำกัด RC101/RC103 และทดสอบ RC102 เฉพาะกลุ่มที่กำหนด", "Campaign / Channel owner (เสนอ)", "รอบแคมเปญถัดไป", "เงินเหลือก่อน Waste/แก้ว และ lift เทียบ control", "ทุกผลเป็น historical association ไม่ใช่ causal uplift"],
        ["SKU / ราคา", "ทำ pilot MixedBerryPremium 4 สัปดาห์: ทดสอบราคา/portion และ batch เล็ก; ไม่เพิ่ม volume จนเงินเหลือหลัง Waste เป็นบวก", "Category / Commercial + Kitchen (เสนอ)", "เริ่มภายใน 1 สัปดาห์", "เงินเหลือหลัง Waste/แก้ว และ Waste rate ระดับ Kitchen × SKU", "ราคาเป็น directional test; ไม่ใช่คำสั่งปรับราคาถาวร"],
        ["Kitchen handoff", f"ใช้ {data['metrics']['selected_method']} สร้าง prep target ราย Kitchen × SKU รวม Waste ที่คาดไว้ และทบทวนทุก 7 วัน", "E-Commerce + Operations (เสนอ)", "weekly review", "WAPE, forecast bias และ Waste rate ระดับ Kitchen × SKU", "prep target เป็นแก้ว ไม่ใช่ PO; ไม่มี on-hand/lead time/BOM"],
    ], columns=["หัวข้องาน", "Action", "Owner ที่เสนอ", "รอบเวลา", "KPI gate", "ข้อจำกัด"])
    st.dataframe(actions, width="stretch", hide_index=True)

    st.markdown("#### ภาพรวมแผน ก.ย.–พ.ย. 2026")
    scenario_totals = data["scenario"].groupby("scenario", as_index=False).agg(
        forecast_units=("forecast_units", "sum"), modeled_operating_result_thb=("modeled_operating_result_thb", "sum")
    )
    scenario_order = ["base", "price_and_waste_action", "downside"]
    scenario_totals["sort_order"] = scenario_totals["scenario"].map({name: index for index, name in enumerate(scenario_order)})
    scenario_totals = scenario_totals.sort_values("sort_order")
    scenario_columns = st.columns(3)
    for column, (_, row) in zip(scenario_columns, scenario_totals.iterrows()):
        scenario_name = {"base": "กรณีฐาน", "price_and_waste_action": "ราคา RC000 + Waste", "downside": "กรณีแย่ลง"}[row["scenario"]]
        column.metric(scenario_name, money(row["modeled_operating_result_thb"]), f"Forecast {row['forecast_units']:,.0f} แก้ว")
    optimized_result = float(scenario_totals.loc[scenario_totals["scenario"] == "price_and_waste_action", "modeled_operating_result_thb"].iloc[0])
    base_result = float(scenario_totals.loc[scenario_totals["scenario"] == "base", "modeled_operating_result_thb"].iloc[0])
    st.markdown(
        f"<div class='callout'><strong>กรณีราคา RC000 + Waste ยังไม่ถึงจุดคุ้มทุน:</strong> จากกรณีฐาน {money(base_result)} การใช้ราคาเฉลี่ยที่รับจริงของ RC000 และลด Waste 25% ลดการขาดทุนได้ {money(optimized_result - base_result)} แต่ยังมีช่องว่าง {money(-optimized_result)} ก่อนคุ้มทุน 3 เดือน ต้องวัดผลจริงก่อนประเมินต้นทุนคงที่ ต้นทุนจัดซื้อ และยอดขายที่เงินเหลือเป็นบวกอีกครั้ง</div>",
        unsafe_allow_html=True,
    )

    with st.expander("หลักคิดและข้อจำกัด"):
        st.markdown("รายได้คือราคาที่ลูกค้าจ่ายหลังโปรโมชัน จึงไม่หักส่วนลดซ้ำ ผลดำเนินงานตามแบบจำลองหักต้นทุนผลไม้ บรรจุภัณฑ์ แรงงาน ค่าคอมมิชชัน ของเสียที่บันทึก และค่าใช้จ่ายคงที่ของครัวแล้ว จึงไม่ใช่ GP variance เทียบงบ เพราะขอบเขต GP ในงบไม่ระบุชัด")
        st.markdown("ผลโปรโมชันเป็นความสัมพันธ์ในข้อมูลย้อนหลัง ไม่ยืนยันว่าโปรโมชันทำให้ยอดขายเปลี่ยน Forecast range มาจาก WAPE เพื่อการวางแผน ไม่ใช่ confidence interval")

    with st.expander("ที่มาของตัวเลขและสถานะ QA"):
        qa = data["qa"]
        st.success(f"ตรวจ artifacts แล้ว: {qa['status']} · ผ่าน {len(qa['checks']) - qa['failed_count']}/{len(qa['checks'])} checks")
        st.write(f"Data version: `{DATA_VERSION}`")
        st.write("เปิดแท็บ “Data Trust & Definitions” เพื่อดูการคัดกรอง issue log และ QA ราย check")


def demand_pricing(data: dict) -> None:
    task_heading(
        "Task 2 · Demand & pricing",
        "Sales, Price & Menu",
        "ดูจำนวนแก้วที่ขายตามเวลา/ช่องทาง และเลือก SKU ที่ควรรักษาราคา จำกัด หรือทดสอบราคาอย่างมี control",
        "Actual: ก.ย. 2025–ส.ค. 2026 · จำนวนแก้วที่ขาย ไม่ใช่ visits, orders หรือ conversion",
    )
    sales_scope = data["sales_clean"].copy()
    platform_options = ["ทุก Platform"] + sorted(sales_scope["platform_name"].dropna().unique().tolist())
    selected_platform = st.selectbox("เลือก Platform สำหรับดู Demand", platform_options, key="sales_platform")
    if selected_platform != "ทุก Platform":
        sales_scope = sales_scope.loc[sales_scope["platform_name"] == selected_platform].copy()
        platform_scope = selected_platform
    else:
        platform_scope = "ทุก Platform"

    hourly = sales_scope.groupby("hour", as_index=False).agg(units_sold=("units_sold", "sum"), gross_revenue_thb=("gross_revenue_thb", "sum"))
    weekday = sales_scope.groupby("day_of_week", as_index=False).agg(units_sold=("units_sold", "sum"), gross_revenue_thb=("gross_revenue_thb", "sum"))
    weekday["weekday"] = weekday["day_of_week"].map(WEEKDAY_NAMES)
    monthly = sales_scope.assign(month=sales_scope["date"].dt.to_period("M").dt.to_timestamp()).groupby("month", as_index=False).agg(
        units_sold=("units_sold", "sum"), gross_revenue_thb=("gross_revenue_thb", "sum")
    )
    peak_hour = hourly.sort_values("units_sold", ascending=False).iloc[0]
    peak_day = weekday.sort_values("units_sold", ascending=False).iloc[0]
    scope_revenue = float(sales_scope["gross_revenue_thb"].sum())
    top_platform = data["platform"].sort_values("gross_revenue_thb", ascending=False).iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("ช่วงเวลาที่ขายสูงสุด", f"{int(peak_hour['hour']):02d}:00", f"{peak_hour['units_sold']:,.0f} แก้วในช่วงข้อมูล")
    c2.metric("วันที่ขายสูงสุด", str(peak_day["weekday"]), f"{peak_day['units_sold']:,.0f} แก้วในช่วงข้อมูล")
    c3.metric("รายได้ในขอบเขตที่เลือก", money(scope_revenue), platform_scope if selected_platform != "ทุก Platform" else f"Platform ที่มีรายได้สูงสุด: {top_platform['platform_name']}")
    st.caption(f"Scope: {platform_scope} · ยอดรายชั่วโมง/รายวันครอบคลุมข้อมูลย้อนหลัง 12 เดือน ไม่ใช่ยอดขายหนึ่งวัน")

    st.markdown("#### ช่วงเวลาใดขายได้มากในขอบเขตที่เลือก?")
    left, right = st.columns(2)
    left.markdown("**จำนวนแก้วขายแยกตามชั่วโมงของวัน**")
    left.bar_chart(
        hourly.set_index("hour")[["units_sold"]].rename(columns={"units_sold": "แก้วรวมทุกวันที่มีข้อมูล"}),
        height=270, x_label="ชั่วโมงของวัน", y_label="แก้วรวม",
    )
    left.caption("เป็นการรวมยอดของชั่วโมงเดียวกันตลอดช่วงข้อมูล ไม่ใช่เส้นเวลาแบบวันต่อวัน")
    right.markdown("**จำนวนแก้วที่ขายตามวัน**")
    right.bar_chart(weekday.set_index("weekday")[["units_sold"]].rename(columns={"units_sold": "แก้ว"}), height=270)
    left, right = st.columns(2)
    left.markdown("**จำนวนแก้วที่ขายรายเดือน**")
    monthly_cups = monthly.set_index("month")[["units_sold"]].rename(columns={"units_sold": "แก้ว"})
    left.line_chart(monthly_cups, height=260)
    right.markdown("**รายได้จากการขายรายเดือน**")
    right.line_chart(monthly.set_index("month")[["gross_revenue_thb"]].rename(columns={"gross_revenue_thb": "บาท"}), height=260)
    st.info("ส่งสัญญาณให้ครัวเตรียม batch ก่อนช่วงเย็นและสุดสัปดาห์ โดยไม่ตีความชั่วโมงที่ไม่มี record ใน export ว่าเป็นยอดขายศูนย์")

    with st.expander("รายละเอียด Demand ตาม Platform / เวลา"):
        normalized_hour = sales_scope.groupby(["date", "hour"], as_index=False)["units_sold"].sum().groupby("hour", as_index=False)["units_sold"].mean().set_index("hour")
        normalized_day = sales_scope.groupby(["date", "day_of_week"], as_index=False)["units_sold"].sum().groupby("day_of_week", as_index=False)["units_sold"].mean()
        normalized_day["weekday"] = normalized_day["day_of_week"].map(WEEKDAY_NAMES)
        normalized_day = normalized_day.set_index("weekday")
        left, right = st.columns(2)
        left.markdown("**จำนวนแก้วเฉลี่ยต่อวันที่มี record แยกตามชั่วโมง**")
        left.bar_chart(normalized_hour.rename(columns={"units_sold": "แก้วเฉลี่ย"}), height=260)
        right.markdown("**จำนวนแก้วเฉลี่ยต่อวันที่มี record แยกตามวัน**")
        right.bar_chart(normalized_day[["units_sold"]].rename(columns={"units_sold": "แก้วเฉลี่ย"}), height=260)
        st.markdown("**Heatmap: วัน × ชั่วโมง และครัว × SKU ในขอบเขตที่เลือก**")
        day_names = list(WEEKDAY_NAMES.values())
        heat = sales_scope.groupby(["date", "day_of_week", "hour"], as_index=False)["units_sold"].sum().groupby(["day_of_week", "hour"], as_index=False)["units_sold"].mean()
        heat["weekday"] = heat["day_of_week"].map(WEEKDAY_NAMES)
        heat_table = heat.pivot(index="weekday", columns="hour", values="units_sold").reindex(day_names).round(1)
        st.dataframe(heat_table.style.background_gradient(cmap="YlOrRd").format("{:.1f} แก้ว"), width="stretch")
        kitchen_heat = sales_scope.groupby(["date", "kitchen", "sku"], as_index=False)["units_sold"].sum().groupby(["kitchen", "sku"], as_index=False)["units_sold"].mean().pivot(index="kitchen", columns="sku", values="units_sold").round(1)
        st.dataframe(kitchen_heat.style.background_gradient(cmap="YlGnBu").format("{:.1f} แก้ว"), width="stretch")
        st.caption("ค่าเฉลี่ยคำนวณเฉพาะวันที่/ชั่วโมงที่มี record; รายการที่ไม่มีใน export ไม่ถูกเติมเป็นศูนย์")

    st.markdown("#### ราคาแต่ละ SKU เหมาะกับเงินเหลือหรือไม่?")
    st.write("ตารางนี้ใช้หลักฐานทั้งพอร์ตเพื่อเทียบราคาที่ลูกค้าจ่ายจริงกับ **ราคาคุ้มทุนก่อน Waste และ fixed overhead** จึงใช้คัดกรอง price fit ไม่ใช่ราคาคุ้มทุนของธุรกิจทั้งหมด และไม่เปลี่ยนตาม Platform filter ด้านบน")
    price_summary = data["price_floor"].merge(
        data["portfolio"][["sku", "contribution_after_waste_per_cup_thb", "waste_rate", "action_note"]], on="sku", how="left"
    )
    price_summary["headroom_before_waste_thb"] = price_summary["realized_price_thb"] - price_summary["break_even_price_before_waste_thb"]
    price_actions = {
        "Watermelon": "รักษาราคา; ทดสอบ +5% ในช่วง Demand สูงโดยมีกลุ่มอ้างอิง",
        "Pineapple": "รักษาราคา; ทดสอบ +5% ในช่วง Demand สูงโดยมีกลุ่มอ้างอิง",
        "Guava": "รักษาราคา; ทดสอบ +5% โดยมีกลุ่มอ้างอิง",
        "PassionFruit": "รักษาราคา; ทบทวน mix และ Waste ก่อนทดสอบราคา",
        "MixedBerryPremium": "ทดสอบ +5% ควบคู่ portion control และ batch เล็ก",
    }
    price_summary["recommendation"] = price_summary["sku"].map(price_actions)
    display_table(
        price_summary.sort_values("contribution_after_waste_per_cup_thb", ascending=False),
        ["sku", "realized_price_thb", "break_even_price_before_waste_thb", "headroom_before_waste_thb", "contribution_before_waste_per_cup_thb", "contribution_after_waste_per_cup_thb", "waste_rate", "recommendation"],
        {"sku": "SKU", "realized_price_thb": "ราคาที่ลูกค้าจ่ายจริง/แก้ว", "break_even_price_before_waste_thb": "ราคาคุ้มทุนก่อน Waste/แก้ว", "headroom_before_waste_thb": "ส่วนต่างเหนือราคาคุ้มทุน", "contribution_before_waste_per_cup_thb": "เงินเหลือก่อน Waste/แก้ว", "contribution_after_waste_per_cup_thb": "เงินเหลือหลัง Waste/แก้ว", "waste_rate": "Waste rate", "recommendation": "ข้อเสนอการทดสอบ"},
        money_columns=("realized_price_thb", "break_even_price_before_waste_thb", "headroom_before_waste_thb", "contribution_before_waste_per_cup_thb", "contribution_after_waste_per_cup_thb"),
        percent_columns=("waste_rate",),
    )
    st.caption("ข้อเสนอราคาเป็น controlled test ไม่ใช่คำสั่งปรับราคาทันที เพราะราคาย้อนหลังเปลี่ยนร่วมกับ rate code และปัจจัยอื่น")

    st.markdown("#### รายละเอียดราคาและเมนูราย SKU")
    sku_options = data["sku"]["sku"].tolist()
    selected_sku = st.selectbox("เลือก SKU", sku_options, index=sku_options.index("MixedBerryPremium") if "MixedBerryPremium" in sku_options else 0, key="sales_sku")
    sku_row = data["sku"].loc[data["sku"]["sku"] == selected_sku].iloc[0]
    price_row = data["price_floor"].loc[data["price_floor"]["sku"] == selected_sku].iloc[0]
    price_headroom = sku_row["realized_price_thb"] - price_row["break_even_price_before_waste_thb"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("จำนวนแก้วที่ขายย้อนหลัง", f"{sku_row['units_sold']:,.0f} แก้ว")
    c2.metric("ราคาที่ลูกค้าจ่ายจริง", money(sku_row["realized_price_thb"], 2))
    c3.metric("ส่วนต่างเหนือราคาคุ้มทุนก่อน Waste", money(price_headroom, 2))
    c4.metric("เงินเหลือหลัง Waste/แก้ว", money(sku_row["contribution_after_waste_per_cup_thb"], 2))
    if selected_sku == "MixedBerryPremium":
        st.info("MixedBerryPremium เริ่มขายหลัง SKU อื่น ช่วงก่อนเปิดขายไม่ใช่ยอดขาย 0 และไม่ควรถูกนำไปเทียบเป็น Demand ที่หายไป")

    left, right = st.columns(2)
    ladder = data["price_ladder"].loc[data["price_ladder"]["sku"] == selected_sku].sort_values("observed_price_thb")
    with left:
        st.markdown("**ราคาเทียบจำนวนแก้วต่อชั่วโมงที่มีรายการขาย**")
        st.line_chart(ladder.set_index("observed_price_thb")[["avg_cups_per_active_hour"]].rename(columns={"avg_cups_per_active_hour": "แก้วต่อชั่วโมง"}), height=250)
    with right:
        st.markdown("**Scenario เงินเหลือหลัง Waste**")
        simulation = data["price_simulation"].loc[data["price_simulation"]["sku"] == selected_sku].sort_values("price_change_pct").copy()
        simulation["price_change_label"] = simulation["price_change_pct"].map(lambda value: pct(value, 0))
        st.line_chart(simulation.set_index("price_change_label")[["projected_contribution_after_waste_thb"]].rename(columns={"projected_contribution_after_waste_thb": "บาท"}), height=250)
    with st.expander("หลักฐานราคาและข้อจำกัดเชิงสถิติ"):
        display_table(
            ladder,
            ["observed_price_thb", "units_sold", "active_hours", "avg_cups_per_active_hour", "contribution_per_cup_thb", "promo_families"],
            {"observed_price_thb": "ราคาที่สังเกต", "units_sold": "จำนวนแก้วที่ขาย", "active_hours": "ชั่วโมงที่มีรายการขาย", "avg_cups_per_active_hour": "แก้ว/ชั่วโมง", "contribution_per_cup_thb": "เงินเหลือ/แก้ว", "promo_families": "กลุ่ม rate code"},
            money_columns=("observed_price_thb", "contribution_per_cup_thb"), integer_columns=("units_sold", "active_hours"), decimal_columns=("avg_cups_per_active_hour",),
        )
        sensitivity = data["price_sensitivity"].copy()
        display_table(
            sensitivity,
            ["sku", "price_points", "min_observed_price_thb", "max_observed_price_thb", "price_cv", "pairwise_midpoint_elasticity_median", "pairwise_comparisons", "interpretation"],
            {"sku": "SKU", "price_points": "จำนวนราคาที่สังเกต", "min_observed_price_thb": "ราคาต่ำสุด", "max_observed_price_thb": "ราคาสูงสุด", "price_cv": "ความผันผวนของราคา", "pairwise_midpoint_elasticity_median": "Price sensitivity (directional)", "pairwise_comparisons": "จำนวนคู่เปรียบเทียบ", "interpretation": "ข้อจำกัด"},
            money_columns=("min_observed_price_thb", "max_observed_price_thb"), percent_columns=("price_cv",), integer_columns=("price_points", "pairwise_comparisons"), decimal_columns=("pairwise_midpoint_elasticity_median",),
        )
        display_table(
            simulation,
            ["price_change_pct", "projected_price_thb", "demand_factor", "projected_units", "projected_contribution_after_waste_thb", "delta_contribution_vs_current_thb", "assumption_source"],
            {"price_change_pct": "การเปลี่ยนราคา", "projected_price_thb": "ราคาใน Scenario", "demand_factor": "Demand factor", "projected_units": "แก้วใน Scenario", "projected_contribution_after_waste_thb": "เงินเหลือหลัง Waste", "delta_contribution_vs_current_thb": "การเปลี่ยนจากปัจจุบัน", "assumption_source": "ที่มาสมมติฐาน"},
            money_columns=("projected_price_thb", "projected_contribution_after_waste_thb", "delta_contribution_vs_current_thb"), percent_columns=("price_change_pct",), integer_columns=("projected_units",), decimal_columns=("demand_factor",),
        )
        best = data["price_simulation_best"].loc[data["price_simulation_best"]["sku"] == selected_sku]
        if not best.empty:
            best_row = best.iloc[0]
            st.info(f"Scenario ให้เงินเหลือสูงสุดที่การเปลี่ยนราคา {pct(best_row['price_change_pct'])} สำหรับ {selected_sku} แต่ใช้สมมติฐาน elasticity {best_row['elasticity_used']:.2f} จึงใช้เพื่อออกแบบ test +5% ในช่วง Demand สูงเท่านั้น ไม่ใช่หลักฐานสำหรับปรับราคาถาวร")


def promotions(data: dict) -> None:
    task_heading(
        "Task 3 · Promotions & rate codes",
        "Platform & Campaign Control",
        "ใช้ contribution gate ตัดสินใจว่าควรหยุด จำกัดกลุ่ม หรือทดสอบ rate code ต่อในรอบแคมเปญถัดไป",
        "Actual: ก.ย. 2025–ส.ค. 2026 · วิเคราะห์ platform/rate code ถึง contribution ก่อน Waste เท่านั้น",
    )
    metrics = data["promotion_depth_metrics"]
    scorecard = data["promo_scorecard"].copy().sort_values("base_code")
    matched = data["promo_matched_scorecard"].copy().sort_values("base_code")
    decision_map = {"CONTROL / DEFAULT": "ใช้เป็นกลุ่มอ้างอิง", "OPTIMIZE / TARGET ONLY": "จำกัดกลุ่มและทดสอบต่อ"}
    scorecard["decision_display"] = scorecard["decision"].map(decision_map).fillna(scorecard["decision"])
    matched["decision_display"] = matched["decision"].map(decision_map).fillna(matched["decision"])

    st.caption("รายได้คือราคาที่ลูกค้าจ่ายหลังโปรโมชัน มูลค่าส่วนลดใช้วิเคราะห์ผลกระทบและไม่ได้ถูกหักจากรายได้ซ้ำ ของเสียไม่มี tag platform/rate code จึงไม่แสดงเงินเหลือหลัง Waste ในระดับนี้")
    st.markdown("#### Platform mix และเงินเหลือก่อน Waste")
    platform = data["platform"].copy().sort_values("gross_revenue_thb", ascending=False)
    display_table(
        platform,
        ["platform_name", "units_sold", "gross_revenue_thb", "revenue_share", "commission_thb", "contribution_before_waste_per_cup_thb"],
        {"platform_name": "Platform", "units_sold": "จำนวนแก้วที่ขาย", "gross_revenue_thb": "รายได้", "revenue_share": "สัดส่วนรายได้", "commission_thb": "ค่าคอมมิชชัน", "contribution_before_waste_per_cup_thb": "เงินเหลือก่อน Waste/แก้ว"},
        integer_columns=("units_sold",), money_columns=("gross_revenue_thb", "commission_thb", "contribution_before_waste_per_cup_thb"), percent_columns=("revenue_share",),
    )
    st.caption("ความต่างระหว่าง Platform อาจเกิดจาก SKU/rate-code mix และต้นทุนที่สังเกตได้ ไม่ใช่ผลเชิงเหตุและผล")

    st.markdown("#### คำตัดสินสำหรับ rate code ที่ใช้งาน")
    promo_actions = pd.DataFrame([
        ["RC000 · Standard", "ใช้เป็นกลุ่มอ้างอิง", "ฐานเปรียบเทียบ: เงินเหลือก่อน Waste 14.48 บาท/แก้ว"],
        ["RC101 · Bundle Deal", "จำกัดกลุ่ม", "Observed lift ต่ำกว่าระดับที่ต้องการเพื่อชดเชยส่วนลด"],
        ["RC102 · Double Day New User", "ออกแบบใหม่และทดสอบต่อ", "เงินเหลือก่อน Waste 6.90 บาท/แก้ว และ observed lift ยังไม่ถึง break-even"],
        ["RC103 · Seasonal Push", "จำกัดกลุ่ม", "Observed lift ต่ำกว่าระดับที่ต้องการเพื่อชดเชยส่วนลด"],
    ], columns=["Rate code", "คำตัดสิน", "เหตุผล"])
    st.dataframe(promo_actions, width="stretch", hide_index=True)

    st.markdown("#### เงินเหลือที่คงเหลือหลังส่วนลด (ก่อน Waste)")
    display_table(
        scorecard,
        ["base_code", "rate_code_name", "discount_pct", "units_sold", "cups_per_active_hour", "discount_cost_thb", "net_revenue_thb", "contribution_before_waste_per_cup_thb", "contribution_margin_pct", "decision_display"],
        {"base_code": "Code", "rate_code_name": "ชื่อ rate code", "discount_pct": "ส่วนลด", "units_sold": "จำนวนแก้วที่ขาย", "cups_per_active_hour": "แก้ว/ชั่วโมงที่มีรายการขาย", "discount_cost_thb": "มูลค่าส่วนลด", "net_revenue_thb": "รายได้", "contribution_before_waste_per_cup_thb": "เงินเหลือก่อน Waste/แก้ว", "contribution_margin_pct": "Contribution margin", "decision_display": "คำตัดสิน"},
        money_columns=("discount_cost_thb", "net_revenue_thb", "contribution_before_waste_per_cup_thb"), percent_columns=("discount_pct", "contribution_margin_pct"), integer_columns=("units_sold",), decimal_columns=("cups_per_active_hour",),
    )
    left, right = st.columns(2)
    left.markdown("**เงินเหลือก่อน Waste ต่อแก้ว**")
    left.bar_chart(scorecard.set_index("base_code")[["contribution_before_waste_per_cup_thb"]].rename(columns={"contribution_before_waste_per_cup_thb": "บาท/แก้ว"}), height=260)
    right.markdown("**มูลค่าส่วนลดรวม**")
    right.bar_chart(scorecard.set_index("base_code")[["discount_cost_thb"]].rename(columns={"discount_cost_thb": "บาท"}), height=260)

    st.markdown("#### ยอดขายเพิ่มพอคุ้มส่วนลดหรือไม่?")
    if not matched.empty:
        lift = matched.copy()
        display_table(
            lift,
            ["base_code", "rate_code_name", "discount_pct", "promo_cups_per_active_hour", "baseline_cups_per_active_hour", "actual_demand_lift_pct", "break_even_lift_pct", "actual_vs_breakeven_gap_pct", "incremental_contribution_thb", "decision_display"],
            {"base_code": "Code", "rate_code_name": "ชื่อ rate code", "discount_pct": "ส่วนลด", "promo_cups_per_active_hour": "แก้วโปรฯ/ชั่วโมง", "baseline_cups_per_active_hour": "แก้วกลุ่มอ้างอิง/ชั่วโมง", "actual_demand_lift_pct": "Observed lift", "break_even_lift_pct": "Break-even lift", "actual_vs_breakeven_gap_pct": "ส่วนต่างจาก break-even", "incremental_contribution_thb": "เงินเหลือเพิ่มเทียบกลุ่มอ้างอิง", "decision_display": "คำตัดสิน"},
            money_columns=("incremental_contribution_thb",), percent_columns=("discount_pct", "actual_demand_lift_pct", "break_even_lift_pct", "actual_vs_breakeven_gap_pct"), decimal_columns=("promo_cups_per_active_hour", "baseline_cups_per_active_hour"),
        )
        lift_chart = lift.set_index("base_code")[["actual_demand_lift_pct", "break_even_lift_pct"]].mul(100)
        lift_chart.columns = ["Observed lift (%)", "Break-even lift ที่ต้องมี (%)"]
        st.bar_chart(lift_chart, height=280)
        st.caption(f"จับคู่ SKU × kitchen × platform × weekday × month × hour × daypart เดียวกัน {int(metrics['matched_strata_count']):,} strata; ชั่วโมงที่ไม่มีใน export ไม่ถูกตีความเป็นศูนย์")

    code_options = scorecard["base_code"].tolist()
    selected_code = st.selectbox("เลือก rate code", code_options, index=code_options.index("RC102") if "RC102" in code_options else 0, key="campaign_rate_code")
    selected = scorecard.set_index("base_code").loc[selected_code]
    selected_match = matched.loc[matched["base_code"] == selected_code]
    p1, p2, p3, p4, p5 = st.columns(5)
    p1.metric("ส่วนลด", pct(selected["discount_pct"]))
    p2.metric("สัดส่วนแก้วจากโปรโมชัน", pct(selected["promo_share_cups"]))
    p3.metric("มูลค่าส่วนลด", money(selected["discount_cost_thb"]))
    p4.metric("เงินเหลือก่อน Waste/แก้ว", money(selected["contribution_before_waste_per_cup_thb"], 2))
    p5.metric("แก้วต่อชั่วโมงที่มีรายการขาย", f"{selected['cups_per_active_hour']:,.1f} แก้ว")
    if not selected_match.empty:
        row = selected_match.iloc[0]
        st.warning(f"{selected_code}: observed lift {pct(row['actual_demand_lift_pct'])} ยังต่ำกว่า break-even lift {pct(row['break_even_lift_pct'])}; เงินเหลือเพิ่มเทียบกลุ่มอ้างอิง {money(row['incremental_contribution_thb'])} จึงให้จำกัดกลุ่มหรือทดสอบต่อ ไม่ใช้แบบกว้าง")

    with st.expander("รายละเอียดการออกแบบและตรวจแคมเปญ"):
        st.markdown("**ประสิทธิภาพและการพึ่งพาโปรโมชัน**")
        efficiency = data["promo_efficiency"].copy()
        matrix = efficiency.set_index("base_code")[["actual_demand_lift_pct", "contribution_lift_pct"]].mul(100)
        matrix.columns = ["Sales lift (%)", "Contribution lift (%)"]
        st.bar_chart(matrix, height=260)
        display_table(
            efficiency,
            ["base_code", "actual_demand_lift_pct", "break_even_lift_pct", "contribution_lift_pct", "incremental_contribution_thb", "promo_discount_cost_thb", "decision"],
            {"base_code": "Code", "actual_demand_lift_pct": "Observed lift", "break_even_lift_pct": "Break-even lift", "contribution_lift_pct": "Contribution lift", "incremental_contribution_thb": "เงินเหลือเพิ่มเทียบกลุ่มอ้างอิง", "promo_discount_cost_thb": "มูลค่าส่วนลด", "decision": "ผลคัดกรอง"},
            money_columns=("incremental_contribution_thb", "promo_discount_cost_thb"), percent_columns=("actual_demand_lift_pct", "break_even_lift_pct", "contribution_lift_pct"),
        )
        dependency = data["promo_dependency"].copy()
        st.markdown("**สัดส่วนยอดขายที่มาจากโปรโมชันตามสินค้า**")
        st.bar_chart(dependency.set_index("sku")[["promo_share_cups"]].mul(100).rename(columns={"promo_share_cups": "% ของยอดขาย"}), height=240)
        display_table(
            dependency, list(dependency.columns),
            {"sku": "SKU", "promo_units": "แก้วจากโปรโมชัน", "total_units": "แก้วรวม", "promo_share_cups": "สัดส่วนจากโปรโมชัน"},
            integer_columns=("promo_units", "total_units"), percent_columns=("promo_share_cups",),
        )

        st.markdown("**หา segment ที่ควรจำกัดกลุ่มหรือทดสอบต่อ**")
        segment_view = st.selectbox("ดูแยกตาม", ["SKU", "ครัว", "Platform", "ชั่วโมง", "ช่วงเวลา"], key="campaign_segment_view")
        segment_specs = {
            "SKU": ("promo_by_sku", "sku"), "ครัว": ("promo_by_kitchen", "kitchen"),
            "Platform": ("promo_by_platform", "platform_name"), "ชั่วโมง": ("promo_by_hour", "hour"), "ช่วงเวลา": ("promo_by_daypart", "daypart"),
        }
        key, label_col = segment_specs[segment_view]
        segment = data[key].copy()
        view_columns = [label_col, "base_code", "matched_strata", "promo_units", "baseline_units", "promo_cups_per_active_hour", "baseline_cups_per_active_hour", "actual_demand_lift_pct", "break_even_lift_pct", "contribution_lift_pct", "incremental_contribution_thb", "decision"]
        display_table(
            segment.sort_values("incremental_contribution_thb"), view_columns,
            {label_col: segment_view, "base_code": "Code", "matched_strata": "Matched strata", "promo_units": "แก้วจากโปรฯ", "baseline_units": "แก้วกลุ่มอ้างอิง", "promo_cups_per_active_hour": "แก้วโปรฯ/ชั่วโมง", "baseline_cups_per_active_hour": "แก้วกลุ่มอ้างอิง/ชั่วโมง", "actual_demand_lift_pct": "Observed lift", "break_even_lift_pct": "Break-even lift", "contribution_lift_pct": "Contribution lift", "incremental_contribution_thb": "เงินเหลือเพิ่มเทียบกลุ่มอ้างอิง", "decision": "ผลคัดกรอง"},
            money_columns=("incremental_contribution_thb",), percent_columns=("actual_demand_lift_pct", "break_even_lift_pct", "contribution_lift_pct"), integer_columns=("matched_strata", "promo_units", "baseline_units"), decimal_columns=("promo_cups_per_active_hour", "baseline_cups_per_active_hour"),
            height=360,
        )

        st.markdown("**ส่วนลดสูงสุดและยอดขายเพิ่มที่ต้องมี**")
        depth = data["promo_depth"].copy()
        depth_sku_options = depth["sku"].drop_duplicates().tolist()
        depth_sku = st.selectbox("เลือก SKU เพื่อดูระดับส่วนลด", depth_sku_options, index=depth_sku_options.index("MixedBerryPremium") if "MixedBerryPremium" in depth_sku_options else 0, key="campaign_discount_sku")
        depth_view = depth.loc[depth["sku"] == depth_sku].sort_values("discount_pct").copy()
        depth_chart = depth_view.set_index("discount_pct")[["required_demand_lift_pct"]].mul(100)
        depth_chart.columns = ["Lift ที่ต้องมีเพื่อรักษาเงินเหลือ (%)"]
        st.line_chart(depth_chart, height=260)
        display_table(
            depth_view,
            ["discount_pct", "effective_price_thb", "promo_contribution_per_cup_thb", "contribution_delta_per_cup_thb", "required_demand_lift_pct"],
            {"discount_pct": "ส่วนลด", "effective_price_thb": "ราคาหลังส่วนลด", "promo_contribution_per_cup_thb": "เงินเหลือโปรโมชัน/แก้ว", "contribution_delta_per_cup_thb": "เงินเหลือลดลง/แก้ว", "required_demand_lift_pct": "Lift ที่ต้องมีเพื่อรักษาเงินเหลือ"},
            money_columns=("effective_price_thb", "promo_contribution_per_cup_thb", "contribution_delta_per_cup_thb"), percent_columns=("discount_pct", "required_demand_lift_pct"),
        )

    st.markdown("#### กติกาก่อนขยายโปรโมชัน")
    st.write("ขยายการใช้ส่วนลดเมื่อเงินเหลือเพิ่มเทียบ control เป็นบวก และ observed lift สูงกว่า break-even lift เท่านั้น เริ่มจาก segment SKU–kitchen–platform–daypart ที่ผ่าน gate แล้วติดตาม Waste แยกในระดับ Kitchen × SKU")
    st.warning("การเปรียบเทียบนี้เป็น historical association ไม่ใช่ causal effect เพราะไม่มีการสุ่มกลุ่มลูกค้า ข้อมูล cannibalization หรือ stockout และ " + metrics["waste_boundary"])


def finance(data: dict) -> None:
    task_heading(
        "Task 4 · Portfolio & budget performance",
        "Portfolio, Kitchen & Budget",
        "ดูว่า SKU หรือครัวใดฉุด contribution และส่ง action ร่วมระหว่าง E-Commerce กับ Operations",
        "Actual: ก.ย. 2025–ส.ค. 2026 · Waste และ contribution หลัง Waste ใช้ได้ในระดับ Kitchen × SKU",
    )
    totals = data["finance_metrics"]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("รายได้จากการขาย", money(totals["historical_revenue_thb"]))
    c2.metric("ส่วนต่างรายได้เทียบงบ", money(totals["total_revenue_variance_thb"]))
    c3.metric("เงินเหลือก่อน Waste", money(totals["historical_contribution_before_waste_thb"]), pct(totals["historical_contribution_margin_pct"]))
    c4.metric("ต้นทุน Waste ที่บันทึก", money(totals["historical_waste_cost_thb"]))
    c5.metric("ผลดำเนินงานตามแบบจำลอง", money(totals["historical_modeled_operating_result_thb"]), pct(totals["historical_operating_margin_pct"]))

    company = data["pnl_company"]
    st.markdown("#### จากรายได้สู่ผลดำเนินงานตามแบบจำลอง")
    st.info("รายได้คือราคาที่ลูกค้าจ่ายหลังโปรโมชัน เงินเหลือก่อน Waste = รายได้ − ต้นทุนผลไม้ − บรรจุภัณฑ์ − แรงงาน − ค่าคอมมิชชัน ผลดำเนินงานตามแบบจำลอง = เงินเหลือก่อน Waste − Waste ที่บันทึก − ค่าใช้จ่ายคงที่ของครัว")
    waterfall = data["pnl_waterfall"]
    waterfall_chart = waterfall.set_index("pnl_component")[["thb"]].copy()
    waterfall_chart.index = ["รายได้", "ต้นทุนผลไม้", "บรรจุภัณฑ์", "แรงงาน", "ค่าคอมมิชชัน", "เงินเหลือก่อน Waste", "ต้นทุน Waste", "เงินเหลือหลัง Waste", "ค่าใช้จ่ายคงที่", "ผลดำเนินงาน"]
    st.bar_chart(waterfall_chart.rename(columns={"thb": "บาท"}), height=320)
    display_table(
        waterfall,
        ["pnl_component", "thb", "definition"],
        {"pnl_component": "รายการ", "thb": "จำนวนเงิน", "definition": "นิยาม"},
        money_columns=("thb",),
    )

    st.markdown("#### รายได้จริงเทียบงบรายเดือน")
    st.caption("เทียบรายได้กับงบได้โดยตรง แต่ไม่ตีความผลดำเนินงานตามแบบจำลองเป็น GP variance เพราะงบไม่ระบุว่า GP รวม commission, Waste, labor หรือ fixed overhead หรือไม่")
    pnl = company.copy().set_index("month")
    chart = pnl[["gross_revenue_thb", "budget_revenue_thb"]].rename(columns={"gross_revenue_thb": "รายได้จริง", "budget_revenue_thb": "งบรายได้"})
    st.line_chart(chart, height=320)
    monthly_cols = ["month", "gross_revenue_thb", "budget_revenue_thb", "revenue_variance_thb", "revenue_variance_pct", "budget_gross_profit_thb", "product_margin_thb", "contribution_before_waste_thb", "contribution_after_waste_thb", "modeled_operating_result_thb", "budget_gp_boundary_status"]
    display_table(
        company, monthly_cols,
        {"month": "เดือน", "gross_revenue_thb": "รายได้จริง", "budget_revenue_thb": "งบรายได้", "revenue_variance_thb": "ส่วนต่าง", "revenue_variance_pct": "ส่วนต่าง (%)", "budget_gross_profit_thb": "GP ในงบ (ขอบเขตไม่ชัด)", "product_margin_thb": "ราคาหักต้นทุนสินค้า", "contribution_before_waste_thb": "เงินเหลือก่อน Waste", "contribution_after_waste_thb": "เงินเหลือหลัง Waste", "modeled_operating_result_thb": "ผลดำเนินงานตามแบบจำลอง", "budget_gp_boundary_status": "สถานะเทียบ GP"},
        money_columns=("gross_revenue_thb", "budget_revenue_thb", "revenue_variance_thb", "budget_gross_profit_thb", "product_margin_thb", "contribution_before_waste_thb", "contribution_after_waste_thb", "modeled_operating_result_thb"), percent_columns=("revenue_variance_pct",), date_columns=("month",),
        height=370,
    )

    st.markdown("#### SKU ใดควรแก้หรือคงไว้?")
    portfolio = data["portfolio"].copy()
    sku_action_map = {
        "Watermelon": "รักษาราคา; ทดสอบราคาในช่วง Demand สูง", "Pineapple": "รักษาราคา; ทดสอบราคาในช่วง Demand สูง",
        "Guava": "รักษาราคา; ทำ controlled price test", "PassionFruit": "ทบทวน mix, Waste และบทบาทสินค้า",
        "MixedBerryPremium": "แก้ราคา portion และการเตรียมก่อนเพิ่ม volume",
    }
    portfolio["action_display"] = portfolio["sku"].map(sku_action_map)
    left, right = st.columns(2)
    with left:
        st.bar_chart(portfolio.set_index("sku")[["contribution_after_waste_thb"]].rename(columns={"contribution_after_waste_thb": "เงินเหลือหลัง Waste (บาท)"}), height=280)
    with right:
        st.scatter_chart(portfolio, x="units_sold", y="contribution_after_waste_margin_pct", size="gross_revenue_thb", color="sku", x_label="จำนวนแก้วที่ขาย", y_label="Margin หลัง Waste", height=280)
    display_table(
        portfolio.sort_values("contribution_after_waste_thb", ascending=False),
        ["sku", "units_sold", "gross_revenue_thb", "revenue_share", "contribution_after_waste_thb", "contribution_after_waste_per_cup_thb", "contribution_after_waste_margin_pct", "waste_cost_thb", "waste_rate", "action_display"],
        {"sku": "SKU", "units_sold": "จำนวนแก้วที่ขาย", "gross_revenue_thb": "รายได้", "revenue_share": "สัดส่วนรายได้", "contribution_after_waste_thb": "เงินเหลือหลัง Waste", "contribution_after_waste_per_cup_thb": "เงินเหลือ/แก้ว", "contribution_after_waste_margin_pct": "Contribution margin", "waste_cost_thb": "ต้นทุน Waste", "waste_rate": "Waste rate", "action_display": "Action ที่เสนอ"},
        money_columns=("gross_revenue_thb", "contribution_after_waste_thb", "contribution_after_waste_per_cup_thb", "waste_cost_thb"), percent_columns=("revenue_share", "contribution_after_waste_margin_pct", "waste_rate"), integer_columns=("units_sold",),
    )
    st.caption("เงินเหลือราย SKU หลัง Waste ยังไม่หักค่าใช้จ่ายคงที่ของครัว จึงไม่ใช่กำไรสุทธิ SKU")

    st.markdown("#### ครัวใดควรแก้ก่อน?")
    kitchen_rollup = data["finance_kitchen"].copy()
    kitchen_action_map = {"BKK_Ladprao": "แก้ก่อน: ผลติดลบและ Waste สูงสุด", "BKK_Sukhumvit": "แก้ลำดับสอง: ผลติดลบ", "Pattaya_Beach": "รักษาผลบวกและคุม Waste", "Pattaya_Central": "รักษาผลบวกและคุม Waste"}
    kitchen_rollup["action_display"] = kitchen_rollup["kitchen"].map(kitchen_action_map)
    left, right = st.columns(2)
    left.markdown("**ผลดำเนินงานตามแบบจำลองรายครัว**")
    left.bar_chart(kitchen_rollup.set_index("kitchen")[["modeled_operating_result_thb"]].rename(columns={"modeled_operating_result_thb": "บาท"}), height=270)
    right.markdown("**ต้นทุน Waste รายครัว**")
    right.bar_chart(kitchen_rollup.set_index("kitchen")[["waste_cost_thb"]].rename(columns={"waste_cost_thb": "บาท"}), height=270)
    display_table(
        kitchen_rollup.sort_values("modeled_operating_result_thb"),
        ["kitchen", "units_sold", "gross_revenue_thb", "contribution_before_waste_thb", "waste_cost_thb", "waste_rate", "fixed_monthly_overhead_thb", "modeled_operating_result_thb", "operating_margin_pct", "action_display"],
        {"kitchen": "ครัว", "units_sold": "จำนวนแก้วที่ขาย", "gross_revenue_thb": "รายได้", "contribution_before_waste_thb": "เงินเหลือก่อน Waste", "waste_cost_thb": "ต้นทุน Waste", "waste_rate": "Waste rate", "fixed_monthly_overhead_thb": "ค่าใช้จ่ายคงที่", "modeled_operating_result_thb": "ผลดำเนินงานตามแบบจำลอง", "operating_margin_pct": "Operating margin", "action_display": "ลำดับความสำคัญ"},
        money_columns=("gross_revenue_thb", "contribution_before_waste_thb", "waste_cost_thb", "fixed_monthly_overhead_thb", "modeled_operating_result_thb"), percent_columns=("waste_rate", "operating_margin_pct"), integer_columns=("units_sold",),
    )
    kitchen_options = kitchen_rollup["kitchen"].tolist()
    selected_kitchen = st.selectbox("ดูแนวโน้มรายเดือนของครัว", kitchen_options, index=kitchen_options.index("BKK_Ladprao") if "BKK_Ladprao" in kitchen_options else 0, key="portfolio_kitchen")
    kitchen = data["pnl_kitchen"].loc[data["pnl_kitchen"]["kitchen"] == selected_kitchen].copy().set_index("month")
    st.line_chart(kitchen[["contribution_after_waste_thb", "modeled_operating_result_thb"]].rename(columns={"contribution_after_waste_thb": "เงินเหลือหลัง Waste", "modeled_operating_result_thb": "ผลดำเนินงานตามแบบจำลอง"}), height=260)

    st.markdown("#### Kitchen × SKU ที่ต้องส่งต่อให้ Operations")
    contribution_by_cell = data["sku_kitchen_pareto"][["kitchen", "sku", "contribution_after_waste_thb", "contribution_after_waste_per_cup_thb"]]
    waste_exceptions = data["waste_heatmap"].merge(contribution_by_cell, on=["kitchen", "sku"], how="left")
    waste_exceptions["handoff_action"] = waste_exceptions.apply(
        lambda row: "แก้ก่อน: ทบทวนราคา/portion และลด batch" if row["contribution_after_waste_thb"] < 0
        else "ลด batch / เพิ่มความถี่ และทบทวน mix" if row["waste_rate"] >= 0.10
        else "ติดตาม Waste และ contribution",
        axis=1,
    )
    waste_exceptions = waste_exceptions.sort_values(["contribution_after_waste_thb", "waste_rate"], ascending=[True, False]).head(8)
    display_table(
        waste_exceptions,
        ["kitchen", "sku", "units_sold", "units_wasted", "waste_rate", "waste_cost_thb", "contribution_after_waste_thb", "contribution_after_waste_per_cup_thb", "handoff_action"],
        {"kitchen": "ครัว", "sku": "SKU", "units_sold": "แก้วที่ขาย", "units_wasted": "Waste (แก้ว)", "waste_rate": "Waste rate", "waste_cost_thb": "ต้นทุน Waste", "contribution_after_waste_thb": "เงินเหลือหลัง Waste", "contribution_after_waste_per_cup_thb": "เงินเหลือหลัง Waste/แก้ว", "handoff_action": "Action ส่งต่อ"},
        integer_columns=("units_sold", "units_wasted"), percent_columns=("waste_rate",), money_columns=("waste_cost_thb", "contribution_after_waste_thb", "contribution_after_waste_per_cup_thb"),
    )
    st.caption("ตารางนี้เป็น Kitchen × SKU เท่านั้น ไม่ได้ระบุว่า Waste เกิดจาก Platform หรือ rate code ใด")

    with st.expander("รายละเอียดต้นทุน Waste และ sensitivity"):
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
    task_heading(
        "Task 5 · Inventory & 3-month outlook",
        "Forecast & Prep Plan",
        "แปลง Forecast ยอดขายเป็นเป้าเตรียมราย Kitchen × SKU และวัดช่องว่างสู่กำไร โดยไม่สร้างยอดขายหรือ Purchase Order ที่ข้อมูลยังรองรับไม่ได้",
        "ข้อมูลถึง 31 ส.ค. 2026 · กรอบเวลาเดิมของกรณีศึกษา ก.ย.–พ.ย. 2026 · ไม่ใช่ Forecast สด ณ วันนี้",
    )
    scenario = data["scenario"].copy()
    base = scenario.loc[scenario["scenario"] == "base"]
    requirements = data["requirements"].copy()
    policy = data["inventory_policy"].copy()
    metrics = data["metrics"]
    gap = metrics["profitability_gap"]
    baseline_units = float(base["forecast_units"].sum())
    baseline_prep = float(requirements["prep_target_cups_base"].sum())
    expected_waste = float(requirements["expected_waste_units_base"].sum())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Forecast ฐาน · 3 เดือน", f"{baseline_units:,.0f} แก้ว")
    c2.metric("เป้าเตรียม · 3 เดือน", f"{baseline_prep:,.0f} แก้ว")
    c3.metric("Waste ที่คาด · 3 เดือน", f"{expected_waste:,.0f} แก้ว")
    c4.metric("ผลดำเนินงานฐาน · 3 เดือน", money(base["modeled_operating_result_thb"].sum()))
    st.info(
        f"ตัวเลขเชื่อมกันดังนี้: เป้าเตรียม {baseline_prep:,.0f} = Forecast ขาย {baseline_units:,.0f} + Waste ที่คาด {expected_waste:,.0f} แก้ว (ต่างเล็กน้อยจากการปัดเศษ) · "
        f"ช่วงวางแผน {metrics['base_forecast_lower_units']:,.0f}–{metrics['base_forecast_upper_units']:,.0f} แก้วมาจาก backtest error ราย SKU ไม่ใช่ statistical confidence interval"
    )
    st.warning("ช่วง ก.ย.–พ.ย. 2026 เป็นกรอบเวลาเดิมของ case ที่ตัดข้อมูล ณ 31 ส.ค. 2026 หากนำไปใช้จริงหลังวันดังกล่าว ต้องเติม Actual ที่เกิดขึ้นแล้วและ Forecast ใหม่ก่อนส่งเป้าเตรียม")
    st.caption("Future platform mix ถูกถือคงที่ตาม recent mix และไม่ได้จำลอง campaign uplift แบบ causal")

    st.markdown("#### ภาพรวม Forecast และเป้าเตรียมที่ปล่อย")
    monthly_plan = requirements.groupby("month", as_index=False).agg(
        forecast_lower_units=("forecast_lower_units", "sum"),
        forecast_units_base=("forecast_units_base", "sum"),
        forecast_upper_units=("forecast_upper_units", "sum"),
        prep_target_cups_base=("prep_target_cups_base", "sum"),
        expected_waste_units_base=("expected_waste_units_base", "sum"),
    ).merge(
        base[["month", "modeled_operating_result_thb"]], on="month", how="left", validate="one_to_one"
    )
    display_table(
        monthly_plan,
        ["month", "forecast_lower_units", "forecast_units_base", "forecast_upper_units", "prep_target_cups_base", "expected_waste_units_base", "modeled_operating_result_thb"],
        {"month": "เดือน", "forecast_lower_units": "ขอบล่าง (แก้ว/เดือน)", "forecast_units_base": "Forecast ขาย (แก้ว/เดือน)", "forecast_upper_units": "ขอบบน (แก้ว/เดือน)", "prep_target_cups_base": "เป้าเตรียม (แก้ว/เดือน)", "expected_waste_units_base": "Waste ที่คาด (แก้ว/เดือน)", "modeled_operating_result_thb": "ผลดำเนินงานฐาน (บาท/เดือน)"},
        date_columns=("month",), integer_columns=("forecast_lower_units", "forecast_units_base", "forecast_upper_units", "prep_target_cups_base", "expected_waste_units_base"), money_columns=("modeled_operating_result_thb",),
    )
    st.bar_chart(
        monthly_plan.set_index("month")[["forecast_units_base", "prep_target_cups_base"]].rename(columns={"forecast_units_base": "Forecast ขาย", "prep_target_cups_base": "เป้าเตรียม"}),
        height=260, stack=False, x_label="เดือน", y_label="แก้ว/เดือน",
    )

    st.markdown("#### Demand ต่อเนื่อง: ใช้ช่วงละ 7 วันเต็ม")
    forecast_start = requirements["date"].min()
    actual_daily = data["daily"].groupby("date", as_index=False)["units_sold"].sum()
    actual_daily = actual_daily.loc[(actual_daily["date"] >= forecast_start - pd.Timedelta(days=91)) & (actual_daily["date"] < forecast_start)].copy()
    actual_daily["period_start"] = forecast_start + pd.to_timedelta(((actual_daily["date"] - forecast_start).dt.days // 7) * 7, unit="D")
    history_7d = actual_daily.groupby("period_start")["units_sold"].sum().rename("Actual · 7 วัน")
    future_daily = data["forecast"].groupby("date", as_index=False)["forecast_units_base"].sum()
    future_daily["period_start"] = forecast_start + pd.to_timedelta(((future_daily["date"] - forecast_start).dt.days // 7) * 7, unit="D")
    forecast_7d = future_daily.groupby("period_start")["forecast_units_base"].sum().rename("Forecast · 7 วัน")
    st.line_chart(pd.concat([history_7d, forecast_7d], axis=1), height=280)
    weekly_shape_note = " Forecast รายสัปดาห์จึงคงที่ตามโครงสร้างโมเดล: มีรูปแบบรายวันตาม weekday แต่ยังไม่มี trend หรือฤดูกาลรายปี" if forecast_7d.nunique() == 1 else ""
    st.caption("แต่ละจุดมี 7 วันเท่ากัน จึงไม่มีหน้าผาเทียมจากสัปดาห์ปฏิทินที่มี Actual 1 วันหรือ Forecast 6 วัน" + weekly_shape_note)

    autumn_source = data["daily"].assign(month=lambda frame: frame["date"].dt.to_period("M").dt.to_timestamp())
    autumn_source = autumn_source.loc[(autumn_source["month"] >= pd.Timestamp("2025-09-01")) & (autumn_source["month"] <= pd.Timestamp("2025-11-01"))].copy()
    common_skus = sorted(set(autumn_source["sku"].unique()) & set(requirements["sku"].unique()))
    autumn_actual = autumn_source.loc[autumn_source["sku"].isin(common_skus)].groupby("month", as_index=False)["units_sold"].sum()
    autumn_actual["month_number"] = autumn_actual["month"].dt.month
    common_forecast = requirements.loc[requirements["sku"].isin(common_skus)].groupby("month", as_index=False).agg(
        forecast_units_base=("forecast_units_base", "sum"), forecast_upper_units=("forecast_upper_units", "sum")
    )
    common_forecast["month_number"] = common_forecast["month"].dt.month
    autumn_compare = pd.DataFrame(index=[9, 10, 11])
    autumn_compare["Actual 2025 · SKU ร่วม"] = autumn_actual.set_index("month_number")["units_sold"]
    autumn_compare["Forecast ฐาน 2026 · SKU ร่วม"] = common_forecast.set_index("month_number")["forecast_units_base"]
    autumn_compare["ขอบบน 2026 · SKU ร่วม"] = common_forecast.set_index("month_number")["forecast_upper_units"]
    autumn_compare.index = [MONTH_NAMES[value] for value in autumn_compare.index]
    st.markdown("#### เช็กฤดูกาลกับช่วงเดียวกันปีก่อน")
    st.bar_chart(autumn_compare, height=260, stack=False, x_label="เดือน", y_label="แก้ว/เดือน")
    oct_actual = float(autumn_actual.loc[autumn_actual["month_number"] == 10, "units_sold"].iloc[0])
    nov_actual = float(autumn_actual.loc[autumn_actual["month_number"] == 11, "units_sold"].iloc[0])
    new_sku_units = float(requirements.loc[~requirements["sku"].isin(common_skus), "forecast_units_base"].sum())
    st.caption(f"เทียบเฉพาะ SKU ที่มีทั้งสองช่วง ({', '.join(common_skus)}); SKU เปิดตัวใหม่แยกออกจากกราฟและมี Forecast 2026 รวม {new_sku_units:,.0f} แก้ว พ.ย. 2025 สูงกว่า ต.ค. 2025 {pct(nov_actual / oct_actual - 1)} แต่มีหลักฐานช่วง ก.ย.–พ.ย. ปีก่อนเพียง 1 รอบ จึงเป็น seasonality watch ไม่บังคับให้เป็น Forecast ฐาน")

    st.markdown("#### ผลตามแบบจำลอง 3 สถานการณ์ที่ตรวจสอบได้")
    scenario_names = {
        "base": "ฐาน · ราคา/ต้นทุน/Waste ล่าสุด",
        "price_and_waste_action": "ราคา RC000 + ลด Waste 25%",
        "downside": "ความเสี่ยง · Demand ขอบล่าง + ต้นทุนสูง",
    }
    scenario_basis = {
        "base": "Demand จากวิธีที่ชนะ backtest; ราคาที่รับจริงและต้นทุน/Waste ล่าสุด",
        "price_and_waste_action": "Demand เท่าฐาน; ใช้ราคาที่รับจริงของ RC000 และลด Waste rate 25%; ไม่สมมติยอดขายเพิ่ม",
        "downside": "Demand ที่ขอบล่างราย SKU; fruit cost p90 และ Waste rate 1.25 เท่า",
    }
    scenario["scenario_name"] = scenario["scenario"].map(scenario_names)
    scenario_chart = scenario.pivot(index="month", columns="scenario_name", values="modeled_operating_result_thb")
    scenario_chart = scenario_chart.reindex(columns=[scenario_names["base"], scenario_names["price_and_waste_action"], scenario_names["downside"]])
    st.bar_chart(scenario_chart, height=280, stack=False, x_label="เดือน", y_label="ผลดำเนินงาน (บาท/เดือน)")
    scenario_total = scenario.groupby("scenario", as_index=False).agg(
        forecast_units=("forecast_units", "sum"), revenue_thb=("revenue_thb", "sum"), contribution_after_waste_thb=("contribution_after_waste_thb", "sum"), fixed_overhead_thb=("fixed_overhead_thb", "sum"), modeled_operating_result_thb=("modeled_operating_result_thb", "sum")
    )
    scenario_total["scenario_display_name"] = scenario_total["scenario"].map(scenario_names)
    scenario_total["basis"] = scenario_total["scenario"].map(scenario_basis)
    scenario_total["sort_order"] = scenario_total["scenario"].map({"base": 0, "price_and_waste_action": 1, "downside": 2})
    display_table(
        scenario_total.sort_values("sort_order"),
        ["scenario_display_name", "basis", "forecast_units", "revenue_thb", "contribution_after_waste_thb", "fixed_overhead_thb", "modeled_operating_result_thb"],
        {"scenario_display_name": "สถานการณ์ · รวม 3 เดือน", "basis": "สมมติฐาน", "forecast_units": "Demand · 3 เดือน (แก้ว)", "revenue_thb": "รายได้ · 3 เดือน", "contribution_after_waste_thb": "เงินเหลือหลัง Waste · 3 เดือน", "fixed_overhead_thb": "ค่าใช้จ่ายคงที่ · 3 เดือน", "modeled_operating_result_thb": "ผลดำเนินงาน · 3 เดือน"},
        integer_columns=("forecast_units",), money_columns=("revenue_thb", "contribution_after_waste_thb", "fixed_overhead_thb", "modeled_operating_result_thb"),
    )

    st.markdown("#### ช่องว่างสู่กำไร: แสดง hurdle ไม่สร้างเป้าขายย้อนกลับ")
    g1, g2, g3 = st.columns(3)
    g1.metric("ขาดทุนฐาน · 3 เดือน", money(gap["base_result_thb"]))
    g2.metric("ดีขึ้นจากราคา + Waste", money(gap["price_waste_action_improvement_thb"]))
    g3.metric("ช่องว่างคงเหลือถึงคุ้มทุน", money(gap["remaining_gap_to_break_even_thb"]))
    st.warning(
        f"Scenario ราคา + Waste ยังติดลบ {money(gap['remaining_gap_to_break_even_thb'])}. หากปิดช่องว่างด้วย volume เพียงทางเดียว จะต้องขายเพิ่มเทียบเท่า {gap['incremental_cups_equivalent']:,.0f} แก้ว "
        f"หรือ {pct(gap['incremental_cups_pct_of_base'])} เหนือ Forecast ฐาน ({gap['incremental_cups_per_day']:,.0f} แก้ว/วัน) ที่ contribution ต่อแก้วเดิม—นี่คือ hurdle เพื่อบอกขนาดปัญหา ไม่ใช่ Forecast หรือเป้ายอดขายที่อนุมัติ"
    )
    profit_actions = pd.DataFrame([
        ["ราคาและโปรโมชัน", "ทดสอบ RC000 เทียบ promo แบบมีกลุ่มควบคุม; นับผลเมื่อ contribution/แก้วดีขึ้นโดยยอดขายสุทธิไม่หาย", "E-Commerce / Growth", "รายสัปดาห์", "รวมอยู่ใน scenario ราคา + Waste แล้ว ห้ามนับซ้ำ"],
        ["Waste", "เริ่ม pilot 4 คู่ Kitchen × MixedBerry ที่เป็นสีแดง ใช้ batch เล็กและถี่ขึ้น", "Kitchen Operations", "ทุก 7 วัน", "เป็นเพียงส่วนย่อยของ scenario ที่สมมติ Waste −25% ครบ 20 คู่; ผล pilot รวมอยู่ใน scenario แล้ว ห้ามนับซ้ำ และต้องมีหลักฐานก่อน scale"],
        ["จัดซื้อและค่าใช้จ่ายคงที่", f"ขอราคา supplier และรายการ overhead จริง; ช่องว่างเทียบเท่า {pct(gap['fixed_overhead_reduction_equivalent_pct'])} ของ overhead 3 เดือนหากใช้คันโยกนี้อย่างเดียว", "Finance / Procurement", "ก่อนใส่ในแผน", "ไม่นับ savings จนมี quote/owner/capacity impact"],
        ["Volume", "เพิ่มเฉพาะ SKU ที่ contribution หลัง Waste เป็นบวก หลังผ่าน demand และ capacity test", "E-Commerce + Operations", "pilot แล้วค่อย scale", f"hurdle {gap['incremental_cups_equivalent']:,.0f} แก้วไม่ใช่คำสั่งให้เตรียมเพิ่ม"],
    ], columns=["คันโยก", "Action", "Owner ที่เสนอ", "รอบตัดสินใจ", "Gate ก่อนนับผล"])
    st.dataframe(profit_actions, width="stretch", hide_index=True)

    st.markdown("#### เป้าเตรียมที่ปล่อย: เลือกครัวและ SKU")
    col1, col2 = st.columns(2)
    kitchens = ["All"] + sorted(data["forecast"]["kitchen"].unique().tolist())
    skus = ["All"] + sorted(data["forecast"]["sku"].unique().tolist())
    selected_kitchen = col1.selectbox("เลือกครัว", kitchens, format_func=lambda option: "ทุกครัว" if option == "All" else option, key="forecast_kitchen")
    selected_sku = col2.selectbox("เลือก SKU สำหรับเป้าเตรียม", skus, format_func=lambda option: "ทุก SKU" if option == "All" else option, key="forecast_sku")
    req = requirements.copy()
    policy_view = policy.copy()
    if selected_kitchen != "All":
        req = req.loc[req["kitchen"] == selected_kitchen]
        policy_view = policy_view.loc[policy_view["kitchen"] == selected_kitchen]
    if selected_sku != "All":
        req = req.loc[req["sku"] == selected_sku]
        policy_view = policy_view.loc[policy_view["sku"] == selected_sku]
    selected_monthly = req.groupby("month", as_index=True).agg(
        forecast_units_base=("forecast_units_base", "sum"), prep_target_cups_base=("prep_target_cups_base", "sum")
    ).rename(columns={"forecast_units_base": "Forecast ขาย", "prep_target_cups_base": "เป้าเตรียม"})
    st.bar_chart(selected_monthly, height=260, stack=False, x_label="เดือน", y_label="แก้ว/เดือน")
    req["month"] = req["date"].dt.to_period("M").dt.to_timestamp()
    prep_monthly = req.groupby(["month", "kitchen", "sku"], as_index=False).agg(
        forecast_lower_units=("forecast_lower_units", "sum"), forecast_units_base=("forecast_units_base", "sum"), forecast_upper_units=("forecast_upper_units", "sum"), planning_error_pct=("planning_error_pct", "first"), waste_rate_base=("waste_rate_base", "first"), prep_target_cups_base=("prep_target_cups_base", "sum"), expected_waste_units_base=("expected_waste_units_base", "sum")
    )
    display_table(
        prep_monthly,
        ["month", "kitchen", "sku", "forecast_lower_units", "forecast_units_base", "forecast_upper_units", "planning_error_pct", "waste_rate_base", "prep_target_cups_base", "expected_waste_units_base"],
        {"month": "เดือน", "kitchen": "ครัว", "sku": "SKU", "forecast_lower_units": "ขอบล่าง (แก้ว/เดือน)", "forecast_units_base": "Forecast ขาย (แก้ว/เดือน)", "forecast_upper_units": "ขอบบน (แก้ว/เดือน)", "planning_error_pct": "SKU pooled WAPE ที่ใช้เป็นช่วงวางแผน", "waste_rate_base": "Waste rate", "prep_target_cups_base": "เป้าเตรียม (แก้ว/เดือน)", "expected_waste_units_base": "Waste ที่คาด (แก้ว/เดือน)"},
        date_columns=("month",), integer_columns=("forecast_lower_units", "forecast_units_base", "forecast_upper_units", "prep_target_cups_base", "expected_waste_units_base"), percent_columns=("planning_error_pct", "waste_rate_base"), height=380,
    )
    st.caption("เป้าเตรียมคำนวณด้วย Waste rate ของแต่ละ Kitchen × SKU และต้อง refresh ทุก 7 วัน; ไม่ใช่จำนวนสั่งซื้อจริงหรือจำนวนสั่งวัตถุดิบ")

    st.markdown("#### นโยบายเตรียมและ buffer กำลังผลิต 7 วัน")
    st.write("ABC อิงเงินเหลือหลัง Waste 3 เดือน ส่วน XYZ ใช้ทั้ง CV, แนวโน้ม 12 สัปดาห์ และความเสี่ยงจากสินค้าเปิดตัวใหม่ Buffer ที่แสดงเป็น cup-equivalent เพื่อเผื่อกำลังผลิต ไม่ใช่ของที่ควรเตรียมค้างไว้")
    alert_map = {
        "RED: loss + high waste": "แดง · เงินเหลือติดลบและ Waste สูงกว่าค่าเฉลี่ย",
        "AMBER: high waste": "เหลือง · Waste สูงกว่าค่าเฉลี่ย",
        "AMBER: volatile demand": "เหลือง · Demand ผันผวน",
        "GREEN: stable policy": "เขียว · ติดตามตามรอบ",
    }
    policy_map = {
        "High availability; weekly rolling forecast": "ทบทวน Forecast ทุก 7 วันและรักษาความพร้อมขาย",
        "Smaller/more frequent prep; tighten waste controls": "ลดขนาด batch และเตรียมถี่ขึ้นเพื่อคุม Waste",
        "Frequent review; conservative safety stock": "ทบทวนถี่และใช้ buffer อย่างระมัดระวัง",
        "Weekly rolling forecast with standard buffer": "ทบทวน Forecast ทุก 7 วันและใช้ buffer มาตรฐาน",
    }
    pattern_map = {"recent launch": "สินค้าใหม่", "material trend": "แนวโน้มเปลี่ยนมาก", "trend watch": "เฝ้าดูแนวโน้ม", "stable": "คงที่"}
    policy_view["alert_display"] = policy_view["inventory_alert"].map(alert_map).fillna(policy_view["inventory_alert"])
    policy_view["policy_display"] = policy_view["inventory_policy"].map(policy_map).fillna(policy_view["inventory_policy"])
    policy_view["pattern_display"] = policy_view["demand_pattern"].map(pattern_map).fillna(policy_view["demand_pattern"])
    display_table(
        policy_view.sort_values(["inventory_alert_rank", "waste_rate"], ascending=[True, False]),
        ["kitchen", "sku", "forecast_3m_cups", "avg_weekly_demand_cups", "recent_12w_trend_pct", "pattern_display", "waste_rate", "contribution_after_waste_per_cup_thb", "abc_class", "xyz_class", "next_7d_forecast_cups", "demand_buffer_7d_cups_policy", "planning_ceiling_next_7d_cups", "alert_display", "policy_display"],
        {"kitchen": "ครัว", "sku": "SKU", "forecast_3m_cups": "Forecast 3 เดือน", "avg_weekly_demand_cups": "เฉลี่ย/สัปดาห์", "recent_12w_trend_pct": "แนวโน้ม Last 4W vs First 4W", "pattern_display": "รูปแบบ Demand", "waste_rate": "Waste rate", "contribution_after_waste_per_cup_thb": "เงินเหลือหลัง Waste/แก้ว", "abc_class": "ABC", "xyz_class": "XYZ", "next_7d_forecast_cups": "Demand 7 วัน", "demand_buffer_7d_cups_policy": "Buffer ความผันผวน", "planning_ceiling_next_7d_cups": "Demand + buffer เพื่อวางกำลัง", "alert_display": "สถานะ", "policy_display": "แนวทาง"},
        integer_columns=("forecast_3m_cups", "avg_weekly_demand_cups", "next_7d_forecast_cups", "demand_buffer_7d_cups_policy", "planning_ceiling_next_7d_cups"), percent_columns=("recent_12w_trend_pct", "waste_rate"), money_columns=("contribution_after_waste_per_cup_thb",), height=450,
    )
    st.caption("Demand + buffer เป็นเพดานสำหรับวางกำลังผลิต ready-to-sell เท่านั้น ห้ามตีความเป็น physical stock, เป้าเตรียมล่วงหน้า หรือ PO; การเตรียมจริงให้ใช้ Forecast รายวัน + Waste ที่คาด และปรับจาก Actual")

    with st.expander("วิธี Forecast, sensitivity ต้นทุน และสูตรเมื่อข้อมูล Inventory ครบ"):
        st.markdown("**เลือกวิธี Forecast อย่างไร?**")
        st.write(f"เลือก `{metrics['selected_method']}` เพราะ pooled WAPE ต่ำสุด {pct(metrics['selected_method_pooled_wape'])} จาก 6 วิธีและ 4 rolling-origin cutoffs (ขอบเขตทดสอบ 28 วัน) โดยใช้ข้อมูลถึง 31 ส.ค. 2026 เท่านั้น วิธีนี้ผสมระดับ Demand ล่าสุดกับรูปแบบวันในสัปดาห์ จึงไม่สร้างเส้นรายวันแบน")
        backtest_view = data["backtest"].copy()
        display_table(
            backtest_view, ["method", "cutoffs", "mae", "wape", "bias_pct"],
            {"method": "วิธี", "cutoffs": "จำนวน cutoff", "mae": "MAE/วัน/คู่", "wape": "Pooled WAPE", "bias_pct": "Pooled Bias"},
            integer_columns=("cutoffs",), percent_columns=("wape", "bias_pct"), decimal_columns=("mae",),
        )
        st.caption(metrics["forecast_uncertainty_basis"] + " Forecast 3 เดือนไม่ได้ถูก freeze: ต้องเติม Actual และทบทวนทุก 7 วัน")
        st.caption(metrics["commission_basis"] + " " + metrics["mixedberry_note"])
        st.markdown("**หากต้นทุนผลไม้สูงขึ้น ผลเป็นอย่างไร?**")
        st.caption("ทุกแถวเป็นผลรวมตลอดกรอบ 3 เดือน ก.ย.–พ.ย. 2026")
        stress = data["fruit_cost_stress"].copy()
        stress["uplift_label"] = stress["fruit_cost_uplift_pct"].map(lambda value: pct(value, 0))
        st.line_chart(stress.set_index("uplift_label")[["modeled_operating_result_thb"]].rename(columns={"modeled_operating_result_thb": "ผลดำเนินงาน (บาท)"}), height=240)
        display_table(
            stress, ["fruit_cost_uplift_pct", "forecast_units", "revenue_thb", "fruit_cost_thb", "waste_cost_thb", "contribution_after_waste_thb", "fixed_overhead_thb", "modeled_operating_result_thb", "operating_margin_pct"],
            {"fruit_cost_uplift_pct": "ต้นทุนผลไม้เพิ่ม", "forecast_units": "Forecast · 3 เดือน (แก้ว)", "revenue_thb": "รายได้ · 3 เดือน", "fruit_cost_thb": "ต้นทุนผลไม้ · 3 เดือน", "waste_cost_thb": "ต้นทุน Waste · 3 เดือน", "contribution_after_waste_thb": "เงินเหลือหลัง Waste · 3 เดือน", "fixed_overhead_thb": "ค่าใช้จ่ายคงที่ · 3 เดือน", "modeled_operating_result_thb": "ผลดำเนินงาน · 3 เดือน", "operating_margin_pct": "Operating margin"},
            percent_columns=("fruit_cost_uplift_pct", "operating_margin_pct"), integer_columns=("forecast_units",), money_columns=("revenue_thb", "fruit_cost_thb", "waste_cost_thb", "contribution_after_waste_thb", "fixed_overhead_thb", "modeled_operating_result_thb"),
        )
        st.markdown("**สูตรเมื่อข้อมูล Inventory ครบ**")
        st.code("target_stock_ingredient_units = forecast_during_(lead_time + review_period) + safety_stock\norder_qty = max(0, target_stock_ingredient_units - usable_on_hand - usable_inbound + committed_demand)", language="text")
        st.info("ยังคำนวณจำนวนสั่งซื้อจริงไม่ได้ เพราะไม่มี on-hand, inbound, supplier lead time, shelf life, BOM/yield และ stockout flags ทุกพจน์ต้องแปลงเป็นหน่วยวัตถุดิบเดียวกันก่อนใช้สูตร; ระหว่างนี้ใช้เป้าเตรียมเป็นแก้วและทบทวน Forecast ทุก 7 วัน")


def data_quality(data: dict) -> None:
    task_heading(
        "Task 1 · Data quality",
        "Data Trust & Definitions",
        "ตรวจที่มาของตัวเลข การคัดกรอง และข้อจำกัดก่อนใช้ผลลัพธ์ตัดสินใจเรื่องแคมเปญ ราคา หรือการเตรียมสินค้า",
        "Released data version: fruitblend24_v1_c2869ce419bf · แหล่งข้อมูลเป็น historical export",
    )
    readiness = data["readiness"]
    raw = readiness["raw_orders"]
    candidate = readiness["candidate_preparation"]
    waste = readiness["waste"]
    reconciliation = data["reconciliation"]
    audit = data["audit"]
    checks = audit["checks"]
    c1, c2, c3 = st.columns(3)
    c1.metric("แถวรายการขายดิบ", f"{checks['raw_order_rows']:,}")
    c2.metric("แถวเมนูที่ใช้วิเคราะห์", f"{checks['retained_candidate_menu_rows']:,}")
    c3.metric("รายได้หลังคัดกรอง", money(reconciliation["retained_menu_revenue_thb"]))

    st.markdown("#### จากข้อมูลดิบสู่ข้อมูลวิเคราะห์ที่เผยแพร่")
    st.markdown(
        f"<div class='callout'><strong>ข้อมูลดิบ {reconciliation['raw_rows']:,} แถว</strong> → ตัด duplicate {reconciliation['duplicate_excess_rows_removed']:,} แถว → แยก non-menu {reconciliation['non_menu_rows_excluded']:,} แถว → <strong>เหลือเมนู {reconciliation['retained_menu_rows']:,} แถว</strong> สำหรับวิเคราะห์</div>",
        unsafe_allow_html=True,
    )
    st.caption(f"หากไม่ตัด duplicate รายได้จะสูงเกินประมาณ {money(reconciliation['duplicate_revenue_removed_thb'])}")

    st.markdown("#### สิ่งที่ตรวจและวิธีจัดการ")
    screening = pd.DataFrame([
        ["ค่าว่าง", "ไม่พบค่าว่างใน 9 field ของข้อมูลขายดิบ", "ไม่ต้อง impute ข้อมูลรายการขาย"],
        ["แถวซ้ำแบบตรงกัน", f"แถวเกิน {raw['exact_duplicate_excess_rows']:,} แถว คิดเป็นรายได้ {money(reconciliation['duplicate_revenue_removed_thb'])}", "ตัดแถวเกินและเก็บ audit trail"],
        ["วันที่ เวลา และจำนวนแก้ว", f"วันที่ผิด: {raw['invalid_dates']}; ชั่วโมงผิด: {raw['invalid_hours']}; จำนวนไม่เป็นบวก: {raw['nonpositive_units']}", "ไม่ปล่อยข้อมูลลักษณะนี้เข้าชุดวิเคราะห์"],
        ["ราคาและรายได้", f"ราคา × จำนวนแก้วไม่ตรง: {raw['revenue_identity_mismatch_rows_over_001_thb']}; สูตรส่วนลดไม่ตรง: {candidate['price_discount_formula_mismatch_rows_over_001_thb']}", "ใช้ราคาหลังโปรโมชันที่สังเกตได้ และไม่หักส่วนลดซ้ำ"],
        ["การ map สินค้า/รหัส", f"base code ไม่รู้จัก: {len(candidate['unknown_base_codes'])}; SKU suffix ไม่ตรง: {candidate['sku_suffix_mismatch_rows']}", "ใช้เฉพาะ 5 SKU ที่ map ได้ และแยก non-menu 370 แถว"],
        ["ต้นทุนครบถ้วน", f"ขาย {candidate['missing_exact_week_fruit_cost_rows']} แถว และ Waste {waste['missing_estimated_waste_cost_rows']} แถวต้องใช้ proxy", "เปิดเผยสมมติฐานและไม่แทนต้นทุนที่หายด้วยศูนย์"],
        ["ค่าผิดปกติ", "ไม่ตัดแถวที่ขาย/ราคาสูงเพียงเพราะสูง", "เก็บ peak และ seasonality; ตัดเฉพาะข้อมูลผิดรูปแบบหรือ map ไม่ได้"],
    ], columns=["สิ่งที่ตรวจ", "หลักฐาน", "การจัดการ"])
    st.dataframe(screening, width="stretch", hide_index=True)

    st.markdown("#### Reconciliation ก่อนและหลังคัดกรอง")
    bridge = pd.DataFrame([
        ["Raw export", reconciliation["raw_rows"], reconciliation["raw_units"], reconciliation["raw_revenue_thb"]],
        ["Less duplicate excess", -reconciliation["duplicate_excess_rows_removed"], -reconciliation["duplicate_units_removed"], -reconciliation["duplicate_revenue_removed_thb"]],
        ["Less non-menu rows", -reconciliation["non_menu_rows_excluded"], -reconciliation["non_menu_units_excluded"], -reconciliation["non_menu_revenue_excluded_thb"]],
        ["Released menu data", reconciliation["retained_menu_rows"], reconciliation["retained_menu_units"], reconciliation["retained_menu_revenue_thb"]],
    ], columns=["Bridge", "Rows", "Units", "Revenue (THB)"])
    bridge["Bridge"] = ["ข้อมูลดิบ", "หัก duplicate ส่วนเกิน", "หัก non-menu", "ข้อมูลเมนูที่เผยแพร่"]
    display_table(
        bridge, ["Bridge", "Rows", "Units", "Revenue (THB)"],
        {"Bridge": "ขั้น", "Rows": "แถว", "Units": "จำนวนแก้ว", "Revenue (THB)": "รายได้"}, integer_columns=("Rows", "Units"), money_columns=("Revenue (THB)",),
    )

    st.markdown("#### ประเด็นที่ต้องติดตาม")
    issues = data["issues"].copy()
    issues["severity_display"] = issues["severity"].map({"high": "สูง", "medium": "กลาง", "low": "ต่ำ"}).fillna(issues["severity"])
    issues["status_display"] = issues["status"].map({"released": "เผยแพร่แล้ว", "assumed": "ใช้สมมติฐาน", "open": "รอข้อมูล"}).fillna(issues["status"])
    display_table(
        issues, ["issue_id", "severity_display", "status_display", "issue", "impact", "recommended_action", "evidence"],
        {"issue_id": "ID", "severity_display": "ความรุนแรง", "status_display": "สถานะ", "issue": "ประเด็น", "impact": "ผลกระทบ", "recommended_action": "Action ที่เสนอ", "evidence": "หลักฐาน"},
        height=330,
    )

    st.markdown("#### สถานะการตรวจสอบ")
    release_qa = data["data_qa"]
    st.success(f"Data-release QA: {release_qa['status']} · ผ่าน {len(release_qa['checks']) - release_qa['failed_count']}/{len(release_qa['checks'])} checks")
    qa_df = pd.DataFrame(data["qa"]["checks"])
    qa_columns = [column for column in ["name", "result", "expected", "actual", "owner", "impact"] if column in qa_df]
    st.dataframe(qa_df[qa_columns].astype(str).rename(columns={"name": "รายการตรวจ", "result": "ผล", "expected": "คาดหวัง", "actual": "ค่าจริง", "owner": "เจ้าของเดิม", "impact": "ผลกระทบ"}), width="stretch", hide_index=True, height=360)
    st.caption("ไฟล์ต้นทางเป็น read-only และระบุ proxy ไว้ชัดเจน ข้อจำกัดที่เหลือคือขอบเขต GP ในงบ, grain ของ Waste และข้อมูลสำหรับควบคุมสินค้าคงคลังที่ยังไม่มี")


def main() -> None:
    st.set_page_config(page_title="FruitBlend24 | E-Commerce Dashboard", page_icon="🥤", layout="wide", initial_sidebar_state="collapsed")
    apply_theme()
    data = load_data()
    st.title("FruitBlend24 · ศูนย์ตัดสินใจ E-Commerce")
    st.caption("ใช้ข้อมูลย้อนหลังที่ผ่าน QA เพื่อเลือกแคมเปญ ราคา และแผนส่งต่อครัว · กรณีศึกษาข้อมูลจำลอง · รุ่นข้อมูล " + DATA_VERSION)
    st.sidebar.header("วิธีใช้แดชบอร์ด")
    st.sidebar.write("อ่านตามลำดับ Task 1 → 6 เพื่อไล่จากความน่าเชื่อถือของข้อมูล ไปสู่ข้อเสนอแนะสรุปสำหรับรอบถัดไป ตัวเลขทุกตัวมาจาก artifact ที่ผ่าน QA")
    st.sidebar.markdown("**ลำดับตาม Task**\n\n1. Task 1 · Data Trust & Definitions\n2. Task 2 · Sales, Price & Menu\n3. Task 3 · Platform & Campaign Control\n4. Task 4 · Portfolio, Kitchen & Budget\n5. Task 5 · Forecast-to-Kitchen Handoff\n6. Task 6 · E-Commerce Action Center")
    tabs = st.tabs(["Task 1 · Data Trust & Definitions", "Task 2 · Sales, Price & Menu", "Task 3 · Platform & Campaign Control", "Task 4 · Portfolio, Kitchen & Budget", "Task 5 · Forecast-to-Kitchen Handoff", "Task 6 · E-Commerce Action Center"])
    with tabs[0]:
        data_quality(data)
    with tabs[1]:
        demand_pricing(data)
    with tabs[2]:
        promotions(data)
    with tabs[3]:
        finance(data)
    with tabs[4]:
        forecast_inventory(data)
    with tabs[5]:
        overview(data)
    st.divider()
    st.caption("ขอบเขต: กรณีศึกษา FruitBlend24 แบบข้อมูลจำลอง ไม่ใช่ข้อมูลสด รายละเอียดสมมติฐานและ QA อยู่ใน reports/fruitblend24_run_001 และ data/processed/fruitblend24_v1_c2869ce419bf")


if __name__ == "__main__":
    main()
