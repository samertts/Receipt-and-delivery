def test_dashboard_summary_requires_authentication(client):
    response = client.get('/api/dashboard/summary')

    assert response.status_code == 401


def test_dashboard_summary_returns_chart_contract(client, admin_token):
    response = client.get(
        '/api/dashboard/summary',
        params={'days': 7},
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == 200
    body = response.json()
    assert body['success'] is True
    assert body['data']['summary']['total_transactions'] == 0
    assert body['data']['summary']['total_organizations'] == 0
    assert body['data']['summary']['by_status']['draft'] == 0
    assert len(body['data']['trend']) == 7
    assert all({'date', 'count'} <= set(point) for point in body['data']['trend'])
    assert body['data']['recent_transactions'] == []
    assert body['meta']['days'] == 7
