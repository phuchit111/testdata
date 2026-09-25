"""A7 memo and HTML presentation generated from QA-passed artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "reports/fruitblend24_run_001"
COMM = RUN / "commercial"
FIN = RUN / "finance"
INV = RUN / "inventory"
OUT = ROOT / "deliverables/fruitblend24_run_001"
CHARTS = OUT / "charts"


def money(v: float, decimals: int = 0) -> str:
    return f"฿{v:,.{decimals}f}"


def pct(v: float, decimals: int = 1) -> str:
    return f"{v * 100:.{decimals}f}%"


def save_chart(svg: str, name: str) -> str:
    CHARTS.mkdir(parents=True, exist_ok=True)
    path = CHARTS / name
    path.write_text(svg, encoding="utf-8")
    return f"charts/{name}"


def svg_bar(labels, values, title, ylabel, colors=None, width=900, height=460):
    colors = colors or ["#0f766e"] * len(values)
    left, right, top, bottom = 72, 24, 64, 62
    plot_w, plot_h = width - left - right, height - top - bottom
    lo = min(0, min(values))
    hi = max(1, max(values)) * 1.15
    y = lambda v: top + plot_h * (hi - v) / (hi - lo)
    zero = y(0)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="white"/>', f'<text x="{left}" y="30" font-family="Arial" font-size="20" font-weight="700" fill="#0f766e">{title}</text>', f'<text x="14" y="{top + plot_h/2}" transform="rotate(-90 14 {top + plot_h/2})" font-family="Arial" font-size="12" fill="#334155">{ylabel}</text>', f'<line x1="{left}" y1="{zero:.1f}" x2="{width-right}" y2="{zero:.1f}" stroke="#334155"/>']
    step = plot_w / max(1, len(values))
    bar_w = step * 0.62
    for i, (label, value, color) in enumerate(zip(labels, values, colors)):
        x = left + i * step + (step - bar_w) / 2
        yy = y(value) if value >= 0 else zero
        hh = abs(y(value) - zero)
        parts.append(f'<rect x="{x:.1f}" y="{yy:.1f}" width="{bar_w:.1f}" height="{max(1,hh):.1f}" fill="{color}" rx="3"/>')
        parts.append(f'<text x="{x+bar_w/2:.1f}" y="{height-32}" text-anchor="middle" font-family="Arial" font-size="11" fill="#334155">{label}</text>')
    parts.append(f'<text x="{left-8}" y="{top+4}" text-anchor="end" font-family="Arial" font-size="11" fill="#64748b">{hi:,.0f}</text>')
    parts.append(f'<text x="{left-8}" y="{zero+4}" text-anchor="end" font-family="Arial" font-size="11" fill="#64748b">0</text>')
    parts.append("</svg>")
    return "".join(parts)


def svg_line(labels, series, title, ylabel, width=960, height=480):
    left, right, top, bottom = 72, 30, 64, 68
    plot_w, plot_h = width - left - right, height - top - bottom
    vals = [v for _, arr, _ in series for v in arr]
    lo = min(0, min(vals))
    hi = max(1, max(vals)) * 1.12
    y = lambda v: top + plot_h * (hi - v) / (hi - lo)
    x = lambda i: left + (plot_w * i / max(1, len(labels)-1))
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="white"/>', f'<text x="{left}" y="30" font-family="Arial" font-size="20" font-weight="700" fill="#0f766e">{title}</text>', f'<text x="14" y="{top + plot_h/2}" transform="rotate(-90 14 {top + plot_h/2})" font-family="Arial" font-size="12" fill="#334155">{ylabel}</text>', f'<line x1="{left}" y1="{y(0):.1f}" x2="{width-right}" y2="{y(0):.1f}" stroke="#cbd5e1"/>']
    for i, label in enumerate(labels):
        parts.append(f'<text x="{x(i):.1f}" y="{height-34}" text-anchor="middle" font-family="Arial" font-size="11" fill="#334155">{label}</text>')
    for name, arr, color in series:
        points = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(arr))
        parts.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="3"/>')
        for i, v in enumerate(arr):
            parts.append(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="4" fill="{color}"/>')
    lx = width - 250
    for j, (name, _, color) in enumerate(series):
        yy = 58 + j * 20
        parts.append(f'<line x1="{lx}" y1="{yy}" x2="{lx+22}" y2="{yy}" stroke="{color}" stroke-width="3"/><text x="{lx+30}" y="{yy+4}" font-family="Arial" font-size="12" fill="#334155">{name}</text>')
    parts.append("</svg>")
    return "".join(parts)


def build() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    sku = pd.read_csv(COMM / "sku_summary.csv", encoding="utf-8-sig")
    price = pd.read_csv(COMM / "price_floor.csv", encoding="utf-8-sig")
    promo = pd.read_csv(COMM / "promo_summary.csv", encoding="utf-8-sig")
    comparator = pd.read_csv(COMM / "promo_comparator_by_stratum.csv", encoding="utf-8-sig")
    finance = pd.read_csv(FIN / "pnl_monthly_company_vs_budget.csv", encoding="utf-8-sig")
    scenarios = pd.read_csv(INV / "scenario_monthly_pnl.csv", encoding="utf-8-sig")
    backtest = pd.read_csv(INV / "backtest_summary.csv", encoding="utf-8-sig")
    forecast = pd.read_csv(INV / "forecast_daily.csv", encoding="utf-8-sig")
    audit = json.loads((RUN / "data/audit.json").read_text(encoding="utf-8"))
    qa = json.loads((RUN / "qa/checks_final.json").read_text(encoding="utf-8"))
    fmetrics = json.loads((INV / "forecast_metrics.json").read_text(encoding="utf-8"))

    # 1. Revenue vs budget
    finance["month_label"] = pd.to_datetime(finance["month"]).dt.strftime("%b-%y")
    revenue_chart = save_chart(
        svg_line(
            finance["month_label"].tolist(),
            [("Actual revenue", (finance["gross_revenue_thb"] / 1e6).tolist(), "#0f766e"), ("Budget revenue", (finance["budget_revenue_thb"] / 1e6).tolist(), "#64748b")],
            "Revenue was below the flat budget in 9 of 12 months", "THB millions",
        ),
        "01_revenue_vs_budget.svg",
    )

    # 2. SKU contribution after waste
    plot_sku = sku.sort_values("contribution_after_waste_thb")
    colors = ["#b91c1c" if v < 0 else "#0f766e" for v in plot_sku["contribution_after_waste_thb"]]
    sku_chart = save_chart(
        svg_bar(plot_sku["sku"].tolist(), (plot_sku["contribution_after_waste_thb"] / 1e3).tolist(), "MixedBerryPremium is the only SKU with negative post-waste contribution", "THB thousands", colors),
        "02_contribution_by_sku.svg",
    )

    # 3. Promo contribution per cup
    promo_plot = promo.copy()
    promo_plot["label"] = promo_plot["base_code"]
    colors = ["#64748b" if code == "RC000" else "#f59e0b" for code in promo_plot["base_code"]]
    promo_chart = save_chart(
        svg_bar(promo_plot["label"].tolist(), promo_plot["contribution_before_waste_per_cup_thb"].tolist(), "Discounted rate codes reduce contribution per cup", "THB/cup", colors),
        "03_promo_contribution_per_cup.svg",
    )

    # 4. Forecast scenarios
    scenarios["month_label"] = pd.to_datetime(scenarios["month"]).dt.strftime("%b-%y")
    forecast_series = []
    scenario_labels = {"base": "Base", "downside": "Downside", "price_and_waste_action": "RC000 price + Waste action"}
    for label, color in [("base", "#0f766e"), ("downside", "#b91c1c"), ("price_and_waste_action", "#2563eb")]:
        d = scenarios.loc[scenarios["scenario"] == label]
        forecast_series.append((scenario_labels[label], (d["modeled_operating_result_thb"] / 1e3).tolist(), color))
    forecast_chart = save_chart(
        svg_line(scenarios.loc[scenarios["scenario"] == "base", "month_label"].tolist(), forecast_series, "The base outlook remains loss-making after fixed kitchen overhead", "THB thousands"),
        "04_forecast_scenarios.svg",
    )

    # Aggregated matched-promo association evidence.
    matched = comparator.loc[comparator["has_standard_comparator"]].copy()
    matched["delta_weight"] = matched["promoted_units"]
    promo_assoc = matched.groupby(["base_code", "rate_code_name"], as_index=False).apply(
        lambda g: pd.Series({
            "promoted_rows": g["promoted_rows"].sum(),
            "standard_rows": g["standard_rows"].sum(),
            "association_units_lift_pct": np.average(g["association_units_lift_pct"], weights=g["delta_weight"]),
            "promoted_contribution_per_cup": np.average(g["promoted_contribution_per_cup"], weights=g["delta_weight"]),
            "standard_contribution_per_cup": np.average(g["standard_contribution_per_cup"], weights=g["delta_weight"]),
        })
    ).reset_index(drop=True)
    promo_assoc["contribution_delta_thb"] = promo_assoc["promoted_contribution_per_cup"] - promo_assoc["standard_contribution_per_cup"]
    promo_assoc["break_even_units_lift_pct"] = promo_assoc["standard_contribution_per_cup"] / promo_assoc["promoted_contribution_per_cup"] - 1

    mixed = sku.loc[sku["sku"] == "MixedBerryPremium"].iloc[0]
    total_rev = finance["gross_revenue_thb"].sum()
    total_budget = finance["budget_revenue_thb"].sum()
    rev_var = total_rev - total_budget
    operating = finance["modeled_operating_result_thb"].sum()
    forecast_base = scenarios.loc[scenarios["scenario"] == "base"]
    forecast_action = scenarios.loc[scenarios["scenario"] == "price_and_waste_action"]
    base_total = forecast_base["modeled_operating_result_thb"].sum()
    action_total = forecast_action["modeled_operating_result_thb"].sum()
    base_cups = forecast["forecast_units_base"].sum()
    base_prep = forecast["prep_target_cups_base"].sum()
    selected = backtest.loc[backtest["method"] == fmetrics["selected_method"]].iloc[0]
    profitability_gap = fmetrics["profitability_gap"]

    recommendations = [
        {
            "title": "Gate discounts by contribution, not volume alone",
            "action": "Pause blanket use of RC101/RC103 and redesign RC102 as a controlled test. Keep the matched standard comparator, require incremental cups to clear the break-even lift, and report contribution after commission.",
            "owner": "Commercial / Growth",
            "timing": "Next 2-week campaign cycle",
            "kpi": "Contribution/cup, incremental cups vs matched control, promo waste rate",
            "evidence": f"Standard contribution is {money(float(promo.loc[promo.base_code == 'RC000', 'contribution_before_waste_per_cup_thb'].iloc[0]), 2)}/cup vs {money(float(promo.loc[promo.base_code == 'RC102', 'contribution_before_waste_per_cup_thb'].iloc[0]), 2)}/cup for RC102. Association is not causation.",
        },
        {
            "title": "Fix MixedBerryPremium before scaling it",
            "action": "Run a 4-week price/portion and prep-control pilot. Do not expand volume until post-waste contribution is positive and waste is below a management-set threshold.",
            "owner": "Category + Kitchen Operations",
            "timing": "Start within 1 week; review weekly",
            "kpi": "Post-waste contribution/cup > 0, waste rate < 10% pilot target, cups sold, repeat demand once IDs exist",
            "evidence": f"{mixed['units_sold']:,.0f} cups and {money(mixed['gross_revenue_thb'])} revenue still produce {money(mixed['contribution_after_waste_thb'])} after {money(mixed['waste_cost_thb'])} waste cost; waste rate is {pct(mixed['waste_rate'])}.",
        },
        {
            "title": "Run a weekly cup-based prep control",
            "action": "Use the selected level-and-weekday blend by kitchen and SKU. Set daily prep to forecast cups plus expected waste at Kitchen x SKU grain, review actuals every seven days, and treat the variability buffer as capacity guidance rather than prepared stock. Keep purchase quantity blank until on-hand, inbound, lead time, shelf life, and recipe yield are captured.",
            "owner": "Operations / Supply",
            "timing": "Daily prep; weekly review",
            "kpi": f"Pooled WAPE target at or below {pct(float(selected['wape']))}; waste rate; forecast bias; service level only after lead-time and stockout data exist",
            "evidence": f"Selected method is {fmetrics['selected_method']} with pooled backtest WAPE {pct(float(fmetrics['selected_method_pooled_wape']))}. Base outlook is {base_cups:,.0f} sold cups and {base_prep:,.0f} prep cups for Sep-Nov.",
        },
    ]

    memo = f"""# FruitBlend24 decision memo

## Executive decision

FruitBlend24 needs a contribution-first operating plan. The retained menu dataset shows {money(total_rev)} revenue across 618,123 cups, {money(abs(rev_var))} below the {money(total_budget)} 12-month revenue budget ({pct(rev_var / total_budget)}). After product costs, platform commission, recorded waste, and fixed kitchen overhead, the modeled operating result is {money(operating)}. The budget gross-profit cost boundary is not defined, so the P&L shows the cost layers separately rather than calling this a confirmed budget GP variance.

## Key insights

1. **MixedBerryPremium is not profitable after waste at the observed mix.** It produces {money(mixed['contribution_after_waste_thb'])} after waste, or {money(mixed['contribution_after_waste_per_cup_thb'], 2)}/cup, with {pct(mixed['waste_rate'])} waste rate. The action is to fix price/portion and prep controls before scaling.
2. **Discounts trade contribution for observed volume.** Standard rate code contribution is {money(float(promo.loc[promo.base_code == 'RC000', 'contribution_before_waste_per_cup_thb'].iloc[0]), 2)}/cup. RC101, RC102, and RC103 are {money(float(promo.loc[promo.base_code == 'RC101', 'contribution_before_waste_per_cup_thb'].iloc[0]), 2)}, {money(float(promo.loc[promo.base_code == 'RC102', 'contribution_before_waste_per_cup_thb'].iloc[0]), 2)}, and {money(float(promo.loc[promo.base_code == 'RC103', 'contribution_before_waste_per_cup_thb'].iloc[0]), 2)}/cup. Matched rows show association, not causal uplift.
3. **The historical business is close to revenue plan but not to operating break-even.** Revenue is below budget by {money(abs(rev_var))}, while modeled operating result is negative after {money(finance['fixed_monthly_overhead_thb'].sum())} fixed overhead. Product decisions should use variable contribution; allocated overhead alone is not a shutdown test.
4. **The original Sep-Nov case horizon remains loss-making under the base forecast.** The selected level-and-weekday blend has pooled backtest WAPE {pct(float(fmetrics['selected_method_pooled_wape']))}. Base modeled operating result totals {money(base_total)}. The price-and-waste test improves this to {money(action_total)}, but leaves a {money(profitability_gap['remaining_gap_to_break_even_thb'])} gap; its volume equivalent is a hurdle, not a demand target.

## Recommendations

""" + "\n".join([f"### {i+1}. {r['title']}\n\n- **Action:** {r['action']}\n- **Owner / timing:** {r['owner']} / {r['timing']}\n- **KPI:** {r['kpi']}\n- **Evidence:** {r['evidence']}\n" for i, r in enumerate(recommendations)]) + f"""
## Method and limitations

- Raw-to-release bridge: 124,397 raw rows → 372 exact duplicate excess rows removed → 370 non-menu rows excluded → 123,655 retained menu rows. Retained revenue is {money(31146932.57)} and all row/unit/revenue bridges reconcile.
- Revenue uses observed price already net of the applied promotion. No second discount is deducted.
- Cost uses weekly fruit cost, packaging, labor, platform commission, daily recorded waste, and monthly kitchen overhead. MixedBerry launch-day cost and four waste costs are explicit proxies, not observed values.
- Forecast uses a rolling-origin comparison of six methods, including a blend of the recent exponential level and seven-day weekday profile. The future view is cup-based at Kitchen x SKU grain. The seven-day variability buffer is capacity guidance, not physical stock. Purchase quantity is not calculable because on-hand, inbound, lead time, shelf life, BOM/yield, and stockout inputs are missing.
- Promotion comparisons are matched associations by SKU, platform, weekday, and month. No customer IDs or randomized assignment evidence support retention, CAC, LTV, or causal promo uplift claims.

## Tools and further work

Python with pandas, NumPy, matplotlib, and the bundled workbook reader. Re-run `src/prepare.py`, `src/qa_data.py`, `src/commercial.py`, `src/finance.py`, `src/forecast_inventory.py`, `src/qa_final.py`, then `src/presentation.py`. Next data additions should be stock balances, inbound orders, recipes/yield, shelf life, stockout flags, customer/order IDs, and management's GP boundary.
"""
    (OUT / "memo.md").write_text(memo, encoding="utf-8")

    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>FruitBlend24 decision presentation</title>
<style>
body{{font-family:Arial, sans-serif;background:#f8fafc;color:#1e293b;margin:0}}
.deck{{max-width:1100px;margin:0 auto;padding:28px}}
section{{background:white;border-radius:16px;padding:34px 42px;margin:0 0 24px;box-shadow:0 2px 12px #0f172a14;page-break-after:always}}
h1{{font-size:34px;margin:0 0 8px;color:#0f766e}} h2{{font-size:26px;color:#0f766e;margin-top:0}} h3{{color:#334155}}
.sub{{color:#64748b;font-size:15px}} .grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:22px 0}}
.card{{background:#f1f5f9;padding:16px;border-radius:12px}} .card .num{{font-size:27px;font-weight:700;color:#0f766e}}
.warn{{background:#fef2f2;border-left:5px solid #b91c1c;padding:12px 16px;border-radius:6px}}
table{{border-collapse:collapse;width:100%;font-size:14px}} th,td{{border-bottom:1px solid #e2e8f0;padding:9px;text-align:left;vertical-align:top}} th{{background:#f1f5f9}}
img{{max-width:100%;height:auto;margin-top:12px}} li{{margin:8px 0;line-height:1.4}}
.footer{{color:#64748b;font-size:12px;margin-top:20px}}
</style></head><body><main class="deck">
<section><h1>FruitBlend24</h1><p class="sub">Revenue management and inventory decision presentation · actuals Sep 2025-Aug 2026 · forecast Sep-Nov 2026</p>
<div class="grid"><div class="card"><div class="num">{money(total_rev)}</div><div>retained menu revenue</div></div><div class="card"><div class="num">{money(rev_var)}</div><div>vs 12-month revenue budget</div></div><div class="card"><div class="num">{money(operating)}</div><div>modeled operating result</div></div></div>
<div class="warn"><b>Decision:</b> protect contribution first. MixedBerry needs an immediate fix, discounts need contribution gates, and the base forecast remains loss-making after kitchen overhead.</div>
</section>
<section><h2>1. Revenue is below plan and fixed overhead absorbs the contribution</h2><img src="{revenue_chart}"><p>Historical retained revenue is {money(total_rev)} against {money(total_budget)} budget. Modeled operating result uses the stated cost layers and subtracts fixed kitchen overhead once per month. The workbook does not define the budget gross-profit boundary.</p></section>
<section><h2>2. Portfolio: MixedBerryPremium needs action before scale</h2><img src="{sku_chart}"><table><tr><th>SKU</th><th>Units</th><th>Revenue</th><th>Post-waste contribution</th><th>Waste rate</th></tr>"""
    for _, row in sku.sort_values("contribution_after_waste_thb", ascending=False).iterrows():
        html += f"<tr><td>{row['sku']}</td><td>{row['units_sold']:,.0f}</td><td>{money(row['gross_revenue_thb'])}</td><td>{money(row['contribution_after_waste_thb'])}</td><td>{pct(row['waste_rate'])}</td></tr>"
    html += f"""</table><p>MixedBerryPremium has {mixed['units_sold']:,.0f} cups and {money(mixed['gross_revenue_thb'])} revenue, but post-waste contribution is {money(mixed['contribution_after_waste_thb'])}. Its {pct(mixed['waste_rate'])} waste rate is the immediate value leak.</p></section>
<section><h2>3. Promotions: observed volume is not enough to justify the discount</h2><img src="{promo_chart}"><table><tr><th>Rate code</th><th>Discount</th><th>Units</th><th>Contribution/cup</th><th>Matched association</th></tr>"""
    for _, row in promo.iterrows():
        assoc = promo_assoc.loc[promo_assoc["base_code"] == row["base_code"]]
        assoc_text = "standard" if row["base_code"] == "RC000" or assoc.empty else f"avg volume association {pct(float(assoc['association_units_lift_pct'].iloc[0]))}"
        html += f"<tr><td>{row['base_code']} {row['rate_code_name']}</td><td>{pct(row['discount_pct'])}</td><td>{row['units_sold']:,.0f}</td><td>{money(row['contribution_before_waste_per_cup_thb'], 2)}</td><td>{assoc_text}</td></tr>"
    html += f"""</table><p>RC101/102/103 contribution per cup is lower than standard. Use the matched rows as a test design input, not as causal uplift. Require incremental cups to exceed the break-even lift before scaling.</p></section>
<section><h2>4. Three-month outlook and prep plan</h2><img src="{forecast_chart}"><p>The selected baseline is {fmetrics['selected_method']} with pooled backtest WAPE {pct(float(fmetrics['selected_method_pooled_wape']))}. The base scenario forecasts {base_cups:,.0f} sold cups and {base_prep:,.0f} prep cups for Sep-Nov. The price-and-waste test improves the modeled result but leaves a {money(profitability_gap['remaining_gap_to_break_even_thb'])} gap. Its break-even volume equivalent is a hurdle, not an approved sales or prep target.</p><table><tr><th>Scenario</th><th>Sep-Nov revenue</th><th>Sep-Nov post-waste contribution</th><th>Sep-Nov modeled operating result</th></tr>"""
    for label in ["base", "downside", "price_and_waste_action"]:
        d = scenarios.loc[scenarios["scenario"] == label]
        html += f"<tr><td>{label.replace('_',' ').title()}</td><td>{money(d['revenue_thb'].sum())}</td><td>{money(d['contribution_after_waste_thb'].sum())}</td><td>{money(d['modeled_operating_result_thb'].sum())}</td></tr>"
    html += f"""</table><p class="warn"><b>Ordering limit:</b> cup requirements can be computed, but order quantity cannot be issued because on-hand, inbound, lead time, shelf life, recipe yield, and stockout data are missing.</p></section>
<section><h2>Recommended actions</h2>"""
    for i, r in enumerate(recommendations, 1):
        html += f"<h3>{i}. {r['title']}</h3><ul><li><b>Action:</b> {r['action']}</li><li><b>Owner / timing:</b> {r['owner']} / {r['timing']}</li><li><b>KPI:</b> {r['kpi']}</li><li><b>Evidence:</b> {r['evidence']}</li></ul>"
    html += f"""<h3>What to add next</h3><p>Capture stock on hand, inbound orders, lead time, shelf life, recipe yield, stockouts, customer/order IDs, and management's gross-profit boundary. These are prerequisites for real purchase quantities, service-level claims, retention, LTV, and a confirmed budget GP variance.</p><p class="footer">Source data version: fruitblend24_v1_c2869ce419bf · metric contract: metric_contract_v1 · final QA status: {qa['status']}</p></section>
</main></body></html>"""
    (OUT / "presentation.html").write_text(html, encoding="utf-8")
    readme = f"""# FruitBlend24 decision dashboard

Run `streamlit run app.py` from the repository root.

The Thai dashboard maps directly to Tasks 1–6 in `question/test.md`. Task 5 separates the released forecast, Kitchen x SKU prep target, scenario P&L, seasonality watch, and profitability hurdle. Its selected `{fmetrics['selected_method']}` forecast has pooled WAPE {pct(float(fmetrics['selected_method_pooled_wape']))}; the seven-day variability buffer is capacity guidance, not physical stock or a purchase order.

Rebuild Task 5 artifacts with `python src/forecast_inventory.py`. Supporting data and QA-passed artifacts remain under `data/processed/` and `reports/fruitblend24_run_001/`.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    return {"output": str(OUT), "charts": [revenue_chart, sku_chart, promo_chart, forecast_chart], "memo": str(OUT / "memo.md"), "presentation": str(OUT / "presentation.html")}


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
