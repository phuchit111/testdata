# A1 data inventory

Source: `data/raw/FruitBlend24_Intern_Case_Data.xlsx`

| Sheet | Rows excluding header | Columns | Grain / role |
|---|---:|---:|---|
| orders_hourly | 124,397 | 9 | date x hour x kitchen x raw item x rate code; raw sales export |
| weekly_fruit_cost | 239 | 3 | Monday week_start x SKU; fruit cost per cup |
| platform_commission_rate | 2 | 3 | platform code; commission rate |
| waste_daily | 6,570 | 5 | date x kitchen x SKU; recorded discarded cups and cost |
| cost_assumptions | 12 | 4 | first five rows are SKU cost assumptions; remaining rows are kitchen overhead |
| rate_code_dim | 4 | 5 | base rate code dictionary |
| platform_dim | 2 | 2 | platform code dictionary |
| sku_code_dim | 5 | 2 | SKU suffix dictionary |
| monthly_budget | 12 | 4 | company month budget |
| data_dictionary | 33 | 3 | source column definitions |

## Coverage

- Orders cover 2025-09-01 through 2026-08-31.
- The next three forecast months are 2026-09 through 2026-11.
- MixedBerryPremium first appears on 2026-03-01, so it has about six months of history and must not be backfilled with pre-launch zeros.

## Candidate audit checks

- No null order cells, invalid dates, invalid hours, nonpositive units, weekday mismatches, or revenue identity mismatches greater than 0.01 THB.
- No invalid rate-code formats, unknown base codes, or SKU suffix mismatches after candidate decoding.
- Exact row bridge and unit/revenue bridges are released in `data/reconciliation.json`.

## Material limitations

The source has no customer ID, order ID, stock on hand, stockout flag, recipe/BOM, yield, supplier lead time, shelf life, or purchase order. Positive sales rows therefore do not prove that absent hourly rows are zero demand.
