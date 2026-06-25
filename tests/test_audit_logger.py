"""Audit logger tests."""

import os
import sys
import sqlite3


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestLogAction:
    def test_log_single_action(self, fresh_db, seed_data):
        from lab_system.app.audit.logger import log_action
        log_action(user_id=1, action="test_action", details="Test details")
        conn = sqlite3.connect(str(fresh_db))
        conn.row_factory = sqlite3.Row
        count = conn.execute("SELECT COUNT(*) c FROM audit_logs").fetchone()["c"]
        conn.close()
        assert count >= 1

    def test_log_multiple_actions(self, fresh_db, seed_data):
        from lab_system.app.audit.logger import log_action
        log_action(user_id=1, action="action1", details="First")
        log_action(user_id=1, action="action2", details="Second")
        conn = sqlite3.connect(str(fresh_db))
        conn.row_factory = sqlite3.Row
        count = conn.execute("SELECT COUNT(*) c FROM audit_logs").fetchone()["c"]
        conn.close()
        assert count >= 2

    def test_log_with_none_user(self, fresh_db, seed_data):
        from lab_system.app.audit.logger import log_action
        log_action(user_id=None, action="system_action", details="No user")

    def test_log_records_machine_name(self, fresh_db, seed_data):
        from lab_system.app.audit.logger import log_action
        log_action(user_id=1, action="test_machine", details="")
        conn = sqlite3.connect(str(fresh_db))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        assert row["machine_name"] is not None
        assert len(row["machine_name"]) > 0

    def test_log_records_timestamp(self, fresh_db, seed_data):
        from lab_system.app.audit.logger import log_action
        log_action(user_id=1, action="test_timestamp", details="")
        conn = sqlite3.connect(str(fresh_db))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        assert row["timestamp"] is not None


class TestAuditChain:
    def test_verify_empty_chain(self, fresh_db, seed_data):
        from lab_system.app.audit.logger import verify_audit_chain
        ok, count, msg = verify_audit_chain()
        assert ok is True
        assert count == 0

    def test_verify_valid_chain(self, fresh_db, seed_data):
        from lab_system.app.audit.logger import log_action, verify_audit_chain
        log_action(user_id=1, action="action1", details="First")
        log_action(user_id=1, action="action2", details="Second")
        log_action(user_id=1, action="action3", details="Third")
        ok, count, msg = verify_audit_chain()
        assert ok is True
        assert count == 3

    def test_verify_with_none_user(self, fresh_db, seed_data):
        from lab_system.app.audit.logger import log_action, verify_audit_chain
        log_action(user_id=None, action="system", details="System action")
        log_action(user_id=1, action="user_action", details="User action")
        ok, count, msg = verify_audit_chain()
        assert ok is True
        assert count == 2
