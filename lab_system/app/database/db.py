import sqlite3
from contextlib import contextmanager
from pathlib import Path
from lab_system.app.settings.config import CONFIG

SCHEMA_VERSION = 4

SCHEMA = '''
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
 FOREIGN KEY(institution_id) REFERENCES organizations(id)
);
CREATE TABLE IF NOT EXISTS transaction_types (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT UNIQUE NOT NULL,
 is_active INTEGER NOT NULL DEFAULT 1,
 is_deleted INTEGER NOT NULL DEFAULT 0,
 created_at TEXT DEFAULT '',
 updated_at TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS sample_types (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT UNIQUE NOT NULL,
 category TEXT DEFAULT '',
 status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active','Archived')),
 is_deleted INTEGER NOT NULL DEFAULT 0,
 created_at TEXT DEFAULT '',
 updated_at TEXT DEFAULT ''
);
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
 received_at TEXT DEFAULT '',
 created_at TEXT NOT NULL,
 updated_at TEXT DEFAULT '',
 archived_at TEXT DEFAULT '',
 is_deleted INTEGER NOT NULL DEFAULT 0,
 notes TEXT DEFAULT '',
 transport_info TEXT DEFAULT '',
 additional_comments TEXT DEFAULT '',
 status TEXT NOT NULL CHECK(status IN ('Draft','Approved','Rejected','Archived','Cancelled')),
 created_by INTEGER,
 updated_by INTEGER,
 FOREIGN KEY(tx_type_id) REFERENCES transaction_types(id),
 FOREIGN KEY(sender_org_id) REFERENCES organizations(id),
 FOREIGN KEY(receiver_org_id) REFERENCES organizations(id),
 FOREIGN KEY(created_by) REFERENCES users(id),
 FOREIGN KEY(updated_by) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS receipt_items (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 receipt_id INTEGER NOT NULL,
 sample_type_id INTEGER NOT NULL,
 total_count INTEGER NOT NULL,
 valid_count INTEGER NOT NULL,
 damaged_count INTEGER NOT NULL,
 rejected_count INTEGER NOT NULL,
 non_conforming_count INTEGER NOT NULL,
 transport_condition TEXT DEFAULT '',
 notes TEXT DEFAULT '',
 created_at TEXT DEFAULT '',
 updated_at TEXT DEFAULT '',
 is_deleted INTEGER NOT NULL DEFAULT 0,
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
CREATE TABLE IF NOT EXISTS backups (id INTEGER PRIMARY KEY AUTOINCREMENT, backup_file TEXT NOT NULL, created_at TEXT NOT NULL, created_by INTEGER, notes TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT NOT NULL, machine_name TEXT NOT NULL, timestamp TEXT NOT NULL, details TEXT DEFAULT '');
CREATE INDEX IF NOT EXISTS idx_receipts_no ON receipts(receipt_no);
CREATE INDEX IF NOT EXISTS idx_receipts_created ON receipts(created_at);
CREATE INDEX IF NOT EXISTS idx_receipts_status ON receipts(status);
CREATE INDEX IF NOT EXISTS idx_receipts_tx_type ON receipts(tx_type_id);
CREATE INDEX IF NOT EXISTS idx_receipts_sender ON receipts(sender_org_id);
CREATE INDEX IF NOT EXISTS idx_receipts_receiver ON receipts(receiver_org_id);
CREATE INDEX IF NOT EXISTS idx_receipts_deleted ON receipts(is_deleted);
CREATE INDEX IF NOT EXISTS idx_items_sample ON receipt_items(sample_type_id);
CREATE INDEX IF NOT EXISTS idx_org_code ON organizations(code);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
'''

DEFAULT_SETTINGS = {
    'receipt.numbering_prefix': 'LAB',
    'receipt.font_size': '11',
    'receipt.margin_mm': '10',
    'receipt.template': 'default',
    'printer.mode': 'A4',
    'backup.auto_enabled': '0',
    'backup.path': str((Path(CONFIG.db_path).parent / 'lab_system' / 'storage' / 'backups').resolve()),
}


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}


def _add_column_if_missing(conn: sqlite3.Connection, table_name: str, column_name: str, ddl: str) -> None:
    if column_name not in _table_columns(conn, table_name):
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")


def migrate_db(conn: sqlite3.Connection) -> None:
    schema_row = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
    current = int(schema_row[0]) if schema_row else 0

    if current < 2:
        _add_column_if_missing(conn, 'receipts', 'additional_comments', "additional_comments TEXT DEFAULT ''")

    if current < 3:
        _add_column_if_missing(conn, 'attachments', 'thumbnail_path', "thumbnail_path TEXT DEFAULT ''")

    if current < 4:
        _add_column_if_missing(conn, 'receipts', 'received_at', "received_at TEXT DEFAULT ''")
        _add_column_if_missing(conn, 'receipts', 'updated_at', "updated_at TEXT DEFAULT ''")
        _add_column_if_missing(conn, 'receipts', 'archived_at', "archived_at TEXT DEFAULT ''")
        _add_column_if_missing(conn, 'receipts', 'updated_by', "updated_by INTEGER")
        _add_column_if_missing(conn, 'receipts', 'is_deleted', "is_deleted INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(conn, 'receipt_items', 'created_at', "created_at TEXT DEFAULT ''")
        _add_column_if_missing(conn, 'receipt_items', 'updated_at', "updated_at TEXT DEFAULT ''")
        _add_column_if_missing(conn, 'receipt_items', 'is_deleted', "is_deleted INTEGER NOT NULL DEFAULT 0")


def init_db():
    with sqlite3.connect(CONFIG.db_path) as conn:
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.executescript(SCHEMA)
        migrate_db(conn)
        conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version',?)", (str(SCHEMA_VERSION),))
        for k, v in DEFAULT_SETTINGS.items():
            conn.execute('INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)', (k, v))


@contextmanager
def get_conn():
    conn = sqlite3.connect(CONFIG.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON;')
    conn.execute('PRAGMA journal_mode=WAL;')
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
