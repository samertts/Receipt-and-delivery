import os
import sqlite3
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_db():
    from lab_system.app.auth.security import hash_password
    from lab_system.app.database.db import SCHEMA
    db_path = Path(tempfile.mkdtemp(prefix="lab_sec_")) / "test.db"
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


class TestSecurityEdgeCases:
    def setup_method(self):
        import lab_system.app.database.db as _db_mod
        self.tmp = Path(tempfile.mkdtemp(prefix="lab_sec_"))
        self.db_path = self.tmp / "test.db"
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        from lab_system.app.database.db import SCHEMA
        conn.executescript(SCHEMA)
        from lab_system.app.auth.security import hash_password
        pwd_hash = hash_password('Admin@123')
        conn.execute("INSERT INTO organizations(name,code,org_type,status) VALUES('Org A','OA-001','Lab','Active')")
        conn.execute("INSERT INTO users(full_name, username, password_hash, role, status) "
                     "VALUES('Admin','admin',?,'Admin','Active')", (pwd_hash,))
        conn.execute("INSERT INTO transaction_types(name,is_active) VALUES('Test',1)")
        conn.execute("INSERT INTO sample_types(name,category,status) VALUES('Serum','Blood','Active')")
        conn.commit()
        conn.close()
        _db_mod.get_conn = _make_get_conn(self.db_path)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_record_login_attempt_success(self):
        from lab_system.app.services.user_service import record_login_attempt
        from lab_system.app.database import db as _db
        record_login_attempt('testuser', True)
        with _db.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM login_attempts WHERE username='testuser' AND success=1"
            ).fetchone()
            assert row is not None
            assert row['success'] == 1
            assert row['username'] == 'testuser'
            assert row['attempted_at'] != ''

    def test_record_login_attempt_failure(self):
        from lab_system.app.services.user_service import record_login_attempt
        from lab_system.app.database import db as _db
        record_login_attempt('failuser', False)
        with _db.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM login_attempts WHERE username='failuser' AND success=0"
            ).fetchone()
            assert row is not None
            assert row['success'] == 0

    def test_get_recent_failures_zero(self):
        from lab_system.app.services.user_service import get_recent_failures
        count = get_recent_failures('nonexistent_user')
        assert count == 0

    def test_get_recent_failures_count(self):
        from lab_system.app.services.user_service import (
            record_login_attempt,
            get_recent_failures,
        )
        for _ in range(3):
            record_login_attempt('highfail', False)
        count = get_recent_failures('highfail', minutes=5)
        assert count >= 3

    def test_get_recent_failures_outside_window(self):
        from lab_system.app.services.user_service import (
            record_login_attempt,
            get_recent_failures,
        )
        from lab_system.app.database import db as _db
        record_login_attempt('oldfail', False)
        with _db.get_conn() as conn:
            conn.execute(
                "UPDATE login_attempts SET attempted_at='2000-01-01T00:00:00' WHERE username='oldfail'"
            )
        count = get_recent_failures('oldfail', minutes=5)
        assert count == 0

    def test_disabled_user_cannot_authenticate(self):
        from lab_system.app.services.user_service import (
            authenticate,
            disable_user,
        )
        user = authenticate('admin', 'Admin@123')
        assert user is not None
        admin_id = user['id']
        disable_user(admin_id)
        user = authenticate('admin', 'Admin@123')
        assert user is None

    def test_enable_user_after_disable(self):
        from lab_system.app.services.user_service import (
            authenticate,
            disable_user,
            enable_user,
        )
        disable_user(1)
        enable_user(1)
        user = authenticate('admin', 'Admin@123')
        assert user is not None


class TestAuditLog:
    def setup_method(self):
        import lab_system.app.database.db as _db_mod
        self.tmp = Path(tempfile.mkdtemp(prefix="lab_sec_aud_"))
        self.db_path = self.tmp / "test.db"
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        from lab_system.app.database.db import SCHEMA
        conn.executescript(SCHEMA)
        from lab_system.app.auth.security import hash_password
        pwd_hash = hash_password('Admin@123')
        conn.execute("INSERT INTO organizations(name,code,org_type,status) VALUES('Org A','OA-001','Lab','Active')")
        conn.execute("INSERT INTO users(full_name, username, password_hash, role, status) "
                     "VALUES('Admin','admin',?,'Admin','Active')", (pwd_hash,))
        conn.execute("INSERT INTO transaction_types(name,is_active) VALUES('Test',1)")
        conn.execute("INSERT INTO sample_types(name,category,status) VALUES('Serum','Blood','Active')")
        conn.commit()
        conn.close()
        _db_mod.get_conn = _make_get_conn(self.db_path)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_log_action_inserts_row(self):
        from lab_system.app.audit.logger import log_action
        from lab_system.app.database import db as _db
        log_action(1, 'test_action', 'test details')
        with _db.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM audit_logs WHERE action='test_action'"
            ).fetchone()
            assert row is not None
            assert row['user_id'] == 1
            assert row['details'] == 'test details'

    def test_log_action_with_empty_details(self):
        from lab_system.app.audit.logger import log_action
        from lab_system.app.database import db as _db
        log_action(None, 'empty_details')
        with _db.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM audit_logs WHERE action='empty_details'"
            ).fetchone()
            assert row is not None
            assert row['user_id'] is None

    def test_audit_chain_first_entry_has_empty_prev(self):
        from lab_system.app.audit.logger import log_action
        from lab_system.app.database import db as _db
        log_action(1, 'chain_test_1')
        with _db.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM audit_logs WHERE action='chain_test_1'"
            ).fetchone()
            assert row['prev_hash'] == ''

    def test_audit_chain_links_entries(self):
        from lab_system.app.audit.logger import log_action, _row_hash
        from lab_system.app.database import db as _db
        log_action(1, 'chain_a', 'first')
        log_action(1, 'chain_b', 'second')
        with _db.get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_logs WHERE action LIKE 'chain_%' ORDER BY id"
            ).fetchall()
            assert len(rows) == 2
            expected = _row_hash(rows[0])
            assert rows[1]['prev_hash'] == expected

    def test_verify_audit_chain_intact(self):
        from lab_system.app.audit.logger import log_action, verify_audit_chain
        log_action(1, 'vchain_1')
        log_action(1, 'vchain_2')
        ok, count, msg = verify_audit_chain()
        assert ok is True
        assert count == 2

    def test_verify_audit_chain_detects_tamper(self):
        from lab_system.app.audit.logger import log_action, verify_audit_chain
        from lab_system.app.database import db as _db
        log_action(1, 'tamper_test')
        log_action(1, 'tamper_test_2')
        with _db.get_conn() as conn:
            conn.execute("UPDATE audit_logs SET details='tampered' WHERE action='tamper_test'")
        ok, idx, msg = verify_audit_chain()
        assert ok is False
        assert idx >= 1


class TestValidators:
    def test_admin_password_from_env(self):
        import os
        orig = os.environ.pop('LAB_ADMIN_PASSWORD', None)
        try:
            from lab_system.app.services.user_service import _generate_admin_password
            pw = _generate_admin_password()
            assert len(pw) == 16
            os.environ['LAB_ADMIN_PASSWORD'] = 'Custom@Pass123'
            assert _generate_admin_password() == 'Custom@Pass123'
        finally:
            if orig is not None:
                os.environ['LAB_ADMIN_PASSWORD'] = orig
            else:
                os.environ.pop('LAB_ADMIN_PASSWORD', None)

    def test_validate_required_empty(self):
        import pytest
        from lab_system.app.utils.validators import validate_required
        from lab_system.app.utils.errors import ValidationError
        with pytest.raises(ValidationError):
            validate_required('', 'test')

    def test_validate_required_whitespace(self):
        import pytest
        from lab_system.app.utils.validators import validate_required
        from lab_system.app.utils.errors import ValidationError
        with pytest.raises(ValidationError):
            validate_required('   ', 'test')

    def test_validate_required_valid(self):
        from lab_system.app.utils.validators import validate_required
        assert validate_required('value', 'test') is None

    def test_password_validation_empty(self):
        from lab_system.app.utils.validators import validate_password
        error = validate_password('')
        assert error is not None

    def test_password_validation_only_special(self):
        from lab_system.app.utils.validators import validate_password
        error = validate_password('@$!%*#?&_')
        assert error is not None

    def test_password_validation_only_digits(self):
        from lab_system.app.utils.validators import validate_password
        error = validate_password('12345678')
        assert error is not None

    def test_password_validation_unicode_arabic(self):
        from lab_system.app.utils.validators import validate_password
        error = validate_password('كلمةمرور123')
        assert error is not None
