# FruitBlend24 — Analyst Case Study
## Revenue Management / Data Analyst Intern Assessment

---

## 1. Background

FruitBlend24 is a fresh fruit smoothie brand with no physical storefront — it sells 100% online, exclusively through LINE MAN and Grab, and operates 24 hours a day. It runs out of 4 central kitchens: Pattaya_Central, Pattaya_Beach, BKK_Sukhumvit, and BKK_Ladprao.

The core menu has 5 items: Watermelon, Pineapple, Guava, Passion Fruit, and a recently-launched premium item, Mixed Berry Premium (imported ingredients, higher price point).

Management wants you, acting as a Revenue/Data Analyst, to analyze 12 months of historical data and recommend how to increase profitability and manage inventory more effectively.

---

## 2. Data Provided

The file `FruitBlend24_Intern_Case_Data.xlsx` contains:

- **orders_hourly** — raw hourly order export by kitchen and product, with selling price, revenue, and the rate/promo code applied
- **rate_code_dim, platform_dim, sku_code_dim** — reference tables to help decode the rate/promo code applied to each order
- **weekly_fruit_cost** — raw fruit cost per cup, by SKU, by week
- **platform_commission_rate** — commission rate charged by each delivery platform
- **waste_daily** — cups wasted/discarded per kitchen per SKU per day, with an estimated cost of that waste
- **monthly_budget** — the company-wide monthly revenue and gross profit budget set by management
- **cost_assumptions** — fixed packaging/labor cost per cup per SKU, and fixed monthly overhead per kitchen
- **data_dictionary** — column definitions for every sheet

> **Note:** orders_hourly is a raw export exactly as it comes out of the platform — treat it accordingly.  
> **Note:** all data is synthetic, generated specifically for this assessment.

---

## 3. Tasks

There is no single correct method — use your own judgment to choose the right tools and approach, and to decide how deep to go on each task. Your final recommendations must be backed by clear, numeric evidence. There are 6 tasks:

1. **Data quality:** assess the raw data and handle whatever issues you find before relying on it for analysis.
2. **Demand & pricing:** understand how demand behaves, and assess whether current pricing is right for each item.
3. **Promotions & rate codes:** assess whether the promo/rate codes currently in use are worth running, and recommend changes.
4. **Portfolio & budget performance:** there is no pre-built P&L in this workbook — put one together yourself from the underlying data, then compare it to the monthly budget and decide which item(s) or kitchens need action, with clear numeric justification.
5. **Inventory & 3-month outlook:** propose an ordering approach that matches demand and minimizes waste, and project inventory needs and P&L for the next 3 months along with a plan to stay profitable. Any forecasting approach is fine — a simple, well-reasoned method is just as acceptable as a formal model.
6. **Present your findings:** package everything into an output that could actually drive a business decision. Choose whichever format you're best at.

---

## 4. Deliverable Format

Your final output must take one of these two forms:

- A working Python app that presents your analysis (e.g. built and deployed with Streamlit), or
- A slide/document presentation of your findings

Whichever you choose, it must include:

- 3-5 key insights, supported by charts or tables
- At least 3 actionable business recommendations, covering pricing, portfolio, and inventory
- The reasoning and assumptions behind your numbers — you should be able to explain why you reached each conclusion

---

## 5. Timeline

You have 7 days from receiving this case to complete and submit your work.

---

## 6. Submission

Submit all work product (your analysis files plus a summary of insights), along with a short note on the tools/approach you used, and what you'd explore further with more time.

Enjoy the case — there is no single correct answer. What matters most is your thought process and the reasoning behind your recommendations.
