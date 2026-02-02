import asyncio
import logging
import json
from src.backend.genesis_core.bus.hyper_sonic import HyperSonicBus
from .dashboard import AetheriumHealthDashboard

logger = logging.getLogger("AuditoriumService")

class AuditoriumService:
    def __init__(self, engine):
        self.engine = engine
        self.dashboard = AetheriumHealthDashboard(engine)
        self.bus = HyperSonicBus() # Writer role
        self.running = False
        self.task = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.task = asyncio.create_task(self.monitor_loop())
        logger.info("🏛️ Auditorium Service Started")

    async def stop(self):
        self.running = False
        if self.task:
            try:
                await self.task
            except asyncio.CancelledError:
                pass

    async def monitor_loop(self):
        logger.info("🏛️ Auditorium Monitor Loop Active")
        while self.running:
            try:
                # 1. Update Auditors with Engine State
                # In a real implementation, we would inspect the engine deeply.
                # For now, we assume the engine exposes some properties or we access internal state.

                # Update Cognition History
                intent_data = getattr(self.engine, "last_intent_packet", None)
                if intent_data:
                    # Convert to dict if pydantic
                    if hasattr(intent_data, "model_dump"):
                        state_snapshot = intent_data.model_dump()
                    else:
                        state_snapshot = {"raw": str(intent_data)}

                    self.dashboard.cognition.record_state({"state": state_snapshot, "intent": "unknown"})

                # Update Consciousness State logic if engine supports it
                # ...

                # 2. Generate Report
                report = await self.dashboard.generate_comprehensive_report()

                # 3. Publish to AetherBus
                # Topic: system.health.report
                payload = json.dumps(report).encode()
                msg_id = self.bus.write("system.health.report", payload)

                # logger.debug(f"Health Report Published: {msg_id}")

                # 4. Sleep (Adaptive?)
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Auditorium Loop Error: {e}")
                await asyncio.sleep(5)
