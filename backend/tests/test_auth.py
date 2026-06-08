from app.services.security import create_access_token, hash_password, verify_password


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = hash_password("Test@1234")
        assert verify_password("Test@1234", hashed)
        assert not verify_password("WrongPass1", hashed)

    def test_different_hashes(self):
        h1 = hash_password("Test@1234")
        h2 = hash_password("Test@1234")
        assert h1 != h2


class TestTokenCreation:
    def test_create_access_token(self):
        token = create_access_token(sub="admin", role="admin")
        assert isinstance(token, str)
        assert len(token) > 20

    def test_token_with_refresh(self):
        from app.services.security import create_refresh_token
        token = create_refresh_token(sub="admin")
        assert isinstance(token, str)
        assert len(token) > 20


class TestLoginAPI:
    def test_login_success(self, client, db):
        from app.models.user import User

        user = User(
            username="testuser",
            full_name="Test User",
            password_hash=hash_password("Test@1234"),
            role="admin",
            status="active",
        )
        db.add(user)
        db.commit()

        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "Test@1234"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client):
        response = client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "Wrong@123"},
        )
        assert response.status_code == 401

    def test_login_missing_fields(self, client):
        response = client.post("/api/auth/login", json={"username": "admin"})
        assert response.status_code == 422


class TestRefreshToken:
    def test_refresh_success(self, client, db):
        from app.models.user import User
        from app.services.security import hash_password

        user = User(
            username="refreshuser",
            full_name="Refresh User",
            password_hash=hash_password("Test@1234"),
            role="admin",
            status="active",
        )
        db.add(user)
        db.commit()

        login_resp = client.post(
            "/api/auth/login",
            json={"username": "refreshuser", "password": "Test@1234"},
        )
        assert login_resp.status_code == 200
        refresh_token = login_resp.json()["refresh_token"]
        assert refresh_token

        refresh_resp = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 200
        data = refresh_resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_invalid_token(self, client):
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert response.status_code == 401


class TestLogout:
    def test_logout_success(self, client, admin_token):
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_logout_without_auth(self, client):
        response = client.post("/api/auth/logout")
        assert response.status_code == 401


class TestChangePassword:
    def test_change_password_success(self, client, db):
        from app.models.user import User
        from app.services.security import hash_password

        user = User(
            username="changepw",
            full_name="Change PW",
            password_hash=hash_password("Old@1234"),
            role="user",
            status="active",
        )
        db.add(user)
        db.commit()

        login_resp = client.post(
            "/api/auth/login",
            json={"username": "changepw", "password": "Old@1234"},
        )
        token = login_resp.json()["access_token"]

        response = client.post(
            "/api/auth/change-password",
            json={"current_password": "Old@1234", "new_password": "New@5678"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        login_resp2 = client.post(
            "/api/auth/login",
            json={"username": "changepw", "password": "New@5678"},
        )
        assert login_resp2.status_code == 200

    def test_change_password_wrong_current(self, client, admin_token):
        response = client.post(
            "/api/auth/change-password",
            json={"current_password": "Wrong@123", "new_password": "New@5678"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 401

    def test_change_password_weak_new(self, client, admin_token):
        response = client.post(
            "/api/auth/change-password",
            json={"current_password": "Admin@123", "new_password": "weak"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422


class TestProtectedEndpoints:
    def test_health_no_auth(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_transactions_no_auth(self, client):
        response = client.get("/api/transactions")
        assert response.status_code == 401

    def test_transactions_with_auth(self, client, admin_token):
        response = client.get(
            "/api/transactions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
