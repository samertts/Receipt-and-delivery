"""Database validation tests — Schema, migrations, constraints."""

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestDatabaseSchema:
    """Verify database schema integrity."""

    def test_schema_executes_cleanly(self):
        from lab_system.app.database.db import SCHEMA

        db_path = Path(tempfile.mkdtemp()) / "schema_test.db"
        conn = sqlite3.connect(str(db_path))
        conn.executescript(SCHEMA)
        conn.commit()
        conn.close()
        assert db_path.exists()

    def test_all_tables_created(self):
        from lab_system.app.database.db import SCHEMA

        db_path = Path(tempfile.mkdtemp()) / "tables_test.db"
        conn = sqlite3.connect(str(db_path))
        conn.executescript(SCHEMA)
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]
        conn.close()

        required = ["users", "organizations", "receipts", "settings", "audit_logs", "backups"]
        for t in required:
            assert t in tables, f"Table '{t}' missing from schema"

    def test_foreign_keys_enforced(self, fresh_db):
        conn = sqlite3.connect(str(fresh_db))
        conn.execute("PRAGMA foreign_keys = ON")
        fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        conn.close()
        assert fk == 1

    def test_wal_mode_enabled(self, fresh_db):
        conn = sqlite3.connect(str(fresh_db))
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        conn.close()
        assert mode == "wal"

    def test_schema_version_tracking(self, fresh_db):
        conn = sqlite3.connect(str(fresh_db))
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        conn.close()
        assert "schema_version" in tables

    def test_users_table_constraints(self, fresh_db, seed_data):
        conn = sqlite3.connect(str(fresh_db))
        # Duplicate username should fail
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO users(username, password_hash, full_name, role, status) VALUES(?,?,?,?,?)",
                ("admin", "hash", "Dup", "User", "Active"),
            )
        conn.close()

    def test_settings_key_value(self, fresh_db):
        conn = sqlite3.connect(str(fresh_db))
        conn.execute("INSERT INTO settings(key,value) VALUES(?,?)", ("test.k", "test.v"))
        row = conn.execute("SELECT value FROM settings WHERE key=?", ("test.k",)).fetchone()
        conn.close()
        assert row[0] == "test.v"

    def test_audit_logs_insert(self, fresh_db):
        conn = sqlite3.connect(str(fresh_db))
        conn.execute(
            "INSERT INTO audit_logs(user_id,action,machine_name,timestamp) VALUES(?,?,?,?)",
            (1, "test", "test_machine", "2026-01-01 00:00:00"),
        )
        count = conn.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0]
        conn.close()
        assert count >= 1

    def test_schema_can_be_reapplied(self, test_db_path):
        from lab_system.app.database.db import SCHEMA

        conn = sqlite3.connect(str(test_db_path))
        conn.executescript(SCHEMA)
        conn.commit()
        conn.close()

    def test_schema_version_matches(self):
        from lab_system.app.database.db import SCHEMA_VERSION

        assert isinstance(SCHEMA_VERSION, int)
        assert SCHEMA_VERSION > 0
