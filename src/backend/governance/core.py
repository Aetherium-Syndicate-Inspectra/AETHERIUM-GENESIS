import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Dict

from src.backend.governance.approval_router import ApprovalRouter, ApprovalTicket
from src.backend.governance.policy_engine import PolicyEngine, PolicyResult, default_policy_engine
from src.backend.governance.risk_tiering import ActionTier, RiskTiering


@dataclass
class GovernanceDecision:
    status: str
    risk_tier: ActionTier
    reason: str
    ticket_id: str | None = None
    recommendation: str | None = None


class GovernanceCore:
    """First-class governance runtime: tiering + policy + approval + containment."""

    def __init__(self, ledger=None, policy_engine: PolicyEngine | None = None, approval_router: ApprovalRouter | None = None):
        self.ledger = ledger
        self.policy_engine = policy_engine or default_policy_engine()
        self.approval_router = approval_router or ApprovalRouter()

    def evaluate_action(self, action: str, resource: str, payload: Dict[str, Any] | None = None) -> GovernanceDecision:
        payload = payload or {}
        tier = RiskTiering.classify(action, payload)

        context = {
            "action": action,
            "resource": resource,
            "payload": payload,
            "environment": payload.get("environment", "development"),
            "risk_tier": tier,
        }
        policy: PolicyResult = self.policy_engine.evaluate(context)

        if policy.effect == "DENY":
            decision = GovernanceDecision(status="DENIED", risk_tier=tier, reason=policy.reason, recommendation="suspend")
            self._record("governance_denied", action, resource, decision)
            return decision

        if policy.effect == "REQUIRE_APPROVAL":
            ticket = ApprovalTicket(
                ticket_id=str(uuid.uuid4()),
                action=action,
                resource=resource,
                risk_tier=tier,
                impact=payload.get("impact", "External side effect may occur"),
                evidence=payload.get("evidence", {}),
            )
            self.approval_router.enqueue(ticket)
            decision = GovernanceDecision(
                status="PENDING_APPROVAL",
                risk_tier=tier,
                reason=policy.reason,
                ticket_id=ticket.ticket_id,
            )
            self._record("governance_pending_approval", action, resource, decision)
            return decision

        decision = GovernanceDecision(status="ALLOWED", risk_tier=tier, reason=policy.reason)
        self._record("governance_allowed", action, resource, decision)
        return decision

    def recommend_recovery(self, event: Dict[str, Any]) -> Dict[str, str]:
        severity = str(event.get("severity", "low")).lower()
        if severity in {"critical", "high"}:
            recommendation = {"mode": "rollback", "reason": "High severity incident"}
        elif event.get("uncertain_state", False):
            recommendation = {"mode": "quarantine", "reason": "State uncertainty detected"}
        else:
            recommendation = {"mode": "suspend", "reason": "Safety-first manual inspection"}

        if self.ledger:
            self.ledger.append_record(payload={"type": "governance_recovery_recommendation", **recommendation}, actor="governance")
        return recommendation

    def _record(self, event_type: str, action: str, resource: str, decision: GovernanceDecision) -> None:
        if not self.ledger:
            return
        self.ledger.append_record(
            payload={
                "type": event_type,
                "action": action,
                "resource": resource,
                "decision": asdict(decision),
                "timestamp": time.time(),
            },
            actor="governance",
            intent_id=decision.ticket_id,
        )
