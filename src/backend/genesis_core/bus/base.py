from __future__ import annotations

import asyncio
import uuid
import warnings
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import msgpack
import orjson

from src.backend.genesis_core.bus.contracts import (
    BusAck,
    BusAckStatus,
    BusCodec,
    BusCodecAdapter,
    BusCompression,
    BusConfig,
    BusPublishRequest,
    CorrelationMixin,
)
from src.backend.genesis_core.protocol.schemas import AetherEvent, AetherEventType


class JsonBusCodec(BusCodecAdapter):
    def encode(self, payload: Dict[str, Any]) -> bytes:
        return orjson.dumps(payload)

    def decode(self, payload: bytes) -> Dict[str, Any]:
        return orjson.loads(payload)


class MsgpackBusCodec(BusCodecAdapter):
    def encode(self, payload: Dict[str, Any]) -> bytes:
        return msgpack.packb(payload, use_bin_type=True)

    def decode(self, payload: bytes) -> Dict[str, Any]:
        return msgpack.unpackb(payload, raw=False)


class BaseAetherBus(ABC, CorrelationMixin):
    """Canonical AetherBus abstraction for governed event transport."""

    def __init__(self, config: Optional[BusConfig] = None):
        self.config = config or BusConfig()
        self._running = False

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def close(self):
        pass

    @abstractmethod
    async def publish(self, event: AetherEvent) -> Optional[BusAck]:
        pass

    async def publish_request(self, request: BusPublishRequest) -> Optional[BusAck]:
        metadata = dict(request.metadata)
        correlation_id = self.ensure_correlation_id(
            request.event,
            metadata=metadata,
            correlation_id=request.correlation_id,
        )
        metadata.setdefault("codec", (request.codec or self.config.codec).value)
        metadata.setdefault("compression", (request.compression or self.config.compression).value)
        if request.topic:
            request.event.extensions.setdefault("topic", request.topic)
        request.event.extensions.setdefault("bus_metadata", {}).update(metadata)
        return await self.publish(request.event)

    @abstractmethod
    async def subscribe(self, session_id: str, callback):
        pass

    @abstractmethod
    async def unsubscribe(self, session_id: str):
        pass

    async def ack(self, event: AetherEvent, detail: Optional[str] = None) -> BusAck:
        correlation_id = self.ensure_correlation_id(event)
        return BusAck(
            message_id=str(uuid.uuid4()),
            status=BusAckStatus.ACCEPTED,
            correlation_id=correlation_id,
            detail=detail,
        )

    async def error(self, event: AetherEvent, detail: str) -> BusAck:
        correlation_id = self.ensure_correlation_id(event)
        return BusAck(
            message_id=str(uuid.uuid4()),
            status=BusAckStatus.ERROR,
            correlation_id=correlation_id,
            detail=detail,
        )

    def get_codec(self, codec: Optional[BusCodec] = None) -> BusCodecAdapter:
        selected = codec or self.config.codec
        if selected == BusCodec.JSON:
            return JsonBusCodec()
        return MsgpackBusCodec()

    def serialize_event(self, event: AetherEvent, codec: Optional[BusCodec] = None) -> bytes:
        self.ensure_correlation_id(event)
        event.extensions.setdefault("bus_metadata", {})
        event.extensions["bus_metadata"].setdefault("codec", (codec or self.config.codec).value)
        event.extensions["bus_metadata"].setdefault("compression", self.config.compression.value)
        return self.get_codec(codec).encode(event.model_dump(mode="json"))

    def deserialize_event(self, payload: bytes, codec: Optional[BusCodec] = None) -> AetherEvent:
        data = self.get_codec(codec).decode(payload)
        return AetherEvent(**data)

    def write(self, topic: str, payload: Any) -> str:
        warnings.warn(
            "BaseAetherBus.write() is a compatibility shim. Prefer publish_request() with a V3 envelope.",
            DeprecationWarning,
            stacklevel=2,
        )
        msg_id = str(uuid.uuid4())
        event = AetherEvent(
            type=AetherEventType.STATE_UPDATE,
            session_id=topic if topic != "system.broadcast" else "*",
        )
        event.extensions["raw_payload"] = payload
        event.extensions["topic"] = topic
        self.ensure_correlation_id(event)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.publish(event))
        except RuntimeError:
            pass
        return msg_id
