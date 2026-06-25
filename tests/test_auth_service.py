"""Tests for auth_service.py — Authentication service."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestAuthService:
    def test_login_success(self, fresh_db, seed_data):
        from lab_system.app.services.auth_service import AuthService

        svc = AuthService()
        user = svc.login("admin", "Admin@123")
        assert user is not None
        assert user["username"] == "admin"
        assert svc.is_logged_in

    def test_login_failure_wrong_password(self, fresh_db, seed_data):
        from lab_system.app.services.auth_service import AuthService
        from lab_system.app.utils.errors import AuthenticationError

        svc = AuthService()
        with pytest.raises(AuthenticationError):
            svc.login("admin", "wrongpassword")

    def test_login_failure_nonexistent_user(self, fresh_db, seed_data):
        from lab_system.app.services.auth_service import AuthService
        from lab_system.app.utils.errors import AuthenticationError

        svc = AuthService()
        with pytest.raises(AuthenticationError):
            svc.login("nonexistent", "password")

    def test_logout(self, fresh_db, seed_data):
        from lab_system.app.services.auth_service import AuthService

        svc = AuthService()
        svc.login("admin", "Admin@123")
        assert svc.is_logged_in
        svc.logout()
        assert not svc.is_logged_in
        assert svc.current_user is None

    def test_current_user_before_login(self, fresh_db):
        from lab_system.app.services.auth_service import AuthService

        svc = AuthService()
        assert svc.current_user is None
        assert not svc.is_logged_in

    def test_check_session_not_logged_in(self, fresh_db):
        from lab_system.app.services.auth_service import AuthService
        from lab_system.app.utils.errors import AuthenticationError

        svc = AuthService()
        with pytest.raises(AuthenticationError):
            svc.check_session()

    def test_check_session_active(self, fresh_db, seed_data):
        from lab_system.app.services.auth_service import AuthService

        svc = AuthService()
        svc.login("admin", "Admin@123")
        svc.check_session()  # Should not raise
        assert svc.is_logged_in

    def test_touch_activity(self, fresh_db, seed_data):
        from lab_system.app.services.auth_service import AuthService

        svc = AuthService()
        svc.login("admin", "Admin@123")
        svc.touch_activity()
        assert svc._last_activity is not None

    def test_needs_password_change_not_logged_in(self, fresh_db):
        from lab_system.app.services.auth_service import AuthService

        svc = AuthService()
        assert not svc.needs_password_change()

    def test_change_password_not_logged_in(self, fresh_db):
        from lab_system.app.services.auth_service import AuthService
        from lab_system.app.utils.errors import AuthenticationError

        svc = AuthService()
        with pytest.raises(AuthenticationError):
            svc.change_password("old", "new")

    def test_get_setting_default(self, fresh_db):
        from lab_system.app.services.auth_service import AuthService

        svc = AuthService()
        val = svc._get_setting("nonexistent.key", "default_val")
        assert val == "default_val"

    def test_get_setting_from_db(self, fresh_db, seed_data):
        from lab_system.app.services.auth_service import AuthService

        svc = AuthService()
        val = svc._get_setting("security.max_login_attempts", "5")
        assert val == "5"
