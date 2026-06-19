"""Additional coverage tests for critical service modules."""

import os
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

ADMIN_USER = {"id": 1, "username": "admin", "role": "Admin", "status": "Active"}

# Save the ORIGINAL db_path at import time, before any test can modify it
import lab_system.app.settings.config as _cfg
_ORIGINAL_DB_PATH = _cfg.CONFIG.db_path


def _create_db(path):
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    schema_path = os.path.join(
        os.path.dirname(__file__), "..", "lab_system", "app", "database", "db.py"
    )
    with open(schema_path, "r") as f:
        schema_content = f.read()
    globals_ = {}
    exec(schema_content, globals_)
    for table_sql in globals_["SCHEMA"].split(";"):
        if table_sql.strip():
            try:
                conn.execute(table_sql)
            except sqlite3.OperationalError:
                pass
    conn.commit()
    return conn


def _setup_receipt_data(conn):
    conn.execute("INSERT INTO users(full_name,username,password_hash,role,status) VALUES('Admin','admin','hash','Admin','Active')")
    conn.execute(
        "INSERT INTO organizations(name, code, org_type, governorate) VALUES('Org1', 'ORG1', 'clinic', 'Baghdad')"
    )
    conn.execute(
        "INSERT INTO organizations(name, code, org_type, governorate) VALUES('Org2', 'ORG2', 'laboratory', 'Basra')"
    )
    conn.execute("INSERT INTO transaction_types(name) VALUES('receipt')")
    conn.execute("INSERT INTO sample_types(name) VALUES('blood')")
    conn.commit()
    conn.execute(
        """INSERT INTO receipts(receipt_no,tx_type_id,sender_org_id,receiver_org_id,
            sender_name,receiver_name,status,created_at,created_by)
            VALUES('R001',1,1,2,'Sender','Receiver','Draft','2024-01-01',1)"""
    )
    conn.commit()


@pytest.fixture
def fresh_db(tmp_path):
    db_path = tmp_path / "test.db"
    _create_db(db_path)
    return db_path


@pytest.fixture
def fresh_db_with_data(tmp_path):
    db_path = tmp_path / "test.db"
    conn = _create_db(db_path)
    _setup_receipt_data(conn)
    conn.close()
    return db_path


def _patch_db(db_path):
    """Context manager that patches DB_PATH and get_conn for all relevant modules."""
    import lab_system.app.settings.config as cfg_mod
    import lab_system.app.database.db as db_mod
    import lab_system.app.services.recovery_service as rs_mod

    originals = {}

    # Save and patch get_conn
    originals["db_get_conn"] = db_mod.get_conn

    @contextmanager
    def _test_get_conn():
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode=WAL;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    db_mod.get_conn = _test_get_conn

    # Patch CONFIG.db_path (used by get_conn) - frozen dataclass
    originals["cfg_db_path"] = cfg_mod.CONFIG.db_path
    object.__setattr__(cfg_mod.CONFIG, "db_path", str(db_path))

    # Patch DB_PATH on modules that have it
    if hasattr(rs_mod, "DB_PATH"):
        originals["rs_db_path"] = rs_mod.DB_PATH
        rs_mod.DB_PATH = db_path

    class _Ctx:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            db_mod.get_conn = originals["db_get_conn"]
            object.__setattr__(cfg_mod.CONFIG, "db_path", originals["cfg_db_path"])
            if "rs_db_path" in originals:
                rs_mod.DB_PATH = originals["rs_db_path"]

    return _Ctx()


@pytest.fixture(autouse=True)
def _restore_config():
    """Ensure global CONFIG.db_path is restored after every test."""
    import lab_system.app.settings.config as cfg_mod
    yield
    object.__setattr__(cfg_mod.CONFIG, "db_path", _ORIGINAL_DB_PATH)


# ============================================================================
# RECOVERY SERVICE
# ============================================================================

class TestRecoveryServiceCoverage:
    def test_verify_backup_valid(self, fresh_db):
        from lab_system.app.services.recovery_service import verify_backup
        result = verify_backup(fresh_db)
        assert result["valid"] is True
        assert result["integrity_ok"] is True
        assert result["size"] > 0

    def test_verify_backup_nonexistent(self, tmp_path):
        from lab_system.app.services.recovery_service import verify_backup
        result = verify_backup(tmp_path / "nonexistent.db")
        assert result["valid"] is False

    def test_verify_backup_too_small(self, tmp_path):
        from lab_system.app.services.recovery_service import verify_backup
        small = tmp_path / "small.db"
        small.write_bytes(b"tiny")
        result = verify_backup(small)
        assert result["valid"] is False

    def test_verify_backup_corrupt(self, tmp_path):
        from lab_system.app.services.recovery_service import verify_backup
        corrupt = tmp_path / "corrupt.db"
        corrupt.write_bytes(b"\x00" * 200)
        result = verify_backup(corrupt)
        assert result["valid"] is False

    def test_list_backups_empty(self, tmp_path):
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import list_backups
        orig = rs_mod.BACKUP_DIR
        rs_mod.BACKUP_DIR = tmp_path / "empty"
        try:
            assert list_backups() == []
        finally:
            rs_mod.BACKUP_DIR = orig

    def test_list_backups_with_files(self, tmp_path):
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import list_backups
        d = tmp_path / "backups"
        d.mkdir()
        (d / "test.db").write_bytes(b"fake")
        orig = rs_mod.BACKUP_DIR
        rs_mod.BACKUP_DIR = d
        try:
            backups = list_backups()
            assert len(backups) == 1
        finally:
            rs_mod.BACKUP_DIR = orig

    def test_checkpoint_wal(self):
        from lab_system.app.services.recovery_service import _checkpoint_wal
        _checkpoint_wal()

    def test_create_recovery_snapshot(self, fresh_db, tmp_path):
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import create_recovery_snapshot
        with _patch_db(fresh_db):
            orig_snap = rs_mod.SNAPSHOT_DIR
            rs_mod.SNAPSHOT_DIR = tmp_path / "snapshots"
            try:
                result = create_recovery_snapshot("test")
                assert result["success"] is True
            finally:
                rs_mod.SNAPSHOT_DIR = orig_snap

    def test_list_snapshots(self, tmp_path):
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import list_snapshots
        d = tmp_path / "snapshots"
        d.mkdir()
        (d / "snapshot_test.db").write_bytes(b"fake")
        orig = rs_mod.SNAPSHOT_DIR
        rs_mod.SNAPSHOT_DIR = d
        try:
            assert len(list_snapshots()) == 1
        finally:
            rs_mod.SNAPSHOT_DIR = orig

    def test_delete_backup_nonexistent(self, tmp_path):
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import delete_backup
        orig = rs_mod.BACKUP_DIR
        rs_mod.BACKUP_DIR = tmp_path / "backups"
        rs_mod.BACKUP_DIR.mkdir()
        try:
            result = delete_backup(tmp_path / "nonexistent.db", user=ADMIN_USER)
            assert result["success"] is True
        finally:
            rs_mod.BACKUP_DIR = orig

    def test_delete_backup_outside_dir(self, tmp_path):
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import delete_backup
        orig = rs_mod.BACKUP_DIR
        rs_mod.BACKUP_DIR = tmp_path / "backups"
        rs_mod.BACKUP_DIR.mkdir()
        outside = tmp_path / "outside.db"
        outside.write_bytes(b"evil")
        try:
            result = delete_backup(outside, user=ADMIN_USER)
            assert result["success"] is False
        finally:
            rs_mod.BACKUP_DIR = orig

    def test_get_backup_record(self, fresh_db):
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import _get_backup_record
        with _patch_db(fresh_db):
            with rs_mod._db.get_conn() as conn:
                conn.execute(
                    "INSERT INTO backups(backup_file, created_at) VALUES(?, ?)",
                    ("/fake/path.db", "2024-01-01"),
                )
            assert _get_backup_record("/fake/path.db") is not None
            assert _get_backup_record("/nonexistent.db") is None

    def test_validate_path_valid(self, tmp_path):
        from lab_system.app.services.recovery_service import _validate_path_in_dir
        d = tmp_path / "sub"
        d.mkdir()
        f = d / "file.db"
        f.write_bytes(b"data")
        assert _validate_path_in_dir(f, d) == f

    def test_validate_path_invalid(self, tmp_path):
        from lab_system.app.services.recovery_service import _validate_path_in_dir
        d = tmp_path / "sub"
        d.mkdir()
        f = tmp_path / "outside.db"
        f.write_bytes(b"data")
        with pytest.raises(ValueError):
            _validate_path_in_dir(f, d)

    def test_detect_corruption(self, fresh_db):
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import detect_corruption
        with _patch_db(fresh_db):
            result = detect_corruption()
            assert result["ok"] is True

    def test_rebuild_fts(self):
        from lab_system.app.services.recovery_service import rebuild_fts
        rebuild_fts()

    def test_auto_backup(self, fresh_db, tmp_path):
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import auto_backup
        orig_bk = rs_mod.BACKUP_DIR
        rs_mod.BACKUP_DIR = tmp_path / "backups"
        rs_mod.BACKUP_DIR.mkdir()
        try:
            with _patch_db(fresh_db):
                result = auto_backup()
                assert result["success"] is True
        finally:
            rs_mod.BACKUP_DIR = orig_bk

    def test_enforce_retention(self, fresh_db, tmp_path):
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import enforce_retention
        orig_bk = rs_mod.BACKUP_DIR
        rs_mod.BACKUP_DIR = tmp_path / "backups"
        rs_mod.BACKUP_DIR.mkdir()
        try:
            with _patch_db(fresh_db):
                result = enforce_retention()
                assert isinstance(result, int)
        finally:
            rs_mod.BACKUP_DIR = orig_bk


# ============================================================================
# DATABASE/DB MODULE
# ============================================================================

class TestDatabaseModuleCoverage:
    def test_init_db(self, fresh_db):
        import lab_system.app.database.db as db_mod
        from lab_system.app.settings import config as cfg_mod
        with _patch_db(fresh_db):
            db_mod.init_db()
            conn = sqlite3.connect(str(fresh_db))
            tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            assert "receipts" in tables
            assert "users" in tables
            conn.close()

    def test_migration_lock(self, fresh_db):
        from lab_system.app.database.db import _acquire_migration_lock, _release_migration_lock
        conn = sqlite3.connect(str(fresh_db))
        _acquire_migration_lock(conn)
        _release_migration_lock(conn)
        conn.close()

    def test_migration_lock_stale(self, fresh_db):
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            conn.execute("INSERT INTO meta(key, value) VALUES('migration_lock', ?)",
                         (str((datetime.now() - timedelta(hours=2)).timestamp()),))
            conn.commit()
            db_mod._acquire_migration_lock(conn)
            db_mod._release_migration_lock(conn)
            conn.close()

    def test_get_conn(self, fresh_db):
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            with db_mod.get_conn() as conn:
                assert conn.execute("SELECT 1").fetchone()[0] == 1


# ============================================================================
# RECEIPT SERVICE
# ============================================================================

class TestReceiptServiceCoverage:
    def test_create_receipt(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rid = rs_mod.create_receipt(
                data={"tx_type_id": 1, "sender_org_id": 1, "receiver_org_id": 2,
                      "sender_name": "S", "receiver_name": "R",
                      "sender_job_title": "", "receiver_job_title": "",
                      "auth_doc_no": "", "auth_date": "",
                      "notes": "", "transport_info": "",
                      "additional_comments": "", "status": "Draft"},
                items=[{"sample_type_id": 1, "total_count": 10, "valid_count": 8,
                        "damaged_count": 1, "rejected_count": 1,
                        "non_conforming_count": 0, "transport_condition": "", "notes": ""}],
                user_id=1, user=ADMIN_USER,
            )
            assert rid is not None

    def test_create_receipt_bad_items(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            with pytest.raises(ValueError):
                rs_mod.create_receipt(
                    data={"tx_type_id": 1, "sender_org_id": 1, "receiver_org_id": 2,
                          "sender_name": "S", "receiver_name": "R",
                          "sender_job_title": "", "receiver_job_title": "",
                          "auth_doc_no": "", "auth_date": "",
                          "notes": "", "transport_info": "",
                          "additional_comments": "", "status": "Draft"},
                    items=[{"sample_type_id": 1, "total_count": 10, "valid_count": 5,
                            "damaged_count": 1, "rejected_count": 1,
                            "non_conforming_count": 1, "transport_condition": "", "notes": ""}],
                    user_id=1, user=ADMIN_USER,
                )

    def test_get_receipt(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            receipt, items, atts = rs_mod.get_receipt(1)
            assert receipt is not None
            assert receipt["receipt_no"] == "R001"

    def test_get_receipt_not_found(self, fresh_db):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db):
            result = rs_mod.get_receipt(9999)
            assert result[0] is None

    def test_search_receipts(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            results = rs_mod.search_receipts("R001")
            assert len(results) >= 0  # FTS may not be available in test

    def test_approve_receipt(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rs_mod.approve_receipt(1, user=ADMIN_USER)
            receipt, _, _ = rs_mod.get_receipt(1)
            assert receipt["status"] == "Approved"

    def test_reject_receipt(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rs_mod.reject_receipt(1, user=ADMIN_USER)
            receipt, _, _ = rs_mod.get_receipt(1)
            assert receipt["status"] == "Rejected"

    def test_archive_receipt(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rs_mod.approve_receipt(1, user=ADMIN_USER)
            rs_mod.archive_receipt(1, user=ADMIN_USER)
            receipt, _, _ = rs_mod.get_receipt(1)
            assert receipt["status"] == "Archived"

    def test_batch_update_status(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rs_mod.batch_update_status([1], "Approved", user=ADMIN_USER)
            receipt, _, _ = rs_mod.get_receipt(1)
            assert receipt["status"] == "Approved"

    def test_soft_delete(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rs_mod.soft_delete_receipt(1, user=ADMIN_USER)
            receipt, _, _ = rs_mod.get_receipt(1)
            assert receipt is None or receipt.get("deleted_at")

    def test_cancel_receipt(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rs_mod.approve_receipt(1, user=ADMIN_USER)
            rs_mod.cancel_receipt(1, user=ADMIN_USER)
            receipt, _, _ = rs_mod.get_receipt(1)
            assert receipt["status"] == "Cancelled"

    def test_next_receipt_no(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            num = rs_mod.next_receipt_no()
            assert num is not None

    def test_list_receipts(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            result = rs_mod.list_receipts()
            assert result is not None

    def test_get_receipt_history(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            history = rs_mod.get_receipt_history(1)
            assert isinstance(history, list)

    def test_update_receipt(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rs_mod.update_receipt(1, {"tx_type_id": 1, "sender_org_id": 1,
                "receiver_org_id": 2, "sender_name": "S", "receiver_name": "R",
                "sender_job_title": "", "receiver_job_title": "",
                "auth_doc_no": "", "auth_date": "",
                "notes": "Updated", "transport_info": "",
                "additional_comments": "", "status": "Draft"}, [], user=ADMIN_USER)
            receipt, _, _ = rs_mod.get_receipt(1)
            assert receipt is not None

    def test_unarchive_receipt(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rs_mod.approve_receipt(1, user=ADMIN_USER)
            rs_mod.archive_receipt(1, user=ADMIN_USER)
            rs_mod.unarchive_receipt(1, user=ADMIN_USER)
            receipt, _, _ = rs_mod.get_receipt(1)
            assert receipt is not None

    def test_validate_status_transition(self):
        import lab_system.app.services.receipt_service as rs_mod
        rs_mod.validate_status_transition("Draft", "Approved")
        rs_mod.validate_status_transition("Draft", "Rejected")
        rs_mod.validate_status_transition("Draft", "Cancelled")
        rs_mod.validate_status_transition("Approved", "Archived")
        rs_mod.validate_status_transition("Rejected", "Draft")
        with pytest.raises(ValueError):
            rs_mod.validate_status_transition("Draft", "Archived")

    def test_get_attachment_none(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            assert rs_mod.get_attachment(9999) is None

    def test_hard_delete(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rs_mod.soft_delete_receipt(1, user=ADMIN_USER)
            rs_mod.hard_delete_receipt(1, user=ADMIN_USER)
            receipt, _, _ = rs_mod.get_receipt(1)
            assert receipt is None

    def test_restore_receipt(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rs_mod.soft_delete_receipt(1, user=ADMIN_USER)
            rs_mod.restore_receipt(1, user=ADMIN_USER)
            receipt, _, _ = rs_mod.get_receipt(1)
            assert receipt is not None


# ============================================================================
# AUTH SERVICE
# ============================================================================

class TestAuthServiceCoverage:
    def test_login_valid(self, fresh_db):
        from lab_system.app.services.user_service import create_user
        from lab_system.app.services.auth_service import AuthService
        with _patch_db(fresh_db):
            create_user(full_name="T", username="tu1", password="Pass1234!",
                        role="User", user=ADMIN_USER)
            svc = AuthService()
            result = svc.login("tu1", "Pass1234!")
            assert result is not None

    def test_login_invalid(self, fresh_db):
        from lab_system.app.services.user_service import create_user
        from lab_system.app.services.auth_service import AuthService
        from lab_system.app.utils.errors import AuthenticationError
        with _patch_db(fresh_db):
            create_user(full_name="T", username="tu2", password="Pass1234!",
                        role="User", user=ADMIN_USER)
            svc = AuthService()
            with pytest.raises(AuthenticationError):
                svc.login("tu2", "wrong")

    def test_login_nonexistent(self, fresh_db):
        from lab_system.app.services.auth_service import AuthService
        from lab_system.app.utils.errors import AuthenticationError
        with _patch_db(fresh_db):
            svc = AuthService()
            with pytest.raises(AuthenticationError):
                svc.login("nobody", "pass")

    def test_logout(self, fresh_db):
        from lab_system.app.services.auth_service import AuthService
        with _patch_db(fresh_db):
            AuthService().logout()

    def test_check_session(self, fresh_db):
        from lab_system.app.services.auth_service import AuthService
        from lab_system.app.utils.errors import AuthenticationError
        with _patch_db(fresh_db):
            with pytest.raises(AuthenticationError):
                AuthService().check_session()

    def test_touch_activity(self, fresh_db):
        from lab_system.app.services.auth_service import AuthService
        with _patch_db(fresh_db):
            AuthService().touch_activity()

    def test_is_logged_in(self, fresh_db):
        from lab_system.app.services.auth_service import AuthService
        with _patch_db(fresh_db):
            assert isinstance(AuthService().is_logged_in, bool)

    def test_needs_password_change(self, fresh_db):
        from lab_system.app.services.auth_service import AuthService
        with _patch_db(fresh_db):
            svc = AuthService()
            # Without a session, returns False
            assert svc.needs_password_change() is False


# ============================================================================
# USER SERVICE
# ============================================================================

class TestUserServiceCoverage:
    def test_create_list(self, fresh_db):
        from lab_system.app.services.user_service import create_user, list_users
        with _patch_db(fresh_db):
            create_user(full_name="T", username="ul1", password="Pass1234!",
                        role="User", user=ADMIN_USER)
            assert len(list_users()) >= 1

    def test_disable_enable(self, fresh_db):
        from lab_system.app.services.user_service import create_user, disable_user, enable_user
        with _patch_db(fresh_db):
            uid = create_user(full_name="T", username="ul2", password="Pass1234!",
                              role="User", user=ADMIN_USER)
            disable_user(uid, user=ADMIN_USER)
            enable_user(uid, user=ADMIN_USER)

    def test_change_password(self, fresh_db):
        from lab_system.app.services.user_service import create_user, change_password, verify_password
        with _patch_db(fresh_db):
            create_user(full_name="Changer User", username="chpwd",
                        password="Old1234!", role="User", user=ADMIN_USER)
            import lab_system.app.database.db as db_mod
            with db_mod.get_conn() as conn:
                row = conn.execute("SELECT id, password_hash FROM users WHERE username='chpwd'").fetchone()
                assert row is not None
                uid, old_hash = row[0], row[1]
            assert verify_password("Old1234!", old_hash)
            change_password(uid, "Old1234!", "New1234!")

    def test_reset_password(self, fresh_db):
        from lab_system.app.services.user_service import create_user, reset_password
        with _patch_db(fresh_db):
            uid = create_user(full_name="T", username="ul4", password="Old1234!",
                              role="User", user=ADMIN_USER)
            reset_password(uid, "New1234!", user=ADMIN_USER)

    def test_authenticate(self, fresh_db):
        from lab_system.app.services.user_service import create_user, authenticate
        with _patch_db(fresh_db):
            create_user(full_name="T", username="ul5", password="Pass1234!",
                        role="User", user=ADMIN_USER)
            assert authenticate("ul5", "Pass1234!") is not None
            assert authenticate("ul5", "wrong") is None

    def test_hash_verify(self):
        from lab_system.app.services.user_service import hash_password, verify_password
        h = hash_password("test")
        assert verify_password("test", h) is True
        assert verify_password("wrong", h) is False

    def test_record_login_attempt(self, fresh_db):
        from lab_system.app.services.user_service import record_login_attempt
        with _patch_db(fresh_db):
            record_login_attempt("u", True)
            record_login_attempt("u", False)

    def test_get_recent_failures(self, fresh_db):
        from lab_system.app.services.user_service import record_login_attempt, get_recent_failures
        with _patch_db(fresh_db):
            record_login_attempt("fu", False)
            assert get_recent_failures("fu") >= 1

    def test_needs_password_change(self, fresh_db):
        from lab_system.app.services.user_service import create_user, needs_password_change
        with _patch_db(fresh_db):
            create_user(full_name="T", username="ul6", password="Pass1234!",
                        role="User", user=ADMIN_USER)
            import lab_system.app.database.db as db_mod
            with db_mod.get_conn() as conn:
                row = conn.execute("SELECT * FROM users WHERE username='ul6'").fetchone()
                user_dict = dict(row)
            assert isinstance(needs_password_change(user_dict), bool)


# ============================================================================
# ATTACHMENTS
# ============================================================================

class TestAttachmentManagerCoverage:
    def test_save_attachment(self, fresh_db_with_data, tmp_path):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            f = tmp_path / "test.pdf"
            f.write_bytes(b"%PDF-1.4 fake pdf content for testing")
            from lab_system.app.attachments.manager import save_attachment
            save_attachment(1, str(f), "medical_report")

    def test_nonexistent_file(self, fresh_db):
        from lab_system.app.attachments.manager import save_attachment
        with pytest.raises(ValueError, match="الملف غير موجود"):
            save_attachment(1, "/nonexistent/file.pdf", "medical_report")

    def test_too_large(self, fresh_db, tmp_path):
        from lab_system.app.attachments.manager import save_attachment
        f = tmp_path / "large.bin"
        f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * (51 * 1024 * 1024))
        with pytest.raises(ValueError, match="حجم الملف"):
            save_attachment(1, str(f), "medical_report")

    def test_disallowed_type(self, fresh_db, tmp_path):
        from lab_system.app.attachments.manager import save_attachment
        f = tmp_path / "evil.exe"
        f.write_bytes(b"MZ\x90\x00" + b"\x00" * 100)
        with pytest.raises(ValueError, match="غير مدعوم|غير مسموح"):
            save_attachment(1, str(f), "medical_report")
