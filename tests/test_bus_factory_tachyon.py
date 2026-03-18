import pytest

from src.backend.genesis_core.bus.contracts import BusCodec, BusCompression, BusPublishRequest
from src.backend.genesis_core.bus.factory import BusFactory
from src.backend.genesis_core.protocol.schemas import AetherEvent, AetherEventType


def _reset_env(monkeypatch):
    for key in [
        "BUS_IMPLEMENTATION",
        "BUS_CODEC",
        "BUS_COMPRESSION",
        "BUS_INTERNAL_ENDPOINT",
        "BUS_EXTERNAL_ENDPOINT",
        "BUS_TIMEOUT_MS",
    ]:
        monkeypatch.delenv(key, raising=False)
    BusFactory.reset()


@pytest.mark.asyncio
async def test_factory_selects_tachyon_from_environment(monkeypatch):
    _reset_env(monkeypatch)
    monkeypatch.setenv("BUS_IMPLEMENTATION", "tachyon")
    monkeypatch.setenv("BUS_CODEC", "json")
    monkeypatch.setenv("BUS_COMPRESSION", "none")
    monkeypatch.setenv("BUS_INTERNAL_ENDPOINT", "tcp://127.0.0.1:5555")
    monkeypatch.setenv("BUS_EXTERNAL_ENDPOINT", "ws://127.0.0.1:5556/ws")

    bus = BusFactory.get_bus()

    assert bus.__class__.__name__ == "AetherBusTachyon"
    assert bus.config.codec == BusCodec.JSON
    assert bus.config.compression == BusCompression.NONE
    assert bus.config.internal_endpoint.address == "tcp://127.0.0.1:5555"
    assert bus.config.external_endpoint.address == "ws://127.0.0.1:5556/ws"
    BusFactory.reset()


@pytest.mark.asyncio
async def test_tachyon_publish_request_propagates_correlation_metadata(monkeypatch):
    _reset_env(monkeypatch)
    bus = BusFactory.get_bus()
    await bus.connect()

    received = []

    async def callback(event):
        received.append(event)

    await bus.subscribe("trace.session", callback)
    event = AetherEvent(type=AetherEventType.STATE_UPDATE, session_id="trace.session")

    ack = await bus.publish_request(
        BusPublishRequest(
            event=event,
            topic="trace.session",
            correlation_id="corr-123",
            codec=BusCodec.JSON,
            compression=BusCompression.NONE,
            metadata={"origin": "unit-test"},
        )
    )

    assert ack is not None
    assert ack.correlation_id == "corr-123"
    assert received[0].extensions["correlation_id"] == "corr-123"
    bus_metadata = received[0].extensions["bus_metadata"]
    assert bus_metadata["codec"] == "json"
    assert bus_metadata["compression"] == "none"
    assert bus_metadata["origin"] == "unit-test"

    await bus.close()
    BusFactory.reset()
