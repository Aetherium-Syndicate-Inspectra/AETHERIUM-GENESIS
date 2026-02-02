import asyncio
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime
import json

from src.backend.genesis_core.protocol.schemas import AetherEvent, AetherEventType

logger = logging.getLogger("MetricCollector")

class MetricCollector:
    """
    Singleton Aggregator for AetherBus Metrics.
    Provides data for the Pulse/Flow visualizations.
    """
    _instance = None

    def __init__(self):
        self.total_events = 0
        self.events_per_second = 0.0
        self.active_sessions = 0
        self.start_time = datetime.now().timestamp()
        self._window_events = 0
        self._last_tick = self.start_time

        # Aggregate Counters
        self.intent_count = 0
        self.manifestation_count = 0

        # Subscribers (Dashboards)
        self.subscribers: List[WebSocket] = []

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def track_event(self, event: AetherEvent):
        """Called by AetherBusExtreme for every event."""
        self.total_events += 1
        self._window_events += 1

        if event.type == AetherEventType.INTENT_DETECTED:
            self.intent_count += 1
        elif event.type == AetherEventType.MANIFESTATION:
            self.manifestation_count += 1

    async def broadcast_loop(self):
        """Periodic broadcast to dashboard subscribers (1Hz)."""
        while True:
            await asyncio.sleep(1.0)
            now = datetime.now().timestamp()
            dt = now - self._last_tick

            # Calc rate
            if dt > 0:
                self.events_per_second = self._window_events / dt

            # Reset window
            self._window_events = 0
            self._last_tick = now

            # Payload
            metrics = {
                "type": "METRICS_UPDATE",
                "uptime": int(now - self.start_time),
                "throughput": round(self.events_per_second, 2),
                "total_processed": self.total_events,
                "active_sessions": self.active_sessions,
                "intents_processed": self.intent_count,
                "manifestations_created": self.manifestation_count,
                "system_status": "STABLE" if self.events_per_second < 1000 else "SATURATED"
            }

            # Broadcast
            dead_sockets = []
            for ws in self.subscribers:
                try:
                    await ws.send_json(metrics)
                except Exception:
                    dead_sockets.append(ws)

            for ws in dead_sockets:
                self.subscribers.remove(ws)

    async def register_dashboard(self, websocket: WebSocket):
        await websocket.accept()
        self.subscribers.append(websocket)
        logger.info("📈 Dashboard Connected")

router = APIRouter(tags=["metrics"])

@router.websocket("/ws/v3/metrics")
async def metrics_endpoint(websocket: WebSocket):
    collector = MetricCollector.get_instance()
    await collector.register_dashboard(websocket)
    try:
        while True:
            # Just keep alive, ignore input
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in collector.subscribers:
            collector.subscribers.remove(websocket)
