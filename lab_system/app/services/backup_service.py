import hashlib
import sqlite3
from datetime import datetime

from lab_system.app.auth.permissions import with_permission
from lab_system.app.database import db as _db
from lab_system.app.settings.config import DB_PATH, STORAGE_DIR


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@with_permission("backup.create")
def create_backup(user_id=None, notes="", user=None):
    target = (
        STORAGE_DIR
        / "backups"
        / f"lab_system_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    )
    target.parent.mkdir(parents=True, exist_ok=True)

    src_conn = sqlite3.connect(str(DB_PATH))
    src_conn.execute("PRAGMA busy_timeout = 5000;")
    try:
        src_conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        dst_conn = sqlite3.connect(str(target))
        try:
            src_conn.backup(dst_conn, pages=-1, progress=None)
        finally:
            dst_conn.close()
    finally:
        src_conn.close()

    checksum = _sha256_file(target)
    with _db.get_conn() as conn:
        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(backups)").fetchall()
        }
        if "checksum" in columns:
            conn.execute(
                "INSERT INTO backups(backup_file,created_at,created_by,notes,checksum) VALUES(?,?,?,?,?)",
                (
                    str(target),
                    datetime.now().isoformat(timespec="seconds"),
                    user_id,
                    notes,
                    checksum,
                ),
            )
        else:
            conn.execute(
                "INSERT INTO backups(backup_file,created_at,created_by,notes) VALUES(?,?,?,?)",
                (str(target), datetime.now().isoformat(timespec="seconds"), user_id, notes),
            )
    return str(target)
