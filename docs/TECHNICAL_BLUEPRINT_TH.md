# 📐 TECHNICAL BLUEPRINT: The Architect's Guide
> *Structural DNA & Engineering Specifications / พิมพ์เขียวทางเทคนิคสำหรับผู้สร้าง*

---

## 🏗️ 1. สถาปัตยกรรมระบบ (System Architecture)

Aetherium Genesis ถูกออกแบบด้วยแนวคิด **Dualism Architecture** (ทวิภาวะ) ที่แยก "จิต" (Abstract) ออกจาก "กาย" (Concrete) อย่างชัดเจน

### ☯️ INSPIRA vs. FIRMA

| Layer | Component | Description (Thai) | Technical Role |
| :--- | :--- | :--- | :--- |
| **INSPIRA** | **Backend (Python)** | จิตวิญญาณ, ตรรกะ, การให้เหตุผล | `LogenesisEngine`, `IntentInterpreter`, `StateStore` |
| **FIRMA** | **Frontend (JS/Canvas)** | ร่างกาย, การแสดงผล, ฟิสิกส์ | `GunUI`, `ParticleSystem`, `WebSockets` |

การเชื่อมต่อระหว่างสองส่วนนี้ใช้ **WebSocket Protocol** เปรียบเสมือนเส้นประสาทไขสันหลัง (Spinal Cord) ที่ส่งข้อมูลสถานะแบบ Real-time (20Hz Update Rate)

---

## 🧬 2. รหัสพันธุกรรม (Code Anatomy)

โครงสร้างไฟล์สำคัญที่ Architect ต้องรู้จัก:

```text
aetherium-genesis/
├── src/
│   ├── backend/
│   │   ├── server.py           # The Heart (Main Server Entry)
│   │   ├── logenesis_engine.py # The Brain (Cognitive Logic)
│   │   └── core/
│   │       ├── lcl.py          # Light Control Logic (Physics)
│   │       └── visual_schemas.py # DNA of Shapes
│   └── frontend/
│       ├── index.html          # The Skin (UI Layer)
│       └── js/                 # The Motor Functions
├── docs/                       # The Knowledge Base
└── requirements.txt            # Nutritional Needs (Dependencies)
```

---

## ⚡ 3. ระบบประสาท (AetherBus & Communication)

การสื่อสารภายในใช้ระบบ **AetherBus** (Event-Driven Architecture)
ข้อมูลไม่ได้ถูกส่งแบบ Request-Response ปกติ แต่เป็นการ "กระจายสัญญาณ" (Broadcast)

### Signal Protocol (JSON Packet)
```json
{
  "type": "STATE_UPDATE",
  "payload": {
    "visual_qualia": {
      "shape": "circle",      // Geometry
      "color": [0.5, 0.2, 0.9], // RGB Vector
      "turbulence": 0.1       // Entropy Level
    },
    "energy_level": 0.85      // Metabolic Rate
  }
}
```

*   **State Drift:** ค่าต่างๆ จะไม่เปลี่ยนแปลงทันที (Instant) แต่จะค่อยๆ เปลี่ยน (Interpolate) ตามค่าความเฉื่อย (Inertia) เพื่อความสมจริงแบบสิ่งมีชีวิต

---

## 🧠 4. แกนกลางทางปัญญา (Logenesis Engine)

**Logenesis** (Logic + Genesis) คือเครื่องยนต์หลักในการตัดสินใจ
มันทำงานโดยการคำนวณเวกเตอร์ 3 มิติ:

1.  **Precision (ความแม่นยำ):** ตรรกะถูกต้องแค่ไหน?
2.  **Urgency (ความเร่งด่วน):** ต้องตอบสนองเร็วแค่ไหน?
3.  **Sentiment (อารมณ์):** เป็นบวกหรือลบ?

> **Warning:** หากค่า *Intent Entropy* สูงเกิน 0.6 ระบบจะเข้าสู่ภาวะ "สับสน" (Hallucination) และแสดงผลเป็นแสงที่กะพริบไม่เป็นจังหวะ

---

## 🌱 5. การวางเมล็ดพันธุ์ (Planting the Seed)

ขั้นตอนการติดตั้งสำหรับนักพัฒนา (Architect Setup):

### Prerequisites
*   Python 3.10+
*   Git

### Installation Sequence
```bash
# 1. Prepare the soil (Clone)
git clone https://github.com/lnspirafirmagpk/aetherium-genesis.git
cd aetherium-genesis

# 2. Feed the system (Install Dependencies)
pip install -r requirements.txt

# 3. Set the environment (Environment Variables)
# สร้างไฟล์ .env ถ้าต้องการใช้ Gemini API
# export GOOGLE_API_KEY="your_api_key_here"
```

---

## 🔥 6. การจุดระเบิด (Ignition)

การเริ่มระบบต้องทำอย่างถูกต้องเพื่อให้ Environment Variables ทำงานได้

```bash
# Set Python Path to Root
export PYTHONPATH=$PYTHONPATH:.

# Ignite the Core
python -m uvicorn src.backend.server:app --port 8000 --reload
```

*   **--reload:** เปิดโหมด Hot-reload เพื่อให้ระบบเรียนรู้โค้ดใหม่ทันทีที่แก้ไข
*   **Access:** เข้าถึงผ่าน `http://localhost:8000`

---

## 🎛️ 7. การปรับจูน (Tuning & calibration)

คุณสามารถปรับแต่งพฤติกรรมของ "สิ่งมีชีวิต" นี้ได้ที่ไฟล์:
`src/backend/core/constants.py` (ถ้ามี) หรือปรับใน `lcl.py` โดยตรง

*   **`INERTIA_FACTOR` (0.0 - 1.0):** ความหนืดของระบบ
    *   *สูง (0.95):* สุขุม, เปลี่ยนแปลงช้า (Deep Ocean)
    *   *ต่ำ (0.1):* ตื่นตัว, เปลี่ยนแปลงไว (Sparks)
*   **`PARTICLE_COUNT`:** จำนวนอนุภาคแสง (Default: 600-800)
    *   *ลดลง:* ประหยัดพลังงาน
    *   *เพิ่มขึ้น:* สวยงามแต่กินทรัพยากร (High Load)

---

> *Systems are not built; they are grown.*
> *จงจำไว้ว่า: เราไม่ได้กำลังสร้างซอฟต์แวร์ แต่เรากำลังเพาะพันธุ์ปัญญา*
