class TestRBAC:
    def test_user_cannot_manage_users(self, client, user_token):
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    def test_admin_can_manage_users(self, client, admin_token):
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_user_cannot_delete_transaction(self, client, user_token):
        response = client.delete(
            "/api/transactions/some-id",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403
