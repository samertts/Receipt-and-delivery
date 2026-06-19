"""Advanced tests for auth service, user service, and permissions."""

import os
import sqlite3
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

ADMIN_USER = {"id": 1, "username": "admin", "role": "Admin", "status": "Active"}


def _make_db():
    from lab_system.app.auth.security import hash_password
    from lab_system.app.database.db import SCHEMA
    db_path = Path(tempfile.mkdtemp(prefix="lab_auth_")) / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA)
    pwd_hash = hash_password('Admin@123')
    conn.execute("INSERT INTO organizations(name,code,org_type,status) VALUES('Org A','OA-001','Lab','Active')")
    conn.execute("INSERT INTO users(full_name, username, password_hash, role, status) "
                 "VALUES('Admin','admin',?,'Admin','Active')", (pwd_hash,))
    conn.execute("INSERT INTO transaction_types(name,is_active) VALUES('Test',1)")
    conn.execute("INSERT INTO sample_types(name,category,status) VALUES('Serum','Blood','Active')")
    conn.commit()
    conn.close()
    return db_path


def _make_get_conn(db_path):
    @contextmanager
    def test_conn():
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    return test_conn


class TestAuthServiceAdvanced:
    @classmethod
    def setup_class(cls):
        import lab_system.app.database.db as _db_mod
        cls.db_path = _make_db()
        _db_mod.get_conn = _make_get_conn(cls.db_path)

    def test_authenticate_valid(self):
        from lab_system.app.services.user_service import authenticate
        user = authenticate('admin', 'Admin@123')
        assert user is not None
        assert user['username'] == 'admin'

    def test_authenticate_invalid(self):
        from lab_system.app.services.user_service import authenticate
        user = authenticate('admin', 'wrong_password')
        assert user is None

    def test_authenticate_nonexistent(self):
        from lab_system.app.services.user_service import authenticate
        user = authenticate('noone', 'Admin@123')
        assert user is None

    def test_needs_password_change_new_user(self):
        from lab_system.app.services.user_service import (
            authenticate,
            needs_password_change,
        )
        user = authenticate('admin', 'Admin@123')
        result = needs_password_change(dict(user))
        assert result is True

    def test_change_password(self):
        from lab_system.app.services.user_service import authenticate, change_password
        change_password(1, 'Admin@123', 'NewPass456!')
        user = authenticate('admin', 'NewPass456!')
        assert user is not None
        change_password(1, 'NewPass456!', 'Admin@123')

    def test_change_password_wrong_old(self):
        import pytest

        from lab_system.app.services.user_service import change_password
        from lab_system.app.utils.errors import AuthenticationError
        with pytest.raises(AuthenticationError, match='كلمة المرور الحالية غير صحيحة'):
            change_password(1, 'wrong_password', 'NewPass456!')

    def test_session_timeout(self):
        from lab_system.app.services.auth_service import AuthService
        auth = AuthService()
        auth.login('admin', 'Admin@123')
        assert auth.current_user is not None
        auth.logout()
        assert auth.current_user is None

    def test_check_permission_valid(self):
        from lab_system.app.auth.permissions import check_permission
        check_permission({'role': 'Admin'}, 'dashboard.view')

    def test_check_permission_invalid(self):
        import pytest

        from lab_system.app.auth.permissions import check_permission
        from lab_system.app.utils.errors import AuthorizationError
        with pytest.raises(AuthorizationError):
            check_permission({'role': 'User'}, 'users.create')

    def test_require_permission_valid(self):
        from lab_system.app.auth.permissions import require_permission
        require_permission('Admin', 'receipts.delete')

    def test_require_permission_invalid(self):
        import pytest

        from lab_system.app.auth.permissions import require_permission
        from lab_system.app.utils.errors import AuthorizationError
        with pytest.raises(AuthorizationError):
            require_permission('User', 'receipts.delete')

    def test_list_users(self):
        from lab_system.app.services.user_service import list_users
        users = list_users()
        assert len(users) >= 1

    def test_seed_service(self):
        from lab_system.app.services.seed_service import seed_organizations
        result = seed_organizations(total=1)
        assert result is None

    def test_auth_is_logged_in(self):
        from lab_system.app.services.auth_service import AuthService
        auth = AuthService()
        auth.login('admin', 'Admin@123')
        assert auth.is_logged_in is True
        auth.logout()
        assert auth.is_logged_in is False

    def test_touch_activity(self):
        from lab_system.app.services.auth_service import AuthService
        auth = AuthService()
        auth.login('admin', 'Admin@123')
        old = auth._last_activity
        auth.touch_activity()
        assert auth._last_activity >= old

    def test_check_session_no_user(self):
        import pytest

        from lab_system.app.services.auth_service import AuthService
        from lab_system.app.utils.errors import AuthenticationError
        auth = AuthService()
        with pytest.raises(AuthenticationError):
            auth.check_session()

    def test_check_session_timeout(self):
        import pytest

        from lab_system.app.services.auth_service import AuthService
        from lab_system.app.utils.errors import SessionExpiredError
        auth = AuthService()
        auth.login('admin', 'Admin@123')
        auth._last_activity = auth._last_activity.replace(year=2000)
        with pytest.raises(SessionExpiredError):
            auth.check_session()

    def test_needs_password_change_no_user(self):
        from lab_system.app.services.auth_service import AuthService
        auth = AuthService()
        assert auth.needs_password_change() is False

    def test_change_password_no_user(self):
        import pytest

        from lab_system.app.services.auth_service import AuthService
        from lab_system.app.utils.errors import AuthenticationError
        auth = AuthService()
        with pytest.raises(AuthenticationError):
            auth.change_password('old', 'new')

    def test_auth_login_failure(self):
        import pytest

        from lab_system.app.services.auth_service import AuthService
        from lab_system.app.utils.errors import AuthenticationError
        auth = AuthService()
        with pytest.raises(AuthenticationError):
            auth.login('admin', 'wrong_password')

    def test_auth_lockout(self):
        import pytest

        from lab_system.app.database import db as _db
        from lab_system.app.services.auth_service import AuthService
        from lab_system.app.utils.errors import AuthenticationError
        auth = AuthService()
        for _ in range(5):
            try:
                auth.login('admin', 'wrong_password')
            except AuthenticationError:
                pass
        with pytest.raises(AuthenticationError, match='تم تجاوز عدد محاولات الدخول'):
            auth.login('admin', 'wrong_password')
        with _db.get_conn() as conn:
            conn.execute("DELETE FROM login_attempts")

    def test_seed_users_when_users_exist(self):
        from lab_system.app.services.user_service import seed_default_users
        result = seed_default_users()
        assert result is False

    def test_disable_and_reset_user(self):
        from lab_system.app.services.user_service import (
            authenticate,
            create_user,
            disable_user,
            list_users,
            reset_password,
        )
        create_user('Temp', 'temp', 'Temp@123', 'User', 1, user=ADMIN_USER)
        reset_password(1, 'NewPass789!', user=ADMIN_USER)
        user = authenticate('admin', 'NewPass789!')
        assert user is not None
        reset_password(1, 'Admin@123!', user=ADMIN_USER)
        users = list_users()
        new_user = next(u for u in users if u['username'] == 'temp')
        disable_user(new_user['id'], user=ADMIN_USER)
        users = list_users()
        disabled = next(u for u in users if u['id'] == new_user['id'])
        assert disabled['status'] == 'Inactive'


class TestSeedDefaultUsers:
    """Uses a fresh empty database to test seed_default_users()."""

    @classmethod
    def setup_class(cls):
        import lab_system.app.database.db as _db_mod
        from lab_system.app.database.db import SCHEMA
        cls.db_path = Path(tempfile.mkdtemp(prefix="lab_seed_")) / "test.db"
        conn = sqlite3.connect(str(cls.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(SCHEMA)
        conn.commit()
        conn.close()

        @contextmanager
        def test_conn():
            c = sqlite3.connect(str(cls.db_path))
            c.row_factory = sqlite3.Row
            c.execute("PRAGMA foreign_keys = ON;")
            try:
                yield c
                c.commit()
            finally:
                c.close()
        _db_mod.get_conn = test_conn

    def test_seed_users_creates_admin(self):
        from lab_system.app.services.user_service import (
            seed_default_users,
        )
        from lab_system.app.database import db as _db
        result = seed_default_users()
        assert result is True
        with _db.get_conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE username='admin'").fetchone()
            assert row is not None
            assert row['role'] == 'Admin'
            assert row['status'] == 'Active'
            assert row['password_changed_at'] != ''
