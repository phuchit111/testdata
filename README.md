# FruitBlend24 Data Project

โปรเจกต์วิเคราะห์ข้อมูลและ Decision Dashboard สำหรับกรณีศึกษา FruitBlend24 โดยเปลี่ยนข้อมูลดิบจาก workbook ให้เป็นข้อมูลที่ตรวจสอบย้อนกลับได้, ตารางวิเคราะห์ด้าน Demand/ราคา/โปรโมชั่น/P&L, Forecast 3 เดือน และแผนเตรียมสินค้าในระดับ Kitchen × SKU

## เริ่มใช้งานอย่างรวดเร็ว

แอปหลักเป็น Streamlit และอ่าน artifacts ที่เผยแพร่แล้วจาก `data/processed/` และ `reports/`

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

จากนั้นเปิด URL ที่ Streamlit แสดงใน terminal โดย entrypoint ที่แนะนำคือ `app.py` ที่รากโปรเจกต์ ซึ่งจะเรียกใช้แอปจาก `deliverables/fruitblend24_run_001/app.py`

## สถานะข้อมูลและผลลัพธ์ล่าสุด

| รายการ | ค่า |
|---|---:|
| Data version | `fruitblend24_v1_c2869ce419bf` |
| ช่วงข้อมูลย้อนหลัง | ก.ย. 2025 – ส.ค. 2026 |
| ช่วง Forecast | ก.ย. 2026 – พ.ย. 2026 |
| รายได้ย้อนหลัง | ฿31,146,933 จาก 618,123 cups |
| งบรายได้รวม | ฿32,400,000; ต่ำกว่างบ ฿1,253,067 |
| ผลดำเนินงานตามแบบจำลอง | -฿403,231 |
| วิธี Forecast ที่เลือก | `level_weekday_blend` (pooled WAPE 21.3%) |
| Forecast ฐาน 3 เดือน | 125,805 cups; เป้าเตรียม 133,400 cups |
| Final QA | ผ่าน; `failed_count: 0` |

ตัวเลขข้างต้นอ้างอิง artifacts ที่ผ่าน QA แล้ว ไม่ใช่การคำนวณใหม่ใน README

## Dashboard มีอะไรบ้าง

แอปภาษาไทยจัดเป็นเส้นทางตัดสินใจสำหรับทีม E-Commerce มี 6 แท็บ ซึ่งเรียงตาม Tasks 1–6 ใน `question/test.md` โดยตรง:

| Task | แท็บ | เนื้อหา |
|---:|---|---|
| 1 | Data Trust & Definitions | Data screening, reconciliation, issue log, assumptions และ QA |
| 2 | Sales, Price & Menu | Demand ตามเวลา/Platform, price ladder และ directional price test ครบ 5 SKU |
| 3 | Platform & Campaign Control | Platform mix, contribution ก่อน Waste, matched historical lift และ break-even guardrail ของ rate code |
| 4 | Portfolio, Kitchen & Budget | P&L, revenue variance เทียบงบ, portfolio, Kitchen × SKU และ Waste |
| 5 | Forecast-to-Kitchen Handoff | Forecast ที่รักษารูปแบบวัน, seasonality watch, scenario P&L, prep target และ capacity buffer ระดับ Kitchen × SKU |
| 6 | E-Commerce Action Center | 3 action สำคัญ, 5 insights และภาพรวม Platform/ช่องว่างกำไร |

ประเด็นหลักที่ Dashboard ช่วยตัดสินใจคือควบคุมโปรโมชั่นด้วย contribution, แก้ `MixedBerryPremium` ก่อนขยาย volume และจัดลำดับการลด Waste ใน `BKK_Ladprao` กับ `BKK_Sukhumvit`

## รัน pipeline ใหม่ทั้งหมด

ให้รันจากโฟลเดอร์รากโปรเจกต์ตามลำดับนี้:

```powershell
python src/prepare.py
python src/qa_data.py
python src/commercial.py
python src/pricing_depth.py
python src/promotion_depth.py
python src/finance.py
python src/forecast_inventory.py
python src/presentation.py
python src/qa_final.py
python src/qa_streamlit.py
```

`src/prepare.py` จะอ่าน `data/raw/FruitBlend24_Intern_Case_Data.xlsx` และสร้าง data release ใหม่ตาม hash ของ source โดยไม่แก้ไขไฟล์ raw เดิม หากรัน pipeline จาก workbook ให้ติดตั้ง dependency เพิ่มถ้ายังไม่มี:

```powershell
python -m pip install openpyxl
```

ลำดับการประมวลผลโดยสรุป:

```text
raw workbook
    ↓
src/prepare.py → data/processed/<data_version>/
    ↓
src/qa_data.py
    ↓
commercial / pricing / promotion / finance / forecast
    ↓
src/presentation.py → deliverables/fruitblend24_run_001/
    ↓
src/qa_final.py → src/qa_streamlit.py
```

## โครงสร้างโฟลเดอร์

| โฟลเดอร์ | เนื้อหา |
|---|---|
| `data/raw/` | Workbook ต้นฉบับ; ไม่แก้ไขทับ |
| `data/processed/` | ข้อมูลที่ทำความสะอาด, metric contract และ assumption ที่ใช้ร่วมกัน |
| `src/` | สคริปต์เตรียมข้อมูล, วิเคราะห์ Commercial/Finance/Forecast, สร้าง presentation และ QA |
| `planning/` | แผนงาน, readiness notes และ profit-recovery analysis |
| `notebooks/` | Notebook สำหรับสำรวจ workflow/readiness |
| `reports/fruitblend24_run_001/` | ตารางผลวิเคราะห์, metrics, scenario, reconciliation และ QA artifacts |
| `deliverables/fruitblend24_run_001/` | Dashboard, memo และ charts สำหรับส่งมอบ |
| `docs/` | รายงานสรุปและคำอธิบายเชิงธุรกิจ |
| `question/` | โจทย์และเกณฑ์ตรวจสอบ |

## ไฟล์ผลลัพธ์สำคัญ

- `deliverables/fruitblend24_run_001/app.py` — Streamlit dashboard ภาษาไทย
- `deliverables/fruitblend24_run_001/memo.md` — Decision memo
- `deliverables/fruitblend24_run_001/charts/` — กราฟประกอบการตัดสินใจ
- `reports/fruitblend24_run_001/data/reconciliation.json` — สะพานตรวจสอบจำนวนแถว, units และรายได้
- `reports/fruitblend24_run_001/inventory/forecast_metrics.json` — วิธี Forecast, backtest และ planning range
- `reports/fruitblend24_run_001/inventory/inventory_policy.csv` — นโยบาย ABC/XYZ ระดับ 20 Kitchen × SKU cells
- `reports/fruitblend24_run_001/inventory/scenario_monthly_pnl.csv` — P&L ในสถานการณ์ 3 เดือน
- `reports/fruitblend24_run_001/qa/checks_final.json` — Final cross-artifact QA
- `reports/fruitblend24_run_001/qa/streamlit_checks.json` — Streamlit smoke/content QA
- `docs/report.md` — รายงานสรุปเชิงธุรกิจแบบละเอียด

## Data quality และการตีความ

จาก raw export 124,397 แถว มีการตัด duplicate ส่วนเกิน 372 แถว และรายการที่ไม่ใช่เมนู 370 แถว เหลือ retained menu rows 123,655 แถว, 618,123 cups และรายได้ ฿31,146,932.57 โดยมี reconciliation และ issue log สำหรับตรวจสอบย้อนกลับ

ควรอ่านตัวเลขโดยคำนึงถึงข้อจำกัดต่อไปนี้:

- ผลโปรโมชั่นเป็น matched association ไม่ใช่ causal uplift เพราะไม่มี randomized assignment, customer ID, stockout และ cannibalization ที่สังเกตได้
- Price simulation เป็น directional scenario โดยใช้สมมติฐาน elasticity ประกอบ ไม่ใช่ causal elasticity
- ขอบเขต GP ใน budget ยังเปิดอยู่ เพราะ source ไม่ระบุว่า budget รวม commission, waste, labor หรือ overhead หรือไม่
- Forecast range เป็น WAPE-based planning range ไม่ใช่ statistical confidence interval และ `MixedBerryPremium` มีประวัติสั้นกว่าสินค้าอื่น
- ยังออก Purchase Order จริงไม่ได้ เพราะไม่มี stock on hand, inbound, supplier lead time, shelf life, BOM/recipe yield และ stockout flags
- Future platform mix ถูกถือคงที่ตาม recent mix; ยังไม่ได้จำลองการเปลี่ยนสัดส่วนช่องทางขาย

รายละเอียดสมมติฐานและข้อจำกัดอยู่ในแท็บ `Data Trust & Definitions`, `docs/report.md` และไฟล์ metrics ใน `reports/fruitblend24_run_001/`

## ตรวจสอบความถูกต้อง

QA ล่าสุดยืนยันว่า:

- data bridge ด้าน rows, units และ revenue reconcile
- Forecast ใช้ข้อมูลก่อน cutoff และไม่มี leakage ใน backtest
- scenario P&L และ overhead reconcile
- Dashboard มีครบทั้ง 6 task tabs และไม่มี exception ใน AppTest
- `reports/fruitblend24_run_001/qa/checks_final.json` และ `streamlit_checks.json` มี `failed_count: 0`
