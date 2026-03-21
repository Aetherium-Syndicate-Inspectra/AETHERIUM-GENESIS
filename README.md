# AETHERIUM GENESIS (AG-OS)
### Unified AI-OS Platform / แพลตฟอร์ม AI-OS แบบบูรณาการ

![Version](https://img.shields.io/badge/version-2.3.0--platform-blueviolet.svg)
![Status](https://img.shields.io/badge/status-ACTIVE-success.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

> AETHERIUM-GENESIS is a governed AI operating layer that connects human intent, AI reasoning, policy validation, execution, memory continuity, and manifestation.

---

## 📖 Platform Overview / ภาพรวมแพลตฟอร์ม

AETHERIUM-GENESIS is not a demo-first interface or a thin LLM wrapper. It is an AI-OS platform designed to keep cognition, governance, execution, memory, and manifestation structurally aligned.

AETHERIUM-GENESIS ไม่ใช่เดโมหน้าเว็บหรือเพียงตัวห่อหุ้ม LLM แต่เป็นแพลตฟอร์ม AI-OS ที่จัดวางการรู้คิด การกำกับดูแล การปฏิบัติการ หน่วยความจำ และการแสดงผลให้เชื่อมกันอย่างมีโครงสร้าง

### Canonical subsystem map / แผนผังองค์ประกอบหลัก

- **Mind — Logenesis**: intent interpretation, reasoning, planning.
- **Kernel — Governance Core / PRGX-AG**: policy validation, risk controls, approval gates.
- **Bus — AetherBus-Tachyon**: canonical transport and correlation propagation.
- **Hands — Vessels**: execution adapters into workspaces, services, and external systems.
- **Memory — Akashic fabric**: append-only continuity, replay joins, and ledger persistence.
- **Body — GunUI / Dashboard / PWA**: render-only manifestation surfaces driven by backend directives.

- **Mind — Logenesis**: แปลความ intent และวางแผนการทำงาน
- **Kernel — Governance Core / PRGX-AG**: บังคับใช้นโยบาย จัดระดับความเสี่ยง และควบคุมการอนุมัติ
- **Bus — AetherBus-Tachyon**: โครงข่ายสื่อสารหลักพร้อมการส่งต่อ correlation
- **Hands — Vessels**: ตัวเชื่อมสำหรับลงมือปฏิบัติในระบบภายนอก
- **Memory — Akashic fabric**: บันทึกต่อเนื่องแบบ append-only รองรับ replay และ audit
- **Body — GunUI / Dashboard / PWA**: ชั้นแสดงผลที่สะท้อนสถานะจาก backend เท่านั้น

---

## 🧠 Canonical Control Loop / วงจรควบคุมหลัก

`Intent -> Reasoning -> Policy Validation -> Execution -> Memory Commit -> Manifestation`

### Runtime guarantees / หลักประกันของระบบ

- **Envelope-first communication** via the V3 `AetherEvent` schema.
- **Governance-first execution** for destructive or high-impact actions.
- **Memory continuity** with causal chains and replay-ready ledger records.
- **Render-only manifestation** so frontend surfaces never become the semantic source of truth.

- **สื่อสารด้วย envelope เป็นหลัก** ผ่านสคีมา V3 `AetherEvent`
- **Governance มาก่อน execution** สำหรับงานที่มีผลกระทบสูงหรือย้อนกลับไม่ได้
- **หน่วยความจำต่อเนื่อง** ผ่าน causal chain และ ledger ที่ replay ได้
- **Frontend เป็นเพียงชั้นแสดงผล** ไม่ใช่ผู้กำหนดความหมายของระบบ

---

## 🏗️ System Architecture Diagram / แผนภาพสถาปัตยกรรมระบบ

The diagram below is organized around the persisted runtime/data model that backs the control plane: ingress envelopes, governance decisions, approval state, append-only Akashic chain blocks, memory projections, and manifestation views.

แผนภาพด้านล่างจัดตามโครงสร้างข้อมูลที่ runtime ใช้งานจริง ได้แก่ ingress envelopes, governance decisions, approval state, chain blocks ของ Akashic แบบ append-only, memory projections และ manifestation views

```mermaid
flowchart TD
    intent[Intent Input<br/>human / system / API]
    ingress[Ingress Layer<br/>FastAPI + WebSocket]
    envelope[AetherEvent Envelope<br/>correlation_id / trace_id / actor / scope]
    runtime[Directive Runtime<br/>policy decision + outcome orchestration]
    approvals[(approval_state<br/>request_id / status / risk_tier / preview_data)]
    vessels[Execution Vessels<br/>workspace / adapters]
    akashic[(akashic_records.chain[]<br/>timestamp / provenance / payload / correlation / prev_hash / hash)]
    lessons[(memory projections<br/>episodes / semantic / procedures / gems)]
    entropy[(entropy continuity<br/>hash-chain / replay joins)]
    body[Manifestation Layer<br/>dashboard / public / sandbox UI]

    intent --> ingress --> envelope --> runtime
    runtime -->|PENDING_APPROVAL| approvals
    runtime -->|DENIED / REJECTED / ERROR outcome| akashic
    runtime -->|ALLOWED| vessels
    approvals -->|decision event| akashic
    vessels -->|execution outcome| akashic
    akashic --> lessons
    entropy --> lessons
    lessons --> body
```

---

## 🗂️ Repository Layout / โครงสร้างรีโพซิทอรี

- `src/backend/` — runtime, governance, buses, memory, vessels, and API routes.
- `src/frontend/` — homepage, dashboard, GunUI surfaces, and public client assets.
- `docs/` — canonical technical specifications, audits, roadmaps, and integration references.
- `tests/` — regression coverage for governance, protocol, UI, memory, and vessel contracts.

- `src/backend/` — runtime, governance, bus, memory, vessels และ API routes
- `src/frontend/` — หน้าแรก Dashboard GunUI และ static assets ฝั่ง client
- `docs/` — เอกสารสถาปัตยกรรม สเปก การตรวจสอบ และ roadmap
- `tests/` — ชุดทดสอบ regression สำหรับ governance, protocol, UI, memory และ vessel contracts

---

## 🚀 Run the Platform / การรันระบบ

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

Optional visual / ML extensions:

```bash
pip install -r requirements/optional-ml-visual.txt
```

Development and test tooling:

```bash
pip install -r requirements/dev.txt
```

### 2. Configure runtime

```bash
export PYTHONPATH=$PYTHONPATH:.
export BUS_IMPLEMENTATION=tachyon
export BUS_INTERNAL_ENDPOINT=tcp://127.0.0.1:5555
export BUS_EXTERNAL_ENDPOINT=ws://127.0.0.1:5556/ws
export BUS_CODEC=msgpack
export BUS_COMPRESSION=none
export BUS_TIMEOUT_MS=2000
```

### 3. Start the system

```bash
python awaken.py
```

or

```bash
python -m uvicorn src.backend.main:app --host 0.0.0.0 --port 8000
```

### 4. Core access points

- Product homepage: `http://localhost:8000`
- Operations dashboard: `http://localhost:8000/dashboard`
- API docs: `http://localhost:8000/docs`
- Public gateway: `http://localhost:8000/public`

---

## ✅ Recommended validation / ชุดตรวจสอบที่แนะนำ

```bash
pytest -q tests/test_aetherium_api.py tests/test_governance_runtime.py tests/test_governance_router.py tests/test_integration_ui.py tests/test_frontend_homepage.py
```

---

## 🔁 Canonical runtime and compatibility notes

- Runtime governance now resolves through `src/backend/governance/core.py` and `src/backend/governance/runtime.py`.
- `/ws/v3/stream` is the canonical ingress. `/ws` and `/ws/v2/stream` remain compatibility adapters and should not gain new business semantics.
- `src/backend/genesis_core/execution/pipeline.py` is the reusable helper for execution metadata validation and memory commits.
- Sandbox GunUI pages under `src/frontend/public/gunui/` are experimental unless they render backend directive envelopes directly.
- `/sandbox/gunui/*` is the explicit sandbox route. `/gunui/*` remains a compatibility alias and should not gain new semantics.
- Governance and runtime outcomes append ledger records with correlation, causation, decision status, and outcome status for replay.

---

## 📝 Migration note / บันทึกการย้ายสถาปัตยกรรม

### What is canonical now

- `src/backend/governance/*` remains the active governance runtime path for policy evaluation, approval routing, and governed ingress.
- `src/backend/genesis_core/execution/pipeline.py` is the shared execution contract for metadata validation and audit/memory commit behavior.
- Backend-provided governance state, directive state, and replay metadata remain the semantic source of truth for manifestation.

### What remains legacy or sandbox

- `/ws` and `/ws/v2/stream` are compatibility-only sockets.
- `/gunui/*` is a compatibility mount; sandbox-facing usage should move to `/sandbox/gunui/*`.
- Duplicate backend roots outside `genesis_core` remain for compatibility and should avoid new business logic unless required for migration.

### Follow-up still needed

- Migrate more adapters from compatibility roots into `src/backend/genesis_core/*`.
- Replace file-backed approval/key persistence with production-grade storage.
- Expand replay/audit APIs so frontend dashboards can consume backend-authored history directly.

See also: [LEGACY.md](LEGACY.md) for the canonical vs legacy vs sandbox matrix.

---

## 📚 Core documents / เอกสารหลัก

- [docs/CANONICAL_TECHNICAL_SPEC.md](docs/CANONICAL_TECHNICAL_SPEC.md)
- [docs/directive_envelope_standard.md](docs/directive_envelope_standard.md)
- [docs/UNIFIED_AI_OS_INTEGRATION.md](docs/UNIFIED_AI_OS_INTEGRATION.md)
- [docs/AETHERBUS_TACHYON_INTEGRATION.md](docs/AETHERBUS_TACHYON_INTEGRATION.md)
- [docs/ARCHITECTURE_AUDIT.md](docs/ARCHITECTURE_AUDIT.md)

© 2026 Aetherium Syndicate Inspectra (ASI)
