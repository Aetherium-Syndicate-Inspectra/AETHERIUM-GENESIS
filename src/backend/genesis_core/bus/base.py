from abc import ABC, abstractmethod
from typing import Callable, Awaitable
from src.backend.genesis_core.protocol.schemas import AetherEvent

class BaseAetherBus(ABC):
    """
    Abstract Interface for the Aetherium Data Plane.
    Decouples the API from the underlying transport (SharedMem, NATS, Memory).
    """

    @abstractmethod
    async def connect(self):
        """Initializes the bus connection."""
        pass

    @abstractmethod
    async def close(self):
        """Closes the bus connection."""
        pass

    @abstractmethod
    async def publish(self, event: AetherEvent):
        """
        Emits an event to the Aether.
        """
        pass

    @abstractmethod
    async def subscribe(self, session_id: str, callback: Callable[[AetherEvent], Awaitable[None]]):
        """
        Subscribes a client (Session) to the Aether stream.
        """
        pass

    @abstractmethod
    async def unsubscribe(self, session_id: str):
        """
        Unsubscribes a client.
        """
        pass
