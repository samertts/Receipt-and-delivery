from app.models.user import User
from app.services.security import hash_password


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

    def test_user_can_view_dashboard_but_not_reports(self, client, user_token):
        headers = {"Authorization": f"Bearer {user_token}"}
        dashboard = client.get("/api/dashboard/summary", headers=headers)
        reports = client.get("/api/reports/summary", headers=headers)
        assert dashboard.status_code == 200
        assert reports.status_code == 403

    def test_admin_profile_returns_permissions(self, client, admin_token):
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["role"] == "admin"
        assert "manage_users" in data["permissions"]
        assert "view_reports" in data["permissions"]
        assert set(data["roles"]) == {"admin", "supervisor", "user", "auditor"}

    def test_admin_can_filter_and_update_user_status(self, client, admin_token, db):
        target = User(
            username="inactive-target",
            full_name="Inactive Target",
            password_hash=hash_password("Target@1234"),
            role="user",
            status="active",
        )
        db.add(target)
        db.commit()
        db.refresh(target)
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.put(
            f"/api/users/{target.id}",
            json={"status": "inactive"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "inactive"

        filtered = client.get("/api/users?status=inactive", headers=headers)
        assert filtered.status_code == 200
        assert any(item["username"] == "inactive-target" for item in filtered.json()["data"])

    def test_admin_cannot_deactivate_themselves(self, client, admin_token, db):
        admin = db.query(User).filter(User.username == "admin").one()
        response = client.put(
            f"/api/users/{admin.id}",
            json={"status": "inactive"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code in (400, 422)

    def test_user_cannot_delete_transaction(self, client, user_token):
        response = client.delete(
            "/api/transactions/some-id",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403
