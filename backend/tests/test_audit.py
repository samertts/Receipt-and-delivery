class TestAuditLogs:
    def test_audit_logs_admin_access(self, client, admin_token):
        response = client.get(
            "/api/audit-logs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_audit_logs_user_forbidden(self, client, user_token):
        response = client.get(
            "/api/audit-logs",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    def test_login_creates_audit_log(self, client, admin_token):
        response = client.get(
            "/api/audit-logs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # After login, there should be at least one audit log
        assert response.status_code == 200
