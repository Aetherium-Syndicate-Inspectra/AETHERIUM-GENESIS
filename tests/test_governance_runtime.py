import json

from src.backend.governance.core import ApprovalRequest, GovernanceCore
from src.backend.genesis_core.memory.akashic import AkashicRecords
from src.backend.governance.risk_tiering import ActionTier, RiskTiering
from src.backend.memory.fabric import MemoryFabric


def test_risk_tiering_and_approval_gate():
    governance = GovernanceCore()
    decision = governance.evaluate_action("send_email", "customer.outbound", {"real_world": True})
    assert decision.status == "PENDING_APPROVAL"
    assert decision.risk_tier == ActionTier.TIER_2_EXTERNAL_IMPACT
    assert decision.ticket_id is not None


def test_policy_denies_secret_mutation_in_production():
    governance = GovernanceCore()
    decision = governance.evaluate_action("update_secret", "prod/secret/payment", {"environment": "production"})
    assert decision.status == "DENIED"
    assert decision.recommendation == "suspend"


def test_dry_run_does_not_enqueue_approval_ticket():
    governance = GovernanceCore()
    decision = governance.evaluate_action("send_email", "customer.outbound", {"real_world": True}, dry_run=True)

    assert decision.status == "PENDING_APPROVAL"
    assert decision.ticket_id == "DRY-RUN"
    assert decision.reason.startswith("[DRY-RUN]")
    assert governance.approval_router.get_inbox() == []


def test_dry_run_policy_deny_uses_dry_run_reasoning():
    governance = GovernanceCore()
    decision = governance.evaluate_action(
        "update_secret",
        "prod/secret/payment",
        {"environment": "production"},
        dry_run=True,
    )

    assert decision.status == "DENIED"
    assert decision.reason.startswith("[DRY-RUN]")


def test_memory_fabric_projection(tmp_path):
    ledger = tmp_path / "akashic.json"
    ledger.write_text('{"chain": [{"hash": "abc", "timestamp": 1, "payload": {"type": "intent_created"}, "provenance": {"actor": "system"}}]}')
    fabric = MemoryFabric(ledger_path=str(ledger), memory_root=str(tmp_path / "memory"))
    counts = fabric.project()
    assert counts["episodic"] == 1
    assert (tmp_path / "memory" / "episodes" / "abc.json").exists()


def test_classifier_defaults_read_only():
    assert RiskTiering.classify("inspect_status") == ActionTier.TIER_0_READ_ONLY


def test_governance_persists_correlation_metadata(tmp_path):
    ledger = AkashicRecords(db_path=str(tmp_path / "akashic.json"))
    governance = GovernanceCore(ledger=ledger)

    governance.evaluate_action(
        "send_email",
        "customer.outbound",
        {"real_world": True},
        correlation_metadata={"correlation_id": "corr-governance", "trace_id": "trace-governance"},
    )

    chain = json.loads((tmp_path / "akashic.json").read_text())["chain"]
    record = chain[-1]
    assert record["correlation"]["correlation_id"] == "corr-governance"
    assert record["correlation"]["trace_id"] == "trace-governance"


def test_governance_records_explicit_approval_decision_status(tmp_path):
    ledger = AkashicRecords(db_path=str(tmp_path / "akashic.json"))
    governance = GovernanceCore(ledger=ledger, config={"auto_approve_tier_1": False})
    governance.request_approval(
        ApprovalRequest(
            request_id="approval-1",
            tier=ActionTier.TIER_2_EXTERNAL_IMPACT,
            actor="tester",
            intent_id="intent-approval-1",
            action_type="send_email",
            resource="customer.outbound",
            preview_data={"real_world": True},
        )
    )

    result = governance.handle_approval("approval-1", "REJECTED")

    chain = json.loads((tmp_path / "akashic.json").read_text())["chain"]
    assert result.status == "REJECTED"
    assert result.status != "NOT_FOUND"
    assert chain[-1]["payload"]["type"] == "approval_decided"
    assert chain[-1]["payload"]["decision_status"] == "REJECTED"
    assert chain[-1]["payload"]["request_id"] == "approval-1"


def test_memory_fabric_projection_preserves_correlation_metadata(tmp_path):
    ledger = tmp_path / "akashic.json"
    ledger.write_text(json.dumps({
        "chain": [{
            "hash": "abc",
            "timestamp": 1,
            "payload": {"type": "intent_created"},
            "provenance": {"actor": "system", "correlation": {"correlation_id": "corr-1", "trace_id": "trace-1"}},
            "correlation": {"correlation_id": "corr-1", "trace_id": "trace-1"}
        }]
    }))
    fabric = MemoryFabric(ledger_path=str(ledger), memory_root=str(tmp_path / "memory"))
    fabric.project()
    projected = json.loads((tmp_path / "memory" / "episodes" / "abc.json").read_text())
    assert projected["correlation"]["correlation_id"] == "corr-1"
    assert projected["correlation"]["trace_id"] == "trace-1"


from src.backend.genesis_core.protocol.schemas import AetherEvent, AetherEventType
from src.backend.governance.runtime import DirectiveRuntime


class _RecordingBus:
    def __init__(self):
        self.events = []

    async def publish(self, event):
        self.events.append(event)
        return None


def _make_envelope(**payload_overrides):
    payload = {"action": "read_file", "resource": "memory.audit", **payload_overrides}
    return AetherEvent(
        type=AetherEventType.INTENT_DETECTED,
        session_id="session-1",
        topic="intent.ingress",
        correlation_id="corr-runtime-1",
        trace_id="trace-runtime-1",
        origin={"service": "api", "subsystem": "body", "channel": "session-1"},
        target={"service": "genesis_core", "subsystem": "mind", "channel": "lifecycle"},
        payload=payload,
        governance={"policy_mode": "enforce", "validated": True},
        memory={"ledger_event_type": "intent_ingress", "causal_chain": ["corr-runtime-1"]},
    )


async def _allowed_planner(envelope):
    return {"handled": envelope.correlation_id}


async def _failing_planner(envelope):
    raise RuntimeError(f"planner failed for {envelope.correlation_id}")


def test_governance_builds_full_envelope_context():
    governance = GovernanceCore()
    envelope = _make_envelope(environment="production")

    context = governance.build_context(envelope)

    assert context.envelope_id == envelope.envelope_id
    assert context.correlation["correlation_id"] == "corr-runtime-1"
    assert context.origin["service"] == "api"
    assert context.target["subsystem"] == "mind"
    assert context.action == "read_file"
    assert context.resource == "memory.audit"
    assert context.environment == "production"


import pytest


@pytest.mark.asyncio
async def test_directive_runtime_emits_decision_and_execution_readiness():
    bus = _RecordingBus()
    runtime = DirectiveRuntime(governance=GovernanceCore(), bus=bus)

    result = await runtime.handle_envelope(_make_envelope(), planner=_allowed_planner)

    assert result.decision.status == "ALLOWED"
    assert result.response == {"handled": "corr-runtime-1"}
    assert [event.topic for event in bus.events] == ["governance.decision", "execution.readiness"]
    assert result.outcome_status == "COMPLETED"
    assert all(event.correlation_id == "corr-runtime-1" for event in bus.events)


def test_directive_runtime_stops_at_pending_approval(tmp_path):
    import asyncio

    ledger = AkashicRecords(db_path=str(tmp_path / "akashic.json"))
    bus = _RecordingBus()
    runtime = DirectiveRuntime(governance=GovernanceCore(ledger=ledger), bus=bus)

    result = asyncio.run(
        runtime.handle_envelope(
            _make_envelope(action="send_email", resource="customer.outbound", real_world=True),
            planner=_allowed_planner,
        )
    )

    assert result.decision.status == "PENDING_APPROVAL"
    assert result.response is None
    assert result.outcome_status == "PENDING_APPROVAL"
    assert [event.topic for event in bus.events] == ["governance.decision"]
    chain = json.loads((tmp_path / "akashic.json").read_text())["chain"]
    assert chain[-1]["payload"]["type"] == "runtime_outcome"
    assert chain[-1]["payload"]["decision_status"] == "PENDING_APPROVAL"
    assert chain[-1]["payload"]["outcome_status"] == "PENDING_APPROVAL"
    assert chain[-1]["correlation"]["correlation_id"] == "corr-runtime-1"


def test_directive_runtime_records_allowed_outcome(tmp_path):
    import asyncio

    ledger = AkashicRecords(db_path=str(tmp_path / "akashic.json"))
    bus = _RecordingBus()
    runtime = DirectiveRuntime(governance=GovernanceCore(ledger=ledger), bus=bus)

    result = asyncio.run(runtime.handle_envelope(_make_envelope(), planner=_allowed_planner))

    chain = json.loads((tmp_path / "akashic.json").read_text())["chain"]
    assert result.outcome_status == "COMPLETED"
    assert chain[-1]["payload"]["type"] == "runtime_outcome"
    assert chain[-1]["payload"]["decision_status"] == "ALLOWED"
    assert chain[-1]["payload"]["outcome_status"] == "COMPLETED"


def test_directive_runtime_records_denied_outcome(tmp_path):
    import asyncio

    ledger = AkashicRecords(db_path=str(tmp_path / "akashic.json"))
    bus = _RecordingBus()
    runtime = DirectiveRuntime(governance=GovernanceCore(ledger=ledger), bus=bus)

    result = asyncio.run(
        runtime.handle_envelope(
            _make_envelope(action="update_secret", resource="prod/secret/payment", environment="production"),
            planner=_allowed_planner,
        )
    )

    chain = json.loads((tmp_path / "akashic.json").read_text())["chain"]
    assert result.decision.status == "DENIED"
    assert result.outcome_status == "DENIED"
    assert chain[-1]["payload"]["type"] == "runtime_outcome"
    assert chain[-1]["payload"]["decision_status"] == "DENIED"
    assert chain[-1]["payload"]["outcome_status"] == "DENIED"


def test_directive_runtime_records_error_outcome_without_raising(tmp_path):
    import asyncio

    ledger = AkashicRecords(db_path=str(tmp_path / "akashic.json"))
    bus = _RecordingBus()
    runtime = DirectiveRuntime(governance=GovernanceCore(ledger=ledger), bus=bus)

    result = asyncio.run(runtime.handle_envelope(_make_envelope(), planner=_failing_planner))

    chain = json.loads((tmp_path / "akashic.json").read_text())["chain"]
    assert result.outcome_status == "ERROR"
    assert "planner failed" in (result.detail or "")
    assert chain[-1]["payload"]["type"] == "runtime_outcome"
    assert chain[-1]["payload"]["decision_status"] == "ALLOWED"
    assert chain[-1]["payload"]["outcome_status"] == "ERROR"
    assert chain[-1]["payload"]["correlation"]["correlation_id"] == "corr-runtime-1"
