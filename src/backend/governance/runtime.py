from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional

from src.backend.governance.core import GovernanceCore, GovernanceDecision
from src.backend.genesis_core.protocol.schemas import AetherEvent, AetherEventType

logger = logging.getLogger("DirectiveRuntime")


@dataclass
class RuntimeResult:
    envelope: AetherEvent
    decision: GovernanceDecision
    response: Any = None
    outcome_status: str | None = None
    detail: str | None = None


class DirectiveRuntime:
    """Canonical governed ingress runtime for human intent and executable directives."""

    def __init__(self, governance: GovernanceCore, bus: Any):
        self.governance = governance
        self.bus = bus

    async def handle_envelope(
        self,
        envelope: AetherEvent,
        planner: Optional[Callable[[AetherEvent], Awaitable[Any]]] = None,
        *,
        dry_run: bool = False,
    ) -> RuntimeResult:
        envelope = self.governance.validate_envelope(envelope)
        decision = self.governance.evaluate_envelope(envelope, dry_run=dry_run)
        await self._publish_decision(envelope, decision)

        if decision.status == "PENDING_APPROVAL":
            await self.commit_runtime_outcome(envelope, decision, outcome_status="PENDING_APPROVAL", detail=decision.reason)
            return RuntimeResult(envelope=envelope, decision=decision, outcome_status="PENDING_APPROVAL", detail=decision.reason)

        if decision.status == "DENIED":
            await self.commit_runtime_outcome(envelope, decision, outcome_status="DENIED", detail=decision.reason)
            return RuntimeResult(envelope=envelope, decision=decision, outcome_status="DENIED", detail=decision.reason)

        if planner is None:
            await self.commit_runtime_outcome(envelope, decision, outcome_status="ALLOWED", detail="Execution planner not attached")
            return RuntimeResult(envelope=envelope, decision=decision, outcome_status="ALLOWED", detail="Execution planner not attached")

        await self._publish_execution_readiness(envelope, decision)
        try:
            response = await planner(envelope)
        except Exception as exc:
            detail = str(exc)
            await self.commit_runtime_outcome(envelope, decision, outcome_status="ERROR", detail=detail, error=detail)
            raise

        detail = "Planner completed"
        await self.commit_runtime_outcome(envelope, decision, outcome_status="COMPLETED", detail=detail)
        return RuntimeResult(envelope=envelope, decision=decision, response=response, outcome_status="COMPLETED", detail=detail)

    async def commit_runtime_outcome(
        self,
        envelope: AetherEvent,
        decision: GovernanceDecision,
        *,
        outcome_status: str,
        detail: str,
        error: str | None = None,
        actor: str = "runtime",
    ) -> str | None:
        if not self.governance.ledger:
            return None
        return self.governance.ledger.append_record(
            payload={
                "type": "runtime_outcome",
                "event_type": "runtime_outcome",
                "correlation_id": envelope.correlation_id,
                "causation_id": envelope.envelope_id,
                "trace_id": envelope.trace_id,
                "action": decision.action,
                "resource": decision.resource,
                "decision_status": decision.status,
                "outcome_status": outcome_status,
                "detail": detail,
                "error": error,
                "actor": actor,
                "origin": envelope.origin.model_dump(mode="json"),
                "replayable": True,
            },
            actor=actor,
            intent_id=decision.ticket_id or envelope.correlation_id,
            causal_link=envelope.envelope_id,
            correlation={
                "correlation_id": envelope.correlation_id,
                "causation_id": envelope.envelope_id,
                "trace_id": envelope.trace_id,
            },
        )

    async def _publish_decision(self, envelope: AetherEvent, decision: GovernanceDecision) -> None:
        policy_effect = decision.policy_effect or (
            "DENY" if decision.status == "DENIED" else "REQUIRE_APPROVAL" if decision.status == "PENDING_APPROVAL" else "ALLOW"
        )
        event = AetherEvent(
            type=AetherEventType.STATE_UPDATE,
            session_id=envelope.session_id,
            topic="governance.decision",
            correlation_id=envelope.correlation_id,
            causation_id=envelope.envelope_id,
            trace_id=envelope.trace_id,
            origin={"service": "governance", "subsystem": "kernel", "channel": envelope.session_id or "runtime"},
            target={"service": "genesis_core", "subsystem": "bus", "channel": envelope.session_id or "runtime"},
            payload={
                "envelope_id": envelope.envelope_id,
                "topic": envelope.topic,
                "governed_action": decision.action,
                "governed_resource": decision.resource,
                "status": {"phase": "governance", "label": decision.status},
                "reason": decision.reason,
                "directive_state": {
                    "correlation_id": envelope.correlation_id,
                    "causation_id": envelope.envelope_id,
                    "trace_id": envelope.trace_id,
                    "manifest_version": "2026.03-manifestation-v1",
                    "semantic_source": "backend",
                },
                "status_block": {"phase": "governance", "label": decision.status},
                "diagnostics": {"governed_action": decision.action, "governed_resource": decision.resource},
                "governance": {
                    "decision": decision.status,
                    "risk_tier": decision.risk_tier.name,
                    "policy_effect": policy_effect,
                    "approval_ticket_id": decision.ticket_id,
                },
                "memory": {"ledger_event_type": decision.ledger_event_type or "governance_decision", "replayable": True},
            },
            governance={
                "decision": decision.status,
                "risk_tier": decision.risk_tier.name,
                "policy_effect": policy_effect,
                "approval_ticket_id": decision.ticket_id,
                "policy_mode": decision.policy_mode,
                "validated": True,
            },
            memory={
                "ledger_event_type": decision.ledger_event_type or "governance_decision",
                "causal_chain": [envelope.correlation_id],
                "replayable": True,
            },
        )
        await self.bus.publish(event)

    async def _publish_execution_readiness(self, envelope: AetherEvent, decision: GovernanceDecision) -> None:
        event = AetherEvent(
            type=AetherEventType.STATE_UPDATE,
            session_id=envelope.session_id,
            topic="execution.readiness",
            correlation_id=envelope.correlation_id,
            causation_id=envelope.envelope_id,
            trace_id=envelope.trace_id,
            origin={"service": "governance", "subsystem": "kernel", "channel": envelope.session_id or "runtime"},
            target={"service": "genesis_core", "subsystem": "mind", "channel": "planner"},
            payload={
                "authorization": "granted",
                "envelope_id": envelope.envelope_id,
                "governed_action": decision.action,
                "governed_resource": decision.resource,
                "status": {"phase": "execution_readiness", "label": "ALLOWED"},
                "directive_state": {
                    "correlation_id": envelope.correlation_id,
                    "causation_id": envelope.envelope_id,
                    "trace_id": envelope.trace_id,
                    "manifest_version": "2026.03-manifestation-v1",
                    "semantic_source": "backend",
                },
                "status_block": {"phase": "execution_readiness", "label": "ALLOWED"},
                "diagnostics": {"governed_action": decision.action, "governed_resource": decision.resource},
                "governance": {
                    "decision": "ALLOWED",
                    "risk_tier": decision.risk_tier.name,
                    "policy_effect": decision.policy_effect or "ALLOW",
                },
                "memory": {"ledger_event_type": "approved_execution_readiness", "replayable": True},
            },
            governance={
                "decision": "ALLOWED",
                "risk_tier": decision.risk_tier.name,
                "policy_effect": decision.policy_effect or "ALLOW",
                "policy_mode": decision.policy_mode,
                "validated": True,
            },
            memory={
                "ledger_event_type": "approved_execution_readiness",
                "causal_chain": [envelope.correlation_id],
                "replayable": True,
            },
        )
        await self.bus.publish(event)
        logger.info(
            "Execution authorized for correlation_id=%s action=%s resource=%s",
            envelope.correlation_id,
            decision.action,
            decision.resource,
        )
