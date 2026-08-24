from datetime import datetime


def test_liveness_returns_an_iso8601_utc_timestamp(client):
    response = client.get('/api/health/live')

    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'alive'
    assert body['timestamp'].endswith('Z')
    parsed = datetime.fromisoformat(body['timestamp'].replace('Z', '+00:00'))
    assert parsed.tzinfo is not None


def test_health_endpoint_keeps_unwrapped_health_contract(client):
    response = client.get('/api/health')

    assert response.status_code == 200
    body = response.json()
    assert body['status'] in {'ok', 'degraded'}
    assert body['checks']['app']['name']
    assert body['checks']['timestamp'].endswith('Z')
