# FruitBlend24 decision memo

## Executive decision

FruitBlend24 needs a contribution-first operating plan. The retained menu dataset shows ฿31,146,933 revenue across 618,123 cups, ฿1,253,067 below the ฿32,400,000 12-month revenue budget (-3.9%). After product costs, platform commission, recorded waste, and fixed kitchen overhead, the modeled operating result is ฿-403,231. The budget gross-profit cost boundary is not defined, so the P&L shows the cost layers separately rather than calling this a confirmed budget GP variance.

## Key insights

1. **MixedBerryPremium is not profitable after waste at the observed mix.** It produces ฿-53,860 after waste, or ฿-1.92/cup, with 20.5% waste rate. The action is to fix price/portion and prep controls before scaling.
2. **Discounts trade contribution for observed volume.** Standard rate code contribution is ฿14.48/cup. RC101, RC102, and RC103 are ฿8.02, ฿6.90, and ฿9.14/cup. Matched rows show association, not causal uplift.
3. **The historical business is close to revenue plan but not to operating break-even.** Revenue is below budget by ฿1,253,067, contribution margin is 27.3% before waste and 24.5% after waste, but modeled operating result is ฿-403,231 after ฿8,040,000 fixed overhead (-1.3% operating margin). Product decisions should use variable contribution; allocated overhead alone is not a shutdown test.
4. **The portfolio is concentrated in two core profit drivers, while the premium SKU destroys contribution after waste.** Watermelon and Pineapple represent 59.8% of revenue but 71.0% of contribution after waste. MixedBerryPremium is the only negative-contribution SKU at ฿-53,860, with 20.5% waste; PassionFruit is positive but lower-margin at 17.9% after-waste contribution margin.
5. **Kitchen action should focus on BKK Ladprao and BKK Sukhumvit, not only the largest-revenue kitchen.** BKK Ladprao has the lowest modeled operating result at ฿-620,840 and the highest waste rate at 8.3%; BKK Sukhumvit is ฿-486,455 after ฿193,291 waste. Pattaya Central and Pattaya Beach remain positive at ฿371,426 and ฿332,639 respectively.
6. **The next three months remain loss-making under the base forecast.** Exponential smoothing over the latest four weeks has the lowest mean rolling-origin WAPE at 24.2% across five tested methods. Base Sep-Nov demand is 126,836 cups, with a WAPE-based planning range of 96,124–157,548 cups; modeled operating result is ฿-777,293 after ฿2,010,000 three-month overhead. The optimized case improves the same forecast through standard pricing and a 25% waste-rate reduction, but is still a planning scenario rather than a guaranteed result.

## Recommendations

### 1. Gate discounts by contribution, not volume alone

- **Action:** Pause blanket use of RC101/RC103 and redesign RC102 as a controlled test. Keep the matched standard comparator, require incremental cups to clear the break-even lift, and report contribution after commission.
- **Owner / timing:** Commercial / Growth / Next 2-week campaign cycle
- **KPI:** Contribution/cup, incremental cups vs matched control, promo waste rate
- **Evidence:** Standard contribution is ฿14.48/cup vs ฿6.90/cup for RC102. Association is not causation.

### 2. Fix MixedBerryPremium before scaling it

- **Action:** Run a 4-week price/portion and prep-control pilot. Do not expand volume until post-waste contribution is positive and waste is below a management-set threshold.
- **Owner / timing:** Category + Kitchen Operations / Start within 1 week; review weekly
- **KPI:** Post-waste contribution/cup > 0, waste rate < 10% pilot target, cups sold, repeat demand once IDs exist
- **Evidence:** 28,044 cups and ฿2,439,127 revenue still produce ฿-53,860 after ฿334,937 waste cost; waste rate is 20.5%.

### 3. Run a weekly cup-based prep control

- **Action:** Use the selected exponential-smoothing baseline by kitchen and SKU. Set daily prep to forecast cups plus expected waste, review the 95% service-level safety-stock policy weekly, and monitor actual vs forecast. Keep purchase quantity blank until on-hand, inbound, lead time, shelf life, and recipe yield are captured.
- **Owner / timing:** Operations / Supply / Daily prep; weekly review
- **KPI:** WAPE target at or below 24.2%; waste rate; forecast bias; service level after stockout data exists
- **Evidence:** Five methods were benchmarked across four rolling cutoffs; `exp_smoothing_4w` selected with mean WAPE 24.2%. Base outlook is 126,836 sold cups and 134,497 prep cups for Sep-Nov; the planning range is 96,124–157,548 sold cups.

### 4. Close the P&L gap with measured recovery, not a sales-only target

- **Action:** Prioritize BKK Ladprao waste-cell reduction and matched-promo redesign before adding blanket volume. Use the dashboard's ฿110,214 matched-promo recovery and ฿347,811 waste-to-company-average sensitivity as planning caps, then validate actual savings weekly.
- **Owner / timing:** Finance + Commercial + Operations / weekly P&L review
- **KPI:** Operating result, waste cost/revenue, contribution/cup, promo incremental contribution versus RC000
- **Evidence:** The historical operating result is ฿-403,231; the two screened sensitivities total ฿458,024, but both are explicitly non-causal planning scenarios.

## Method and limitations

- Raw-to-release bridge: 124,397 raw rows → 372 exact duplicate excess rows removed → 370 non-menu rows excluded → 123,655 retained menu rows. Retained revenue is ฿31,146,933 and all row/unit/revenue bridges reconcile.
- Revenue uses observed price already net of the applied promotion. No second discount is deducted.
- Cost uses weekly fruit cost, packaging, labor, platform commission, daily recorded waste, and monthly kitchen overhead. MixedBerry launch-day cost and four waste costs are explicit proxies, not observed values.
- The finance layer includes product-level contribution, kitchen-level operating profit, contribution margin %, revenue/profit mix, kitchen × SKU waste heatmap, weekly fruit-cost trend, SKU × kitchen Pareto, and a month-on-month price/mix versus volume diagnostic. Budget gross profit is not directly comparable because the source dictionary and budget sheet do not define its cost boundary.
- Forecast uses a rolling-origin comparison of five methods: last-day naive, four-week moving average, four-week exponential smoothing, seasonal-naive 7-day, and eight-week weekday median. The future view is cup-based at Kitchen × SKU level. Lower/upper demand bounds use selected-method WAPE as a planning range, not a confidence interval. Inventory policy uses recent 12-week demand CV for XYZ, positive contribution after waste for ABC, and a proposed 95% service level / Z=1.65 / seven-day review assumption. Purchase quantity is not calculable from the provided case because on-hand, inbound, lead time, shelf life, BOM/yield, and stockout inputs are missing.
- The fruit-cost stress test holds base demand, pricing, waste rate, and overhead constant while testing +5%, +10%, and +20% fruit-cost uplifts. Base 3-month operating result is ฿-777,293 and falls to approximately ฿-1,162,518 at +20%; this is a sensitivity, not a commodity forecast.
- Promotion comparisons are matched associations by SKU, platform, weekday, and month. No customer IDs or randomized assignment evidence support retention, CAC, LTV, or causal promo uplift claims.

## Tools and further work

Python with pandas, NumPy, matplotlib, and the bundled workbook reader. Re-run `src/prepare.py`, `src/qa_data.py`, `src/commercial.py`, `src/finance.py`, `src/forecast_inventory.py`, `src/qa_final.py`, then `src/presentation.py`. Next data additions should be stock balances, inbound orders, recipes/yield, shelf life, stockout flags, customer/order IDs, and management's GP boundary.
