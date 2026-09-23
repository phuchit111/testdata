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


MONTH_NAMES_TH = {
    1: "ม.ค.", 2: "ก.พ.", 3: "มี.ค.", 4: "เม.ย.", 5: "พ.ค.", 6: "มิ.ย.",
    7: "ก.ค.", 8: "ส.ค.", 9: "ก.ย.", 10: "ต.ค.", 11: "พ.ย.", 12: "ธ.ค.",
}
WEEKDAY_NAMES_TH = {0: "จันทร์", 1: "อังคาร", 2: "พุธ", 3: "พฤหัสบดี", 4: "ศุกร์", 5: "เสาร์", 6: "อาทิตย์"}


def month_th(value) -> str:
    timestamp = pd.Timestamp(value)
    return f"{MONTH_NAMES_TH[timestamp.month]} {timestamp.year}"


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
    """Show selected business fields with Thai labels and units that remain readable in a table."""
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
            view[column] = pd.to_datetime(view[column]).map(month_th)
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
    c1.metric("รายได้จากการขาย", money(revenue), "ยอดจริงหลังคัดข้อมูล")
    c2.metric("ต่างจากเป้ารายได้", money(revenue_variance), pct(revenue_variance / float(pnl["budget_revenue_thb"].sum())))
    c3.metric("ผลดำเนินงานตามแบบจำลอง", money(operating), "หลังของเสียและค่าใช้จ่ายคงที่")
    return revenue, revenue_variance, operating


def overview(data: dict) -> None:
    task_heading("Task 6 · สรุปเพื่อการตัดสินใจ", "ภาพรวมและแผนแก้ไข", "เริ่มจากภาพรวม แล้วค่อยเปิดดูหลักฐานเรื่องราคา โปรโมชั่น สินค้า ครัว และการเตรียมสินค้า")
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">FRUITBLEND24 · กรณีศึกษาข้อมูลจำลอง</div>
          <h2>ขายได้ แต่เงินที่เหลือหลังต้นทุนยังไม่พอ</h2>
          <p>รายได้อยู่ใกล้เป้าหมาย แต่ส่วนลด สินค้าที่มีเงินเหลือติดลบ ของเสีย และค่าใช้จ่ายคงที่ ทำให้ผลดำเนินงานตามแบบจำลองยังขาดทุน</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    revenue, revenue_variance, operating = metric_cards(data)
    st.caption("ผลย้อนหลัง: ก.ย. 2025–ส.ค. 2026 · แผนคาดการณ์: ก.ย.–พ.ย. 2026 · ไม่ใช่ข้อมูลสด")

    pnl = data["pnl_company"].copy().set_index("month")
    left, right = st.columns((1.1, 0.9))
    with left:
        st.markdown("#### ยอดขายจริงเทียบเป้าในแต่ละเดือน")
        st.line_chart(
            pnl[["gross_revenue_thb", "budget_revenue_thb"]].rename(columns={"gross_revenue_thb": "รายได้จริง", "budget_revenue_thb": "เป้ารายได้"}),
            height=280,
        )
    with right:
        st.markdown("#### เงินจากยอดขายหายไปกับอะไร?")
        waterfall = data["pnl_waterfall"].copy().set_index("pnl_component")
        waterfall.index = [
            "รายได้", "ต้นทุนผลไม้", "บรรจุภัณฑ์", "แรงงาน", "ค่าคอมมิชชันแพลตฟอร์ม",
            "เงินเหลือก่อนของเสีย", "ต้นทุนของเสีย", "เงินเหลือหลังของเสีย", "ค่าใช้จ่ายคงที่", "ผลดำเนินงาน",
        ]
        st.bar_chart(waterfall[["thb"]].rename(columns={"thb": "บาท"}), height=280)

    st.markdown("#### 5 ข้อค้นพบที่ควรใช้ตัดสินใจ")
    reconciliation = data["reconciliation"]
    peak_hour = data["hourly"].sort_values("units_sold", ascending=False).iloc[0]
    weekend_revenue_share = float(data["weekday"].loc[data["weekday"]["day_of_week"].isin([5, 6]), "revenue_share"].sum())
    mixed = data["sku"].loc[data["sku"]["sku"] == "MixedBerryPremium"].iloc[0]
    promo = data["promo"].set_index("base_code")
    base_wape = float(data["metrics"]["selected_method_mean_wape"])
    base_outlook = data["scenario"].loc[data["scenario"]["scenario"] == "base"]
    insights = pd.DataFrame([
        ["ข้อมูลพร้อมใช้", f"ตัดรายการซ้ำ 372 แถว ป้องกันรายได้ถูกนับเกิน {money(reconciliation['duplicate_revenue_removed_thb'])}; ตัดรายการที่ไม่ใช่เมนู 370 แถว", "ใช้เฉพาะข้อมูลเมนูที่ผ่านการคัดกรอง 123,655 แถว"],
        ["ลูกค้าซื้อเป็นช่วง", f"ยอดรวมสูงสุดอยู่ที่ 22:00 จำนวน {peak_hour['units_sold']:,.0f} แก้ว; เสาร์–อาทิตย์สร้างรายได้ {pct(weekend_revenue_share)}", "เพิ่มการเตรียมก่อนช่วงค่ำและวันหยุด ลดการเตรียมล่วงหน้าช่วงยอดต่ำ"],
        ["โปรโมชันกินเงินเหลือ", f"RC102 เหลือ {money(promo.loc['RC102', 'contribution_before_waste_per_cup_thb'], 2)}/แก้ว เทียบราคาปกติ {money(promo.loc['RC000', 'contribution_before_waste_per_cup_thb'], 2)}/แก้ว ก่อนของเสีย", "ใช้ราคาปกติเป็นกลุ่มเปรียบเทียบ และทดสอบโปรโมชันแบบควบคุม"],
        ["MixedBerryPremium ต้องแก้ก่อนขยาย", f"เงินเหลือหลังของเสีย {money(mixed['contribution_after_waste_thb'])} หรือ {money(mixed['contribution_after_waste_per_cup_thb'], 2)}/แก้ว; ของเสีย {pct(mixed['waste_rate'])}", "ทดลองปรับราคา ปริมาณ และการเตรียมเป็นรอบเล็กก่อนเพิ่มยอดขาย"],
        ["3 เดือนข้างหน้ายังมีช่องว่าง", f"กรณีฐานคาด {base_outlook['forecast_units'].sum():,.0f} แก้ว และขาดทุนตามแบบจำลอง {money(base_outlook['modeled_operating_result_thb'].sum())}; WAPE {pct(base_wape)}", "วางแผนเตรียมรายครัว–สินค้า และทำมาตรการราคา/ของเสียควบคู่กัน"],
    ], columns=["ข้อค้นพบ", "หลักฐานเชิงตัวเลข", "สิ่งที่ควรทำ"])
    st.dataframe(insights, width="stretch", hide_index=True)

    st.markdown("#### จุดที่ควรเริ่มแก้")
    card1, card2, card3 = st.columns(3)
    card1.warning("**สินค้า:** MixedBerryPremium\n\nเงินเหลือหลังของเสียติดลบ และมีของเสีย 20.5% จึงยังไม่ควรเร่งขยายยอด")
    card2.warning("**โปรโมชั่น:** RC101–RC103\n\nเงินเหลือต่อแก้วต่ำกว่าราคาปกติทั้งหมด ควรเลิกใช้แบบหว่านและทดสอบเฉพาะกลุ่ม")
    card3.warning("**ครัว:** BKK_Ladprao และ BKK_Sukhumvit\n\nผลดำเนินงานตามแบบจำลองติดลบ จึงควรไล่ดูคู่ครัว–สินค้าและของเสียก่อน")

    st.markdown("#### แผนลงมือทำ")
    actions = pd.DataFrame([
        ["ราคาและโปรโมชั่น", "ใช้ RC000 เป็นกลุ่มเปรียบเทียบ จำกัด RC101/RC103 และทดสอบ RC102 เฉพาะลูกค้าใหม่หรือช่วงยอดต่ำ โดยผ่านเกณฑ์เงินเหลือต่อแก้วก่อนขยาย", "ทีม Commercial + Growth (ข้อเสนอ)", "รอบแคมเปญถัดไป 2 สัปดาห์", "เงินเหลือต่อแก้ว, ยอดเพิ่มเทียบกลุ่มควบคุม, ของเสียจากโปรโมชัน"],
        ["สินค้า", "ทำ pilot MixedBerryPremium 4 สัปดาห์: ทดสอบราคา/ปริมาณต่อแก้ว และเตรียมแบบรอบเล็ก ห้ามขยายจนเงินเหลือหลังของเสียเป็นบวก", "ทีม Category + Kitchen Operations (ข้อเสนอ)", "เริ่มภายใน 1 สัปดาห์; ทบทวนรายสัปดาห์", "เงินเหลือหลังของเสียต่อแก้ว > 0; ของเสียต่ำกว่าเป้าหมาย pilot 10%"],
        ["การเตรียมสินค้า", f"ใช้ {data['metrics']['selected_method']} คาดการณ์รายวันระดับครัว–สินค้า รวมของเสียคาดการณ์เป็นเป้าเตรียม และทบทวนทุก 7 วัน", "ทีม Operations + Supply (ข้อเสนอ)", "เตรียมรายวัน; ทบทวนรายสัปดาห์", f"WAPE ≤ {pct(base_wape)}, ของเสีย, forecast bias, service level เมื่อมีข้อมูลของหมด"],
        ["ฟื้นผลดำเนินงานครัว", "เริ่มที่ Ladprao และ Sukhumvit: ดูคู่ครัว–สินค้าที่เงินเหลือติดลบหรือของเสียสูง ทบทวนราคา/โปรโมชันและขนาดรอบเตรียม", "ผู้จัดการครัว + Commercial (ข้อเสนอ)", "ประชุมติดตามรายสัปดาห์", "ผลดำเนินงาน, ต้นทุนของเสีย/รายได้, เงินเหลือต่อแก้ว"],
    ], columns=["ด้าน", "สิ่งที่ทำ", "ผู้รับผิดชอบที่เสนอ", "จังหวะทำงาน", "ตัวชี้วัด"])
    st.dataframe(actions, width="stretch", hide_index=True)

    st.markdown("#### มองไปข้างหน้า: ก.ย.–พ.ย. 2026")
    scenario_totals = data["scenario"].groupby("scenario_display", as_index=False).agg(
        forecast_units=("forecast_units", "sum"), modeled_operating_result_thb=("modeled_operating_result_thb", "sum")
    )
    scenario_order = ["Base case", "Optimized case", "Downside case"]
    scenario_totals["sort_order"] = scenario_totals["scenario_display"].map({name: index for index, name in enumerate(scenario_order)})
    scenario_totals = scenario_totals.sort_values("sort_order")
    scenario_columns = st.columns(3)
    for column, (_, row) in zip(scenario_columns, scenario_totals.iterrows()):
        thai_name = {"Base case": "กรณีฐาน", "Optimized case": "กรณีปรับปรุง", "Downside case": "กรณีแย่ลง"}[row["scenario_display"]]
        column.metric(thai_name, money(row["modeled_operating_result_thb"]), f"คาดขาย {row['forecast_units']:,.0f} แก้ว")
    optimized_result = float(scenario_totals.loc[scenario_totals["scenario_display"] == "Optimized case", "modeled_operating_result_thb"].iloc[0])
    base_result = float(scenario_totals.loc[scenario_totals["scenario_display"] == "Base case", "modeled_operating_result_thb"].iloc[0])
    st.markdown(
        f"<div class='callout'><strong>แผนไปสู่กำไรยังไม่จบในกรณีปรับปรุง:</strong> จากกรณีฐาน {money(base_result)} การใช้ราคาที่รับจริงแบบมาตรฐานและลดอัตราของเสีย 25% ช่วยลดการขาดทุน {money(optimized_result - base_result)} แต่ยังเหลือช่องว่าง {money(-optimized_result)} ก่อนคุ้มทุนใน 3 เดือน จึงต้องวัดผลจริงและประเมินต้นทุนคงที่ ต้นทุนจัดซื้อ และยอดขายที่สร้างเงินเหลือเป็นบวกเพิ่มเติม</div>",
        unsafe_allow_html=True,
    )

    with st.expander("หลักคิดและข้อจำกัดที่มีผลต่อการตัดสินใจ"):
        st.markdown("รายได้ใช้ราคาที่สังเกตได้หลังโปรโมชันแล้ว จึงไม่หักส่วนลดซ้ำ ผลดำเนินงานตามแบบจำลองหักต้นทุนผลไม้ บรรจุภัณฑ์ แรงงาน ค่าคอมมิชชัน ของเสียที่บันทึก และค่าใช้จ่ายคงที่ของครัว แต่ขอบเขตต้นทุนของ GP ในงบยังไม่ระบุ จึงไม่เรียกผลนี้ว่าเป็นส่วนต่าง GP เทียบงบ")
        st.markdown("ผลโปรโมชั่นเป็นความสัมพันธ์จากข้อมูล ไม่ใช่การพิสูจน์ว่าโปรโมชันทำให้ยอดเปลี่ยน ส่วนช่วง Forecast เป็นช่วงวางแผนจาก WAPE ไม่ใช่ช่วงความเชื่อมั่นทางสถิติ")

    with st.expander("ที่มาและสถานะการตรวจสอบ"):
        qa = data["qa"]
        st.success(f"ตรวจ artifact ที่ใช้คำนวณแล้ว: {qa['status']} · ผ่าน {len(qa['checks']) - qa['failed_count']}/{len(qa['checks'])} รายการ")
        st.write(f"ข้อมูลเวอร์ชัน: `{DATA_VERSION}`")
        st.write("เปิดแท็บ “ที่มาข้อมูลและข้อจำกัด” เพื่อดูการคัดกรองข้อมูล รายการประเด็น และ QA รายข้อ")


def demand_pricing(data: dict) -> None:
    task_heading("Task 2 · Demand & pricing", "ยอดขายและความเหมาะสมของราคา", "ลูกค้าซื้อเมื่อไร และราคาแต่ละสินค้ามีพื้นที่เหลือเหนือระดับคุ้มทุนก่อนของเสียมากน้อยแค่ไหน?")
    hourly = data["hourly"].copy()
    weekday = data["weekday"].copy()
    weekday["weekday"] = weekday["day_of_week"].map(WEEKDAY_NAMES_TH)
    monthly = data["monthly_demand"].copy()
    peak_hour = hourly.sort_values("units_sold", ascending=False).iloc[0]
    peak_day = weekday.sort_values("units_sold", ascending=False).iloc[0]
    top_platform = data["platform"].sort_values("gross_revenue_thb", ascending=False).iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("ช่วงยอดขายรวมสูงสุด", f"{int(peak_hour['hour']):02d}:00", f"{peak_hour['units_sold']:,.0f} แก้วตลอดช่วงย้อนหลัง")
    c2.metric("วันที่ยอดขายสูงสุด", str(peak_day["weekday"]), f"{peak_day['units_sold']:,.0f} แก้วตลอดช่วงย้อนหลัง")
    c3.metric("แพลตฟอร์มรายได้สูงสุด", str(top_platform["platform_name"]), money(top_platform["gross_revenue_thb"]))
    st.caption("ยอดตามชั่วโมงและวันด้านบนเป็นผลรวม 12 เดือน ไม่ใช่ยอดขายของวันเดียว")

    st.markdown("#### ลูกค้าซื้อเมื่อไร?")
    left, right = st.columns(2)
    left.markdown("**ยอดขายรวมตามชั่วโมง**")
    left.bar_chart(hourly.set_index("hour")[["units_sold"]].rename(columns={"units_sold": "แก้ว"}), height=270)
    right.markdown("**ยอดขายรวมตามวันในสัปดาห์**")
    right.bar_chart(weekday.set_index("weekday")[["units_sold"]].rename(columns={"units_sold": "แก้ว"}), height=270)
    left, right = st.columns(2)
    left.markdown("**ยอดขายรวมรายเดือน**")
    monthly_cups = monthly.set_index("month")[["units_sold"]].rename(columns={"units_sold": "แก้ว"})
    left.line_chart(monthly_cups, height=260)
    right.markdown("**รายได้รวมรายเดือน**")
    right.line_chart(monthly.set_index("month")[["gross_revenue_thb"]].rename(columns={"gross_revenue_thb": "บาท"}), height=260)
    st.info("การเตรียมสินค้าควรเพิ่มก่อนช่วงค่ำ โดยเฉพาะ 22:00 และวันเสาร์–อาทิตย์ แต่ไม่ควรตีความว่าแถวชั่วโมงที่ไม่พบใน export เป็นยอดขายศูนย์")

    with st.expander("ดู Demand แบบเทียบต่อวันและรายละเอียดช่วงเวลา"):
        normalized_hour = data["hourly_normalized"].copy().set_index("hour")
        normalized_day = data["weekday_normalized"].copy()
        normalized_day["weekday"] = normalized_day["day_of_week"].map(WEEKDAY_NAMES_TH)
        normalized_day = normalized_day.set_index("weekday")
        left, right = st.columns(2)
        left.markdown("**เฉลี่ยต่อวันที่มีข้อมูลตามชั่วโมง**")
        left.bar_chart(normalized_hour[["avg_cups_per_active_day"]].rename(columns={"avg_cups_per_active_day": "แก้วเฉลี่ย"}), height=260)
        right.markdown("**เฉลี่ยต่อวันที่มีข้อมูลตามวันในสัปดาห์**")
        right.bar_chart(normalized_day[["avg_cups_per_active_day"]].rename(columns={"avg_cups_per_active_day": "แก้วเฉลี่ย"}), height=260)
        daypart = data["daypart"].sort_values("daypart_order").set_index("daypart")
        st.markdown("**เฉลี่ยต่อชั่วโมงที่สังเกตตามช่วงเวลา**")
        st.bar_chart(daypart[["avg_cups_per_observed_hour"]].rename(columns={"avg_cups_per_observed_hour": "แก้วเฉลี่ย"}), height=240)
        st.markdown("**แผนภาพความต้องการ: วัน × ชั่วโมง และครัว × สินค้า**")
        day_names = list(WEEKDAY_NAMES_TH.values())
        heat = data["heatmap"].copy()
        heat["weekday"] = heat["day_of_week"].map(WEEKDAY_NAMES_TH)
        heat_table = heat.pivot(index="weekday", columns="hour", values="avg_cups_per_active_day").reindex(day_names).round(1)
        st.dataframe(heat_table.style.background_gradient(cmap="YlOrRd").format("{:.1f} แก้ว"), width="stretch")
        kitchen_heat = data["kitchen_sku"].pivot(index="kitchen", columns="sku", values="avg_cups_per_active_day").round(1)
        st.dataframe(kitchen_heat.style.background_gradient(cmap="YlGnBu").format("{:.1f} แก้ว"), width="stretch")

    st.markdown("#### ราคาปัจจุบันของแต่ละสินค้า")
    st.write("ตารางนี้เทียบราคาที่ลูกค้าจ่ายจริงกับระดับคุ้มทุน **ก่อนของเสียและค่าใช้จ่ายคงที่** จึงใช้เพื่อคัดกรองความเหมาะสมของราคา ไม่ใช่ราคาคุ้มทุนของทั้งธุรกิจ")
    price_summary = data["price_floor"].merge(
        data["portfolio"][["sku", "contribution_after_waste_per_cup_thb", "waste_rate", "action_note"]], on="sku", how="left"
    )
    price_summary["headroom_before_waste_thb"] = price_summary["realized_price_thb"] - price_summary["break_even_price_before_waste_thb"]
    price_actions = {
        "Watermelon": "คงราคา; ทดสอบ +5% ช่วงยอดสูงและปกป้องสินค้าพร้อมขาย",
        "Pineapple": "คงราคา; ทดสอบ +5% ช่วงยอดสูงและปกป้องสินค้าพร้อมขาย",
        "Guava": "คงราคา; ทดลอง +5% เฉพาะช่วงยอดสูงพร้อมกลุ่มควบคุม",
        "PassionFruit": "คงราคา; ทบทวนการกระจายและของเสียก่อนทดสอบราคา",
        "MixedBerryPremium": "ทดลอง +5% พร้อมคุมปริมาณและการเตรียมเป็นรอบเล็ก",
    }
    price_summary["recommendation"] = price_summary["sku"].map(price_actions)
    display_table(
        price_summary.sort_values("contribution_after_waste_per_cup_thb", ascending=False),
        ["sku", "realized_price_thb", "break_even_price_before_waste_thb", "headroom_before_waste_thb", "contribution_before_waste_per_cup_thb", "contribution_after_waste_per_cup_thb", "waste_rate", "recommendation"],
        {"sku": "สินค้า", "realized_price_thb": "ราคาที่รับจริง/แก้ว", "break_even_price_before_waste_thb": "คุ้มทุนก่อนของเสีย/แก้ว", "headroom_before_waste_thb": "ส่วนต่างเหนือคุ้มทุน", "contribution_before_waste_per_cup_thb": "เงินเหลือก่อนของเสีย/แก้ว", "contribution_after_waste_per_cup_thb": "เงินเหลือหลังของเสีย/แก้ว", "waste_rate": "อัตราของเสีย", "recommendation": "ข้อเสนอทดสอบ"},
        money_columns=("realized_price_thb", "break_even_price_before_waste_thb", "headroom_before_waste_thb", "contribution_before_waste_per_cup_thb", "contribution_after_waste_per_cup_thb"),
        percent_columns=("waste_rate",),
    )
    st.caption("ข้อเสนอราคาเป็นการทดสอบแบบมีกลุ่มควบคุม ไม่ใช่คำสั่งปรับราคาทันที เพราะการเปลี่ยนราคาที่สังเกตได้ส่วนใหญ่มาจาก rate code และปัจจัยอื่นร่วมกัน")

    st.markdown("#### ดูรายละเอียดราคาสินค้ารายตัว")
    sku_options = data["sku"]["sku"].tolist()
    selected_sku = st.selectbox("เลือกสินค้า", sku_options, index=sku_options.index("MixedBerryPremium") if "MixedBerryPremium" in sku_options else 0)
    sku_row = data["sku"].loc[data["sku"]["sku"] == selected_sku].iloc[0]
    price_row = data["price_floor"].loc[data["price_floor"]["sku"] == selected_sku].iloc[0]
    price_headroom = sku_row["realized_price_thb"] - price_row["break_even_price_before_waste_thb"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ยอดขายย้อนหลัง", f"{sku_row['units_sold']:,.0f} แก้ว")
    c2.metric("ราคาที่รับจริง", money(sku_row["realized_price_thb"], 2))
    c3.metric("ส่วนต่างเหนือคุ้มทุนก่อนของเสีย", money(price_headroom, 2))
    c4.metric("เงินเหลือหลังของเสียต่อแก้ว", money(sku_row["contribution_after_waste_per_cup_thb"], 2))

    left, right = st.columns(2)
    ladder = data["price_ladder"].loc[data["price_ladder"]["sku"] == selected_sku].sort_values("observed_price_thb")
    with left:
        st.markdown("**ราคาเทียบยอดขายต่อชั่วโมงที่มีข้อมูล**")
        st.line_chart(ladder.set_index("observed_price_thb")[["avg_cups_per_active_hour"]].rename(columns={"avg_cups_per_active_hour": "แก้วต่อชั่วโมง"}), height=250)
    with right:
        st.markdown("**สถานการณ์เงินเหลือหลังของเสีย**")
        simulation = data["price_simulation"].loc[data["price_simulation"]["sku"] == selected_sku].sort_values("price_change_pct").copy()
        simulation["price_change_label"] = simulation["price_change_pct"].map(lambda value: pct(value, 0))
        st.line_chart(simulation.set_index("price_change_label")[["projected_contribution_after_waste_thb"]].rename(columns={"projected_contribution_after_waste_thb": "บาท"}), height=250)
    with st.expander("หลักฐานราคาและข้อจำกัดเชิงสถิติ"):
        display_table(
            ladder,
            ["observed_price_thb", "units_sold", "active_hours", "avg_cups_per_active_hour", "contribution_per_cup_thb", "promo_families"],
            {"observed_price_thb": "ราคาที่พบ", "units_sold": "ยอดขาย", "active_hours": "ชั่วโมงที่มีข้อมูล", "avg_cups_per_active_hour": "แก้ว/ชั่วโมง", "contribution_per_cup_thb": "เงินเหลือ/แก้ว", "promo_families": "กลุ่ม rate code"},
            money_columns=("observed_price_thb", "contribution_per_cup_thb"), integer_columns=("units_sold", "active_hours"), decimal_columns=("avg_cups_per_active_hour",),
        )
        sensitivity = data["price_sensitivity"].copy()
        display_table(
            sensitivity,
            ["sku", "price_points", "min_observed_price_thb", "max_observed_price_thb", "price_cv", "pairwise_midpoint_elasticity_median", "pairwise_comparisons", "interpretation"],
            {"sku": "สินค้า", "price_points": "ระดับราคาที่พบ", "min_observed_price_thb": "ราคาต่ำสุด", "max_observed_price_thb": "ราคาสูงสุด", "price_cv": "ความผันผวนราคา", "pairwise_midpoint_elasticity_median": "ความไวต่อราคา (เชิงทิศทาง)", "pairwise_comparisons": "คู่เปรียบเทียบ", "interpretation": "ข้อจำกัด"},
            money_columns=("min_observed_price_thb", "max_observed_price_thb"), percent_columns=("price_cv",), integer_columns=("price_points", "pairwise_comparisons"), decimal_columns=("pairwise_midpoint_elasticity_median",),
        )
        display_table(
            simulation,
            ["price_change_pct", "projected_price_thb", "demand_factor", "projected_units", "projected_contribution_after_waste_thb", "delta_contribution_vs_current_thb", "assumption_source"],
            {"price_change_pct": "การเปลี่ยนราคา", "projected_price_thb": "ราคาสมมติ", "demand_factor": "ตัวคูณ Demand", "projected_units": "ยอดขายสมมติ", "projected_contribution_after_waste_thb": "เงินเหลือหลังของเสีย", "delta_contribution_vs_current_thb": "ต่างจากปัจจุบัน", "assumption_source": "ที่มาสมมติฐาน"},
            money_columns=("projected_price_thb", "projected_contribution_after_waste_thb", "delta_contribution_vs_current_thb"), percent_columns=("price_change_pct",), integer_columns=("projected_units",), decimal_columns=("demand_factor",),
        )
        best = data["price_simulation_best"].loc[data["price_simulation_best"]["sku"] == selected_sku]
        if not best.empty:
            best_row = best.iloc[0]
            st.info(f"แบบจำลองเชิงตัวอย่างให้ผลเงินเหลือสูงสุดที่ราคาเปลี่ยน {pct(best_row['price_change_pct'])} สำหรับ {selected_sku} แต่ใช้สมมติฐาน elasticity {best_row['elasticity_used']:.2f} จึงใช้เพื่อออกแบบการทดสอบ +5% ช่วงยอดสูงเท่านั้น ไม่ใช่หลักฐานว่าควรปรับราคาไปที่ค่านั้น")


def promotions(data: dict) -> None:
    task_heading("Task 3 · Promotions & rate codes", "โปรโมชันคุ้มไหม?", "ดูเงินเหลือต่อแก้วและผลเทียบกลุ่มราคาแบบมาตรฐานก่อนตัดสินใจเพิ่มยอดขายด้วยส่วนลด")
    metrics = data["promotion_depth_metrics"]
    scorecard = data["promo_scorecard"].copy().sort_values("base_code")
    matched = data["promo_matched_scorecard"].copy().sort_values("base_code")
    decision_map = {"CONTROL / DEFAULT": "ใช้เป็นกลุ่มเปรียบเทียบ", "OPTIMIZE / TARGET ONLY": "จำกัดและทดสอบเฉพาะกลุ่ม"}
    scorecard["thai_decision"] = scorecard["decision"].map(decision_map).fillna(scorecard["decision"])
    matched["thai_decision"] = matched["decision"].map(decision_map).fillna(matched["decision"])

    st.caption("รายได้เป็นราคาที่ลูกค้าจ่ายหลังโปรโมชันแล้ว ต้นทุนส่วนลดจึงแสดงเพื่อวิเคราะห์ผลกระทบ แต่ไม่นำไปหักจากรายได้ซ้ำ")
    st.markdown("#### สรุปการตัดสินใจต่อรหัสที่ใช้อยู่")
    promo_actions = pd.DataFrame([
        ["RC000 · Standard", "คงไว้", "เป็นฐานเปรียบเทียบ: เหลือ 14.48 บาท/แก้วก่อนของเสีย"],
        ["RC101 · Bundle Deal", "จำกัด", "ยอดเพิ่มที่เห็นยังต่ำกว่าระดับที่ต้องเพิ่มเพื่อคุ้มส่วนลด"],
        ["RC102 · Double Day New User", "ออกแบบใหม่และทดสอบ", "เหลือ 6.90 บาท/แก้วก่อนของเสีย และยอดเพิ่มที่เห็นยังไม่ถึงจุดคุ้ม"],
        ["RC103 · Seasonal Push", "จำกัด", "ยอดเพิ่มที่เห็นยังต่ำกว่าระดับที่ต้องเพิ่มเพื่อคุ้มส่วนลด"],
    ], columns=["รหัสและชื่อ", "ข้อเสนอ", "เหตุผล"])
    st.dataframe(promo_actions, width="stretch", hide_index=True)

    st.markdown("#### Scorecard: ลดราคาแล้วเหลือเงินเท่าไร?")
    display_table(
        scorecard,
        ["base_code", "rate_code_name", "discount_pct", "units_sold", "cups_per_active_hour", "discount_cost_thb", "net_revenue_thb", "contribution_before_waste_per_cup_thb", "contribution_margin_pct", "thai_decision"],
        {"base_code": "รหัส", "rate_code_name": "ชื่อ", "discount_pct": "ส่วนลด", "units_sold": "ยอดขาย", "cups_per_active_hour": "แก้ว/ชั่วโมง", "discount_cost_thb": "ต้นทุนส่วนลด", "net_revenue_thb": "รายได้หลังส่วนลด", "contribution_before_waste_per_cup_thb": "เงินเหลือก่อนของเสีย/แก้ว", "contribution_margin_pct": "สัดส่วนเงินเหลือ", "thai_decision": "ข้อเสนอ"},
        money_columns=("discount_cost_thb", "net_revenue_thb", "contribution_before_waste_per_cup_thb"), percent_columns=("discount_pct", "contribution_margin_pct"), integer_columns=("units_sold",), decimal_columns=("cups_per_active_hour",),
    )
    left, right = st.columns(2)
    left.markdown("**เงินเหลือก่อนของเสียต่อแก้ว**")
    left.bar_chart(scorecard.set_index("base_code")[["contribution_before_waste_per_cup_thb"]].rename(columns={"contribution_before_waste_per_cup_thb": "บาท/แก้ว"}), height=260)
    right.markdown("**ต้นทุนส่วนลดรวม**")
    right.bar_chart(scorecard.set_index("base_code")[["discount_cost_thb"]].rename(columns={"discount_cost_thb": "บาท"}), height=260)

    st.markdown("#### ยอดขายเพิ่มพอคุ้มส่วนลดหรือไม่?")
    if not matched.empty:
        lift = matched.copy()
        display_table(
            lift,
            ["base_code", "rate_code_name", "discount_pct", "promo_cups_per_active_hour", "baseline_cups_per_active_hour", "actual_demand_lift_pct", "break_even_lift_pct", "actual_vs_breakeven_gap_pct", "incremental_contribution_thb", "thai_decision"],
            {"base_code": "รหัส", "rate_code_name": "ชื่อ", "discount_pct": "ส่วนลด", "promo_cups_per_active_hour": "แก้ว/ชม. เมื่อมีโปร", "baseline_cups_per_active_hour": "แก้ว/ชม. ฐานปกติ", "actual_demand_lift_pct": "ยอดเพิ่มที่พบ", "break_even_lift_pct": "ยอดเพิ่มที่ต้องมีเพื่อคุ้ม", "actual_vs_breakeven_gap_pct": "ส่วนต่างจากจุดคุ้ม", "incremental_contribution_thb": "เงินเหลือเพิ่มเทียบฐาน", "thai_decision": "ข้อเสนอ"},
            money_columns=("incremental_contribution_thb",), percent_columns=("discount_pct", "actual_demand_lift_pct", "break_even_lift_pct", "actual_vs_breakeven_gap_pct"), decimal_columns=("promo_cups_per_active_hour", "baseline_cups_per_active_hour"),
        )
        lift_chart = lift.set_index("base_code")[["actual_demand_lift_pct", "break_even_lift_pct"]].mul(100)
        lift_chart.columns = ["ยอดเพิ่มที่พบ (%)", "ยอดเพิ่มที่ต้องมีเพื่อคุ้ม (%)"]
        st.bar_chart(lift_chart, height=280)
        st.caption(f"เทียบในกลุ่ม SKU × ครัว × แพลตฟอร์ม × วัน × เดือน × ชั่วโมง × ช่วงเวลาเดียวกัน {int(metrics['matched_strata_count']):,} แถว โดยแถวชั่วโมงที่ไม่พบใน export ไม่ได้ถูกนับเป็นศูนย์")

    code_options = scorecard["base_code"].tolist()
    selected_code = st.selectbox("ดูรายละเอียดรหัสโปรโมชั่น", code_options, index=code_options.index("RC102") if "RC102" in code_options else 0)
    selected = scorecard.set_index("base_code").loc[selected_code]
    selected_match = matched.loc[matched["base_code"] == selected_code]
    p1, p2, p3, p4, p5 = st.columns(5)
    p1.metric("ส่วนลด", pct(selected["discount_pct"]))
    p2.metric("สัดส่วนยอดขายทั้งหมด", pct(selected["promo_share_cups"]))
    p3.metric("ต้นทุนส่วนลด", money(selected["discount_cost_thb"]))
    p4.metric("เงินเหลือก่อนของเสีย/แก้ว", money(selected["contribution_before_waste_per_cup_thb"], 2))
    p5.metric("ยอดขายต่อชั่วโมง", f"{selected['cups_per_active_hour']:,.1f} แก้ว")
    if not selected_match.empty:
        row = selected_match.iloc[0]
        st.warning(f"{selected_code}: ยอดขายเพิ่มที่เห็น {pct(row['actual_demand_lift_pct'])} แต่ต้องเพิ่ม {pct(row['break_even_lift_pct'])} จึงคุ้มส่วนลด และเงินเหลือเพิ่มเทียบฐานเป็น {money(row['incremental_contribution_thb'])} จึงยังไม่ควรขยายแบบหว่าน")

    with st.expander("รายละเอียดสำหรับออกแบบการทดสอบโปรโมชัน"):
        st.markdown("**ประสิทธิภาพและการพึ่งพาโปรโมชัน**")
        efficiency = data["promo_efficiency"].copy()
        matrix = efficiency.set_index("base_code")[["actual_demand_lift_pct", "contribution_lift_pct"]].mul(100)
        matrix.columns = ["ยอดขายเพิ่ม (%)", "เงินเหลือเพิ่ม (%)"]
        st.bar_chart(matrix, height=260)
        display_table(
            efficiency,
            ["base_code", "actual_demand_lift_pct", "break_even_lift_pct", "contribution_lift_pct", "incremental_contribution_thb", "promo_discount_cost_thb", "promo_roi_on_discount", "decision"],
            {"base_code": "รหัส", "actual_demand_lift_pct": "ยอดเพิ่มที่พบ", "break_even_lift_pct": "ยอดเพิ่มเพื่อคุ้ม", "contribution_lift_pct": "เงินเหลือเพิ่ม", "incremental_contribution_thb": "เงินเหลือเพิ่มเทียบฐาน", "promo_discount_cost_thb": "ต้นทุนส่วนลด", "promo_roi_on_discount": "ROI ส่วนลด", "decision": "ผลคัดกรอง"},
            money_columns=("incremental_contribution_thb", "promo_discount_cost_thb"), percent_columns=("actual_demand_lift_pct", "break_even_lift_pct", "contribution_lift_pct", "promo_roi_on_discount"),
        )
        dependency = data["promo_dependency"].copy()
        st.markdown("**สัดส่วนยอดขายที่มาจากโปรโมชันตามสินค้า**")
        st.bar_chart(dependency.set_index("sku")[["promo_share_cups"]].mul(100).rename(columns={"promo_share_cups": "% ของยอดขาย"}), height=240)
        display_table(
            dependency, list(dependency.columns),
            {"sku": "สินค้า", "promo_units": "ยอดขายจากโปร", "total_units": "ยอดขายรวม", "promo_share_cups": "สัดส่วนจากโปร"},
            integer_columns=("promo_units", "total_units"), percent_columns=("promo_share_cups",),
        )

        st.markdown("**ค้นหากลุ่มที่ควรหยุดหรือทดสอบต่อ**")
        segment_view = st.selectbox("แยกกลุ่มตาม", ["สินค้า", "ครัว", "แพลตฟอร์ม", "ชั่วโมง", "ช่วงเวลา"])
        segment_specs = {
            "สินค้า": ("promo_by_sku", "sku"), "ครัว": ("promo_by_kitchen", "kitchen"),
            "แพลตฟอร์ม": ("promo_by_platform", "platform_name"), "ชั่วโมง": ("promo_by_hour", "hour"), "ช่วงเวลา": ("promo_by_daypart", "daypart"),
        }
        key, label_col = segment_specs[segment_view]
        segment = data[key].copy()
        view_columns = [label_col, "base_code", "matched_strata", "promo_units", "baseline_units", "promo_cups_per_active_hour", "baseline_cups_per_active_hour", "actual_demand_lift_pct", "break_even_lift_pct", "contribution_lift_pct", "incremental_contribution_thb", "decision"]
        display_table(
            segment.sort_values("incremental_contribution_thb"), view_columns,
            {label_col: segment_view, "base_code": "รหัส", "matched_strata": "กลุ่มเทียบ", "promo_units": "ยอดขายเมื่อมีโปร", "baseline_units": "ยอดขายฐาน", "promo_cups_per_active_hour": "แก้ว/ชม. เมื่อมีโปร", "baseline_cups_per_active_hour": "แก้ว/ชม. ฐาน", "actual_demand_lift_pct": "ยอดเพิ่มที่พบ", "break_even_lift_pct": "ยอดเพิ่มเพื่อคุ้ม", "contribution_lift_pct": "เงินเหลือเพิ่ม", "incremental_contribution_thb": "เงินเหลือเพิ่มเทียบฐาน", "decision": "ผลคัดกรอง"},
            money_columns=("incremental_contribution_thb",), percent_columns=("actual_demand_lift_pct", "break_even_lift_pct", "contribution_lift_pct"), integer_columns=("matched_strata", "promo_units", "baseline_units"), decimal_columns=("promo_cups_per_active_hour", "baseline_cups_per_active_hour"),
            height=360,
        )

        st.markdown("**เกณฑ์ส่วนลดสูงสุดที่ต้องแลกด้วยยอดขายเพิ่ม**")
        depth = data["promo_depth"].copy()
        depth_sku_options = depth["sku"].drop_duplicates().tolist()
        depth_sku = st.selectbox("เลือกสินค้าสำหรับดูระดับส่วนลด", depth_sku_options, index=depth_sku_options.index("MixedBerryPremium") if "MixedBerryPremium" in depth_sku_options else 0)
        depth_view = depth.loc[depth["sku"] == depth_sku].sort_values("discount_pct").copy()
        depth_chart = depth_view.set_index("discount_pct")[["required_demand_lift_pct"]].mul(100)
        depth_chart.columns = ["ยอดขายเพิ่มที่ต้องมีเพื่อคงสัดส่วนเงินเหลือ (%)"]
        st.line_chart(depth_chart, height=260)
        display_table(
            depth_view,
            ["discount_pct", "effective_price_thb", "promo_contribution_per_cup_thb", "contribution_delta_per_cup_thb", "required_demand_lift_pct"],
            {"discount_pct": "ส่วนลด", "effective_price_thb": "ราคาหลังลด", "promo_contribution_per_cup_thb": "เงินเหลือเมื่อมีโปร/แก้ว", "contribution_delta_per_cup_thb": "เงินเหลือที่ลดลง/แก้ว", "required_demand_lift_pct": "ยอดขายเพิ่มเพื่อคงเงินเหลือ"},
            money_columns=("effective_price_thb", "promo_contribution_per_cup_thb", "contribution_delta_per_cup_thb"), percent_columns=("discount_pct", "required_demand_lift_pct"),
        )

    st.markdown("#### กติกาก่อนขยายโปรโมชัน")
    st.write("ขยายส่วนลดเมื่อเงินเหลือเพิ่มเทียบกลุ่มควบคุมเป็นบวก และยอดขายเพิ่มจริงมากกว่าระดับที่ต้องมีเพื่อชดเชยส่วนลดเท่านั้น เริ่มจากกลุ่มสินค้า–ครัว–แพลตฟอร์ม–ช่วงเวลาที่ผ่านเกณฑ์ แล้วติดตามของเสียร่วมด้วย")
    st.warning("ผลการเทียบเป็นความสัมพันธ์ในข้อมูล ยังไม่ยืนยันผลเชิงเหตุและผล เพราะไม่มีการสุ่มกลุ่มลูกค้า ข้อมูลการแย่งยอดจากสินค้าอื่น และข้อมูลของหมด " + metrics["waste_boundary"])


def finance(data: dict) -> None:
    task_heading("Task 4 · Portfolio & budget performance", "สินค้า สาขา และผลเทียบงบ", "P&L นี้ประกอบจากต้นทุนผลไม้ บรรจุภัณฑ์ แรงงาน ค่าคอมมิชชัน ของเสีย และค่าใช้จ่ายคงที่ เพื่อหาว่าส่วนใดควรแก้ก่อน")
    totals = data["finance_metrics"]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("รายได้จากการขาย", money(totals["historical_revenue_thb"]))
    c2.metric("ต่างจากเป้ารายได้", money(totals["total_revenue_variance_thb"]))
    c3.metric("เงินเหลือก่อนของเสีย", money(totals["historical_contribution_before_waste_thb"]), pct(totals["historical_contribution_margin_pct"]))
    c4.metric("ต้นทุนของเสีย", money(totals["historical_waste_cost_thb"]))
    c5.metric("ผลดำเนินงานตามแบบจำลอง", money(totals["historical_modeled_operating_result_thb"]), pct(totals["historical_operating_margin_pct"]))

    company = data["pnl_company"]
    st.markdown("#### จากรายได้สู่ผลดำเนินงาน")
    st.info("รายได้คือราคาที่ลูกค้าจ่ายหลังโปรโมชัน เงินเหลือก่อนของเสีย = รายได้ − ต้นทุนผลไม้ − บรรจุภัณฑ์ − แรงงาน − ค่าคอมมิชชัน ผลดำเนินงานตามแบบจำลอง = เงินเหลือก่อนของเสีย − ของเสียที่บันทึก − ค่าใช้จ่ายคงที่ครัว")
    waterfall = data["pnl_waterfall"]
    waterfall_chart = waterfall.set_index("pnl_component")[["thb"]].copy()
    waterfall_chart.index = ["รายได้", "ต้นทุนผลไม้", "บรรจุภัณฑ์", "แรงงาน", "ค่าคอมมิชชัน", "เงินเหลือก่อนของเสีย", "ต้นทุนของเสีย", "เงินเหลือหลังของเสีย", "ค่าใช้จ่ายคงที่", "ผลดำเนินงาน"]
    st.bar_chart(waterfall_chart.rename(columns={"thb": "บาท"}), height=320)
    display_table(
        waterfall,
        ["pnl_component", "thb", "definition"],
        {"pnl_component": "รายการ", "thb": "จำนวนเงิน", "definition": "คำอธิบายที่มา"},
        money_columns=("thb",),
    )

    st.markdown("#### รายได้จริงเทียบงบรายเดือน")
    st.caption("ข้อมูล budget ไม่ได้นิยามว่า GP รวมค่าคอมมิชชัน ของเสีย แรงงาน หรือค่าใช้จ่ายคงที่หรือไม่ จึงเทียบเป้ารายได้ได้โดยตรง ส่วนชั้น GP แสดงเพื่อวิเคราะห์เท่านั้น")
    pnl = company.copy().set_index("month")
    chart = pnl[["gross_revenue_thb", "budget_revenue_thb"]].rename(columns={"gross_revenue_thb": "รายได้จริง", "budget_revenue_thb": "เป้ารายได้"})
    st.line_chart(chart, height=320)
    monthly_cols = ["month", "gross_revenue_thb", "budget_revenue_thb", "revenue_variance_thb", "revenue_variance_pct", "budget_gross_profit_thb", "product_margin_thb", "contribution_before_waste_thb", "contribution_after_waste_thb", "modeled_operating_result_thb", "budget_gp_boundary_status"]
    display_table(
        company, monthly_cols,
        {"month": "เดือน", "gross_revenue_thb": "รายได้จริง", "budget_revenue_thb": "เป้ารายได้", "revenue_variance_thb": "ต่างจากเป้า", "revenue_variance_pct": "ต่างจากเป้า (%)", "budget_gross_profit_thb": "เป้า GP (ขอบเขตยังเปิด)", "product_margin_thb": "ส่วนต่างราคากับต้นทุนสินค้า", "contribution_before_waste_thb": "เงินเหลือก่อนของเสีย", "contribution_after_waste_thb": "เงินเหลือหลังของเสีย", "modeled_operating_result_thb": "ผลดำเนินงานตามแบบจำลอง", "budget_gp_boundary_status": "สถานะเทียบ GP"},
        money_columns=("gross_revenue_thb", "budget_revenue_thb", "revenue_variance_thb", "budget_gross_profit_thb", "product_margin_thb", "contribution_before_waste_thb", "contribution_after_waste_thb", "modeled_operating_result_thb"), percent_columns=("revenue_variance_pct",), date_columns=("month",),
        height=370,
    )

    st.markdown("#### สินค้าไหนควรทำอะไร?")
    portfolio = data["portfolio"].copy()
    sku_action_map = {
        "Watermelon": "รักษาความพร้อมขาย; ทดสอบราคาเฉพาะช่วงยอดสูง", "Pineapple": "รักษาความพร้อมขาย; ทดสอบราคาเฉพาะช่วงยอดสูง",
        "Guava": "รักษาความพร้อมขาย; ทดสอบราคาแบบควบคุม", "PassionFruit": "ทบทวนการกระจาย ของเสีย และบทบาทสินค้า",
        "MixedBerryPremium": "แก้ราคา ปริมาณ และการเตรียมก่อนขยาย",
    }
    portfolio["thai_action"] = portfolio["sku"].map(sku_action_map)
    left, right = st.columns(2)
    with left:
        st.bar_chart(portfolio.set_index("sku")[["contribution_after_waste_thb"]].rename(columns={"contribution_after_waste_thb": "เงินเหลือหลังของเสีย (บาท)"}), height=280)
    with right:
        st.scatter_chart(portfolio, x="units_sold", y="contribution_after_waste_margin_pct", size="gross_revenue_thb", color="sku", x_label="ยอดขาย (แก้ว)", y_label="สัดส่วนเงินเหลือหลังของเสีย", height=280)
    display_table(
        portfolio.sort_values("contribution_after_waste_thb", ascending=False),
        ["sku", "units_sold", "gross_revenue_thb", "revenue_share", "contribution_after_waste_thb", "contribution_after_waste_per_cup_thb", "contribution_after_waste_margin_pct", "waste_cost_thb", "waste_rate", "thai_action"],
        {"sku": "สินค้า", "units_sold": "ยอดขาย", "gross_revenue_thb": "รายได้", "revenue_share": "สัดส่วนรายได้", "contribution_after_waste_thb": "เงินเหลือหลังของเสีย", "contribution_after_waste_per_cup_thb": "เงินเหลือ/แก้ว", "contribution_after_waste_margin_pct": "สัดส่วนเงินเหลือ", "waste_cost_thb": "ต้นทุนของเสีย", "waste_rate": "อัตราของเสีย", "thai_action": "สิ่งที่ควรทำ"},
        money_columns=("gross_revenue_thb", "contribution_after_waste_thb", "contribution_after_waste_per_cup_thb", "waste_cost_thb"), percent_columns=("revenue_share", "contribution_after_waste_margin_pct", "waste_rate"), integer_columns=("units_sold",),
    )
    st.caption("เงินเหลือระดับสินค้าเป็นเงินเหลือหลังของเสียก่อนจัดสรรค่าใช้จ่ายคงที่ของครัว จึงไม่ใช่กำไรสุทธิของสินค้า")

    st.markdown("#### ครัวไหนควรเริ่มแก้ก่อน?")
    kitchen_rollup = data["finance_kitchen"].copy()
    kitchen_action_map = {"BKK_Ladprao": "ต้องแก้ก่อน: ผลติดลบและของเสียสูงสุด", "BKK_Sukhumvit": "ต้องแก้ลำดับสอง: ผลติดลบ", "Pattaya_Beach": "รักษาผลบวกและคุมของเสีย", "Pattaya_Central": "รักษาผลบวกและคุมของเสีย"}
    kitchen_rollup["thai_action"] = kitchen_rollup["kitchen"].map(kitchen_action_map)
    left, right = st.columns(2)
    left.markdown("**ผลดำเนินงานตามแบบจำลองรายครัว**")
    left.bar_chart(kitchen_rollup.set_index("kitchen")[["modeled_operating_result_thb"]].rename(columns={"modeled_operating_result_thb": "บาท"}), height=270)
    right.markdown("**ต้นทุนของเสียตามครัว**")
    right.bar_chart(kitchen_rollup.set_index("kitchen")[["waste_cost_thb"]].rename(columns={"waste_cost_thb": "บาท"}), height=270)
    display_table(
        kitchen_rollup.sort_values("modeled_operating_result_thb"),
        ["kitchen", "units_sold", "gross_revenue_thb", "contribution_before_waste_thb", "waste_cost_thb", "waste_rate", "fixed_monthly_overhead_thb", "modeled_operating_result_thb", "operating_margin_pct", "thai_action"],
        {"kitchen": "ครัว", "units_sold": "ยอดขาย", "gross_revenue_thb": "รายได้", "contribution_before_waste_thb": "เงินเหลือก่อนของเสีย", "waste_cost_thb": "ต้นทุนของเสีย", "waste_rate": "อัตราของเสีย", "fixed_monthly_overhead_thb": "ค่าใช้จ่ายคงที่", "modeled_operating_result_thb": "ผลดำเนินงานตามแบบจำลอง", "operating_margin_pct": "สัดส่วนผลดำเนินงาน", "thai_action": "ลำดับทำงาน"},
        money_columns=("gross_revenue_thb", "contribution_before_waste_thb", "waste_cost_thb", "fixed_monthly_overhead_thb", "modeled_operating_result_thb"), percent_columns=("waste_rate", "operating_margin_pct"), integer_columns=("units_sold",),
    )
    kitchen_options = kitchen_rollup["kitchen"].tolist()
    selected_kitchen = st.selectbox("ดูแนวโน้มรายเดือนของครัว", kitchen_options, index=kitchen_options.index("BKK_Ladprao") if "BKK_Ladprao" in kitchen_options else 0)
    kitchen = data["pnl_kitchen"].loc[data["pnl_kitchen"]["kitchen"] == selected_kitchen].copy().set_index("month")
    st.line_chart(kitchen[["contribution_after_waste_thb", "modeled_operating_result_thb"]].rename(columns={"contribution_after_waste_thb": "เงินเหลือหลังของเสีย", "modeled_operating_result_thb": "ผลดำเนินงานตามแบบจำลอง"}), height=260)

    with st.expander("รายละเอียดต้นทุน ของเสีย และการวิเคราะห์ความไว"):
        st.markdown("**ที่มาของการเปลี่ยนรายได้เดือนต่อเดือน**")
        decomp = data["revenue_decomp"].dropna(subset=["prior_month"]).copy()
        if not decomp.empty:
            st.bar_chart(decomp.set_index("month")[["volume_effect_thb", "price_mix_effect_thb"]].rename(columns={"volume_effect_thb": "ผลจากปริมาณ", "price_mix_effect_thb": "ผลจากราคา/ส่วนผสม"}), height=250)
            display_table(
                decomp, ["month", "revenue_change_thb", "volume_effect_thb", "price_mix_effect_thb", "decomposition_check_thb", "basis"],
                {"month": "เดือน", "revenue_change_thb": "รายได้เปลี่ยน", "volume_effect_thb": "ผลจากปริมาณ", "price_mix_effect_thb": "ผลจากราคา/ส่วนผสม", "decomposition_check_thb": "ผลตรวจสอบ", "basis": "ขอบเขต"},
                money_columns=("revenue_change_thb", "volume_effect_thb", "price_mix_effect_thb", "decomposition_check_thb"), date_columns=("month",),
            )
        st.markdown("**ของเสียแยกครัว–สินค้า**")
        waste = data["waste_heatmap"].copy()
        waste_table = waste.pivot(index="kitchen", columns="sku", values="waste_rate").mul(100).round(1)
        st.dataframe(waste_table.style.background_gradient(cmap="YlOrRd").format("{:.1f}%"), width="stretch")
        display_table(
            waste.sort_values("waste_rate", ascending=False), ["kitchen", "sku", "units_sold", "units_wasted", "waste_rate", "waste_cost_thb", "waste_cost_pct_revenue"],
            {"kitchen": "ครัว", "sku": "สินค้า", "units_sold": "ยอดขาย", "units_wasted": "ของเสีย (แก้ว)", "waste_rate": "อัตราของเสีย", "waste_cost_thb": "ต้นทุนของเสีย", "waste_cost_pct_revenue": "ต้นทุนของเสีย/รายได้"},
            integer_columns=("units_sold", "units_wasted"), percent_columns=("waste_rate", "waste_cost_pct_revenue"), money_columns=("waste_cost_thb",),
        )
        st.markdown("**แนวโน้มต้นทุนผลไม้และการกระจายเงินเหลือ**")
        fruit_cost = data["fruit_cost_trend"].copy()
        st.line_chart(fruit_cost.pivot(index="week_start", columns="sku", values="fruit_cost_per_cup_thb"), height=270)
        pareto = data["sku_kitchen_pareto"].copy()
        display_table(
            pareto.head(12), ["kitchen", "sku", "units_sold", "gross_revenue_thb", "contribution_after_waste_thb", "contribution_mix", "cumulative_contribution_mix", "profit_rank"],
            {"kitchen": "ครัว", "sku": "สินค้า", "units_sold": "ยอดขาย", "gross_revenue_thb": "รายได้", "contribution_after_waste_thb": "เงินเหลือหลังของเสีย", "contribution_mix": "สัดส่วนเงินเหลือ", "cumulative_contribution_mix": "สัดส่วนสะสม", "profit_rank": "อันดับ"},
            integer_columns=("units_sold", "profit_rank"), money_columns=("gross_revenue_thb", "contribution_after_waste_thb"), percent_columns=("contribution_mix", "cumulative_contribution_mix"),
        )
        st.markdown("**โอกาสฟื้นผลดำเนินงานจากข้อมูลย้อนหลัง**")
        display_table(
            data["gap_closing"], ["gap_or_opportunity", "thb", "basis", "status"],
            {"gap_or_opportunity": "รายการ", "thb": "มูลค่า", "basis": "ฐานคิด", "status": "สถานะ"}, money_columns=("thb",),
        )
        display_table(
            data["finance_scenarios"], ["scenario", "modeled_operating_result_thb", "delta_vs_current_thb", "basis", "status"],
            {"scenario": "สถานการณ์", "modeled_operating_result_thb": "ผลดำเนินงานตามแบบจำลอง", "delta_vs_current_thb": "ต่างจากปัจจุบัน", "basis": "ฐานคิด", "status": "สถานะ"}, money_columns=("modeled_operating_result_thb", "delta_vs_current_thb"),
        )
        st.caption("Sensitivity นี้เป็นหลักฐานคัดกรองจากข้อมูลย้อนหลัง: ผลโปรโมชันเป็น association ก่อนของเสีย และ sensitivity ของเสียคงต้นทุนของเสียต่อแก้วไว้ จึงไม่ใช่ผลประหยัดที่รับประกัน หรือสะพานไปยัง GP budget โดยตรง")


def forecast_inventory(data: dict) -> None:
    task_heading("Task 5 · Inventory & 3-month outlook", "แผน 3 เดือนและการเตรียมสินค้า", "คาดการณ์ความต้องการระดับครัว–สินค้า แล้วแปลงเป็นแผนคุ้มทุนและเป้าเตรียมที่รวมของเสีย โดยยังไม่สร้างใบสั่งซื้อจากข้อมูลที่ไม่มี")
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
    c1.metric("Forecast เดิม (ฐาน)", f"{baseline_units:,.0f} แก้ว")
    c2.metric("ช่วงสำหรับวางแผน", f"{data['metrics']['base_forecast_lower_units']:,.0f}–{data['metrics']['base_forecast_upper_units']:,.0f} แก้ว")
    c3.metric("เป้าเตรียมจาก Forecast เดิม", f"{baseline_prep:,.0f} แก้ว")
    c4.metric("ของเสียที่คาด", f"{requirements['expected_waste_units_base'].sum():,.0f} แก้ว")
    c5.metric("ผล Forecast เดิม", money(base["modeled_operating_result_thb"].sum()))
    st.caption("ช่วงสำหรับวางแผนคำนวณจาก WAPE ของวิธีที่เลือก ไม่ใช่ช่วงความเชื่อมั่นทางสถิติ")
    st.info(
        f"หน้านี้มีตัวเลข 2 ชุด: Forecast เดิมคาดขาย {baseline_units:,.0f} แก้วและเตรียม {baseline_prep:,.0f} แก้ว "
        f"โดยยังไม่ใช้มาตรการ; ส่วนเป้าสมจริงเพื่อคุ้มทุนคาดขาย {target_units:,.0f} แก้วและเตรียม {target_prep:,.0f} แก้ว "
        f"เมื่อสมมติว่าราคา โปรโมชัน ของเสีย ต้นทุน และยอดขายเป้าทำได้ตามแผน โดยพฤศจิกายนเพิ่มจาก Forecast เดิมประมาณ {pct(nov_growth_pct)} "
        "จึงไม่ควรนำสองชุดไปเทียบว่าเป็น Forecast เดียวกัน"
    )

    st.markdown("#### เป้าสมจริงเพื่อคุ้มทุนสะสม")
    st.warning(
        f"นี่คือเป้าบริหารที่คำนวณย้อนจากจุดคุ้มทุน ไม่ใช่ Forecast ใหม่หรือการรับประกันกำไร: "
        f"ถ้าทำมาตรการครบ ผลตามแบบจำลองจะอยู่ที่ {money(recovery['proposed_target_result_thb'])} ใน 3 เดือน "
        f"แต่เดือนแรกยังขาดทุน และเดือน 3 ต้องเพิ่มยอดสุทธิของ Watermelon, Pineapple และ Guava "
        f"ประมาณ {pct(recovery['final_month_core_growth_needed_for_3m_breakeven'])} เพื่อให้คุ้มทุนสะสม"
    )
    nov_evidence = recovery["november_growth_evidence"]
    st.caption(
        f"แม้เป้า พ.ย. สูงกว่า Forecast พ.ย. {pct(nov_growth_pct)} แต่เส้นเป้าบริหารเพิ่มจาก ต.ค. → พ.ย. "
        f"{pct(nov_evidence['conditional_target_oct_to_nov_total_growth'])}; ใช้ยอดขายจริงยืนยันก่อนเพิ่มการเตรียมสินค้า"
    )

    st.markdown("#### ฐานรองรับและ Gate ของเป้า พ.ย.")
    st.info(
        f"ยอดจริงปี 2025 โต ต.ค. → พ.ย. {pct(nov_evidence['historical_oct_to_nov_total_growth'])} รวมทุกสินค้า "
        f"และ {pct(nov_evidence['historical_oct_to_nov_core_growth'])} สำหรับ Watermelon, Pineapple, Guava. "
        f"จึงรองรับได้เพียงสมมติฐานฤดูกาล—not a new forecast. {nov_evidence['limitation']}"
    )
    evidence_view = recovery_nov_evidence.copy()
    evidence_view["month_label"] = evidence_view["month"].map(lambda value: MONTH_NAMES_TH[int(value)])
    display_table(
        evidence_view,
        ["month_label", "historical_total_cups_2025", "historical_total_mom_growth", "historical_core_cups_2025", "historical_core_mom_growth", "conditional_target_total_cups_2026", "conditional_target_total_mom_growth", "conditional_target_core_cups_2026", "conditional_target_core_mom_growth"],
        {"month_label": "เดือน", "historical_total_cups_2025": "ยอดจริงรวม 2025", "historical_total_mom_growth": "ยอดจริงรวม MoM", "historical_core_cups_2025": "ยอดจริง Core 2025", "historical_core_mom_growth": "ยอดจริง Core MoM", "conditional_target_total_cups_2026": "เป้ารวมแบบมีเงื่อนไข 2026", "conditional_target_total_mom_growth": "เป้ารวม MoM", "conditional_target_core_cups_2026": "เป้า Core แบบมีเงื่อนไข 2026", "conditional_target_core_mom_growth": "เป้า Core MoM"},
        integer_columns=("historical_total_cups_2025", "historical_core_cups_2025", "conditional_target_total_cups_2026", "conditional_target_core_cups_2026"),
        percent_columns=("historical_total_mom_growth", "historical_core_mom_growth", "conditional_target_total_mom_growth", "conditional_target_core_mom_growth"),
    )
    st.write(
        "ก่อนปล่อยยอดเพิ่ม ต้องมีผลทดสอบ ต.ค. ที่วัด incremental core cups หลัง cannibalization และเงินเหลือหลัง commission/waste เป็นบวก; "
        "ยืนยันว่าค่าโฆษณา/กะเสริมยังอยู่ในงบ; และผ่าน capacity trial รายครัว. หากข้อใดไม่ผ่าน ให้ reforecast จาก actual และไม่ผลิตเพื่อไล่เป้ากำไร."
    )
    display_table(
        recovery_nov_capacity,
        ["kitchen", "net_extra_cups_per_day", "extra_core_cups_per_day"],
        {"kitchen": "ครัว", "net_extra_cups_per_day": "ยอดสุทธิเพิ่ม/วัน", "extra_core_cups_per_day": "Core cups เพิ่ม/วัน"},
        decimal_columns=("net_extra_cups_per_day", "extra_core_cups_per_day"),
    )
    st.caption(
        f"Capacity Gate รวม: ยอดสุทธิเพิ่ม {recovery['november_capacity_gate']['net_extra_cups_per_day']:,.1f} แก้ว/วัน, "
        f"แต่ต้องทำ Core เพิ่ม {recovery['november_capacity_gate']['extra_core_cups_per_day']:,.1f} แก้ว/วัน เพราะแผนพัก MixedBerry."
    )
    recovery_monthly["month"] = pd.to_datetime(recovery_monthly["month"])
    display_table(
        recovery_monthly,
        ["month", "planned_units", "planned_prep", "contribution_thb", "fixed_overhead_thb", "implementation_cost_thb", "operating_result_thb", "cumulative_result_thb"],
        {"month": "เดือน", "planned_units": "เป้าขาย", "planned_prep": "เป้าเตรียมเมื่อยอดถึงเป้า", "contribution_thb": "เงินเหลือหลังของเสีย", "fixed_overhead_thb": "ค่าใช้จ่ายคงที่ตามเป้า", "implementation_cost_thb": "งบดำเนินแผน", "operating_result_thb": "ผลดำเนินงาน", "cumulative_result_thb": "ผลสะสม"},
        date_columns=("month",), integer_columns=("planned_units", "planned_prep"), money_columns=("contribution_thb", "fixed_overhead_thb", "implementation_cost_thb", "operating_result_thb", "cumulative_result_thb"),
    )
    st.caption("เงื่อนไขหลักของเป้านี้คือ ลดของเสีย/ต้นทุนผลไม้/ค่าใช้จ่ายคงที่ และสร้างยอดสุทธิหลังการเปลี่ยนราคาและโปรโมชันตามแผน หากทำไม่ครบ ผลจะกลับไปติดลบ")

    st.markdown("#### ยอดขายย้อนหลังต่อด้วยยอดขายคาดการณ์")
    history_weekly = data["weekly_demand"].groupby("week_start", as_index=True)["units_sold"].sum().rename("Historical cups")
    future_weekly = data["forecast"].assign(week_start=lambda d: d["date"] - pd.to_timedelta(d["date"].dt.dayofweek, unit="D")).groupby("week_start", as_index=True).agg(
        base_forecast=("forecast_units_base", "sum"), lower=("forecast_lower_units", "sum"), upper=("forecast_upper_units", "sum")
    ).rename(columns={"base_forecast": "คาดการณ์กรณีฐาน", "lower": "ขอบล่างสำหรับวางแผน", "upper": "ขอบบนสำหรับวางแผน"})
    history_weekly = history_weekly.rename("ยอดขายย้อนหลัง")
    history_chart = pd.concat([history_weekly, future_weekly], axis=1)
    st.line_chart(history_chart, height=280)

    st.markdown("#### ผลดำเนินงานที่คาดใน 3 สถานการณ์")
    scenario_chart = scenario.pivot(index="month", columns="scenario_display", values="modeled_operating_result_thb")
    scenario_chart = scenario_chart.rename(columns={"Base case": "กรณีฐาน", "Downside case": "กรณีแย่ลง", "Optimized case": "กรณีปรับปรุง"})
    scenario_chart = scenario_chart.reindex(columns=["กรณีฐาน", "กรณีปรับปรุง", "กรณีแย่ลง"])
    st.line_chart(scenario_chart, height=280)
    scenario_total = scenario.groupby("scenario_display", as_index=False).agg(
        forecast_units=("forecast_units", "sum"), revenue_thb=("revenue_thb", "sum"), contribution_after_waste_thb=("contribution_after_waste_thb", "sum"), fixed_overhead_thb=("fixed_overhead_thb", "sum"), modeled_operating_result_thb=("modeled_operating_result_thb", "sum")
    )
    scenario_total["scenario_th"] = scenario_total["scenario_display"].map({"Base case": "กรณีฐาน", "Downside case": "กรณีแย่ลง", "Optimized case": "กรณีปรับปรุง"})
    scenario_total["sort_order"] = scenario_total["scenario_display"].map({"Base case": 0, "Optimized case": 1, "Downside case": 2})
    display_table(
        scenario_total.sort_values("sort_order"),
        ["scenario_th", "forecast_units", "revenue_thb", "contribution_after_waste_thb", "fixed_overhead_thb", "modeled_operating_result_thb"],
        {"scenario_th": "สถานการณ์", "forecast_units": "ยอดขายคาดการณ์", "revenue_thb": "รายได้", "contribution_after_waste_thb": "เงินเหลือหลังของเสีย", "fixed_overhead_thb": "ค่าใช้จ่ายคงที่", "modeled_operating_result_thb": "ผลดำเนินงานตามแบบจำลอง"},
        integer_columns=("forecast_units",), money_columns=("revenue_thb", "contribution_after_waste_thb", "fixed_overhead_thb", "modeled_operating_result_thb"),
    )
    optimized_result = float(scenario_total.loc[scenario_total["scenario_display"] == "Optimized case", "modeled_operating_result_thb"].iloc[0])
    base_result = float(scenario_total.loc[scenario_total["scenario_display"] == "Base case", "modeled_operating_result_thb"].iloc[0])
    st.warning(f"กรณีปรับปรุงใช้ราคาที่รับจริงแบบมาตรฐานและลดอัตราของเสีย 25% โดยไม่สมมติว่ายอดขายเพิ่มจากราคา ผลจึงดีขึ้น {money(optimized_result - base_result)} จากกรณีฐาน แต่ยังขาดทุน {money(-optimized_result)} ใน 3 เดือน นี่คือช่องว่างที่ต้องปิดด้วยมาตรการที่มีผลจริงและไม่ซ้ำกับสมมติฐานกรณีปรับปรุง")

    st.markdown("#### เป้าเตรียมเมื่อแผนยอดขายได้รับการยืนยัน")
    st.info("อย่าเตรียมเพิ่มตามเป้าเติบโตทันที เป้าด้านล่างเป็นความต้องการเมื่อยอดขายตามแผนเกิดขึ้นจริง ใช้ยอดคำสั่งซื้อและยอดขายระหว่างวันยืนยันก่อน แล้วคำนวณรอบเตรียมใหม่ทุก 7 วัน")
    recovery_prep["month"] = pd.to_datetime(recovery_prep["month"])
    display_table(
        recovery_prep,
        ["month", "kitchen", "sku", "baseline_units", "target_sales", "target_prep", "expected_waste", "waste_rate_target", "target_price", "extra_sales_vs_base", "contribution_per_cup"],
        {"month": "เดือน", "kitchen": "ครัว", "sku": "สินค้า", "baseline_units": "ฐานคาดการณ์", "target_sales": "เป้าขาย", "target_prep": "เป้าเตรียม", "expected_waste": "ของเสียที่คาด", "waste_rate_target": "อัตราของเสียเป้า", "target_price": "ราคาเป้าทดสอบ", "extra_sales_vs_base": "ยอดเพิ่มจากฐาน", "contribution_per_cup": "เงินเหลือหลังของเสีย/แก้ว"},
        date_columns=("month",), integer_columns=("baseline_units", "target_sales", "target_prep", "expected_waste", "extra_sales_vs_base"), percent_columns=("waste_rate_target",), money_columns=("target_price", "contribution_per_cup",), height=420,
    )
    st.caption("เป้าเตรียมนี้เป็นแก้วตามแบบจำลอง ไม่ใช่จำนวนสั่งซื้อวัตถุดิบ เพราะยังไม่มี stock on hand, inbound, lead time, shelf life และ BOM/yield")

    with st.expander("ดูผลรายครัวและความเสี่ยงเมื่อทำเป้าไม่ได้"):
        recovery_kitchen["month"] = pd.to_datetime(recovery_kitchen["month"])
        display_table(
            recovery_kitchen,
            ["month", "kitchen", "target_sales", "target_prep", "contribution_thb", "fixed_overhead_thb", "operating_before_central_implementation_thb"],
            {"month": "เดือน", "kitchen": "ครัว", "target_sales": "เป้าขาย", "target_prep": "เป้าเตรียม", "contribution_thb": "เงินเหลือหลังของเสีย", "fixed_overhead_thb": "ค่าใช้จ่ายคงที่ตามเป้า", "operating_before_central_implementation_thb": "ผลครัวก่อนงบส่วนกลาง"},
            date_columns=("month",), integer_columns=("target_sales", "target_prep"), money_columns=("contribution_thb", "fixed_overhead_thb", "operating_before_central_implementation_thb",),
        )
        display_table(
            recovery_sensitivity,
            ["scenario", "operating_result_thb", "gap_to_zero_thb"],
            {"scenario": "ถ้าเกิดเงื่อนไขนี้", "operating_result_thb": "ผลดำเนินงานรวม 3 เดือน", "gap_to_zero_thb": "ช่องว่างถึงคุ้มทุน"},
            money_columns=("operating_result_thb", "gap_to_zero_thb",),
        )
        st.markdown("**สะพานปิดช่องว่างแบบคำนวณต่อเนื่อง**")
        display_table(
            recovery_bridge,
            ["step", "increment_thb", "result_thb"],
            {"step": "ขั้นตอน", "increment_thb": "ผลเพิ่มจากขั้นก่อน", "result_thb": "ผลสะสมตามแบบจำลอง"},
            money_columns=("increment_thb", "result_thb",),
        )
        st.caption("ผลจากมาตรการแต่ละขั้นคำนวณต่อเนื่อง จึงไม่ควรนำผลประหยัดแต่ละแถวมาบวกซ้ำเป็นอิสระ")

    st.markdown("#### เป้าเตรียมสินค้า: มองตามสินค้าและเลือกดูครัว")
    sku_monthly = data["forecast_monthly_sku"].pivot(index="month", columns="sku", values="forecast_units")
    st.bar_chart(sku_monthly, height=280)
    st.caption("โมเดลคาดการณ์ทำระดับครัว × สินค้า 20 คู่ กราฟนี้รวมขึ้นมาระดับสินค้าเพื่อให้ดูง่าย")
    col1, col2 = st.columns(2)
    kitchens = ["All"] + sorted(data["forecast"]["kitchen"].unique().tolist())
    skus = ["All"] + sorted(data["forecast"]["sku"].unique().tolist())
    selected_kitchen = col1.selectbox("เลือกครัว", kitchens, format_func=lambda option: "ทุกครัว" if option == "All" else option)
    selected_sku = col2.selectbox("เลือกสินค้า", skus, format_func=lambda option: "ทุกสินค้า" if option == "All" else option)
    filtered = data["forecast"].copy()
    req = requirements.copy()
    if selected_kitchen != "All":
        filtered = filtered.loc[filtered["kitchen"] == selected_kitchen]
        req = req.loc[req["kitchen"] == selected_kitchen]
    if selected_sku != "All":
        filtered = filtered.loc[filtered["sku"] == selected_sku]
        req = req.loc[req["sku"] == selected_sku]
    daily = filtered.groupby("date", as_index=True)["forecast_units_base"].sum().to_frame("ยอดขายคาดการณ์ (แก้ว)")
    st.line_chart(daily, height=300)
    req["month"] = req["date"].dt.to_period("M").dt.to_timestamp()
    prep_monthly = req.groupby(["month", "kitchen", "sku"], as_index=False).agg(
        forecast_lower_units=("forecast_lower_units", "sum"), forecast_units_base=("forecast_units_base", "sum"), forecast_upper_units=("forecast_upper_units", "sum"), prep_target_cups_lower=("prep_target_cups_lower", "sum"), prep_target_cups_base=("prep_target_cups_base", "sum"), prep_target_cups_upper=("prep_target_cups_upper", "sum"), expected_waste_units_base=("expected_waste_units_base", "sum")
    )
    display_table(
        prep_monthly,
        ["month", "kitchen", "sku", "forecast_lower_units", "forecast_units_base", "forecast_upper_units", "prep_target_cups_lower", "prep_target_cups_base", "prep_target_cups_upper", "expected_waste_units_base"],
        {"month": "เดือน", "kitchen": "ครัว", "sku": "สินค้า", "forecast_lower_units": "ยอดขายขอบล่าง", "forecast_units_base": "ยอดขายกรณีฐาน", "forecast_upper_units": "ยอดขายขอบบน", "prep_target_cups_lower": "เตรียมขอบล่าง", "prep_target_cups_base": "เป้าเตรียมกรณีฐาน", "prep_target_cups_upper": "เตรียมขอบบน", "expected_waste_units_base": "ของเสียที่คาด"},
        date_columns=("month",), integer_columns=("forecast_lower_units", "forecast_units_base", "forecast_upper_units", "prep_target_cups_lower", "prep_target_cups_base", "prep_target_cups_upper", "expected_waste_units_base"), height=360,
    )

    st.markdown("#### นโยบายเตรียมและเติมสินค้า")
    st.write("จัด ABC จากเงินเหลือหลังของเสียใน 3 เดือน และ XYZ จากความผันผวน Demand 12 สัปดาห์ Safety stock เป็นนโยบายเสนอที่ service level 95% (Z = 1.65) และทบทวนทุก 7 วัน ไม่ใช่ระยะเวลาจัดส่งจาก supplier")
    alert_map = {"green": "ปกติ", "amber": "ของเสียสูง", "red": "เงินเหลือติดลบ + ของเสียสูง"}
    policy["alert_th"] = policy["inventory_alert"].str.lower().map(alert_map).fillna(policy["inventory_alert"])
    display_table(
        policy.sort_values(["inventory_alert", "waste_rate"], ascending=[True, False]),
        ["kitchen", "sku", "forecast_3m_cups", "avg_weekly_demand_cups", "demand_cv", "waste_rate", "contribution_after_waste_per_cup_thb", "abc_class", "xyz_class", "safety_stock_cups_policy", "target_stock_next_7d_cups", "alert_th", "inventory_policy"],
        {"kitchen": "ครัว", "sku": "สินค้า", "forecast_3m_cups": "คาดขาย 3 เดือน", "avg_weekly_demand_cups": "เฉลี่ย/สัปดาห์", "demand_cv": "ความผันผวน Demand", "waste_rate": "อัตราของเสีย", "contribution_after_waste_per_cup_thb": "เงินเหลือหลังของเสีย/แก้ว", "abc_class": "ABC", "xyz_class": "XYZ", "safety_stock_cups_policy": "Safety stock ที่เสนอ", "target_stock_next_7d_cups": "เป้าสต็อก 7 วัน", "alert_th": "สถานะ", "inventory_policy": "นโยบาย"},
        integer_columns=("forecast_3m_cups", "avg_weekly_demand_cups", "safety_stock_cups_policy", "target_stock_next_7d_cups"), percent_columns=("demand_cv", "waste_rate"), money_columns=("contribution_after_waste_per_cup_thb",), height=430,
    )
    st.caption("คู่ครัว–สินค้าที่เป็น “ของเสียสูง” หรือ “เงินเหลือติดลบ + ของเสียสูง” ต้องเตรียมรอบเล็กและถี่ขึ้น นี่คือ alert การผลิต ไม่ใช่ใบสั่งซื้ออัตโนมัติ")

    with st.expander("วิธี Forecast, ความไวต้นทุน และขอบเขตการสั่งซื้อ"):
        st.markdown("**เลือกวิธี Forecast อย่างไร?**")
        st.write(f"เลือก `{data['metrics']['selected_method']}` เพราะ WAPE เฉลี่ยจาก rolling-origin backtest 4 จุดต่ำสุดที่ {pct(data['metrics']['selected_method_mean_wape'])} เทียบ 5 วิธี และใช้ข้อมูลก่อน 31 ส.ค. 2026 เท่านั้น")
        backtest_view = data["backtest"].copy()
        display_table(
            backtest_view, ["method", "cutoffs", "mae", "wape", "bias_pct"],
            {"method": "วิธี", "cutoffs": "จำนวนช่วงทดสอบ", "mae": "MAE (แก้ว)", "wape": "WAPE", "bias_pct": "Bias"},
            integer_columns=("cutoffs",), percent_columns=("wape", "bias_pct"), decimal_columns=("mae",),
        )
        st.caption(data["metrics"]["forecast_uncertainty_basis"])
        st.markdown("**P&L รายเดือนของทุกสถานการณ์**")
        display_table(
            scenario,
            ["scenario_display", "month", "forecast_units", "revenue_thb", "sold_fruit_cost_thb", "sold_packaging_cost_thb", "sold_labor_cost_thb", "commission_thb", "waste_cost_thb", "contribution_after_waste_thb", "fixed_overhead_thb", "modeled_operating_result_thb", "operating_margin_pct"],
            {"scenario_display": "สถานการณ์", "month": "เดือน", "forecast_units": "ยอดขายคาดการณ์", "revenue_thb": "รายได้", "sold_fruit_cost_thb": "ต้นทุนผลไม้", "sold_packaging_cost_thb": "บรรจุภัณฑ์", "sold_labor_cost_thb": "แรงงาน", "commission_thb": "ค่าคอมมิชชัน", "waste_cost_thb": "ต้นทุนของเสีย", "contribution_after_waste_thb": "เงินเหลือหลังของเสีย", "fixed_overhead_thb": "ค่าใช้จ่ายคงที่", "modeled_operating_result_thb": "ผลดำเนินงานตามแบบจำลอง", "operating_margin_pct": "สัดส่วนผลดำเนินงาน"},
            date_columns=("month",), integer_columns=("forecast_units",), money_columns=("revenue_thb", "sold_fruit_cost_thb", "sold_packaging_cost_thb", "sold_labor_cost_thb", "commission_thb", "waste_cost_thb", "contribution_after_waste_thb", "fixed_overhead_thb", "modeled_operating_result_thb"), percent_columns=("operating_margin_pct",), height=380,
        )
        st.caption(data["metrics"]["commission_basis"] + " " + data["metrics"]["mixedberry_note"])
        st.markdown("**ถ้าต้นทุนผลไม้เพิ่ม ผลจะเป็นอย่างไร?**")
        stress = data["fruit_cost_stress"].copy()
        stress["uplift_label"] = stress["fruit_cost_uplift_pct"].map(lambda value: pct(value, 0))
        st.line_chart(stress.set_index("uplift_label")[["modeled_operating_result_thb"]].rename(columns={"modeled_operating_result_thb": "ผลดำเนินงานตามแบบจำลอง (บาท)"}), height=240)
        display_table(
            stress, ["fruit_cost_uplift_pct", "forecast_units", "revenue_thb", "fruit_cost_thb", "waste_cost_thb", "contribution_after_waste_thb", "fixed_overhead_thb", "modeled_operating_result_thb", "operating_margin_pct"],
            {"fruit_cost_uplift_pct": "ต้นทุนผลไม้เพิ่ม", "forecast_units": "ยอดขายคาดการณ์", "revenue_thb": "รายได้", "fruit_cost_thb": "ต้นทุนผลไม้", "waste_cost_thb": "ต้นทุนของเสีย", "contribution_after_waste_thb": "เงินเหลือหลังของเสีย", "fixed_overhead_thb": "ค่าใช้จ่ายคงที่", "modeled_operating_result_thb": "ผลดำเนินงานตามแบบจำลอง", "operating_margin_pct": "สัดส่วนผลดำเนินงาน"},
            percent_columns=("fruit_cost_uplift_pct", "operating_margin_pct"), integer_columns=("forecast_units",), money_columns=("revenue_thb", "fruit_cost_thb", "waste_cost_thb", "contribution_after_waste_thb", "fixed_overhead_thb", "modeled_operating_result_thb"),
        )
        st.markdown("**สูตรที่ใช้เมื่อมีข้อมูลสต็อกครบ**")
        st.code("target_stock = forecast_during_review_period + safety_stock\norder_qty = max(0, target_stock - usable_on_hand - usable_inbound + committed_demand)", language="text")
        st.info("ยังไม่คำนวณจำนวนสั่งซื้อจริง เพราะกรณีศึกษานี้ไม่มี stock on hand, inbound, supplier lead time, shelf life, BOM/recipe yield และ stockout flags จนกว่าจะมีข้อมูลเหล่านี้ ให้ใช้เป้าเตรียมเป็นแก้วและนโยบาย safety stock สำหรับการผลิตรายวัน ทบทวน Forecast เมื่อมี actual ใหม่ทุกสัปดาห์")


def data_quality(data: dict) -> None:
    task_heading("Task 1 · Data quality", "ที่มาข้อมูลและข้อจำกัด", "ตรวจข้อมูลดิบก่อนใช้ตัดสินใจ เพื่อให้รายได้ Demand โปรโมชั่น และ P&L ไม่ถูกตีความจากแถวที่ซ้ำหรือรายการที่ไม่ใช่เมนู")
    readiness = data["readiness"]
    raw = readiness["raw_orders"]
    candidate = readiness["candidate_preparation"]
    waste = readiness["waste"]
    reconciliation = data["reconciliation"]
    audit = data["audit"]
    checks = audit["checks"]
    c1, c2, c3 = st.columns(3)
    c1.metric("แถวคำสั่งซื้อดิบ", f"{checks['raw_order_rows']:,}")
    c2.metric("แถวเมนูที่ใช้วิเคราะห์", f"{checks['retained_candidate_menu_rows']:,}")
    c3.metric("รายได้หลังคัดกรอง", money(reconciliation["retained_menu_revenue_thb"]))

    st.markdown("#### จากข้อมูลดิบสู่ข้อมูลที่ใช้วิเคราะห์")
    st.markdown(
        f"<div class='callout'><strong>{reconciliation['raw_rows']:,} แถวข้อมูลดิบ</strong> → ตัดแถวซ้ำ {reconciliation['duplicate_excess_rows_removed']:,} แถว → ตัดรายการที่ไม่ใช่เมนู {reconciliation['non_menu_rows_excluded']:,} แถว → เหลือ <strong>{reconciliation['retained_menu_rows']:,} แถวเมนู</strong> สำหรับวิเคราะห์</div>",
        unsafe_allow_html=True,
    )
    st.caption(f"หากไม่ตัดแถวซ้ำ รายได้จะถูกนับสูงเกินประมาณ {money(reconciliation['duplicate_revenue_removed_thb'])}")

    st.markdown("#### สิ่งที่ตรวจและวิธีจัดการ")
    screening = pd.DataFrame([
        ["ค่าว่าง", f"ไม่พบค่าว่างใน 9 ฟิลด์ของคำสั่งซื้อดิบ", "ไม่ต้องแทนค่าในฟิลด์คำสั่งซื้อ"],
        ["แถวซ้ำแบบตรงกัน", f"เกิน {raw['exact_duplicate_excess_rows']:,} แถว และมีรายได้ {money(reconciliation['duplicate_revenue_removed_thb'])}", "ตัดแถวที่เกิน และเก็บการตรวจสอบย้อนกลับไว้"],
        ["วัน เวลา และจำนวนขาย", f"วันผิดรูปแบบ {raw['invalid_dates']}; ชั่วโมงผิด {raw['invalid_hours']}; ยอดขายไม่เป็นบวก {raw['nonpositive_units']}", "ไม่มีรายการลักษณะนี้ผ่านเข้าสู่ชุดข้อมูลที่เผยแพร่"],
        ["ราคาและรายได้", f"แถวที่ราคา × จำนวนไม่เท่ารายได้: {raw['revenue_identity_mismatch_rows_over_001_thb']}; สูตรส่วนลดไม่ตรง: {candidate['price_discount_formula_mismatch_rows_over_001_thb']}", "คงราคาหลังโปรโมชันที่พบจริง และไม่หักส่วนลดซ้ำ"],
        ["การจับคู่สินค้า/รหัส", f"รหัสฐานที่ไม่รู้จัก {len(candidate['unknown_base_codes'])}; SKU suffix ไม่ตรง {candidate['sku_suffix_mismatch_rows']}", "ใช้เฉพาะ 5 สินค้าหลักที่จับคู่ได้; ตัดรายการไม่ใช่เมนู 370 แถว"],
        ["ความครบต้นทุน", f"ยอดขาย {candidate['missing_exact_week_fruit_cost_rows']} แถว และของเสีย {waste['missing_estimated_waste_cost_rows']} แถว ต้องใช้ proxy", "แสดงสถานะสมมติฐานไว้ และไม่ตั้งต้นทุนที่ขาดเป็นศูนย์"],
        ["ค่าที่สูงผิดปกติ", "ไม่ตัดรายการที่ถูกต้องเพียงเพราะยอดขายหรือราคาสูง", "เก็บ peak และฤดูกาลไว้; ตัดเฉพาะข้อมูลผิดรูปแบบหรือจับคู่ไม่ได้"],
    ], columns=["สิ่งที่ตรวจ", "หลักฐาน", "วิธีจัดการ"])
    st.dataframe(screening, width="stretch", hide_index=True)

    st.markdown("#### กระทบยอดก่อน–หลังคัดกรอง")
    bridge = pd.DataFrame([
        ["Raw export", reconciliation["raw_rows"], reconciliation["raw_units"], reconciliation["raw_revenue_thb"]],
        ["Less duplicate excess", -reconciliation["duplicate_excess_rows_removed"], -reconciliation["duplicate_units_removed"], -reconciliation["duplicate_revenue_removed_thb"]],
        ["Less non-menu rows", -reconciliation["non_menu_rows_excluded"], -reconciliation["non_menu_units_excluded"], -reconciliation["non_menu_revenue_excluded_thb"]],
        ["Released menu data", reconciliation["retained_menu_rows"], reconciliation["retained_menu_units"], reconciliation["retained_menu_revenue_thb"]],
    ], columns=["Bridge", "Rows", "Units", "Revenue (THB)"])
    bridge["Bridge"] = ["ข้อมูลดิบ", "ตัดแถวซ้ำที่เกิน", "ตัดรายการไม่ใช่เมนู", "ข้อมูลเมนูที่ใช้วิเคราะห์"]
    display_table(
        bridge, ["Bridge", "Rows", "Units", "Revenue (THB)"],
        {"Bridge": "ขั้นตอน", "Rows": "แถว", "Units": "จำนวนแก้ว", "Revenue (THB)": "รายได้"}, integer_columns=("Rows", "Units"), money_columns=("Revenue (THB)",),
    )

    st.markdown("#### ประเด็นที่ยังต้องติดตาม")
    issues = data["issues"].copy()
    issues["severity_th"] = issues["severity"].map({"high": "สูง", "medium": "กลาง", "low": "ต่ำ"}).fillna(issues["severity"])
    issues["status_th"] = issues["status"].map({"released": "จัดการแล้ว", "assumed": "ใช้สมมติฐาน", "open": "ยังเปิดอยู่"}).fillna(issues["status"])
    display_table(
        issues, ["issue_id", "severity_th", "status_th", "issue", "impact", "recommended_action", "evidence"],
        {"issue_id": "รหัส", "severity_th": "ความสำคัญ", "status_th": "สถานะ", "issue": "ประเด็น", "impact": "ผลกระทบ", "recommended_action": "สิ่งที่ควรทำ", "evidence": "หลักฐาน"},
        height=330,
    )

    st.markdown("#### สถานะการตรวจสอบ")
    release_qa = data["data_qa"]
    st.success(f"Data-release QA: {release_qa['status']} · ผ่าน {len(release_qa['checks']) - release_qa['failed_count']}/{len(release_qa['checks'])} จาก {len(release_qa['checks'])} รายการ")
    qa_df = pd.DataFrame(data["qa"]["checks"])
    qa_columns = [column for column in ["name", "result", "expected", "actual", "owner", "impact"] if column in qa_df]
    st.dataframe(qa_df[qa_columns].astype(str).rename(columns={"name": "รายการตรวจ", "result": "ผล", "expected": "ค่าที่คาด", "actual": "ค่าที่พบ", "owner": "ผู้รับผิดชอบเดิม", "impact": "ผลกระทบ"}), width="stretch", hide_index=True, height=360)
    st.caption("ไฟล์ต้นทางเป็นแบบอ่านอย่างเดียว Proxy ยังคงระบุสถานะไว้ชัดเจน ข้อจำกัดสำคัญที่เหลือคือขอบเขต GP ในงบ ความครอบคลุมของของเสีย และข้อมูลควบคุมสต็อกที่ยังไม่มี")


def main() -> None:
    st.set_page_config(page_title="FruitBlend24 | Decision Dashboard", page_icon="🥤", layout="wide", initial_sidebar_state="collapsed")
    apply_theme()
    data = load_data()
    st.title("FruitBlend24 · Decision Dashboard")
    st.caption("แปลงข้อมูลยอดขาย ราคา โปรโมชั่น ต้นทุน และของเสีย ให้เป็นสิ่งที่ทีมตัดสินใจได้ · กรณีศึกษาข้อมูลจำลอง · เวอร์ชันข้อมูล " + DATA_VERSION)
    st.sidebar.header("อ่านเว็บนี้อย่างไร")
    st.sidebar.write("เริ่มที่ภาพรวมเพื่อเข้าใจปัญหา แล้วเปิดแท็บที่ตอบคำถามของคุณ ทุกตัวเลขเชื่อมกลับไปยัง artifact ที่ผ่าน QA")
    st.sidebar.markdown("**เส้นทางแนะนำ**\n\n1. ภาพรวมและแผนแก้ไข\n2. สินค้า สาขา และผลเทียบงบ\n3. โปรโมชั่นคุ้มไหม\n4. ยอดขายและความเหมาะสมของราคา\n5. แผน 3 เดือนและการเตรียมสินค้า\n6. ที่มาข้อมูลและข้อจำกัด")
    tabs = st.tabs(["ภาพรวมและแผนแก้ไข", "สินค้า สาขา และผลเทียบงบ", "โปรโมชั่นคุ้มไหม", "ยอดขายและความเหมาะสมของราคา", "แผน 3 เดือนและการเตรียมสินค้า", "ที่มาข้อมูลและข้อจำกัด"])
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
    st.caption("ขอบเขต: กรณีศึกษา FruitBlend24 ที่เป็นข้อมูลจำลอง รายละเอียด assumptions และ QA เก็บไว้ใต้ reports/fruitblend24_run_001 และ data/processed/fruitblend24_v1_c2869ce419bf")


if __name__ == "__main__":
    main()
