import hashlib
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from lab_system.app.settings.config import CONFIG

SCHEMA_VERSION = 11

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS organizations (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL,
 code TEXT UNIQUE NOT NULL,
 org_type TEXT NOT NULL DEFAULT 'Other',
 governorate TEXT DEFAULT '',
 address TEXT DEFAULT '',
 phone TEXT DEFAULT '',
 email TEXT DEFAULT '',
 logo_path TEXT DEFAULT '',
 notes TEXT DEFAULT '',
 status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active','Inactive','Archived'))
);
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 full_name TEXT NOT NULL,
 username TEXT UNIQUE NOT NULL,
 password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('Admin','Supervisor','User','Auditor')),
 institution_id INTEGER,
 phone TEXT DEFAULT '',
 notes TEXT DEFAULT '',
 status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active','Inactive')),
 password_changed_at TEXT DEFAULT '',
 FOREIGN KEY(institution_id) REFERENCES organizations(id)
);
CREATE TABLE IF NOT EXISTS transaction_types (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, is_active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS sample_types (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, category TEXT DEFAULT '', status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active','Archived')));
CREATE TABLE IF NOT EXISTS templates (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, config_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS receipts (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 receipt_no TEXT UNIQUE NOT NULL,
 tx_type_id INTEGER NOT NULL,
 sender_org_id INTEGER NOT NULL,
 receiver_org_id INTEGER NOT NULL,
 sender_name TEXT NOT NULL,
 receiver_name TEXT NOT NULL,
 sender_job_title TEXT DEFAULT '',
 receiver_job_title TEXT DEFAULT '',
 auth_doc_no TEXT DEFAULT '',
 auth_date TEXT,
 created_at TEXT NOT NULL,
 notes TEXT DEFAULT '',
 transport_info TEXT DEFAULT '',
 additional_comments TEXT DEFAULT '',
 deleted_at TEXT DEFAULT '',
 status TEXT NOT NULL CHECK(status IN ('Draft','Approved','Rejected','Archived','Cancelled')),
 created_by INTEGER,
 FOREIGN KEY(tx_type_id) REFERENCES transaction_types(id),
 FOREIGN KEY(sender_org_id) REFERENCES organizations(id),
 FOREIGN KEY(receiver_org_id) REFERENCES organizations(id),
 FOREIGN KEY(created_by) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS receipt_history (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 receipt_id INTEGER NOT NULL,
 field_name TEXT NOT NULL,
 old_value TEXT DEFAULT '',
 new_value TEXT DEFAULT '',
 changed_by INTEGER REFERENCES users(id),
 changed_at TEXT NOT NULL,
 FOREIGN KEY(receipt_id) REFERENCES receipts(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS receipt_items (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 receipt_id INTEGER NOT NULL,
 sample_type_id INTEGER NOT NULL,
 total_count INTEGER NOT NULL CHECK(total_count >= 0),
 valid_count INTEGER NOT NULL CHECK(valid_count >= 0),
 damaged_count INTEGER NOT NULL CHECK(damaged_count >= 0),
 rejected_count INTEGER NOT NULL CHECK(rejected_count >= 0),
 non_conforming_count INTEGER NOT NULL CHECK(non_conforming_count >= 0),
 transport_condition TEXT DEFAULT '',
 notes TEXT DEFAULT '',
 FOREIGN KEY(receipt_id) REFERENCES receipts(id) ON DELETE CASCADE,
 FOREIGN KEY(sample_type_id) REFERENCES sample_types(id)
);
CREATE TABLE IF NOT EXISTS attachments (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 receipt_id INTEGER NOT NULL,
 file_path TEXT NOT NULL,
 file_type TEXT NOT NULL,
 file_hash TEXT NOT NULL,
 file_size INTEGER NOT NULL DEFAULT 0,
 category TEXT NOT NULL,
 thumbnail_path TEXT DEFAULT '',
 created_at TEXT NOT NULL,
 FOREIGN KEY(receipt_id) REFERENCES receipts(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS schema_version (
 id INTEGER PRIMARY KEY CHECK (id = 1),
 version INTEGER NOT NULL,
 app_version TEXT NOT NULL,
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS migration_history (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 migration_key TEXT UNIQUE NOT NULL,
 checksum TEXT NOT NULL,
 applied_at TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('applied','rolled_back','failed')),
 notes TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS migration_lock (
 id INTEGER PRIMARY KEY CHECK(id = 1),
 is_locked INTEGER NOT NULL DEFAULT 0,
 owner TEXT DEFAULT '',
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS backups (id INTEGER PRIMARY KEY AUTOINCREMENT, backup_file TEXT NOT NULL, created_at TEXT NOT NULL, created_by INTEGER REFERENCES users(id), notes TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER REFERENCES users(id), action TEXT NOT NULL, machine_name TEXT NOT NULL, timestamp TEXT NOT NULL, details TEXT DEFAULT '', prev_hash TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS login_attempts (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 username TEXT NOT NULL,
 success INTEGER NOT NULL DEFAULT 0,
 attempted_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sync_queue (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 entity_type TEXT NOT NULL,
 entity_id INTEGER NOT NULL,
 action TEXT NOT NULL CHECK(action IN ('create','update','delete')),
 payload TEXT DEFAULT '',
 idempotency_key TEXT DEFAULT '',
 status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','synced','conflict','failed')),
 retry_count INTEGER NOT NULL DEFAULT 0,
 created_at TEXT NOT NULL,
 synced_at TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_sync_status ON sync_queue(status);
CREATE INDEX IF NOT EXISTS idx_sync_entity ON sync_queue(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_login_attempts_user ON login_attempts(username, attempted_at);
CREATE INDEX IF NOT EXISTS idx_receipts_no ON receipts(receipt_no);
CREATE INDEX IF NOT EXISTS idx_receipts_created ON receipts(created_at);
CREATE INDEX IF NOT EXISTS idx_items_sample ON receipt_items(sample_type_id);
CREATE INDEX IF NOT EXISTS idx_org_code ON organizations(code);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_receipts_status_created ON receipts(status, created_at);
CREATE INDEX IF NOT EXISTS idx_receipt_items_receipt_id ON receipt_items(receipt_id);
CREATE VIRTUAL TABLE IF NOT EXISTS receipts_fts USING fts5(receipt_no, sender_name, receiver_name, content='receipts', content_rowid='id');
CREATE VIRTUAL TABLE IF NOT EXISTS organizations_fts USING fts5(name, code, content='organizations', content_rowid='id');
CREATE TRIGGER IF NOT EXISTS receipts_ai AFTER INSERT ON receipts BEGIN
    INSERT OR REPLACE INTO receipts_fts(rowid, receipt_no, sender_name, receiver_name)
    VALUES (NEW.id, NEW.receipt_no, NEW.sender_name, NEW.receiver_name);
END;
CREATE TRIGGER IF NOT EXISTS receipts_ad AFTER DELETE ON receipts BEGIN
    DELETE FROM receipts_fts WHERE rowid = OLD.id;
END;
CREATE TRIGGER IF NOT EXISTS receipts_au AFTER UPDATE ON receipts BEGIN
    DELETE FROM receipts_fts WHERE rowid = OLD.id;
    INSERT INTO receipts_fts(rowid, receipt_no, sender_name, receiver_name)
    VALUES (NEW.id, NEW.receipt_no, NEW.sender_name, NEW.receiver_name);
END;
CREATE TRIGGER IF NOT EXISTS organizations_ai AFTER INSERT ON organizations BEGIN
    INSERT OR REPLACE INTO organizations_fts(rowid, name, code)
    VALUES (NEW.id, NEW.name, NEW.code);
END;
CREATE TRIGGER IF NOT EXISTS organizations_ad AFTER DELETE ON organizations BEGIN
    DELETE FROM organizations_fts WHERE rowid = OLD.id;
END;
CREATE TRIGGER IF NOT EXISTS organizations_au AFTER UPDATE ON organizations BEGIN
    DELETE FROM organizations_fts WHERE rowid = OLD.id;
    INSERT INTO organizations_fts(rowid, name, code)
    VALUES (NEW.id, NEW.name, NEW.code);
END;
"""


def rebuild_fts():
    try:
        with get_conn() as conn:
            conn.execute("DELETE FROM receipts_fts;")
            conn.execute(
                "INSERT INTO receipts_fts(rowid, receipt_no, sender_name, receiver_name) "
                "SELECT id, receipt_no, sender_name, receiver_name FROM receipts "
                "WHERE deleted_at IS NULL OR deleted_at = '';"
            )
            conn.execute("DELETE FROM organizations_fts;")
            conn.execute(
                "INSERT INTO organizations_fts(rowid, name, code) "
                "SELECT id, name, code FROM organizations;"
            )
    except Exception:
        pass


DEFAULT_SETTINGS = {
    "receipt.numbering_prefix": "LAB",
    "receipt.font_size": "11",
    "receipt.margin_mm": "10",
    "receipt.template": "default",
    "printer.mode": "A4",
    "backup.auto_enabled": "0",
    "backup.retention_max": "30",
    "backup.path": str((CONFIG.storage_dir / "backups").resolve()),
    "session.timeout_minutes": "15",
    "security.max_login_attempts": "5",
    "security.login_lockout_minutes": "5",
    "security.force_password_change_days": "0",
}


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    return {
        row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    }


def migrate_db(conn: sqlite3.Connection) -> None:
    schema_row = conn.execute(
        "SELECT value FROM meta WHERE key='schema_version'"
    ).fetchone()
    current = int(schema_row[0]) if schema_row else 0

    if current < 2:
        if "additional_comments" not in _table_columns(conn, "receipts"):
            statement = (
                "ALTER TABLE receipts ADD COLUMN additional_comments TEXT DEFAULT ''"
            )
            conn.execute(statement)
            _record_migration(conn, "v2_receipts_additional_comments", statement)

    if current < 3:
        if "thumbnail_path" not in _table_columns(conn, "attachments"):
            statement = (
                "ALTER TABLE attachments ADD COLUMN thumbnail_path TEXT DEFAULT ''"
            )
            conn.execute(statement)
            _record_migration(conn, "v3_attachments_thumbnail_path", statement)

    if current < 4:
        conn.execute(
            "INSERT OR IGNORE INTO schema_version(id, version, app_version, updated_at) VALUES(1, ?, ?, ?)",
            (
                SCHEMA_VERSION,
                CONFIG.app_version,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        _record_migration(
            conn,
            "v4_lifecycle_metadata",
            "schema_version + migration_history initialization",
        )

    if current < 5:
        statement = "sync_queue table with indexes for future synchronization"
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sync_queue (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             entity_type TEXT NOT NULL,
             entity_id INTEGER NOT NULL,
             action TEXT NOT NULL CHECK(action IN ('create','update','delete')),
             payload TEXT DEFAULT '',
             status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','synced','conflict','failed')),
             retry_count INTEGER NOT NULL DEFAULT 0,
             created_at TEXT NOT NULL,
             synced_at TEXT DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_sync_status ON sync_queue(status);
            CREATE INDEX IF NOT EXISTS idx_sync_entity ON sync_queue(entity_type, entity_id);
        """)
        _record_migration(conn, "v5_sync_queue", statement)

    if current < 6:
        if "password_changed_at" not in _table_columns(conn, "users"):
            conn.execute(
                "ALTER TABLE users ADD COLUMN password_changed_at TEXT DEFAULT '';"
            )
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS login_attempts (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             username TEXT NOT NULL,
             success INTEGER NOT NULL DEFAULT 0,
             attempted_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_login_attempts_user ON login_attempts(username, attempted_at);
        """)
        _record_migration(
            conn, "v6_security_hardening", "password_changed_at + login_attempts table"
        )

    if current < 7:
        if "deleted_at" not in _table_columns(conn, "receipts"):
            conn.execute("ALTER TABLE receipts ADD COLUMN deleted_at TEXT DEFAULT '';")
        conn.executescript("""
            CREATE INDEX IF NOT EXISTS idx_receipts_deleted ON receipts(deleted_at);
            CREATE INDEX IF NOT EXISTS idx_receipts_status_created ON receipts(status, created_at);
        """)
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS receipts_fts USING fts5(
                receipt_no, sender_name, receiver_name,
                content='receipts', content_rowid='id'
            )
        """)
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS organizations_fts USING fts5(
                name, code,
                content='organizations', content_rowid='id'
            )
        """)
        conn.execute("INSERT INTO receipts_fts(receipts_fts) VALUES('rebuild')")
        conn.execute(
            "INSERT INTO organizations_fts(organizations_fts) VALUES('rebuild')"
        )
        # FTS sync triggers
        conn.executescript("""
            CREATE TRIGGER IF NOT EXISTS receipts_ai AFTER INSERT ON receipts BEGIN
                INSERT OR REPLACE INTO receipts_fts(rowid, receipt_no, sender_name, receiver_name)
                VALUES (NEW.id, NEW.receipt_no, NEW.sender_name, NEW.receiver_name);
            END;

            CREATE TRIGGER IF NOT EXISTS receipts_ad AFTER DELETE ON receipts BEGIN
                DELETE FROM receipts_fts WHERE rowid = OLD.id;
            END;

            CREATE TRIGGER IF NOT EXISTS receipts_au AFTER UPDATE ON receipts BEGIN
                DELETE FROM receipts_fts WHERE rowid = OLD.id;
                INSERT INTO receipts_fts(rowid, receipt_no, sender_name, receiver_name)
                VALUES (NEW.id, NEW.receipt_no, NEW.sender_name, NEW.receiver_name);
            END;

            CREATE TRIGGER IF NOT EXISTS organizations_ai AFTER INSERT ON organizations BEGIN
                INSERT OR REPLACE INTO organizations_fts(rowid, name, code)
                VALUES (NEW.id, NEW.name, NEW.code);
            END;

            CREATE TRIGGER IF NOT EXISTS organizations_ad AFTER DELETE ON organizations BEGIN
                DELETE FROM organizations_fts WHERE rowid = OLD.id;
            END;

            CREATE TRIGGER IF NOT EXISTS organizations_au AFTER UPDATE ON organizations BEGIN
                DELETE FROM organizations_fts WHERE rowid = OLD.id;
                INSERT INTO organizations_fts(rowid, name, code)
                VALUES (NEW.id, NEW.name, NEW.code);
            END;
        """)
        _recreate_table_with_fk(conn, "backups")
        _recreate_table_with_fk(conn, "audit_logs")
        _record_migration(
            conn, "v7_data_integrity", "soft delete, FTS5, indexes, FKs, CHECKs"
        )

    if current < 8:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS receipt_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                old_value TEXT DEFAULT '',
                new_value TEXT DEFAULT '',
                changed_by INTEGER REFERENCES users(id),
                changed_at TEXT NOT NULL,
                FOREIGN KEY(receipt_id) REFERENCES receipts(id) ON DELETE CASCADE
            )
        """)
        _record_migration(conn, "v8_receipt_history", "receipt history table")

    if current < 9:
        conn.executescript("""
            CREATE INDEX IF NOT EXISTS idx_receipt_items_receipt_id ON receipt_items(receipt_id);
            CREATE INDEX IF NOT EXISTS idx_receipts_deleted ON receipts(deleted_at);
        """)
        conn.execute("DELETE FROM receipts_fts;")
        conn.execute(
            "INSERT INTO receipts_fts(rowid, receipt_no, sender_name, receiver_name) "
            "SELECT id, receipt_no, sender_name, receiver_name FROM receipts "
            "WHERE deleted_at IS NULL OR deleted_at = ''"
        )
        _record_migration(
            conn,
            "v9_index_and_fts_fix",
            "receipt_items(receipt_id) index, deleted_at index, FTS rebuild",
        )

    if current < 10:
        if "prev_hash" not in _table_columns(conn, "audit_logs"):
            conn.execute("ALTER TABLE audit_logs ADD COLUMN prev_hash TEXT DEFAULT ''")
        _record_migration(
            conn,
            "v10_audit_integrity",
            "add prev_hash column for audit chain integrity",
        )

    if current < 11:
        if "idempotency_key" not in _table_columns(conn, "sync_queue"):
            conn.execute(
                "ALTER TABLE sync_queue ADD COLUMN idempotency_key TEXT DEFAULT ''"
            )
        _record_migration(
            conn, "v11_sync_idempotency", "add idempotency_key column to sync_queue"
        )


def _recreate_table_with_fk(conn: sqlite3.Connection, table: str) -> None:
    fk_map = {"user_id": "users(id)", "created_by": "users(id)"}
    cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
    if not cols:
        return
    col_defs = []
    for c in cols:
        cid, name, ctype, notnull, default, pk = c
        parts = [name, ctype]
        if pk:
            parts.append("PRIMARY KEY AUTOINCREMENT" if pk == 1 else "PRIMARY KEY")
        if notnull:
            parts.append("NOT NULL")
        if default is not None:
            if default == "":
                parts.append("DEFAULT ''")
            else:
                parts.append(f"DEFAULT '{default}'")
        ref = fk_map.get(name)
        if ref:
            parts.append(f"REFERENCES {ref}")
        col_defs.append(" ".join(parts))
    ddl = f"CREATE TABLE IF NOT EXISTS _new ({', '.join(col_defs)})"
    conn.execute(f"SAVEPOINT sp_fk_{table}")
    conn.execute(ddl)
    conn.execute(f"INSERT OR IGNORE INTO _new SELECT * FROM {table}")
    conn.execute(f"DROP TABLE {table}")
    conn.execute(f"ALTER TABLE _new RENAME TO {table}")
    conn.execute(f"RELEASE sp_fk_{table}")


def _backup_before_migration():
    db_path = Path(CONFIG.db_path)
    if not db_path.exists():
        return
    backup_dir = db_path.parent / "migration_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"pre_migration_{timestamp}.db"
    shutil.copy2(str(db_path), str(backup_path))


def init_db():
    _backup_before_migration()
    with sqlite3.connect(CONFIG.db_path) as conn:
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(SCHEMA)
        _acquire_migration_lock(conn)
        try:
            migrate_db(conn)
        finally:
            _release_migration_lock(conn)
        now = datetime.now().isoformat(timespec="seconds")
        conn.execute(
            "INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version',?)",
            (str(SCHEMA_VERSION),),
        )
        conn.execute(
            "INSERT OR REPLACE INTO schema_version(id, version, app_version, updated_at) VALUES(1, ?, ?, ?)",
            (SCHEMA_VERSION, CONFIG.app_version, now),
        )
        for k, v in DEFAULT_SETTINGS.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k, v)
            )


@contextmanager
def get_conn():
    conn = sqlite3.connect(CONFIG.db_path)
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


def _record_migration(
    conn: sqlite3.Connection, migration_key: str, payload: str, notes: str = ""
) -> None:
    checksum = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    conn.execute(
        """INSERT OR REPLACE INTO migration_history(migration_key, checksum, applied_at, status, notes)
        VALUES(?, ?, ?, 'applied', ?)""",
        (migration_key, checksum, datetime.now().isoformat(timespec="seconds"), notes),
    )


def _acquire_migration_lock(conn: sqlite3.Connection) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute(
        "INSERT OR IGNORE INTO migration_lock(id, is_locked, owner, updated_at) VALUES(1, 0, '', ?)",
        (now,),
    )
    row = conn.execute(
        "SELECT is_locked, updated_at FROM migration_lock WHERE id=1"
    ).fetchone()
    if row and int(row[0]) == 1:
        updated_at = row[1]
        if updated_at:
            lock_time = datetime.fromisoformat(updated_at)
            if datetime.now() - lock_time > timedelta(minutes=5):
                conn.execute(
                    "UPDATE migration_lock SET is_locked=0, owner='', updated_at=? WHERE id=1",
                    (now,),
                )
            else:
                raise RuntimeError(
                    "Migration lock is active; aborting concurrent migration."
                )
        else:
            raise RuntimeError(
                "Migration lock is active; aborting concurrent migration."
            )
    conn.execute(
        "UPDATE migration_lock SET is_locked=1, owner='init_db', updated_at=? WHERE id=1",
        (now,),
    )


def _release_migration_lock(conn: sqlite3.Connection) -> None:
    conn.execute(
        "UPDATE migration_lock SET is_locked=0, owner='', updated_at=? WHERE id=1",
        (datetime.now().isoformat(timespec="seconds"),),
    )
