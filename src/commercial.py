"""A3 commercial analysis: demand, pricing, and promotion evidence tables."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data/processed/fruitblend24_v1_c2869ce419bf"
OUT = ROOT / "reports/fruitblend24_run_001/commercial"


def write(df: pd.DataFrame, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / name, index=False, encoding="utf-8-sig")


def build() -> dict:
    sales = pd.read_csv(DATA_DIR / "sales_clean.csv", encoding="utf-8-sig")
    daily = pd.read_csv(DATA_DIR / "sales_daily.csv", encoding="utf-8-sig")
    rates = pd.read_csv(DATA_DIR / "rate_code_dim.csv", encoding="utf-8-sig")
    sales["date"] = pd.to_datetime(sales["date"])
    sales["month"] = pd.to_datetime(sales["month"])
    sales["day_of_week"] = sales["date"].dt.dayofweek
    sales["hour"] = pd.to_numeric(sales["hour"])
    daily["date"] = pd.to_datetime(daily["date"])
    daily["month"] = pd.to_datetime(daily["month"])

    base_agg = {
        "units_sold": "sum", "gross_revenue_thb": "sum", "commission_thb": "sum",
        "sold_fruit_cost_thb": "sum", "sold_packaging_cost_thb": "sum",
        "sold_labor_cost_thb": "sum", "product_margin_thb": "sum",
        "contribution_before_waste_thb": "sum",
    }

    sku = sales.groupby("sku", as_index=False).agg(base_agg)
    waste_by_sku = daily.groupby("sku", as_index=False).agg(units_wasted=("units_wasted", "sum"), waste_cost_thb=("waste_cost_thb", "sum"))
    sku = sku.merge(waste_by_sku, on="sku", how="left", validate="one_to_one")
    sku["contribution_after_waste_thb"] = sku["contribution_before_waste_thb"] - sku["waste_cost_thb"]
    sku["realized_price_thb"] = sku["gross_revenue_thb"] / sku["units_sold"]
    sku["contribution_before_waste_per_cup_thb"] = sku["contribution_before_waste_thb"] / sku["units_sold"]
    sku["contribution_after_waste_per_cup_thb"] = sku["contribution_after_waste_thb"] / sku["units_sold"]
    sku["waste_rate"] = sku["units_wasted"] / (sku["units_wasted"] + sku["units_sold"])
    sku["revenue_share"] = sku["gross_revenue_thb"] / sku["gross_revenue_thb"].sum()
    write(sku.sort_values("contribution_after_waste_thb", ascending=False), "sku_summary.csv")

    kitchen = sales.groupby("kitchen", as_index=False).agg(base_agg)
    kitchen_waste = daily.groupby("kitchen", as_index=False).agg(units_wasted=("units_wasted", "sum"), waste_cost_thb=("waste_cost_thb", "sum"))
    kitchen = kitchen.merge(kitchen_waste, on="kitchen", how="left", validate="one_to_one")
    kitchen["contribution_after_waste_thb"] = kitchen["contribution_before_waste_thb"] - kitchen["waste_cost_thb"]
    kitchen["realized_price_thb"] = kitchen["gross_revenue_thb"] / kitchen["units_sold"]
    kitchen["contribution_after_waste_per_cup_thb"] = kitchen["contribution_after_waste_thb"] / kitchen["units_sold"]
    kitchen["waste_rate"] = kitchen["units_wasted"] / (kitchen["units_wasted"] + kitchen["units_sold"])
    write(kitchen.sort_values("contribution_after_waste_thb", ascending=False), "kitchen_summary.csv")

    platform = sales.groupby(["platform_code", "platform_name"], as_index=False).agg(base_agg)
    platform["realized_price_thb"] = platform["gross_revenue_thb"] / platform["units_sold"]
    platform["contribution_before_waste_per_cup_thb"] = platform["contribution_before_waste_thb"] / platform["units_sold"]
    platform["revenue_share"] = platform["gross_revenue_thb"] / platform["gross_revenue_thb"].sum()
    write(platform.sort_values("gross_revenue_thb", ascending=False), "platform_summary.csv")

    monthly = sales.groupby("month", as_index=False).agg(base_agg)
    monthly_waste = daily.groupby("month", as_index=False).agg(units_wasted=("units_wasted", "sum"), waste_cost_thb=("waste_cost_thb", "sum"))
    monthly = monthly.merge(monthly_waste, on="month", how="left", validate="one_to_one")
    monthly["contribution_after_waste_thb"] = monthly["contribution_before_waste_thb"] - monthly["waste_cost_thb"]
    monthly["realized_price_thb"] = monthly["gross_revenue_thb"] / monthly["units_sold"]
    monthly["waste_rate"] = monthly["units_wasted"] / (monthly["units_wasted"] + monthly["units_sold"])
    write(monthly, "monthly_demand_value.csv")

    hour = sales.groupby(["hour"], as_index=False).agg(units_sold=("units_sold", "sum"), gross_revenue_thb=("gross_revenue_thb", "sum"))
    hour["revenue_share"] = hour["gross_revenue_thb"] / hour["gross_revenue_thb"].sum()
    write(hour, "hourly_demand.csv")

    weekday = sales.groupby(["day_of_week"], as_index=False).agg(units_sold=("units_sold", "sum"), gross_revenue_thb=("gross_revenue_thb", "sum"))
    weekday["revenue_share"] = weekday["gross_revenue_thb"] / weekday["gross_revenue_thb"].sum()
    write(weekday, "weekday_demand.csv")

    promo = sales.groupby(["base_code", "rate_code_name", "discount_pct"], as_index=False).agg(
        rows=("source_row_id", "size"), units_sold=("units_sold", "sum"), gross_revenue_thb=("gross_revenue_thb", "sum"),
        contribution_before_waste_thb=("contribution_before_waste_thb", "sum"), commission_thb=("commission_thb", "sum"),
    )
    promo["realized_price_thb"] = promo["gross_revenue_thb"] / promo["units_sold"]
    promo["contribution_before_waste_per_cup_thb"] = promo["contribution_before_waste_thb"] / promo["units_sold"]
    promo["revenue_share"] = promo["gross_revenue_thb"] / promo["gross_revenue_thb"].sum()
    write(promo, "promo_summary.csv")

    # Compare promo rows with RC000 only inside SKU x platform x weekday x month
    # strata. This is an association comparator, not a causal estimate.
    sales["stratum"] = sales["sku"].astype(str) + "|" + sales["platform_code"].astype(str) + "|" + sales["day_of_week"].astype(str) + "|" + sales["month"].dt.strftime("%Y-%m")
    standard = sales.loc[sales["base_code"] == "RC000"].groupby("stratum").agg(
        standard_rows=("source_row_id", "size"), standard_avg_units_row=("units_sold", "mean"),
        standard_avg_revenue_row=("gross_revenue_thb", "mean"), standard_contribution_per_cup=("contribution_before_waste_thb", "sum"),
        standard_units=("units_sold", "sum"),
    ).reset_index()
    standard["standard_contribution_per_cup"] = standard["standard_contribution_per_cup"] / standard["standard_units"]
    promoted = sales.loc[sales["base_code"] != "RC000"].groupby(["base_code", "rate_code_name", "discount_pct", "stratum"], as_index=False).agg(
        promoted_rows=("source_row_id", "size"), promoted_avg_units_row=("units_sold", "mean"), promoted_avg_revenue_row=("gross_revenue_thb", "mean"),
        promoted_contribution_per_cup=("contribution_before_waste_thb", "sum"), promoted_units=("units_sold", "sum"),
    )
    promoted["promoted_contribution_per_cup"] = promoted["promoted_contribution_per_cup"] / promoted["promoted_units"]
    comparator = promoted.merge(standard, on="stratum", how="left")
    comparator["association_units_lift_pct"] = comparator["promoted_avg_units_row"] / comparator["standard_avg_units_row"] - 1
    comparator["contribution_per_cup_delta_thb"] = comparator["promoted_contribution_per_cup"] - comparator["standard_contribution_per_cup"]
    comparator["has_standard_comparator"] = comparator["standard_rows"].fillna(0) > 0
    write(comparator.sort_values(["base_code", "has_standard_comparator"], ascending=[True, False]), "promo_comparator_by_stratum.csv")

    # Price floor uses weighted observed fruit, packaging, labour and platform
    # commission. It is a break-even calculation, not a demand elasticity model.
    price = sales.groupby("sku", as_index=False).agg(
        units_sold=("units_sold", "sum"), realized_price_thb=("gross_revenue_thb", lambda s: s.sum()),
        sold_fruit_cost_thb=("sold_fruit_cost_thb", "sum"), sold_packaging_cost_thb=("sold_packaging_cost_thb", "sum"),
        sold_labor_cost_thb=("sold_labor_cost_thb", "sum"), commission_thb=("commission_thb", "sum"),
        contribution_before_waste_thb=("contribution_before_waste_thb", "sum"),
    )
    price["realized_price_thb"] = price["realized_price_thb"] / price["units_sold"]
    price["fruit_cost_per_cup"] = price["sold_fruit_cost_thb"] / price["units_sold"]
    price["packaging_cost_per_cup"] = price["sold_packaging_cost_thb"] / price["units_sold"]
    price["labor_cost_per_cup"] = price["sold_labor_cost_thb"] / price["units_sold"]
    price["commission_rate_weighted"] = price["commission_thb"] / (price["realized_price_thb"] * price["units_sold"])
    price["variable_cost_per_cup_before_commission"] = price[["fruit_cost_per_cup", "packaging_cost_per_cup", "labor_cost_per_cup"]].sum(axis=1)
    price["break_even_price_before_waste_thb"] = price["variable_cost_per_cup_before_commission"] / (1 - price["commission_rate_weighted"])
    price["contribution_before_waste_per_cup_thb"] = price["contribution_before_waste_thb"] / price["units_sold"]
    write(price, "price_floor.csv")

    matched = comparator.loc[comparator["has_standard_comparator"]]
    metrics = {
        "scope": "A3 commercial analysis from verified data version",
        "data_version": "fruitblend24_v1_c2869ce419bf",
        "caution": "Promotion comparisons are matched associations within available strata, not causal uplift. Price variation is largely generated by promo codes, so elasticity is not identified.",
        "promo_rows_with_standard_comparator": int(len(matched)),
        "promo_rows_without_standard_comparator": int((~comparator["has_standard_comparator"]).sum()),
        "top_sku_by_contribution_after_waste": sku.sort_values("contribution_after_waste_thb", ascending=False).iloc[0]["sku"],
        "lowest_sku_by_contribution_after_waste": sku.sort_values("contribution_after_waste_thb", ascending=True).iloc[0]["sku"],
        "peak_hour_by_units": int(hour.sort_values("units_sold", ascending=False).iloc[0]["hour"]),
        "peak_weekday_by_units": int(weekday.sort_values("units_sold", ascending=False).iloc[0]["day_of_week"]),
    }
    (OUT / "commercial_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
