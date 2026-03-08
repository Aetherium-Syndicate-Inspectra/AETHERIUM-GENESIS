from fastapi.testclient import TestClient

from src.backend.main import app


def test_logenesis_stream_flow_v3():
    """Regression test for the unified /ws/v3/stream transport."""
    with TestClient(app) as client:
        with client.websocket_connect('/ws/v3/stream?session_id=ae-test-logenesis') as websocket:
            handshake = websocket.receive_json()
            assert handshake['type'] == 'handshake'

            websocket.send_json({'text': 'hello'})

            received = []
            for _ in range(12):
                msg = websocket.receive_json()
                received.append(msg.get('type'))
                if msg.get('type') in {'manifestation', 'degradation'}:
                    break

            assert 'intent_detected' in received
            assert 'state_update' in received
            assert any(t in {'manifestation', 'degradation'} for t in received)
