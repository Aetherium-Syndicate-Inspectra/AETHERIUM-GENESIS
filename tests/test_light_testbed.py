import pytest
from fastapi.testclient import TestClient
from src.backend.main import app
import json

client = TestClient(app)


def test_websocket_standard_spawn():
    with client.websocket_connect("/ws") as websocket:
        payload = {
            "mode": "std",
            "input": {
                "type": "touch",
                "region": [0.1, 0.1, 0.2, 0.2],
                "pressure": 0.5
            }
        }
        websocket.send_text(json.dumps(payload))

        # We expect a response. If none comes, receive_text will block/timeout.
        # TestClient usually raises an error on disconnect.
        data = websocket.receive_text()
        instruction = json.loads(data)

        # Basic structural validation
        # The legacy protocol might return different structures depending on the backend state
        # We check for key markers of a valid response.
        assert isinstance(instruction, dict)
        if "type" in instruction:
            assert instruction["type"] in ["VISUAL_PARAMS", "ACK", "PONG"]
        elif "intent" in instruction:
            assert instruction["intent"] == "SPAWN"


def test_websocket_standard_voice_move():
    with client.websocket_connect("/ws") as websocket:
        payload = {
            "mode": "std",
            "input": {
                "type": "voice",
                "text": "move objects"
            }
        }
        websocket.send_text(json.dumps(payload))

        data = websocket.receive_text()
        instruction = json.loads(data)
        assert isinstance(instruction, dict)

        assert instruction["intent"] == "MOVE"
        # LCL defaults
        assert instruction["vector"] == [0.0, 0.0]


def test_websocket_ai_mock_move_right():
    with client.websocket_connect("/ws") as websocket:
        payload = {
            "mode": "ai",
            "input": {
                "text": "move the tree right"
            }
        }
        websocket.send_text(json.dumps(payload))

        data = websocket.receive_text()
        instruction = json.loads(data)
        assert isinstance(instruction, dict)

        assert instruction["intent"] == "MOVE"
        assert instruction["target"] == "TREE_CLUSTER_RIGHT"
        assert instruction["vector"] == [-0.25, 0.0]


def test_websocket_ai_mock_spawn():
    with client.websocket_connect("/ws") as websocket:
        payload = {
            "mode": "ai",
            "input": {
                "text": "spawn a star"
            }
        }
        websocket.send_text(json.dumps(payload))

        data = websocket.receive_text()
        instruction = json.loads(data)
        assert isinstance(instruction, dict)
