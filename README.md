# AETHERIUM GENESIS (AG-OS)

Governed AI-OS platform that enforces a canonical control loop:

`Intent -> Reasoning -> Policy Validation -> Execution -> Memory Commit -> Manifestation`

This repository contains a FastAPI backend, governance/runtime services, Akashic memory, and HTML-based operator interfaces.

## Repository structure

```text
.
├── .github/workflows/               # CI, security, CodeQL, issue-triage automations
├── docs/                            # Specs, audits, manuals, architecture references
├── requirements/                    # Runtime/dev/optional dependency sets
├── scripts/                         # Repository validation and benchmarking utilities
├── src/
│   ├── backend/
│   │   ├── main.py                  # FastAPI app entrypoint
│   │   ├── routers/                 # API routers (aetherium/governance/entropy/metrics)
│   │   ├── governance/              # Runtime governance engine
│   │   ├── genesis_core/            # Bus, models, memory, protocol, execution core
│   │   ├── vessels/                 # External system adapters
│   │   └── auth/                    # Auth providers/routes/session manager
│   └── frontend/                    # Homepage/dashboard/public UI surfaces
├── tests/                           # Unit, integration, frontend, and system tests
└── README.md
```

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

## Development workflow

- Validate repository structure and markdown hygiene:

  ```bash
  python scripts/validate_repo_structure.py
  ```

- Run lint + tests locally:

  ```bash
  flake8 src tests scripts
  pytest -q tests --ignore=tests/manual
  ```

## Testing

Run all tests:

```bash
pytest
```

Run a focused subset:

```bash
pytest tests/test_frontend_homepage.py tests/test_integration_ui.py
```

## CI/CD workflows

- `lint_test.yml`: repository validation, flake8 linting, pytest, markdown lint.
- `security.yml`: dependency review, `pip-audit`, `bandit`, TruffleHog scan.
- `codeql.yml`: CodeQL analysis for Actions + Python.
- `summary.yml`: auto-comment triage summary on newly opened issues.

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
