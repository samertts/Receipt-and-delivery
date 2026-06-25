"""Recovery service tests."""

import os
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


ADMIN_USER = {"id": 1, "username": "admin", "role": "Admin", "status": "Active"}


def _make_valid_backup(tmp_path):
    """Create a valid SQLite backup file."""
    from lab_system.app.database.db import SCHEMA
    db_path = tmp_path / "backup.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.close()
    return db_path


def _make_invalid_file(tmp_path):
    """Create an invalid file."""
    p = tmp_path / "invalid.txt"
    p.write_text("not a database")
    return p


def _make_small_file(tmp_path):
    """Create a file too small to be a database."""
    p = tmp_path / "small.db"
    p.write_bytes(b"X")
    return p


class TestVerifyBackup:
    def test_valid_backup(self, fresh_db, seed_data, tmp_path):
        from lab_system.app.services.recovery_service import verify_backup
        db = _make_valid_backup(tmp_path)
        result = verify_backup(db)
        assert result["valid"] is True
        assert result["integrity_ok"] is True
        assert result["size"] > 0

    def test_nonexistent_file(self, fresh_db, seed_data):
        from lab_system.app.services.recovery_service import verify_backup
        result = verify_backup(Path("/nonexistent/file.db"))
        assert result["valid"] is False
        assert "not found" in result["error"].lower()

    def test_too_small_file(self, fresh_db, seed_data, tmp_path):
        from lab_system.app.services.recovery_service import verify_backup
        f = _make_small_file(tmp_path)
        result = verify_backup(f)
        assert result["valid"] is False
        assert "too small" in result["error"].lower()

    def test_invalid_file(self, fresh_db, seed_data, tmp_path):
        from lab_system.app.services.recovery_service import verify_backup
        f = _make_invalid_file(tmp_path)
        result = verify_backup(f)
        assert result["valid"] is False


class TestPathValidation:
    def test_valid_path_passes(self, tmp_path):
        from lab_system.app.services.recovery_service import _validate_path_in_dir
        allowed = tmp_path / "backups"
        allowed.mkdir()
        f = allowed / "test.db"
        f.write_text("data")
        result = _validate_path_in_dir(f, allowed)
        assert result == f.resolve()

    def test_path_traversal_raises(self, tmp_path):
        from lab_system.app.services.recovery_service import _validate_path_in_dir
        allowed = tmp_path / "backups"
        allowed.mkdir()
        bad_path = tmp_path / "other" / ".." / ".." / "etc" / "passwd"
        with pytest.raises(ValueError, match="not inside"):
            _validate_path_in_dir(bad_path, allowed)


class TestListBackups:
    def test_empty_dir(self, fresh_db, seed_data):
        from lab_system.app.services.recovery_service import list_backups
        result = list_backups()
        assert isinstance(result, list)

    def test_with_backups(self, fresh_db, seed_data, tmp_path):
        from lab_system.app.services.recovery_service import list_backups
        from lab_system.app.services.backup_service import create_backup
        create_backup(user_id=1, user=ADMIN_USER)
        result = list_backups()
        assert len(result) >= 1
        assert "path" in result[0]
        assert "name" in result[0]
        assert "size" in result[0]


class TestRecoverySnapshot:
    def test_create_snapshot(self, fresh_db, seed_data):
        from lab_system.app.services.recovery_service import create_recovery_snapshot
        result = create_recovery_snapshot(reason="test")
        assert result["success"] is True
        assert Path(result["path"]).exists()
        assert "snapshot_test_" in result["name"]

    def test_list_snapshots(self, fresh_db, seed_data):
        from lab_system.app.services.recovery_service import create_recovery_snapshot, list_snapshots
        create_recovery_snapshot(reason="test")
        snapshots = list_snapshots()
        assert len(snapshots) >= 1
        assert "path" in snapshots[0]


class TestDetectCorruption:
    def test健康的_db(self, fresh_db, seed_data):
        from lab_system.app.services.recovery_service import detect_corruption
        result = detect_corruption()
        assert result["ok"] is True
        assert len(result["errors"]) == 0


class TestEnforceRetention:
    def test_no_deletion_when_under_limit(self, fresh_db, seed_data):
        from lab_system.app.services.recovery_service import enforce_retention
        deleted = enforce_retention(max_backups=100)
        assert deleted == 0
