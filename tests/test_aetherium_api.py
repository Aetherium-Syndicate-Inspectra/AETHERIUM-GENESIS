import asyncio
from fastapi.testclient import TestClient
from src.backend.main import app
from src.backend.security.key_manager import KeyTier
from src.backend.routers.aetherium import _manifestation_bridge_payload, _publish_runtime_state
from src.backend.genesis_core.protocol.schemas import AetherEvent, AetherEventType
import json
import time

def test_aetherium_flow():
    # Trigger Startup Events
    with TestClient(app) as client:
        # Inject an internal key for testing
        km = app.state.key_manager
        abe_id = "test-abe-id"
        test_key = km.create_key(abe_id=abe_id, tier=KeyTier.INTERNAL, label="Test Key")

        contract_data = {
            "identity": {
                "abe_id": abe_id,
                "entity_name": "Test Client"
            },
            "intent": {
                "primary_intent": "OBSERVER"
            }
        }

        # 1. Control Plane
        response = client.post("/v1/session", json={
            "client": "test_script",
            "access_key": test_key,
            "abe_contract": contract_data
        })
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        session_id = data["session_id"]

        print(f"Session: {session_id}")

        # 2. Data Plane
        with client.websocket_connect(f"/ws/v3/stream?session_id={session_id}") as websocket:
            # Expect Handshake
            msg = websocket.receive_json()
            assert msg["type"] == "handshake"
            assert msg["directive_state"]["correlation_id"] == session_id
            assert msg["directive_state"]["trace_id"] == session_id
            assert msg["directive_state"]["manifest_version"] == "2026.03-manifestation-v1"
            assert msg["frontend_contract"] == "render-only"
            print("Handshake received")

            # Send Intent
            websocket.send_json({"text": "Hello Aether", "correlation_id": "corr-client-1", "trace_id": "trace-client-1"})

            # Expect Stream
            received_types = []

            for _ in range(10): # Increased safety limit
                try:
                    msg = websocket.receive_json()
                    received_types.append(msg["type"])
                    print(f"Received: {msg['type']}")

                    if msg["type"] == "intent_detected" and msg["topic"] == "intent.ingress":
                        assert msg["directive_state"]["correlation_id"] == "corr-client-1"
                        assert msg["directive_state"]["trace_id"] == "trace-client-1"
                        assert msg["frontend_contract"] == "render-only"
                        assert msg["directive_state"]["manifest_version"] == "2026.03-manifestation-v1"
                        assert msg["status"] == {"phase": "intent_ingress", "label": "RECEIVED"}
                    if msg["topic"] == "governance.decision":
                        assert msg["directive_state"]["correlation_id"] == "corr-client-1"
                        assert msg["status"]["label"] in {"ALLOWED", "PENDING_APPROVAL", "DENIED"}
                        assert msg["payload"]["memory"]["ledger_event_type"].startswith("governance_")
                    if msg["type"] == "manifestation":
                        assert msg["directive_state"]["correlation_id"] == "corr-client-1"
                        assert msg["directive_state"]["trace_id"] == "trace-client-1"
                        assert msg["directive_state"]["manifest_version"] == "2026.03-manifestation-v1"
                        assert msg["payload"]["memory"]["ledger_event_type"] == "runtime_outcome"
                        break
                    if msg["type"] == "degradation":
                        break
                except Exception as e:
                    print(f"Receive Error: {e}")
                    break

            assert "intent_detected" in received_types
            assert any(event_type in received_types for event_type in ("manifestation", "degradation"))


def test_manifestation_bridge_payload_exposes_render_only_contract():
    event = AetherEvent(
        type=AetherEventType.STATE_UPDATE,
        topic="governance.decision",
        session_id="ae-test",
        correlation_id="corr-1",
        trace_id="trace-1",
        origin={"service": "governance", "subsystem": "kernel", "channel": "ae-test"},
        target={"service": "client", "subsystem": "manifestation", "channel": "ae-test"},
        payload={
            "status": "ALLOWED",
            "status_block": {"phase": "governance", "label": "ALLOWED"},
            "diagnostics": {"bridge": "ws_v3"},
        },
    )

    payload = _manifestation_bridge_payload(event, lifecycle_stage="governance_emit")

    assert payload["frontend_contract"] == "render-only"
    assert payload["semantic_source"] == "backend"
    assert payload["directive_state"]["manifest_version"] == "2026.03-manifestation-v1"
    assert payload["status"] == {"phase": "governance", "label": "ALLOWED"}


class _RecordingBus:
    def __init__(self):
        self.events = []

    async def publish(self, event):
        self.events.append(event)


def _make_runtime_result(status: str, outcome_status: str, *, ticket_id: str | None = None, detail: str = "detail"):
    from src.backend.governance.core import GovernanceDecision
    from src.backend.governance.risk_tiering import ActionTier
    from src.backend.governance.runtime import RuntimeResult

    decision = GovernanceDecision(
        status=status,
        risk_tier=ActionTier.TIER_2_EXTERNAL_IMPACT if status != "ALLOWED" else ActionTier.TIER_0_READ_ONLY,
        reason=detail,
        action="send_email",
        resource="customer.outbound",
        policy_effect="REQUIRE_APPROVAL" if status == "PENDING_APPROVAL" else "DENY" if status == "DENIED" else "ALLOW",
        policy_mode="enforce",
        ticket_id=ticket_id,
    )
    return RuntimeResult(
        envelope=AetherEvent(
            type=AetherEventType.INTENT_DETECTED,
            topic="intent.ingress",
            session_id="ae-test",
            correlation_id="corr-state-1",
            causation_id="cause-state-1",
            trace_id="trace-state-1",
            origin={"service": "api", "subsystem": "body", "channel": "ae-test"},
            target={"service": "genesis_core", "subsystem": "mind", "channel": "lifecycle"},
            payload={"action": "send_email", "resource": "customer.outbound"},
            governance={"validated": True, "policy_mode": "enforce"},
            memory={"ledger_event_type": "intent_ingress", "causal_chain": ["corr-state-1"]},
        ),
        decision=decision,
        outcome_status=outcome_status,
        detail=detail,
        record_id="record-1",
        outcome_metadata={
            "type": "runtime_outcome",
            "decision_status": status,
            "outcome_status": outcome_status,
            "correlation_id": "corr-state-1",
        },
        error={"type": "RuntimeError", "message": detail, "governed": True} if outcome_status == "ERROR" else None,
    )


def test_publish_runtime_state_emits_consistent_context_blocks():
    ingress_envelope = AetherEvent(
        type=AetherEventType.INTENT_DETECTED,
        topic="intent.ingress",
        session_id="ae-test",
        correlation_id="corr-state-1",
        causation_id="cause-state-1",
        trace_id="trace-state-1",
        origin={"service": "api", "subsystem": "body", "channel": "ae-test"},
        target={"service": "genesis_core", "subsystem": "mind", "channel": "lifecycle"},
        payload={"action": "send_email", "resource": "customer.outbound"},
        governance={"validated": True, "policy_mode": "enforce"},
        memory={"ledger_event_type": "intent_ingress", "causal_chain": ["corr-state-1"]},
    )
    cases = [
        ("PENDING_APPROVAL", "PENDING_APPROVAL", "governance.approval.pending", "governance", AetherEventType.STATE_UPDATE),
        ("DENIED", "DENIED", "governance.denied", "governance", AetherEventType.DEGRADATION),
        ("ALLOWED", "ERROR", "runtime.error", "runtime", AetherEventType.DEGRADATION),
        ("ALLOWED", "COMPLETED", "runtime.completed", "manifestation", AetherEventType.STATE_UPDATE),
    ]

    for decision_status, outcome_status, topic, phase, event_type in cases:
        bus = _RecordingBus()
        result = _make_runtime_result(decision_status, outcome_status, ticket_id="ticket-1", detail=f"{topic} detail")
        asyncio.run(_publish_runtime_state(
            bus=bus,
            session_id="ae-test",
            ingress_envelope=ingress_envelope,
            runtime_result=result,
            topic=topic,
            event_type=event_type,
            phase=phase,
            label=outcome_status,
            ledger_event_type="runtime_outcome",
            origin={"service": "governance", "subsystem": "kernel", "channel": "ae-test"},
            error=result.detail if outcome_status in {"ERROR", "DENIED"} else None,
            extra_payload={"detail": result.detail},
        ))

        assert len(bus.events) == 1
        event = bus.events[0]
        assert event.topic == topic
        assert event.payload["directive_state"]["correlation_id"] == "corr-state-1"
        assert event.payload["governance"]["decision"] == decision_status
        assert event.payload["memory"]["ledger_event_type"] == "runtime_outcome"
        assert event.payload["runtime_outcome"]["outcome_status"] == outcome_status
        assert event.governance.policy_mode == "enforce"
        assert event.memory.ledger_record_id == "record-1"
