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

**Daily pipeline (07:30–09:30 BKK multi-cron):**
1. `rebuild_fraud_analysis.py --no-push` → builds fraud_data.json *(continue-on-error)*
2. `build_product_data_mysql.py --no-push` → builds product_data.json *(continue-on-error)*
3. `build_lost_product_data.py` → builds lost_product_data.json *(continue-on-error)*
4. push_lost_data → push JSON ไป tumsbux/lost-Product repo
5. `update_dashboard.py` → updates sales + injects fraud/product → pushes daily-report

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

1. **เริ่มงานใหม่** → อ่าน `Roadmap.md` ก่อน (Phase 3c/3d, B/C/D queued)
2. **ตัดสินใจอะไรสำคัญ** → บันทึกใน `Decisions.md`
3. **เจอ bug แปลก** แก้ได้แล้ว → เพิ่มใน `Gotchas.md`
4. **ทำงานเสร็จ** → update `Changelog.md` + ลบจาก `Roadmap.md`
5. **ไฟล์ไหนยาวเกิน ~300 บรรทัด** → พิจารณาแตกย่อย

---

_Last updated: 2026-06-08_
