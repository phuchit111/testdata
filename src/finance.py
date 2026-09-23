"""A4 finance and portfolio analysis built on the shared metric contract."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data/processed/fruitblend24_v1_c2869ce419bf"
OUT = ROOT / "reports/fruitblend24_run_001/finance"
COMMERCIAL_OUT = ROOT / "reports/fruitblend24_run_001/commercial"


OVERHEAD = {
    "Pattaya_Central": 180000.0,
    "Pattaya_Beach": 150000.0,
    "BKK_Sukhumvit": 200000.0,
    "BKK_Ladprao": 140000.0,
}


def write(df: pd.DataFrame, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / name, index=False, encoding="utf-8-sig")


def ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Return a safe ratio without converting zero denominators to infinity."""
    return numerator / denominator.where(denominator != 0)


def decorate_pnl(frame: pd.DataFrame) -> pd.DataFrame:
    """Add decision-useful unit economics and margin fields to any P&L grain."""
    frame = frame.copy()
    frame["revenue_per_cup_thb"] = ratio(frame["gross_revenue_thb"], frame["units_sold"])
    frame["realized_price_thb"] = frame["revenue_per_cup_thb"]
    frame["fruit_cost_per_cup_thb"] = ratio(frame["sold_fruit_cost_thb"], frame["units_sold"])
    frame["packaging_cost_per_cup_thb"] = ratio(frame["sold_packaging_cost_thb"], frame["units_sold"])
    frame["labor_cost_per_cup_thb"] = ratio(frame["sold_labor_cost_thb"], frame["units_sold"])
    frame["commission_per_cup_thb"] = ratio(frame["commission_thb"], frame["units_sold"])
    frame["contribution_before_waste_per_cup_thb"] = ratio(frame["contribution_before_waste_thb"], frame["units_sold"])
    frame["contribution_after_waste_per_cup_thb"] = ratio(frame["contribution_after_waste_thb"], frame["units_sold"])
    frame["product_margin_pct"] = ratio(frame["product_margin_thb"], frame["gross_revenue_thb"])
    frame["contribution_margin_pct"] = ratio(frame["contribution_before_waste_thb"], frame["gross_revenue_thb"])
    frame["contribution_after_waste_margin_pct"] = ratio(frame["contribution_after_waste_thb"], frame["gross_revenue_thb"])
    if "modeled_operating_result_thb" in frame.columns:
        frame["operating_margin_pct"] = ratio(frame["modeled_operating_result_thb"], frame["gross_revenue_thb"])
    frame["waste_cost_pct_revenue"] = ratio(frame["waste_cost_thb"], frame["gross_revenue_thb"])
    frame["waste_rate"] = ratio(frame["units_wasted"], frame["units_sold"] + frame["units_wasted"])
    return frame


def sum_pnl(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    grouped = frame.groupby(keys, as_index=False).agg(
        units_sold=("units_sold", "sum"), gross_revenue_thb=("gross_revenue_thb", "sum"),
        sold_fruit_cost_thb=("sold_fruit_cost_thb", "sum"), sold_packaging_cost_thb=("sold_packaging_cost_thb", "sum"),
        sold_labor_cost_thb=("sold_labor_cost_thb", "sum"), commission_thb=("commission_thb", "sum"),
        product_margin_thb=("product_margin_thb", "sum"), contribution_before_waste_thb=("contribution_before_waste_thb", "sum"),
        units_wasted=("units_wasted", "sum"), waste_cost_thb=("waste_cost_thb", "sum"),
    )
    grouped["contribution_after_waste_thb"] = grouped["contribution_before_waste_thb"] - grouped["waste_cost_thb"]
    grouped["realized_price_thb"] = ratio(grouped["gross_revenue_thb"], grouped["units_sold"])
    return decorate_pnl(grouped)


def build() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    daily = pd.read_csv(DATA_DIR / "sales_daily.csv", encoding="utf-8-sig")
    daily["date"] = pd.to_datetime(daily["date"])
    daily["month"] = pd.to_datetime(daily["month"])
    daily["fixed_monthly_overhead_thb"] = daily["kitchen"].map(OVERHEAD)

    pnl_monthly_kitchen = sum_pnl(daily, ["month", "kitchen"])
    pnl_monthly_kitchen["fixed_monthly_overhead_thb"] = pnl_monthly_kitchen["kitchen"].map(OVERHEAD)
    pnl_monthly_kitchen["modeled_operating_result_thb"] = pnl_monthly_kitchen["contribution_after_waste_thb"] - pnl_monthly_kitchen["fixed_monthly_overhead_thb"]
    pnl_monthly_kitchen = decorate_pnl(pnl_monthly_kitchen)
    write(pnl_monthly_kitchen, "pnl_monthly_kitchen.csv")

    pnl_monthly_sku = sum_pnl(daily, ["month", "sku"])
    write(pnl_monthly_sku, "pnl_monthly_sku.csv")

    pnl_monthly_company = pnl_monthly_kitchen.groupby("month", as_index=False).agg(
        units_sold=("units_sold", "sum"), gross_revenue_thb=("gross_revenue_thb", "sum"),
        sold_fruit_cost_thb=("sold_fruit_cost_thb", "sum"), sold_packaging_cost_thb=("sold_packaging_cost_thb", "sum"),
        sold_labor_cost_thb=("sold_labor_cost_thb", "sum"), commission_thb=("commission_thb", "sum"),
        product_margin_thb=("product_margin_thb", "sum"), contribution_before_waste_thb=("contribution_before_waste_thb", "sum"),
        units_wasted=("units_wasted", "sum"), waste_cost_thb=("waste_cost_thb", "sum"),
        fixed_monthly_overhead_thb=("fixed_monthly_overhead_thb", "sum"), modeled_operating_result_thb=("modeled_operating_result_thb", "sum"),
    )
    pnl_monthly_company["contribution_after_waste_thb"] = pnl_monthly_company["contribution_before_waste_thb"] - pnl_monthly_company["waste_cost_thb"]
    pnl_monthly_company = decorate_pnl(pnl_monthly_company)

    budget = pd.read_csv(DATA_DIR / "monthly_budget.csv", encoding="utf-8-sig")
    budget["month"] = pd.to_datetime(budget["month"])
    budget_compare = pnl_monthly_company.merge(budget[["month", "budget_revenue_thb", "budget_gross_profit_thb"]], on="month", how="left", validate="one_to_one")
    budget_compare["revenue_variance_thb"] = budget_compare["gross_revenue_thb"] - budget_compare["budget_revenue_thb"]
    budget_compare["revenue_variance_pct"] = budget_compare["revenue_variance_thb"] / budget_compare["budget_revenue_thb"]
    budget_compare["budget_gp_target_to_revenue_pct"] = ratio(budget_compare["budget_gross_profit_thb"], budget_compare["budget_revenue_thb"])
    budget_compare["budget_gp_comparable"] = False
    budget_compare["budget_gp_note"] = "Diagnostic only: monthly_budget does not define which cost lines are included in gross profit."
    for col in ["product_margin_thb", "contribution_before_waste_thb", "contribution_after_waste_thb", "modeled_operating_result_thb"]:
        budget_compare[f"{col}_vs_budget_gp_thb"] = budget_compare[col] - budget_compare["budget_gross_profit_thb"]
    budget_compare["budget_gp_boundary_status"] = "OPEN: source does not define comparable cost boundary"
    write(budget_compare, "pnl_monthly_company_vs_budget.csv")
    write(pnl_monthly_company, "pnl_monthly_company.csv")

    portfolio = pnl_monthly_sku.groupby("sku", as_index=False).agg(
        units_sold=("units_sold", "sum"), gross_revenue_thb=("gross_revenue_thb", "sum"),
        sold_fruit_cost_thb=("sold_fruit_cost_thb", "sum"), sold_packaging_cost_thb=("sold_packaging_cost_thb", "sum"),
        sold_labor_cost_thb=("sold_labor_cost_thb", "sum"), commission_thb=("commission_thb", "sum"),
        product_margin_thb=("product_margin_thb", "sum"), contribution_before_waste_thb=("contribution_before_waste_thb", "sum"),
        units_wasted=("units_wasted", "sum"), waste_cost_thb=("waste_cost_thb", "sum"),
        contribution_after_waste_thb=("contribution_after_waste_thb", "sum"),
    )
    portfolio = decorate_pnl(portfolio)
    portfolio["revenue_share"] = portfolio["gross_revenue_thb"] / portfolio["gross_revenue_thb"].sum()
    portfolio["contribution_mix"] = portfolio["contribution_after_waste_thb"] / portfolio["contribution_after_waste_thb"].sum()
    volume_median = portfolio["units_sold"].median()
    margin_median = portfolio["contribution_after_waste_margin_pct"].median()
    portfolio["volume_band"] = portfolio["units_sold"].ge(volume_median).map({True: "High volume", False: "Low volume"})
    portfolio["margin_band"] = portfolio["contribution_after_waste_margin_pct"].ge(margin_median).map({True: "High margin", False: "Low margin"})
    portfolio["portfolio_quadrant"] = portfolio["volume_band"] + " + " + portfolio["margin_band"]
    portfolio["profit_rank"] = portfolio["contribution_after_waste_thb"].rank(method="min", ascending=False).astype(int)
    portfolio["action_note"] = portfolio["portfolio_quadrant"].map({
        "High volume + High margin": "Protect availability; test price headroom selectively",
        "High volume + Low margin": "Fix price, promo, commission, or input cost leakage",
        "Low volume + High margin": "Targeted growth opportunity; validate demand pockets",
        "Low volume + Low margin": "Review distribution, waste, and strategic role before rationalizing",
    }).fillna("Use variable contribution and demand evidence; allocated overhead is not a shutdown test")
    portfolio["profit_layer"] = "Contribution after waste; kitchen overhead is not allocated to SKU"
    write(portfolio.sort_values("contribution_after_waste_thb", ascending=False), "portfolio_summary.csv")

    kitchen_summary = pnl_monthly_kitchen.groupby("kitchen", as_index=False).agg(
        units_sold=("units_sold", "sum"), gross_revenue_thb=("gross_revenue_thb", "sum"),
        sold_fruit_cost_thb=("sold_fruit_cost_thb", "sum"), sold_packaging_cost_thb=("sold_packaging_cost_thb", "sum"),
        sold_labor_cost_thb=("sold_labor_cost_thb", "sum"), commission_thb=("commission_thb", "sum"),
        product_margin_thb=("product_margin_thb", "sum"), contribution_before_waste_thb=("contribution_before_waste_thb", "sum"),
        units_wasted=("units_wasted", "sum"), waste_cost_thb=("waste_cost_thb", "sum"),
        contribution_after_waste_thb=("contribution_after_waste_thb", "sum"), fixed_monthly_overhead_thb=("fixed_monthly_overhead_thb", "sum"),
        modeled_operating_result_thb=("modeled_operating_result_thb", "sum"),
    )
    kitchen_summary = decorate_pnl(kitchen_summary)
    kitchen_summary["revenue_share"] = kitchen_summary["gross_revenue_thb"] / kitchen_summary["gross_revenue_thb"].sum()
    kitchen_summary["contribution_mix"] = kitchen_summary["contribution_after_waste_thb"] / kitchen_summary["contribution_after_waste_thb"].sum()
    kitchen_summary["overhead_pct_revenue"] = ratio(kitchen_summary["fixed_monthly_overhead_thb"], kitchen_summary["gross_revenue_thb"])
    kitchen_summary["overhead_per_cup_thb"] = ratio(kitchen_summary["fixed_monthly_overhead_thb"], kitchen_summary["units_sold"])
    kitchen_summary["profit_layer"] = "Operating result after recorded waste and fixed kitchen overhead"
    write(kitchen_summary.sort_values("modeled_operating_result_thb"), "kitchen_summary.csv")

    waste_heatmap = daily.groupby(["kitchen", "sku"], as_index=False).agg(
        units_sold=("units_sold", "sum"), gross_revenue_thb=("gross_revenue_thb", "sum"),
        units_wasted=("units_wasted", "sum"), waste_cost_thb=("waste_cost_thb", "sum"),
    )
    waste_heatmap["waste_rate"] = ratio(waste_heatmap["units_wasted"], waste_heatmap["units_sold"] + waste_heatmap["units_wasted"])
    waste_heatmap["waste_cost_pct_revenue"] = ratio(waste_heatmap["waste_cost_thb"], waste_heatmap["gross_revenue_thb"])
    waste_heatmap["waste_cost_per_wasted_cup_thb"] = ratio(waste_heatmap["waste_cost_thb"], waste_heatmap["units_wasted"])
    write(waste_heatmap.sort_values("waste_rate", ascending=False), "waste_heatmap.csv")

    fruit_cost = pd.read_csv(DATA_DIR / "weekly_fruit_cost.csv", encoding="utf-8-sig")
    fruit_cost["week_start"] = pd.to_datetime(fruit_cost["week_start"])
    fruit_cost = fruit_cost.sort_values(["sku", "week_start"])
    fruit_cost["fruit_cost_change_pct_vs_prior_week"] = fruit_cost.groupby("sku")["fruit_cost_per_cup_thb"].pct_change()
    write(fruit_cost, "fruit_cost_trend.csv")

    sku_kitchen = sum_pnl(daily, ["kitchen", "sku"])
    sku_kitchen["profit_layer"] = "Contribution after waste; overhead intentionally not allocated"
    sku_kitchen = sku_kitchen.sort_values("contribution_after_waste_thb", ascending=False).reset_index(drop=True)
    sku_kitchen["profit_rank"] = sku_kitchen.index + 1
    total_combo_contribution = sku_kitchen["contribution_after_waste_thb"].sum()
    sku_kitchen["contribution_mix"] = sku_kitchen["contribution_after_waste_thb"] / total_combo_contribution
    sku_kitchen["cumulative_contribution_mix"] = sku_kitchen["contribution_mix"].cumsum()
    sku_kitchen["top_20pct_flag"] = sku_kitchen["profit_rank"] <= max(1, round(len(sku_kitchen) * 0.2))
    write(sku_kitchen, "sku_kitchen_pareto.csv")

    waterfall = pd.DataFrame([
        ["Revenue", float(pnl_monthly_company["gross_revenue_thb"].sum())],
        ["Fruit cost", -float(pnl_monthly_company["sold_fruit_cost_thb"].sum())],
        ["Packaging cost", -float(pnl_monthly_company["sold_packaging_cost_thb"].sum())],
        ["Labor cost", -float(pnl_monthly_company["sold_labor_cost_thb"].sum())],
        ["Platform commission", -float(pnl_monthly_company["commission_thb"].sum())],
        ["Contribution before waste", float(pnl_monthly_company["contribution_before_waste_thb"].sum())],
        ["Recorded waste cost", -float(pnl_monthly_company["waste_cost_thb"].sum())],
        ["Contribution after waste", float(pnl_monthly_company["contribution_after_waste_thb"].sum())],
        ["Fixed kitchen overhead", -float(pnl_monthly_company["fixed_monthly_overhead_thb"].sum())],
        ["Modeled operating result", float(pnl_monthly_company["modeled_operating_result_thb"].sum())],
    ], columns=["pnl_component", "thb"])
    waterfall["definition"] = "Metric contract; operating result is contribution after waste less fixed kitchen overhead"
    write(waterfall, "pnl_waterfall.csv")

    diagnostic = pnl_monthly_company.sort_values("month").copy()
    diagnostic["prior_month"] = diagnostic["month"].shift(1)
    diagnostic["prior_units_sold"] = diagnostic["units_sold"].shift(1)
    diagnostic["prior_revenue_thb"] = diagnostic["gross_revenue_thb"].shift(1)
    diagnostic["prior_realized_price_thb"] = diagnostic["realized_price_thb"].shift(1)
    diagnostic["revenue_change_thb"] = diagnostic["gross_revenue_thb"] - diagnostic["prior_revenue_thb"]
    diagnostic["volume_effect_thb"] = (diagnostic["units_sold"] - diagnostic["prior_units_sold"]) * diagnostic["prior_realized_price_thb"]
    diagnostic["price_mix_effect_thb"] = (diagnostic["realized_price_thb"] - diagnostic["prior_realized_price_thb"]) * diagnostic["units_sold"]
    diagnostic["decomposition_check_thb"] = diagnostic["revenue_change_thb"] - diagnostic["volume_effect_thb"] - diagnostic["price_mix_effect_thb"]
    diagnostic["basis"] = "Month-on-month diagnostic; not a direct budget variance decomposition because budget has no cups or price plan"
    write(diagnostic, "revenue_variance_diagnostic.csv")

    company_waste_rate = float(pnl_monthly_company["units_wasted"].sum() / (pnl_monthly_company["units_sold"].sum() + pnl_monthly_company["units_wasted"].sum()))
    cell = waste_heatmap.copy()
    cell["target_waste_units_at_company_rate"] = cell["units_sold"] * company_waste_rate / (1 - company_waste_rate)
    cell["waste_recovery_to_company_avg_thb"] = (cell["waste_cost_thb"] - cell["target_waste_units_at_company_rate"] * cell["waste_cost_per_wasted_cup_thb"]).clip(lower=0)
    waste_recovery = float(cell["waste_recovery_to_company_avg_thb"].sum())
    write(cell.sort_values("waste_recovery_to_company_avg_thb", ascending=False), "waste_recovery_diagnostic.csv")

    promo_recovery = 0.0
    promo_basis = "No promotion efficiency artifact available"
    promo_efficiency_path = COMMERCIAL_OUT / "promo_efficiency_matrix.csv"
    if promo_efficiency_path.exists():
        promo_efficiency = pd.read_csv(promo_efficiency_path, encoding="utf-8-sig")
        promo_recovery = float((-promo_efficiency["incremental_contribution_thb"].clip(upper=0)).sum())
        promo_basis = "Matched promotion screening only; association, before waste, not a guaranteed saving"
    current_operating = float(pnl_monthly_company["modeled_operating_result_thb"].sum())
    scenarios = pd.DataFrame([
        ["Current actual modeled result", current_operating, 0.0, "Observed released sales and recorded costs", "Observed model"],
        ["Promo matched cells revert to standard", current_operating + promo_recovery, promo_recovery, promo_basis, "Screening scenario"],
        ["Waste rate moves toward company average", current_operating + waste_recovery, waste_recovery, "Holding cell waste cost/cup constant; planning sensitivity only", "Planning scenario"],
        ["Combined screening sensitivity", current_operating + promo_recovery + waste_recovery, promo_recovery + waste_recovery, "Adds the two sensitivities; not a causal or budget bridge", "Illustrative scenario"],
    ], columns=["scenario", "modeled_operating_result_thb", "delta_vs_current_thb", "basis", "status"])
    write(scenarios, "finance_scenarios.csv")

    revenue_gap = float(pnl_monthly_company["gross_revenue_thb"].sum() - budget["budget_revenue_thb"].sum())
    gap_plan = pd.DataFrame([
        ["Revenue shortfall vs budget", revenue_gap, "Actual revenue minus budget revenue; not a profit recovery estimate", "Observed vs budget"],
        ["Promo matched-cell recovery", promo_recovery, promo_basis, "Screening scenario"],
        ["Waste-to-company-average recovery", waste_recovery, "Holding waste cost/cup constant; planning sensitivity only", "Planning scenario"],
        ["Combined screened recovery", promo_recovery + waste_recovery, "Sum of the two sensitivities; interaction effects not measured", "Illustrative scenario"],
    ], columns=["gap_or_opportunity", "thb", "basis", "status"])
    write(gap_plan, "gap_closing_plan.csv")

    total = pnl_monthly_company.sum(numeric_only=True)
    metrics = {
        "scope": "A4 historical P&L and portfolio analysis",
        "data_version": "fruitblend24_v1_c2869ce419bf",
        "budget_gp_definition": "OPEN: monthly budget does not define whether GP includes commission, waste, labor, or overhead",
        "historical_revenue_thb": float(total["gross_revenue_thb"]),
        "historical_units_sold": float(total["units_sold"]),
        "historical_product_margin_thb": float(total["product_margin_thb"]),
        "historical_contribution_before_waste_thb": float(total["contribution_before_waste_thb"]),
        "historical_waste_cost_thb": float(total["waste_cost_thb"]),
        "historical_contribution_after_waste_thb": float(total["contribution_after_waste_thb"]),
        "historical_overhead_thb": float(total["fixed_monthly_overhead_thb"]),
        "historical_modeled_operating_result_thb": float(total["modeled_operating_result_thb"]),
        "total_budget_revenue_thb": float(budget["budget_revenue_thb"].sum()),
        "total_revenue_variance_thb": float(budget_compare["revenue_variance_thb"].sum()),
        "historical_contribution_margin_pct": float(total["contribution_before_waste_thb"] / total["gross_revenue_thb"]),
        "historical_contribution_after_waste_margin_pct": float(total["contribution_after_waste_thb"] / total["gross_revenue_thb"]),
        "historical_operating_margin_pct": float(total["modeled_operating_result_thb"] / total["gross_revenue_thb"]),
        "company_waste_rate": company_waste_rate,
        "budget_gp_target_to_revenue_pct": float(budget["budget_gross_profit_thb"].sum() / budget["budget_revenue_thb"].sum()),
        "budget_gp_comparable": False,
        "budget_gp_boundary_status": "OPEN: source does not define whether budget GP includes commission, waste, labor, or overhead",
        "promo_matched_screening_recovery_thb": promo_recovery,
        "waste_to_company_average_recovery_thb": waste_recovery,
        "top_sku_by_contribution_after_waste": str(portfolio.sort_values("contribution_after_waste_thb", ascending=False).iloc[0]["sku"]),
        "lowest_sku_by_contribution_after_waste": str(portfolio.sort_values("contribution_after_waste_thb").iloc[0]["sku"]),
        "lowest_kitchen_by_operating_result": str(kitchen_summary.sort_values("modeled_operating_result_thb").iloc[0]["kitchen"]),
    }
    (OUT / "finance_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
