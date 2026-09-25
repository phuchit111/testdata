# FruitBlend24 decision dashboard

Run `streamlit run app.py` from the repository root.

The Thai dashboard maps directly to Tasks 1–6 in `question/test.md`. Task 5 separates the released forecast, Kitchen x SKU prep target, scenario P&L, seasonality watch, and profitability hurdle. Its selected `level_weekday_blend` forecast has pooled WAPE 21.3%; the seven-day variability buffer is capacity guidance, not physical stock or a purchase order.

Rebuild Task 5 artifacts with `python src/forecast_inventory.py`. Supporting data and QA-passed artifacts remain under `data/processed/` and `reports/fruitblend24_run_001/`.
