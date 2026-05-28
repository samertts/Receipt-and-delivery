"""
Database recovery and backup verification service.

Provides tools to verify backup integrity, detect database corruption,
and attempt recovery from WAL or backup files.
"""

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from lab_system.app.database import db as _db
from lab_system.app.settings.config import DB_PATH, STORAGE_DIR
from lab_system.app.utils.logging import setup_file_logging

logger = setup_file_logging(STORAGE_DIR / "logs", "INFO")


def verify_backup(path: Path | str) -> dict:
    """Check whether a backup file has a valid SQLite header and passes integrity check."""
    path = Path(path)
    result = {"valid": False, "size": 0, "error": None, "integrity_ok": False}
    if not path.exists():
        result["error"] = "File not found"
        return result
    result["size"] = path.stat().st_size
    if result["size"] < 100:
        result["error"] = "File too small to be a valid database"
        return result
    try:
        conn = sqlite3.connect(str(path))
        row = conn.execute("PRAGMA integrity_check;").fetchone()
        if row and row[0] == "ok":
            result["integrity_ok"] = True
            result["valid"] = True
        else:
            result["error"] = f"Integrity check failed: {row}"
        conn.close()
    except Exception as e:
        result["error"] = str(e)
    return result


def list_backups() -> list[dict]:
    """Return metadata for all backup files stored in the backups directory."""
    backups_dir = STORAGE_DIR / "backups"
    records = []
    if not backups_dir.exists():
        return records
    for f in sorted(backups_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if f.suffix == ".db":
            info = f.stat()
            records.append({
                "path": str(f),
                "name": f.name,
                "size": info.st_size,
                "modified": datetime.fromtimestamp(info.st_mtime).isoformat(timespec="seconds"),
            })
    return records


def restore_from_backup(backup_path: Path | str) -> dict:
    """Restore the production database from a verified backup file."""
    backup_path = Path(backup_path)
    result = {"success": False, "error": None, "restored_path": None}
    verification = verify_backup(backup_path)
    if not verification["valid"]:
        result["error"] = verification.get("error", "Backup verification failed")
        return result
    try:
        dest = DB_PATH
        backup_dest = dest.with_suffix(".db.corrupted")
        if dest.exists():
            shutil.move(str(dest), str(backup_dest))
        shutil.copy2(str(backup_path), str(dest))
        with _db.get_conn() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys = ON;")
        result["success"] = True
        result["restored_path"] = str(dest)
    except Exception as e:
        result["error"] = str(e)
    return result


def delete_backup(backup_path: Path | str) -> dict:
    """Remove a backup file from disk and its database record."""
    backup_path = Path(backup_path)
    result = {"success": False, "error": None}
    try:
        if backup_path.exists():
            backup_path.unlink()
        with _db.get_conn() as conn:
            conn.execute("DELETE FROM backups WHERE backup_file = ?", (str(backup_path),))
        result["success"] = True
    except Exception as e:
        result["error"] = str(e)
    return result
