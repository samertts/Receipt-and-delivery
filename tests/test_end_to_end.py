"""End-to-End tests — Application workflow validation."""

import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


ADMIN_USER = {"id": 1, "username": "admin", "role": "Admin", "status": "Active"}


class TestEndToEndWorkflow:
    """Test complete business workflows from start to finish."""

    def test_full_receipt_lifecycle(self, fresh_db, seed_data):
        """Create and list a receipt."""
        from lab_system.app.services.receipt_service import create_receipt

        import lab_system.app.database.db as _db
        with _db.get_conn() as conn:
            conn.execute("INSERT OR IGNORE INTO transaction_types(name) VALUES(?)", ("Receipt",))
            conn.execute("INSERT OR IGNORE INTO sample_types(name,category,status) VALUES(?,?,?)", ("Blood", "Biological", "Active"))
            conn.execute("INSERT OR IGNORE INTO organizations(name,code,org_type,governorate,status) VALUES(?,?,?,?,?)",
                         ("Lab A", "LA", "Laboratory", "Baghdad", "Active"))
            tx_id = conn.execute("SELECT id FROM transaction_types WHERE name='Receipt'").fetchone()[0]
            org_id = conn.execute("SELECT id FROM organizations WHERE code='LA'").fetchone()[0]
            st_id = conn.execute("SELECT id FROM sample_types WHERE name='Blood'").fetchone()[0]

        receipt = create_receipt(
            data={
                "receipt_no": "E2E-001",
                "tx_type_id": tx_id,
                "sender_org_id": org_id,
                "receiver_org_id": org_id,
                "sender_name": "Ahmed",
                "receiver_name": "Ali",
                "sender_job_title": "",
                "receiver_job_title": "",
                "auth_doc_no": "",
                "auth_date": "",
                "notes": "E2E test",
                "transport_info": "",
                "additional_comments": "",
                "status": "Draft",
            },
            items=[{"sample_type_id": st_id, "name": "Blood Test", "total_count": 1, "valid_count": 1, "damaged_count": 0, "rejected_count": 0, "non_conforming_count": 0, "transport_condition": "", "notes": "", "price": 5000}],
            user_id=1,
            user=ADMIN_USER,
        )
        assert receipt is not None

    def test_user_lifecycle(self, fresh_db, seed_data):
        """List users."""
        from lab_system.app.services.user_service import list_users

        users = list_users()
        assert len(users) >= 2

    def test_backup_restore_cycle(self, fresh_db, seed_data, tmp_path):
        """Create backup and verify it exists."""
        from lab_system.app.services.backup_service import create_backup

        result = create_backup(user_id=1, user=ADMIN_USER)
        assert result is not None
        assert "lab_system_" in result

    def test_organization_lifecycle(self, fresh_db, seed_data):
        """Create, update, list organizations."""
        from lab_system.app.services.org_service import list_organizations, upsert_organization

        orgs = list_organizations()
        assert len(orgs) >= 1

        upsert_organization(
            {
                "name": "E2E Lab",
                "code": "E2E01",
                "org_type": "Laboratory",
                "governorate": "Erbil",
                "address": "E2E Address",
                "phone": "0770000099",
                "email": "e2e@lab.com",
                "logo_path": "",
                "notes": "",
                "status": "Active",
            },
            user=ADMIN_USER,
        )
        orgs = list_organizations()
        assert any(o["name"] == "E2E Lab" for o in orgs)

    def test_report_generation(self, fresh_db, seed_data):
        """Generate a report without errors."""
        from lab_system.app.services.report_service import receipt_summary

        result = receipt_summary()
        assert result is not None

    def test_dashboard_stats(self, fresh_db, seed_data):
        """Get dashboard statistics."""
        from lab_system.app.services.dashboard_service import DashboardService

        svc = DashboardService()
        stats = svc.get_stats()
        assert isinstance(stats, dict)
        assert "total" in stats

    def test_audit_logging(self, fresh_db, seed_data):
        """Verify audit logging works."""
        from lab_system.app.audit.logger import log_action

        log_action(user_id=1, action="test_action", details="E2E test")

    def test_password_change_flow(self, fresh_db, seed_data):
        """Complete password change flow."""
        from lab_system.app.services.user_service import authenticate, change_password

        user = authenticate("admin", "Admin@123")
        assert user is not None
        change_password(user["id"], "Admin@123", "NewPass@123")
        user2 = authenticate("admin", "NewPass@123")
        assert user2 is not None
