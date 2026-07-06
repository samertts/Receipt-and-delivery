"""Regression tests for desktop password policy enforcement."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_desktop_change_password_rejects_weak_new_password(fresh_db, seed_data):
    from lab_system.app.services.user_service import change_password
    from lab_system.app.utils.errors import ValidationError

    with pytest.raises(ValidationError):
        change_password(1, "Admin@123", "weak")


def test_desktop_reset_password_rejects_weak_password(fresh_db, seed_data):
    from lab_system.app.services.user_service import reset_password
    from lab_system.app.utils.errors import ValidationError

    with pytest.raises(ValidationError):
        reset_password(1, "weak", user={"role": "Admin"})
