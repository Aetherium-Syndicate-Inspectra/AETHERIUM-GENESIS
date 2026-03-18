import logging
import os
from typing import Optional

from src.backend.genesis_core.bus.contracts import (
    BusCodec,
    BusCompression,
    BusConfig,
    BusEndpoint,
    BusReconnectPolicy,
    BusRole,
)

logger = logging.getLogger("BusFactory")


class BusFactory:
    _instance = None

    @classmethod
    def reset(cls) -> None:
        cls._instance = None

    @classmethod
    def _load_config(cls) -> BusConfig:
        implementation = os.getenv("BUS_IMPLEMENTATION", "tachyon").strip().lower()
        codec = BusCodec(os.getenv("BUS_CODEC", BusCodec.MSGPACK.value).strip().lower())
        compression = BusCompression(os.getenv("BUS_COMPRESSION", BusCompression.NONE.value).strip().lower())
        internal_endpoint = BusEndpoint(
            role=BusRole.INTERNAL,
            transport=os.getenv("BUS_INTERNAL_TRANSPORT", "zeromq"),
            address=os.getenv("BUS_INTERNAL_ENDPOINT", "tcp://127.0.0.1:5555"),
        )
        external_endpoint = BusEndpoint(
            role=BusRole.EXTERNAL,
            transport=os.getenv("BUS_EXTERNAL_TRANSPORT", "websocket"),
            address=os.getenv("BUS_EXTERNAL_ENDPOINT", "ws://127.0.0.1:5556/ws"),
        )
        reconnect = BusReconnectPolicy(
            initial_delay_ms=int(os.getenv("BUS_RECONNECT_INITIAL_DELAY_MS", "250")),
            max_delay_ms=int(os.getenv("BUS_RECONNECT_MAX_DELAY_MS", "5000")),
            max_attempts=int(os.getenv("BUS_RECONNECT_MAX_ATTEMPTS", "10")),
        )
        return BusConfig(
            implementation=implementation,
            internal_endpoint=internal_endpoint,
            external_endpoint=external_endpoint,
            codec=codec,
            compression=compression,
            timeout_ms=int(os.getenv("BUS_TIMEOUT_MS", "2000")),
            reconnect=reconnect,
        )

    @classmethod
    def get_bus(cls, config: Optional[BusConfig] = None):
        if cls._instance is not None and config is None:
            return cls._instance

        resolved_config = config or cls._load_config()
        implementation = resolved_config.implementation.lower()

        if implementation == "tachyon":
            from src.backend.genesis_core.bus.tachyon import AetherBusTachyon
            bus = AetherBusTachyon(config=resolved_config)
        elif implementation in {"extreme", "legacy"}:
            from src.backend.genesis_core.bus.extreme import AetherBusExtreme
            bus = AetherBusExtreme(config=resolved_config)
        else:
            raise ValueError(f"Unsupported bus implementation: {implementation}")

        logger.info(
            "BusFactory selected implementation=%s internal=%s external=%s codec=%s compression=%s timeout_ms=%s",
            implementation,
            resolved_config.internal_endpoint.address,
            resolved_config.external_endpoint.address,
            resolved_config.codec.value,
            resolved_config.compression.value,
            resolved_config.timeout_ms,
        )
        if config is None:
            cls._instance = bus
        return bus
