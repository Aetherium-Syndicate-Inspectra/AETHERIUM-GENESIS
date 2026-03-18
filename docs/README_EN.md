# AETHERIUM GENESIS (AG-OS)
### Cognitive Infrastructure & Resonance Ecosystem (ASI Readiness)

![Version](https://img.shields.io/badge/version-2.2.0--resonance-blueviolet.svg)
![Status](https://img.shields.io/badge/status-ACTIVE-success.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

> **"This is not just AI, but a state of 'Resonators' (Intelligence Resonance)
working together on a high-speed pathway of thought."**

---

## 📖 Current System Overview

The system has been restructured for maximum agility and speed, with a clear separation of concerns:

*   **src/backend/**: The Core (Mind). Processes logic, ethics, and strategic decision-making.
*   **src/frontend/**: The Body. A PWA interface using a Particle System to manifest "Intent" through light.
*   **docs/**: Knowledge Base. Contains Manifestos, Blueprints, Business Plans, and Conceptual Anchors.
*   **tests/**: Verification Suite. Ensures system integrity and state consistency.

---

## 🧠 Core Concept: From AI Agents to "Resonators"

We have transitioned from traditional Agent systems to a **Resonance Architecture**:
1.  **AetherBus Tachyon**: An intelligence resonance pathway reducing latency to microseconds.
2.  **Primary Resonators**: 12 core resonator positions (Visionary, Technical, Governance, etc.).
3.  **Negative Latency**: Predictive processing (Ghost Workers) that lets the AI think before the human acts.

---

## 🏛️ Deep Architecture

The system coordinates through the **Sopan Protocol**:
`Input (Human Intent) → LogenesisEngine (Formator) → AetherBus (Resonance) → ValidatorAgent (Audit) → AgioSage (Cognitive) → Output (Manifestation)`

### Key Technologies:
- **FastAPI & WebSockets**: Real-time ingress/manifestation surfaces governed by backend directives.
- **AetherBus-Tachyon**: Canonical ZeroMQ + WebSocket bridge for V3 envelope transport.
- **Akashic Records**: Permanent memory via an immutable ledger (`data/akashic_records.json`).
- **PWA (Progressive Web App)**: A manifestation client that renders backend-authored directives only.

---

## Directive-Only Vessel Contract

- Vessels under `src/backend/vessels/` must receive a canonical `AetherEvent` envelope, not loose `action + params` pairs.
- Executable directives must include `payload.action`, `payload.params`, `payload.execution_scope`, `payload.actor`, and traceable envelope metadata.
- Vessel adapters must reject execution unless governance metadata is validated and the decision is explicitly allowed.
- Every execution outcome is written to Akashic memory before the adapter returns to the caller.

## Least-Privilege Rules

- Keep vessel code limited to external-system adapter logic; do not place reasoning, approval, or business policy inside the adapter.
- Declare the minimum required capability in `execution_scope.permissions` and never widen scope inside the vessel.
- Do not hardcode credentials. Use `.env` / secret-manager references such as `${ENV_VAR}`, `env:NAME`, or `secret://path`.
- Preserve `correlation_id`, `trace_id`, actor identity, and source identity end-to-end for replay and auditability.

## 🚀 Running the System

### 1. Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set PYTHONPATH
export PYTHONPATH=$PYTHONPATH:.
```

### 2. System Awakening
Choose your execution mode:

**Developer / Web Mode (Recommended)**
```bash
python awaken.py
```
*Cleans shared memory and starts the backend with auto-reload.*

**Core Mode (Production)**
```bash
python -m uvicorn src.backend.main:app --host 0.0.0.0 --port 8000
```

Access Points:
- **Product UI**: `http://localhost:8000`
- **Developer Dashboard**: `http://localhost:8000/dashboard`
- **API Docs**: `http://localhost:8000/docs`

---

## 🗺️ Essential Documents
*   [**🇬🇧 USAGE_EN.md**](../USAGE_EN.md) - Comprehensive User Guide.
*   [**📐 TECHNICAL_BLUEPRINT_TH.md**](TECHNICAL_BLUEPRINT_TH.md) - Technical architecture details.
*   [**📜 CONSTITUTION.md**](CONSTITUTION.md) - Core system principles.

---

© 2026 Aetherium Syndicate Inspectra (ASI)
*“Where intelligences resonate, harmony emerges.”*
