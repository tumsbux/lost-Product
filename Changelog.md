# Changelog

> งานที่ทำเสร็จ — เรียงจากใหม่ → เก่า
> Format: [Keep a Changelog](https://keepachangelog.com/)

---

## [2026-07-11] Fix: silent MySQL disconnect crash in build_lost_product_data.py (Claude, Cowork)

### Root cause
- GHA runs #87 (08:58 BKK) and #88 (09:57 BKK) today both showed job Status "Success" but step "Build lost product data" actually failed with exit code 1 — masked by `continue-on-error: true` in `daily-update.yml`
- Identical symptom to `build_store_discount_data.py`'s Jul 10 crash (Changelog `[2026-07-10]` in `co work dashboard` repo) — one long-lived MySQL connection held across the whole script run, including the heavy current-year JOIN + batched name/branch lookups, which run LATE in the pipeline after other DB-heavy steps
- This is exactly the "not yet done" item flagged in that earlier fix's Changelog entry

### Fixed — `build_lost_product_data.py`
- Added `_run_with_retry(cfg, fn, *args, **kwargs)` — opens a fresh connection per call, retries up to 3x (5s backoff) on errno 2013 ("lost connection during query") / 2006 ("server has gone away")
- `query_year()` (current year), `query_branch_info()`, `query_name_map()` now each get their own fresh connection via the wrapper instead of sharing one `conn` opened at the top of `main()`
- Verified via `python3 -m py_compile` on a reconstructed copy (bash mount workaround, per Gotchas.md)
- ADR in `Decisions.md` `[2026-07-11]`

### Not yet pushed
- Sandbox has no direct network access to `api.github.com` (proxy allowlist blocks it) — fix is saved locally in `F:\lost-Product\build_lost_product_data.py` but needs the user to run `push_lost_product_files.py` on their own machine to deploy, then verify the next GHA run has no exit-code-1 annotation on "Build lost product data"

## [2026-06-23] Lost Product Dashboard Auto-Update Fix (Claude)

### Fixed
- **🔄 `lost_product_data.json` ไม่อัปเดตรายวัน**: root cause คือ `daily-update.yml` ใน lost-Product repo ไม่มี step สำหรับ `build_lost_product_data.py` — ข้อมูลถูก build แค่จาก daily-report GHA ซึ่ง push ล้มเหลวมาตั้งแต่ 6 มิ.ย.
- **📋 `daily-update.yml`** — แก้หลายรอบ (commits `e38a1cf` → `6bbf3e0` → `d094a9f` → `db16084` → `f6d57a8`):
  - เพิ่ม "Restore parquet cache" step: `git fetch origin cache` + `git checkout FETCH_HEAD -- cache/` + `git reset HEAD cache/` (unstage)
  - เพิ่ม "Build lost product data" step (continue-on-error, timeout 20 min)
  - เพิ่ม `pyarrow` ใน pip install (ขาดทำให้ pandas.read_parquet() crash)
  - เพิ่ม `git pull --rebase origin main` ก่อน `git push` (ป้องกัน push rejection จาก concurrent runs)
  - เพิ่ม `git reset HEAD cache/` ซ้ำใน commit step (ป้องกัน parquet ถูก commit ไปบน main)
  - เพิ่ม job timeout 15 → 45 min
- **🏷️ `build_lost_product_data.py`**: แก้ `built_by` จาก hardcoded `antigravity-gemini-3-flash` เป็น `dashboard-bot`
- **🌿 Orphan branch `cache`**: สร้าง branch ใน `tumsbux/lost-Product` เก็บ `cache/lost_qty_2021_2025.parquet` (1.3MB) + `cache/lost_store_2021_2025.parquet` (32MB)
- **🚫 `.gitignore`**: เพิ่ม `cache/*.parquet` ป้องกัน parquet ถูก commit ไป main branch โดยไม่ตั้งใจ (commit `db16084`)
- **🧹 Cleanup**: ลบ parquet files ที่ commit ไป main โดยไม่ตั้งใจ (`git rm --cached`, commit `d094a9f`)

## [2026-06-22] Fix undefined and missing store info in Dead Stock Executive Report (Antigravity)

### Fixed
- **📋 Dead Stock Dashboard Executive Report**: Fixed the `undefined` store code and `NaN` values shown in the Top 5 Locked Inventory Branches table of the Executive Report modal.
- **🏬 Store Metadata Extraction**: Rewrote `openExecutiveReport()` in `dead_stock_dashboard.html` to aggregate store name, DM, and RM properties directly from the product stores array in `dead_stock_data.json` instead of relying on the empty `data.store_info` object, resolving the `'ไม่ระบุ'` ('Unspecified') and `'undefined'` display issues.
- **🚀 Deploy**: Pushed the updated `dead_stock_dashboard.html` file directly to the `tumsbux/lost-Product` repository via the GitHub Contents API, and synchronized it with the local `F:\lost-Product-git\` mirror.

## [2026-06-20] GP & Product Analysis June 1-19 Sync and Performance Fix (Antigravity)

### Fixed
- **⚡ GP Analysis Database Query Timeout (GHA)**: Added `FORCE INDEX (idx_optimize_sales_report)` to both queries in `build_gp_analysis.py`. This resolved the 15-minute query timeout issue on the `fact_sales` table which was causing the `Daily GP Analysis Rebuild` workflow to be cancelled. The query now finishes in ~3.3 minutes on GHA.
- **📅 June 1–19 Data Rebuild**: Manually triggered the GHA workflows for both `lost-Product` (`Daily GP Analysis Rebuild`) and `daily-report` (`Daily Dashboard Update`). Both completed successfully, updating:
  - `gp_analysis_dashboard.html` / `gp_analysis_data.json` to show **วัน 1-19** (June 1-19, 2026).
  - `product_dashboard.html` / `product_data.json` to show **วัน 1-19** (June 1-19, 2026).
- **⚙️ Auto-Update Verification**: Verified that:
  - GP Analysis, Thongfah, and Product/Sales/Fraud dashboards are scheduled and configured to auto-update daily.
  - The weekly rebuild for Dead Stock and Visual Adjustment is scheduled for Sundays at 09:00 BKK and will run automatically tomorrow morning (June 21).

## [2026-06-19] Bill-level Comparison: blh_acc/bld_acc vs fact_sales (Claude)

### Added
- **📊 Bill-level comparison Excel report** (`bill_level_comparison.xlsx`) — 7 sheets:
  1. สรุปผลที่แก้ไขแล้ว (corrected summary)
  2. สาเหตุของผลต่าง (root cause decomposition — 100% explained)
  3. รายบิลที่มีส่วนลด (top 30 bills with prorated_discount)
  4. โครงสร้างส่วนลด (discount field relationships)
  5. sotype=3 detail (77 bills in DW but filtered from ACC query)
  6. SQL ที่ถูกต้อง (corrected queries)
  7. sodisc_bath วิเคราะห์ (sodisc_bath is supplementary field, not in sodisc formula)

### Fixed (BUG corrections from earlier report)
- **⚠️ Double-subtraction bug:** `SUM(net_sales_amt - prorated_discount)` double-deducted bill discounts → correct: `SUM(net_sales_amt)` directly (34,268,972 vs wrong 34,083,851)
- **⚠️ Double-counting bill discounts:** `sodisc + sodisc_bill + sodisc_score` counted twice → correct: `sodisc` alone = 195,376 (not 390,752)

### Documentation updated
- `Architecture.md` — added gap analysis results, sodisc_bath deep analysis, BUG warnings
- `Gotchas.md` — added net_sales_amt double-subtraction trap + sodisc double-counting trap

### Findings
- **Data quality 99.95%** — 228,070 bills match perfectly, zero actual data corruption
- **Gap ฿110,228** = prorated_discount (−185K) + sotype=3 (+75K) + rounding (~207฿)
- `sodisc_bath` = supplementary copy of `sodisc_bill` (recorded in only 36/602 bills), not used in calculations
- `sodisc_score` unit = baht (not points), most common value = 20฿

---

## [2026-06-19] Thongfah & GP Analysis Dashboard Optimizations and Updates (Antigravity)

### Fixed
- **⚡ Thongfah Query Timeout**: Replaced `CAST(f.sotowhs AS UNSIGNED) <= 500` with the indexed string comparison `f.sotowhs >= '001' AND f.sotowhs <= '500'` and added `FORCE INDEX (idx_optimize_sales_report)` to the query in `thongfah_dashboard/build_data.py`. This resolved the 5-minute timeout failures on GitHub Actions, reducing execution time to ~55 seconds.
- **📅 Thongfah Data Range Update**: Manually rebuilt the dataset locally to include data up to `2026-06-18` (181,382 rows) and successfully pushed `data.json` to GitHub using `push_data_json.ps1` to resolve the user's report of stale date ranges.
- **🚀 Thongfah Code Sync**: Deployed the optimized `build_data.py` script to the `tumsbux/thongfah-dashboard` repository to recover the automated daily update workflow.
- **⚡ GP Analysis Query Optimization**: Optimized the SQL queries in `build_gp_analysis.py` by replacing the CPU-heavy `CAST(sotowhs AS UNSIGNED)` with `sotowhs >= '001' AND sotowhs <= '500'` and changing the `YEAR(sodate) = %s AND MONTH(sodate) = %s` filter to an indexed range search (`sodate >= %s AND sodate < %s`). Also cleaned all unicode arrow characters (`→` / `\u2192`) causing crashes on standard Windows consoles.
- **📅 GP Analysis Data Range Update**: Rebuilt and pushed `gp_analysis_data.json` successfully (covering up to `2026-06-18`, 2,054,783 rows) to resolve the user's report of stale date range.
- **🚀 GP Analysis Code Sync**: Deployed the optimized `build_gp_analysis.py` to the repository.
- **⚙️ GP Analysis Auto-Update**: Created and deployed `.github/workflows/daily-update.yml` in the `lost-Product` repository to automatically run the builder daily at 08:30 AM (for initial update) and 10:30 AM Bangkok time (after the MySQL ETL completes to get yesterday's freshly synced data), keeping the dashboard updated automatically every morning.

## [2026-06-18] Executive Board Report (รายงานสรุปสำหรับผู้บริหาร) (Antigravity)

### Added
- **📋 Executive Report** button and modal on all 4 dashboards (`gp_analysis`, `dead_stock`, `lost_product`, `visual_adj`).
- `@media print` style overrides to isolate the report modal and format it beautifully for A4 paper printouts.
- **Dynamic JavaScript Reports**:
  - `gp_analysis_dashboard.html`: Dynamically groups store sales/costs/GP by RM and DM and compiles them into performance scorecards.
  - `dead_stock_dashboard.html`: Promoted local variables to global (`META`, `SUMMARY`, `STORE_INFO`) and dynamically displays the Top 5 locked inventory stores.
  - `lost_product_dashboard.html`: Summarizes active, stale, and lost SKU counts, extracts the Top 10 lost products by sales impact (`lost_score`), and outlines replenishment safety buffers.
  - `visual_adj_dashboard.html`: Dynamically counts High-Risk (net > ฿1M) and Medium-Risk (฿300k–฿1M) adjustment branches, lists the Top 5 outlier stores, and details security recommendations (CCTV and POS lockdowns).

### Changed
- Synced the updated HTML files to `F:\lost-Product-git` mirror.
- Deployed the changes to GitHub main branch using `push_lost_product_files.py` REST API script.

---

## [2026-06-17] AI bar + Cascading RM/DM filters + Visual polish (Claude)

### Added
- **AI Analysis bar** ทุก 4 dashboards: gp_analysis (4 buttons), dead_stock (4 buttons), visual_adj (4 buttons), lost_product (4 buttons) — CSS `.ai-bar`/`.ai-btn`/`.ai-modal` + `aiAnalyze()` context-specific per dashboard
- **Cascading RM/DM dropdown filters**: selecting RM filters DM options and vice versa
  - `gp_analysis_dashboard.html`: `refreshDropdowns()` — called after `renderStores()` in `applyStoreFilters()`
  - `visual_adj_dashboard.html`: `refreshStoreDropdowns()` — replaces static population
  - `lost_product_dashboard.html`: `refreshRmDmDropdowns()` — integrated with existing `onScopeChange()` + `rebuildStoreOptions()`
  - dead_stock has type/group filters only (no RM/DM) — no cascading needed
- **Discount KPI card** (gp_analysis): purple card showing Discount MTD from `disc` field
- **MoM comparison cards** (gp_analysis): 5 cards with ▲/▼ vs previous month

### Fixed
- **gp_analysis_dashboard.html corruption**: AI JS injected inside Chart.js CDN script tag + file truncated at line 454 — complete rebuild from clean GitHub version
- **Column width wrapping** (gp_analysis): ประเภท/กลุ่ม columns — added `white-space:nowrap` + `max-width` + `text-overflow:ellipsis`
- **Cascading filter bug** (3 iterations): (1) dropdowns empty on load → add `refreshDropdowns()` call, (2) selected value lost after DOM rebuild → restore value, (3) `refreshDropdowns()` called before reading values → moved to after filter+render

---

## [2026-06-16] lost_product_dashboard hydration fix + MemoryError fixes + cron 10:30 (Claude)

### Fixed
- **`lost_product_dashboard.html` undefined ทุกค่า**: compact schema v2 เก็บ products เป็น array-of-arrays แต่ JS อ่านเป็น object properties → เพิ่ม hydration block แปลง array→object — commit `e2542204`
- **Fetch URL typo**: `lost-Product-/` → `lost-Product/` (hyphen เกิน) — commit `15495d29`
- **parcode แสดงเป็น index แทน barcode จริง**: `parcode`/`iprod` เก็บเป็น index ของ `codes[]` — เพิ่ม `codes[p.parcode]` resolve + `store_breakdown` key resolve ตาม `index.html` — commit `f435c889`
- **Push ผิด repo**: ใช้ `push_files_api.py` (→ daily-report) แทน `push_lost_product_files.py` (→ lost-Product) ทำให้ push เวอร์ชันเก่า
- **`fraud_agg.py` OverflowError** (line 116 `to_json()`): เพิ่ม `import gc` + `gc.collect()` 2 จุดใน `build_month()` — June data build สำเร็จ `1,640 bills | ฿262,230` ✅ — commit `0146bf84`
- **`build_lost_product_data.py` MemoryError** (`fetchall()` 1M+ rows): เพิ่ม `gc.collect()` + `del df/df2` รอบ `pd.read_sql()` ทั้ง 2 query ใน `query_year()` — commit `4611c9c8`
- **Dashboard stuck วัน 14**: `update_dashboard.py` git clone exit 128 (false "OK") → push manual ผ่าน `push_files_api.py` 8 ไฟล์ — commit `85756424` — dashboard แสดงวัน 15 ✅

### Added
- **cron-job.org 10:30 BKK** (`Trigger daily-report GHA 10.30`, job 7833703): เปิด job ที่มีอยู่แต่ inactive → enabled — trigger รอบ 2 หลัง ETL sync เสร็จ (fact_sales มักพร้อม ~10:27+)
- **cron-job.org 10:35 BKK** (`Trigger thongfah GHA 10.35`): ยืนยัน active อยู่แล้ว

### Root cause (ETL timing)
`fact_sales` ข้อมูลร้านค่าปลีก (sotowhs ≤ 500) sync เสร็จหลัง 10:27 BKK — GHA 8:30 ได้แค่วันก่อนหน้า, cron 10:30 catch หลัง ETL พร้อม

### Gotchas updated
- เพิ่ม 3 entries: `fraud_agg.py OverflowError`, `build_lost_product_data.py MemoryError`, `git clone exit 128 false positive`

---

## [2026-06-15] cron-job.org — GHA trigger ตรงเวลา (Claude)

### Added
- **cron-job.org** trigger 3 repos ผ่าน GitHub API `workflow_dispatch` (ไม่มี free-tier delay อีก):
  - `Trigger daily-report GHA` → 08:30 BKK ทุกวัน (`30 8 * * *` Asia/Bangkok)
  - `Trigger thongfah GHA` → 08:35 BKK ทุกวัน (`35 8 * * *`)
  - `Trigger lost-Product weekly GHA` → 09:00 BKK ทุกอาทิตย์ (`0 9 * * 0`)
- Headers: `Authorization: token <PAT>` / `Accept: application/vnd.github.v3+json` / `Content-Type: application/json`
- Body: `{"ref":"main"}` — ทุก job test run 204 No Content ✅

---

## [2026-06-15] docs: compact + update all .md files (Claude)

### Changed
- `CLAUDE.md` (−42%): Pending Approval ยาว → Deployed table + 4 Pending bullets
- `Roadmap.md` (−74%): ตัด [x] items ออกหมด เหลือ 2 pending + Q2 goals
- `Gotchas.md`: เพิ่ม 2 entries (MemoryError/gc.collect, push ผิด repo)
- `Decisions.md`: เพิ่ม 2 ADR (push_lost_product_files.py, weekly-rebuild.yml)
- Commits: `97bce37e` (CLAUDE.md) + `9f2725e9` (Roadmap.md) + `42c31ab2` (Gotchas.md) + `7c407fa0` (Decisions.md)

---

## [2026-06-15] Phase C+D: fixes + GHA weekly-rebuild (Claude)

### Fixed
- **Dead Stock**: กรองกลุ่มไม่ใช่ retail ออก (`EXCLUDED_ITY + EXCLUDED_IGRCODE`) → 6,917 → 6,474 products
- **Dead Stock**: กรอง null parcode + สินค้าไม่มีชื่อใน dim_product
- **Dead Stock**: dropdown กลุ่มแสดง `igrdesc` — เพิ่ม `query_group_names()` + field `group_name` ใน JSON
- **Visual Adj**: ลบ LIMIT 500 → all SKUs (49,094)
- **Visual Adj**: แก้ UnicodeEncodeError (cp874) + `datetime.utcnow()` deprecation
- **`gc.collect()`**: เพิ่มระหว่าง step ใน `build_dead_stock.py` ป้องกัน MemoryError

### Added
- **`push_lost_product_files.py`**: push → `tumsbux/lost-Product` ผ่าน Contents API + `--repo-path` flag
- **`.github/workflows/weekly-rebuild.yml`**: GHA ทุกอาทิตย์ 09:00 BKK — test run 7m 36s ✅
- Secrets ใน lost-Product: DB_HOST/PORT/USER/PASSWORD/DB_DATABASE/GH_PAT

### Commits
`038d284d` (dead_stock_data.json) + `316367a5` (dead_stock_dashboard+build_dead_stock) + `22c92f7b` (push script) + `26575150` (workflow) + `c1f41ca9` (Changelog)

---

## [2026-06-15] Phase D: Visual Adjustment Audit (Claude)

### Added
- **`build_visual_adj.py`**: ibl (locno=visual, shelfno=adjustment) + itd_acc UNION — 204 stores / 49,094 SKUs / 41,205 sessions — net_qty=−10,455,868 / net_value=฿−332,447,546
- **`visual_adj_dashboard.html`**: 3 tabs (ตามร้าน/ตามสินค้า/Sessions), risk badge HIGH/MED/LOW
- Commits: `e95cf2a7` (data 13.6MB) + `a75e68f5` (dashboard+script)

---

## [2026-06-14] งานทั้งหมดในวันนี้ (Claude + Antigravity)

| งาน | ผล |
|---|---|
| Phase C Dead Stock | `build_dead_stock.py` + dashboard — 6,917 products, ฿12.2M — threshold 90d |
| Phase B Days-until-OOS | product_dashboard.html col 12 — 🔴≤7d 🟠≤14d 🔵>14d — JS-only |
| Phase 3c/3d refactor | update_dashboard 1160→939L (−21%), rebuild_fraud 934→458L (−51%) |
| bugfix(3c) whsdd loop | 7 lines dropped → day_totals never populated → `target(d1-0)` ทุก run — restored |
| bugfix(3c) THAI_MON | Phase 3c surgery ลบ script code ระหว่าง func defs — restored L619-644 |
| bugfix(fraud) rttime | `str[:2]` บน "0 days 18:00:20" → "0 " → 07:00 ทุกตัว — Antigravity fix `_parse_time_row()` ✅ GHA Run 27503699346 |
| Thongfah GHA live | daily-update.yml, 168,753 rows, 08:35 BKK — Secrets added, GHA Run #1 ✅ |
| Thongfah fixes | %GP tfoot, CSS tfoot, GROUP BY sodate→DATE(f.sodate), git stderr PS |
| Verify 210 stores | 203 active + ~7 historical, 901/999=warehouse filtered ✅ — no bug |
| PAT rotate | `dashboard-bot-4` (classic repo+workflow) — local+VM+GHA updated |

---

## [2026-06-12] งานทั้งหมดในวันนี้ (Claude + Antigravity)

| งาน | ผล |
|---|---|
| Cache orphan branch | Option A: force-push → branch `cache`, main cleaned — commits d57451ee+b42be68c+dd6fb478 |
| Compact JSON v2 | 77.9→51.9MB (−33%), schema v2, codes index — daily-report `858db387`, lost-Product `fdeacd1` |
| MySQL MCP live | agent-102 READ-only, tools execute_sql/get_schema_info/get_table_sample ✅ |
| VM mirror กู้คืน | agent-ab-sandbox restart via SSH, sync 10min — SSH creds ย้ายออก 2026-06-13 |
| build_grouped_with_barcodes | v2 decode + join key fix — รันจริง Windows ✅ (65,812 products parity) |
| Lost Product × Onhand xlsx | `build_lost_onhand_xlsx.py` — 97,475 rows, ฿68.5M, streaming write_only |
| push_files_api.py | selective push daily-report ผ่าน Git Data API |
| IR เงื่อนไข 1 | fraud cache lag → document-only (user decision, circular dependency) |
| IR เงื่อนไข 3 | repo bloat → orphan branch cache (approved + deployed) |

---

## [2026-06-11] งานทั้งหมดในวันนี้ (Claude + Antigravity)

| งาน | ผล |
|---|---|
| onhand=0 fix | stream tuple cursor + gc + better except logging → 936,307 rows ✅ |
| Product YoY same-period | filter prev-year day<=days_elapsed — `47.6M YoY +21.8%` verified |
| JSON size investigation | 74.2MB > 70MB threshold → ADR compact encoding proposed |
| Phase IR audit | Antigravity implement IR-B/C/D โดยไม่ผ่าน user → escalated, user accept มีเงื่อนไข |

---

## [2026-06-10] Phase IR Caching (Antigravity + Claude verify)

- IR-A Lost Product Parquet: 2021-2025 → `cache/lost_qty/store_2021_2025.parquet` — 3 min → <30s
- IR-B Product MTD: `cache/product_mtd_{YYYY-MM}.parquet` — daily upsert D-7..D-1
- IR-C Sales Daily: `cache/sales_daily_{YYYY-MM}.json` + `sales_monthly_tot.json`
- IR-D Fraud: freeze M-3 into `cache/fraud_closed_{YYYY-MM}.json`, score from IR-C cache
- Sunday full-refresh auto-detect (Bangkok timezone) in GHA
- `lib/safe_write.py`: `safe_write_parquet()` schema validation + re-read check

---

## [2026-06-09] Standalone deployment workflow (Antigravity)

- VM `start_services.py`: commit-SHA sync ทุก 10 นาที (แทน time-based)
- GHA + `push_lost_data.ps1`: push `index.html` + `analytics.js` ไป lost-Product พร้อม JSON
- Removed deprecated `lost_product_dashboard.html` จาก daily-report

---

## [2026-06-08] Documentation split (Claude)

- CLAUDE.md 73KB → 8 files: Architecture / Design / Decisions / Gotchas / Roadmap / Changelog / Skill.md
- Mirror copies ที่ `F:\lost-Product\`

---

## [2026-06-06] Lost Product — size + store fix (Claude + Antigravity)

- **Size**: MIN_QTY 5→15, MIN_AMT=3000 OR logic → 97MB → ~45-55MB (−40-50%)
- **Store**: เปลี่ยนจาก `SUBSTRING(sono,3,4)` → JOIN blh_acc ใช้ `sotowhs` → 79 → 210 stores ใน store_breakdown
- Commits: `2560cc4`, `7321daf`

---

## [2026-06-05] Lost Product — Phase A onhand + ipunit3 fix (Claude)

- Phase A: onhand per store จาก `MYWMS2023_CENTER.ibl WHERE locno='stock' AND shelfno='shelfno'`
- `ipunit3` source: `dim_product` (ไม่ใช่ `dim_item_barcode` ที่ไม่มี column นี้) → 13,074/13,077 nonzero
- Lost Product ย้ายไป standalone repo `tumsbux/lost-Product` (แยกจาก daily-report เพราะ JSON > 50MB)

---

## [≤2026-06-04] Sales / Fraud Dashboard foundation (Claude + Antigravity)

- Phase 3b: update_dashboard 1215→1006L, extract `dashboards/helpers.py` + `mysql_queries.py`, verified byte-diff
- YoY same-source sync: header + monthly list อ่านจาก fact_sales เดียวกัน
- JS Proxy dynamic MTH dict (แทน static const)
- Fraud template restore (full-featured จาก commit afaa0d5)
- `solinetype NOT IN ('C','R')` filter (แทน `=='N'`)
