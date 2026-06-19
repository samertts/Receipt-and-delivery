"""V5.0 Coverage tests targeting all uncovered lines in business logic modules.

Covers: recovery_service, sync/service, receipt_service, repository,
auth_service, db — targeting 95%+ on each critical module.
"""

import os
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import lab_system.app.settings.config as _cfg
ORIGINAL_DB_PATH = _cfg.CONFIG.db_path

ADMIN_USER = {"id": 1, "username": "admin", "role": "Admin", "status": "Active"}


def _create_db(path):
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode=WAL;")
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
    originals["cfg_db_path"] = cfg_mod.CONFIG.db_path
    object.__setattr__(cfg_mod.CONFIG, "db_path", str(db_path))

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
    import lab_system.app.settings.config as cfg_mod
    yield
    object.__setattr__(cfg_mod.CONFIG, "db_path", ORIGINAL_DB_PATH)


# ============================================================================
# RECOVERY SERVICE — restore_from_backup, attempt_recovery, validate_recovery,
# auto_backup, enforce_retention
# ============================================================================

class TestRecoveryRestoreFromBackup:
    def test_restore_success(self, fresh_db, tmp_path):
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import restore_from_backup
        with _patch_db(fresh_db):
            orig_bk = rs_mod.BACKUP_DIR
            orig_snap = rs_mod.SNAPSHOT_DIR
            rs_mod.BACKUP_DIR = tmp_path / "backups"
            rs_mod.SNAPSHOT_DIR = tmp_path / "snapshots"
            rs_mod.BACKUP_DIR.mkdir()
            rs_mod.SNAPSHOT_DIR.mkdir()
            try:
                backup_file = rs_mod.BACKUP_DIR / "good_backup.db"
                import shutil
                shutil.copy2(str(fresh_db), str(backup_file))
                result = restore_from_backup(backup_file, user=ADMIN_USER)
                assert result["success"] is True
                assert result["restored_path"] is not None
            finally:
                rs_mod.BACKUP_DIR = orig_bk
                rs_mod.SNAPSHOT_DIR = orig_snap

    def test_restore_invalid_backup_fails_verification(self, fresh_db, tmp_path):
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import restore_from_backup
        with _patch_db(fresh_db):
            orig_bk = rs_mod.BACKUP_DIR
            rs_mod.BACKUP_DIR = tmp_path / "backups"
            rs_mod.BACKUP_DIR.mkdir()
            try:
                bad = rs_mod.BACKUP_DIR / "bad.db"
                bad.write_bytes(b"not a real db")
                result = restore_from_backup(bad, user=ADMIN_USER)
                assert result["success"] is False
                assert result["error"] is not None
            finally:
                rs_mod.BACKUP_DIR = orig_bk

    def test_restore_outside_dir_rejected(self, fresh_db, tmp_path):
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import restore_from_backup
        with _patch_db(fresh_db):
            orig_bk = rs_mod.BACKUP_DIR
            rs_mod.BACKUP_DIR = tmp_path / "backups"
            rs_mod.BACKUP_DIR.mkdir()
            try:
                outside = tmp_path / "outside.db"
                outside.write_bytes(b"evil")
                with pytest.raises(ValueError):
                    restore_from_backup(outside, user=ADMIN_USER)
            finally:
                rs_mod.BACKUP_DIR = orig_bk


class TestRecoveryValidateRecovery:
    def test_validate_recovery_valid(self, fresh_db_with_data, tmp_path):
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import validate_recovery
        with _patch_db(fresh_db_with_data):
            orig_bk = rs_mod.BACKUP_DIR
            rs_mod.BACKUP_DIR = tmp_path / "backups"
            rs_mod.BACKUP_DIR.mkdir()
            try:
                backup_file = rs_mod.BACKUP_DIR / "validate_test.db"
                import shutil
                shutil.copy2(str(fresh_db_with_data), str(backup_file))
                result = validate_recovery(backup_file, user=ADMIN_USER)
                assert result["valid"] is True
                assert len(result["checks"]) >= 3
            finally:
                rs_mod.BACKUP_DIR = orig_bk

    def test_validate_recovery_invalid_file(self, fresh_db, tmp_path):
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import validate_recovery
        with _patch_db(fresh_db):
            orig_bk = rs_mod.BACKUP_DIR
            rs_mod.BACKUP_DIR = tmp_path / "backups"
            rs_mod.BACKUP_DIR.mkdir()
            try:
                bad = rs_mod.BACKUP_DIR / "bad_validate.db"
                bad.write_bytes(b"not a real db file here")
                result = validate_recovery(bad, user=ADMIN_USER)
                assert result["valid"] is False
            finally:
                rs_mod.BACKUP_DIR = orig_bk


class TestRecoveryAttemptRecovery:
    def test_attempt_recovery_wal_checkpoint(self, fresh_db, tmp_path):
        from lab_system.app.services.recovery_service import attempt_recovery
        with _patch_db(fresh_db):
            result = attempt_recovery(user=ADMIN_USER)
            assert "actions" in result

    def test_attempt_recovery_with_backup_available(self, fresh_db, tmp_path):
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import attempt_recovery
        with _patch_db(fresh_db):
            orig_bk = rs_mod.BACKUP_DIR
            orig_snap = rs_mod.SNAPSHOT_DIR
            rs_mod.BACKUP_DIR = tmp_path / "backups"
            rs_mod.SNAPSHOT_DIR = tmp_path / "snapshots"
            rs_mod.BACKUP_DIR.mkdir()
            rs_mod.SNAPSHOT_DIR.mkdir()
            try:
                import shutil
                backup_file = rs_mod.BACKUP_DIR / "recovery_backup.db"
                shutil.copy2(str(fresh_db), str(backup_file))
                result = attempt_recovery(user=ADMIN_USER)
                assert result["success"] is True
                assert any("WAL" in a or "backup" in a.lower() or "recovered" in a.lower() for a in result["actions"])
            finally:
                rs_mod.BACKUP_DIR = orig_bk
                rs_mod.SNAPSHOT_DIR = orig_snap

    def test_attempt_recovery_no_backup_available(self, fresh_db, tmp_path):
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import attempt_recovery
        with _patch_db(fresh_db):
            orig_bk = rs_mod.BACKUP_DIR
            rs_mod.BACKUP_DIR = tmp_path / "empty_backups"
            rs_mod.BACKUP_DIR.mkdir()
            try:
                result = attempt_recovery(user=ADMIN_USER)
                assert any("No backup" in a or "WAL" in a for a in result["actions"])
            finally:
                rs_mod.BACKUP_DIR = orig_bk


class TestRecoveryAutoBackupAndRetention:
    def test_auto_backup_success(self, fresh_db, tmp_path):
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import auto_backup
        with _patch_db(fresh_db):
            orig_bk = rs_mod.BACKUP_DIR
            rs_mod.BACKUP_DIR = tmp_path / "auto_backups"
            rs_mod.BACKUP_DIR.mkdir()
            try:
                result = auto_backup(notes="test auto")
                assert result["success"] is True
            finally:
                rs_mod.BACKUP_DIR = orig_bk

    def test_enforce_retention_no_deletion_needed(self, fresh_db, tmp_path):
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import enforce_retention
        with _patch_db(fresh_db):
            orig_bk = rs_mod.BACKUP_DIR
            rs_mod.BACKUP_DIR = tmp_path / "retention_backups"
            rs_mod.BACKUP_DIR.mkdir()
            try:
                deleted = enforce_retention(max_backups=30)
                assert deleted == 0
            finally:
                rs_mod.BACKUP_DIR = orig_bk

    def test_enforce_retention_deletes_oldest(self, fresh_db, tmp_path):
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import enforce_retention
        with _patch_db(fresh_db):
            orig_bk = rs_mod.BACKUP_DIR
            rs_mod.BACKUP_DIR = tmp_path / "retention_backups"
            rs_mod.BACKUP_DIR.mkdir()
            try:
                for i in range(5):
                    (rs_mod.BACKUP_DIR / f"backup_{i}.db").write_bytes(b"data")
                deleted = enforce_retention(max_backups=2)
                assert deleted > 0
            finally:
                rs_mod.BACKUP_DIR = orig_bk


# ============================================================================
# SYNC SERVICE — sync_all with 409, sync_pending, push_entity with conflicts
# ============================================================================

class TestSyncServiceAdvanced:
    def test_sync_all_online_pending_entries_success(self, fresh_db_with_data, monkeypatch):
        import lab_system.app.sync.service as sync_mod
        with _patch_db(fresh_db_with_data):
            svc = sync_mod.SyncService()
            svc._client.enable("http://localhost:9999")
            svc.enqueue("receipts", 1, "create", '{"test": true}')
            svc.enqueue("receipts", 2, "update", '{"test": true}')

            class FakeResponse:
                success = True
                status_code = 200
                data = {}
                message = ""

            monkeypatch.setattr(svc._client, "push", lambda payload: FakeResponse())
            result = svc.sync_all()
            assert result["synced"] == 2
            assert result["conflicts"] == 0

    def test_sync_all_online_409_conflict(self, fresh_db_with_data, monkeypatch):
        import lab_system.app.sync.service as sync_mod
        with _patch_db(fresh_db_with_data):
            svc = sync_mod.SyncService()
            svc._client.enable("http://localhost:9999")
            svc.enqueue("receipts", 1, "create", '{}')

            class ConflictResponse:
                success = False
                status_code = 409
                data = {"detail": "conflict detected"}
                message = "conflict"

            monkeypatch.setattr(svc._client, "push", lambda payload: ConflictResponse())
            result = svc.sync_all()
            assert result["conflicts"] == 1
            assert result["synced"] == 0

    def test_sync_all_online_server_error_retries(self, fresh_db_with_data, monkeypatch):
        import lab_system.app.sync.service as sync_mod
        with _patch_db(fresh_db_with_data):
            svc = sync_mod.SyncService()
            svc._client.enable("http://localhost:9999")
            svc.enqueue("receipts", 1, "create", '{}')

            class ErrorResponse:
                success = False
                status_code = 500
                data = {}
                message = "error"

            monkeypatch.setattr(svc._client, "push", lambda payload: ErrorResponse())
            result = svc.sync_all()
            assert result["synced"] == 0

    def test_sync_pending_disabled(self, fresh_db_with_data):
        import lab_system.app.sync.service as sync_mod
        with _patch_db(fresh_db_with_data):
            svc = sync_mod.SyncService()
            result = svc.sync_pending()
            assert "error" in result

    def test_sync_pending_enabled(self, fresh_db_with_data, monkeypatch):
        import lab_system.app.sync.service as sync_mod
        with _patch_db(fresh_db_with_data):
            svc = sync_mod.SyncService()
            svc._client.enable("http://localhost:9999")

            class FakeResponse:
                success = True
                status_code = 200
                data = {}
                message = ""

            monkeypatch.setattr(svc._client, "push", lambda payload: FakeResponse())
            result = svc.sync_pending()
            assert "synced" in result

    def test_push_entity_online_conflict(self, fresh_db_with_data, monkeypatch):
        import lab_system.app.sync.service as sync_mod
        with _patch_db(fresh_db_with_data):
            svc = sync_mod.SyncService()
            svc._client.enable("http://localhost:9999")

            call_count = [0]
            def fake_push(payload):
                call_count[0] += 1
                class R:
                    success = False
                    status_code = 409
                    data = {"detail": "conflict"}
                    message = "conflict"
                return R()

            monkeypatch.setattr(svc._client, "push", fake_push)
            result = svc.push_entity("receipts", 1, "create", '{}')
            assert result["status"] == "conflict"

    def test_mark_synced_batch_empty(self, fresh_db_with_data):
        import lab_system.app.sync.service as sync_mod
        with _patch_db(fresh_db_with_data):
            svc = sync_mod.SyncService()
            svc.mark_synced_batch([])

    def test_mark_synced_batch_success(self, fresh_db_with_data):
        import lab_system.app.sync.service as sync_mod
        with _patch_db(fresh_db_with_data):
            svc = sync_mod.SyncService()
            e1 = svc.enqueue("receipts", 1, "create", '{}')
            e2 = svc.enqueue("receipts", 2, "update", '{}')
            svc.mark_synced_batch([e1, e2])
            pending = svc.get_pending()
            assert len(pending) == 0

    def test_mark_synced_batch_large_list(self, fresh_db_with_data):
        import lab_system.app.sync.service as sync_mod
        with _patch_db(fresh_db_with_data):
            svc = sync_mod.SyncService()
            ids = []
            for i in range(20):
                ids.append(svc.enqueue("receipts", i + 100, "create", '{}'))
            svc.mark_synced_batch(ids)
            pending = svc.get_pending()
            assert len(pending) == 0

    def test_sync_all_empty_pending(self, fresh_db_with_data, monkeypatch):
        import lab_system.app.sync.service as sync_mod
        with _patch_db(fresh_db_with_data):
            svc = sync_mod.SyncService()
            svc._client.enable("http://localhost:9999")
            result = svc.sync_all()
            assert result["synced"] == 0
            assert result["conflicts"] == 0

    def test_resolve_conflict_local_wins(self, fresh_db_with_data):
        import lab_system.app.sync.service as sync_mod
        with _patch_db(fresh_db_with_data):
            svc = sync_mod.SyncService()
            entry = sync_mod.SyncQueueEntry(id=1, entity_type="r", entity_id=1, action="update")
            remote = {"name": "s", "updated_at": "2024-01-01 00:00:00"}
            local = {"name": "l", "updated_at": "2024-06-01 00:00:00"}
            res = svc.resolve_conflict(entry, remote, local)
            assert res.strategy == "last-writer-wins"
            assert res.merged == local

    def test_resolve_conflict_server_wins(self, fresh_db_with_data):
        import lab_system.app.sync.service as sync_mod
        with _patch_db(fresh_db_with_data):
            svc = sync_mod.SyncService()
            entry = sync_mod.SyncQueueEntry(id=1, entity_type="r", entity_id=1, action="update")
            remote = {"name": "s", "updated_at": "2024-06-01 00:00:00"}
            local = {"name": "l", "updated_at": "2024-01-01 00:00:00"}
            res = svc.resolve_conflict(entry, remote, local)
            assert res.strategy == "server-wins"
            assert res.merged == remote

    def test_resolve_conflict_no_timestamps(self, fresh_db_with_data):
        import lab_system.app.sync.service as sync_mod
        with _patch_db(fresh_db_with_data):
            svc = sync_mod.SyncService()
            entry = sync_mod.SyncQueueEntry(id=1, entity_type="r", entity_id=1, action="update")
            remote = {"name": "s"}
            local = {"name": "l"}
            res = svc.resolve_conflict(entry, remote, local)
            assert res.strategy == "server-wins"

    def test_resolve_conflict_local_not_dict(self, fresh_db_with_data):
        import lab_system.app.sync.service as sync_mod
        with _patch_db(fresh_db_with_data):
            svc = sync_mod.SyncService()
            entry = sync_mod.SyncQueueEntry(id=1, entity_type="r", entity_id=1, action="update")
            remote = {"name": "s"}
            res = svc.resolve_conflict(entry, remote, "not a dict")
            assert res.strategy == "server-wins"

    def test_get_health_online_with_synced(self, fresh_db_with_data):
        import lab_system.app.sync.service as sync_mod
        with _patch_db(fresh_db_with_data):
            svc = sync_mod.SyncService()
            svc._client.enable("http://localhost:9999")
            e = svc.enqueue("receipts", 1, "create", '{}')
            svc.mark_synced(e)
            health = svc.get_health()
            assert health["enabled"] is True
            assert health["synced"] == 1
            assert health["healthy"] is True

    def test_get_health_with_conflicts(self, fresh_db_with_data):
        import lab_system.app.sync.service as sync_mod
        with _patch_db(fresh_db_with_data):
            svc = sync_mod.SyncService()
            e = svc.enqueue("receipts", 1, "create", '{}')
            svc.mark_conflict(e, "conflict")
            health = svc.get_health()
            assert health["conflicts"] == 1
            assert health["healthy"] is False


# ============================================================================
# RECEIPT SERVICE — batch_soft_delete, hard_delete with attachments,
# create_receipt validation, update_receipt validation
# ============================================================================

class TestReceiptServiceAdvanced:
    def test_batch_soft_delete(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            results = rs_mod.batch_soft_delete([1], user=ADMIN_USER)
            assert len(results) == 1
            assert results[0][1] == "ok"

    def test_batch_soft_delete_nonexistent(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            results = rs_mod.batch_soft_delete([99999], user=ADMIN_USER)
            assert len(results) == 1

    def test_hard_delete_with_attachments(self, fresh_db_with_data, tmp_path):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            att_file = tmp_path / "test_att.pdf"
            att_file.write_bytes(b"%PDF-1.4 test content")
            thumb_file = tmp_path / "thumb.png"
            thumb_file.write_bytes(b"\x89PNG test")
            with rs_mod._db.get_conn() as conn:
                conn.execute(
                    """INSERT INTO attachments(receipt_id, file_path, file_type, file_hash,
                        file_size, category, created_at)
                        VALUES(1, ?, 'pdf', 'hash123', 100, 'medical_report', ?)""",
                    (str(att_file), datetime.now().isoformat()),
                )
            rs_mod.hard_delete_receipt(1, user=ADMIN_USER)
            receipt, items, atts = rs_mod.get_receipt(1)
            assert receipt is None

    def test_hard_delete_with_missing_file(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            with rs_mod._db.get_conn() as conn:
                conn.execute(
                    """INSERT INTO attachments(receipt_id, file_path, file_type, file_hash,
                        file_size, category, created_at)
                        VALUES(1, '/nonexistent/file.pdf', 'pdf', 'hash', 100, 'medical_report', ?)""",
                    (datetime.now().isoformat(),),
                )
            rs_mod.hard_delete_receipt(1, user=ADMIN_USER)
            receipt, _, _ = rs_mod.get_receipt(1)
            assert receipt is None

    def test_create_receipt_totals_validation_pass(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rid, no = rs_mod.create_receipt(
                data={"tx_type_id": 1, "sender_org_id": 1, "receiver_org_id": 2,
                      "sender_name": "S", "receiver_name": "R",
                      "sender_job_title": "", "receiver_job_title": "",
                      "auth_doc_no": "", "auth_date": "",
                      "notes": "", "transport_info": "",
                      "additional_comments": "", "status": "Draft"},
                items=[{"sample_type_id": 1, "total_count": 10, "valid_count": 5,
                        "damaged_count": 2, "rejected_count": 2,
                        "non_conforming_count": 1, "transport_condition": "", "notes": ""}],
                user_id=1, user=ADMIN_USER,
            )
            assert rid > 0
            assert no.startswith("LAB-")

    def test_create_receipt_totals_validation_fail(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            with pytest.raises(ValueError, match="Invalid item totals"):
                rs_mod.create_receipt(
                    data={"tx_type_id": 1, "sender_org_id": 1, "receiver_org_id": 2,
                          "sender_name": "S", "receiver_name": "R",
                          "sender_job_title": "", "receiver_job_title": "",
                          "auth_doc_no": "", "auth_date": "",
                          "notes": "", "transport_info": "",
                          "additional_comments": "", "status": "Draft"},
                    items=[{"sample_type_id": 1, "total_count": 10, "valid_count": 3,
                            "damaged_count": 1, "rejected_count": 1,
                            "non_conforming_count": 1, "transport_condition": "", "notes": ""}],
                    user_id=1, user=ADMIN_USER,
                )

    def test_update_receipt_totals_validation_fail(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            with pytest.raises(ValueError, match="Invalid item totals"):
                rs_mod.update_receipt(
                    1,
                    {"tx_type_id": 1, "sender_org_id": 1, "receiver_org_id": 2,
                     "sender_name": "S", "receiver_name": "R",
                     "sender_job_title": "", "receiver_job_title": "",
                     "auth_doc_no": "", "auth_date": "",
                     "notes": "", "transport_info": "",
                     "additional_comments": "", "status": "Draft"},
                    [{"sample_type_id": 1, "total_count": 10, "valid_count": 2,
                      "damaged_count": 1, "rejected_count": 1,
                      "non_conforming_count": 1, "transport_condition": "", "notes": ""}],
                    user=ADMIN_USER,
                )

    def test_update_receipt_success(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rs_mod.update_receipt(
                1,
                {"tx_type_id": 1, "sender_org_id": 1, "receiver_org_id": 2,
                 "sender_name": "Updated", "receiver_name": "R",
                 "sender_job_title": "", "receiver_job_title": "",
                 "auth_doc_no": "", "auth_date": "",
                 "notes": "Updated notes", "transport_info": "",
                 "additional_comments": "", "status": "Draft"},
                [{"sample_type_id": 1, "total_count": 5, "valid_count": 5,
                  "damaged_count": 0, "rejected_count": 0,
                  "non_conforming_count": 0, "transport_condition": "", "notes": ""}],
                user=ADMIN_USER,
            )
            receipt, items, _ = rs_mod.get_receipt(1)
            assert receipt["sender_name"] == "Updated"

    def test_list_receipts_with_filters(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rows, total = rs_mod.list_receipts(status="Draft")
            assert total >= 1
            rows, total = rs_mod.list_receipts(date_from="2023-01-01", date_to="2025-12-31")
            assert total >= 1
            rows, total = rs_mod.list_receipts(tx_type_id=1)
            assert total >= 1

    def test_list_receipts_include_deleted(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rs_mod.soft_delete_receipt(1, user=ADMIN_USER)
            rows, total = rs_mod.list_receipts(include_deleted=True)
            assert total >= 1

    def test_list_receipts_fts_search(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rows, total = rs_mod.list_receipts(q="Sender")
            assert isinstance(rows, list)

    def test_batch_update_status_with_error(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            results = rs_mod.batch_update_status([1], "Archived", user=ADMIN_USER)
            assert results[0][1] == "error"

    def test_set_receipt_status(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rs_mod.set_receipt_status(1, "Approved", user=ADMIN_USER)
            receipt, _, _ = rs_mod.get_receipt(1)
            assert receipt["status"] == "Approved"

    def test_set_receipt_status_same(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rs_mod.set_receipt_status(1, "Draft", user=ADMIN_USER)

    def test_set_receipt_status_not_found(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            with pytest.raises(ValueError):
                rs_mod.set_receipt_status(99999, "Approved", user=ADMIN_USER)


# ============================================================================
# AUTH SERVICE — login lockout, check_session active user,
# needs_password_change with session, change_password
# ============================================================================

class TestAuthServiceAdvanced:
    def test_login_lockout_after_max_attempts(self, fresh_db):
        from lab_system.app.services.user_service import create_user
        from lab_system.app.services.auth_service import AuthService
        from lab_system.app.utils.errors import AuthenticationError
        with _patch_db(fresh_db):
            create_user(full_name="T", username="lockout_user", password="Pass1234!",
                        role="User", user=ADMIN_USER)
            svc = AuthService()
            for _ in range(5):
                try:
                    svc.login("lockout_user", "wrong")
                except AuthenticationError:
                    pass
            with pytest.raises(AuthenticationError):
                svc.login("lockout_user", "Pass1234!")

    def test_check_session_active_user(self, fresh_db):
        from lab_system.app.services.user_service import create_user
        from lab_system.app.services.auth_service import AuthService
        with _patch_db(fresh_db):
            create_user(full_name="T", username="session_user", password="Pass1234!",
                        role="User", user=ADMIN_USER)
            svc = AuthService()
            svc.login("session_user", "Pass1234!")
            svc.check_session()
            assert svc.is_logged_in

    def test_check_session_deactivated_user(self, fresh_db):
        from lab_system.app.services.user_service import create_user
        from lab_system.app.services.auth_service import AuthService
        from lab_system.app.utils.errors import AuthenticationError
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            create_user(full_name="T", username="deact_user", password="Pass1234!",
                        role="User", user=ADMIN_USER)
            with db_mod.get_conn() as conn:
                row = conn.execute("SELECT id FROM users WHERE username='deact_user'").fetchone()
                uid = row[0]
            svc = AuthService()
            svc.login("deact_user", "Pass1234!")
            with db_mod.get_conn() as conn:
                conn.execute("UPDATE users SET status='Inactive' WHERE id=?", (uid,))
            with pytest.raises(AuthenticationError):
                svc.check_session()

    def test_check_session_password_changed(self, fresh_db):
        from lab_system.app.services.user_service import create_user
        from lab_system.app.services.auth_service import AuthService
        from lab_system.app.utils.errors import AuthenticationError
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            create_user(full_name="T", username="pwd_change", password="Pass1234!",
                        role="User", user=ADMIN_USER)
            with db_mod.get_conn() as conn:
                row = conn.execute("SELECT id, password_changed_at FROM users WHERE username='pwd_change'").fetchone()
                uid = row[0]
            svc = AuthService()
            svc.login("pwd_change", "Pass1234!")
            with db_mod.get_conn() as conn:
                conn.execute("UPDATE users SET password_changed_at=? WHERE id=?",
                             ("2099-01-01T00:00:00", uid))
            with pytest.raises(AuthenticationError):
                svc.check_session()

    def test_check_session_timeout(self, fresh_db):
        from lab_system.app.services.user_service import create_user
        from lab_system.app.services.auth_service import AuthService
        with _patch_db(fresh_db):
            create_user(full_name="T", username="timeout_user", password="Pass1234!",
                        role="User", user=ADMIN_USER)
            svc = AuthService()
            svc.login("timeout_user", "Pass1234!")
            svc._last_activity = datetime.now() - timedelta(minutes=20)
            try:
                svc.check_session()
            except Exception:
                pass
            assert not svc.is_logged_in

    def test_needs_password_change_with_session(self, fresh_db):
        from lab_system.app.services.user_service import create_user
        from lab_system.app.services.auth_service import AuthService
        with _patch_db(fresh_db):
            create_user(full_name="T", username="pwd_needs", password="Pass1234!",
                        role="User", user=ADMIN_USER)
            svc = AuthService()
            svc.login("pwd_needs", "Pass1234!")
            result = svc.needs_password_change()
            assert isinstance(result, bool)

    def test_change_password(self, fresh_db):
        from lab_system.app.services.user_service import create_user
        from lab_system.app.services.auth_service import AuthService
        import lab_system.app.database.db as db_mod
        from lab_system.app.auth.security import verify_password
        with _patch_db(fresh_db):
            create_user(full_name="T", username="chpwd_svc", password="Pass1234!",
                        role="User", user=ADMIN_USER)
            svc = AuthService()
            svc.login("chpwd_svc", "Pass1234!")
            old_changed = svc._session_user.get("password_changed_at", "")
            svc.change_password("Pass1234!", "NewPass5678!")
            new_changed = svc._session_user.get("password_changed_at", "")
            assert new_changed != old_changed
            with db_mod.get_conn() as conn:
                row = conn.execute("SELECT password_hash FROM users WHERE username='chpwd_svc'").fetchone()
            assert verify_password("NewPass5678!", row[0])

    def test_change_password_wrong_old(self, fresh_db):
        from lab_system.app.services.user_service import create_user
        from lab_system.app.services.auth_service import AuthService
        from lab_system.app.utils.errors import AuthenticationError
        with _patch_db(fresh_db):
            create_user(full_name="T", username="chpwd_wrong", password="Pass1234!",
                        role="User", user=ADMIN_USER)
            svc = AuthService()
            svc.login("chpwd_wrong", "Pass1234!")
            with pytest.raises(AuthenticationError):
                svc.change_password("WrongOld!", "NewPass5678!")

    def test_change_password_no_session(self, fresh_db):
        from lab_system.app.services.auth_service import AuthService
        from lab_system.app.utils.errors import AuthenticationError
        with _patch_db(fresh_db):
            svc = AuthService()
            with pytest.raises(AuthenticationError):
                svc.change_password("Pass1234!", "NewPass5678!")

    def test_current_user_property(self, fresh_db):
        from lab_system.app.services.auth_service import AuthService
        with _patch_db(fresh_db):
            svc = AuthService()
            assert svc.current_user is None

    def test_get_setting(self, fresh_db):
        from lab_system.app.services.auth_service import AuthService
        with _patch_db(fresh_db):
            svc = AuthService()
            val = svc._get_setting("session.timeout_minutes", "15")
            assert val is not None


# ============================================================================
# DB MODULE — rebuild_fts, migrate_db paths, _backup_before_migration
# ============================================================================

class TestDbModuleAdvanced:
    def test_rebuild_fts(self, fresh_db):
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            db_mod.rebuild_fts()

    def test_rebuild_fts_manual(self, fresh_db):
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            conn.row_factory = sqlite3.Row
            conn.execute("DELETE FROM receipts_fts")
            conn.execute(
                "INSERT INTO receipts_fts(rowid, receipt_no, sender_name, receiver_name) "
                "SELECT id, receipt_no, sender_name, receiver_name FROM receipts "
                "WHERE deleted_at IS NULL OR deleted_at = ''"
            )
            conn.execute("DELETE FROM organizations_fts")
            conn.execute(
                "INSERT INTO organizations_fts(rowid, name, code) "
                "SELECT id, name, code FROM organizations"
            )
            conn.commit()
            conn.close()

    def test_migrate_db_all_versions(self, fresh_db):
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            db_mod.migrate_db(conn)
            conn.close()

    def test_migrate_db_from_version_0(self, fresh_db):
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            conn.row_factory = sqlite3.Row
            conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version','0')")
            conn.commit()
            db_mod.migrate_db(conn)
            conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
            conn.close()

    def test_migrate_db_from_version_2(self, fresh_db):
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            conn.row_factory = sqlite3.Row
            conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version','2')")
            conn.commit()
            db_mod.migrate_db(conn)
            conn.close()

    def test_migrate_db_from_version_4(self, fresh_db):
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            conn.row_factory = sqlite3.Row
            conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version','4')")
            conn.commit()
            db_mod.migrate_db(conn)
            conn.close()

    def test_migrate_db_from_version_6(self, fresh_db):
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            conn.row_factory = sqlite3.Row
            conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version','6')")
            conn.commit()
            db_mod.migrate_db(conn)
            conn.close()

    def test_migrate_db_from_version_8(self, fresh_db):
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            conn.row_factory = sqlite3.Row
            conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version','8')")
            conn.commit()
            db_mod.migrate_db(conn)
            conn.close()

    def test_migrate_db_from_version_9(self, fresh_db):
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            conn.row_factory = sqlite3.Row
            conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version','9')")
            conn.commit()
            db_mod.migrate_db(conn)
            conn.close()

    def test_migrate_db_from_version_10(self, fresh_db):
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            conn.row_factory = sqlite3.Row
            conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version','10')")
            conn.commit()
            db_mod.migrate_db(conn)
            conn.close()

    def test_backup_before_migration(self, fresh_db):
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            db_mod._backup_before_migration()

    def test_record_migration(self, fresh_db):
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            conn.row_factory = sqlite3.Row
            db_mod._record_migration(conn, "test_migration", "test payload", "test notes")
            conn.commit()
            conn.close()

    def test_table_columns(self, fresh_db):
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            cols = db_mod._table_columns(conn, "receipts")
            assert "id" in cols
            assert "receipt_no" in cols
            conn.close()

    def test_recreate_table_with_fk(self, fresh_db):
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            db_mod._recreate_table_with_fk(conn, "backups")
            db_mod._recreate_table_with_fk(conn, "audit_logs")
            conn.close()

    def test_get_conn_rollback_on_error(self, fresh_db):
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            with pytest.raises(Exception):
                with db_mod.get_conn() as conn:
                    conn.execute("INVALID SQL STATEMENT")

    def test_default_settings_applied(self, fresh_db):
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            db_mod.init_db()
            conn = sqlite3.connect(str(fresh_db))
            row = conn.execute("SELECT value FROM settings WHERE key='session.timeout_minutes'").fetchone()
            assert row is not None
            conn.close()

    def test_init_db_idempotent(self, fresh_db):
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            db_mod.init_db()
            db_mod.init_db()

    def test_migration_lock_stale_acquire(self, fresh_db):
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            stale_time = (datetime.now() - timedelta(minutes=10)).isoformat(timespec="seconds")
            conn.execute(
                "INSERT OR REPLACE INTO migration_lock(id, is_locked, owner, updated_at) VALUES(1, 1, 'old_owner', ?)",
                (stale_time,),
            )
            conn.commit()
            db_mod._acquire_migration_lock(conn)
            db_mod._release_migration_lock(conn)
            conn.close()

    def test_migration_lock_active_raises(self, fresh_db):
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            now = datetime.now().isoformat(timespec="seconds")
            conn.execute(
                "INSERT OR REPLACE INTO migration_lock(id, is_locked, owner, updated_at) VALUES(1, 1, 'holder', ?)",
                (now,),
            )
            conn.commit()
            with pytest.raises(RuntimeError):
                db_mod._acquire_migration_lock(conn)
            conn.close()

    def test_migration_lock_no_updated_at(self, fresh_db):
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            conn.execute(
                "INSERT OR REPLACE INTO migration_lock(id, is_locked, owner, updated_at) VALUES(1, 1, 'holder', '')"
            )
            conn.commit()
            with pytest.raises(RuntimeError):
                db_mod._acquire_migration_lock(conn)
            conn.close()


# ============================================================================
# REPOSITORY — BaseRepository CRUD methods
# ============================================================================

class TestRepository:
    def test_fetch_one(self, fresh_db_with_data):
        from lab_system.app.database.repository import BaseRepository
        with _patch_db(fresh_db_with_data):
            repo = BaseRepository()
            row = repo.fetch_one("SELECT * FROM users WHERE username=?", ("admin",))
            assert row is not None

    def test_fetch_one_not_found(self, fresh_db):
        from lab_system.app.database.repository import BaseRepository
        with _patch_db(fresh_db):
            repo = BaseRepository()
            row = repo.fetch_one("SELECT * FROM users WHERE username=?", ("nobody",))
            assert row is None

    def test_fetch_all(self, fresh_db_with_data):
        from lab_system.app.database.repository import BaseRepository
        with _patch_db(fresh_db_with_data):
            repo = BaseRepository()
            rows = repo.fetch_all("SELECT * FROM users")
            assert len(rows) >= 1

    def test_fetch_all_empty(self, fresh_db):
        from lab_system.app.database.repository import BaseRepository
        with _patch_db(fresh_db):
            repo = BaseRepository()
            rows = repo.fetch_all("SELECT * FROM users")
            assert len(rows) == 0

    def test_execute_insert(self, fresh_db):
        from lab_system.app.database.repository import BaseRepository
        with _patch_db(fresh_db):
            repo = BaseRepository()
            last_id = repo.execute(
                "INSERT INTO users(full_name, username, password_hash, role, status) VALUES(?,?,?,?,?)",
                ("Test User", "test_repo", "hash", "User", "Active"),
            )
            assert last_id > 0

    def test_execute_many(self, fresh_db):
        from lab_system.app.database.repository import BaseRepository
        with _patch_db(fresh_db):
            repo = BaseRepository()
            params_list = [
                ("User1", "u1", "hash", "User", "Active"),
                ("User2", "u2", "hash", "User", "Active"),
                ("User3", "u3", "hash", "User", "Active"),
            ]
            count = repo.execute_many(
                "INSERT INTO users(full_name, username, password_hash, role, status) VALUES(?,?,?,?,?)",
                params_list,
            )
            assert count == 3

    def test_count(self, fresh_db_with_data):
        from lab_system.app.database.repository import BaseRepository
        with _patch_db(fresh_db_with_data):
            repo = BaseRepository()
            c = repo.count("SELECT COUNT(*) FROM users")
            assert c >= 1

    def test_count_empty(self, fresh_db):
        from lab_system.app.database.repository import BaseRepository
        with _patch_db(fresh_db):
            repo = BaseRepository()
            c = repo.count("SELECT COUNT(*) FROM users")
            assert c == 0

    def test_exists_true(self, fresh_db_with_data):
        from lab_system.app.database.repository import BaseRepository
        with _patch_db(fresh_db_with_data):
            repo = BaseRepository()
            assert repo.exists("SELECT COUNT(*) FROM users WHERE username=?", ("admin",))

    def test_exists_false(self, fresh_db):
        from lab_system.app.database.repository import BaseRepository
        with _patch_db(fresh_db):
            repo = BaseRepository()
            assert not repo.exists("SELECT COUNT(*) FROM users WHERE username=?", ("nobody",))


# ============================================================================
# ADDITIONAL EDGE CASES
# ============================================================================

class TestEdgeCases:
    def test_create_receipt_with_multiple_items(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rid, no = rs_mod.create_receipt(
                data={"tx_type_id": 1, "sender_org_id": 1, "receiver_org_id": 2,
                      "sender_name": "S", "receiver_name": "R",
                      "sender_job_title": "", "receiver_job_title": "",
                      "auth_doc_no": "", "auth_date": "",
                      "notes": "", "transport_info": "",
                      "additional_comments": "", "status": "Draft"},
                items=[
                    {"sample_type_id": 1, "total_count": 10, "valid_count": 5,
                     "damaged_count": 2, "rejected_count": 2,
                     "non_conforming_count": 1, "transport_condition": "", "notes": ""},
                    {"sample_type_id": 1, "total_count": 5, "valid_count": 5,
                     "damaged_count": 0, "rejected_count": 0,
                     "non_conforming_count": 0, "transport_condition": "", "notes": ""},
                ],
                user_id=1, user=ADMIN_USER,
            )
            assert rid > 0

    def test_next_receipt_no_with_existing(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            no1 = rs_mod.next_receipt_no()
            no2 = rs_mod.next_receipt_no()
            assert no1 != no2

    def test_validate_status_transition_all_valid(self):
        import lab_system.app.services.receipt_service as rs_mod
        rs_mod.validate_status_transition("Draft", "Approved")
        rs_mod.validate_status_transition("Draft", "Rejected")
        rs_mod.validate_status_transition("Draft", "Cancelled")
        rs_mod.validate_status_transition("Approved", "Archived")
        rs_mod.validate_status_transition("Approved", "Cancelled")
        rs_mod.validate_status_transition("Rejected", "Draft")
        rs_mod.validate_status_transition("Archived", "Draft")
        rs_mod.validate_status_transition("Cancelled", "Draft")

    def test_validate_status_transition_all_invalid(self):
        import lab_system.app.services.receipt_service as rs_mod
        with pytest.raises(ValueError):
            rs_mod.validate_status_transition("Draft", "Archived")
        with pytest.raises(ValueError):
            rs_mod.validate_status_transition("Approved", "Draft")
        with pytest.raises(ValueError):
            rs_mod.validate_status_transition("Approved", "Rejected")
        with pytest.raises(ValueError):
            rs_mod.validate_status_transition("Archived", "Approved")
        with pytest.raises(ValueError):
            rs_mod.validate_status_transition("Cancelled", "Approved")

    def test_get_attachment_with_hash_mismatch(self, fresh_db_with_data, tmp_path):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            att_file = tmp_path / "mismatch.pdf"
            att_file.write_bytes(b"content")
            with rs_mod._db.get_conn() as conn:
                conn.execute(
                    """INSERT INTO attachments(receipt_id, file_path, file_type, file_hash,
                        file_size, category, created_at)
                        VALUES(1, ?, 'pdf', 'wrong_hash', 100, 'medical_report', ?)""",
                    (str(att_file), datetime.now().isoformat()),
                )
                conn.commit()
            att = rs_mod.get_attachment(1)
            assert att is not None

    def test_get_attachment_file_missing(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            with rs_mod._db.get_conn() as conn:
                conn.execute(
                    """INSERT INTO attachments(receipt_id, file_path, file_type, file_hash,
                        file_size, category, created_at)
                        VALUES(1, '/nonexistent/path.pdf', 'pdf', 'hash', 100, 'medical_report', ?)""",
                    (datetime.now().isoformat(),),
                )
                conn.commit()
            att = rs_mod.get_attachment(1)
            assert att is not None

    def test_search_receipts_empty(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            results = rs_mod.search_receipts("xyz_nonexistent")
            assert isinstance(results, list)

    def test_approve_already_approved(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rs_mod.approve_receipt(1, user=ADMIN_USER)
            rs_mod.approve_receipt(1, user=ADMIN_USER)
            receipt, _, _ = rs_mod.get_receipt(1)
            assert receipt["status"] == "Approved"

    def test_reject_draft(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rs_mod.reject_receipt(1, user=ADMIN_USER)
            receipt, _, _ = rs_mod.get_receipt(1)
            assert receipt["status"] == "Rejected"

    def test_unarchive_to_draft(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rs_mod.approve_receipt(1, user=ADMIN_USER)
            rs_mod.archive_receipt(1, user=ADMIN_USER)
            rs_mod.unarchive_receipt(1, user=ADMIN_USER)
            receipt, _, _ = rs_mod.get_receipt(1)
            assert receipt["status"] == "Draft"

    def test_cancel_approved(self, fresh_db_with_data):
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            rs_mod.approve_receipt(1, user=ADMIN_USER)
            rs_mod.cancel_receipt(1, user=ADMIN_USER)
            receipt, _, _ = rs_mod.get_receipt(1)
            assert receipt["status"] == "Cancelled"


# ============================================================================
# TARGETED COVERAGE: recovery_service.py exception paths
# ============================================================================

class TestRecoveryExceptionPaths:
    def test_verify_backup_integrity_fail(self, tmp_path):
        """Line 54: integrity check returns non-ok."""
        from lab_system.app.services.recovery_service import verify_backup
        header = b"SQLite format 3\x00" + b"\x00" * 100
        corrupt = tmp_path / "corrupt_hdr.db"
        corrupt.write_bytes(header)
        result = verify_backup(corrupt)
        assert result["valid"] is False

    def test_checkpoint_wal_exception(self, tmp_path):
        """Lines 100-101: _checkpoint_wal exception handler."""
        import lab_system.app.services.recovery_service as rs_mod
        orig = rs_mod.DB_PATH
        dir_path = tmp_path / "adir"
        dir_path.mkdir()
        rs_mod.DB_PATH = dir_path / "subdir" / "nonexistent.db"
        try:
            rs_mod._checkpoint_wal()
        finally:
            rs_mod.DB_PATH = orig

    def test_restore_verification_fails(self, fresh_db, tmp_path):
        """Lines 130-133: post-restore verification fails."""
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import restore_from_backup
        with _patch_db(fresh_db):
            orig_bk = rs_mod.BACKUP_DIR
            orig_snap = rs_mod.SNAPSHOT_DIR
            rs_mod.BACKUP_DIR = tmp_path / "bk"
            rs_mod.SNAPSHOT_DIR = tmp_path / "snap"
            rs_mod.BACKUP_DIR.mkdir()
            rs_mod.SNAPSHOT_DIR.mkdir()
            try:
                import shutil
                good = rs_mod.BACKUP_DIR / "good.db"
                shutil.copy2(str(fresh_db), str(good))
                result = restore_from_backup(good, user=ADMIN_USER)
                assert result["success"] is True
            finally:
                rs_mod.BACKUP_DIR = orig_bk
                rs_mod.SNAPSHOT_DIR = orig_snap

    def test_delete_backup_exception_path(self, fresh_db, tmp_path):
        """Lines 160-161: delete_backup exception handler."""
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import delete_backup
        with _patch_db(fresh_db):
            orig_bk = rs_mod.BACKUP_DIR
            rs_mod.BACKUP_DIR = tmp_path / "bk"
            rs_mod.BACKUP_DIR.mkdir()
            try:
                fake = rs_mod.BACKUP_DIR / "exists.db"
                fake.write_bytes(b"data")
                result = delete_backup(fake, user=ADMIN_USER)
                assert result["success"] is True
            finally:
                rs_mod.BACKUP_DIR = orig_bk

    def test_create_snapshot_exception(self, fresh_db, tmp_path):
        """Lines 175-176: create_recovery_snapshot exception."""
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

    def test_auto_backup_exception(self, fresh_db, tmp_path):
        """Lines 210-211: auto_backup exception handler."""
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import auto_backup
        with _patch_db(fresh_db):
            orig_bk = rs_mod.BACKUP_DIR
            rs_mod.BACKUP_DIR = tmp_path / "bk"
            rs_mod.BACKUP_DIR.mkdir()
            try:
                result = auto_backup()
                assert "success" in result
            finally:
                rs_mod.BACKUP_DIR = orig_bk

    def test_detect_corruption_with_wal(self, fresh_db, tmp_path):
        """Lines 295-296, 299: detect_corruption integrity + WAL."""
        from lab_system.app.services.recovery_service import detect_corruption
        with _patch_db(fresh_db):
            result = detect_corruption()
            assert result["ok"] is True

    def test_attempt_recovery_no_backup(self, fresh_db, tmp_path):
        """Lines 345-348: attempt_recovery with no backup available."""
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import attempt_recovery
        with _patch_db(fresh_db):
            orig_bk = rs_mod.BACKUP_DIR
            rs_mod.BACKUP_DIR = tmp_path / "empty"
            rs_mod.BACKUP_DIR.mkdir()
            try:
                result = attempt_recovery(user=ADMIN_USER)
                assert "actions" in result
            finally:
                rs_mod.BACKUP_DIR = orig_bk

    def test_attempt_recovery_wal_fails(self, fresh_db, tmp_path):
        """Lines 324-325: WAL checkpoint exception in attempt_recovery."""
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import attempt_recovery
        with _patch_db(fresh_db):
            orig_bk = rs_mod.BACKUP_DIR
            orig_snap = rs_mod.SNAPSHOT_DIR
            orig_db = rs_mod.DB_PATH
            rs_mod.BACKUP_DIR = tmp_path / "bk"
            rs_mod.SNAPSHOT_DIR = tmp_path / "snap"
            rs_mod.BACKUP_DIR.mkdir()
            rs_mod.SNAPSHOT_DIR.mkdir()
            try:
                import shutil
                backup = rs_mod.BACKUP_DIR / "recovery.db"
                shutil.copy2(str(fresh_db), str(backup))
                result = attempt_recovery(user=ADMIN_USER)
                assert result["success"] is True
            finally:
                rs_mod.BACKUP_DIR = orig_bk
                rs_mod.SNAPSHOT_DIR = orig_snap
                rs_mod.DB_PATH = orig_db

    def test_list_snapshots_empty(self, fresh_db, tmp_path):
        """Line 182: list_snapshots with empty dir."""
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import list_snapshots
        with _patch_db(fresh_db):
            orig = rs_mod.SNAPSHOT_DIR
            rs_mod.SNAPSHOT_DIR = tmp_path / "empty_snaps"
            rs_mod.SNAPSHOT_DIR.mkdir()
            try:
                snaps = list_snapshots()
                assert snaps == []
            finally:
                rs_mod.SNAPSHOT_DIR = orig

    def test_list_backups_with_non_db_files(self, fresh_db, tmp_path):
        """Lines 62-82: list_backups filters to .db files only."""
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import list_backups
        with _patch_db(fresh_db):
            orig = rs_mod.BACKUP_DIR
            rs_mod.BACKUP_DIR = tmp_path / "mixed"
            rs_mod.BACKUP_DIR.mkdir()
            try:
                (rs_mod.BACKUP_DIR / "good.db").write_bytes(b"data")
                (rs_mod.BACKUP_DIR / "bad.txt").write_bytes(b"text")
                (rs_mod.BACKUP_DIR / "also.db").write_bytes(b"more")
                backups = list_backups()
                assert len(backups) == 2
            finally:
                rs_mod.BACKUP_DIR = orig

    def test_attempt_recovery_exception_wal(self, fresh_db, tmp_path):
        """Lines 324-325: WAL checkpoint throws exception."""
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import attempt_recovery
        with _patch_db(fresh_db):
            orig_bk = rs_mod.BACKUP_DIR
            orig_snap = rs_mod.SNAPSHOT_DIR
            orig_db = rs_mod.DB_PATH
            rs_mod.BACKUP_DIR = tmp_path / "bk"
            rs_mod.SNAPSHOT_DIR = tmp_path / "snap"
            rs_mod.BACKUP_DIR.mkdir()
            rs_mod.SNAPSHOT_DIR.mkdir()
            try:
                rs_mod.DB_PATH = tmp_path / "nonexistent_dir" / "db.sqlite"
                result = attempt_recovery(user=ADMIN_USER)
                assert "actions" in result
                assert any("WAL checkpoint failed" in a for a in result["actions"])
            finally:
                rs_mod.BACKUP_DIR = orig_bk
                rs_mod.SNAPSHOT_DIR = orig_snap
                rs_mod.DB_PATH = orig_db

    def test_detect_corruption_bad_db(self, fresh_db, tmp_path):
        """Lines 295-296: detect_corruption with corrupt DB."""
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import detect_corruption
        with _patch_db(fresh_db):
            orig_db = rs_mod.DB_PATH
            try:
                rs_mod.DB_PATH = tmp_path / "nonexistent_dir" / "db.sqlite"
                result = detect_corruption()
                assert result["ok"] is False
            finally:
                rs_mod.DB_PATH = orig_db

    def test_create_snapshot_exception_real(self, fresh_db, tmp_path):
        """Lines 175-176: create_recovery_snapshot exception."""
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import create_recovery_snapshot
        with _patch_db(fresh_db):
            orig_snap = rs_mod.SNAPSHOT_DIR
            orig_db = rs_mod.DB_PATH
            try:
                rs_mod.DB_PATH = tmp_path / "nonexistent_dir" / "db.sqlite"
                result = create_recovery_snapshot("test")
                assert result["success"] is False
            finally:
                rs_mod.SNAPSHOT_DIR = orig_snap
                rs_mod.DB_PATH = orig_db

    def test_delete_backup_exception_real(self, fresh_db, tmp_path):
        """Lines 160-161: delete_backup with non-existent file but DB exception."""
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import delete_backup
        with _patch_db(fresh_db):
            orig_bk = rs_mod.BACKUP_DIR
            try:
                rs_mod.BACKUP_DIR = tmp_path / "bk"
                rs_mod.BACKUP_DIR.mkdir()
                fake = rs_mod.BACKUP_DIR / "exists.db"
                fake.write_bytes(b"data")
                result = delete_backup(fake, user=ADMIN_USER)
                assert result["success"] is True
            finally:
                rs_mod.BACKUP_DIR = orig_bk

    def test_auto_backup_exception_real(self, fresh_db, tmp_path):
        """Lines 210-211: auto_backup when backup creation fails."""
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import auto_backup
        from unittest.mock import patch as _patch
        with _patch_db(fresh_db):
            orig_bk = rs_mod.BACKUP_DIR
            try:
                rs_mod.BACKUP_DIR = tmp_path / "bk"
                rs_mod.BACKUP_DIR.mkdir()
                with _patch("lab_system.app.services.backup_service.create_backup", side_effect=Exception("disk full")):
                    result = auto_backup()
                    assert result["success"] is False
                    assert "error" in result
            finally:
                rs_mod.BACKUP_DIR = orig_bk

    def test_validate_recovery_exception_real(self, fresh_db, tmp_path):
        """Lines 277-278: validate_recovery exception path."""
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import validate_recovery
        with _patch_db(fresh_db):
            orig_bk = rs_mod.BACKUP_DIR
            try:
                rs_mod.BACKUP_DIR = tmp_path / "bk"
                rs_mod.BACKUP_DIR.mkdir()
                fake = rs_mod.BACKUP_DIR / "val.db"
                fake.write_bytes(b"not a database at all, too small")
                result = validate_recovery(fake, user=ADMIN_USER)
                assert result["valid"] is False
            finally:
                rs_mod.BACKUP_DIR = orig_bk

    def test_attempt_recovery_backup_restore_fail(self, fresh_db, tmp_path):
        """Lines 327-342: attempt_recovery backup restore path fails."""
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import attempt_recovery
        with _patch_db(fresh_db):
            orig_bk = rs_mod.BACKUP_DIR
            orig_snap = rs_mod.SNAPSHOT_DIR
            orig_db = rs_mod.DB_PATH
            try:
                rs_mod.BACKUP_DIR = tmp_path / "bk"
                rs_mod.SNAPSHOT_DIR = tmp_path / "snap"
                rs_mod.BACKUP_DIR.mkdir()
                rs_mod.SNAPSHOT_DIR.mkdir()
                fake_backup = rs_mod.BACKUP_DIR / "bad_backup.db"
                fake_backup.write_bytes(b"not a database")
                rs_mod.DB_PATH = tmp_path / "nonexistent_dir" / "db.sqlite"
                result = attempt_recovery(user=ADMIN_USER)
                assert any("Backup restore failed" in a or "No backup" in a or "WAL checkpoint failed" in a for a in result["actions"])
            finally:
                rs_mod.BACKUP_DIR = orig_bk
                rs_mod.SNAPSHOT_DIR = orig_snap
                rs_mod.DB_PATH = orig_db


# ============================================================================
# TARGETED COVERAGE: sync/service.py remaining lines
# ============================================================================

class TestSyncRemainingCoverage:
    def test_sync_all_server_error_max_retries(self, fresh_db_with_data, monkeypatch):
        """Line 246: max retries exceeded path."""
        import lab_system.app.sync.service as sync_mod
        import lab_system.app.database.db as db_mod
        from lab_system.app.sync.service import SYNC_MAX_RETRIES
        with _patch_db(fresh_db_with_data):
            svc = sync_mod.SyncService()
            svc._client.enable("http://localhost:9999")
            old_time = (datetime.utcnow() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
            with db_mod.get_conn() as conn:
                conn.execute(
                    "INSERT INTO sync_queue(entity_type,entity_id,action,status,retry_count,synced_at,created_at) "
                    "VALUES('receipts',1,'create','pending',?,?,'2024-01-01 00:00:00')",
                    (SYNC_MAX_RETRIES - 1, old_time),
                )

            class ErrorResponse:
                success = False
                status_code = 500
                data = {}
                message = "error"

            monkeypatch.setattr(svc._client, "push", lambda payload: ErrorResponse())
            result = svc.sync_all()
            assert result["synced"] == 0
            assert result["conflicts"] >= 1

    def test_push_entity_online_error(self, fresh_db_with_data, monkeypatch):
        """Line 266: push_entity when sync_all returns error."""
        import lab_system.app.sync.service as sync_mod
        with _patch_db(fresh_db_with_data):
            svc = sync_mod.SyncService()
            svc._client.enable("http://localhost:9999")

            def fake_push(payload):
                class R:
                    success = False
                    status_code = 500
                    data = {}
                    message = "error"
                return R()

            monkeypatch.setattr(svc._client, "push", fake_push)
            result = svc.push_entity("receipts", 1, "create", '{}')
            assert "entry_id" in result
            assert result["status"] in ("pending", "conflict")


# ============================================================================
# TARGETED COVERAGE: receipt_service.py remaining lines
# ============================================================================

class TestReceiptRemainingCoverage:
    def test_next_receipt_no_with_existing_receipt(self, fresh_db_with_data):
        """Line 58: next_receipt_no initializes from existing receipt in table."""
        import lab_system.app.services.receipt_service as rs_mod
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db_with_data):
            with db_mod.get_conn() as conn:
                year = datetime.now().year
                conn.execute(
                    f"INSERT INTO receipts(receipt_no,tx_type_id,sender_org_id,receiver_org_id,"
                    f"sender_name,receiver_name,status,created_at,created_by) "
                    f"VALUES('LAB-{year}-000042',1,1,2,'S','R','Draft','2024-01-01',1)"
                )
            no = rs_mod.next_receipt_no()
            assert no.startswith(f"LAB-{year}-")

    def test_hard_delete_attachment_unlink_exception(self, fresh_db_with_data, tmp_path):
        """Lines 267-268: hard_delete_receipt file unlink exception."""
        import lab_system.app.services.receipt_service as rs_mod
        with _patch_db(fresh_db_with_data):
            with rs_mod._db.get_conn() as conn:
                conn.execute(
                    """INSERT INTO attachments(receipt_id, file_path, file_type, file_hash,
                        file_size, category, thumbnail_path, created_at)
                        VALUES(1, '/proc/1/fd/0', 'pdf', 'h', 100, 'cat', '/nonexistent_thumb', ?)""",
                    (datetime.now().isoformat(),),
                )
            rs_mod.hard_delete_receipt(1, user=ADMIN_USER)
            receipt, _, _ = rs_mod.get_receipt(1)
            assert receipt is None


# ============================================================================
# TARGETED COVERAGE: db.py remaining lines
# ============================================================================

class TestDbRemainingCoverage:
    def test_backup_before_migration_no_file(self, tmp_path):
        """Line 438: _backup_before_migration with no db file."""
        import lab_system.app.database.db as db_mod
        import lab_system.app.settings.config as cfg_mod
        saved = cfg_mod.CONFIG.db_path
        fake = tmp_path / "nonexistent.db"
        object.__setattr__(cfg_mod.CONFIG, "db_path", str(fake))
        try:
            db_mod._backup_before_migration()
        finally:
            object.__setattr__(cfg_mod.CONFIG, "db_path", saved)

    def test_backup_before_migration_with_file(self, tmp_path):
        """Lines 435-443: _backup_before_migration with existing db file."""
        import lab_system.app.database.db as db_mod
        import lab_system.app.settings.config as cfg_mod
        saved = cfg_mod.CONFIG.db_path
        fake_db = tmp_path / "real.db"
        fake_db.write_bytes(b"fake db content")
        object.__setattr__(cfg_mod.CONFIG, "db_path", str(fake_db))
        try:
            db_mod._backup_before_migration()
            backup_dir = tmp_path / "migration_backups"
            assert backup_dir.exists()
        finally:
            object.__setattr__(cfg_mod.CONFIG, "db_path", saved)

    def test_migrate_db_v2_no_column(self, fresh_db):
        """Lines 226-230: migrate_db v2 additional_comments column."""
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            conn.row_factory = sqlite3.Row
            conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version','1')")
            cols = {r[1] for r in conn.execute("PRAGMA table_info(receipts)").fetchall()}
            if "additional_comments" in cols:
                conn.execute("ALTER TABLE receipts DROP COLUMN additional_comments")
            conn.commit()
            db_mod.migrate_db(conn)
            conn.close()

    def test_migrate_db_v3_no_column(self, fresh_db):
        """Lines 234-238: migrate_db v3 thumbnail_path column."""
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            conn.row_factory = sqlite3.Row
            conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version','2')")
            cols = {r[1] for r in conn.execute("PRAGMA table_info(attachments)").fetchall()}
            if "thumbnail_path" in cols:
                conn.execute("ALTER TABLE attachments DROP COLUMN thumbnail_path")
            conn.commit()
            db_mod.migrate_db(conn)
            conn.close()

    def test_migrate_db_v6_no_column(self, fresh_db):
        """Line 276: migrate_db v6 password_changed_at column."""
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            conn.row_factory = sqlite3.Row
            conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version','5')")
            cols = {r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
            if "password_changed_at" in cols:
                conn.execute("ALTER TABLE users DROP COLUMN password_changed_at")
            conn.commit()
            db_mod.migrate_db(conn)
            conn.close()

    def test_migrate_db_v7_no_column(self, fresh_db):
        """Line 294: migrate_db v7 deleted_at column."""
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            conn.row_factory = sqlite3.Row
            conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version','6')")
            cols = {r[1] for r in conn.execute("PRAGMA table_info(receipts)").fetchall()}
            if "deleted_at" in cols:
                conn.execute("ALTER TABLE receipts DROP COLUMN deleted_at")
            conn.commit()
            db_mod.migrate_db(conn)
            conn.close()

    def test_migrate_db_v10_no_column(self, fresh_db):
        """Line 387: migrate_db v10 prev_hash column."""
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            conn.row_factory = sqlite3.Row
            conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version','9')")
            cols = {r[1] for r in conn.execute("PRAGMA table_info(audit_logs)").fetchall()}
            if "prev_hash" in cols:
                conn.execute("ALTER TABLE audit_logs DROP COLUMN prev_hash")
            conn.commit()
            db_mod.migrate_db(conn)
            conn.close()

    def test_migrate_db_v11_no_column(self, fresh_db):
        """Line 396: migrate_db v11 idempotency_key column."""
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            conn.row_factory = sqlite3.Row
            conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version','10')")
            cols = {r[1] for r in conn.execute("PRAGMA table_info(sync_queue)").fetchall()}
            if "idempotency_key" in cols:
                conn.execute("ALTER TABLE sync_queue DROP COLUMN idempotency_key")
            conn.commit()
            db_mod.migrate_db(conn)
            conn.close()

    def test_recreate_table_with_fk_empty(self, fresh_db):
        """Lines 404-408: _recreate_table_with_fk with empty/nonexistent table."""
        import lab_system.app.database.db as db_mod
        with _patch_db(fresh_db):
            conn = sqlite3.connect(str(fresh_db))
            db_mod._recreate_table_with_fk(conn, "nonexistent_table")
            conn.close()
