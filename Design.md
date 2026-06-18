# Design — Dashboard Views & UI

> Dashboard structure, color rules, GA4 analytics

---

## 📊 Dashboard Views

### index.html — Hub
Hero KPIs: ยอดขาย MTD, vs เป้า MTD, Projected, YoY Projected, GP%
- 4 KPI cards
- RM table
- Monthly trend chart

### sales_dashboard_v8.html — Sales (~290KB)
| View | Content |
|------|---------|
| Home | KPI cards, Gauge YoY, Monthly Trend chart |
| RM/DM/Store | Detail tables + charts |
| Executive | 7-section report; `excTarget = total_target × 1.155` (+15.5% challenge) |
| Report | RM cards + DM table + charts |

### fraud_dashboard.html — Fraud Detection
Tabs: Overview · Store Risk · พนักงาน (rtuname) · Return Bill · เวลา · ร้าน · DM · RM

**Risk badges:** HIGH / MEDIUM / LOW

**Overview KPI card #3** (แก้ 2026-06-02): เปลี่ยนจาก "Repeat rtsono" (`n_so_dup`/`so_dup_amt` = 8 bills) → **"Return Bill"** (`n`/`total` = ยอดบิล return ทั้งหมด เช่น 131 bills · ฿18,270)
```js
{l:'🧾 Return Bill',v:fmt(n)+' bills',sub:'฿'+fmt(total),c:'kr'},
```
หมายเหตุ: doughnut "Fraud Signals" ยังใช้ label "Repeat rtsono" ถูกต้อง (เป็น fraud-signal breakdown คนละตัวกับ KPI card)

### product_dashboard.html — Products (~31KB)
Top products by sales value. Store/DM/RM filter. YoY comparison. Line Type modal.

**Columns (per 2026-06-05 fix):** parcode · ชื่อ · กลุ่ม · ... · col 11 = Onhand · col 12 = ipunit3

### lost_product_dashboard.html — Lost Products
**Canonical URL:** https://tumsbux.github.io/lost-Product/

**Filters:** RM · DM · Store · สถานะ · กลุ่ม · ประเภท · หายไป (years gone) · search

**KPIs (5 cards, all recompute live except status filter):**
Total · ACTIVE · STALE · LOST · Peak qty

**Table columns:**
parcode · ชื่อ · กลุ่ม · 2021-2026 qty · ขายปีล่าสุด · หายไป (ปี) · peak qty · สถานะ · lost_score

**Color rules:**
- เขียว = had sales (positive value)
- gray "—" = no sales (no concern)
- red "0" = had history but stopped (current-year disappearance)

**Two-pass filter in `applyAll()`:**
- **Pass 1 `kpiBase`** = scope (RM/DM/Store) + ประเภท + กลุ่ม + หายไป + search → used for KPI cards
- **Pass 2 `filtered`** = `kpiBase` + status → used for the table

Total card subtitle shows active filters: `🔍 N ร้าน · ประเภท: ... · กลุ่ม: ... · หาย ≥Xปี · ค้นหา: "..."`

Empty-table state: `⚠️ ไม่มีสินค้าตรงเงื่อนไขในขอบเขตนี้ — ลองล้าง filter...` + console.warn naming scope stores with no entry in `store_breakdown`

**AI Analysis bar (4 pill buttons, purple gradient):**
- 🔍 สาเหตุสินค้าหาย — cluster LOST by group/brand/last_year
- 🔄 แนะนำสินค้าทดแทน — pair top 10 LOST with ACTIVE alternatives (same group, ±30% price)
- 📈 ระบุโอกาส Recovery — high-peak recently-lost candidates + baht recovery estimate
- 📊 Trend ปีต่อปี — yearly active/new/lost counts + net change

All AI analyses use `window.kpiBase` (post-filter except status). Modal pattern: centered, Escape closes, click-outside closes.

**Export:** XLSX button uses SheetJS to download filtered rows

## 📋 Executive Board Report UI Pattern

To support formal business and audit reporting, all four dashboards feature a standardized print-optimized report view:
- **Trigger**: Red-to-crimson gradient button `📋 Executive Report` inside `.ai-bar` (floated right with `margin-left: auto;`).
- **Modal Wrapper**: Reuses the existing `#ai-modal` markup, styled dynamically with local inline CSS blocks.
- **Print query (`@media print`)**:
  - Hides all other page elements (`body > * { display: none !important; }`).
  - Isolates and fits the `#ai-modal` and its children onto the page (`position: absolute; left: 0; top: 0; width: 100%;`).
  - Adjusts styling (removes shadows, disables button displays, expands scroll containers) to make it look like a clean PDF/A4 page.
- **Tone**: Formal Thai business and loss prevention register terminology.
- **Data Source**: Aggregates from local memory JSON caches (e.g. `DATA` or `D`) to avoid additional network payloads.

---

## 📈 lost_score formula

```python
if status == 'ACTIVE':           # has 2026 sales
    lost_score = 0
elif status == 'STALE':          # has 2025 but not 2026
    lost_score = max_qty
else:  # LOST: no 2025 AND no 2026
    lost_score = years_gone * max_qty
```

Where `max_qty` = peak annual qty across 6 years, `years_gone = current_year - last_year`

**Reading:** "How much annual qty are we missing × how long we've been missing it". Sort DESC to rank by recovery priority.

**Example** (parcode `8887771939` แผ่นใยขัดพื้น):
- 2021=5,561 · 2022=**13,562** · 2023=8,478 · 2024=1,080 · 2025=0 · 2026=0
- max_qty = 13,562 (peak 2022) · last_year = 2024 · years_gone = 2 · status = LOST
- lost_score = 2 × 13,562 = **27,124** ✓

---

## 📊 GA4 Analytics

**Measurement ID:** `G-E3ZFFKXFT8` (property: "Tuenjai Dashboard")
**File:** `analytics.js` — shared module, included ทุก dashboard

**Events:**
`dashboard_viewed`, `filter_applied`, `filter_reset`, `view_changed`, `sort_changed`, `linetype_modal_viewed`, `search_performed`, `data_load_failed`, `dashboard_navigated`

**Custom Dimensions (7):**
`dashboard_name`, `filter_scope`, `filter_rm`, `filter_dm`, `filter_store`, `days_elapsed`, `data_month`

**⚠️ ถ้า GA4 หายหลัง daily run:** ตรวจสอบว่า `analytics.js` อยู่ใน `push_files` ใน `update_dashboard.py`

---

## 📊 Metrics & Columns Reference

**See `Column_Reference.xlsx`** ใน repo root สำหรับ:
- Sales / Discount / GP / Cost column mapping
- Power BI DAX measures (ready to copy)
- SQL query patterns
- Live GP calculator

**Canonical formulas (verified 2026-06-10):**
```
Discount Total = SUM(blh_acc.sodisc)
              = SUM(sodisc_bill + sodisc_coupon + sodisc_perc + sodisc_score)
              ⚠️ อย่ารวม sodisc_bath (subset ของ sodisc_bill)

Net Sales      = Gross Sales − Allocated Bill Discount
GP Amount      = Net Sales − Total Cost
GP %           = GP Amount / Net Sales
```

---

## 🔢 Number Formatting

- **เงิน:** `฿30,691,672` (comma separator, no decimal for big numbers)
- **เปอร์เซ็นต์:** `35.2%` (1 decimal)
- **GP%:** `35.2%`
- **Date Thai:** ใช้ `_TH_MONTHS` (long) / `_TH_MONTHS_SHORT` (short, "ม.ค.")
- **Year:** ทั้ง CE (2026) และ BE (2569) ตามตำแหน่ง

---

## 🎨 Risk Color Convention

| Level | Use case | Reference |
|---|---|---|
| **HIGH** (red) | สาขาเสี่ยงสูง — สะดุดตา | Fraud dashboard store risk |
| **MEDIUM** (orange/yellow) | สาขาเสี่ยงปานกลาง | Fraud dashboard |
| **LOW** (green) | สาขาปกติ | Fraud dashboard |

---

## 🌐 Cross-Origin / Repo Strategy

- **daily-report repo** serves: index, sales, fraud, product, lost_product_dashboard.html (deprecated copy)
- **lost-Product repo** serves: standalone `index.html` (which IS `lost_product_dashboard.html` renamed) + `lost_product_data.json` (~92MB)
- Same `tumsbux.github.io` host → no CORS issue, but fetch uses **relative path** `./lost_product_data.json` since standalone in same repo

---

_Last updated: 2026-06-18_
