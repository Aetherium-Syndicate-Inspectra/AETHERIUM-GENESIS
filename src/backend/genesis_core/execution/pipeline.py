from __future__ import annotations

import logging
from typing import Any, Dict

from src.backend.genesis_core.memory.akashic import AkashicRecords
from src.backend.genesis_core.protocol.schemas import AetherEvent


logger = logging.getLogger("governed.execution")


class GovernedExecutionPipeline:
    """Shared helper for governed execution and memory commits."""

    def __init__(self, *, ledger: AkashicRecords | None = None, actor_label: str = "execution") -> None:
        self.ledger = ledger
        self.actor_label = actor_label

    def require_execution_metadata(self, envelope: AetherEvent, payload: Dict[str, Any]) -> None:
        governance = envelope.governance
        execution_scope = payload.get("execution_scope") or {}
        actor = payload.get("actor") or {}

        if not envelope.correlation_id or not envelope.trace_id:
            raise ValueError("Execution requires correlation_id and trace_id")
        if not envelope.origin or not envelope.origin.service:
            raise ValueError("Execution requires origin.service metadata")
        if not actor.get("id") or not actor.get("type"):
            raise ValueError("Execution requires actor.id and actor.type metadata")
        if not governance.validated:
            raise PermissionError("Execution requires validated governance metadata")
        if governance.decision not in {"ALLOWED", "ALLOW"}:
            raise PermissionError("Execution requires an allowed governance decision")
        if not governance.policy_effect:
            raise PermissionError("Execution requires explicit governance policy_effect metadata")
        if not execution_scope.get("system"):
            raise ValueError("Execution requires execution_scope.system")
        if not execution_scope.get("permissions"):
            raise ValueError("Execution requires execution_scope.permissions")

    def record_outcome(
        self,
        *,
        envelope: AetherEvent,
        payload: Dict[str, Any],
        result: Dict[str, Any],
        vessel_name: str,
    ) -> Dict[str, Any]:
        response = dict(result)
        response.setdefault("memory", {})
        response["memory"]["correlation_id"] = envelope.correlation_id

        if not self.ledger:
            return response

        ledger_hash = self.ledger.append_record(
            payload={
                "type": "execution_outcome",
                "event_type": "execution_outcome",
                "vessel": vessel_name,
                "action": payload.get("action"),
                "result": result,
                "correlation_id": envelope.correlation_id,
                "causation_id": envelope.envelope_id,
                "trace_id": envelope.trace_id,
                "execution_scope": payload.get("execution_scope"),
                "governance": envelope.governance.model_dump(mode="json"),
                "actor": payload.get("actor"),
                "source": envelope.origin.model_dump(mode="json"),
                "status": result.get("status", "ok"),
                "replayable": True,
            },
            actor=f"{self.actor_label}:{vessel_name}",
            intent_id=envelope.envelope_id,
            causal_link=envelope.causation_id or envelope.envelope_id,
            correlation={
                "correlation_id": envelope.correlation_id,
                "causation_id": envelope.envelope_id,
                "trace_id": envelope.trace_id,
            },
        )
        logger.info(
            "execution_outcome_recorded",
            extra={
                "vessel": vessel_name,
                "action": payload.get("action"),
                "correlation_id": envelope.correlation_id,
                "ledger_record_id": ledger_hash,
            },
        )
        response["memory"]["ledger_record_id"] = ledger_hash
        return response
