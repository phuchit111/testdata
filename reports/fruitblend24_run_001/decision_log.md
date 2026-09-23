# FruitBlend24 decision log

## A0 decisions

- Scope actuals to 1 Sep 2025–31 Aug 2026. Forecast 1 Sep–30 Nov 2026.
- Release one shared data version before starting the commercial, finance, and forecast branches.
- Keep the raw workbook read-only. All transformations are reproducible through `src/prepare.py`.
- Treat budget gross profit as undefined until management confirms its cost boundary. Show multiple contribution layers instead of silently forcing a definition.
- Separate observed outcomes from association and scenario assumptions. Do not use revenue during promotion as causal uplift without a comparable assignment design.

## A1 findings carried into A2

- 372 exact duplicate excess order rows.
- 370 deduplicated non-menu rows, consisting of 134 experimental drink rows, 122 Combo Set A rows, and 114 empty-cup rows.
- 75 menu sales rows without an exact-week fruit cost, all attributable to the 1 Mar 2026 MixedBerryPremium launch-day gap.
- Four waste rows with missing estimated cost covering 96 cups.
- No null order fields, invalid dates/hours, weekday mismatches, revenue identity mismatches, unknown rate codes, or SKU suffix mismatches in the candidate audit.

## A2 release

`fruitblend24_v1_c2869ce419bf` is released for the next QA step. It includes clean sales, daily sales, clean waste, exception tables, a reconciliation bridge, a metric contract, and a manifest with hashes. The release uses the explicit proxies in `assumptions.json`; it is not a claim that the source data has no limitations.
