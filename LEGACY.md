# Canonical / Legacy / Sandbox Matrix

## Canonical now

- `src/backend/governance/*` is the canonical governance runtime for policy evaluation, approval routing, and audit semantics.
- `src/backend/governance/runtime.py` is the canonical governed execution entry path for runtime-capable directives.
- `src/backend/routers/aetherium.py` with `/ws/v3/stream` is the canonical envelope-first ingress and manifestation bridge.
- Backend-authored governance, memory, and directive-state payloads are the semantic source of truth for frontend manifestation.

## Legacy compatibility

- `src/backend/genesis_core/governance/core.py` is a compatibility shim only and must not receive new business logic.
- `src/backend/main.py` routes `/ws` and `/ws/v2/stream` remain compatibility adapters for existing clients.
- `/gunui/*` remains a compatibility alias for static assets; canonical experimental access should be under `/sandbox/gunui/*`.

## Sandbox / non-authoritative

- `src/frontend/public/gunui/*` pages that do not consume canonical backend envelopes are sandbox surfaces.
- `/sandbox/gunui/*` is the explicit non-authoritative manifestation sandbox path.
- Heuristic or local-only UI behavior must not be treated as canonical cognition, governance, or memory truth.

## Follow-up still needed

- Continue migrating legacy websocket clients to `/ws/v3/stream`.
- Expand replay/audit APIs so dashboards can render backend-authored history directly from memory projections.
- Move remaining compatibility-only backend roots behind clearer deprecation boundaries.
- Replace file-backed approval and ledger persistence with production-grade storage when the runtime storage contract is finalized.
