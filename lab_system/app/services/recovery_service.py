"""
Database recovery and backup verification service.

Provides tools to verify backup integrity, detect database corruption,
attempt recovery from WAL or backup files, and manage backup retention.
"""

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from lab_system.app.auth.permissions import with_permission
from lab_system.app.database import db as _db
from lab_system.app.database.db import rebuild_fts
from lab_system.app.settings.config import DB_PATH, STORAGE_DIR
from lab_system.app.utils.logging import setup_file_logging

logger = setup_file_logging(STORAGE_DIR / "logs", "INFO")

BACKUP_DIR = STORAGE_DIR / "backups"
SNAPSHOT_DIR = STORAGE_DIR / "snapshots"


def _validate_path_in_dir(path: Path, allowed_dir: Path) -> Path:
    resolved = path.resolve()
    allowed = allowed_dir.resolve()
    if not str(resolved).startswith(str(allowed)):
        raise ValueError(f"Path {resolved} is not inside {allowed}")
    return resolved


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
        conn.execute("PRAGMA busy_timeout = 3000;")
        try:
            row = conn.execute("PRAGMA integrity_check;").fetchone()
            if row and row[0] == "ok":
                result["integrity_ok"] = True
                result["valid"] = True
            else:
                result["error"] = f"Integrity check failed: {row}"
        finally:
            conn.close()
    except Exception as e:
        result["error"] = str(e)
    return result


def list_backups() -> list[dict]:
    """Return metadata for all backup files stored in the backups directory."""
    records = []
    if not BACKUP_DIR.exists():
        return records
    for f in sorted(BACKUP_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if f.suffix == ".db":
            info = f.stat()
            records.append({
                "path": str(f),
                "name": f.name,
                "size": info.st_size,
                "modified": datetime.fromtimestamp(info.st_mtime).isoformat(timespec="seconds"),
            })
    return records


def _get_backup_record(path: str) -> dict | None:
    with _db.get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM backups WHERE backup_file = ?", (path,),
        ).fetchone()
    return dict(row) if row else None


def _checkpoint_wal():
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        conn.close()
    except Exception:
        pass


@with_permission('backup.restore')
def restore_from_backup(backup_path: Path | str, user=None) -> dict:
    """Restore the production database from a verified backup file."""
    backup_path = _validate_path_in_dir(Path(backup_path), BACKUP_DIR)
    result = {"success": False, "error": None, "restored_path": None}
    verification = verify_backup(backup_path)
    if not verification["valid"]:
        result["error"] = verification.get("error", "Backup verification failed")
        return result
    try:
        snapshot_result = create_recovery_snapshot("pre_restore")
        result["pre_restore_snapshot"] = snapshot_result.get("path")

        _checkpoint_wal()

        dest = DB_PATH
        backup_dest = dest.with_suffix(".db.corrupted")
        if dest.exists():
            shutil.move(str(dest), str(backup_dest))
        shutil.copy2(str(backup_path), str(dest))
        with _db.get_conn() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys = ON;")
        rebuild_fts()
        verify = verify_backup(dest)
        if not verify["valid"]:
            if backup_dest.exists():
                shutil.move(str(backup_dest), str(dest))
            result["error"] = "Restored database failed integrity check"
            return result
        result["success"] = True
        result["restored_path"] = str(dest)
    except Exception as e:
        result["error"] = str(e)
    return result


@with_permission('backup.delete')
def delete_backup(backup_path: Path | str, user=None) -> dict:
    """Remove a backup file from disk and its database record."""
    result = {"success": False, "error": None}
    backup_path = Path(backup_path)
    if backup_path.exists():
        try:
            backup_path = _validate_path_in_dir(backup_path, BACKUP_DIR)
        except ValueError as e:
            result["error"] = str(e)
            return result
    try:
        if backup_path.exists():
            backup_path.unlink()
        with _db.get_conn() as conn:
            conn.execute("DELETE FROM backups WHERE backup_file = ?", (str(backup_path),))
        result["success"] = True
    except Exception as e:
        result["error"] = str(e)
    return result


def create_recovery_snapshot(reason="manual") -> dict:
    """Create a point-in-time snapshot of the current database."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"snapshot_{reason}_{ts}.db"
    target = SNAPSHOT_DIR / name
    try:
        shutil.copy2(str(DB_PATH), str(target))
        return {"success": True, "path": str(target), "name": name}
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_snapshots() -> list[dict]:
    records = []
    if not SNAPSHOT_DIR.exists():
        return records
    for f in sorted(SNAPSHOT_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if f.suffix == ".db":
            info = f.stat()
            records.append({
                "path": str(f), "name": f.name, "size": info.st_size,
                "created": datetime.fromtimestamp(info.st_mtime).isoformat(timespec="seconds"),
            })
    return records


def auto_backup(notes="auto") -> dict:
    """Create automatic backup and enforce retention policy."""
    from lab_system.app.services.backup_service import create_backup
    _system_user = {"id": 0, "username": "system", "role": "Admin", "status": "Active"}
    try:
        path = create_backup(user_id=None, notes=notes, user=_system_user)
        enforce_retention()
        return {"success": True, "path": path}
    except Exception as e:
        return {"success": False, "error": str(e)}


def enforce_retention(max_backups=30) -> int:
    """Remove oldest backups exceeding max_backups. Returns number deleted."""
    _system_user = {"id": 0, "username": "system", "role": "Admin", "status": "Active"}
    backups = list_backups()
    if len(backups) <= max_backups:
        return 0
    deleted = 0
    for b in backups[max_backups:]:
        result = delete_backup(b["path"], user=_system_user)
        if result["success"]:
            deleted += 1
    return deleted


@with_permission('backup.verify')
def validate_recovery(backup_path: Path | str, user=None) -> dict:
    """Validate that a backup can be restored successfully (dry run)."""
    backup_path = _validate_path_in_dir(Path(backup_path), BACKUP_DIR)
    result = {"valid": False, "checks": []}

    v = verify_backup(backup_path)
    result["checks"].append({"name": "integrity", "passed": v["valid"], "detail": v.get("error")})
    if not v["valid"]:
        result["valid"] = False
        return result

    try:
        conn = sqlite3.connect(str(backup_path))
        conn.execute("PRAGMA busy_timeout = 3000;")
        try:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '\\_%' ESCAPE '\\'",
            ).fetchall()
            table_count = len(tables)
            result["checks"].append({"name": "tables", "passed": table_count > 0, "detail": f"{table_count} tables"})

            row = conn.execute("SELECT COUNT(*) c FROM receipts").fetchone()
            result["checks"].append({"name": "receipts_count", "passed": True, "detail": f"{row[0]} receipts"})

            row = conn.execute("SELECT COUNT(*) c FROM users").fetchone()
            result["checks"].append({"name": "users_count", "passed": row[0] > 0, "detail": f"{row[0]} users"})
        finally:
            conn.close()
    except Exception as e:
        result["checks"].append({"name": "read_error", "passed": False, "detail": str(e)})

    result["valid"] = all(c["passed"] for c in result["checks"])
    return result


def detect_corruption() -> dict:
    """Check current database for corruption."""
    result = {"ok": True, "errors": []}
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("PRAGMA busy_timeout = 3000;")
        try:
            row = conn.execute("PRAGMA integrity_check;").fetchone()
            if not row or row[0] != "ok":
                result["ok"] = False
                result["errors"].append(f"Integrity: {row}")
            wal_path = DB_PATH.with_name(DB_PATH.name + "-wal")
            if wal_path.exists() and wal_path.stat().st_size > 0:
                result["wal_size"] = wal_path.stat().st_size
        finally:
            conn.close()
    except Exception as e:
        result["ok"] = False
        result["errors"].append(str(e))
    return result


@with_permission('backup.restore')
def attempt_recovery(user=None) -> dict:
    """Attempt to recover the database from WAL or latest backup."""
    result = {"success": False, "actions": []}

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.execute("PRAGMA wal_checkpoint(PASSIVE);")
        conn.close()
        result["actions"].append("WAL checkpoint performed")
        verify = detect_corruption()
        if verify["ok"]:
            result["success"] = True
            logger.info("Database recovered via WAL checkpoint")
            return result
    except Exception as e:
        result["actions"].append(f"WAL checkpoint failed: {e}")

    backups = list_backups()
    if backups:
        latest = backups[0]
        restore_result = restore_from_backup(latest["path"])
        if restore_result["success"]:
            result["success"] = True
            result["actions"].append(f"Restored from backup: {latest['name']}")
            logger.info(f"Database recovered from backup: {latest['name']}")
        else:
            result["actions"].append(f"Backup restore failed: {restore_result.get('error')}")
    else:
        result["actions"].append("No backup available for recovery")

    return result
