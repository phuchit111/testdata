# A6 data-release QA review

Status: **passed**
Data version: `fruitblend24_v1_c2869ce419bf`
Source SHA-256: `c2869ce419bf796bf1351c46b6bdd813a4c35add7031c4e143630858a0a6c6f8`

## Checks

| Check | Result | Expected | Actual |
|---|---|---:|---:|
| source hash matches manifest | PASS | c2869ce419bf796bf1351c46b6bdd813a4c35add7031c4e143630858a0a6c6f8 | c2869ce419bf796bf1351c46b6bdd813a4c35add7031c4e143630858a0a6c6f8 |
| raw row bridge | PASS | True | True |
| raw unit bridge | PASS | True | True |
| raw revenue bridge | PASS | True | True |
| released sales source ids unique | PASS | True | True |
| released sales retain expected rows | PASS | 123655 | 123655 |
| released sales revenue identity | PASS | 0 | 0 |
| released sales daily grain unique | PASS | True | True |
| waste source grain unique | PASS | True | True |
| no unresolved sales fruit cost | PASS | 0 | 0 |
| no unresolved waste cost | PASS | 0 | 0 |
| sales daily revenue reconciles | PASS | 31146932.57 | 31146932.57 |
| sales daily units reconciles | PASS | 618123.0 | 618123.0 |
| launch-day proxy count | PASS | 75 | 75 |
| waste proxy count | PASS | 4 | 4 |

## QA conclusion

The released data version is acceptable for A3/A4 analysis because row, unit, revenue, source-id, daily-grain, and cost-status checks pass. The release does not remove the business limitations around the budget cost boundary, waste coverage, or inventory controls.

## Next owner

A3 Commercial and A4 Finance may now work in parallel from this version. A5 must wait for the demand and finance baseline inputs.
