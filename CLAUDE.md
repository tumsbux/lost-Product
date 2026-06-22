# CLAUDE.md — Dashboard System Index

**Project:** Tuensjai Panichkroup Co., Ltd. — Data Dashboard Suite
**Owner:** data.inwza.008@gmail.com (tumsbux)
**Working directory:** `F:\co work dashboard\`
**Repos:**
- Main: `tumsbux/daily-report` → https://tumsbux.github.io/daily-report/
- Lost Product: `tumsbux/lost-Product` → https://tumsbux.github.io/lost-Product/

---

## 📂 Documentation (โหลดเฉพาะที่ต้องใช้)

| ไฟล์ | เนื้อหา | โหลดเมื่อ |
|---|---|---|
| [Architecture.md](./Architecture.md) | Tech stack, pipeline, file inventory, DB schema | งานใหม่, แก้ pipeline, สำรวจ DB |
| [Design.md](./Design.md) | Dashboard views, color rules, GA4 | งาน frontend / UI |
| [Decisions.md](./Decisions.md) | ADR — ทำไม schedule แบบนี้, ทำไม split repo | ก่อนเปลี่ยน architecture |
| [Gotchas.md](./Gotchas.md) | Edit tool truncation, sono format trap, PS+git | debug เจอ error แปลก |
| [Roadmap.md](./Roadmap.md) | Phase 3c/3d, B/C/D (OOS / Dead Stock / Visual Adj) | วางแผนต่อ |
| [Changelog.md](./Changelog.md) | งานที่ทำเสร็จ (Phase 3b, Lost Product, etc.) | review |
| [Skill.md](./Skill.md) | บทเรียนส่วนตัว (Edit tool, probe-first, etc.) | ทบทวนเอง |
| [How_To_Modify_Dashboards.md](./How_To_Modify_Dashboards.md) | คู่มือ user สำหรับแก้ UI/ETL/deploy | คนใหม่เริ่มงาน |
| [Column_Reference.xlsx](./Column_Reference.xlsx) | **Quick reference card** — ยอดขาย/ส่วนลด/GP/cost columns + DAX measures + SQL patterns | งาน Power BI / สร้าง measure ใหม่ |

---

## 🤝 Multi-Agent Collaboration (สำคัญ! เพิ่ม 2026-06-10)

User ทำงาน Dashboard ด้วย **2 agents** ขนานกัน:
1. **Claude (Cowork mode)** — Opus 4.7 / Sonnet 4.6 — ตัวที่กำลังอ่านอันนี้
2. **Antigravity (Gemini 3 Flash)** — Google Antigravity IDE — แก้ dashboard ตัวเดียวกัน

**กฎ collab:**
- **อ่าน `.md` ทุกไฟล์ก่อนเริ่มงาน** — ทั้ง 2 agents — ห้าม assume context จาก training
- **เขียน ADR ใน `Decisions.md` ทุก architectural change** — ก่อน touch code
- **Cache file (Phase IR) ต้องมี `_meta.built_by`** — track ว่า agent ไหน build (`claude-opus-4-7` vs `antigravity-gemini-3-flash`)
- **Schema/rule hash header** ป้องกัน agent หนึ่ง schema เปลี่ยน อีก agent อ่าน cache เดิมแล้วงง
- **Roadmap.md "Now" section** = source of truth สำหรับ in-flight work — ห้าม start งานที่ agent อื่น claim ไว้
- **CLAUDE.md** (ไฟล์นี้) = primary doc, ทั้ง 2 agents อ่าน
- **ถ้าเจอ commit ไม่รู้จัก:** อ่าน Decisions.md + Changelog.md ก่อนเสมอ

## 🔒 Verification Gates (จาก AI DevKit concept — เพิ่ม 2026-06-20)

**Rule 1 — No "done" without evidence:**
ทุก Roadmap item ก่อน mark ✅ ต้องมี verification evidence:
- Pipeline change → GHA run log หรือ manual Windows test output
- Dashboard change → screenshot หรือ verify step ใน bash
- SQL change → query result จาก MySQL MCP
ห้าม assume จากการที่ code ดูถูกต้อง

**Rule 2 — Plan-first, no-code-before-approval:**
ทั้ง Claude และ Antigravity: ถ้างานมี architectural impact (ใหม่, เปลี่ยน pipeline, schema, caching) ต้อง:
1. Draft plan ใน Decisions.md (ADR)
2. **STOP — รอ user confirm ก่อน**
3. ห้าม implement จนกว่าจะได้รับการ approve
Reason: Antigravity IR-B/C/D incident 2026-06-10

---

## 🔔 Session Management Rules (user preference)

- **Warn at long context (~85%):** เมื่อรู้สึก conversation ยาวมาก (อ่านไฟล์ใหญ่ + tool หลายรอบ) ให้แจ้งผู้ใช้**ทุกครั้ง**ก่อนทำงานต่อ — แนะนำให้เริ่มแชทใหม่ใน Cowork
- **Summary recap before session ends:** สรุปสิ่งที่ทำในเซสชันให้กระชับ (commit list + ผลลัพธ์หลัก) ทุกครั้งก่อน session อาจถูกตัด
- **Update docs every fix:** ทุกครั้งที่แก้/เพิ่ม feature ให้ sync ไฟล์ที่เกี่ยวข้องทันที + push ขึ้น main
- **ข้อจำกัด:** Cowork ไม่มี `/compact` — วิธีเดียวคือเริ่มแชทใหม่ Claude ไม่สามารถ monitor context % realtime — ต้อง self-estimate
- **Model note:** Opus 4.7 burns limits fast — งาน routine (update, push) ใช้ Sonnet ประหยัดกว่า

---

## ⚡ Quick Context

ระบบ Dashboard อัปเดตอัตโนมัติทุกวัน **08:30 Bangkok** ผ่าน **GitHub Actions** (ไม่ต้องเปิด laptop)

**Daily pipeline (single cron 08:30 BKK — `30 1 * * *` UTC):**
1. Restore cache from orphan branch `cache`
2. `rebuild_fraud_analysis.py --no-push` → builds fraud_data.json *(continue-on-error)*
3. `build_product_data_mysql.py --no-push` → builds product_data.json *(continue-on-error)*
4. `build_lost_product_data.py` → builds lost_product_data.json *(continue-on-error)*
5. push_lost_data → push JSON ไป tumsbux/lost-Product repo
6. `update_dashboard.py` → updates sales + injects fraud/product → pushes daily-report
7. Push cache → orphan branch `cache` (force, single commit)

**Manual run (Windows):**
```powershell
& "F:\co work dashboard\run_manual_update.ps1"          # auto-detect day
& "F:\co work dashboard\run_manual_update.ps1" -Day 1   # specify day
```

---

## 🔑 Critical Rules

- **Sandbox เข้า MySQL host `203.154.83.62:13306` ไม่ได้** — verification ต้องรันบน Windows
- **`db_config.json` ห้าม commit** — มี MySQL password + GitHub PAT
- **Files pushed daily:** `index.html, sales_dashboard_v8.html, fraud_dashboard.html, fraud_analysis.html, fraud_data.json, product_dashboard.html, product_data.json, lost_product_dashboard.html, analytics.js` (lost_product_data.json ไป repo แยก)
- **Edit tool truncation bug** — อย่าใช้ Edit กับไฟล์ HTML/JS > 20KB ใช้ Python via Bash แทน (ดู Gotchas)
- **valid_store rule:** `int(code) <= 500` (excludes 901-999, WBT, WHC, WPT)
- **rebuild_fraud_analysis.py ต้องรันก่อน update_dashboard.py**
- **Two folders for lost-Product:** `F:\lost-Product\` = Cowork working copy (no .git), `F:\lost-Product-git\` = real git clone — edits ต้อง sync ทั้งสอง หรือทำใน `-git\` แล้ว copy กลับ

---

## 🚀 Daily Workflow

1. **เริ่มงานใหม่** → อ่าน `Roadmap.md` ก่อน
2. **ตัดสินใจอะไรสำคัญ** → บันทึกใน `Decisions.md`
3. **เจอ bug แปลก** แก้ได้แล้ว → เพิ่มใน `Gotchas.md`
4. **ทำงานเสร็จ** → update `Changelog.md` + ลบจาก `Roadmap.md`
5. **ไฟล์ไหนยาวเกิน ~300 บรรทัด** → พิจารณาแตกย่อย

---

## 📦 Deployed (ล่าสุด — 2026-06-20)

| งาน | วันที่ | หมายเหตุ |
|---|---|---|
| IR-A Lost Product Parquet cache | 2026-06-10 | cache/lost_qty/store_2021_2025.parquet |
| IR-B/C/D Product/Sales/Fraud cache | 2026-06-12 | orphan branch `cache`, 3 conditions cleared ✅ |
| Compact JSON v2 (77.9→51.9 MB, −33%) | 2026-06-12 | schema v2, daily-report `858db387`, lost-Product `fdeacd1` |
| MySQL MCP (`agent-102`, READ-only) | 2026-06-12 | tools: execute_sql / get_schema_info / get_table_sample — ดู Gotchas §Claude-Desktop-Store |
| VM mirror recovered + SSH creds ย้าย | 2026-06-12–13 | sync 10 นาที, creds ← db_config.json, ops: §4b |
| PAT rotate (`dashboard-bot-4`) | 2026-06-14 | classic, repo+workflow scope — local + VM + GHA updated |
| Phase 3c/3d refactor | 2026-06-14 | update_dashboard −21%, rebuild_fraud −51% lines |
| Phase B Days-until-OOS column | 2026-06-14 | product_dashboard, JS-only, color-coded |
| Thongfah dashboard + GHA (08:35 BKK) | 2026-06-14 | tumsbux/thongfah-dashboard, 168K+ rows — ดู `คู่มือ_Dashboard_ธงฟ้า.docx` |
| **Phase C Dead Stock** | **2026-06-15** | 6,474 products, 90d threshold, group_name dropdown |
| **Phase D Visual Adjustment** | **2026-06-15** | all SKUs, ibl+itd_acc, store-level fraud signal |
| **GHA weekly-rebuild.yml** (lost-Product) | **2026-06-15** | Sundays 09:00 BKK, test run 7m 36s ✅ |
| **Executive Board Report** | **2026-06-18** | Thai executive report modal + print media query overrides on all 4 dashboards |
| **Thongfah & GP Optimizations + Auto-Update** | **2026-06-19** | `build_data.py` + `build_gp_analysis.py` query optimizations (~55s runtime) + added daily GP analysis GHA rebuild workflow in `lost-Product` repo (runs at 08:30 AM & 10:30 AM BKK) |
| **Discount Structure Fix** | **2026-06-19** | Claude: แก้ double-subtraction + double-counting bugs, split discount columns ใน GP Analysis + Thongfah — ดู ADR |
| **GP & Product Analysis June 1-19 Sync & Index Fix** | **2026-06-20** | Antigravity: Added `FORCE INDEX` to `build_gp_analysis.py` to fix GHA query timeouts. Triggered manual GHA runs for both `lost-Product` and `daily-report` to update June 1-19 dashboards (days_elapsed: 19) |
| **Dead Stock Executive Report Fix** | **2026-06-22** | Antigravity: Fixed undefined/NaN values in Dead Stock Executive Report Top 5 table by extracting store metadata directly from product stores array. |

## 🟡 Pending

- [ ] **Rebuild + Push dashboards** — thongfah data.json มี field ใหม่ (sku_disc), gp_analysis_dashboard.html + thongfah index.html แก้แล้วรอ push

- 🖥️ **ขอ IT ตั้ง restart policy VM** (`agent-ab-sandbox.tjinternal.com`) — container ตายแล้วไม่มี auto-restart — ops: `How_To_Modify_Dashboards.md §4b`
- [ ] **ย้าย SSH creds ออกจาก scripts** ใน `F:\lost-Product\` (run_vm_command.py ฯลฯ ฝัง password ใน working copy ของ repo) → ย้ายเป็น config แยก หรือ move ไป `F:\co work dashboard\`
- ⚠️ **Push reminders:** daily-report → `push_files_api.py` เท่านั้น (**ห้าม** `push_py_to_github.py`) / lost-Product → `push_lost_product_files.py` / ไฟล์ > 30MB → `push_data_json.ps1` (git clone) / PAT: `dashboard-bot-4`
- ⚠️ **`F:\lost-Product-git\` stale `index.lock`** — ลบก่อนใช้: `Remove-Item F:\lost-Product-git\.git\index.lock`

---

_Last updated: 2026-06-22_
