# Directive Envelope Standard (v1)

This document defines the canonical directive envelope used to connect Intent, Reasoning, Governance, Execution, Memory commit, and Manifestation.

## Objectives

- Provide one stable packet shape for cross-subsystem traceability.
- Preserve replayability in Akashic Memory.
- Preserve governance-first execution gates with explicit risk and approval metadata.

## Canonical schema

```json
{
  "envelope_version": "1.0.0",
  "protocol_version": "2026.03",
  "envelope_id": "uuid",
  "trace_id": "otel-trace-id",
  "intent": {
    "intent_id": "string",
    "origin": "agent|user|system",
    "input": {},
    "timestamp": 0
  },
  "reasoning": {
    "planner": "string",
    "summary": "string",
    "artifacts": [],
    "timestamp": 0
  },
  "governance": {
    "decision": "ALLOWED|DENIED|PENDING_APPROVAL",
    "risk_tier": "TIER_0..TIER_3",
    "policy_effect": "ALLOW|DENY|REQUIRE_APPROVAL",
    "policy_mode": "enforce|dry_run",
    "approval_ticket_id": "string|null",
    "timestamp": 0
  },
  "execution": {
    "vessels": [],
    "status": "pending|committed|aborted",
    "side_effects": [],
    "timestamp": 0
  },
  "memory_commit": {
    "ledger_hash": "string",
    "hash_prev": "string",
    "timestamp": 0
  },
  "manifestation": {
    "surface": "gunui|api|dashboard",
    "state": {},
    "timestamp": 0
  }
}
```

## Compatibility rules

1. New fields must be additive and optional within a minor version.
2. Removing or renaming fields requires a major version bump.
3. Producers and consumers must validate `envelope_version` and `protocol_version` before processing.
4. Governance metadata (`risk_tier`, `policy_effect`, `policy_mode`) is mandatory for any executable directive.

## Runtime requirements

- All execution-capable flows must log envelope-correlated governance events.
- Dry-run decisions must be tagged with `policy_mode=dry_run` and must not produce irreversible side effects.
- Envelope IDs and trace IDs must be persisted into Akashic records for replay and audit exports.
