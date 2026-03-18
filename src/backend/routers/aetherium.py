from fastapi import APIRouter, WebSocket, Request, WebSocketDisconnect, HTTPException, Body
from typing import Dict, Any, Optional
import uuid
import json
import logging
import asyncio
from datetime import datetime

from src.backend.genesis_core.protocol.schemas import AetherEvent, AetherEventType, StateData
from src.backend.genesis_core.models.intent import SystemIntent, IntentPayload, IntentContext
from src.backend.genesis_core.protocol.abe_contract import ABEContract
from src.backend.security.key_manager import KeyManager

logger = logging.getLogger("AetheriumAPI")

def _validate_ingress_envelope(raw_payload: Dict[str, Any], session_id: str) -> AetherEvent:
    text = raw_payload.get("text", "")
    payload = {
        "client_message": raw_payload,
        "text": text,
    }
    return AetherEvent(
        type=AetherEventType.INTENT_DETECTED,
        session_id=session_id,
        topic="intent.ingress",
        correlation_id=raw_payload.get("correlation_id") or session_id,
        causation_id=raw_payload.get("causation_id"),
        origin={"service": "api", "subsystem": "body", "channel": session_id},
        target={"service": "genesis_core", "subsystem": "mind", "channel": "lifecycle"},
        payload=payload,
        governance={"validated": True, "policy_mode": "enforce"},
        memory={"ledger_event_type": "intent_ingress", "causal_chain": [session_id]},
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
    # 1. Extract Headers/Body
    access_key = body.get("access_key")
    abe_contract_json = body.get("abe_contract")

    # 2. Key Manager Lookup
    app_state = request.app.state
    if not hasattr(app_state, "key_manager"):
        # Fallback for testing/uninitialized state
        logger.warning("KeyManager not found on app state. Allowing Anonymous (Dev Mode).")
        # In PROD, raise HTTPException(503, "System Not Ready")
    else:
        key_manager: KeyManager = app_state.key_manager

        # 3. Validate Contract & Key
        try:
            # Parse Contract
            if not abe_contract_json:
                raise ValueError("Missing .abe contract")

            contract = ABEContract.from_json(json.dumps(abe_contract_json) if isinstance(abe_contract_json, dict) else abe_contract_json)

            # Verify Key Bind
            if not access_key:
                raise ValueError("Missing Access Key")

            if not key_manager.validate_access(access_key, contract.identity.abe_id):
                 logger.warning(f"Session Rejected: Invalid Key/Subscription for {contract.identity.abe_id}")
                 raise HTTPException(status_code=403, detail="Access Denied: Invalid Key or Subscription Suspended")

            logger.info(f"✅ Session Authorized: {contract.identity.entity_name} [{contract.intent.primary_intent}]")

        except ValueError as e:
            logger.error(f"Contract Validation Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
             if isinstance(e, HTTPException): raise e
             logger.error(f"Session Error: {e}")
             raise HTTPException(status_code=500, detail="Internal Handshake Error")

    # 4. Create Session
    session_id = f"ae-{uuid.uuid4().hex[:8]}"

    return {
        "session_id": session_id,
        "ws_endpoint": "/ws/v3/stream",
        "expires_in": 3600
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
        # Strict Mode: Should enforce session_id from /v1/session
        session_id = f"ae-anon-{uuid.uuid4().hex[:6]}"

    logger.info(f"🔗 Stream Connected: {session_id}")

    # Dependency Injection
    app_state = websocket.app.state
    if not hasattr(app_state, "aether_bus") or not hasattr(app_state, "engine"):
        logger.error("🔥 System Not Initialized (Bus/Engine missing)")
        await websocket.close(code=1011)
        return

    bus = app_state.aether_bus
    engine = app_state.engine

    # Metric Hook (if enabled)
    metric_collector = getattr(app_state, "metric_collector", None)

    # 1. Define the Bridge (Bus -> WebSocket)
    async def bridge_callback(event: AetherEvent):
        try:
            # Metric Tick
            if metric_collector:
                metric_collector.track_event(event)

            # Send to WS
            AetherEvent.model_validate(event.model_dump(mode="json"))
            await websocket.send_text(event.model_dump_json())
        except Exception as e:
            logger.warning(f"Bridge Error {session_id}: {e}")

    # 2. Subscribe to the Aether
    await bus.subscribe(session_id, bridge_callback)

    # Send Initial State
    await bus.publish(AetherEvent(
        type=AetherEventType.HANDSHAKE,
        session_id=session_id,
        topic="manifestation.handshake",
        origin={"service": "api", "subsystem": "body", "channel": session_id},
        target={"service": "client", "subsystem": "manifestation", "channel": session_id},
        payload={"state": {"state": "connected", "confidence": 1.0, "energy": 1.0, "coherence": 1.0}},
        state=StateData(state="connected", confidence=1.0, energy=1.0, coherence=1.0),
        memory={"ledger_event_type": "manifestation_handshake", "causal_chain": [session_id]},
    ))

    try:
        while True:
            # 3. Listen to Client (Intent Injection)
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
                intent = SystemIntent(
                    origin_agent=session_id,
                    target_agent="AgioSage_v1",
                    intent_type="COGNITIVE_QUERY",
                    payload=IntentPayload(content=user_text, modality="text"),
                    context=IntentContext(
                        emotional_valence=0.0,
                        energy_level=0.5,
                        turbulence=0.0,
                        source_confidence=1.0
                    )
                )

                async def process_task():
                    try:
                        response_intent = await engine.lifecycle.process_request(intent)
                        if response_intent:
                            await bus.publish(AetherEvent(
                                type=AetherEventType.MANIFESTATION,
                                session_id=session_id,
                                topic="manifestation.response",
                                correlation_id=response_intent.correlation_id or intent.vector_id,
                                causation_id=intent.vector_id,
                                origin={"service": "genesis_core", "subsystem": "mind", "channel": "lifecycle"},
                                target={"service": "client", "subsystem": "manifestation", "channel": session_id},
                                payload={"system_intent": response_intent.model_dump()},
                                governance={"validated": True, "policy_mode": "enforce"},
                                memory={"ledger_event_type": "manifestation_emit", "causal_chain": [intent.vector_id]},
                            ))
                    except Exception as e:
                        logger.error(f"Processing Error: {e}")
                        await bus.publish(AetherEvent(
                            type=AetherEventType.DEGRADATION,
                            session_id=session_id,
                            topic="system.error",
                            origin={"service": "api", "subsystem": "body", "channel": session_id},
                            target={"service": "client", "subsystem": "manifestation", "channel": session_id},
                            payload={"error": str(e)},
                            error=str(e),
                        ))

                asyncio.create_task(process_task())

    except WebSocketDisconnect:
        logger.info(f"👋 Stream Disconnected: {session_id}")
    except Exception as e:
        logger.error(f"🔥 Stream Error: {e}")
    finally:
        await bus.unsubscribe(session_id)
