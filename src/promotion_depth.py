"""Task 3 promotion depth: P&L, matched demand lift, and segment decisions.

The raw export contains observed post-promotion revenue. This module keeps that
definition, reconstructs list-price discount spend from the SKU master price,
and compares promotions with a standard-rate control inside matched strata.
The comparison is a screening association, not a causal experiment.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data/processed/fruitblend24_v1_c2869ce419bf"
OUT = ROOT / "reports/fruitblend24_run_001/commercial"
DATA_VERSION = "fruitblend24_v1_c2869ce419bf"


def write(df: pd.DataFrame, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / name, index=False, encoding="utf-8-sig")


def daypart(hour: int) -> str:
    if hour <= 5:
        return "Late Night"
    if hour <= 10:
        return "Morning"
    if hour <= 14:
        return "Lunch"
    if hour <= 17:
        return "Afternoon"
    if hour <= 21:
        return "Dinner"
    return "Late Evening"


def add_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Add comparable demand, contribution, and decision metrics to a match table."""
    out = df.copy()
    out["promo_cups_per_active_hour"] = out["promo_units"] / out["promo_active_hours"].replace(0, np.nan)
    out["baseline_cups_per_active_hour"] = out["baseline_units"] / out["promo_active_hours"].replace(0, np.nan)
    out["actual_demand_lift_pct"] = out["promo_units"] / out["baseline_units"].replace(0, np.nan) - 1
    out["promo_contribution_per_cup_thb"] = out["promo_contribution_thb"] / out["promo_units"].replace(0, np.nan)
    out["baseline_contribution_per_cup_thb"] = out["baseline_contribution_thb"] / out["baseline_units"].replace(0, np.nan)
    out["break_even_lift_pct"] = (
        out["baseline_contribution_per_cup_thb"] / out["promo_contribution_per_cup_thb"].replace(0, np.nan) - 1
    )
    out.loc[out["promo_contribution_per_cup_thb"] <= 0, "break_even_lift_pct"] = np.nan
    out["contribution_lift_pct"] = out["promo_contribution_thb"] / out["baseline_contribution_thb"].replace(0, np.nan) - 1
    out["actual_vs_breakeven_gap_pct"] = out["actual_demand_lift_pct"] - out["break_even_lift_pct"]
    out["promo_roi_on_discount"] = out["incremental_contribution_thb"] / out["promo_discount_cost_thb"].replace(0, np.nan)
    return out


def decision_label(row: pd.Series) -> str:
    if row.get("base_code") == "RC000":
        return "CONTROL / DEFAULT"
    if pd.isna(row.get("actual_demand_lift_pct")):
        return "TEST / NO MATCHED CONTROL"
    if row.get("incremental_contribution_thb", 0) > 0 and row.get("actual_vs_breakeven_gap_pct", -np.inf) >= 0:
        return "KEEP / SCALE SELECTIVELY"
    if row.get("actual_demand_lift_pct", 0) > 0:
        return "OPTIMIZE / TARGET ONLY"
    return "REDUCE / PAUSE BLANKET USE"


def aggregate_matches(matches: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """Aggregate matched promo-vs-standard strata at a business segment level."""
    if matches.empty:
        return pd.DataFrame()
    keys = ["base_code", *group_cols]
    grouped = matches.groupby(keys, as_index=False, observed=True).agg(
        matched_strata=("stratum_id", "nunique"),
        promo_rows=("promo_rows", "sum"),
        promo_units=("promo_units", "sum"),
        promo_active_hours=("promo_active_hours", "sum"),
        baseline_units=("baseline_units", "sum"),
        incremental_units=("incremental_units", "sum"),
        promo_contribution_thb=("promo_contribution_thb", "sum"),
        baseline_contribution_thb=("baseline_contribution_thb", "sum"),
        incremental_contribution_thb=("incremental_contribution_thb", "sum"),
        promo_discount_cost_thb=("promo_discount_cost_thb", "sum"),
    )
    return add_metrics(grouped)


def build() -> dict:
    sales = pd.read_csv(DATA_DIR / "sales_clean.csv", encoding="utf-8-sig")
    rates = pd.read_csv(DATA_DIR / "rate_code_dim.csv", encoding="utf-8-sig")
    sales["date"] = pd.to_datetime(sales["date"])
    sales["month"] = pd.to_datetime(sales["month"])
    sales["hour"] = pd.to_numeric(sales["hour"], errors="coerce").astype(int)
    sales["day_of_week"] = sales["date"].dt.dayofweek
    sales["daypart"] = sales["hour"].map(daypart)
    sales["date_hour"] = sales["date"].dt.strftime("%Y-%m-%d") + "|" + sales["hour"].astype(str)

    # Revenue in the released contract is already post-promotion realized revenue.
    # List-price discount spend is reconstructed only for scoring the promotion.
    sales["list_revenue_thb"] = sales["base_price_thb"] * sales["units_sold"]
    sales["discount_amount_per_cup_thb"] = (sales["base_price_thb"] - sales["observed_price_thb"]).clip(lower=0)
    sales["discount_cost_thb"] = sales["discount_amount_per_cup_thb"] * sales["units_sold"]
    sales["net_revenue_thb"] = sales["gross_revenue_thb"]

    # A code-to-dimension check is kept beside the analysis so a mapping problem
    # cannot silently become a business recommendation.
    known_codes = set(rates["base_code"].astype(str))
    unknown_codes = sorted(set(sales["base_code"].astype(str)) - known_codes)
    revenue_identity_mismatch_rows = int((sales["gross_revenue_thb"] - sales["observed_price_thb"] * sales["units_sold"]).abs().gt(0.01).sum())

    code_dim = rates[["base_code", "rate_code_name", "discount_pct"]].drop_duplicates("base_code")
    total_units = float(sales["units_sold"].sum())
    total_revenue = float(sales["gross_revenue_thb"].sum())

    scorecard = sales.groupby(["base_code"], as_index=False, observed=True).agg(
        rows=("source_row_id", "size"),
        units_sold=("units_sold", "sum"),
        active_hours=("date_hour", "nunique"),
        list_revenue_thb=("list_revenue_thb", "sum"),
        net_revenue_thb=("net_revenue_thb", "sum"),
        discount_cost_thb=("discount_cost_thb", "sum"),
        commission_thb=("commission_thb", "sum"),
        sold_fruit_cost_thb=("sold_fruit_cost_thb", "sum"),
        sold_packaging_cost_thb=("sold_packaging_cost_thb", "sum"),
        sold_labor_cost_thb=("sold_labor_cost_thb", "sum"),
        contribution_before_waste_thb=("contribution_before_waste_thb", "sum"),
    ).merge(code_dim, on="base_code", how="left", validate="one_to_one")
    scorecard["realized_price_thb"] = scorecard["net_revenue_thb"] / scorecard["units_sold"]
    scorecard["list_price_thb"] = scorecard["list_revenue_thb"] / scorecard["units_sold"]
    scorecard["cups_per_active_hour"] = scorecard["units_sold"] / scorecard["active_hours"]
    scorecard["contribution_before_waste_per_cup_thb"] = scorecard["contribution_before_waste_thb"] / scorecard["units_sold"]
    scorecard["contribution_margin_pct"] = scorecard["contribution_before_waste_thb"] / scorecard["net_revenue_thb"]
    scorecard["discount_cost_per_cup_thb"] = scorecard["discount_cost_thb"] / scorecard["units_sold"]
    scorecard["promo_share_cups"] = scorecard["units_sold"] / total_units
    scorecard["revenue_share"] = scorecard["net_revenue_thb"] / total_revenue
    scorecard["control_or_promo"] = np.where(scorecard["base_code"].eq("RC000"), "Control", "Promotion")

    # Match each promo to RC000 inside SKU x kitchen x platform x weekday x month
    # x daypart. The active-hour denominator avoids rewarding a code merely for
    # being switched on longer. It also does not treat absent export rows as zero.
    stratum_cols = ["sku", "kitchen", "platform_code", "platform_name", "day_of_week", "month", "hour", "daypart"]
    sales["stratum_id"] = sales[stratum_cols].astype(str).agg("|".join, axis=1)
    standard = sales.loc[sales["base_code"] == "RC000"].groupby(stratum_cols, as_index=False, observed=True).agg(
        standard_rows=("source_row_id", "size"),
        standard_units=("units_sold", "sum"),
        standard_active_hours=("date_hour", "nunique"),
        standard_contribution_thb=("contribution_before_waste_thb", "sum"),
    )
    standard["standard_cups_per_active_hour"] = standard["standard_units"] / standard["standard_active_hours"]
    standard["standard_contribution_per_cup_thb"] = standard["standard_contribution_thb"] / standard["standard_units"]

    promoted = sales.loc[sales["base_code"] != "RC000"].groupby(
        ["base_code", "rate_code_name", "discount_pct", *stratum_cols], as_index=False, observed=True
    ).agg(
        promo_rows=("source_row_id", "size"),
        promo_units=("units_sold", "sum"),
        promo_active_hours=("date_hour", "nunique"),
        promo_contribution_thb=("contribution_before_waste_thb", "sum"),
        promo_discount_cost_thb=("discount_cost_thb", "sum"),
    )
    matches = promoted.merge(standard, on=stratum_cols, how="left", validate="many_to_one")
    matches["stratum_id"] = matches[stratum_cols].astype(str).agg("|".join, axis=1)
    matches["has_standard_comparator"] = matches["standard_rows"].fillna(0).gt(0)
    matches["baseline_units"] = matches["standard_cups_per_active_hour"] * matches["promo_active_hours"]
    matches["baseline_contribution_thb"] = matches["standard_contribution_per_cup_thb"] * matches["baseline_units"]
    matches["incremental_units"] = matches["promo_units"] - matches["baseline_units"]
    matches["incremental_contribution_thb"] = matches["promo_contribution_thb"] - matches["baseline_contribution_thb"]
    matched = matches.loc[matches["has_standard_comparator"]].copy()
    matched = add_metrics(matched)

    by_code = aggregate_matches(matched, [])
    by_code = by_code.merge(code_dim, on="base_code", how="left", validate="one_to_one", suffixes=("", "_dim"))
    by_code["decision"] = by_code.apply(decision_label, axis=1)
    by_code = by_code.rename(columns={"matched_strata": "matched_strata_count"})
    write(by_code.sort_values("base_code"), "promo_matched_scorecard.csv")
    scorecard = scorecard.merge(by_code[["base_code", "decision"]], on="base_code", how="left", validate="one_to_one")
    scorecard.loc[scorecard["base_code"] == "RC000", "decision"] = "CONTROL / DEFAULT"
    write(scorecard.sort_values("base_code"), "promo_scorecard.csv")

    # Segment views support targeted use instead of a portfolio-wide stop/keep.
    by_sku = aggregate_matches(matched, ["sku"])
    by_kitchen = aggregate_matches(matched, ["kitchen"])
    by_platform = aggregate_matches(matched, ["platform_name"])
    by_hour = aggregate_matches(matched, ["hour"])
    by_daypart = aggregate_matches(matched, ["daypart"])
    by_segment = aggregate_matches(matched, ["sku", "kitchen", "platform_name", "daypart"])
    for df, name in [
        (by_sku, "promo_by_sku.csv"),
        (by_kitchen, "promo_by_kitchen.csv"),
        (by_platform, "promo_by_platform.csv"),
        (by_hour, "promo_by_hour.csv"),
        (by_daypart, "promo_by_daypart.csv"),
        (by_segment, "promo_by_segment.csv"),
    ]:
        if not df.empty:
            df["decision"] = df.apply(decision_label, axis=1)
            write(df.sort_values(["base_code"] + [c for c in df.columns if c in ["sku", "kitchen", "platform_name", "daypart"]]), name)

    # Promotion dependency: how much of each SKU relies on any discount code?
    dep = sales.groupby("sku", as_index=False, observed=True).agg(total_units=("units_sold", "sum"), total_revenue_thb=("gross_revenue_thb", "sum"))
    promo_only = sales.loc[sales["base_code"] != "RC000"].groupby("sku", as_index=False, observed=True).agg(promo_units=("units_sold", "sum"), promo_revenue_thb=("gross_revenue_thb", "sum"))
    dep = dep.merge(promo_only, on="sku", how="left").fillna({"promo_units": 0, "promo_revenue_thb": 0})
    dep["promo_share_cups"] = dep["promo_units"] / dep["total_units"]
    dep["promo_share_revenue"] = dep["promo_revenue_thb"] / dep["total_revenue_thb"]
    for code in sorted(sales.loc[sales["base_code"] != "RC000", "base_code"].unique()):
        code_units = sales.loc[sales["base_code"] == code].groupby("sku")["units_sold"].sum()
        dep[f"{code}_share_cups"] = dep["sku"].map(code_units).fillna(0) / dep["total_units"]
    write(dep.sort_values("promo_share_cups", ascending=False), "promo_dependency_by_sku.csv")

    # Deterministic margin guardrail: for every discount depth, show the demand
    # lift needed to preserve standard-rate contribution. This is a break-even
    # curve, not a claim that the observed lift is causal.
    standard_sku = sales.loc[sales["base_code"] == "RC000"].copy()
    standard_sku["variable_cost_before_commission_thb"] = standard_sku[["sold_fruit_cost_thb", "sold_packaging_cost_thb", "sold_labor_cost_thb"]].sum(axis=1)
    sku_econ = standard_sku.groupby("sku", as_index=False, observed=True).agg(
        list_price_thb=("base_price_thb", "median"),
        standard_units=("units_sold", "sum"),
        standard_contribution_thb=("contribution_before_waste_thb", "sum"),
        variable_cost_before_commission_thb=("variable_cost_before_commission_thb", "sum"),
        commission_thb=("commission_thb", "sum"),
        revenue_thb=("gross_revenue_thb", "sum"),
    )
    sku_econ["standard_contribution_per_cup_thb"] = sku_econ["standard_contribution_thb"] / sku_econ["standard_units"]
    sku_econ["variable_cost_per_cup_thb"] = sku_econ["variable_cost_before_commission_thb"] / sku_econ["standard_units"]
    sku_econ["commission_rate_weighted"] = sku_econ["commission_thb"] / sku_econ["revenue_thb"]
    depth_rows = []
    for _, row in sku_econ.iterrows():
        for depth in [0.00, 0.05, 0.10, 0.15, 0.20, 0.25]:
            effective_price = row["list_price_thb"] * (1 - depth)
            promo_contribution = effective_price * (1 - row["commission_rate_weighted"]) - row["variable_cost_per_cup_thb"]
            required_lift = row["standard_contribution_per_cup_thb"] / promo_contribution - 1 if promo_contribution > 0 else np.nan
            depth_rows.append({
                "sku": row["sku"],
                "discount_pct": depth,
                "list_price_thb": row["list_price_thb"],
                "effective_price_thb": effective_price,
                "standard_contribution_per_cup_thb": row["standard_contribution_per_cup_thb"],
                "promo_contribution_per_cup_thb": promo_contribution,
                "contribution_delta_per_cup_thb": promo_contribution - row["standard_contribution_per_cup_thb"],
                "required_demand_lift_pct": required_lift,
                "commission_rate_weighted": row["commission_rate_weighted"],
            })
    depth = pd.DataFrame(depth_rows)
    write(depth, "promo_depth_breakeven.csv")

    # A tidy table for the efficiency matrix chart: x = demand lift, y =
    # contribution lift, with the required-lift gap retained for explanation.
    efficiency = by_code[[
        "base_code", "rate_code_name", "discount_pct", "promo_units", "promo_active_hours",
        "baseline_units", "actual_demand_lift_pct", "break_even_lift_pct",
        "actual_vs_breakeven_gap_pct", "contribution_lift_pct", "incremental_contribution_thb",
        "promo_discount_cost_thb", "promo_roi_on_discount", "decision",
    ]].copy()
    write(efficiency.sort_values("base_code"), "promo_efficiency_matrix.csv")

    by_code_map = by_code.set_index("base_code")
    metrics = {
        "data_version": DATA_VERSION,
        "scope": "Task 3 promotion P&L, matched active-hour demand lift, break-even guardrails, and targeted segments",
        "caution": "Promotion lift and efficiency are matched associations, not causal estimates. Allocation, customer identity, stockouts, and cannibalization are not observed.",
        "revenue_definition": "net_revenue_thb equals observed gross_revenue_thb; observed revenue is already post-promotion, so discount is not deducted again.",
        "discount_definition": "discount_cost_thb equals (base_price_thb - observed_price_thb) x units_sold, floored at zero after QA.",
        "active_hour_definition": "unique observed date x hour within each SKU x kitchen x platform x weekday x month x hour x daypart stratum; missing export rows are not treated as zero demand.",
        "match_definition": stratum_cols,
        "matched_strata_count": int(len(matched)),
        "promo_share_cups": float(sales.loc[sales["base_code"] != "RC000", "units_sold"].sum() / total_units),
        "discount_cost_total_thb": float(sales.loc[sales["base_code"] != "RC000", "discount_cost_thb"].sum()),
        "unknown_base_codes": unknown_codes,
        "revenue_identity_mismatch_rows": revenue_identity_mismatch_rows,
        "waste_boundary": "Waste is recorded daily by SKU and kitchen, not tagged to rate code; promo P&L is before waste. Company P&L separately subtracts recorded waste.",
        "decision_rule": "Keep/scale selectively only when matched incremental contribution is positive and actual demand lift clears break-even lift; otherwise target, reduce, or pause blanket use.",
        "code_decisions": {code: str(row["decision"]) for code, row in by_code_map.iterrows()},
    }
    (OUT / "promotion_depth_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {
        "data_version": DATA_VERSION,
        "status": "ready_for_review",
        "artifacts": [
            "promo_scorecard.csv", "promo_matched_scorecard.csv", "promo_efficiency_matrix.csv", "promo_by_sku.csv",
            "promo_by_kitchen.csv", "promo_by_platform.csv", "promo_by_daypart.csv",
            "promo_by_hour.csv", "promo_by_segment.csv", "promo_dependency_by_sku.csv", "promo_depth_breakeven.csv",
            "promotion_depth_metrics.json",
        ],
        "checks": [
            "Rate codes decoded from rate_code_dim; unknown codes surfaced.",
            "Observed revenue retained as post-promotion net revenue; discount not double-counted.",
            "Active-hour denominator used inside matched strata.",
            "Demand lift and contribution lift labelled as association, not causal uplift.",
            "Break-even demand lift is a contribution guardrail; promo P&L excludes rate-code-attributed waste.",
        ],
    }
    (OUT / "promotion_depth_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=True, indent=2))
