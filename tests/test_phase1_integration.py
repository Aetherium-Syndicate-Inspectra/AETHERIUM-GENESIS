from fastapi.testclient import TestClient

from src.backend.main import app


def test_phase1_websocket_flow_uses_v3_stream():
    """Ensure phase-1 style text input works on the unified v3 stream."""
    with TestClient(app) as client:
        with client.websocket_connect('/ws/v3/stream?session_id=ae-test-phase1') as websocket:
            handshake = websocket.receive_json()
            assert handshake['type'] == 'handshake'

            websocket.send_json({'text': 'Make a blue sphere'})

            seen_manifestation = False
            for _ in range(12):
                payload = websocket.receive_json()
                if payload.get('type') == 'manifestation':
                    manifestation = payload.get('manifestation', {})
                    assert manifestation.get('intent')
                    assert 'content' in manifestation
                    seen_manifestation = True
                    break

            assert seen_manifestation
