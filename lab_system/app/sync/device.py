import uuid

from lab_system.app.database import db as _db

DEVICE_ID_KEY = "sync.device_id"
BRANCH_ID_KEY = "sync.branch_id"


def get_device_id() -> str:
    with _db.get_conn() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?",
            (DEVICE_ID_KEY,),
        ).fetchone()
        if row:
            return row["value"]
        device_id = uuid.uuid4().hex[:16].upper()
        conn.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?)",
            (DEVICE_ID_KEY, device_id),
        )
        return device_id


def get_branch_id() -> str:
    with _db.get_conn() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?",
            (BRANCH_ID_KEY,),
        ).fetchone()
        if row:
            return row["value"]
        return ""


def set_branch_id(branch_id: str) -> None:
    with _db.get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings(key, value) VALUES(?, ?)",
            (BRANCH_ID_KEY, branch_id),
        )
