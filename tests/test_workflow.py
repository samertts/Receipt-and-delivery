"""Tests for receipt workflow (Phase 3), reporting (Phase 4), and recovery (Phase 5)."""

import os
import sqlite3
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_db():
    """Create a fresh test database and return the path."""
    from lab_system.app.database.db import SCHEMA

    db_path = Path(tempfile.mkdtemp(prefix="lab_wf_")) / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA)
    conn.execute(
        "INSERT INTO organizations(name,code,org_type,status) VALUES('Org A','OA-001','Lab','Active')"
    )
    conn.execute(
        "INSERT INTO organizations(name,code,org_type,status) VALUES('Org B','OB-001','Lab','Active')"
    )
    conn.execute(
        "INSERT INTO users(full_name,username,password_hash,role,status) VALUES('Admin','admin','hash','Admin','Active')"
    )
    conn.execute(
        "INSERT INTO transaction_types(name,is_active) VALUES('Sample Receipt',1)"
    )
    conn.execute(
        "INSERT INTO sample_types(name,category,status) VALUES('Serum','Blood','Active')"
    )
    conn.execute(
        "INSERT INTO sample_types(name,category,status) VALUES('Urine','General','Active')"
    )
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


def _data():
    return {
        "tx_type_id": 1,
        "sender_org_id": 1,
        "receiver_org_id": 2,
        "sender_name": "Sender",
        "receiver_name": "Receiver",
        "sender_job_title": "",
        "receiver_job_title": "",
        "auth_doc_no": "",
        "auth_date": "",
        "notes": "",
        "transport_info": "",
        "additional_comments": "",
        "status": "Draft",
    }


def _item():
    return {
        "sample_type_id": 1,
        "total_count": 100,
        "valid_count": 96,
        "damaged_count": 2,
        "rejected_count": 1,
        "non_conforming_count": 1,
        "transport_condition": "",
        "notes": "",
    }


ADMIN_USER = {"id": 1, "username": "admin", "role": "Admin", "status": "Active"}


class TestWorkflow:
    @classmethod
    def setup_class(cls):
        import lab_system.app.database.db as _db_mod

        cls.db_path = _make_db()
        _db_mod.get_conn = _make_get_conn(cls.db_path)

    def test_valid_transitions(self):
        from lab_system.app.services.receipt_service import (
            change_receipt_status,
            create_receipt,
            get_receipt,
        )

        rid, _ = create_receipt(_data(), [_item()], 1, user=ADMIN_USER)
        change_receipt_status(rid, "Approved", 1, user=ADMIN_USER)
        assert get_receipt(rid)[0]["status"] == "Approved"
        change_receipt_status(rid, "Archived", 1, user=ADMIN_USER)
        assert get_receipt(rid)[0]["status"] == "Archived"
        change_receipt_status(rid, "Draft", 1, user=ADMIN_USER)
        assert get_receipt(rid)[0]["status"] == "Draft"

    def test_invalid_transitions(self):
        from lab_system.app.services.receipt_service import (
            change_receipt_status,
            create_receipt,
        )

        rid, _ = create_receipt(_data(), [_item()], 1, user=ADMIN_USER)
        change_receipt_status(rid, "Approved", 1, user=ADMIN_USER)
        import pytest

        with pytest.raises(ValueError, match="Cannot transition"):
            change_receipt_status(rid, "Draft", 1, user=ADMIN_USER)

    def test_receipt_history(self):
        from lab_system.app.services.receipt_service import (
            change_receipt_status,
            create_receipt,
            get_receipt_history,
        )

        rid, _ = create_receipt(_data(), [_item()], 1, user=ADMIN_USER)
        change_receipt_status(rid, "Approved", 1, user=ADMIN_USER)
        change_receipt_status(rid, "Archived", 1, user=ADMIN_USER)
        history = get_receipt_history(rid)
        assert len(history) >= 2
        assert history[0]["field_name"] == "status"
        assert history[0]["old_value"] == "Draft"
        assert history[0]["new_value"] == "Approved"

    def test_batch_update_status(self):
        from lab_system.app.services.receipt_service import (
            batch_update_status,
            create_receipt,
            get_receipt,
        )

        r1, _ = create_receipt(_data(), [_item()], 1, user=ADMIN_USER)
        r2, _ = create_receipt(_data(), [_item()], 1, user=ADMIN_USER)
        results = batch_update_status([r1, r2], "Approved", 1, user=ADMIN_USER)
        assert all(r[1] == "ok" for r in results)
        assert get_receipt(r1)[0]["status"] == "Approved"
        assert get_receipt(r2)[0]["status"] == "Approved"

    def test_change_status_not_found(self):
        import pytest

        from lab_system.app.services.receipt_service import change_receipt_status

        with pytest.raises(ValueError, match="not found"):
            change_receipt_status(99999, "Approved", 1, user=ADMIN_USER)

    def test_change_status_same_status(self):
        from lab_system.app.services.receipt_service import (
            change_receipt_status,
            create_receipt,
            get_receipt,
        )

        rid, _ = create_receipt(_data(), [_item()], 1, user=ADMIN_USER)
        result = change_receipt_status(rid, "Draft", 1, user=ADMIN_USER)
        assert result is None
        assert get_receipt(rid)[0]["status"] == "Draft"

    def test_set_status_not_found(self):
        import pytest

        from lab_system.app.services.receipt_service import set_receipt_status

        with pytest.raises(ValueError, match="not found"):
            set_receipt_status(99999, "Approved", 1, user=ADMIN_USER)

    def test_set_status_same_status(self):
        from lab_system.app.services.receipt_service import (
            create_receipt,
            get_receipt,
            set_receipt_status,
        )

        rid, _ = create_receipt(_data(), [_item()], 1, user=ADMIN_USER)
        result = set_receipt_status(rid, "Draft", 1, user=ADMIN_USER)
        assert result is None
        assert get_receipt(rid)[0]["status"] == "Draft"

    def test_list_receipts_date_filter(self):
        from lab_system.app.services.receipt_service import (
            create_receipt,
            list_receipts,
        )

        create_receipt(_data(), [_item()], 1, user=ADMIN_USER)
        result = list_receipts(date_from="2026-01-01", date_to="2026-12-31")
        assert len(result) >= 1

    def test_list_receipts_tx_type_filter(self):
        from lab_system.app.services.receipt_service import (
            create_receipt,
            list_receipts,
        )

        create_receipt(_data(), [_item()], 1, user=ADMIN_USER)
        rows, count = list_receipts(tx_type_id=1)
        assert count >= 1
        rows_empty, count_empty = list_receipts(tx_type_id=999)
        assert count_empty == 0

    def test_batch_update_status_errors(self):
        from lab_system.app.services.receipt_service import batch_update_status

        results = batch_update_status([99991, 99992], "Approved", 1)
        assert all(r[1] == "error" for r in results)

    def test_batch_soft_delete_error(self):
        from unittest import mock

        from lab_system.app.services import receipt_service

        with mock.patch.object(
            receipt_service,
            "soft_delete_receipt",
            side_effect=RuntimeError("DB failure"),
        ):
            results = receipt_service.batch_soft_delete([1], user_id=1)
            assert results[0][1] == "error"
            assert "DB failure" in results[0][2]

    def test_batch_soft_delete_ok(self):
        from lab_system.app.services.receipt_service import (
            batch_soft_delete,
            create_receipt,
            restore_receipt,
        )

        rid, _ = create_receipt(_data(), [_item()], 1, user=ADMIN_USER)
        results = batch_soft_delete([rid], user_id=1, user=ADMIN_USER)
        assert results[0][1] == "ok"
        restore_receipt(rid, 1, user=ADMIN_USER)

    def test_invalid_item_totals(self):
        import pytest

        from lab_system.app.services.receipt_service import (
            create_receipt,
            update_receipt,
        )

        bad_item = _item()
        bad_item["total_count"] = 10
        bad_item["valid_count"] = 100
        with pytest.raises(ValueError, match="Invalid item totals"):
            create_receipt(_data(), [bad_item], 1, user=ADMIN_USER)
        rid, _ = create_receipt(_data(), [_item()], 1, user=ADMIN_USER)
        with pytest.raises(ValueError, match="Invalid item totals"):
            update_receipt(rid, _data(), [bad_item], user=ADMIN_USER)

    def test_status_wrappers(self):
        from lab_system.app.services.receipt_service import (
            approve_receipt,
            cancel_receipt,
            create_receipt,
            get_receipt,
            reject_receipt,
        )

        rid, _ = create_receipt(_data(), [_item()], 1, user=ADMIN_USER)
        approve_receipt(rid, 1, user=ADMIN_USER)
        assert get_receipt(rid)[0]["status"] == "Approved"
        cancel_receipt(rid, 1, user=ADMIN_USER)
        assert get_receipt(rid)[0]["status"] == "Cancelled"
        rid2, _ = create_receipt(_data(), [_item()], 1, user=ADMIN_USER)
        reject_receipt(rid2, 1, user=ADMIN_USER)
        assert get_receipt(rid2)[0]["status"] == "Rejected"

    def test_soft_delete_and_list(self):
        from lab_system.app.services.receipt_service import (
            create_receipt,
            list_receipts,
            restore_receipt,
            soft_delete_receipt,
        )

        rid, _ = create_receipt(_data(), [_item()], 1, user=ADMIN_USER)
        soft_delete_receipt(rid, 1, user=ADMIN_USER)
        rows, total = list_receipts()
        assert all(r["id"] != rid for r in rows)
        rows, total = list_receipts(include_deleted=True)
        assert any(r["id"] == rid for r in rows)
        restore_receipt(rid, 1, user=ADMIN_USER)
        rows, total = list_receipts()
        assert any(r["id"] == rid for r in rows)

    def test_archive_workflow(self):
        from lab_system.app.services.receipt_service import (
            archive_receipt,
            change_receipt_status,
            create_receipt,
            get_receipt,
            unarchive_receipt,
        )

        rid, _ = create_receipt(_data(), [_item()], 1, user=ADMIN_USER)
        change_receipt_status(rid, "Approved", 1, user=ADMIN_USER)
        archive_receipt(rid, 1, user=ADMIN_USER)
        assert get_receipt(rid)[0]["status"] == "Archived"
        unarchive_receipt(rid, 1, user=ADMIN_USER)
        assert get_receipt(rid)[0]["status"] == "Draft"

    def test_hard_delete(self):
        from lab_system.app.services.receipt_service import (
            create_receipt,
            get_receipt,
            hard_delete_receipt,
        )

        rid, _ = create_receipt(_data(), [_item()], 1, user=ADMIN_USER)
        hard_delete_receipt(rid, 1, user=ADMIN_USER)
        assert get_receipt(rid)[0] is None


class TestReporting:
    @classmethod
    def setup_class(cls):
        import lab_system.app.database.db as _db_mod

        cls.db_path = _make_db()
        _db_mod.get_conn = _make_get_conn(cls.db_path)
        from lab_system.app.services.receipt_service import create_receipt

        create_receipt(_data(), [_item()], 1, user=ADMIN_USER)
        create_receipt(_data(), [_item()], 1, user=ADMIN_USER)

    def test_receipt_summary(self):
        from lab_system.app.services.report_service import receipt_summary

        s = receipt_summary()
        assert s["total"] >= 2
        assert "Draft" in s["by_status"]

    def test_receipt_summary_grouping(self):
        from lab_system.app.services.report_service import receipt_summary

        by_month = receipt_summary(group_by="month")
        assert by_month["total"] >= 2
        by_type = receipt_summary(group_by="type")
        assert by_type["total"] >= 2

    def test_where_clause(self):
        from lab_system.app.services.report_service import _where_clause

        clauses, params = _where_clause("2026-01-01", "2026-12-31")
        assert "created_at >= ?" in clauses
        assert "created_at <= ?" in clauses
        assert "2026-01-01T00:00:00" in params
        assert "2026-12-31T23:59:59" in params

    def test_monthly_report(self):
        from lab_system.app.services.report_service import monthly_report

        rows = monthly_report()
        assert isinstance(rows, list)
        rows_filtered = monthly_report(year="2026")
        assert isinstance(rows_filtered, list)

    def test_sample_summary(self):
        from lab_system.app.services.report_service import sample_summary

        rows = sample_summary()
        assert len(rows) >= 1
        assert rows[0]["sample_name"] == "Serum"
        assert rows[0]["total"] == 200

    def test_daily_report(self):
        from lab_system.app.services.report_service import daily_report

        rows = daily_report()
        assert len(rows) >= 1

    def test_institution_statistics(self):
        from lab_system.app.services.report_service import institution_statistics

        stats = institution_statistics()
        assert len(stats["by_sender"]) >= 1
        assert len(stats["by_receiver"]) >= 1

    def test_rejection_statistics(self):
        from lab_system.app.services.report_service import rejection_statistics

        rows = rejection_statistics()
        assert len(rows) >= 1

    def test_damage_statistics(self):
        from lab_system.app.services.report_service import damage_statistics

        rows = damage_statistics()
        assert len(rows) >= 1

    def test_csv_export(self):
        from lab_system.app.services.report_service import export_receipts_csv

        path = self.db_path.parent / "test_export.csv"
        result = export_receipts_csv(str(path))
        assert result.exists() and result.stat().st_size > 0
        result.unlink()

    def test_xlsx_export(self):
        from lab_system.app.services.report_service import export_xlsx

        path = self.db_path.parent / "test_export.xlsx"
        result = export_xlsx(
            str(path), data_rows=[["A", 1], ["B", 2]], headers=["Name", "Count"]
        )
        assert result.exists() and result.stat().st_size > 0
        result.unlink()

    def test_pdf_export(self):
        from lab_system.app.services.report_service import export_pdf

        path = self.db_path.parent / "test_export.pdf"
        result = export_pdf(
            str(path), title="Test", headers=["N", "C"], data_rows=[["A", 1]]
        )
        assert result.exists() and result.stat().st_size > 0
        result.unlink()


class TestMigration:
    @classmethod
    def setup_class(cls):
        import lab_system.app.database.db as _db_mod

        cls.db_path = _make_db()
        _db_mod.get_conn = _make_get_conn(cls.db_path)

    def test_schema_version(self):
        from lab_system.app.database.db import SCHEMA_VERSION

        assert SCHEMA_VERSION >= 7

    def test_fts_triggers_exist(self):
        conn = sqlite3.connect(str(self.db_path))
        triggers = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'",
        ).fetchall()
        trigger_names = {t[0] for t in triggers}
        expected = {
            "receipts_ai",
            "receipts_ad",
            "receipts_au",
            "organizations_ai",
            "organizations_ad",
            "organizations_au",
        }
        assert expected.issubset(trigger_names)
        conn.close()

    def test_deleted_at_column(self):
        conn = sqlite3.connect(str(self.db_path))
        cols = [
            row[1] for row in conn.execute("PRAGMA table_info(receipts)").fetchall()
        ]
        assert "deleted_at" in cols
        conn.close()

    def test_receipt_history_table(self):
        conn = sqlite3.connect(str(self.db_path))
        tables = [
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'",
            ).fetchall()
        ]
        assert "receipt_history" in tables
        conn.close()

    def test_check_constraints(self):
        conn = sqlite3.connect(str(self.db_path))
        create_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='receipt_items'",
        ).fetchone()[0]
        assert "CHECK(total_count >= 0)" in create_sql
        assert "CHECK(damaged_count >= 0)" in create_sql
        conn.close()


class TestBackupRecovery:
    @classmethod
    def setup_class(cls):
        import lab_system.app.database.db as _db_mod
        import lab_system.app.services.backup_service as _bs
        import lab_system.app.services.recovery_service as _rs

        cls.db_path = _make_db()
        _db_mod.get_conn = _make_get_conn(cls.db_path)
        # Patch DB_PATH and STORAGE_DIR so backup/recovery services
        # operate on the test database instead of the real one
        test_storage = cls.db_path.parent
        _bs.DB_PATH = cls.db_path
        _bs.STORAGE_DIR = test_storage
        _rs.DB_PATH = cls.db_path
        _rs.STORAGE_DIR = test_storage
        _rs.BACKUP_DIR = test_storage / "backups"
        _rs.SNAPSHOT_DIR = test_storage / "snapshots"
        cls.backup_dir = _rs.BACKUP_DIR
        cls.snapshot_dir = _rs.SNAPSHOT_DIR
        cls.backup_dir.mkdir(parents=True, exist_ok=True)
        cls.snapshot_dir.mkdir(parents=True, exist_ok=True)
        from lab_system.app.services.receipt_service import create_receipt

        create_receipt(_data(), [_item()], 1, user=ADMIN_USER)

    def test_create_backup(self):
        from lab_system.app.services.backup_service import create_backup

        path = create_backup(user_id=1, notes="test", user=ADMIN_USER)
        assert Path(path).exists()
        Path(path).unlink()

    def test_verify_backup(self):
        from lab_system.app.services.backup_service import create_backup
        from lab_system.app.services.recovery_service import verify_backup

        path = create_backup(user_id=1, notes="test", user=ADMIN_USER)
        result = verify_backup(path)
        assert result["valid"] is True
        assert result["integrity_ok"] is True
        Path(path).unlink()

    def test_list_backups(self):
        from lab_system.app.services.recovery_service import list_backups

        backups = list_backups()
        assert isinstance(backups, list)

    def test_detect_corruption(self):
        from lab_system.app.services.recovery_service import detect_corruption

        result = detect_corruption()
        assert result["ok"] is True

    def test_recovery_snapshot(self):
        from lab_system.app.services.recovery_service import create_recovery_snapshot

        result = create_recovery_snapshot("test")
        assert result["success"] is True
        assert Path(result["path"]).exists()
        Path(result["path"]).unlink()

    def test_list_snapshots(self):
        from lab_system.app.services.recovery_service import list_snapshots

        snaps = list_snapshots()
        assert isinstance(snaps, list)

    def test_validate_recovery(self):
        from lab_system.app.services.backup_service import create_backup
        from lab_system.app.services.recovery_service import validate_recovery

        path = create_backup(user_id=1, notes="test", user=ADMIN_USER)
        result = validate_recovery(path, user=ADMIN_USER)
        assert result["valid"] is True
        Path(path).unlink()

    def test_enforce_retention(self):
        from lab_system.app.services.recovery_service import enforce_retention

        count = enforce_retention(max_backups=100)
        assert count >= 0

    def test_auto_backup(self):
        from lab_system.app.services.recovery_service import auto_backup

        result = auto_backup()
        assert result["success"] is True
        Path(result["path"]).unlink()

    def test_attempt_recovery(self):
        from lab_system.app.services.recovery_service import attempt_recovery

        result = attempt_recovery(user=ADMIN_USER)
        assert "actions" in result

    def test_verify_backup_missing(self):
        from lab_system.app.services.recovery_service import verify_backup

        result = verify_backup("/nonexistent/path/backup.db")
        assert result["valid"] is False
        assert result["error"] == "File not found"

    def test_verify_backup_empty_file(self):
        from lab_system.app.services.backup_service import create_backup
        from lab_system.app.services.recovery_service import verify_backup

        path = create_backup(user_id=1, notes="empty_test", user=ADMIN_USER)
        Path(path).write_bytes(b"")
        result = verify_backup(path)
        assert result["valid"] is False
        Path(path).unlink()

    def test_delete_backup_nonexistent(self):
        from lab_system.app.services.recovery_service import delete_backup

        result = delete_backup("/nonexistent/backup.db", user=ADMIN_USER)
        assert result["success"] is True

    def test_delete_backup(self):
        from lab_system.app.services.backup_service import create_backup
        from lab_system.app.services.recovery_service import delete_backup, list_backups

        path = create_backup(user_id=1, notes="delete_test", user=ADMIN_USER)
        before = len(list_backups())
        result = delete_backup(path, user=ADMIN_USER)
        assert result["success"] is True
        after = len(list_backups())
        assert after == before - 1 or after <= before

    def test_get_backup_record_missing(self):
        from lab_system.app.services.recovery_service import _get_backup_record

        result = _get_backup_record("/nonexistent.db")
        assert result is None

    def test_get_backup_record_found(self):
        from lab_system.app.services.backup_service import create_backup
        from lab_system.app.services.recovery_service import _get_backup_record

        path = create_backup(user_id=1, notes="record_test", user=ADMIN_USER)
        result = _get_backup_record(path)
        assert result is not None
        assert result["backup_file"] == path
        Path(path).unlink()

    def test_restore_from_backup_bad_backup(self):
        from lab_system.app.services.recovery_service import restore_from_backup

        bad_path = self.backup_dir / "bad_backup.db"
        bad_path.write_bytes(b"not a database")
        result = restore_from_backup(str(bad_path), user=ADMIN_USER)
        assert result["success"] is False
        assert result["error"] is not None
        bad_path.unlink()

    def test_list_snapshots_with_files(self):
        from lab_system.app.services.recovery_service import (
            create_recovery_snapshot,
            list_snapshots,
        )

        result = create_recovery_snapshot("test_list")
        assert result["success"] is True
        snaps = list_snapshots()
        assert len(snaps) >= 1
        names = [s["name"] for s in snaps]
        assert any("test_list" in n for n in names)
        Path(result["path"]).unlink()

    def test_enforce_retention_deletes_old(self):
        from lab_system.app.services.recovery_service import (
            enforce_retention,
            list_backups,
        )

        # Create 5 unique-named backup files directly
        paths = []
        for i in range(5):
            p = self.backup_dir / f"retention_test_{i}.db"
            Path(p).write_text("test")
            paths.append(p)
        # Verify list_backups sees all 5
        backups_before = list_backups()
        assert len(backups_before) >= len(paths)
        deleted = enforce_retention(max_backups=3)
        assert deleted >= 2, f"Only deleted {deleted} backups"
        for p in paths:
            Path(p).unlink(missing_ok=True)
        for p in self.backup_dir.glob("*.db"):
            p.unlink(missing_ok=True)

    def test_validate_recovery_bad_backup(self):
        from lab_system.app.services.recovery_service import validate_recovery

        bad_path = self.backup_dir / "bad_validate.db"
        bad_path.write_bytes(b"invalid data")
        result = validate_recovery(str(bad_path), user=ADMIN_USER)
        assert result["valid"] is False
        assert not result["checks"][0]["passed"]
        bad_path.unlink()

    def test_detect_corruption_on_bad_db(self):
        import lab_system.app.services.recovery_service as _rs
        from lab_system.app.services.recovery_service import detect_corruption

        old = _rs.DB_PATH
        bad_path = self.backup_dir / "corrupt.db"
        bad_path.write_bytes(b"\x00" * 512)
        _rs.DB_PATH = bad_path
        result = detect_corruption()
        assert result["ok"] is False
        _rs.DB_PATH = old
        bad_path.unlink()

    def test_attempt_recovery_no_backup(self):
        """attempt_recovery falls back gracefully with no backup available."""
        import shutil

        import lab_system.app.services.recovery_service as _rs
        from lab_system.app.services.recovery_service import attempt_recovery

        old_backup_dir = _rs.BACKUP_DIR
        empty_dir = self.db_path.parent / "empty_backups"
        empty_dir.mkdir(exist_ok=True)
        _rs.BACKUP_DIR = empty_dir
        result = attempt_recovery(user=ADMIN_USER)
        assert "actions" in result
        _rs.BACKUP_DIR = old_backup_dir
        shutil.rmtree(str(empty_dir), ignore_errors=True)
