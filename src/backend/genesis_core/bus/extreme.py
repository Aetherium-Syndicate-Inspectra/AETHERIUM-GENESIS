import asyncio
import logging
from typing import Dict, Callable, Awaitable, Set
from src.backend.genesis_core.protocol.schemas import AetherEvent
from src.backend.genesis_core.bus.base import BaseAetherBus

logger = logging.getLogger("AetherBusExtreme")

class AetherBusExtreme(BaseAetherBus):
    """
    Concrete implementation of the AetherBus using AsyncIO for the internal Data Plane.
    Acts as the high-speed nervous system for Aetherium.
    """
    def __init__(self):
        # session_id -> callback
        self._subscribers: Dict[str, Callable[[AetherEvent], Awaitable[None]]] = {}
        self._global_listeners: Set[Callable[[AetherEvent], Awaitable[None]]] = set()
        self._running = False

    async def connect(self):
        self._running = True
        logger.info("🚀 [AetherBusExtreme] Connected (AsyncIO Mode).")

    async def close(self):
        self._running = False
        self._subscribers.clear()
        self._global_listeners.clear()
        logger.info("🛑 [AetherBusExtreme] Closed.")

    async def publish(self, event: AetherEvent):
        """
        Dispatches the event to relevant subscribers.
        """
        if not self._running:
            return

        tasks = []

        # 1. Targeted Delivery
        if event.session_id:
            if event.session_id in self._subscribers:
                callback = self._subscribers[event.session_id]
                tasks.append(callback(event))
            else:
                # logger.debug(f"Event for unknown session {event.session_id} dropped.")
                pass

        # 2. Global Broadcast (if session_id is None, or if we have global listeners)
        # Note: In this simple model, if session_id is None, we broadcast to EVERYONE.
        if event.session_id is None:
            for callback in self._subscribers.values():
                tasks.append(callback(event))

        # 3. Global Listeners (Debug tools, Recorders) - always get everything
        for listener in self._global_listeners:
            tasks.append(listener(event))

        if tasks:
            # Run all callbacks concurrently
            await asyncio.gather(*tasks, return_exceptions=True)

    async def subscribe(self, session_id: str, callback: Callable[[AetherEvent], Awaitable[None]]):
        if session_id in self._subscribers:
            logger.warning(f"⚠️ [AetherBusExtreme] Session {session_id} already subscribed. Overwriting.")
        self._subscribers[session_id] = callback
        logger.debug(f"🔗 [AetherBusExtreme] Subscribed session: {session_id}")

    async def unsubscribe(self, session_id: str):
        if session_id in self._subscribers:
            del self._subscribers[session_id]
            logger.debug(f"🔌 [AetherBusExtreme] Unsubscribed session: {session_id}")

    async def add_global_listener(self, callback: Callable[[AetherEvent], Awaitable[None]]):
        """For system-wide logging or diagnostics."""
        self._global_listeners.add(callback)
