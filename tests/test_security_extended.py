"""Security tests — SQL injection, path traversal, input validation."""

import os
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


ADMIN_USER = {"id": 1, "username": "admin", "role": "Admin", "status": "Active"}


class TestSQLInjection:
    """Verify SQL injection resistance."""

    def test_login_sql_injection_username(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import authenticate

        result = authenticate("' OR '1'='1", "anything")
        assert result is None

    def test_login_sql_injection_password(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import authenticate

        result = authenticate("admin", "' OR '1'='1")
        assert result is None

    def test_login_sql_injection_union(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import authenticate

        result = authenticate("admin' UNION SELECT * FROM users--", "anything")
        assert result is None

    def test_settings_sql_injection(self, fresh_db, seed_data):
        from lab_system.app.database import db

        with db.get_conn() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key=?",
                ("' OR '1'='1",),
            ).fetchone()
            assert row is None


class TestPathTraversal:
    """Verify path traversal resistance."""

    def test_backup_path_traversal(self, fresh_db, seed_data):
        from lab_system.app.services.recovery_service import restore_from_backup

        with pytest.raises((ValueError, Exception)):
            restore_from_backup(Path("../../etc/passwd"), user=ADMIN_USER)


class TestInputValidation:
    """Verify input validation."""

    def test_empty_username_rejected(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import authenticate

        result = authenticate("", "password")
        assert result is None

    def test_long_username_handled(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import authenticate

        long_name = "A" * 1000
        result = authenticate(long_name, "password")
        assert result is None

    def test_special_characters_handled(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import authenticate

        result = authenticate("!@#$%^&*()", "password")
        assert result is None

    def test_null_bytes_handled(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import authenticate

        result = authenticate("admin\x00", "password")
        assert result is None


class TestAuthentication:
    """Verify authentication security."""

    def test_password_hashed_not_stored_plaintext(self, fresh_db, seed_data):
        conn = sqlite3.connect(str(fresh_db))
        row = conn.execute("SELECT password_hash FROM users WHERE username='admin'").fetchone()
        conn.close()
        assert row is not None
        assert row[0] != "Admin@123"
        assert len(row[0]) > 20

    def test_password_change_requires_old(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import change_password

        with pytest.raises(Exception):
            change_password(1, "wrongoldpassword", "NewPass@123")


class TestAuthorization:
    """Verify authorization controls."""

    def test_admin_required_for_user_creation(self, fresh_db, seed_data):
        from lab_system.app.auth.permissions import with_permission

        @with_permission("users.create")
        def create_user_permitted(user=None):
            return True

        with pytest.raises(Exception):
            create_user_permitted()

    def test_regular_user_cannot_admin(self, fresh_db, seed_data):
        from lab_system.app.auth.permissions import with_permission

        regular_user = {"id": 2, "username": "user1", "role": "User", "status": "Active"}

        @with_permission("users.delete")
        def delete_user_permitted(user=None):
            return True

        with pytest.raises(Exception):
            delete_user_permitted(user=regular_user)
