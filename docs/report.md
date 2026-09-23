# FruitBlend24 — รายงานสรุปภาพรวมและแนวทางอธิบาย Streamlit Dashboard

> รายงานนี้เป็นสรุปสำหรับใช้ประกอบการนำเสนอ Dashboard และการตัดสินใจทางธุรกิจ โดยอ้างอิงข้อมูลรุ่น `fruitblend24_v1_c2869ce419bf` และผลลัพธ์จาก artifact ที่ผ่าน QA แล้ว

## 1. Executive summary

FruitBlend24 ยังมีความต้องการซื้ออยู่ แต่ผลกำไรถูกกดจากส่วนลด สินค้าที่ contribution ติดลบ Waste และต้นทุนผลไม้ ไม่ใช่ปัญหาเรื่องยอดขายเพียงอย่างเดียว ดังนั้นแนวทางหลักควรเป็น **contribution-first operating plan** คือเลือกยอดขายที่สร้างกำไร คุมโปรโมชั่นตามกำไร และเตรียมสินค้าให้สอดคล้องกับ Demand ราย Kitchen × SKU

ตัวเลขผลการดำเนินงานย้อนหลัง 12 เดือน:

| ตัวชี้วัด | ผลลัพธ์ | ความหมาย |
|---|---:|---|
| Revenue | ฿31,146,933 | รายได้จากรายการเมนูที่ผ่านการคัดกรองแล้ว |
| Units sold | 618,123 cups | ปริมาณขายที่ใช้เป็นฐานวิเคราะห์ |
| Revenue budget | ฿32,400,000 | งบรายได้รวม 12 เดือน |
| Revenue variance | -฿1,253,067 (-3.9%) | รายได้ต่ำกว่างบประมาณ |
| Contribution margin ก่อน Waste | 27.3% | กำไรหลังต้นทุนสินค้า/ค่าคอมมิชชัน/packaging/labor ก่อน Waste |
| Contribution margin หลัง Waste | 24.5% | กำไรหลังหัก Waste แล้ว |
| Fixed overhead | ฿8,040,000 | ค่าใช้จ่ายคงที่ของ Kitchen ทั้งหมด |
| Modeled operating result | -฿403,231 | ผลประกอบการหลังหักต้นทุนและ overhead ตาม model |

ข้อสรุปเชิงบริหารคือ ธุรกิจอยู่ใกล้แผนรายได้มากกว่าจุดคุ้มทุน แต่ยังไม่สามารถแปลงยอดขายเป็นกำไรได้เพียงพอ โดยเฉพาะในสินค้าหรือ Kitchen ที่มี Waste สูงและ contribution ต่ำ

## 2. เส้นทางจากข้อมูลดิบไปสู่ข้อเสนอแนะ

Dashboard ถูกออกแบบให้ผู้ฟังติดตามเหตุผลได้ตามลำดับนี้:

```text
Raw workbook
    ↓
Data quality screening
    ↓
Demand / pricing / promotion analysis
    ↓
Historical P&L and portfolio diagnosis
    ↓
Kitchen × SKU forecast
    ↓
Inventory policy and scenario P&L
    ↓
Business recommendations
```

ตัวเลขแต่ละหน้าจึงไม่ได้เป็นตัวเลขที่แยกกัน แต่เป็นลำดับเหตุผลเดียวกัน ตั้งแต่ตรวจสอบความน่าเชื่อถือของข้อมูล ไปจนถึงการตัดสินใจด้านราคา สินค้า และวัตถุดิบ

## 3. Key insight 1 — Data quality ต้องทำก่อนเชื่อผลวิเคราะห์

ข้อมูล `orders_hourly` เป็น raw platform export จึงต้องจัดการก่อนนำไปคำนวณ:

- Raw rows ทั้งหมด: **124,397 rows**
- Exact duplicate excess rows ที่ลบออก: **372 rows**
- รายการที่ไม่ใช่เมนูและไม่นำไปวิเคราะห์ยอดขาย: **370 rows**
- Retained menu rows: **123,655 rows**
- Duplicate ที่ไม่ถูกลบจะทำให้รายได้ถูกนับเกินประมาณ **฿91,488**

ความหมายทางธุรกิจ: หากไม่ทำความสะอาดก่อน ยอดขาย อัตราโปรโมชั่น และกำไรต่อสินค้าอาจถูกตีความสูงเกินจริง รายงานจึงใช้เฉพาะ retained menu dataset และเก็บ issue log/reconciliation ไว้ตรวจสอบย้อนกลับ

## 4. Key insight 2 — Demand มีรูปแบบตามเวลาและวัน

ผลจากการวิเคราะห์ Demand:

- Peak hour คือประมาณ **22:00 น.** มีประมาณ **53,779 cups**
- วันเสาร์–อาทิตย์รวมกันสร้างรายได้ประมาณ **30.9%**
- Demand มีความแตกต่างตาม Kitchen, SKU, platform, weekday และ hour

ความหมายทางธุรกิจ: ไม่ควรเตรียมวัตถุดิบหรือกำหนดกำลังผลิตเท่ากันทั้งวัน การวางแผนควรเพิ่ม prep capacity ก่อนช่วง Peak และลดการเตรียมล่วงหน้าในช่วง Demand ต่ำ เพื่อป้องกันของเหลือ

## 5. Key insight 3 — Promotion เพิ่มยอดขายได้ แต่ไม่ได้แปลว่าเพิ่มกำไร

Promotion scorecard ดู contribution ต่อแก้ว ไม่ได้ดูยอดขายอย่างเดียว:

| Rate code | Contribution โดยประมาณ |
|---|---:|
| RC000 standard | ฿14.48/cup |
| RC101 | ฿8.02/cup |
| RC102 | ฿6.90/cup |
| RC103 | ฿9.14/cup |

RC102 ให้ contribution ต่ำกว่า standard ประมาณ **฿7.58/cup** แม้อาจช่วยให้เกิดยอดขายหรือการทดลองซื้อเพิ่มขึ้น ดังนั้นผลลัพธ์นี้ควรตีความเป็น association จากข้อมูลที่สังเกตได้ ไม่ใช่ causal uplift เพราะไม่มี randomized assignment หรือ customer ID

แนวทางที่เหมาะสม:

1. ใช้ RC000 เป็น control
2. หยุดหรือจำกัด blanket use ของ RC101 และ RC103
3. เปลี่ยน RC102 เป็น controlled test เช่น new-user, off-peak หรือ platform ที่ต้องการกระตุ้น
4. ให้โปรโมชั่นผ่าน contribution break-even gate ก่อนขยายการใช้งาน

## 6. Key insight 4 — Portfolio และ Kitchen บางส่วนเป็นต้นเหตุของการขาดทุน

### 6.1 สินค้า

`MixedBerryPremium` เป็นรายการที่ต้องแก้ก่อนขยาย:

- Revenue ประมาณ **฿2,439,127**
- Volume ประมาณ **28,044 cups**
- Waste cost ประมาณ **฿334,937**
- Contribution หลัง Waste: **-฿53,860**
- Contribution หลัง Waste ต่อแก้ว: **-฿1.92/cup**
- Waste rate: **20.5%**

ในทางกลับกัน `Watermelon` และ `Pineapple` เป็นแกนหลักของพอร์ต โดยรวมกันคิดเป็นประมาณ **59.8% ของรายได้** และ **71.0% ของ contribution หลัง Waste**

### 6.2 Kitchen

Kitchen ที่ควรได้รับการแก้ไขเร่งด่วน:

| Kitchen | ผลประกอบการที่ modeled | ประเด็น |
|---|---:|---|
| BKK_Ladprao | -฿620,840 | ต่ำสุด และ Waste สูงสุดประมาณ 8.3% |
| BKK_Sukhumvit | -฿486,455 | มี Waste cost ประมาณ ฿193,291 |
| Pattaya Central | +฿371,426 | ผลประกอบการเป็นบวก |
| Pattaya Beach | +฿332,639 | ผลประกอบการเป็นบวก |

ความหมายทางธุรกิจ: ควรเริ่มแก้จาก Kitchen × SKU cells ที่ขาดทุนและ Waste สูง ไม่ใช่ดูเฉพาะ Kitchen ที่มียอดขายสูงที่สุด

## 7. Key insight 5 — 3-month outlook ยังขาดทุน หากไม่ปรับการดำเนินงาน

### 7.1 วิธี Forecast

เปรียบเทียบ 5 วิธีด้วย rolling-origin backtest 4 cutoffs:

- Last-day naive
- Four-week moving average
- Four-week exponential smoothing
- Seasonal naive 7-day
- Eight-week weekday median

วิธีที่เลือกคือ `exp_smoothing_4w` เพราะมี mean WAPE ต่ำสุดที่ **24.2%** โดย forecast ใช้ข้อมูลก่อน cutoff วันที่ **2026-08-31** เท่านั้น จึงไม่ใช้ actual หลังช่วง forecast มาปนกัน

### 7.2 Base forecast Sep–Nov 2026

| ตัวชี้วัด | ผลลัพธ์ |
|---|---:|
| Forecast demand | 126,836 cups |
| Planning range | 96,124–157,548 cups |
| Base prep target รวม expected waste | 134,497 cups |
| Expected waste | 7,662 cups |
| Three-month fixed overhead | ฿2,010,000 |
| Base modeled operating result | -฿777,293 |

Planning range นี้คำนวณจาก WAPE ของวิธีที่เลือก จึงเป็น **ช่วงสำหรับวางแผน** ไม่ใช่ statistical confidence interval

### 7.3 Scenario P&L

| Scenario | ผลประกอบการ Sep–Nov โดยประมาณ | สมมติฐานหลัก |
|---|---:|---|
| Base case | -฿777,293 | ราคาและ Waste ล่าสุด, fruit cost median ล่าสุด |
| Downside case | -฿1,195,606 | Demand ลดตาม WAPE, fruit cost p90, Waste 1.25 เท่า |
| Optimized case | -฿597,324 | ใช้ standard realized price และลด Waste rate 25% |

Optimized case เป็น planning scenario ไม่ใช่การรับประกันผลลัพธ์ และไม่ได้สมมติ causal demand uplift จากการขึ้นราคา

## 8. Inventory policy ที่ Dashboard เสนอ

ระบบคำนวณนโยบายในระดับ **20 Kitchen × SKU cells** โดยใช้:

- **ABC:** จัดกลุ่มจาก contribution หลัง Waste ที่คาดการณ์ใน 3 เดือน
- **XYZ:** จัดกลุ่มจาก demand CV ย้อนหลัง 12 สัปดาห์
  - X: CV ≤ 25%
  - Y: CV ≤ 50%
  - Z: CV > 50%
- Safety stock: เสนอระดับ service level **95%**, `Z = 1.65`
- Review period: **7 วัน**

ผล alert ปัจจุบัน:

- **10 Green:** stable policy
- **6 Amber:** high waste
- **4 Red:** loss + high waste

แนวทางปฏิบัติคือใช้ forecast cups + expected waste เป็น prep target และเปลี่ยนเป็น batch เล็กลง/ถี่ขึ้นใน Amber/Red cells โดยเฉพาะ MixedBerryPremium

สูตรเชิงแนวคิดที่ใช้ใน Dashboard:

```text
target_stock = forecast_during_review_period + safety_stock
order_qty = max(0, target_stock - usable_on_hand - usable_inbound + committed_demand)
```

อย่างไรก็ตาม Dashboard **ยังไม่ออก Purchase Order จริง** เพราะ workbook ไม่มีข้อมูล on-hand, inbound, supplier lead time, shelf life, BOM/recipe yield และ stockout flags การเว้น purchase quantity ไว้จึงเป็นการควบคุมความเสี่ยง ไม่ใช่ข้อมูลขาดหายโดยไม่ตั้งใจ

## 9. ต้นทุนผลไม้และความเสี่ยงต่อกำไร

เมื่อคง Demand, ราคา, Waste rate และ overhead ตาม base case แล้วทดสอบต้นทุนผลไม้:

| Fruit cost uplift | Modeled operating result |
|---:|---:|
| 0% | -฿777,293 |
| +5% | -฿873,599 |
| +10% | -฿969,906 |
| +20% | -฿1,162,518 |

ผลนี้ชี้ว่า Waste reduction และการควบคุม fruit cost มีผลต่อกำไรโดยตรง และควรติดตามเป็น KPI รายสัปดาห์ ไม่ใช่รอให้เห็นผลใน P&L รายเดือนเท่านั้น

## 10. Business recommendations

### Recommendation 1 — Contribution-gated pricing and promotion

**การทำงาน:** ใช้ RC000 เป็น control, จำกัด RC101/RC103 และทดสอบ RC102 เฉพาะ segment/ช่วงเวลาที่ต้องการกระตุ้น

**เหตุผล:** RC102 ให้ contribution ฿6.90/cup เทียบกับ standard ฿14.48/cup

**KPI:** contribution/cup, incremental cups เทียบกับ control, promo waste rate

### Recommendation 2 — Fix MixedBerryPremium before scaling

**การทำงาน:** ทดลอง 4 สัปดาห์โดยปรับราคา Portion และ prep control ลด batch size และไม่ขยาย volume จน contribution หลัง Waste เป็นบวก

**เหตุผล:** สินค้าขาดทุน ฿53,860, ติดลบ ฿1.92/cup และ Waste 20.5%

**KPI:** contribution หลัง Waste > 0, Waste ต่ำกว่า management target, cups sold และ forecast bias

### Recommendation 3 — Operate a weekly Kitchen × SKU prep control

**การทำงาน:** ใช้ `exp_smoothing_4w` เป็น baseline ราย Kitchen × SKU, ตั้ง prep target เป็น forecast + expected waste, review policy ทุก 7 วัน และเริ่มจาก Amber/Red cells

**เหตุผล:** Base outlook มี 126,836 sold cups แต่ต้องเตรียมประมาณ 134,497 cups เมื่อรวม Waste

**KPI:** WAPE ≤ 24.2%, waste rate, forecast bias, service level เมื่อมี stockout data

### Recommendation 4 — Focus recovery on high-impact Kitchen cells

**การทำงาน:** เริ่มที่ BKK_Ladprao และ BKK_Sukhumvit โดยลด Waste และทบทวน price/promo mix ของ cells ที่ contribution ติดลบ

**เหตุผล:** BKK_Ladprao มี modeled operating result ต่ำสุดที่ -฿620,840 และ Waste สูงสุดประมาณ 8.3%

**KPI:** operating result, waste cost/revenue, contribution/cup และ recovery ที่เกิดขึ้นจริงเทียบกับ scenario

## 11. สมมติฐานและข้อจำกัดที่ต้องพูดให้ชัด

1. Revenue ใช้ราคาที่สังเกตได้หลังโปรโมชั่นแล้ว จึงไม่หักส่วนลดซ้ำ
2. P&L ใช้ weekly fruit cost, packaging/labor, platform commission, recorded waste และ monthly kitchen overhead
3. Budget GP boundary ยังเปิดอยู่ เพราะไฟล์ budget ไม่ระบุว่า GP รวม commission, waste, labor หรือ overhead หรือไม่ ดังนั้น `-฿403,231` เป็น modeled operating result ไม่ใช่การยืนยันว่า budget GP variance เท่ากัน
4. Promotion analysis เป็น matched association ไม่ใช่ causal effect เพราะไม่มี customer ID หรือ randomized test
5. Forecast range เป็น WAPE-based planning range ไม่ใช่ confidence interval
6. MixedBerryPremium เป็น recent launch จึงมี active history สั้นกว่า SKU อื่น และไม่มีการเติม zero ก่อนเปิดตัว
7. Future platform commission mix ถูกถือคงที่ตาม recent 56-day SKU-weighted mix; ยังไม่ได้จำลองการเปลี่ยน platform mix
8. Purchase quantity ยังไม่คำนวณจนกว่าจะมี stock on hand, inbound, lead time, shelf life, BOM/yield และ stockout flags

## 12. วิธีอธิบายเว็บแบบสั้นในห้องประชุม

ใช้ลำดับการพูดต่อไปนี้:

> “เว็บนี้เปลี่ยนข้อมูลดิบให้เป็น decision dashboard ตั้งแต่ตรวจสอบข้อมูล Demand ราคา Promotion P&L และ Forecast ไปจนถึง Inventory policy”

> “ภาพรวมคือเรามี Demand แต่กำไรยังติดลบ เพราะส่วนลดบางตัวลด contribution, MixedBerryPremium ขาดทุนหลัง Waste และบาง Kitchen มี Waste สูง”

> “ในช่วง 3 เดือนข้างหน้า Base forecast อยู่ที่ 126,836 cups และ modeled operating result อยู่ที่ -฿777,293 ดังนั้นเป้าหมายไม่ใช่เพิ่มยอดขายทุกวิธี แต่ต้องเพิ่มยอดขายที่สร้าง contribution”

> “ข้อเสนอคือจำกัดโปรโมชั่นที่ contribution ต่ำ, แก้ MixedBerryPremium ก่อน scale และใช้ forecast ราย Kitchen × SKU เพื่อเตรียมวัตถุดิบแบบ smaller and more frequent batches”

> “Inventory policy ในเว็บเป็น prep planning และ safety-stock framework ยังไม่ใช่ purchase order เพราะข้อมูล stock จริงและ supplier lead time ยังไม่มี”

## 13. การตรวจสอบและไฟล์ที่เกี่ยวข้อง

- Streamlit entrypoint: `app.py`
- Dashboard: `deliverables/fruitblend24_run_001/app.py`
- Written decision memo: `deliverables/fruitblend24_run_001/memo.md`
- Forecast metrics: `reports/fruitblend24_run_001/inventory/forecast_metrics.json`
- Inventory policy: `reports/fruitblend24_run_001/inventory/inventory_policy.csv`
- Scenario P&L: `reports/fruitblend24_run_001/inventory/scenario_monthly_pnl.csv`
- QA results: `reports/fruitblend24_run_001/qa/checks_final.json` และ `reports/fruitblend24_run_001/qa/streamlit_checks.json`

ผลการตรวจสอบล่าสุด:

- Python compile ผ่าน
- Streamlit AppTest ผ่านและไม่มี exception
- ครบทั้ง 6 task tabs
- Final QA `failed_count: 0`
- Live Streamlit health บนพอร์ต 8502 เป็น `ok`

รัน Dashboard ด้วยคำสั่ง:

```powershell
streamlit run app.py
```

## 14. สิ่งที่ควรทำต่อหากมีเวลาเพิ่ม

- เพิ่ม stock on hand, inbound และ supplier lead time เพื่อคำนวณ order quantity จริง
- เพิ่ม shelf life และ BOM/recipe yield เพื่อแปลง cups เป็นปริมาณผลไม้จริง
- เพิ่ม stockout flags เพื่อแยก Demand จริงออกจาก Demand ที่ถูกจำกัดด้วยของหมด
- เพิ่ม customer/order IDs เพื่อวัด repeat, retention, CAC/LTV และ causal promotion uplift
- ทำ A/B test โปรโมชั่นโดยกำหนด control และ treatment ชัดเจน
- ทบทวน cost boundary ของ management budget ให้ตรงกับ P&L model

## 15. รายการสำหรับส่งงาน

### ไฟล์วิเคราะห์ทั้งหมด

- `src/` — สคริปต์เตรียมข้อมูล วิเคราะห์ Commercial/Finance/Forecast และ QA
- `data/raw/` — ไฟล์ข้อมูลต้นฉบับ
- `data/processed/` — ข้อมูลที่ทำความสะอาดและตรวจสอบแล้ว
- `reports/fruitblend24_run_001/` — ตารางผลวิเคราะห์, metrics, scenario และ QA artifacts
- `deliverables/fruitblend24_run_001/app.py` — Streamlit decision dashboard
- `deliverables/fruitblend24_run_001/memo.md` — Decision memo
- `deliverables/fruitblend24_run_001/charts/` — กราฟประกอบการวิเคราะห์

### Summary ของ Key Insights

ธุรกิจมีรายได้ย้อนหลัง **฿31.15 ล้านบาท** จาก **618,123 cups** แต่ modeled operating result ยังติดลบ **฿403,231** หลังต้นทุนและ fixed overhead โดยสาเหตุหลักคือ contribution จากโปรโมชั่นต่ำ, `MixedBerryPremium` ขาดทุนหลัง Waste และ Waste สูงในบาง Kitchen โดยเฉพาะ `BKK_Ladprao` ดังนั้นแนวทางหลักคือใช้ contribution-gated promotion, แก้ SKU ที่ขาดทุนก่อน scale และวางแผน prep ราย Kitchen × SKU ตาม Forecast

### Tools / Approach ที่ใช้

- ใช้ **Python, pandas และ NumPy** สำหรับ data cleaning, aggregation, reconciliation, P&L, promotion analysis และ scenario calculation
- ใช้ **matplotlib/SVG** สำหรับสร้างกราฟ Revenue vs Budget, contribution, promotion และ forecast scenarios
- ใช้ **Streamlit** สำหรับสร้าง Dashboard ภาษาไทยและสรุปผลเพื่อการตัดสินใจ
- คัดกรองข้อมูลจาก 124,397 raw rows เหลือ 123,655 retained menu rows หลังลบ duplicate และ non-menu rows
- เปรียบเทียบ Forecast 5 วิธีด้วย rolling-origin backtest และเลือก `exp_smoothing_4w` ที่มี mean WAPE ต่ำสุด 24.2%
- วิเคราะห์โปรโมชั่นแบบ matched association ไม่สรุปเป็น causal uplift เนื่องจากไม่มี customer ID หรือ randomized assignment

### สิ่งที่อยากวิเคราะห์เพิ่มเติมหากมีเวลามากกว่านี้

- เพิ่ม stock on hand, inbound, supplier lead time, shelf life และ BOM/recipe yield เพื่อคำนวณ order quantity และวัตถุดิบจริง
- เพิ่ม stockout flags เพื่อแยก Demand จริงออกจาก Demand ที่ถูกจำกัดด้วยของหมด
- เพิ่ม customer/order IDs เพื่อวิเคราะห์ repeat, retention, CAC/LTV และผลกระทบของโปรโมชั่นในระดับลูกค้า
- ทำ A/B test โปรโมชั่นที่มี control/treatment ชัดเจน เพื่อวัด incremental contribution หลัง Waste
- ทบทวน cost boundary ของ management budget ให้สอดคล้องกับ P&L model
