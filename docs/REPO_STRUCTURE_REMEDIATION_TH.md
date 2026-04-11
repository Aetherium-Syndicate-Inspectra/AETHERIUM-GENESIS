# ข้อเสนอการจัดระเบียบโครงสร้าง AETHERIUM-GENESIS ตามเอกสาร canonical

## 1. บทสรุปผู้บริหาร

AETHERIUM-GENESIS ไม่ควรถูกตีความเป็นหน้าเดโม, visual playground, หรือ chatbot wrapper แต่ต้องถูกทำให้ชัดเจนว่าเป็น **AI-OS control plane** ที่แปลง `Intent -> Reasoning -> Policy Validation -> Execution -> Memory Commit -> Manifestation` ให้เป็นระบบที่ตรวจสอบย้อนหลังได้, ถูกกำกับด้วย governance, และรักษาความต่อเนื่องผ่าน memory ledger.

**จุดหมายปลายทางสุดท้ายของ repository นี้** ตามเอกสาร canonical คือ:

> เป็น governed AI operating layer / central operating layer ที่ทำหน้าที่เป็นตัวกลางระหว่าง human intent กับ machine action โดยมี governance เป็นด่านบังคับ, memory เป็นแหล่งความจริง, bus เป็น backbone, และ frontend เป็น manifestation surface เท่านั้น.

ใน Phase 1 แบบ cross-repo เอกสารยังระบุบทบาทของ AETHERIUM-GENESIS ให้ชัดว่าเป็น **Mind + Body orchestration surface** ที่รับ intent, เตรียม directive, และส่งผลลัพธ์ไปยัง manifestation surface โดย governance kernel และ canonical bus อาจเชื่อมร่วมกับรีโปอื่นได้.

## 2. เป้าหมายสถาปัตยกรรมที่แท้จริง

จาก `AGENTS.md`, `docs/CANONICAL_TECHNICAL_SPEC.md`, `ARCHITECTURE.md`, และ `docs/UNIFIED_AI_OS_INTEGRATION.md` เป้าหมายที่แท้จริงไม่ใช่ “ทำ UI ให้สวย” แต่คือการทำให้รีโปนี้เป็นแกนกลางของระบบต่อไปนี้:

1. **Mind** — แปล intent, reasoning, planning.
2. **Kernel** — policy, approval, risk tiering, execution gate.
3. **Bus** — event envelope transport และ correlation continuity.
4. **Hands** — vessels/adapters สำหรับลงมือทำงานกับ external systems.
5. **Memory** — append-only ledger, replay, auditability.
6. **Body** — dashboard / GunUI / manifestation surfaces ที่ render ตาม backend เท่านั้น.

ดังนั้น success state ของ repository นี้คือ:

- ทุก action path สำคัญต้องผ่าน governance.
- ทุก execution/outcome ต้องผูกกับ memory chain.
- ทุก subsystem คุยกันผ่าน schema/envelope ชัดเจน.
- frontend ไม่มีสิทธิ์ “สร้างความหมาย” เอง.
- legacy/demo surface ต้องถูกลดบทบาทลงเป็น sandbox หรือ compatibility layer.

## 3. ภาพรวมโครงสร้างปัจจุบัน

### 3.1 สิ่งที่ทำได้ดีแล้ว

รีโปมีองค์ประกอบหลักครบเกือบทั้งหมดแล้ว:

- `src/backend/main.py` ทำหน้าที่เป็น runtime host รวม FastAPI, routers, bus, metrics, entropy, governance runtime, และ startup lifecycle.
- `src/backend/routers/aetherium.py` มี session + `/ws/v3/stream` ซึ่งเป็น canonical ingress สำหรับ envelope-first interaction.
- `src/backend/genesis_core/` รวม bus, governance, logenesis, memory, protocol, vessels, state, audit ไว้ค่อนข้างชัด.
- `src/frontend/index.html` ถูกปรับมาเป็นหน้า landing/operator entry ที่สื่อสาร identity ของแพลตฟอร์มได้ตรงกับ canonical docs.
- `docs/` มีเอกสาร canonical ค่อนข้างครบ ทั้ง technical spec, execution model, architecture audit, directive envelope, roadmap, และ integration guide.

### 3.2 ปัญหาโครงสร้างหลักที่ยังค้างอยู่

แม้แกนหลักจะมีอยู่แล้ว แต่โครงสร้างยัง “สองโลกปะปนกัน” ระหว่าง:

- **canonical platform paths** ที่พยายามเป็น AI-OS จริง
- **legacy / experimental / demo-first paths** ที่ยังอยู่ใน tree เดียวกัน

ผลคือ repository ยังมีภาวะต่อไปนี้:

1. มี **duplicate domain roots** เช่น `src/backend/governance` กับ `src/backend/genesis_core/governance`, `src/backend/vessels` กับ `src/backend/genesis_core/vessels`, `src/backend/memory` กับ `src/backend/genesis_core/memory`.
2. มี **legacy frontend/sandbox pages** จำนวนมากใน `src/frontend/public/gunui/` ที่ไม่ใช่ canonical manifestation path.
3. มี **root-level narrative / manifesto / analysis files** หลายชุดที่ทับซ้อนกัน ทำให้ source-of-truth ของเอกสารไม่ชัด.
4. มี **runtime artifacts / secret-like local files** ปะปนใน repo root เช่น `access_keys.json`, `server_log.txt`, และ data file ที่ควรถูกควบคุมให้ชัดเจนว่า production-safe แค่ไหน.
5. ยังไม่มีโครงสร้างระดับ repository ที่บอกอย่างชัดเจนว่าอะไรคือ `canonical`, อะไรคือ `legacy`, และอะไรคือ `sandbox`.

## 4. สิ่งที่ “ควรลบ” หรือ “ควรถอดออกจาก canonical path”

คำว่า “ลบ” ในที่นี้ควรตีความเป็น 3 ระดับ: **ลบจริง**, **ย้ายไป legacy/sandbox**, หรือ **หยุดอ้างว่าเป็น canonical**.

### 4.1 ควรลบออกจาก root หรือย้ายไปโฟลเดอร์ archive/docs-history

ไฟล์ root ระดับ narrative/analysis ที่ซ้อนกับ `docs/` มากเกินไปควรถูกย้ายออกจาก root เพื่อให้ root เหลือเฉพาะไฟล์สำหรับ runtime + onboarding:

- `AETHERIUM_GENESIS_EXPLAINED.txt`
- `GENESIS_OMNI_STATE_MANIFEST.md`
- `SYSTEM_ANALYSIS_TH.md`
- `USAGE_EN.md`
- `USAGE_TH.md`
- `ARCHITECTURE.md` (ถ้าจะคงไว้ที่ root ต้องระบุให้ชัดว่าเป็น canonical summary; ถ้าไม่เช่นนั้นควรย้ายเข้า `docs/architecture/`)

**ข้อเสนอ:** ให้ root เหลือเพียง `README.md`, `AGENTS.md`, `SECURITY.md`, dependency files, entry scripts, และลิงก์ไปเอกสาร canonical ใน `docs/`.

### 4.2 ควรย้าย `src/frontend/public/gunui/` บางหน้าไป sandbox/non-canonical

ไฟล์ต่อไปนี้มีลักษณะเป็น visual experiment หรือ local heuristic path มากกว่าจะเป็น manifestation surface ที่ผูกกับ backend directives:

- `src/frontend/public/gunui/edge_gunui_connector.html`
- `src/frontend/public/gunui/particle_system.html`
- `src/frontend/public/gunui/light_testbed.html`
- `src/frontend/public/gunui/living_interface.html`
- `src/frontend/public/gunui/nirodha_standby.html`
- `src/frontend/public/gunui/generative_ui.html`

**ข้อเสนอ:**
- ย้ายทั้งหมดไป `src/frontend/sandbox/gunui/` หรือ `src/frontend/public/_sandbox/gunui/`
- หน้าเดียวที่ควรเหลือใน canonical public path คือหน้าที่ consume backend directive envelope โดยตรง
- ทุก sandbox page ต้องติดป้าย non-canonical เหมือน `edge_gunui_connector.html` หรือถูกตัดออกจาก navigation หลัก

### 4.3 ควรลบ/หยุด track ไฟล์ local-sensitive หรือ runtime artifact จาก VCS

ไฟล์เหล่านี้ไม่ควรเป็นส่วนหนึ่งของ repository state ระยะยาว:

- `access_keys.json`
- `server_log.txt`

**ข้อเสนอ:**
- เปลี่ยนเป็น `.example` หรือ dev fixture ที่ไม่มีข้อมูลจริง
- เพิ่มการโหลดจาก environment/secret manager/local ignored file แทน
- เพิ่ม policy ว่า root ห้ามมี runtime dump หรือ access material ที่ mutable

## 5. สิ่งที่ “ควรแก้ไข” โดยเร็ว

### 5.1 แก้ความซ้ำซ้อนของ backend domain roots

ตอนนี้ `src/backend/` มีทั้งสาย canonical และสาย legacy ปะปนกัน ทำให้ developer ไม่รู้ว่า class/logic ใหม่ควรลงที่ไหน.

**อาการที่พบ:**
- `src/backend/governance/` และ `src/backend/genesis_core/governance/`
- `src/backend/vessels/` และ `src/backend/genesis_core/vessels/`
- `src/backend/memory/` และ `src/backend/genesis_core/memory/`
- `src/backend/agents/` และ `src/backend/genesis_core/agents/`

**ข้อเสนอเชิงโครงสร้าง:**
- ให้ `src/backend/genesis_core/` เป็น **canonical subsystem root**
- ให้ package ระดับ `src/backend/governance`, `src/backend/vessels`, `src/backend/memory`, `src/backend/agents` เป็นเพียง:
  - adapter/facade ระยะสั้น หรือ
  - legacy compatibility layer ที่มี deprecation note ชัดเจน
- ห้ามเพิ่ม business logic ใหม่ใน duplicate roots

### 5.2 แก้เส้นแบ่งระหว่าง canonical UI กับ sandbox UI

แม้หน้า homepage ใหม่จะ align แล้ว แต่ใน tree ยังมีหลายหน้า HTML ที่สะท้อน “old identity” ของ repo ในฐานะ visual lab.

**ข้อเสนอ:**
- สร้าง convention ใหม่
  - `src/frontend/public/canonical/` = operator-facing manifestation surfaces
  - `src/frontend/public/dashboard/` = operations UI
  - `src/frontend/public/_sandbox/` = experimental pages
- ตัดลิงก์จาก canonical navigation ไปยังหน้า sandbox
- ทุกหน้า canonical ต้องรับ state จาก backend directive bridge เท่านั้น

### 5.3 แก้ source-of-truth ของเอกสาร

ปัจจุบันข้อมูลสำคัญกระจายอยู่ทั้งใน root และ `docs/`.

**ข้อเสนอ:**
- `README.md` = onboarding + runtime overview แบบสั้น
- `docs/CANONICAL_TECHNICAL_SPEC.md` = technical source of truth
- `docs/directive_envelope_standard.md` = protocol source of truth
- `docs/UNIFIED_AI_OS_INTEGRATION.md` = cross-repo role/boundary source of truth
- audit / roadmap / manifesto แยกเป็นหมวดเฉพาะ

ควรตั้งโครงสร้างเอกสารใหม่ เช่น:

```text
docs/
  canonical/
    technical_spec.md
    execution_model.md
    directive_envelope_standard.md
    subsystem_map.md
  audits/
    architecture_audit.md
    platform_audit_and_workplan.md
  roadmap/
    evolution_roadmap.md
    ai_os_platform_roadmap_th.md
  narrative/
    manifesto_th.md
    concept_sheet.md
  archive/
```

## 6. สิ่งที่ “ควรปรับปรุง” เพื่อไปให้ถึง AI-OS จริง

### 6.1 ทำ canonical governed execution pipeline ให้เห็นเป็นหนึ่งเดียว

ตามเอกสาร เป้าหมายไม่ใช่มี governance อยู่ “บางแห่ง” แต่ต้องเป็น **mandatory path** ทุกครั้งที่มี execution-capable action.

**ควรทำต่อ:**
- สร้าง orchestration utility กลาง เช่น `governed_execution_pipeline`
- ลำดับบังคับ: ingress -> intent normalization -> policy decision -> approval state -> vessel execution -> memory commit -> manifestation emit
- router และ service ทุกตัวต้องเรียกผ่าน pipeline นี้ แทนการประกอบ flow เอง

### 6.2 ทำให้ memory เป็น product infrastructure แบบสมบูรณ์

แม้ `data/akashic_records.json` ถูกระบุเป็น source-of-truth แล้ว แต่ในระดับโครงสร้าง repo ยังดูเหมือนเป็น data file มากกว่าจะเป็น subsystem ที่ชัด.

**ควรทำต่อ:**
- แยก `memory` เป็น package ที่มีชัดเจนทั้ง ledger, projection, replay, export
- แยก fixture/test data ออกจาก canonical data path
- กำหนด retention, export, verification scripts, และ migration strategy

### 6.3 ทำให้ frontend เป็น manifestation-only จริง

เป้าหมายสุดท้ายของ repo คือ frontend ต้อง “แสดงสิ่งที่ระบบตัดสินใจแล้ว” ไม่ใช่ “คาดเดา/สร้างความหมายจาก animation”.

**ควรทำต่อ:**
- สร้าง `directive bridge client` กลางที่ทุกหน้า canonical ใช้ร่วมกัน
- ยุบ logic การตีความ event ฝั่ง client ให้เหลือเฉพาะ render mapping ตาม contract
- แยก diagnostic UI, replay UI, approval UI ออกจาก generative visual experiments

### 6.4 ทำให้ protocol-first มองเห็นได้จาก tree

ปัจจุบัน protocol มีอยู่จริง แต่ tree ยังไม่สื่อพอว่าอะไรคือ boundary contract ที่ทุก subsystem ต้องใช้.

**ควรทำต่อ:**
- ยก `protocol/`, `models/`, `contracts/` ให้เป็นชั้นที่เห็นชัดที่สุดใน canonical backend
- เพิ่ม schema registry หรือ generated contract artifacts สำหรับ frontend/backend/test ใช้ร่วมกัน
- เลิกเพิ่ม implicit payload shape แบบ ad hoc ตาม router/page เฉพาะกิจ

## 7. โครงสร้างเป้าหมายที่แนะนำ

### 7.1 Backend target structure

```text
src/backend/
  app/
    main.py
    routers/
      aetherium.py
      governance.py
      metrics.py
      entropy.py
  canonical/
    protocol/
    models/
    contracts/
    bus/
    mind/
    kernel/
    hands/
    memory/
    audit/
    state/
  integrations/
    auth/
    security/
    external_vessels/
  legacy/
    websocket_v2/
    compatibility/
  sandbox/
    experimental/
```

ถ้าต้องการลด blast radius ในการ refactor สามารถ map กับของเดิมได้แบบนี้:

- `genesis_core/logenesis` -> `canonical/mind`
- `genesis_core/governance` -> `canonical/kernel`
- `genesis_core/bus` -> `canonical/bus`
- `genesis_core/vessels` -> `canonical/hands`
- `genesis_core/memory` -> `canonical/memory`
- `genesis_core/protocol` + `models` -> `canonical/protocol`, `canonical/models`
- package ซ้ำระดับบน -> `legacy/compatibility` หรือ facade ที่ห้ามรับ logic ใหม่

### 7.2 Frontend target structure

```text
src/frontend/
  public/
    canonical/
      index.html
      dashboard/
      gunui/
      replay/
      approvals/
    _sandbox/
      gunui/
      visual_tests/
  shared/
    directive_client/
    render_contracts/
    diagnostics/
```

### 7.3 Docs target structure

```text
docs/
  canonical/
  audits/
  roadmap/
  integration/
  narrative/
  archive/
```

## 8. ลำดับความสำคัญของงานที่ควรทำจริง

### ระยะ 1 — ทำ source-of-truth ให้ชัด

1. ประกาศ `genesis_core` เป็น canonical backend root.
2. ย้ายเอกสาร root ที่ซ้ำซ้อนไป `docs/`.
3. ติดป้าย `legacy` / `sandbox` ให้ทุก path ที่ไม่ใช่ canonical.
4. เอา runtime artifacts และ secret-like files ออกจาก VCS.

### ระยะ 2 — ลดโครงสร้างซ้ำและลด drift

1. หยุดเพิ่ม logic ใหม่ใน duplicate roots.
2. ย้าย frontend experiments ไป `_sandbox`.
3. ทำ shared directive client สำหรับหน้า canonical.
4. ทำ deprecation matrix สำหรับ websocket v2 / legacy paths.

### ระยะ 3 — เสริม platform identity ให้ครบ loop

1. รวม governed execution path ให้เป็น reusable pipeline.
2. เพิ่ม replay/audit/export surfaces ที่อิง memory ledger จริง.
3. เพิ่ม contract test ระหว่าง backend envelope กับ frontend manifestation.
4. ทำให้ approval -> execution -> memory -> manifestation เป็น flow ที่ตรวจสอบได้ end-to-end.

## 9. คำตอบตรงต่อคำถาม: “จุดสุดท้ายของฐานข้อมูลนี้คืออะไร”

หากตีความคำว่า “ฐานข้อมูลนี้” ในความหมายของ repository/system ตามเอกสารทั้งหมด จุดสุดท้าย **ไม่ใช่** การมีหน้าเว็บสวย, particle UI, หรือ chatbot ที่คุยได้ดีขึ้น.

**จุดสุดท้ายคือการทำให้ AETHERIUM-GENESIS กลายเป็น governed AI operating layer ที่ใช้ได้จริง** โดย:

- รับ intent จากมนุษย์หรือระบบ
- แปลงเป็น reasoning/plan ที่มี protocol ชัดเจน
- ให้ governance ตรวจสอบก่อน action
- execute ผ่าน vessels ที่ควบคุมได้
- commit ทุกอย่างลง memory ที่ replay/audit ได้
- manifest ผลลัพธ์ให้มนุษย์เห็นอย่าง faithful

หรือพูดให้สั้นที่สุด:

> เป้าหมายปลายทางคือ “control plane ระหว่าง intent กับ action” ที่ audit ได้, replay ได้, govern ได้, และไม่ปล่อยให้ UI หรือ autonomy ล้ำหน้า governance/memory.

## 10. ข้อเสนอเชิงปฏิบัติที่แนะนำให้เริ่มทันที

1. สร้าง `docs/canonical/` และย้าย canonical docs เข้าไป.
2. สร้าง `src/frontend/public/_sandbox/` แล้วย้าย GunUI experiment pages.
3. ประกาศ policy ว่า `src/backend/genesis_core/` คือ canonical backend implementation root.
4. ทำ `LEGACY.md` หรือ `deprecation matrix` สำหรับ path ซ้ำทั้งหมด.
5. ถอด `access_keys.json` และ `server_log.txt` ออกจาก repository state ปกติ.
6. สร้าง roadmap refactor 3 ระยะ: source-of-truth -> de-duplication -> governed pipeline hardening.

---

เอกสารนี้ตั้งใจเป็น “actionable structure proposal” สำหรับพา repository จากสภาพ “มีของครบแต่ปะปนหลายยุค” ไปสู่สภาพ “เป็น AI-OS platform ที่มี canonical boundaries ชัดเจน” ตามเจตนารมณ์ของเอกสารหลัก.
