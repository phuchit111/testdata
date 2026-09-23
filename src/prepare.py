"""Build the shared FruitBlend24 data release from the raw workbook.

This module implements the A2 data-preparation contract from
planning/workflow_plan.th.md.  It never overwrites the source workbook.  The
release keeps raw values, source row ids, exception rows, and explicit cost
status flags so downstream work can distinguish observed values from proxies.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/raw/FruitBlend24_Intern_Case_Data.xlsx"
RUN_ID = "fruitblend24_run_001"
SOURCE_SHA256 = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
DATA_VERSION = f"fruitblend24_v1_{SOURCE_SHA256[:12]}"
METRIC_VERSION = "metric_contract_v1"
ASSUMPTION_VERSION = "assumption_ledger_v1"
OUT = ROOT / "data/processed" / DATA_VERSION
REPORT_DATA = ROOT / "reports" / RUN_ID / "data"


ALIASES = {
    "Watermelon": [
        "Watermelon Ice", "Watermelon smoothy", "Watermelon Smoothie",
        "watermelon ice", "แตงโมปั่นสด", "แตงโมปั่น", "แตงโมปั่น (ไซส์ M)",
    ],
    "Pineapple": [
        "สับปะรดปั่น", "Pineapple Ice", "pineapple ice", "สัปปะรดปั่น",
        "Pineapple Smoothie", "Pineapple smoothie ",
    ],
    "Guava": [
        "Guava Ice", "Guava Smoothie", "ฝรั่งปั่น (ใส่เกลือ)",
        "guava ice", "ฝรั่งปั่น",
    ],
    "PassionFruit": [
        "Passion Fruit Smoothie", "เสาวรสปั่น", "Passion Fruit Ice",
        "เสาวรสปั่นเข้มข้น", "passionfruit ice",
    ],
    "MixedBerryPremium": [
        "เบอร์รี่ปั่นพรีเมียม", "berry premium smoothie", "Mixed Berry (Premium)",
        "เบอร์รี่รวมพรีเมียม", "Mixed Berry Premium",
    ],
}
NAME_TO_SKU = {name: sku for sku, names in ALIASES.items() for name in names}


def read_sheet(sheet_name: str) -> pd.DataFrame:
    return pd.read_excel(SOURCE, sheet_name=sheet_name, engine="openpyxl")


def iso_dates(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
    return df


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_release() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    REPORT_DATA.mkdir(parents=True, exist_ok=True)

    orders = read_sheet("orders_hourly")
    orders.insert(0, "source_row_id", range(2, len(orders) + 2))
    source_cols = [
        "date", "hour", "day_of_week", "kitchen", "item_name_raw",
        "price_thb", "units_sold", "gross_revenue_thb", "rate_code",
    ]
    orders["date"] = pd.to_datetime(orders["date"], errors="coerce").dt.normalize()
    orders["duplicate_key"] = pd.util.hash_pandas_object(orders[source_cols], index=False).astype("uint64").astype(str)
    duplicate_mask = orders.duplicated(source_cols, keep="first")
    duplicate_rows = orders.loc[duplicate_mask].copy()
    duplicate_rows["exception_reason"] = "exact_duplicate"
    deduped = orders.loc[~duplicate_mask].copy()

    deduped["sku"] = deduped["item_name_raw"].map(NAME_TO_SKU)
    non_menu = deduped.loc[deduped["sku"].isna()].copy()
    non_menu["exception_reason"] = "non_menu_or_unmapped_name"
    sales = deduped.loc[deduped["sku"].notna()].copy()

    code = sales["rate_code"].str.extract(r"^(LM|GB)-(RC\d{3})(?:-([A-Z]{2}))?$")
    code.columns = ["platform_code", "base_code", "sku_code"]
    sales = pd.concat([sales, code], axis=1)
    sales["week_start"] = sales["date"] - pd.to_timedelta(sales["date"].dt.dayofweek, unit="D")
    sales["month"] = sales["date"].dt.to_period("M").dt.to_timestamp()

    rate_dim = read_sheet("rate_code_dim")
    platform_dim = read_sheet("platform_dim")
    sku_dim = read_sheet("sku_code_dim")
    fruit = read_sheet("weekly_fruit_cost")
    assumptions = read_sheet("cost_assumptions")
    sku_assumptions = assumptions.loc[assumptions["sku"].isin(ALIASES.keys()), ["sku", "packaging_cost_per_cup_thb", "labor_cost_per_cup_thb", "base_price_thb"]].copy()
    kitchen_overhead = pd.DataFrame({
        "kitchen": ["Pattaya_Central", "Pattaya_Beach", "BKK_Sukhumvit", "BKK_Ladprao"],
        "fixed_monthly_overhead_thb": [180000.0, 150000.0, 200000.0, 140000.0],
        "note": ["rent + utilities + base staff, central kitchen"] * 4,
    })
    commissions = read_sheet("platform_commission_rate")
    budget = read_sheet("monthly_budget")

    rate_dim["discount_pct"] = pd.to_numeric(rate_dim["discount_pct"])
    sales = sales.merge(rate_dim[["base_code", "rate_code_name", "discount_pct"]], on="base_code", how="left", validate="many_to_one")
    sales = sales.merge(platform_dim, on="platform_code", how="left", validate="many_to_one")
    sales = sales.merge(sku_dim.rename(columns={"sku": "sku_from_code"}), on="sku_code", how="left")
    sales = sales.merge(commissions[["platform_code", "commission_rate"]], on="platform_code", how="left", validate="many_to_one")
    sales = sales.merge(assumptions, on="sku", how="left", validate="many_to_one")

    fruit["week_start"] = pd.to_datetime(fruit["week_start"])
    sales = sales.merge(fruit, on=["week_start", "sku"], how="left", validate="many_to_one")
    sales["fruit_cost_raw_thb"] = sales["fruit_cost_per_cup_thb"]

    # Only the launch-day MixedBerryPremium gap is estimated.  The first
    # observed cost after launch is the explicit proxy in the assumption ledger.
    first_available_cost = float(
        fruit.loc[
            (fruit["sku"] == "MixedBerryPremium")
            & (fruit["week_start"] == pd.Timestamp("2026-03-02")),
            "fruit_cost_per_cup_thb",
        ].iloc[0]
    )
    launch_gap = (sales["sku"] == "MixedBerryPremium") & (sales["date"] == pd.Timestamp("2026-03-01"))
    sales["fruit_cost_used_thb"] = sales["fruit_cost_per_cup_thb"]
    sales["fruit_cost_status"] = "observed_exact_week"
    sales.loc[launch_gap & sales["fruit_cost_used_thb"].isna(), "fruit_cost_used_thb"] = first_available_cost
    sales.loc[launch_gap & sales["fruit_cost_raw_thb"].isna(), "fruit_cost_status"] = "estimated_proxy_first_available_week"
    sales.loc[sales["fruit_cost_used_thb"].isna(), "fruit_cost_status"] = "missing_unresolved"

    sales["observed_price_thb"] = sales["price_thb"]
    sales["gross_revenue_calc_thb"] = sales["units_sold"] * sales["observed_price_thb"]
    sales["revenue_gap_thb"] = sales["gross_revenue_thb"] - sales["gross_revenue_calc_thb"]
    sales["commission_thb"] = sales["gross_revenue_thb"] * sales["commission_rate"]
    sales["sold_fruit_cost_thb"] = sales["units_sold"] * sales["fruit_cost_used_thb"]
    sales["sold_packaging_cost_thb"] = sales["units_sold"] * sales["packaging_cost_per_cup_thb"]
    sales["sold_labor_cost_thb"] = sales["units_sold"] * sales["labor_cost_per_cup_thb"]
    sales["product_margin_thb"] = sales["gross_revenue_thb"] - sales["sold_fruit_cost_thb"] - sales["sold_packaging_cost_thb"] - sales["sold_labor_cost_thb"]
    sales["contribution_before_waste_thb"] = sales["product_margin_thb"] - sales["commission_thb"]

    sales_out = sales.drop(columns=["fruit_cost_per_cup_thb"]).copy()
    sales_out = iso_dates(sales_out, ["date", "week_start", "month"])
    write_csv(sales_out, OUT / "sales_clean.csv")

    duplicate_out = duplicate_rows[source_cols + ["source_row_id", "duplicate_key", "exception_reason"]].copy()
    duplicate_out = iso_dates(duplicate_out, ["date"])
    non_menu_out = non_menu[source_cols + ["source_row_id", "duplicate_key", "item_name_raw", "units_sold", "gross_revenue_thb", "exception_reason"]].copy()
    non_menu_out = non_menu_out.loc[:, ~non_menu_out.columns.duplicated()]
    non_menu_out = iso_dates(non_menu_out, ["date"])
    write_csv(duplicate_out, REPORT_DATA / "exceptions_exact_duplicates.csv")
    write_csv(non_menu_out, REPORT_DATA / "exceptions_non_menu.csv")

    # Sales at the daily grain is the only grain used to join daily waste.
    numeric_sales = {
        "units_sold": "sum", "gross_revenue_thb": "sum", "commission_thb": "sum",
        "sold_fruit_cost_thb": "sum", "sold_packaging_cost_thb": "sum",
        "sold_labor_cost_thb": "sum", "product_margin_thb": "sum",
        "contribution_before_waste_thb": "sum",
    }
    sales_daily = sales.groupby(["date", "kitchen", "sku"], as_index=False).agg(numeric_sales)
    sales_daily["realized_price_thb"] = sales_daily["gross_revenue_thb"] / sales_daily["units_sold"]
    sales_daily["week_start"] = sales_daily["date"] - pd.to_timedelta(sales_daily["date"].dt.dayofweek, unit="D")
    sales_daily["month"] = sales_daily["date"].dt.to_period("M").dt.to_timestamp()

    waste = read_sheet("waste_daily")
    waste.insert(0, "source_row_id", range(2, len(waste) + 2))
    waste["date"] = pd.to_datetime(waste["date"], errors="coerce").dt.normalize()
    waste["week_start"] = waste["date"] - pd.to_timedelta(waste["date"].dt.dayofweek, unit="D")
    waste = waste.merge(fruit, on=["week_start", "sku"], how="left", validate="many_to_one")
    waste = waste.merge(assumptions, on="sku", how="left", validate="many_to_one")
    waste = waste.reset_index(drop=True)
    waste["units_wasted"] = pd.to_numeric(waste["units_wasted"], errors="coerce")
    waste["est_waste_cost_thb"] = pd.to_numeric(waste["est_waste_cost_thb"], errors="coerce").astype(float)
    waste["fruit_cost_raw_thb"] = waste["fruit_cost_per_cup_thb"]
    waste["fruit_cost_used_thb"] = waste["fruit_cost_per_cup_thb"]
    waste["waste_cost_raw_thb"] = waste["est_waste_cost_thb"]
    waste["waste_cost_status"] = "observed_estimated_cost"
    waste_launch_gap = (waste["sku"] == "MixedBerryPremium") & (waste["date"] == pd.Timestamp("2026-03-01"))
    waste.loc[waste_launch_gap & waste["fruit_cost_used_thb"].isna(), "fruit_cost_used_thb"] = first_available_cost
    missing_cost = waste["est_waste_cost_thb"].isna()
    estimate_mask = missing_cost & waste["fruit_cost_used_thb"].notna()
    for idx in waste.index[estimate_mask]:
        waste.at[idx, "est_waste_cost_thb"] = float(
            waste.at[idx, "units_wasted"]
            * (waste.at[idx, "fruit_cost_used_thb"] + waste.at[idx, "packaging_cost_per_cup_thb"])
        )
    waste.loc[estimate_mask, "waste_cost_status"] = "estimated_from_fruit_cost_plus_packaging"
    waste.loc[missing_cost & waste["fruit_cost_used_thb"].isna(), "waste_cost_status"] = "missing_unresolved"
    waste_out = waste.drop(columns=["fruit_cost_per_cup_thb"]).copy()
    waste_out = iso_dates(waste_out, ["date", "week_start"])
    write_csv(waste_out, OUT / "waste_clean.csv")

    waste_daily = waste[["date", "kitchen", "sku", "units_wasted", "est_waste_cost_thb", "waste_cost_status"]].copy()
    sales_daily = sales_daily.merge(waste_daily, on=["date", "kitchen", "sku"], how="left", validate="one_to_one")
    # A missing row in waste_daily is treated as no recorded waste for the
    # accounting schedule, while the coverage limitation remains disclosed.
    sales_daily["units_wasted"] = sales_daily["units_wasted"].fillna(0)
    sales_daily["waste_cost_thb"] = sales_daily["est_waste_cost_thb"].fillna(0)
    sales_daily["waste_cost_status"] = sales_daily["waste_cost_status"].fillna("no_waste_row_recorded")
    sales_daily["contribution_after_waste_thb"] = sales_daily["contribution_before_waste_thb"] - sales_daily["waste_cost_thb"]
    sales_daily = iso_dates(sales_daily, ["date", "week_start", "month"])
    write_csv(sales_daily, OUT / "sales_daily.csv")

    # Copy small reference inputs into the version so future analysis can be
    # run without re-reading the workbook for dimensions or budget policy.
    for name, frame in {
        "weekly_fruit_cost": fruit,
        "sku_cost_assumptions": sku_assumptions,
        "kitchen_overhead": kitchen_overhead,
        "platform_commission_rate": commissions,
        "rate_code_dim": rate_dim,
        "platform_dim": platform_dim,
        "sku_code_dim": sku_dim,
        "monthly_budget": budget,
    }.items():
        frame_out = frame.copy()
        frame_out = iso_dates(frame_out, ["week_start", "month"])
        write_csv(frame_out, OUT / f"{name}.csv")

    raw_bridge = {
        "raw_rows": int(len(orders)),
        "duplicate_excess_rows_removed": int(len(duplicate_rows)),
        "non_menu_rows_excluded": int(len(non_menu)),
        "retained_menu_rows": int(len(sales)),
        "raw_units": float(orders["units_sold"].sum()),
        "duplicate_units_removed": float(duplicate_rows["units_sold"].sum()),
        "non_menu_units_excluded": float(non_menu["units_sold"].sum()),
        "retained_menu_units": float(sales["units_sold"].sum()),
        "raw_revenue_thb": float(orders["gross_revenue_thb"].sum()),
        "duplicate_revenue_removed_thb": float(duplicate_rows["gross_revenue_thb"].sum()),
        "non_menu_revenue_excluded_thb": float(non_menu["gross_revenue_thb"].sum()),
        "retained_menu_revenue_thb": float(sales["gross_revenue_thb"].sum()),
    }
    raw_bridge["row_bridge_reconciles"] = raw_bridge["raw_rows"] == raw_bridge["duplicate_excess_rows_removed"] + raw_bridge["non_menu_rows_excluded"] + raw_bridge["retained_menu_rows"]
    raw_bridge["unit_bridge_reconciles"] = abs(raw_bridge["raw_units"] - raw_bridge["duplicate_units_removed"] - raw_bridge["non_menu_units_excluded"] - raw_bridge["retained_menu_units"]) < 1e-9
    raw_bridge["revenue_bridge_reconciles"] = abs(raw_bridge["raw_revenue_thb"] - raw_bridge["duplicate_revenue_removed_thb"] - raw_bridge["non_menu_revenue_excluded_thb"] - raw_bridge["retained_menu_revenue_thb"]) < 0.01

    metrics_contract = {
        "metric_version": METRIC_VERSION,
        "revenue": "sum(gross_revenue_thb) where gross_revenue_thb = units_sold * observed_price_thb; observed price already includes discount",
        "sold_fruit_cost": "sum(units_sold * fruit_cost_used_thb), with source status retained for proxies",
        "sold_packaging_cost": "sum(units_sold * packaging_cost_per_cup_thb)",
        "sold_labor_cost": "sum(units_sold * labor_cost_per_cup_thb)",
        "commission": "sum(gross_revenue_thb * commission_rate)",
        "product_margin": "revenue - sold_fruit_cost - sold_packaging_cost - sold_labor_cost",
        "contribution_before_waste": "product_margin - commission",
        "contribution_after_waste": "contribution_before_waste - waste_cost_thb",
        "modeled_operating_result": "contribution_after_waste - kitchen_monthly_overhead",
        "waste_rate": "units_wasted / (units_sold + units_wasted), disclosed as a planning denominator assumption",
        "cost_boundary_note": "Budget gross profit boundary is not defined in source; show product margin and contribution separately, and label any GP bridge as an assumption.",
    }
    (OUT / "metric_contract.json").write_text(json.dumps(metrics_contract, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "reconciliation.json").write_text(json.dumps(raw_bridge, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest_files = [p for p in OUT.rglob("*") if p.is_file()]
    manifest = {
        "run_id": RUN_ID,
        "source": str(SOURCE),
        "source_sha256": SOURCE_SHA256,
        "data_version": DATA_VERSION,
        "metric_version": METRIC_VERSION,
        "assumption_version": ASSUMPTION_VERSION,
        "files": [{"path": str(p.relative_to(ROOT)), "sha256": sha256(p), "bytes": p.stat().st_size} for p in sorted(manifest_files)],
        "checks": {
            "row_bridge_reconciles": raw_bridge["row_bridge_reconciles"],
            "unit_bridge_reconciles": raw_bridge["unit_bridge_reconciles"],
            "revenue_bridge_reconciles": raw_bridge["revenue_bridge_reconciles"],
            "unknown_platform_codes": sorted(sales["platform_name"].isna().drop_duplicates().astype(str).tolist()) if sales["platform_name"].isna().any() else [],
            "unknown_base_codes": sorted(sales.loc[sales["rate_code_name"].isna(), "base_code"].dropna().unique().tolist()),
            "sku_suffix_mismatch_rows": int((sales["sku_code"].notna() & (sales["sku"] != sales["sku_from_code"])).sum()),
            "missing_fruit_cost_raw_rows": int(sales["fruit_cost_raw_thb"].isna().sum()),
            "estimated_fruit_cost_rows": int((sales["fruit_cost_status"] == "estimated_proxy_first_available_week").sum()),
            "unresolved_fruit_cost_rows": int((sales["fruit_cost_status"] == "missing_unresolved").sum()),
            "missing_waste_cost_raw_rows": int(missing_cost.sum()),
            "estimated_waste_cost_rows": int((waste["waste_cost_status"] == "estimated_from_fruit_cost_plus_packaging").sum()),
            "unresolved_waste_cost_rows": int((waste["waste_cost_status"] == "missing_unresolved").sum()),
        },
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (REPORT_DATA / "reconciliation.json").write_text(json.dumps(raw_bridge, ensure_ascii=False, indent=2), encoding="utf-8")
    (REPORT_DATA / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    result = build_release()
    print(json.dumps({"data_version": result["data_version"], "output_dir": str(OUT), "checks": result["checks"]}, ensure_ascii=False, indent=2))
