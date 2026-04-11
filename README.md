# AETHERIUM GENESIS (AG-OS)

Governed AI-OS platform that enforces a canonical control loop:

`Intent -> Reasoning -> Policy Validation -> Execution -> Memory Commit -> Manifestation`

This repository contains a FastAPI backend, governance/runtime services, Akashic memory, and HTML-based operator interfaces.

## What is in this repo

- **Backend runtime**: `src/backend/main.py` and routers for Aetherium, governance, entropy, and metrics.
- **Governance core**: policy/risk/approval flow in `src/backend/governance/`.
- **Execution + memory**: execution pipeline, vessels, and Akashic continuity in `src/backend/genesis_core/` and `src/backend/memory/`.
- **Frontend surfaces**: homepage + dashboard + sandbox GunUI pages in `src/frontend/`.
- **Regression tests**: end-to-end and unit coverage in `tests/`.

## Quick start

### 1) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Run the platform

```bash
uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3) Open key entrypoints

- Home: `http://localhost:8000/`
- Dashboard: `http://localhost:8000/dashboard`
- OpenAPI docs: `http://localhost:8000/docs`
- Governance approvals API: `http://localhost:8000/governance/approvals`
- Metrics API: `http://localhost:8000/v1/metrics/resonator-reliability`
- Public gateway page: `http://localhost:8000/public`
- Overseer page: `http://localhost:8000/overseer`

## Testing

Run all tests:

```bash
pytest
```

Run a focused subset:

```bash
pytest tests/test_frontend_homepage.py tests/test_integration_ui.py
```

## Architecture map

- **Mind**: Logenesis reasoning and planning.
- **Kernel**: governance policy/risk/approval.
- **Bus**: AetherBus transport and event propagation.
- **Hands**: execution vessels/adapters.
- **Memory**: Akashic ledger and projections.
- **Body**: dashboard + homepage + manifestation surfaces.

## Security

Please see `SECURITY.md` for responsible disclosure and response targets.

## License

This project is licensed under the MIT License. See `LICENSE`.
