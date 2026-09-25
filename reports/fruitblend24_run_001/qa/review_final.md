# A6 cross-artifact QA

Status: **passed**

| Check | Result | Expected | Actual | Owner |
|---|---|---:|---:|---|
| historical company P&L has 12 months | PASS | 12 | 12 | A4 |
| historical revenue equals released retained sales | PASS | 31146932.57 | 31146932.57 | A4 |
| budget comparison retains 12 months | PASS | 12 | 12 | A4 |
| forecast horizon only after cutoff | PASS | 2026-09-01 to 2026-11-30 | 2026-09-01 to 2026-11-30 | A5 |
| backtest targets are after each cutoff | PASS | True | True | A5 |
| backtest benchmarks six methods | PASS | ['exp_smoothing_4w', 'level_weekday_blend', 'moving_avg_4w', 'naive_last_day', 'seasonal_naive_7d', 'weekday_median_8w'] | {'methods': ['exp_smoothing_4w', 'level_weekday_blend', 'moving_avg_4w', 'naive_last_day', 'seasonal_naive_7d', 'weekday_median_8w'], 'selected': 'level_weekday_blend'} | A5 |
| forecast uncertainty range is ordered | PASS | True | {'lower_le_base_le_upper': True} | A5 |
| inventory policy covers Kitchen x SKU cells | PASS | 20 cells | {'rows': 20, 'kitchens': 4, 'skus': 5} | A5 |
| Kitchen x SKU prep reconciles to displayed waste rate | PASS | max error < 1e-10 | 1.3877787807814457e-16 | A5 |
| purchase quantity boundary remains explicit | PASS | True | {'all_not_calculable': True, 'limitations': ['No on-hand', 'No inbound', 'No lead time', 'No shelf life', 'No BOM/yield', 'No stockout flags']} | A5 |
| fruit cost stress test declines operating result | PASS | 0/5/10/20% and monotonic decline | {'points': [0.0, 5.0, 10.0, 20.0], 'declines': True} | A5 |
| scenario daily formulas reconcile | PASS | 0 | 4.547473508864641e-13 | A5/A4 |
| scenario monthly revenue rebuild | PASS | 0 | 4.656612873077393e-10 | A5/A4 |
| scenario monthly contribution rebuild | PASS | 0 | 0.0 | A5/A4 |
| scenario overhead charged once per month | PASS | 670000 | [670000.0] | A4 |
| promo summary contains standard and three promo families | PASS | ['RC000', 'RC101', 'RC102', 'RC103'] | ['RC000', 'RC101', 'RC102', 'RC103'] | A3 |
| MixedBerry after-waste contribution is visible | PASS | <0 | -53860.02719999995 | A4 |
| memo exists | PASS | True | True | A7 |
| memo includes three action sections | PASS | >=3 | 3 | A7 |

## Review conclusion

Historical P&L, commercial evidence, backtest coverage, forecast horizon, and scenario aggregation reconcile. The recommendation layer must preserve the three limitations above and must not recalculate metrics independently.
