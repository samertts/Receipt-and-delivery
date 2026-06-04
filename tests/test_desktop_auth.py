"""
Tests for the desktop app authentication and security modules.

Run with: python -m pytest tests/test_desktop_auth.py -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lab_system.app.auth.security import hash_password, verify_password
from lab_system.app.utils.validators import validate_password, validate_username


class TestDesktopPasswordHashing:
    def test_hash_and_verify(self):
        hashed = hash_password("Test@1234")
        assert verify_password("Test@1234", hashed)
        assert not verify_password("WrongPass1", hashed)

    def test_different_hashes(self):
        h1 = hash_password("Same@123")
        h2 = hash_password("Same@123")
        assert h1 != h2


class TestDesktopPasswordValidation:
    def test_valid_password(self):
        assert validate_password("Strong@123") is None

    def test_short_password(self):
        error = validate_password("Ab@1")
        assert error is not None

    def test_no_uppercase(self):
        error = validate_password("weakpass@1")
        assert error is not None

    def test_no_lowercase(self):
        error = validate_password("WEAKPASS@1")
        assert error is not None

    def test_no_digit(self):
        error = validate_password("Weakpass@a")
        assert error is not None

    def test_no_special(self):
        error = validate_password("Weakpass1a")
        assert error is not None


class TestDesktopUsernameValidation:
    def test_valid_username(self):
        assert validate_username("admin") is None
        assert validate_username("user_1") is None

    def test_short_username(self):
        error = validate_username("ab")
        assert error is not None

    def test_invalid_chars(self):
        error = validate_username("user name")
        assert error is not None
        error = validate_username("user@name")
        assert error is not None


class TestDesktopPermissions:
    def test_admin_permissions(self):
        from lab_system.app.auth.permissions import ROLE_PERMISSIONS
        assert "users.create" in ROLE_PERMISSIONS["Admin"]
        assert "dashboard.view" in ROLE_PERMISSIONS["Admin"]
        assert "settings.update" in ROLE_PERMISSIONS["Admin"]

    def test_user_permissions(self):
        from lab_system.app.auth.permissions import ROLE_PERMISSIONS
        assert "dashboard.view" in ROLE_PERMISSIONS["User"]
        assert "users.create" not in ROLE_PERMISSIONS["User"]
        assert "receipts.create" in ROLE_PERMISSIONS["User"]

    def test_require_permission_valid(self):
        from lab_system.app.auth.permissions import require_permission
        require_permission("Admin", "users.create")

    def test_require_permission_invalid(self):
        from lab_system.app.auth.permissions import require_permission
        from lab_system.app.utils.errors import AuthorizationError
        import pytest
        with pytest.raises(AuthorizationError):
            require_permission("User", "users.create")
