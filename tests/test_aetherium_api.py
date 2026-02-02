from fastapi.testclient import TestClient
from src.backend.main import app
import json
import time

def test_aetherium_flow():
    # Trigger Startup Events
    with TestClient(app) as client:
        # 1. Control Plane
        response = client.post("/v1/session", json={"client": "test_script"})
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        session_id = data["session_id"]

        print(f"Session: {session_id}")

        # 2. Data Plane
        with client.websocket_connect(f"/ws/v3/stream?session_id={session_id}") as websocket:
            # Expect Handshake
            msg = websocket.receive_json()
            assert msg["type"] == "handshake"
            print("Handshake received")

            # Send Intent
            websocket.send_json({"text": "Hello Aether"})

            # Expect Stream
            received_types = []

            # We assume the background task runs.
            # In TestClient, asyncio background tasks created by `create_task` inside the request handler
            # MIGHT run if the loop yields. `receive_json` yields.

            for _ in range(5): # Safety limit
                try:
                    # Give it a bit of time logic? No, receive_json blocks.
                    msg = websocket.receive_json()
                    received_types.append(msg["type"])
                    print(f"Received: {msg['type']}")

                    if msg["type"] == "manifestation":
                        break
                    if msg["type"] == "degradation":
                        break
                except Exception as e:
                    print(f"Receive Error: {e}")
                    break

            assert "intent_detected" in received_types
            assert "state_update" in received_types
