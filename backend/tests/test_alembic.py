from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_CONFIG = ROOT / "backend" / "alembic.ini"


def _run_alembic(database_url: str, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    return subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ALEMBIC_CONFIG), *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_alembic_upgrade_downgrade_upgrade_and_check(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'alembic.db'}"

    upgraded = _run_alembic(database_url, "upgrade", "head")
    assert upgraded.returncode == 0, upgraded.stderr

    current = _run_alembic(database_url, "current")
    assert current.returncode == 0, current.stderr
    assert "8c2d4e5f6a02" in current.stdout

    with sqlite3.connect(tmp_path / "alembic.db") as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(sync_logs)")}
        assert "idempotency_key" in columns
        indexes = {
            row[1]
            for row in conn.execute("PRAGMA index_list(sync_logs)")
        }
        assert "uq_sync_log_idempotency_key" in indexes

    downgraded = _run_alembic(database_url, "downgrade", "-1")
    assert downgraded.returncode == 0, downgraded.stderr

    upgraded_again = _run_alembic(database_url, "upgrade", "head")
    assert upgraded_again.returncode == 0, upgraded_again.stderr

    checked = _run_alembic(database_url, "check")
    assert checked.returncode == 0, checked.stderr
    assert "No new upgrade operations detected" in checked.stdout


def test_production_init_db_is_blocked(monkeypatch):
    from app.core.config import settings
    from app.db.session import init_db

    monkeypatch.setattr(settings, "environment", "production")
    with pytest.raises(RuntimeError, match="alembic upgrade head"):
        init_db()
