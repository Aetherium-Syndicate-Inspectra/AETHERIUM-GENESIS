from fastapi import APIRouter, WebSocket, Request, WebSocketDisconnect, HTTPException
from typing import Dict, Any
import uuid
import json
import logging
import asyncio

from src.backend.genesis_core.protocol.correlation import CorrelationPolicy
from src.backend.genesis_core.protocol.schemas import (
    AetherEvent,
    AetherEventType,
    ManifestationDirectivePayload,
    ManifestationDirectiveState,
    StateData,
)
from src.backend.genesis_core.models.intent import SystemIntent, IntentPayload, IntentContext
from src.backend.governance.runtime import DirectiveRuntime
from src.backend.genesis_core.protocol.abe_contract import ABEContract
from src.backend.security.key_manager import KeyManager

logger = logging.getLogger("AetheriumAPI")


MANIFEST_VERSION = "2026.03-manifestation-v1"


def _status_block(label: str, phase: str) -> dict[str, Any]:
    return {"phase": phase, "label": label}


def _context_block(event: AetherEvent, *, directive_state: dict[str, Any], governance: dict[str, Any] | None = None, ledger_event_type: str | None = None) -> dict[str, Any]:
    return {
        "directive_state": directive_state,
        "governance": governance or {},
        "memory": {
            "ledger_event_type": ledger_event_type,
            "correlation_id": event.correlation_id,
            "causation_id": event.causation_id or event.envelope_id,
            "trace_id": event.trace_id,
            "replayable": True,
        },
    }


def _governance_block(
    *,
    decision: str,
    risk_tier: str | None = None,
    policy_effect: str | None = None,
    approval_ticket_id: str | None = None,
    policy_mode: str = "enforce",
) -> dict[str, Any]:
    return {
        "decision": decision,
        "risk_tier": risk_tier,
        "policy_effect": policy_effect,
        "approval_ticket_id": approval_ticket_id,
        "policy_mode": policy_mode,
        "validated": True,
    }


def _memory_block(
    *,
    event: AetherEvent,
    ledger_event_type: str,
    record_id: str | None = None,
    replayable: bool = True,
) -> dict[str, Any]:
    return {
        "ledger_event_type": ledger_event_type,
        "causal_chain": [event.correlation_id],
        "replayable": replayable,
        "correlation_id": event.correlation_id,
        "causation_id": event.envelope_id,
        "trace_id": event.trace_id,
        "ledger_record_id": record_id,
    }


def _directive_state(event: AetherEvent, *, lifecycle_stage: str | None = None, sandbox: bool = False) -> dict[str, Any]:
    return ManifestationDirectiveState(
        correlation_id=event.correlation_id,
        causation_id=event.causation_id,
        trace_id=event.trace_id,
        topic=event.topic,
        directive_type=event.type,
        manifest_version=MANIFEST_VERSION,
        session_id=event.session_id,
        lifecycle_stage=lifecycle_stage,
        sandbox=sandbox,
    ).model_dump(mode="json")


def _manifestation_bridge_payload(event: AetherEvent, *, lifecycle_stage: str | None = None) -> dict[str, Any]:
    payload = event.model_dump(mode="json")
    nested_payload = payload.get("payload", {})
    payload["directive_state"] = _directive_state(event, lifecycle_stage=lifecycle_stage)
    payload["manifest_version"] = MANIFEST_VERSION
    payload["semantic_source"] = "backend"
    payload["frontend_contract"] = "render-only"
    payload["render_state"] = payload.get("render_state") if isinstance(payload.get("render_state"), dict) else nested_payload.get("render_state", {})
    payload["status"] = payload.get("status") if isinstance(payload.get("status"), dict) else nested_payload.get("status_block") or nested_payload.get("status", {})
    payload["replay"] = payload.get("replay") if isinstance(payload.get("replay"), dict) else nested_payload.get("replay", {})
    payload["diagnostics"] = payload.get("diagnostics") if isinstance(payload.get("diagnostics"), dict) else nested_payload.get("diagnostics", {})
    ManifestationDirectivePayload.model_validate({
        "directive_state": payload["directive_state"],
        "render_state": payload["render_state"],
        "status": payload["status"],
        "replay": payload["replay"],
        "diagnostics": payload["diagnostics"],
        "semantic_source": payload["semantic_source"],
    })
    return payload


def _validate_ingress_envelope(raw_payload: Dict[str, Any], session_id: str) -> AetherEvent:
    text = raw_payload.get("text", "")
    correlation = CorrelationPolicy.build(
        correlation_id=raw_payload.get("correlation_id"),
        causation_id=raw_payload.get("causation_id"),
        trace_id=raw_payload.get("trace_id"),
        session_id=session_id,
    )
    payload = {
        "client_message": raw_payload,
        "text": text,
        "status": _status_block("RECEIVED", "intent_ingress"),
        "directive_state": {
            "session_id": session_id,
            "manifest_version": MANIFEST_VERSION,
            "semantic_source": "backend",
            **{k: v for k, v in correlation.items() if v is not None},
        },
    }
    return AetherEvent(
        type=AetherEventType.INTENT_DETECTED,
        session_id=session_id,
        topic="intent.ingress",
        correlation_id=correlation["correlation_id"],
        causation_id=correlation["causation_id"],
        trace_id=correlation["trace_id"],
        origin={"service": "api", "subsystem": "body", "channel": session_id},
        target={"service": "genesis_core", "subsystem": "mind", "channel": "lifecycle"},
        payload=payload,
        governance={"validated": True, "policy_mode": "enforce"},
        memory={"ledger_event_type": "intent_ingress", "causal_chain": [correlation["correlation_id"]]},
    )


def _manifestation_payload(event: AetherEvent, *, lifecycle_stage: str | None = None) -> str:
    return json.dumps(_manifestation_bridge_payload(event, lifecycle_stage=lifecycle_stage))




def _runtime_policy_effect(runtime_result) -> str:
    return runtime_result.decision.policy_effect or (
        "DENY"
        if runtime_result.decision.status == "DENIED"
        else "REQUIRE_APPROVAL"
        if runtime_result.decision.status == "PENDING_APPROVAL"
        else "ALLOW"
    )


async def _publish_runtime_state(
    *,
    bus,
    session_id: str,
    ingress_envelope: AetherEvent,
    runtime_result,
    topic: str,
    event_type: AetherEventType,
    phase: str,
    label: str,
    ledger_event_type: str,
    origin: dict[str, Any],
    error: str | None = None,
    extra_payload: dict[str, Any] | None = None,
) -> None:
    directive_state = _directive_state(ingress_envelope, lifecycle_stage=phase)
    governance_block = _governance_block(
        decision=runtime_result.decision.status,
        risk_tier=runtime_result.decision.risk_tier.name,
        policy_effect=_runtime_policy_effect(runtime_result),
        approval_ticket_id=runtime_result.decision.ticket_id,
        policy_mode=runtime_result.decision.policy_mode,
    )
    context_block = _context_block(
        ingress_envelope,
        directive_state=directive_state,
        governance=governance_block,
        ledger_event_type="runtime_outcome",
    )
    memory_block = _memory_block(
        event=ingress_envelope,
        ledger_event_type=ledger_event_type,
        record_id=runtime_result.record_id,
    )
    payload = {
        "status": _status_block(label, phase),
        "runtime_outcome": runtime_result.outcome_metadata,
        **context_block,
    }
    if extra_payload:
        payload.update(extra_payload)
    await bus.publish(
        AetherEvent(
            type=event_type,
            session_id=session_id,
            topic=topic,
            correlation_id=ingress_envelope.correlation_id,
            causation_id=ingress_envelope.envelope_id,
            trace_id=ingress_envelope.trace_id,
            origin=origin,
            target={"service": "client", "subsystem": "manifestation", "channel": session_id},
            payload=payload,
            governance=governance_block,
            memory=memory_block,
            error=error,
        )
    )


router = APIRouter(tags=["aetherium"])


@router.post("/v1/session")
async def create_session(request: Request, body: Dict[str, Any]):
    """
    Control Plane: Establish a conscious connection.
    Requires:
    1. Valid .abe Contract (Identity)
    2. Valid Access Key (Permission)
    """
    access_key = body.get("access_key")
    abe_contract_json = body.get("abe_contract")

    app_state = request.app.state
    if not hasattr(app_state, "key_manager"):
        logger.warning("KeyManager not found on app state. Allowing Anonymous (Dev Mode).")
    else:
        key_manager: KeyManager = app_state.key_manager

        try:
            if not abe_contract_json:
                raise ValueError("Missing .abe contract")

            contract = ABEContract.from_json(
                json.dumps(abe_contract_json) if isinstance(abe_contract_json, dict) else abe_contract_json
            )

            if not access_key:
                raise ValueError("Missing Access Key")

            if not key_manager.validate_access(access_key, contract.identity.abe_id):
                logger.warning("Session Rejected: Invalid Key/Subscription for %s", contract.identity.abe_id)
                raise HTTPException(status_code=403, detail="Access Denied: Invalid Key or Subscription Suspended")

            logger.info("Session Authorized: %s [%s]", contract.identity.entity_name, contract.intent.primary_intent)

        except ValueError as exc:
            logger.error("Contract Validation Error: %s", exc)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            if isinstance(exc, HTTPException):
                raise exc
            logger.error("Session Error: %s", exc)
            raise HTTPException(status_code=500, detail="Internal Handshake Error") from exc

    session_id = f"ae-{uuid.uuid4().hex[:8]}"

    return {
        "session_id": session_id,
        "ws_endpoint": "/ws/v3/stream",
        "expires_in": 3600,
    }


@router.websocket("/ws/v3/stream")
async def stream_endpoint(websocket: WebSocket):
    """
    Data Plane: The Aetherium Stream.
    Bi-directional state emission and intent resonance.
    """
    await websocket.accept()

    session_id = websocket.query_params.get("session_id")
    if not session_id:
        session_id = f"ae-anon-{uuid.uuid4().hex[:6]}"

    logger.info("Stream Connected: %s", session_id)

    app_state = websocket.app.state
    if not hasattr(app_state, "aether_bus") or not hasattr(app_state, "engine"):
        logger.error("System Not Initialized (Bus/Engine missing)")
        await websocket.close(code=1011)
        return

    bus = app_state.aether_bus
    engine = app_state.engine
    directive_runtime: DirectiveRuntime = app_state.directive_runtime
    metric_collector = getattr(app_state, "metric_collector", None)

    async def bridge_callback(event: AetherEvent):
        try:
            if metric_collector:
                metric_collector.track_event(event)
            AetherEvent.model_validate(event.model_dump(mode="json"))
            await websocket.send_text(_manifestation_payload(event, lifecycle_stage="manifestation_emit"))
        except Exception as exc:
            logger.warning("Bridge Error %s: %s", session_id, exc)

    await bus.subscribe(session_id, bridge_callback)

    handshake_correlation = CorrelationPolicy.build(session_id=session_id)
    await bus.publish(
        AetherEvent(
            type=AetherEventType.HANDSHAKE,
            session_id=session_id,
            topic="manifestation.handshake",
            correlation_id=handshake_correlation["correlation_id"],
            trace_id=handshake_correlation["trace_id"],
            origin={"service": "api", "subsystem": "body", "channel": session_id},
            target={"service": "client", "subsystem": "manifestation", "channel": session_id},
            payload={
                "state": {"state": "connected", "confidence": 1.0, "energy": 1.0, "coherence": 1.0},
                "directive_state": {**handshake_correlation, "manifest_version": MANIFEST_VERSION, "semantic_source": "backend"},
                "status": _status_block("CONNECTED", "handshake"),
                "diagnostics": {"bridge": "ws_v3", "frontend_contract": "render-only"},
            },
            state=StateData(state="connected", confidence=1.0, energy=1.0, coherence=1.0),
            memory={"ledger_event_type": "manifestation_handshake", "causal_chain": [handshake_correlation["correlation_id"]]},
        )
    )

    try:
        while True:
            data_text = await websocket.receive_text()

            try:
                payload = json.loads(data_text)
            except json.JSONDecodeError:
                continue

            if payload.get("type") == "PING":
                await websocket.send_json({"type": "PONG"})
                continue

            ingress_envelope = _validate_ingress_envelope(payload, session_id)
            await bus.publish(ingress_envelope)

            user_text = payload.get("text", "")
            if not user_text and "intent_vector" in payload:
                user_text = "[Abstract Intent]"

            if user_text:
                ingress_envelope.payload.setdefault("action", "cognitive_query")
                ingress_envelope.payload.setdefault("resource", "mind.lifecycle")
                ingress_envelope.payload.setdefault("intent_type", "COGNITIVE_QUERY")

                async def governed_planner(envelope: AetherEvent) -> SystemIntent | None:
                    intent = SystemIntent(
                        origin_agent=session_id,
                        target_agent="AgioSage_v1",
                        intent_type="COGNITIVE_QUERY",
                        payload=IntentPayload(content=user_text, modality="text"),
                        correlation_id=envelope.correlation_id,
                        context=IntentContext(
                            emotional_valence=0.0,
                            energy_level=0.5,
                            turbulence=0.0,
                            source_confidence=1.0,
                        ),
                    )
                    return await engine.lifecycle.process_request(intent)

                async def process_task() -> None:
                    try:
                        runtime_result = await directive_runtime.handle_envelope(ingress_envelope, planner=governed_planner)
                        if runtime_result.decision.status == "PENDING_APPROVAL":
                            await _publish_runtime_state(
                                bus=bus,
                                session_id=session_id,
                                ingress_envelope=ingress_envelope,
                                runtime_result=runtime_result,
                                topic="governance.approval.pending",
                                event_type=AetherEventType.STATE_UPDATE,
                                phase="governance",
                                label="PENDING_APPROVAL",
                                ledger_event_type="governance_pending_approval",
                                origin={"service": "governance", "subsystem": "kernel", "channel": session_id},
                                extra_payload={
                                    "approval_ticket_id": runtime_result.decision.ticket_id,
                                    "reason": runtime_result.decision.reason,
                                },
                            )
                            return
                        if runtime_result.decision.status == "DENIED":
                            await _publish_runtime_state(
                                bus=bus,
                                session_id=session_id,
                                ingress_envelope=ingress_envelope,
                                runtime_result=runtime_result,
                                topic="governance.denied",
                                event_type=AetherEventType.DEGRADATION,
                                phase="governance",
                                label="DENIED",
                                ledger_event_type="governance_denied",
                                origin={"service": "governance", "subsystem": "kernel", "channel": session_id},
                                error=runtime_result.decision.reason,
                                extra_payload={"error": runtime_result.decision.reason},
                            )
                            return
                        if runtime_result.outcome_status == "ERROR":
                            await _publish_runtime_state(
                                bus=bus,
                                session_id=session_id,
                                ingress_envelope=ingress_envelope,
                                runtime_result=runtime_result,
                                topic="runtime.error",
                                event_type=AetherEventType.DEGRADATION,
                                phase="runtime",
                                label="ERROR",
                                ledger_event_type="runtime_outcome",
                                origin={"service": "genesis_core", "subsystem": "mind", "channel": "planner"},
                                error=runtime_result.detail,
                                extra_payload={"error": runtime_result.detail},
                            )
                            return

                        response_intent = runtime_result.response
                        if response_intent:
                            await bus.publish(
                                AetherEvent(
                                    type=AetherEventType.MANIFESTATION,
                                    session_id=session_id,
                                    topic="manifestation.response",
                                    correlation_id=response_intent.correlation_id or ingress_envelope.correlation_id,
                                    causation_id=ingress_envelope.envelope_id,
                                    trace_id=ingress_envelope.trace_id,
                                    origin={"service": "genesis_core", "subsystem": "mind", "channel": "lifecycle"},
                                    target={"service": "client", "subsystem": "manifestation", "channel": session_id},
                                    payload={
                                        "system_intent": response_intent.model_dump(),
                                        "status": _status_block(runtime_result.outcome_status or "COMPLETED", "manifestation"),
                                        "runtime_outcome": runtime_result.outcome_metadata,
                                        **_context_block(
                                            ingress_envelope,
                                            directive_state=_directive_state(ingress_envelope, lifecycle_stage="manifestation"),
                                            governance=_governance_block(
                                                decision=runtime_result.decision.status,
                                                risk_tier=runtime_result.decision.risk_tier.name,
                                                policy_effect=_runtime_policy_effect(runtime_result),
                                                approval_ticket_id=runtime_result.decision.ticket_id,
                                                policy_mode=runtime_result.decision.policy_mode,
                                            ),
                                            ledger_event_type="runtime_outcome",
                                        ),
                                    },
                                    governance=_governance_block(
                                        decision=runtime_result.decision.status,
                                        risk_tier=runtime_result.decision.risk_tier.name,
                                        policy_effect=_runtime_policy_effect(runtime_result),
                                        approval_ticket_id=runtime_result.decision.ticket_id,
                                        policy_mode=runtime_result.decision.policy_mode,
                                    ),
                                    memory=_memory_block(
                                        event=ingress_envelope,
                                        ledger_event_type="manifestation_emit",
                                        record_id=runtime_result.record_id,
                                    ),
                                )
                            )
                    except Exception as exc:
                        logger.error("Processing Error: %s", exc)
                        await bus.publish(
                            AetherEvent(
                                type=AetherEventType.DEGRADATION,
                                session_id=session_id,
                                topic="system.error",
                                correlation_id=ingress_envelope.correlation_id,
                                causation_id=ingress_envelope.envelope_id,
                                trace_id=ingress_envelope.trace_id,
                                origin={"service": "api", "subsystem": "body", "channel": session_id},
                                target={"service": "client", "subsystem": "manifestation", "channel": session_id},
                                    payload={
                                        "error": str(exc),
                                        "status": _status_block("ERROR", "runtime"),
                                        "runtime_outcome": {
                                            "type": "runtime_outcome",
                                            "event_type": "runtime_outcome",
                                            "correlation_id": ingress_envelope.correlation_id,
                                            "causation_id": ingress_envelope.envelope_id,
                                            "trace_id": ingress_envelope.trace_id,
                                            "action": ingress_envelope.payload.get("action"),
                                            "resource": ingress_envelope.payload.get("resource"),
                                            "decision_status": "ERROR",
                                            "outcome_status": "ERROR",
                                            "detail": str(exc),
                                            "replayable": True,
                                            "memory_stage": "not_committed",
                                        },
                                        **_context_block(ingress_envelope, directive_state=_directive_state(ingress_envelope, lifecycle_stage="error"), ledger_event_type="runtime_outcome"),
                                    },
                                    governance=_governance_block(decision="ERROR", policy_effect="ERROR"),
                                    memory=_memory_block(event=ingress_envelope, ledger_event_type="runtime_outcome"),
                                    error=str(exc),
                                )
                            )

                asyncio.create_task(process_task())

    except WebSocketDisconnect:
        logger.info("Stream Disconnected: %s", session_id)
    except Exception as exc:
        logger.error("Stream Error: %s", exc)
    finally:
        await bus.unsubscribe(session_id)
