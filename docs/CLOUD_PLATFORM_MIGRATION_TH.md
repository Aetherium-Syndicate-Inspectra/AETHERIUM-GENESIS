# Cloud Platform Migration (Stateless + Multi-tenant)

เอกสารนี้สรุปแนวทางย้าย `AETHERIUM-GENESIS` จากโหมด state-based (ไฟล์ JSON) ไปสู่สถาปัตยกรรม stateless ที่พร้อมรันบน Cloud Run

## 1) ย้าย Akashic จาก JSON → Firestore

อัปเดต `AkashicRecords` ให้เลือก backend ได้ 2 แบบ

- `json` (ค่าเริ่มต้น): ใช้สำหรับ local/dev
- `firestore`: ใช้สำหรับ production ที่ต้องการ persistence ข้าม instance

ตัวอย่างการใช้งาน:

```python
from src.backend.genesis_core.memory.akashic import AkashicRecords

akashic = AkashicRecords(
    backend="firestore",
    firestore_collection="akashic_records",
    default_tenant_id="tenant-acme",
)

akashic.append_record(
    {
        "type": "audit_log",
        "actor": "user-001",
        "action": "PERMISSION_CHECK",
        "result": "ALLOW",
    },
    tenant_id="tenant-acme",
)

history = akashic.get_behavioral_history(
    actor_id="user-001",
    tenant_id="tenant-acme",
)
```

Environment ที่แนะนำ:

- `AKASHIC_BACKEND=firestore`
- `GOOGLE_CLOUD_PROJECT=<project-id>`

## 2) Multi-tenancy

ใน implementation ใหม่ของ `AkashicRecords` มี `tenant_id` ในทุก method สำคัญ:

- `append_record(..., tenant_id=...)`
- `get_behavioral_history(..., tenant_id=...)`
- `get_recent_audits(..., tenant_id=...)`
- `verify_hash_chain(tenant_id=...)`

ผลคือข้อมูลแต่ละ tenant แยก chain กันชัดเจน ลดความเสี่ยงข้อมูลรั่วข้าม account

## 3) Secret Management

- อย่า bake `access_keys.json` ลง image
- ใช้ Secret Manager inject เป็น env var ตอน runtime
- ใช้ ADC/Workload Identity ให้ Firestore client อ่านสิทธิ์จาก service account

## 4) AetherBus บน Cloud

แนะนำ phase ถัดไป:

- ใช้ Redis/Memorystore เป็น distributed bus transport
- แยก message channel ตาม tenant (`tenant_id:event_topic`)
- เพิ่ม retry + dead-letter queue

## 5) Decouple Frontend/Backend

- แยก `src/frontend` ไป hosting แยก (Firebase Hosting/Vercel)
- เรียก backend ผ่าน API เท่านั้น

## 6) awaken.py เป็น Orchestrator

เพิ่ม health supervision loop:

- ตรวจ child services
- restart เฉพาะโมดูลที่ค้าง
- expose health/readiness สำหรับ Cloud Run

## Suggested Roadmap

1. **Phase 1:** JSON → Firestore/Cloud SQL
2. **Phase 2:** Multi-stage Docker build
3. **Phase 3:** GitHub Actions CI/CD ไป Cloud Run
4. **Phase 4:** Tenant Management Dashboard
