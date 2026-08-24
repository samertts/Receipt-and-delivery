import pytest
from fastapi import WebSocketDisconnect


def test_notifications_websocket_accepts_active_user_and_handles_ping(client, admin_token):
    with client.websocket_connect(f'/api/ws/notifications?token={admin_token}') as websocket:
        assert websocket.receive_json()['type'] == 'connected'
        websocket.send_text('ping')
        assert websocket.receive_json() == {'type': 'pong'}


def test_notifications_websocket_rejects_invalid_token(client):
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect('/api/ws/notifications?token=invalid-token'):
            pass

    assert exc_info.value.code == 1008
