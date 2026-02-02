from fastapi import APIRouter, WebSocket, Request, WebSocketDisconnect, HTTPException
from typing import Dict, Any, Optional
import uuid
import json
import logging
import asyncio
from datetime import datetime

from src.backend.genesis_core.protocol.schemas import (
    AetherEvent, AetherEventType, StateData, IntentData, IntentVector
)
from src.backend.genesis_core.models.intent import SystemIntent, IntentPayload, IntentContext

logger = logging.getLogger("AetheriumAPI")

router = APIRouter(tags=["aetherium"])

@router.post("/v1/session")
async def create_session(request: Request, body: Dict[str, Any]):
    """
    Control Plane: Establish a conscious connection.
    """
    client_type = body.get("client", "unknown")
    capabilities = body.get("capabilities", [])

    session_id = f"ae-{uuid.uuid4().hex[:8]}"

    logger.info(f"✨ New Session Requested: {session_id} [{client_type}]")

    # Store session metadata if needed (Redis/Mem) - Skipping for now

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

    # Handshake: Wait for session_id or assume anonymous?
    # For now, we assume query param or first message?
    # Let's rely on query param ?session_id=... or just generate one if missing.
    session_id = websocket.query_params.get("session_id")
    if not session_id:
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

    # 1. Define the Bridge (Bus -> WebSocket)
    async def bridge_callback(event: AetherEvent):
        try:
            # We filter in the Bus usually, but double check
            # Send to WS
            await websocket.send_text(event.model_dump_json())
        except Exception as e:
            logger.warning(f"Bridge Error {session_id}: {e}")
            # If WS is dead, we might want to cancel subscription?
            # The finally block handles it usually.

    # 2. Subscribe to the Aether
    await bus.subscribe(session_id, bridge_callback)

    # Send Initial State
    await bus.publish(AetherEvent(
        type=AetherEventType.HANDSHAKE,
        session_id=session_id,
        state=StateData(state="connected", confidence=1.0, energy=1.0, coherence=1.0)
    ))

    try:
        while True:
            # 3. Listen to Client (Intent Injection)
            data_text = await websocket.receive_text()

            try:
                payload = json.loads(data_text)
            except json.JSONDecodeError:
                continue

            # Check if this is a keep-alive
            if payload.get("type") == "PING":
                await websocket.send_json({"type": "PONG"})
                continue

            # Process Intent
            # Map Client JSON to SystemIntent
            # We assume the client sends something like { "text": "Hello" } or IntentVector

            user_text = payload.get("text", "")
            if not user_text and "intent_vector" in payload:
                user_text = "[Abstract Intent]" # TODO: Handle pure vector input

            if user_text:
                # Construct SystemIntent
                intent = SystemIntent(
                    origin_agent=session_id,
                    target_agent="AgioSage_v1",
                    intent_type="COGNITIVE_QUERY",
                    payload=IntentPayload(content=user_text, modality="text"),
                    context=IntentContext(
                        emotional_valence=0.0, # TODO: Parse from payload
                        energy_level=0.5,
                        turbulence=0.0,
                        source_confidence=1.0
                    )
                )

                # 4. Invoke AgioSage with Emission
                # Note: We access AgioSage via Engine -> Lifecycle
                # We do NOT await the full process if we want to keep listening?
                # Actually, AgioSage is async. If we await, we block input.
                # But for a conversation, blocking is okay-ish.
                # Ideally, spawn a task.

                async def process_task():
                    try:
                        await engine.lifecycle.agio_sage.process_query(intent, emitter=bus.publish)
                    except Exception as e:
                        logger.error(f"Processing Error: {e}")
                        await bus.publish(AetherEvent(
                            type=AetherEventType.DEGRADATION,
                            session_id=session_id,
                            error=str(e)
                        ))

                asyncio.create_task(process_task())

    except WebSocketDisconnect:
        logger.info(f"👋 Stream Disconnected: {session_id}")
    except Exception as e:
        logger.error(f"🔥 Stream Error: {e}")
    finally:
        # Cleanup
        await bus.unsubscribe(session_id)
