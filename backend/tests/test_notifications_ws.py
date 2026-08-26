import pytest
from fastapi import WebSocketDisconnect

from app.core.cookie_auth import ACCESS_COOKIE


def test_notifications_websocket_accepts_active_user_and_handles_ping(client, admin_token):
    client.cookies.set(ACCESS_COOKIE, admin_token)
    with client.websocket_connect('/api/ws/notifications') as websocket:
        assert websocket.receive_json()['type'] == 'connected'
        websocket.send_text('ping')
        assert websocket.receive_json() == {'type': 'pong'}


def test_notifications_websocket_rejects_invalid_cookie(client):
    client.cookies.set(ACCESS_COOKIE, 'invalid-token')
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect('/api/ws/notifications') as websocket:
            websocket.receive_json()
    assert exc_info.value.code == 1008


def test_notifications_websocket_rejects_disallowed_origin(client, admin_token):
    client.cookies.set(ACCESS_COOKIE, admin_token)
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(
            '/api/ws/notifications', headers={'Origin': 'https://evil.example'}
        ) as websocket:
            websocket.receive_json()
    assert exc_info.value.code == 1008
