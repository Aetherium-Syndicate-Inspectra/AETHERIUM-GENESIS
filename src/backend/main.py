import asyncio
import json
import logging
import os
import sys
import time
import msgpack

# Ensure src is in path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

# Try to load uvloop for high performance (Server Mode)
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware

import math
from src.backend.genesis_core.logenesis.engine import LogenesisEngine
from src.backend.genesis_core.models.logenesis import LogenesisResponse, IntentPacket
from src.backend.genesis_core.models.visual import TemporalPhase, IntentCategory, BaseShape
from src.backend.auth.routes import router as auth_router
# Aetherium API Imports
from src.backend.routers.aetherium import router as aetherium_router
from src.backend.routers.metrics import router as metrics_router
from src.backend.routers.metrics import MetricCollector
from src.backend.routers.entropy import router as entropy_router
from src.backend.genesis_core.bus.extreme import AetherBusExtreme
from src.backend.security.key_manager import KeyManager
from src.backend.genesis_core.entropy import AkashicTreasury, EntropyValidator

from src.backend.departments.development.javana_core.reflex_kernel import JavanaKernel
from src.backend.departments.development.javana_core.responses import REFLEX_PARAMS

# Auditorium Imports
from src.backend.genesis_core.auditorium.service import AuditoriumService
from src.backend.genesis_core.bus.factory import BusFactory
import zlib
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AetherServer")

# --- Gatekeeper Middleware (Rate Limiting) ---
class GatekeeperMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.request_counts = {} # IP -> (timestamp, count)
        # Simple token bucket or window
        self.RATE_LIMIT = 1000 # requests per second (Very high for internal, adjust for public)

    async def dispatch(self, request: Request, call_next):
        # Basic Logic:
        # In a real scenario, use Redis. Here strictly in-memory for demo/speed.
        client_ip = request.client.host
        now = time.time()

        # Cleanup old entries (lazy)
        if client_ip in self.request_counts:
            ts, count = self.request_counts[client_ip]
            if now - ts > 1.0:
                 self.request_counts[client_ip] = (now, 1)
            else:
                 if count > self.RATE_LIMIT:
                     # 429 Too Many Requests
                     return JSONResponse(status_code=429, content={"error": "Gatekeeper: Rate Limit Exceeded"})
                 self.request_counts[client_ip] = (ts, count + 1)
        else:
             self.request_counts[client_ip] = (now, 1)

        response = await call_next(request)
        return response

app = FastAPI()
app.add_middleware(GatekeeperMiddleware)
app.include_router(auth_router)
app.include_router(aetherium_router)
app.include_router(metrics_router)
app.include_router(entropy_router)

# Global Services
auditorium: Optional[AuditoriumService] = None

# --- DEEPGRAM INTERFACE STUB ---
class DeepgramTranscriber:
    """Interface for Deepgram Live Transcription.

    Disabled by default, using Mock Mode in development.
    """
    def __init__(self, api_key: str = None):
        """Initializes the transcriber.

        Args:
            api_key: The Deepgram API key. If None, the transcriber is disabled.
        """
        self.api_key = api_key
        self.enabled = False # Set to True if API key is provided and needed

    async def transcribe_stream(self, audio_chunk: bytes):
        """Transcribes a chunk of audio data.

        Args:
            audio_chunk: Raw audio bytes.

        Returns:
            The transcribed text, or None if disabled.
        """
        if not self.enabled:
            return None
        # Actual Deepgram implementation would go here
        return "Deepgram Transcription Placeholder"

# Initialize Engine and Transcriber
engine = LogenesisEngine()
transcriber = DeepgramTranscriber(api_key=os.getenv("DEEPGRAM_API_KEY"))
# Initialize JAVANA (The Reflex System)
javana = JavanaKernel()

@app.on_event("startup")
async def startup_event():
    global auditorium

    # Awakening: Start the Bio-Digital Organism
    await engine.startup()

    # Initialize AetherBusExtreme (V2 Protocol)
    # We attach it to app.state for the API Router to use
    aether_bus = AetherBusExtreme()
    await aether_bus.connect()
    app.state.aether_bus = aether_bus
    app.state.engine = engine # Expose engine to router

    # Initialize Security & Metrics
    app.state.key_manager = KeyManager()
    app.state.entropy_validator = EntropyValidator()
    app.state.akashic_treasury = AkashicTreasury()

    metric_collector = MetricCollector.get_instance()
    app.state.metric_collector = metric_collector

    # Hook Metrics to Bus
    await aether_bus.add_global_listener(metric_collector.track_event)

    # Start Metrics Broadcast Loop
    asyncio.create_task(metric_collector.broadcast_loop())

    # Start Auditorium Service
    auditorium = AuditoriumService(engine)
    auditorium.start()

@app.on_event("shutdown")
async def shutdown_event():
    # Enter Nirodha
    await engine.shutdown()

    if hasattr(app.state, "aether_bus"):
        await app.state.aether_bus.close()

    if auditorium:
        await auditorium.stop()

# Mount static files and routes (Must be after specific routes)

# 1. Specific Asset Routes (for clean URLs in PWA)
@app.get("/sw.js")
async def get_sw():
    """
    Serve the frontend service worker JavaScript file.
    
    Returns:
        FileResponse: Response streaming the `src/frontend/public/sw.js` file with `application/javascript` media type.
    """
    return FileResponse(os.path.join(BASE_DIR, "src/frontend/public/sw.js"), media_type="application/javascript")

@app.get("/manifest.json")
async def get_manifest():
    """
    Serve the web application's manifest.json file.
    
    Returns:
        FileResponse: A response streaming the `src/frontend/public/manifest.json` file with media type `application/json`.
    """
    return FileResponse(os.path.join(BASE_DIR, "src/frontend/public/manifest.json"), media_type="application/json")

# 2. Mount Subdirectories
app.mount("/gunui", StaticFiles(directory=os.path.join(BASE_DIR, "src/frontend/public/gunui"), html=True), name="gunui")
app.mount("/icons", StaticFiles(directory=os.path.join(BASE_DIR, "src/frontend/public/icons")), name="icons")
app.mount("/public", StaticFiles(directory=os.path.join(BASE_DIR, "src/frontend/public")), name="public")

@app.get("/dashboard")
async def dashboard():
    """
    Serve the dashboard HTML page.
    
    Returns:
        FileResponse: A response that serves the dashboard.html file from the frontend directory.
    """
    return FileResponse(os.path.join(BASE_DIR, "src/frontend/dashboard.html"))

@app.get("/public")
async def public_gateway():
    """
    Serve the public gateway HTML page.
    
    Returns:
        FileResponse: Response that serves the `src/frontend/aether_public.html` file from the project base directory.
    """
    return FileResponse(os.path.join(BASE_DIR, "src/frontend/aether_public.html"))

@app.get("/overseer")
async def overseer_gateway():
    """
    Serve the Aether overseer HTML page.
    
    Returns:
        FileResponse: Response serving the `aether_overseer.html` file from the project's frontend directory.
    """
    return FileResponse(os.path.join(BASE_DIR, "src/frontend/aether_overseer.html"))

# 3. Mount Root (The Living Interface)
# NOTE: We mount src/frontend as root, so index.html is served at /
app.mount("/", StaticFiles(directory=os.path.join(BASE_DIR, "src/frontend"), html=True), name="root")