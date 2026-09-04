# เอกสารสูตร KPI สำหรับทีม IT: ระบบ GP Analysis Dashboard & Transaction Audit (สำหรับทีม IT)

สถานะ: CURRENT — ตรวจจากโค้ดจริง [`F:\lost-Product\build_gp_analysis.py`, `F:\lost-Product\gp_analysis_dashboard.html`, `F:\lost-Product\gp_analysis_data.json`] [2026-09-04]

---

## 0. หลักการที่ต้องเข้าใจก่อนอ่านสูตร

### 0.1 หน้านี้คืออะไรในเชิงธุรกิจ
ระบบนี้คือ **Gross Profit (GP) Recovery & Monitoring Engine** ของเครือข่ายร้านค้าปลีก (จำนวน 202 สาขาในฐานข้อมูลปัจจุบัน) พัฒนาขึ้นเพื่อรับมือกับวิกฤตอัตรากำไรขั้นต้น (GP%) ที่ร่วงลงอย่างรวดเร็วจาก **31.5% ในเดือนสิงหาคม 2026 (2026-08)** ลงมาอยู่ที่ **24.2% ในเดือนกันยายน 2026 (2026-09 MTD)** 

สาเหตุทางธุรกิจที่ระบบนี้ถูกสร้างขึ้นมาจับโดยเฉพาะประกอบด้วย 4 ปัจจัยหลัก:
1. **วิกฤตสินค้าเทศกาล (Category 22: Festival Goods):** สาขานำสินค้ากลุ่มนี้ไปแจกเป็นของแถมหรือยิงขายในราคา ฿0 หรือให้ส่วนลด 100% ทำให้ระบบตัดต้นทุนสินค้า (COGS) เต็มจำนวนโดยไม่มียอดขายมาชดเชย ส่งผลกระทบกด GP รวมของบริษัทลดลงถึง **-7.09 percentage points (pp)**
2. **โครงสร้างกำไร Minimart (Category 02):** มีสัดส่วนยอดขายสูงแต่มาร์จิ้นต่ำกว่าเกณฑ์ปกติ กดดัน GP รวมอีก **-3.69 pp**
3. **การทุจริต/ข้อผิดพลาดระดับบิล (Transaction Anomalies):** แคชเชียร์ยิงขายของแถม ฿0, ให้ส่วนลดผิดเกณฑ์ (>50%), หรือตั้งราคาทุนสูงกว่าราคาขายป้าย
4. **การปนเปื้อนของร้าน Online (สาขา 901):** มีโมเดลการคิดราคา ต้นทุน และส่วนลดต่างจากสาขาหน้าร้านทั่วไป หากนำมารวมกับสาขาหน้าร้านจะทำให้ตัวเลขบิดเบือน จึงต้องแยกแท็บวิเคราะห์ต่างหาก

---

### 0.2 ค่าคงที่/ตรึงไว้ (Static/Pro-Forma) vs ยอดสะสม/อัปเดตตลอด (MTD Actuals)
ในระบบมีการแบ่งประเภทของตัวเลขออกเป็น 2 ชั้นอย่างชัดเจน:

1. **ยอดสะสม MTD (Actual Accumulated Numbers):**
   - คำนวณสะสมจากบิลขายจริงใน `fact_sales` ตั้งแต่วันที่ 1 ของเดือนปัจจุบัน (`2026-09-01`) จนถึงวันล่าสุดที่มีการบันทึกข้อมูล (`days_elapsed = 3` วัน)
   - ฟิลด์ใน JSON ได้แก่ `summary.sales`, `summary.cost`, `summary.disc`, `summary.gp`, `summary.gp_pct`
   - ในหน้าเว็บฝั่ง Client-side เมื่อมีการกรอง RM/DM/ค้นหา จะเกิดการคำนวณใหม่สดๆ ใน RAM ของเบราว์เซอร์ โดยเก็บค่ารวมดั้งเดิมไว้ใน Attribute `dataset.orig` เพื่อสลับกลับมาเมื่อล้างตัวกรอง

2. **ค่าตรึง/แบบจำลอง Pro-Forma (Pro-Forma Baseline & Simulation Constants):**
   - ในแท็บ **"💡 จำลอง Pro-Forma GP (รออนุมัติ)"** (`updateSimulation()`) มีการตรึงตัวเลขฐานและค่าการปรับปรุงเชิงยุทธศาสตร์ไว้ 3 ค่า:
     - `baseGpPct = 22.79`: ค่า GP% ฐาน ณ จุดที่เริ่มตรวจพบวิกฤต (อ้างอิงจากรอบวิเคราะห์ก่อนหน้า)
     - `m1` (ปรับปรุง Category 22 เป็นงบการตลาด): `+7.09 pp` (เพิ่มกำไร `+฿736,271`)
     - `m2` (ปรับราคากลุ่ม Minimart 02 ให้สะท้อนต้นทุนจริง): `+0.55 pp` (เพิ่มกำไร `+฿57,450`)
     - `m3` (ปิดจุดรั่วไหลบิลขายต่ำกว่าทุน/แจกฟรี 0 บาท): `+1.20 pp` (เพิ่มกำไร `+฿125,000`)
   - **เหตุผลที่ต้องแยก:** ค่าจริง MTD สะท้อนสิ่งที่เกิดขึ้นจริงในอดีตจนถึงปัจจุบัน ส่วนค่า Pro-Forma เป็นการจำลองผลลัพธ์ล่วงหน้า (Forward-Looking Scenario) หากผู้บริหารอนุมัติมาตรการทางบัญชีและการตั้งราคา

---

### 0.3 ระบบอ่านข้อมูลจากไหนตอนโหลดหน้า และ "ไม่ต่อ" อะไรบ้าง
- **ตอนผู้ใช้งานเปิดหน้าเว็บ (`gp_analysis_dashboard.html`):**
  - หน้าเว็บเป็น **Static Single Page Application (SPA)**
  - รันฟังก์ชัน `fetch('gp_analysis_data.json')` เพียงครั้งเดียวตอนโหลดหน้า
  - **ไม่ต่อ Database ใดๆ ทั้งสิ้น (Zero Database Connection at Runtime)**
  - **ไม่ต่อ Backend API, Node.js หรือ Python Server ใดๆ**
  - การกรอง (Filter), การจัดเรียง (Sorting), การยุบ/ขยายลำดับชั้น RM ➔ DM ➔ สาขา/บิล (Tree View) ทำงานบน Client-side JavaScript ใน RAM ของเบราว์เซอร์ 100%
- **ตอนประมวลผลข้อมูลหลังบ้าน (`build_gp_analysis.py`):**
  - เป็นสคริปต์ Python แบบ Batch Pipeline ทำหน้าที่ Query ข้อมูลจาก MySQL เข้ามาประมวลผล Aggregate และ Export ออกมาเป็นไฟล์ `gp_analysis_data.json`
  - ทำการต่อ Database 2 ตัว:
    1. Database `data-lake` บน MySQL Server (Default Port 13306)
    2. Database `MYPOS2018_CENTER` บน MySQL Server เดียวกัน

---

### 0.4 ตารางสรุป ตารางและไฟล์ที่เกี่ยวข้องทั้งหมดในระบบ

| ชื่อตาราง / ไฟล์ | ประเภท | 1 แถวคืออะไร | ความถี่ในการเขียน / อัปเดต | บทบาทในระบบ |
| :--- | :--- | :--- | :--- | :--- |
| `data-lake.fact_sales` | MySQL Table | 1 รายการขายย่อยในบิล (Transaction Line Item) | ระบบ POS หน้าร้าน Sync เข้า Data Lake รายวัน/ตามรอบ ETL | ตารางหลักที่ใช้คำนวณยอดขาย, ต้นทุน, ส่วนลด และค้นหารายการผิดปกติ |
| `data-lake.dim_branch` | MySQL Table | 1 สาขา (Store Master) | อัปเดตเมื่อมีการเปิด/ปิด หรือปรับโครงสร้างสาขา | Master ข้อมูลสาขา รหัส, ชื่อ, ผู้จัดการเขต (DM), ผู้จัดการภาค (RM) |
| `data-lake.dim_product` | MySQL Table | 1 รหัสสินค้าหลัก (iprod) | Sync ข้อมูล Master สินค้าจากระบบ ERP/POS | Master สินค้า, รหัสกลุ่มสินค้า (igrcode), ต้นทุนเฉลี่ย (iacst), ราคาขาย Price 3 (ipunit3) |
| `MYPOS2018_CENTER.item_group` | MySQL Table | 1 กลุ่มสินค้า (Product Subgroup) | อัปเดตเมื่อมีการเพิ่มกลุ่มสินค้า | ใช้แปลงรหัสกลุ่ม `igrcode` เป็นชื่อกลุ่มภาษาไทย `igrdesc` |
| `MYPOS2018_CENTER.item_type` | MySQL Table | 1 ประเภทสินค้าหลัก (Category Type) | อัปเดตเมื่อมีการปรับหมวดหมู่ | ใช้แปลงรหัสประเภท 2 หลักแรก `itycode` เป็นชื่อประเภท `itydesc` |
| `MYPOS2018_CENTER.item_barcode` | MySQL Table | 1 บาร์โค้ดสินค้า (Barcode Alias) | อัปเดตเมื่อมีการผูกบาร์โค้ดใหม่ | ใช้ Map รหัสบาร์โค้ดที่ยิงหน้าร้านกลับมาเป็นรหัสสินค้าหลัก (`master iprod`) |
| `gp_analysis_data.json` | JSON File (~8.3 MB) | ทั้งระบบรวมเป็น 1 Snapshot JSON Object | รันผ่านสคริปต์ `build_gp_analysis.py` ทุกเช้า หรือเมื่อต้องการ Refresh | คลังข้อมูลสำเร็จรูป (Pre-aggregated Data) ให้แดชบอร์ดโหลดไปแสดงผล |
| `gp_analysis_dashboard.html` | HTML/JS File | หน้าเว็บ Dashboard ทั้งหมด | แก้ไขเมื่อมีการพัฒนา UI หรือปรับปรุงสูตรการแสดงผล | ส่วนต่อประสานผู้ใช้ (User Interface & Interactive Logic) |
| `push_lost_product_files.py` | Python CLI Script | - | ทำงานเมื่อรันคำสั่ง Push ข้อมูล | อัปโหลดไฟล์ขึ้น GitHub Pages Repository ผ่าน REST API |

---

## 1. ที่มาของข้อมูลตั้งต้น

### 1.1 เกณฑ์การเข้า/ออกจากชุดข้อมูล (Filtering Criteria)

| ลำดับ | เงื่อนไขในโค้ด | แหล่งข้อมูล (ตาราง.คอลัมน์) | ความหมายเชิงธุรกิจ | เหตุผลทางเทคนิค |
| :---: | :--- | :--- | :--- | :--- |
| 1 | `sodate >= %s` | `fact_sales.sodate` | วิเคราะห์ข้อมูลย้อนหลัง 2 เดือน (เดือนก่อนหน้า + เดือนปัจจุบัน MTD) | กำหนดช่วงเวลาเปรียบเทียบ MoM และควบคุมขนาด Query |
| 2 | `solinetype NOT IN ('C', 'R')` | `fact_sales.solinetype` | ตัดรายการบิลที่ถูกยกเลิก (Cancel) และรายการคืนเงิน (Return) | ป้องกันยอดขายและต้นทุนเบิ้ล หรือติดลบจากการยกเลิก |
| 3 | `soretflag = 'N'` | `fact_sales.soretflag` | ไม่เอาบิลที่ถูก Flag เป็นใบลดหนี้/บิลคืนสินค้า | ใช้เฉพาะบิลขายจริงที่สมบูรณ์เท่านั้น |
| 4 | `sotowhs >= '001' AND sotowhs <= '500'` | `fact_sales.sotowhs` | เอาเฉพาะสาขาหน้าร้านค้าปลีกปกติ (สาขา 001 ถึง 500) | **ตัดสาขา 901 (Online/ศูนย์กลาง) และคลังสินค้าออก** |
| 5 | `ty NOT IN ('03','12','15','20','26')` | `dim_product.igrcode` (2 หลักแรก) | ตัดสินค้าที่ไม่อยู่ในการค้าปลีกทั่วไป (Excluded Item Types) | ดูรายละเอียดในรายการ `EXCLUDED_ITY` |
| 6 | `soqty > 0` | `fact_sales.soqty` | ใช้เฉพาะรายการขายที่มีจำนวนสินค้ามากกว่า 0 | กรองเฉพาะใน Query ตรวจสอบบิลผิดปกติ (`query_anomalies`) |
| 7 | `total_cost > solineamt` | `fact_sales.total_cost`, `fact_sales.solineamt` | ดึงเฉพาะบิลที่ต้นทุนรวมสูงกว่ายอดขาย (บิลขาดทุน) | เงื่อนไขหลักสำหรับดึง 250 บิลผิดปกติใน `query_anomalies` |

---

### 1.2 จุดเตือน ⚠️ ทุกจุดที่เคยมีคนเข้าใจผิดหรือเคยพังจริง

> [!CAUTION]
> ⚠️ **จุดเตือน 1: ห้ามใช้ `solineamt` เป็นยอดขายสุทธิเด็ดขาด! ต้องใช้ `net_sales_amt` เท่านั้น**
> - **สิ่งที่ดูเหมือนถูก:** หลายคนคิดว่า `fact_sales.solineamt` คือยอดขายสุทธิ เพราะชื่อคือ "Sales Line Amount"
> - **ความจริง:** `solineamt` เป็นเพียงยอดขายระดับแถวก่อนหักส่วนลดท้ายบิล! ยอดขายสุทธิที่แท้จริงหลังจากหักส่วนลดท้ายบิลที่เฉลี่ยลงมาในระดับแถวแล้วคือ **`fact_sales.net_sales_amt`**
> - **ผลกระทบถ้าใช้ผิด:** หากใช้ `SUM(solineamt)` ยอดขายของบริษัทจะพองเกินจริงทันที **หลายล้านบาท** และทำให้ตัวเลข GP% สูงเกินจริงอย่างมีนัยสำคัญ
> - **สูตรส่วนลดที่ถูกต้องใน SQL:**
>   - ส่วนลดระดับสินค้า (SKU Discount): `SUM(soqty * sopricdisc)`
>   - ส่วนลดระดับท้ายบิล (Bill Discount): `SUM(solineamt - net_sales_amt)`
>   - ส่วนลดรวมทั้งหมด (Total Discount): `sku_disc + bill_disc`

> [!WARNING]
> ⚠️ **จุดเตือน 2: สาขา 901 (ร้าน Online) ปนเปื้อนโครงสร้างหน้าร้าน**
> - **สิ่งที่เคยพังจริง:** ในการคำนวณเวอร์ชันแรก ไม่ได้ใส่เงื่อนไขกรอง `sotowhs <= '500'` ทำให้ยอดขายและบิลของสาขา 901 ซึ่งเป็นร้านค้าออนไลน์ เข้ามาปะปนกับสาขาหน้าร้าน
> - **ปัญหา:** ร้านค้าออนไลน์มีสัดส่วนสินค้า ค่าธรรมเนียม และการยิงโปรโมชันที่ไม่เหมือนหน้าร้าน ทำให้ตัวเลขกำไรขั้นต้นของสาขาหน้าร้านผิดเพี้ยน ปัจจุบันจึงต้องแยกสาขา 901 ออกไปไว้ในแท็บเฉพาะ "🌐 ร้าน Online (สาขา 901)"

> [!WARNING]
> ⚠️ **จุดเตือน 3: บิลของแถม 0 บาท (Category 22 วิกฤตสินค้าเทศกาล)**
> - **สาเหตุ:** แคชเชียร์ยิงขายสินค้าเทศกาลที่นำมาจัดรายการของสมนาคุณ โดยบันทึกราคาขาย `solineamt = 0`, `net_sales_amt = 0` แต่ระบบตัดสต็อกต้นทุน `total_cost` เต็มจำนวน
> - **ความเสียหายจริง:** เกิดผลขาดทุนสะสมในเดือน MTD เป็นมูลค่ากว่า **7.3 แสนบาท** และกด GP รวมของบริษัทร่วงลงทันที **-7.09 pp**

> [!IMPORTANT]
> ⚠️ **จุดเตือน 4: ตัวเลขส่วนลดของ Category 22 ในระดับสาขา (`festival_stores`) เป็นค่าประมาณการ (Estimated Proportion)**
> - **ในโค้ด `build_gp_analysis.py` (บรรทัด 560-575):**
>   เพื่อประหยัด RAM และเวลาในการรัน Query ตารางย่อย `ps_agg` (Product × Store) ไม่ได้เก็บ `sku_disc` และ `bill_disc` แยกรายสาขา แต่ใช้วิธีคำนวณสัดส่วน:
>   $$\text{disc\_ratio} = \frac{\text{prod\_disc}}{\text{prod\_cost}} \quad (\text{ถ้าต้นทุน } \le 0 \text{ จะใช้ } 1.82)$$
>   แล้วนำไปคูณกลับ: `st['disc'] += v['cost'] * disc_ratio`
>   **ทีม IT ต้องทราบว่า:** ยอดส่วนลดในตาราง `fest-store-tbl` และ `fest-tree-tbl` เป็นตัวเลขประมาณการเชิงสัดส่วน ไม่ใช่ผลรวมตรงจากระดับบรรทัดบิล

> [!NOTE]
> ⚠️ **จุดเตือน 5: ประสิทธิภาพ Query บน `fact_sales` ต้องบังคับใช้ Index**
> - ตาราง `fact_sales` มีขนาดหลายสิบล้านแถว การ Query ต้องระบุ `FORCE INDEX (idx_optimize_sales_report)` ใน SQL Statement เสมอ หากไม่ระบุ MySQL Query Optimizer อาจทำ Full Table Scan ทำให้ระบบค้างหรือเกิด Connection Timeout

---

### 1.3 ตารางฟิลด์ระดับแถว (Row-Level Field Mapping)

| ชื่อฟิลด์ใน JSON | แหล่งข้อมูล (ตาราง.คอลัมน์จริง) | สูตร / Expression ในโค้ด | คำอธิบาย |
| :--- | :--- | :--- | :--- |
| `whs` / `code` | `fact_sales.sotowhs` | `f'{int(sotowhs):03d}'` | รหัสสาขา ฟอร์แมตเป็นตัวเลข 3 หลักเสมอ |
| `iprod` | `fact_sales.iprod` | `barcodes.get(iprod, iprod)` | รหัสสินค้าหลัก (Master Product Code) |
| `mo` | `fact_sales.sodate` | `CONCAT(YEAR(sodate), '-', LPAD(MONTH(sodate),2,'0'))` | เดือนในรูปแบบ `YYYY-MM` เช่น `'2026-09'` |
| `sales` | `fact_sales.net_sales_amt` | `SUM(net_sales_amt)` | ยอดขายสุทธิจริงหลังหักส่วนลดทุกประเภท |
| `cost` | `fact_sales.total_cost` | `SUM(total_cost)` | ต้นทุนขายรวมของรายการนั้นๆ |
| `sku_disc` | `fact_sales.soqty`, `fact_sales.sopricdisc` | `SUM(soqty * sopricdisc)` | ยอดส่วนลดระดับรายการสินค้า |
| `bill_disc` | `fact_sales.solineamt`, `fact_sales.net_sales_amt` | `SUM(solineamt - net_sales_amt)` | ยอดส่วนลดระดับท้ายบิลที่เฉลี่ยลงรายการ |
| `disc` | - | `sku_disc + bill_disc` | ส่วนลดรวมทุกประเภท |
| `qty` | `fact_sales.soqty` | `SUM(soqty)` | จำนวนชิ้นสินค้าที่ขายได้ |
| `gp` | - | `sales - cost` | กำไรขั้นต้น (Gross Profit) |
| `gp_pct` | - | `(sales - cost) / sales * 100` (ถ้า sales = 0 ให้เป็น 0) | อัตรากำไรขั้นต้นคิดเป็นเปอร์เซ็นต์ |

---

## 2. ที่มาของข้อมูลยอดสะสม/รายวัน

### 2.1 SQL จริงที่ใช้ดึงข้อมูล

#### 1) Query สรุปยอดขายระดับสาขาและสินค้า (`query_gp_data`):
```sql
SELECT sotowhs, iprod,
       CONCAT(YEAR(sodate), '-', LPAD(MONTH(sodate),2,'0')) as mo,
       SUM(net_sales_amt) as sales,
       SUM(total_cost) as cost,
       SUM(soqty * sopricdisc) as sku_disc,
       SUM(solineamt - net_sales_amt) as bill_disc,
       SUM(soqty) as qty
FROM `data-lake`.fact_sales FORCE INDEX (idx_optimize_sales_report)
WHERE sodate >= %s
  AND solinetype NOT IN ('C','R')
  AND soretflag = 'N'
  AND sotowhs >= '001' AND sotowhs <= '500'
GROUP BY sotowhs, iprod, mo;
```

#### 2) Query ตรวจสอบบิลขายผิดปกติ 250 รายการ (`query_anomalies`):
```sql
SELECT sono, DATE_FORMAT(sodate, '%Y-%m-%d') as sodate, sotowhs, iprod,
       soqty, sopricunit, solineamt, socstunit, total_cost,
       (total_cost - solineamt) as loss
FROM `data-lake`.fact_sales
WHERE sodate >= %s
  AND sotowhs != '901'
  AND total_cost > solineamt
  AND soqty > 0
  AND solinetype NOT IN ('C','R')
  AND soretflag = 'N'
ORDER BY (total_cost - solineamt) DESC
LIMIT 250;
```

#### 3) Query วันที่ข้อมูลล่าสุด MTD (`days_elapsed`):
```sql
SELECT MAX(DAY(sodate)) 
FROM `data-lake`.fact_sales FORCE INDEX (idx_optimize_sales_report)
WHERE sodate >= %s AND sodate < %s
  AND soretflag = 'N'
  AND sotowhs >= '001' AND sotowhs <= '500';
```

---

### 2.2 หมายเหตุ Edge Cases ที่เคยเกิดปัญหาจริง
1. **กรณีข้อมูลไม่มาเลย หรือยังไม่มีการเปิดบิลในวันนั้น:**
   - ฟังก์ชัน `MAX(DAY(sodate))` จะคืนค่า `None` โค้ดจะ Fallback ไปใช้ `days_elapsed = 1` เพื่อป้องกันการหารด้วยศูนย์ (`ZeroDivisionError`)
2. **ฟิลด์ที่ชื่อคล้ายกันแต่ห้ามใช้สลับกัน:**
   - `sopricunit` (ราคาขายป้ายต่อหน่วย) vs `socstunit` (ต้นทุนต่อหน่วย): ในการคำนวณส่วนลดบิลผิดปกติ `disc = (qty * sopricunit) - solineamt` ห้ามใช้ `socstunit`
   - `iprod` vs `parcode` vs `barcode`: สินค้าบางรายการมีหลายบาร์โค้ด ในระบบต้องยึด `iprod` จาก `dim_product` เป็นหลัก ส่วน `parcode` ใช้สำหรับแสดงผลบนหน้าจอให้พนักงานจำง่าย
3. **การหารด้วยศูนย์ (Division by Zero):**
   - ทุกจุดใน JavaScript และ Python จะมี Guard เสมอ เช่น `(sales > 0) ? (gp / sales * 100) : 0` หากไม่มียอดขาย GP% จะถูกตั้งเป็น `0.0` ทันที ไม่ปล่อยให้เป็น `NaN` หรือ `Infinity`

---

## 3. สูตร KPI แต่ละองค์ประกอบบนหน้าจอ

> เรียงลำดับจากบนลงล่าง และจากซ้ายไปขวา ตามที่ปรากฏบนหน้าจอจริงทุกจุด

| ชื่อที่เห็นบนจอ (คำเป๊ะๆ) | สูตรคำนวณในโค้ด / Expression ที่ใช้จริง |
| :--- | :--- |
| **📈 GP Analysis Dashboard** | หัวข้อหลักของระบบ (Title) |
| **ข้อความ Subtitle (`#hdr-sub`)** | `"ข้อมูล ณ " + _meta.current_month + " (MTD ผ่านไป " + _meta.days_elapsed + " วัน) \| รวม " + summary.store_count + " สาขา \| " + summary.product_count + " สินค้า"` |
| **ปุ่ม AI: 🎪 วิกฤตเทศกาล (-7.09 pp)** | ข้อความระบุผลกระทบ Category 22: `addPp = 7.09` (คำนวณจากสัดส่วนผลขาดทุนของ Category 22 ต่อ Net Sales รวม) |
| **ปุ่ม AI: 🛒 โครงสร้าง Minimart (-3.69 pp)** | ข้อความระบุผลกระทบ Category 02: `addPp = 0.55 - 3.69` (คำนวณจากส่วนต่าง GP ปัจจุบันเทียบกับเกณฑ์ 25%) |
| **ปุ่ม AI: 💡 จำลอง Pro-Forma GP (รออนุมัติ)** | ปุ่มสลับแท็บไปที่ `switchTab('simulation')` |
| **ปุ่ม AI: 🎯 แผนยุทธศาสตร์ GP & ยอดขาย** | ปุ่มสลับแท็บไปที่ `switchTab('strategy')` |
| **ปุ่ม AI: ⚠️ ตรวจสอบต้นทุน & ขายผิดปกติ** | ปุ่มสลับแท็บไปที่ `switchTab('audit')` |
| **ปุ่ม AI: 🌐 ร้าน Online (สาขา 901)** | ปุ่มสลับแท็บไปที่ `switchTab('branch901')` |
| **ปุ่ม AI: 📋 Executive Report** | ปุ่มเปิด Modal รายงานผู้บริหาร `openExecutiveReport()` |
| **[KPI 1] Net Sales MTD (`#k-sales`)** | ถ้าไม่ฟิลเตอร์: `summary.sales`<br>ถ้าฟิลเตอร์สาขา: `SUM(s.sales)` ของสาขาที่ผ่านการฟิลเตอร์ |
| **[KPI 1] ป้ายเปรียบเทียบ MoM (`#k-sales-cmp`)** | ถ้าไม่ฟิลเตอร์: `((sales_mtd / days_elapsed * days_in_prev_mo) - sales_prev) / sales_prev * 100` (ฉายยอดเต็มเดือนเทียบเดือนก่อน)<br>ถ้าฟิลเตอร์: แสดงข้อความ `"X ร้าน (filtered)"` |
| **[KPI 2] Discount MTD (`#k-disc`)** | ถ้าไม่ฟิลเตอร์: `summary.disc`<br>ถ้าฟิลเตอร์สาขา: `SUM(s.disc)` ของสาขาที่ผ่านการฟิลเตอร์ |
| **[KPI 2] ป้ายเปรียบเทียบ MoM (`#k-disc-cmp`)** | สูตรเทียบฉายยอดเต็มเดือนเช่นเดียวกับ KPI 1 |
| **[KPI 3] Cost MTD (`#k-cost`)** | ถ้าไม่ฟิลเตอร์: `summary.cost`<br>ถ้าฟิลเตอร์สาขา: `SUM(s.cost)` ของสาขาที่ผ่านการฟิลเตอร์ |
| **[KPI 3] ป้ายเปรียบเทียบ MoM (`#k-cost-cmp`)** | สูตรเทียบฉายยอดเต็มเดือนเช่นเดียวกับ KPI 1 |
| **[KPI 4] GP Amount (`#k-gp`)** | ถ้าไม่ฟิลเตอร์: `summary.gp = summary.sales - summary.cost`<br>ถ้าฟิลเตอร์สาขา: `totSales - totCost` |
| **[KPI 4] ป้ายเปรียบเทียบ MoM (`#k-gp-cmp`)** | สูตรเทียบฉายยอดเต็มเดือนเช่นเดียวกับ KPI 1 |
| **[KPI 5] GP % (`#k-gp-pct`)** | ถ้าไม่ฟิลเตอร์: `summary.gp_pct = (summary.gp / summary.sales) * 100`<br>ถ้าฟิลเตอร์สาขา: `(totGp / totSales) * 100` |
| **[KPI 5] ป้ายเปรียบเทียบ MoM (`#k-gp-pct-cmp`)** | `gp_pct_mtd - gp_pct_prev` (แสดงผลต่างเป็นหน่วย percentage points: `pp`) |
| **แท็บ 1: 🏪 Store - คอลัมน์ GP** | `r.gp = r.sales - r.cost` |
| **แท็บ 1: 🏪 Store - คอลัมน์ GP %** | `r.gp_pct = (r.sales > 0) ? (r.gp / r.sales * 100) : 0` |
| **แท็บ 2: 📦 Product - คอลัมน์ส่วนลดรวม** | `p.disc = p.sku_disc + p.bill_disc` |
| **แท็บ 2: 📦 Product - คอลัมน์ GP %** | `p.gp_pct = (p.sales > 0) ? ((p.sales - p.cost) / p.sales * 100) : 0` |
| **แท็บ 3: 📈 Trend - กราฟแท่ง & เส้น** | แท่งสีน้ำเงิน = `m.sales`, แท่งสีส้ม = `m.cost`, เส้นสีเขียว = `m.gp_pct` |
| **แท็บ 4: 🎪 วิกฤตเทศกาล - ยอดขาย Category 22** | `kSales = SUM(festStores.sales)` (เฉพาะสินค้า `type_code == '22'`) |
| **แท็บ 4: 🎪 วิกฤตเทศกาล - ต้นทุน Category 22** | `kCost = SUM(festStores.cost)` |
| **แท็บ 4: 🎪 วิกฤตเทศกาล - ส่วนลดที่แจก** | `kDisc = SUM(festStores.disc)` |
| **แท็บ 4: 🎪 วิกฤตเทศกาล - GP ขาดทุนสุทธิ** | `kGp = SUM(festStores.gp)` (ค่าติดลบเสมอ) |
| **แท็บ 5: 🛒 Minimart - Sales MTD Minimart** | `totMiniSales = SUM(miniProds.sales)` (เฉพาะสินค้า `type_code == '02'`) |
| **แท็บ 5: 🛒 Minimart - Cost MTD Minimart** | `totMiniCost = SUM(miniProds.cost)` |
| **แท็บ 5: 🛒 Minimart - GP MTD Minimart** | `totMiniGp = totMiniSales - totMiniCost` พร้อมป้ายเปอร์เซ็นต์ `totMiniGp / totMiniSales * 100` |
| **แท็บ 6: 💡 จำลอง Pro-Forma - GP หลังปรับปรุง (`#sim-res-gp`)** | `finalGpPct = 22.79 + (m1 ? 7.09 : 0) + (m2 ? 0.55 : 0) + (m3 ? 1.20 : 0)` |
| **แท็บ 6: 💡 จำลอง Pro-Forma - เพิ่มขึ้นทันที (`#sim-res-diff`)** | `addPp = (m1 ? 7.09 : 0) + (m2 ? 0.55 : 0) + (m3 ? 1.20 : 0)` |
| **แท็บ 6: 💡 จำลอง Pro-Forma - กำไรขั้นต้นเพิ่มขึ้น (`#sim-res-amt`)** | `addAmt = (m1 ? 736271 : 0) + (m2 ? 57450 : 0) + (m3 ? 125000 : 0)` |
| **แท็บ 8: ⚠️ ตรวจสอบต้นทุน - รายการบิลขาดทุน (`#audit-kpi-tx-count`)** | `txList.length` (จำนวนบิลที่มี `total_cost > solineamt`) = 250 รายการ |
| **แท็บ 8: ⚠️ ตรวจสอบต้นทุน - คอลัมน์ส่วนลด (`#tbl-audit-tx`)** | `r.disc = (r.disc != null) ? r.disc : Math.max(0, (r.qty * r.u_price) - r.sales)` |
| **แท็บ 8: ⚠️ ตรวจสอบต้นทุน - คอลัมน์ขาดทุน (`#tbl-audit-tx`)** | `r.loss = r.cost - r.sales` (แสดงค่า `-฿...`) |
| **แท็บ 8: ⚠️ ตรวจสอบต้นทุน - สินค้าป้ายขาดทุน (`#tbl-audit-master`)** | `r.diff = r.cost - (r.price3 != null ? r.price3 : r.price)` |
| **แท็บ 8: ⚠️ ตรวจสอบต้นทุน - ทุนสูงกว่า (%) (`#tbl-audit-master`)** | `r.diff_pct = (r.cost - price) / price * 100` |
| **แท็บ 8: ⚠️ ตรวจสอบต้นทุน - Grand Total ทุกตาราง** | ผลรวม `SUM(...)` ของแถวทั้งหมดที่แสดง พร้อมพื้นหลัง Navy `#0f172a` ตัวหนังสือหนา |
| **แท็บ 9: 🌐 ร้าน Online (901) - ยอดขาย MTD** | `b901.monthly[current_month].sales` |
| **แท็บ 9: 🌐 ร้าน Online (901) - กำไรขั้นต้น GP** | `b901.monthly[current_month].gp` |
| **แท็บ 9: 🌐 ร้าน Online (901) - ส่วนลด (disc)** | `Math.max(0, (a.qty * a.u_price) - a.sales)` |

---

## 4. ตัวเลขปัจจุบัน ณ วันที่ตรวจ (Snapshot Data)

> ข้อมูล Snapshot จากไฟล์ `gp_analysis_data.json` ที่ถูก Build ล่าสุดเมื่อ **2026-09-04 03:53:45 UTC**
> ข้อมูลครอบคลุมรอบขาย 1 - 3 กันยายน 2026 (`days_elapsed = 3` วัน)

```json
{
  "_meta": {
    "schema": 3,
    "built_by": "antigravity-gemini-3-flash",
    "built_at": "2026-09-04T03:53:45.931633Z",
    "current_month": "2026-09",
    "days_elapsed": 3,
    "months": ["2026-08", "2026-09"]
  },
  "summary": {
    "sales": 14870054.52,
    "disc": 2156326.58,
    "cost": 11273911.11,
    "gp": 3596143.41,
    "gp_pct": 24.18,
    "store_count": 202,
    "product_count": 11135
  }
}
```

### สรุปตัวเลขเปรียบเทียบ MoM:
- **ยอดขาย MTD กันยายน 2026 (3 วัน):** ฿14,870,054.52 (ฉายยอดเต็มเดือน 30 วันได้ ~฿148.7M เทียบสิงหาคม ฿132.8M เติบโตประมาณ +12.0%)
- **ต้นทุนขาย MTD (3 วัน):** ฿11,273,911.11
- **ส่วนลดสะสม MTD (3 วัน):** ฿2,156,326.58
- **กำไรขั้นต้น GP MTD (3 วัน):** ฿3,596,143.41
- **อัตรากำไรขั้นต้น GP% MTD:** **24.18% (หรือ ~24.2%)**
- **เทียบกับเดือนสิงหาคม 2026 (เต็มเดือน):**
  - ยอดขายสิงหาคม: ฿132,775,403.76
  - ต้นทุนสิงหาคม: ฿90,978,118.08
  - ส่วนลดสิงหาคม: ฿4,259,475.19
  - กำไรขั้นต้นสิงหาคม: ฿41,797,285.68
  - **อัตรา GP% สิงหาคม: 31.48% (~31.5%)**
  - **ส่วนต่าง GP% (Delta):** **-7.30 percentage points (-7.30 pp)**

### ตัวเลขในระบบตรวจสอบความผิดปกติ (Audit Sub-modules):
- **จำนวนสาขาทั้งหมดในระบบ:** 202 สาขา (เฉพาะสาขา 001 - 500)
- **จำนวนสินค้าทั้งหมดที่มียอดเคลื่อนไหว:** 11,135 SKUs
- **บิลขายที่ติดลบผิดปกติ (Transaction Anomalies):** 250 บิล (จำกัด Limit ไว้ 250 รายการแรกที่ขาดทุนสูงสุด)
- **สินค้าที่มีต้นทุนเฉลี่ยสูงกว่าราคาป้าย (Price 3 Master Anomaly):** 97 รายการ
- **สาขา 901 (ร้าน Online):**
  - ยอดขาย MTD: มีข้อมูล 2 เดือนย้อนหลัง
  - สินค้าขายดี Top 100: 100 รายการ
  - บิลขายผิดปกติ: 32 รายการ

---

## 5. ตารางเข้างาน/Schedule (Jobs & Data Pipelines)

| ชื่องาน / Script | เวลาที่รัน / Trigger | พฤติกรรมพิเศษ (Idempotent / Guard) | ระยะเวลาที่ใช้รัน | ผลลัพธ์ที่ได้ |
| :--- | :--- | :--- | :--- | :--- |
| `build_gp_analysis.py` | รันทุกเช้าเวลา 06:00 น. หรือเมื่อสั่ง Manual Refresh | **เป็น Idempotent 100%:** รันซ้ำกี่ครั้งก็ได้ผลลัพธ์เดิม ไม่ทำให้ข้อมูลเบิ้ล เพราะเป็นการ Query อ่านอย่างเดียว แล้วเขียนทับไฟล์ `gp_analysis_data.json` ทั้งฉบับ | ประมาณ 30 - 45 วินาที | ไฟล์ `gp_analysis_data.json` ขนาด ~8.3 MB และซิงค์ไปที่ `F:\facebook\gp_data.json` |
| `push_lost_product_files.py` | รันต่อจาก `build_gp_analysis.py` ทันที | ตรวจสอบ SHA ของไฟล์บน GitHub หากไฟล์ไม่มีการเปลี่ยนแปลงจะไม่สร้าง Commit ซ้ำซ้อน | ประมาณ 10 - 20 วินาที | อัปโหลดไฟล์ขึ้น GitHub Repository (`lost-Product`) เพื่อให้ GitHub Pages ทำการ Deploy |
| GitHub Pages Build & Deploy | อัตโนมัติเมื่อมี Commit บน GitHub | GitHub Actions ทำการ build static assets ไปยัง CDN | ประมาณ 30 - 60 วินาที | หน้าเว็บจริงอัปเดตที่ `https://tumsbux.github.io/lost-Product/` |

---

## ท้ายเอกสาร: สรุปแหล่งข้อมูลและสิทธิ์การเข้าถึง (Database & Schema Summary)

| ฐานข้อมูล (Database) | โฮสต์ / การเชื่อมต่อ | ตารางที่แตะ (Tables) | สิทธิ์การเข้าถึง (Access Level) | จุดเขียนข้อมูลกลับ (Write Operations) |
| :--- | :--- | :--- | :--- | :--- |
| `data-lake` | MySQL (Port 13306) | `fact_sales`<br>`dim_branch`<br>`dim_product` | **READ-ONLY 100%** | **ไม่มี** ระบบไม่เคยทำการ INSERT, UPDATE, หรือ DELETE ข้อมูลใดๆ ในฐานข้อมูล `data-lake` |
| `MYPOS2018_CENTER` | MySQL (Port 13306) | `item_group`<br>`item_type`<br>`item_barcode` | **READ-ONLY 100%** | **ไม่มี** ระบบอ่านเฉพาะข้อมูล Master Name และ Barcode Mapping เท่านั้น |
| Local File System | Local PC (`F:\lost-Product\`, `F:\facebook\`) | `gp_analysis_data.json`<br>`gp_analysis_dashboard.html`<br>`mockup_cost_anomaly_tab.html` | Read / Write | เขียนบันทึกไฟล์ JSON Snapshot และไฟล์ HTML หน้าจอ Dashboard บนดิสก์ Local |
| GitHub Remote Repo | `https://github.com/tumsbux/lost-Product` | Repository Contents | Read / Write (ผ่าน Personal Access Token) | อัปเดตไฟล์ HTML, JSON และ Python ผ่าน REST API เพื่อให้หน้าเว็บบน GitHub Pages อัปเดต |

### หมายเหตุและข้อสังเกตเพิ่มเติมสำหรับทีม IT (Audit Notice):
1. **จุดน่าสงสัย 1: ค่า `baseGpPct = 22.79` ในแท็บจำลอง:** ในฟังก์ชัน `updateSimulation()` มีการฮาร์ดโค้ดตัวเลข `22.79` เอาไว้ ซึ่งเป็นค่า GP% ของรอบการคำนวณก่อนหน้า หากในอนาคตต้องการให้สะท้อนค่าจริง ควรผูกเป็น `DATA.summary.gp_pct`
2. **จุดน่าสงสัย 2: อัตราส่วนลดของ Category 22 ในระดับสาขา:** ใน `build_gp_analysis.py` บรรทัด 560 มีการใช้ค่าคงที่ `1.82` เป็น Fallback (`disc_ratio = (p_disc / p_cost) if p_cost > 0 else 1.82`) ซึ่งเป็นค่า Factor ที่ได้จากการคำนวณเฉลี่ยของสินค้าเทศกาล หากหมวดหมู่นี้มีการเปลี่ยนประเภทของแถม ค่านี้อาจต้องได้รับการทบทวน
3. **การทดสอบความถูกต้อง:** ทุก Query ในเอกสารนี้ได้รับการตรวจสอบจากโค้ดจริงที่กำลังรันใน Production ปัจจุบัน และสามารถนำ SQL ในข้อ 2 ไป Execute ตรงบน Database Client (เช่น DBeaver หรือ MySQL Workbench) เพื่อสอบทานตัวเลขได้ทันที
