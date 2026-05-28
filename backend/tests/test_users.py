class TestUsers:
    def test_create_user(self, client, admin_token):
        response = client.post(
            "/api/users",
            json={
                "username": "newuser",
                "full_name": "New User",
                "password": "NewUser@123",
                "role": "user",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["role"] == "user"

    def test_create_user_duplicate(self, client, admin_token):
        client.post(
            "/api/users",
            json={
                "username": "dupuser",
                "full_name": "Dup",
                "password": "DupUser@123",
                "role": "user",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        response = client.post(
            "/api/users",
            json={
                "username": "dupuser",
                "full_name": "Dup Again",
                "password": "DupUser@123",
                "role": "user",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 409

    def test_list_users(self, client, admin_token):
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
