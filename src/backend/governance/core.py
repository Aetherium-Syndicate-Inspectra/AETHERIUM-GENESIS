import time
import uuid
from dataclasses import asdict, dataclass, field
import logging
from typing import Any, Dict, Optional

from src.backend.genesis_core.protocol.correlation import CorrelationPolicy
from src.backend.genesis_core.protocol.schemas import AetherEvent

from src.backend.governance.approval_router import ApprovalRouter, ApprovalTicket
from src.backend.governance.policy_engine import PolicyEngine, PolicyResult, default_policy_engine
from src.backend.governance.risk_tiering import ActionTier, RiskTiering

logger = logging.getLogger("governance.core")

@dataclass
class ApprovalRequest:
    request_id: str
    tier: ActionTier
    actor: str
    intent_id: str
    action_type: str
    preview_data: Dict[str, Any]
    resource: str = "unknown"
    status: str = "PENDING_APPROVAL"
    created_at: float = field(default_factory=time.time)


@dataclass
class ApprovalDecisionResult:
    status: str
    request_id: str
    decision: str
    detail: str
    ticket: ApprovalTicket | None = None


@dataclass
class GovernanceEnvelopeContext:
    envelope_id: str
    correlation: Dict[str, Any]
    session_id: str | None
    origin: Dict[str, Any]
    target: Dict[str, Any]
    topic: str
    action: str
    resource: str
    payload: Dict[str, Any]
    environment: str
    governance: Dict[str, Any]
    memory: Dict[str, Any]


@dataclass
class GovernanceDecision:
    status: str
    risk_tier: ActionTier
    reason: str
    action: str
    resource: str
    policy_effect: str | None = None
    policy_mode: str = "enforce"
    ticket_id: str | None = None
    recommendation: str | None = None
    ledger_event_type: str | None = None


class GovernanceCore:
    """First-class governance runtime: tiering + policy + approval + containment."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        ledger=None,
        policy_engine: PolicyEngine | None = None,
        approval_router: ApprovalRouter | None = None,
    ):
        self.config = config or {}
        self.ledger = ledger
        self.policy_engine = policy_engine or default_policy_engine()
        self.approval_router = approval_router or ApprovalRouter()

    @property
    def pending_approvals(self) -> Dict[str, ApprovalTicket]:
        return self.approval_router._inbox

    def list_pending_approvals(self) -> list[ApprovalTicket]:
        return self.approval_router.get_inbox()

    def assess_risk(self, action_type: str, payload: Dict[str, Any]) -> ActionTier:
        return RiskTiering.classify(action_type, payload)

    def validate_envelope(self, envelope: AetherEvent) -> AetherEvent:
        validated = AetherEvent.model_validate(envelope.model_dump(mode="json"))
        validated.governance.validated = True
        if not validated.correlation_id:
            raise ValueError("Governance gate requires correlation_id")
        return validated

    def build_context(self, envelope: AetherEvent) -> GovernanceEnvelopeContext:
        envelope = self.validate_envelope(envelope)
        payload = envelope.payload or {}
        action = str(
            payload.get("action")
            or payload.get("intent_type")
            or payload.get("directive_type")
            or envelope.type
        ).lower()
        resource = str(
            payload.get("resource")
            or payload.get("topic")
            or envelope.topic
            or envelope.target.channel
            or envelope.target.service
        )
        return GovernanceEnvelopeContext(
            envelope_id=envelope.envelope_id,
            correlation=CorrelationPolicy.build(
                correlation_id=envelope.correlation_id,
                causation_id=envelope.causation_id,
                trace_id=envelope.trace_id,
                session_id=envelope.session_id,
            ),
            session_id=envelope.session_id,
            origin=envelope.origin.model_dump(mode="json"),
            target=envelope.target.model_dump(mode="json"),
            topic=envelope.topic,
            action=action,
            resource=resource,
            payload=payload,
            environment=str(payload.get("environment") or envelope.extensions.get("environment") or "development"),
            governance=envelope.governance.model_dump(mode="json"),
            memory=envelope.memory.model_dump(mode="json"),
        )

    def evaluate_envelope(self, envelope: AetherEvent, dry_run: bool = False) -> GovernanceDecision:
        context = self.build_context(envelope)
        return self.evaluate_action(
            action=context.action,
            resource=context.resource,
            payload=context.payload,
            dry_run=dry_run,
            correlation_metadata=context.correlation,
            envelope_context=context,
        )

    def evaluate_action(
        self,
        action: str,
        resource: str,
        payload: Dict[str, Any] | None = None,
        dry_run: bool = False,
        correlation_metadata: Dict[str, Any] | None = None,
        envelope_context: GovernanceEnvelopeContext | None = None,
    ) -> GovernanceDecision:
        payload = payload or {}
        correlation = CorrelationPolicy.build(
            correlation_id=(correlation_metadata or {}).get("correlation_id") or payload.get("correlation_id"),
            causation_id=(correlation_metadata or {}).get("causation_id") or payload.get("causation_id"),
            trace_id=(correlation_metadata or {}).get("trace_id") or payload.get("trace_id"),
            fallback=action,
        )
        tier = RiskTiering.classify(action, payload)

        context = {
            "action": action,
            "resource": resource,
            "payload": payload,
            "environment": payload.get("environment", "development"),
            "risk_tier": tier,
            "envelope": asdict(envelope_context) if envelope_context else None,
        }
        policy: PolicyResult = self.policy_engine.evaluate(context, dry_run=dry_run)
        mode_suffix = "_dry_run" if dry_run else ""
        reason = f"[DRY-RUN] {policy.reason}" if dry_run else policy.reason
        mode = "dry_run" if dry_run else policy.mode

        if policy.effect == "DENY":
            decision = GovernanceDecision(
                status="DENIED",
                risk_tier=tier,
                reason=reason,
                action=action,
                resource=resource,
                policy_effect=policy.effect,
                policy_mode=mode,
                recommendation="suspend",
                ledger_event_type=f"governance_denied{mode_suffix}",
            )
            self._record(f"governance_denied{mode_suffix}", decision, policy, correlation, envelope_context)
            logger.info("governance_decision", extra={"status": decision.status, "action": action, "resource": resource, "correlation_id": correlation["correlation_id"]})
            return decision

        if policy.effect == "REQUIRE_APPROVAL":
            if dry_run:
                decision = GovernanceDecision(
                    status="PENDING_APPROVAL",
                    risk_tier=tier,
                    reason=reason,
                    action=action,
                    resource=resource,
                    policy_effect=policy.effect,
                    policy_mode=mode,
                    ticket_id="DRY-RUN",
                    ledger_event_type=f"governance_pending_approval{mode_suffix}",
                )
                self._record(f"governance_pending_approval{mode_suffix}", decision, policy, correlation, envelope_context)
                logger.info("governance_decision", extra={"status": decision.status, "action": action, "resource": resource, "correlation_id": correlation["correlation_id"]})
                return decision

            ticket = ApprovalTicket(
                ticket_id=str(uuid.uuid4()),
                action=action,
                resource=resource,
                risk_tier=tier,
                impact=payload.get("impact", "External side effect may occur"),
                evidence=payload.get("evidence", {}),
                status="PENDING_APPROVAL",
            )
            self.approval_router.enqueue(ticket)
            decision = GovernanceDecision(
                status="PENDING_APPROVAL",
                risk_tier=tier,
                reason=reason,
                action=action,
                resource=resource,
                policy_effect=policy.effect,
                policy_mode=mode,
                ticket_id=ticket.ticket_id,
                ledger_event_type="governance_pending_approval",
            )
            self._record("governance_pending_approval", decision, policy, correlation, envelope_context)
            logger.info("governance_decision", extra={"status": decision.status, "action": action, "resource": resource, "correlation_id": correlation["correlation_id"], "ticket_id": ticket.ticket_id})
            return decision

        decision = GovernanceDecision(
            status="ALLOWED",
            risk_tier=tier,
            reason=reason,
            action=action,
            resource=resource,
            policy_effect=policy.effect,
            policy_mode=mode,
            ledger_event_type=f"governance_allowed{mode_suffix}",
        )
        self._record(f"governance_allowed{mode_suffix}", decision, policy, correlation, envelope_context)
        logger.info("governance_decision", extra={"status": decision.status, "action": action, "resource": resource, "correlation_id": correlation["correlation_id"]})
        return decision

    def request_approval(self, request: ApprovalRequest) -> bool:
        if request.tier <= ActionTier.TIER_0_READ_ONLY:
            request.status = "ALLOWED"
            self._record_approval_result(
                request,
                "ALLOWED",
                "Read-only action allowed without approval",
                event_type="approval_allowed",
            )
            return True

        if request.tier == ActionTier.TIER_1_REVERSIBLE and self.config.get("auto_approve_tier_1", True):
            request.status = "APPROVED"
            self._record_approval_result(request, "APPROVED", "Tier 1 auto-approved", event_type="approval_auto_approved")
            return True

        ticket = ApprovalTicket(
            ticket_id=request.request_id,
            action=request.action_type,
            resource=request.resource,
            risk_tier=request.tier,
            impact=request.preview_data.get("impact", "External side effect may occur") if isinstance(request.preview_data, dict) else "External side effect may occur",
            evidence=request.preview_data if isinstance(request.preview_data, dict) else {"preview": request.preview_data},
            status="PENDING_APPROVAL",
            created_at=request.created_at,
        )
        request.status = "PENDING_APPROVAL"
        self.approval_router.enqueue(ticket)
        self._record_approval_result(request, "PENDING_APPROVAL", "Human approval required", event_type="approval_requested")
        return False

    def handle_approval(self, request_id: str, decision: str) -> ApprovalDecisionResult:
        ticket = self.pending_approvals.get(request_id)
        if ticket is None:
            return ApprovalDecisionResult(
                status="NOT_FOUND",
                request_id=request_id,
                decision=decision.upper(),
                detail="Approval request not found",
            )

        normalized_decision = self.approval_router.decide(request_id, decision)
        result = ApprovalDecisionResult(
            status=normalized_decision,
            request_id=request_id,
            decision=normalized_decision,
            detail="Approval recorded" if normalized_decision == "APPROVED" else "Request rejected by operator",
            ticket=ticket,
        )
        self._record_approval_decision(ticket, result)
        logger.info("approval_decision_recorded", extra={"request_id": request_id, "decision": normalized_decision, "action": ticket.action, "resource": ticket.resource})
        return result

    def _record(self, event_type, decision, policy, correlation, envelope_context=None):
        if not self.ledger:
            return
        payload = {
            "type": event_type,
            "event_type": event_type,
            "decision_status": getattr(decision, "status", None),
            "action": getattr(decision, "action", None),
            "resource": getattr(decision, "resource", None),
            "policy_effect": getattr(decision, "policy_effect", None),
            "policy_mode": getattr(decision, "policy_mode", None),
            "risk_tier": getattr(getattr(decision, "risk_tier", None), "name", None),
            "reason": getattr(decision, "reason", None),
            "recommendation": getattr(decision, "recommendation", None),
            "ticket_id": getattr(decision, "ticket_id", None),
            "correlation_id": correlation.get("correlation_id"),
            "causation_id": correlation.get("causation_id"),
            "trace_id": correlation.get("trace_id"),
            "envelope_context": asdict(envelope_context) if envelope_context else None,
            "policy_snapshot": {
                "effect": getattr(policy, "effect", None),
                "reason": getattr(policy, "reason", None),
                "mode": getattr(policy, "mode", None),
            },
            "replayable": True,
        }
        self.ledger.append_record(
            payload=payload,
            actor="governance",
            intent_id=getattr(decision, "ticket_id", None) or correlation.get("correlation_id"),
            causal_link=correlation.get("causation_id"),
            correlation=correlation,
        )

    def _record_approval_result(self, request: ApprovalRequest, status: str, detail: str, *, event_type: str) -> None:
        if not self.ledger:
            return
        correlation = CorrelationPolicy.build(
            correlation_id=request.intent_id,
            causation_id=request.request_id,
            fallback=request.intent_id or request.request_id,
        )
        self.ledger.append_record(
            payload={
                "type": "approval_state",
                "event_type": event_type,
                "request_id": request.request_id,
                "intent_id": request.intent_id,
                "action": request.action_type,
                "resource": request.resource,
                "risk_tier": request.tier.name,
                "decision_status": status,
                "detail": detail,
                "actor": request.actor,
                "preview_data": request.preview_data,
                "replayable": True,
            },
            actor="governance",
            intent_id=request.intent_id,
            causal_link=request.request_id,
            correlation=correlation,
        )

    def _record_approval_decision(self, ticket: ApprovalTicket, result: ApprovalDecisionResult) -> None:
        if not self.ledger:
            return
        correlation = CorrelationPolicy.build(
            correlation_id=ticket.ticket_id,
            causation_id=ticket.ticket_id,
            fallback=ticket.ticket_id,
        )
        self.ledger.append_record(
            payload={
                "type": "approval_decided",
                "event_type": "approval_decided",
                "request_id": result.request_id,
                "decision_status": result.status,
                "decision": result.decision,
                "detail": result.detail,
                "action": ticket.action,
                "resource": ticket.resource,
                "risk_tier": ticket.risk_tier.name,
                "approval_status": ticket.status,
                "evidence": ticket.evidence,
                "replayable": True,
            },
            actor="governance",
            intent_id=result.request_id,
            causal_link=ticket.ticket_id,
            correlation=correlation,
        )

    def simulate_rule_promotion(self, gem: Dict[str, Any], shadow_mode: bool = True) -> Dict[str, Any]:
        promoted_rule = {
            "rule_id": f"rule-{gem.get('gem_id', 'unknown')}",
            "title": gem.get("title"),
            "principle": gem.get("principle"),
            "source": "gem",
            "status": "SHADOW" if shadow_mode else "ACTIVE",
        }
        result = {
            "mode": "shadow" if shadow_mode else "active",
            "would_block_actions": ["send_email", "delete_all_data"],
            "promoted_rule": promoted_rule,
        }
        if self.ledger:
            self.ledger.append_record(
                payload={"type": "policy_simulation", "result": result, "event_type": "policy_simulation", "timestamp": time.time()},
                actor="governance",
                intent_id=promoted_rule["rule_id"],
                causal_link=gem.get("gem_id"),
            )
        return result

    def recommend_recovery(self, event: Dict[str, Any]) -> Dict[str, str]:
        severity = str(event.get("severity", "low")).lower()
        if severity in {"critical", "high"}:
            recommendation = {"mode": "rollback", "reason": "High severity incident"}
        elif event.get("uncertain_state", False):
            recommendation = {"mode": "quarantine", "reason": "State uncertainty detected"}
        else:
            recommendation = {"mode": "suspend", "reason": "Safety-first manual inspection"}

        if self.ledger:
            self.ledger.append_record(payload={"type": "governance_recovery_recommendation", "event_type": "governance_recovery_recommendation", **recommendation}, actor="governance", correlation=CorrelationPolicy.build(fallback="governance_recovery_recommendation"))
        return recommendation

    def _record_approval_result(self, request: ApprovalRequest, status: str, detail: str, *, event_type: str) -> None:
        if not self.ledger:
            return
        correlation = CorrelationPolicy.build(correlation_id=request.intent_id, causation_id=request.request_id, fallback=request.actor)
        self.ledger.append_record(
            payload={
                "type": event_type,
                "event_type": event_type,
                "timestamp": time.time(),
                "request_id": request.request_id,
                "intent_id": request.intent_id,
                "action": request.action_type,
                "resource": request.resource,
                "decision_status": status,
                "detail": detail,
                "risk_tier": request.tier.name,
                "preview": request.preview_data,
            },
            actor=request.actor,
            intent_id=request.intent_id,
            causal_link=request.request_id,
            correlation=correlation,
        )

    def _record_approval_decision(self, ticket: ApprovalTicket, result: ApprovalDecisionResult) -> None:
        if not self.ledger:
            return
        correlation = CorrelationPolicy.build(correlation_id=result.request_id, causation_id=result.request_id, fallback=ticket.action)
        self.ledger.append_record(
            payload={
                "type": "approval_decided",
                "event_type": "approval_decided",
                "timestamp": time.time(),
                "request_id": result.request_id,
                "action": ticket.action,
                "resource": ticket.resource,
                "decision_status": result.status,
                "decision": result.decision,
                "detail": result.detail,
                "risk_tier": ticket.risk_tier.name,
            },
            actor="governance",
            intent_id=result.request_id,
            causal_link=result.request_id,
            correlation=correlation,
        )

    def _record(
        self,
        event_type: str,
        decision: GovernanceDecision,
        policy: PolicyResult,
        correlation: Dict[str, Any],
        envelope_context: GovernanceEnvelopeContext | None,
    ) -> None:
        if not self.ledger:
            return
        self.ledger.append_record(
            payload={
                "type": event_type,
                "event_type": event_type,
                "timestamp": time.time(),
                "action": decision.action,
                "resource": decision.resource,
                "decision_status": decision.status,
                "decision": asdict(decision),
                "policy": {
                    "effect": policy.effect,
                    "metadata": policy.metadata,
                    "mode": policy.mode,
                },
                "envelope": asdict(envelope_context) if envelope_context else None,
            },
            actor="governance",
            intent_id=decision.ticket_id or decision.action,
            causal_link=decision.ticket_id or decision.action,
            correlation=correlation,
        )
