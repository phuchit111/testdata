# FruitBlend24 decision memo

## Executive decision

FruitBlend24 needs a contribution-first operating plan. The retained menu dataset shows ฿31,146,933 revenue across 618,123 cups, ฿1,253,067 below the ฿32,400,000 12-month revenue budget (-3.9%). After product costs, platform commission, recorded waste, and fixed kitchen overhead, the modeled operating result is ฿-403,231. The budget gross-profit cost boundary is not defined, so the P&L shows the cost layers separately rather than calling this a confirmed budget GP variance.

## Key insights

1. **MixedBerryPremium is not profitable after waste at the observed mix.** It produces ฿-53,860 after waste, or ฿-1.92/cup, with 20.5% waste rate. The action is to fix price/portion and prep controls before scaling.
2. **Discounts trade contribution for observed volume.** Standard rate code contribution is ฿14.48/cup. RC101, RC102, and RC103 are ฿8.02, ฿6.90, and ฿9.14/cup. Matched rows show association, not causal uplift.
3. **The historical business is close to revenue plan but not to operating break-even.** Revenue is below budget by ฿1,253,067, while modeled operating result is negative after ฿8,040,000 fixed overhead. Product decisions should use variable contribution; allocated overhead alone is not a shutdown test.
4. **The original Sep-Nov case horizon remains loss-making under the base forecast.** The selected level-and-weekday blend has pooled backtest WAPE 21.3%. Base modeled operating result totals ฿-785,233. The price-and-waste test improves this to ฿-606,686, but leaves a ฿606,686 gap; its volume equivalent is a hurdle, not a demand target.

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

- **Action:** Use the selected level-and-weekday blend by kitchen and SKU. Set daily prep to forecast cups plus expected waste at Kitchen x SKU grain, review actuals every seven days, and treat the variability buffer as capacity guidance rather than prepared stock. Keep purchase quantity blank until on-hand, inbound, lead time, shelf life, and recipe yield are captured.
- **Owner / timing:** Operations / Supply / Daily prep; weekly review
- **KPI:** Pooled WAPE target at or below 21.3%; waste rate; forecast bias; service level only after lead-time and stockout data exist
- **Evidence:** Selected method is level_weekday_blend with pooled backtest WAPE 21.3%. Base outlook is 125,805 sold cups and 133,400 prep cups for Sep-Nov.

## Method and limitations

- Raw-to-release bridge: 124,397 raw rows → 372 exact duplicate excess rows removed → 370 non-menu rows excluded → 123,655 retained menu rows. Retained revenue is ฿31,146,933 and all row/unit/revenue bridges reconcile.
- Revenue uses observed price already net of the applied promotion. No second discount is deducted.
- Cost uses weekly fruit cost, packaging, labor, platform commission, daily recorded waste, and monthly kitchen overhead. MixedBerry launch-day cost and four waste costs are explicit proxies, not observed values.
- Forecast uses a rolling-origin comparison of six methods, including a blend of the recent exponential level and seven-day weekday profile. The future view is cup-based at Kitchen x SKU grain. The seven-day variability buffer is capacity guidance, not physical stock. Purchase quantity is not calculable because on-hand, inbound, lead time, shelf life, BOM/yield, and stockout inputs are missing.
- Promotion comparisons are matched associations by SKU, platform, weekday, and month. No customer IDs or randomized assignment evidence support retention, CAC, LTV, or causal promo uplift claims.

## Tools and further work

Python with pandas, NumPy, matplotlib, and the bundled workbook reader. Re-run `src/prepare.py`, `src/qa_data.py`, `src/commercial.py`, `src/finance.py`, `src/forecast_inventory.py`, `src/qa_final.py`, then `src/presentation.py`. Next data additions should be stock balances, inbound orders, recipes/yield, shelf life, stockout flags, customer/order IDs, and management's GP boundary.
