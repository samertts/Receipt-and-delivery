"""Shared test fixtures for the QA framework."""

import os
import sqlite3
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="session")
def test_db_path():
    """Create a test database with full schema."""
    from lab_system.app.database.db import SCHEMA

    db_path = Path(tempfile.mkdtemp(prefix="lab_qa_")) / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def fresh_db(test_db_path, tmp_path):
    """Fresh database for each test with patched get_conn."""
    import lab_system.app.database.db as db_mod

    db_copy = tmp_path / "test.db"
    import shutil
    shutil.copy2(str(test_db_path), str(db_copy))

    @contextmanager
    def test_conn():
        c = sqlite3.connect(str(db_copy))
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys = ON;")
        c.execute("PRAGMA busy_timeout = 5000;")
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()

    orig = db_mod.get_conn
    db_mod.get_conn = test_conn
    yield db_copy
    db_mod.get_conn = orig


@pytest.fixture
def admin_user():
    """Admin user fixture."""
    return {"id": 1, "username": "admin", "role": "Admin", "status": "Active"}


@pytest.fixture
def regular_user():
    """Regular user fixture."""
    return {"id": 2, "username": "user1", "role": "User", "status": "Active"}


@pytest.fixture
def seed_data(fresh_db):
    """Seed test data into the database."""
    conn = sqlite3.connect(str(fresh_db))
    conn.row_factory = sqlite3.Row

    # Seed admin user
    from lab_system.app.auth.security import hash_password
    conn.execute(
        """INSERT OR IGNORE INTO users(username, password_hash, full_name, role, status, password_changed_at)
           VALUES(?, ?, ?, ?, ?, ?)""",
        ("admin", hash_password("Admin@123"), "Admin User", "Admin", "Active", ""),
    )
    conn.execute(
        """INSERT OR IGNORE INTO users(username, password_hash, full_name, role, status, password_changed_at)
           VALUES(?, ?, ?, ?, ?, ?)""",
        ("user1", hash_password("User@123"), "Regular User", "User", "Active", ""),
    )

    # Seed organization
    conn.execute(
        """INSERT OR IGNORE INTO organizations(name, code, org_type, governorate, address, phone, email, logo_path, notes, status)
           VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("Test Lab", "TL001", "Laboratory", "Baghdad", "Test Address", "0770000000", "test@lab.com", "", "", "Active"),
    )

    # Seed settings
    conn.execute("INSERT OR IGNORE INTO settings(key, value) VALUES(?, ?)", ("security.max_login_attempts", "5"))
    conn.execute("INSERT OR IGNORE INTO settings(key, value) VALUES(?, ?)", ("security.login_lockout_minutes", "5"))
    conn.execute("INSERT OR IGNORE INTO settings(key, value) VALUES(?, ?)", ("session.timeout_minutes", "15"))

    conn.commit()
    conn.close()
    return fresh_db
