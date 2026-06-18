def _unwrap(body: dict) -> dict:
    return body.get("data", body)


class TestOrganizations:
    def test_create_organization(self, client, admin_token):
        response = client.post(
            "/api/organizations",
            json={
                "name": "مختبر بغداد المركزي",
                "code": "BGD-001",
                "address": "بغداد",
                "phone": "+964-771234567",
                "email": "bgd@lab.iq",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 201
        data = _unwrap(response.json())
        assert data["name"] == "مختبر بغداد المركزي"
        assert data["code"] == "BGD-001"

    def test_create_organization_duplicate_code(self, client, admin_token):
        client.post(
            "/api/organizations",
            json={"name": "Org1", "code": "ORG-001"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        response = client.post(
            "/api/organizations",
            json={"name": "Org2", "code": "ORG-001"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 409

    def test_list_organizations(self, client, admin_token):
        response = client.get(
            "/api/organizations",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
