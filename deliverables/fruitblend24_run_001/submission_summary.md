# FruitBlend24 — Submission Summary

## 1. ไฟล์ที่ส่งมอบ

ชุดงานประกอบด้วยไฟล์หลักต่อไปนี้:

- `memo.md` — Decision memo และข้อเสนอแนะเชิงธุรกิจ
- `app.py` — Streamlit decision dashboard
- `charts/` — กราฟประกอบการวิเคราะห์
- `../../docs/report.md` — รายงานสรุปฉบับเต็ม
- `../../src/` — สคริปต์เตรียมข้อมูล วิเคราะห์ Forecast และ QA
- `../../data/processed/` — ข้อมูลที่ผ่านการทำความสะอาดและตรวจสอบแล้ว
- `../../reports/fruitblend24_run_001/` — ผลลัพธ์เชิงตาราง, metrics, scenario และ QA artifacts

เปิด Dashboard จากโฟลเดอร์โปรเจกต์ด้วย:

```powershell
streamlit run app.py
```

## 2. Key Insights

1. รายได้ย้อนหลังอยู่ที่ **฿31.15 ล้านบาท** จาก **618,123 cups** ต่ำกว่างบรายได้ ฿32.40 ล้านบาทประมาณ **3.9%** แต่ผลประกอบการตามแบบจำลองอยู่ที่ **-฿403,231** หลังต้นทุนและ fixed overhead
2. `MixedBerryPremium` เป็น SKU ที่ต้องแก้ก่อนขยาย: contribution หลัง Waste **-฿53,860**, หรือ **-฿1.92/cup**, และ Waste rate **20.5%**
3. โปรโมชั่นทำให้ contribution ต่อแก้วลดลงเมื่อเทียบกับ standard: RC000 **฿14.48/cup**, RC101 **฿8.02**, RC102 **฿6.90**, RC103 **฿9.14** จึงควรใช้โปรโมชั่นแบบมีเงื่อนไขและทดสอบกับ control
4. `Watermelon` และ `Pineapple` เป็นตัวขับเคลื่อนหลักของพอร์ต คิดเป็นประมาณ **59.8% ของรายได้** และ **71.0% ของ contribution หลัง Waste**
5. จุดที่ควรเร่งแก้คือ `BKK_Ladprao` ซึ่งมี modeled operating result **-฿620,840** และ Waste rate สูงสุดประมาณ **8.3%**; `BKK_Sukhumvit` เป็นอีกจุดที่ต้องติดตาม
6. Forecast Sep–Nov 2026 แบบฐานคาดการณ์ **125,805 cups** และ modeled operating result **-฿785,233**; price + Waste test ยังมีช่องว่างสู่คุ้มทุน **฿606,686** จึงควรพิสูจน์ contribution, Waste และต้นทุนทีละคันโยกแทนการสร้างเป้ายอดขายย้อนกลับ

## 3. Tools / Approach

- **Python** สำหรับ workflow ทั้งหมด ตั้งแต่เตรียมข้อมูล คำนวณ metrics, P&L, promotion, forecast และ QA
- **pandas / NumPy** สำหรับ data cleaning, aggregation, reconciliation และ scenario calculation
- **matplotlib / SVG charts** สำหรับสร้างกราฟสรุป Revenue vs Budget, contribution, promotion และ forecast scenarios
- **Streamlit** สำหรับสร้าง decision dashboard ภาษาไทยแบบหลายแท็บ
- คัดกรองข้อมูลจาก raw workbook: 124,397 rows → ลบ exact duplicate excess 372 rows → ตัด non-menu 370 rows → เหลือ retained menu rows 123,655 rows
- เปรียบเทียบ Forecast 6 วิธีด้วย rolling-origin backtest 4 cutoffs และเลือก `level_weekday_blend` ซึ่งมี pooled WAPE ต่ำสุด **21.3%**
- ทำ P&L ในระดับบริษัท, Kitchen และ SKU โดยแยก product cost, packaging/labor, platform commission, waste และ fixed overhead
- วิเคราะห์โปรโมชั่นแบบ matched association ตาม SKU, platform, weekday และ month; ไม่ตีความเป็น causal uplift
- ทำ prep policy ในระดับ Kitchen × SKU 20 cells โดยใช้ ABC, trend-aware XYZ และ 7-day capacity buffer; ไม่อ้าง service level หรือ Purchase Order เมื่อยังไม่มี lead time/stockout data

## 4. ข้อจำกัดสำคัญ

- Budget gross-profit cost boundary ไม่ได้ระบุชัด จึงรายงานเป็น **modeled operating result** ไม่ใช่การยืนยัน budget GP variance
- Promotion analysis เป็น association จากข้อมูลสังเกตการณ์ เพราะไม่มี customer ID หรือ randomized assignment
- Forecast range เป็น WAPE-based planning range ไม่ใช่ confidence interval
- ยังไม่สามารถคำนวณ purchase order จริงได้ เพราะไม่มี stock on hand, inbound, supplier lead time, shelf life, BOM/recipe yield และ stockout flags

## 5. สิ่งที่อยากวิเคราะห์เพิ่มเติมหากมีเวลา

- เพิ่ม stock on hand, inbound และ supplier lead time เพื่อคำนวณ order quantity จริง
- เพิ่ม BOM/recipe yield และ shelf life เพื่อแปลง forecast cups เป็นวัตถุดิบและลดของเสีย
- เพิ่ม stockout flags เพื่อแยก demand จริงออกจาก demand ที่ถูกจำกัดด้วยของหมด
- เพิ่ม customer/order IDs เพื่อวิเคราะห์ repeat, retention, CAC/LTV และ customer-level promotion impact
- ทำ A/B test โปรโมชั่นโดยกำหนด control/treatment ชัดเจน และวัด incremental contribution หลัง Waste
- ทบทวน cost boundary ของ management budget ให้สอดคล้องกับ P&L model

## 6. QA Status

Final QA ผ่านทั้งหมด (`failed_count: 0`) และตรวจสอบแล้วว่า historical P&L, budget comparison, forecast horizon, inventory coverage, scenario formulas, promotion summary และ memo สอดคล้องกัน
