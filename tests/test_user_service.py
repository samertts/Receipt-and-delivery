"""User service tests."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


ADMIN_USER = {"id": 1, "username": "admin", "role": "Admin", "status": "Active"}


class TestAuthenticate:
    def test_valid_login(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import authenticate
        user = authenticate("admin", "Admin@123")
        assert user is not None
        assert user["username"] == "admin"
        assert user["role"] == "Admin"

    def test_wrong_password(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import authenticate
        result = authenticate("admin", "WrongPassword")
        assert result is None

    def test_nonexistent_user(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import authenticate
        result = authenticate("nobody", "password")
        assert result is None

    def test_empty_credentials(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import authenticate
        result = authenticate("", "")
        assert result is None

    def test_lockout_after_max_attempts(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import authenticate
        from lab_system.app.utils.errors import AuthenticationError
        for _ in range(5):
            authenticate("admin", "WrongPassword")
        with pytest.raises(AuthenticationError):
            authenticate("admin", "WrongPassword", max_attempts=5, lockout_minutes=5)


class TestChangePassword:
    def test_successful_change(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import authenticate, change_password
        user = authenticate("admin", "Admin@123")
        change_password(user["id"], "Admin@123", "NewPass@123")
        user2 = authenticate("admin", "NewPass@123")
        assert user2 is not None

    def test_wrong_old_password(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import change_password
        from lab_system.app.utils.errors import AuthenticationError
        with pytest.raises(AuthenticationError):
            change_password(1, "WrongOld", "NewPass@123")


class TestListUsers:
    def test_list_users(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import list_users
        users = list_users()
        assert len(users) >= 2
        assert any(u["username"] == "admin" for u in users)

    def test_list_includes_roles(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import list_users
        users = list_users()
        roles = [u["role"] for u in users]
        assert "Admin" in roles
        assert "User" in roles


class TestCreateUser:
    def test_create_user(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import create_user, list_users
        create_user("New User", "newuser", "Pass@123", "User", user=ADMIN_USER)
        users = list_users()
        assert any(u["username"] == "newuser" for u in users)

    def test_create_without_permission(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import create_user
        regular_user = {"id": 2, "username": "user1", "role": "User", "status": "Active"}
        with pytest.raises(Exception):
            create_user("Bad User", "baduser", "Pass@123", "User", user=regular_user)


class TestDisableEnableUser:
    def test_disable_user(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import disable_user, list_users
        disable_user(2, user=ADMIN_USER)
        users = list_users()
        user = next(u for u in users if u["id"] == 2)
        assert user["status"] == "Inactive"

    def test_enable_user(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import disable_user, enable_user, list_users
        disable_user(2, user=ADMIN_USER)
        enable_user(2, user=ADMIN_USER)
        users = list_users()
        user = next(u for u in users if u["id"] == 2)
        assert user["status"] == "Active"


class TestResetPassword:
    def test_reset_password(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import reset_password, authenticate
        reset_password(1, "ResetPass@123", user=ADMIN_USER)
        user = authenticate("admin", "ResetPass@123")
        assert user is not None


class TestNeedsPasswordChange:
    def test_needs_change_empty(self):
        from lab_system.app.services.user_service import needs_password_change
        assert needs_password_change({"password_changed_at": ""}) is True

    def test_no_change_when_set(self):
        from lab_system.app.services.user_service import needs_password_change
        assert needs_password_change({"password_changed_at": "2026-01-01T00:00:00"}) is False

    def test_no_change_when_none(self):
        from lab_system.app.services.user_service import needs_password_change
        assert needs_password_change({"password_changed_at": None}) is True


class TestRecordLoginAttempt:
    def test_record_attempt(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import record_login_attempt, get_recent_failures
        record_login_attempt("admin", True)
        record_login_attempt("admin", False)
        failures = get_recent_failures("admin", minutes=5)
        assert failures == 1

    def test_get_recent_failures_empty(self, fresh_db, seed_data):
        from lab_system.app.services.user_service import get_recent_failures
        failures = get_recent_failures("nobody", minutes=5)
        assert failures == 0
