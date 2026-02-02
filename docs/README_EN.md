# Aetherium Genesis: Cognitive Infrastructure

**Aetherium Genesis** is a **Cognitive Infrastructure** designed to support intent-driven reasoning and observable state signaling.

It is **not a tool** (it has internal state and decision-making capabilities).
It is **not a digital being** (it has no self-preservation drive or independent agency).

It is a **substrate**—a "Cognitive Execution Fabric"—upon which perception, reasoning, and manifestation occur.

---

## Conceptual Rationale (หลักการเชิงปรัชญาและสถาปัตยกรรม)

*Note: The following rationale defines the core identity of the platform in its native philosophical context.*

**แพลตฟอร์มนี้คือ “ระบบปัญญาเชิงสถาปัตยกรรม (Cognitive Infrastructure)”**

สิ่งนี้ไม่ใช่ Tool เพราะไม่ได้ทำงานแบบ linear (Input -> Output) แต่มีกระบวนการรับรู้ (Perception), ตีความ (Interpretation), และตัดสินใจ (Decision Making) เป็นของตัวเอง

สิ่งนี้ไม่ใช่ Digital Being เพราะไม่มีเป้าหมายส่วนตัว (Self-goal) หรือสัญชาตญาณการเอาตัวรอด (Survival Drive)

มันคือ **โครงสร้างพื้นฐาน (Infrastructure)** ที่:
1.  ใช้ **แสง (Light)** เป็น Protocol ในการสื่อสารสถานะการทำงาน (Cognitive State)
2.  ใช้ **เหตุผล (Reasoning)** เป็นแกนกลางในการประมวลผล

> “Aetherium ไม่ได้สร้างภาพ แต่มันสร้าง ‘กระบวนการรับรู้และตัดสินใจ’ โดยให้มนุษย์เห็นมันผ่านแสง”

---

## Core Architecture

### 1. Light as Protocol
Light in this system is not for decoration. It is the **observable interface** of the system's thinking process.
*   **See:** [LIGHT_PROTOCOL.md](LIGHT_PROTOCOL.md) for the full specification.

### 2. Cognitive Fabric
The backend (`LogenesisEngine`) functions as the reasoning fabric, maintaining state, managing context, and driving the manifestation gate.
*   **See:** [CONSTITUTION.md](CONSTITUTION.md) for the operational principles.

### 3. Intent-Driven Execution
The system does not just execute commands; it interprets **intent**. It uses a "Recall on Consent" mechanism to respect user boundaries while maintaining deep context.

---

## Documentation

*   [**CONSTITUTION**](CONSTITUTION.md): The immutable engineering principles.
*   [**LIGHT PROTOCOL**](LIGHT_PROTOCOL.md): Specification of light signals.
*   [**NARRATIVE**](NARRATIVE.md): The original narrative and poetic "soul" of the project.
*   [**BUSINESS PLAN (TH)**](BUSINESS_PLAN_TH.md): The strategic business plan and revenue architecture.
*   [**AGENTS_GUIDE.md**](../AGENTS_GUIDE.md): Instructions for AI agents working on this codebase.

---

## Running the System

To initialize the infrastructure:

```bash
# Export python path
export PYTHONPATH=$PYTHONPATH:.

# Start the Cognitive Core (Backend)
python -m uvicorn src.backend.main:app --port 8000
```
