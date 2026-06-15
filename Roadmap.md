# Roadmap

> งานค้าง + แผนต่อไป — เสร็จแล้วย้ายไป `Changelog.md`

---

## 🔥 Now (สัปดาห์นี้)

- [ ] 🖥️ **ขอ IT ตั้ง restart policy ให้ VM container** (`agent-ab-sandbox`) — `start_services.py` ไม่มี auto-restart (ตาย 11 มิ.ย.) — ขอ ops ADR ด้วยว่าใครเป็นคน setup — size: XS

- [ ] 🔐 **ย้าย SSH creds ออกจาก VM scripts** — `run_vm_command.py` / `check_vm_status.py` / `push_to_vm.py` / `upload_test.py` ใน `F:\lost-Product` ฝัง password (อยู่ใน working copy ของ repo public) → ย้ายเป็น config แยกแบบ `db_config.json` หรือย้าย scripts ไป `F:\co work dashboard\` — size: XS

---

## 📅 Next (Sprint หน้า)

_ไม่มี items ที่กำลังรอ — ดู 💭 Later สำหรับงานถัดไป_

---

## 💭 Later (อยากทำ ยังไม่เร่ง)

- [ ] **verify GHA weekly-rebuild รอบถัดไป (Sunday 2026-06-22)** — เช็ค step Restore cache ใน daily-report ยัง + weekly-rebuild step เขียวครบ — size: XS

- [ ] **Phase E: อะไรถัดไป** — TBD — รอ user กำหนด

---

## 🧊 Icebox

- ~~Real-time stream processing~~ — daily batch ดีพอ
- ~~Move to self-hosted MySQL backend~~ — rejected (see Decisions.md)
- ~~Migrate all scripts to use `lib/`~~ — Phase 3 strategy ดีกว่า
- ~~`update_dashboard_v1_backup.py`~~ — clean up after stable Phase 3b
- ~~`CLAUDE.old.md` (73KB backup)~~ — ลบได้เมื่อมั่นใจ split สมบูรณ์

---

## 🐛 Known Issues

- [ ] `fetch_missing_facts.py` warning ในทุก daily run — severity: low — ชี้ไปที่ `scripts/explore/fetch_missing_facts.py` แทน
- [ ] pandas SQLAlchemy warning ทุกครั้งที่รัน — severity: low
- [ ] Console cmd window ค้างทั้งวัน — severity: low (cosmetic)

---

## 🎯 Quarterly Goals

### Q2 2026
- [x] Lost Product dashboard (live at https://tumsbux.github.io/lost-Product/)
- [x] Phase 3b/3c/3d refactor (–51% lines, verified zero drift)
- [x] Documentation split (CLAUDE.md 73KB → 8 files)
- [x] Phase IR-A/B/C/D Caching (Parquet + orphan branch `cache`)
- [x] Compact JSON v2 (77.9→51.9 MB, −33%)
- [x] Thongfah dashboard + GHA (08:35 BKK daily, 168K+ rows)
- [x] Phase B: Days-until-OOS column (product_dashboard)
- [x] Phase C: Dead Stock report (6,474 products, group_name, GHA weekly)
- [x] Phase D: Visual Adjustment audit (all SKUs, store-level signal)
- [x] MySQL MCP live (agent-102 READ-only, Cowork Sonnet)
- [ ] VM auto-restart policy (pending IT)
