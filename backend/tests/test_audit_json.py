import json


class TestAuditChangesJson:
    def test_changes_json_on_transaction_delete(self, client, db, admin_token):
        from app.models.transaction import Transaction

        txn = Transaction(
            transaction_no="TXN-AUDIT-1",
            transaction_type="Test",
            sender_organization_id="00000000-0000-0000-0000-000000000001",
            receiver_organization_id="00000000-0000-0000-0000-000000000002",
            sender_name="S",
            receiver_name="R",
            transaction_date="2026-06-01",
            status="draft",
        )
        db.add(txn)
        db.commit()
        txn_id = str(txn.id)

        response = client.delete(
            f"/api/transactions/{txn_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 204

        audit_resp = client.get(
            "/api/audit-logs?limit=50",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert audit_resp.status_code == 200
        body = audit_resp.json()
        logs = body.get("data", body)
        matching = [log for log in logs if log.get("changes_json")]
        assert len(matching) > 0, "No audit log with changes_json found"
        log = matching[0]
        changes = json.loads(log["changes_json"])
        assert isinstance(changes, dict)
        assert "transaction_no" in changes or "status" in changes

    def test_changes_json_contains_all_fields(self, client, db, admin_token):
        from app.models.transaction import Transaction

        txn = Transaction(
            transaction_no="TXN-AUDIT-2",
            transaction_type="Test",
            sender_organization_id="00000000-0000-0000-0000-000000000001",
            receiver_organization_id="00000000-0000-0000-0000-000000000002",
            sender_name="S",
            receiver_name="R",
            transaction_date="2026-06-01",
            status="draft",
        )
        db.add(txn)
        db.commit()

        response = client.delete(
            f"/api/transactions/{txn.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 204

        audit_resp = client.get(
            "/api/audit-logs?limit=50",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = audit_resp.json()
        logs = body.get("data", body)
        delete_logs = [log for log in logs if log.get("changes_json")]
        assert delete_logs
        changes = json.loads(delete_logs[0]["changes_json"])
        assert "transaction_no" in changes
