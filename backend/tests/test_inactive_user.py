class TestInactiveUser:
    def test_inactive_user_cannot_login(self, client, db):
        from app.models.user import User
        from app.services.security import hash_password

        user = User(
            username="inactive_user",
            full_name="Inactive User",
            password_hash=hash_password("Test@1234"),
            role="user",
            status="inactive",
        )
        db.add(user)
        db.commit()

        response = client.post(
            "/api/auth/login",
            json={"username": "inactive_user", "password": "Test@1234"},
        )
        assert response.status_code == 401

    def test_inactive_user_cannot_change_password(self, client, db):
        from app.models.user import User
        from app.services.security import hash_password, create_access_token

        user = User(
            username="inactive_change",
            full_name="Inactive Change",
            password_hash=hash_password("Old@1234"),
            role="user",
            status="inactive",
        )
        db.add(user)
        db.commit()

        token = create_access_token(sub=user.username, role=user.role)
        response = client.post(
            "/api/auth/change-password",
            json={"current_password": "Old@1234", "new_password": "New@5678"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_suspended_user_cannot_login(self, client, db):
        from app.models.user import User
        from app.services.security import hash_password

        user = User(
            username="suspended_user",
            full_name="Suspended User",
            password_hash=hash_password("Test@1234"),
            role="user",
            status="suspended",
        )
        db.add(user)
        db.commit()

        response = client.post(
            "/api/auth/login",
            json={"username": "suspended_user", "password": "Test@1234"},
        )
        assert response.status_code == 401
