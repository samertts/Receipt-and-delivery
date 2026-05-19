import sqlite3
from contextlib import contextmanager
from lab_system.app.settings.config import DB_PATH

SCHEMA = '''
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 username TEXT UNIQUE NOT NULL,
 full_name TEXT NOT NULL,
 password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('Admin','Supervisor','User','Auditor')),
 active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS organizations (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL,
 code TEXT UNIQUE NOT NULL,
 address TEXT DEFAULT '',
 phone TEXT DEFAULT '',
 email TEXT DEFAULT '',
 logo_path TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS receipts (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 receipt_no TEXT UNIQUE NOT NULL,
 tx_type TEXT NOT NULL,
 sender_org_id INTEGER NOT NULL,
 receiver_org_id INTEGER NOT NULL,
 sender_name TEXT NOT NULL,
 receiver_name TEXT NOT NULL,
 auth_doc_no TEXT DEFAULT '',
 auth_date TEXT,
 created_at TEXT NOT NULL,
 notes TEXT DEFAULT '',
 status TEXT NOT NULL CHECK(status IN ('Draft','Approved','Rejected','Archived','Cancelled')),
 created_by INTEGER,
 FOREIGN KEY(sender_org_id) REFERENCES organizations(id),
 FOREIGN KEY(receiver_org_id) REFERENCES organizations(id),
 FOREIGN KEY(created_by) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS receipt_items (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 receipt_id INTEGER NOT NULL,
 sample_type TEXT NOT NULL,
 total_count INTEGER NOT NULL,
 valid_count INTEGER NOT NULL,
 damaged_count INTEGER NOT NULL,
 rejected_count INTEGER NOT NULL,
 non_conforming_count INTEGER NOT NULL,
 transport_condition TEXT DEFAULT '',
 notes TEXT DEFAULT '',
 FOREIGN KEY(receipt_id) REFERENCES receipts(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS attachments (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 receipt_id INTEGER NOT NULL,
 file_path TEXT NOT NULL,
 file_type TEXT NOT NULL,
 file_hash TEXT NOT NULL,
 category TEXT NOT NULL,
 created_at TEXT NOT NULL,
 FOREIGN KEY(receipt_id) REFERENCES receipts(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS audit_logs (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER,
 action TEXT NOT NULL,
 machine_name TEXT NOT NULL,
 timestamp TEXT NOT NULL,
 details TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS settings (
 key TEXT PRIMARY KEY,
 value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS backups (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 backup_file TEXT NOT NULL,
 created_at TEXT NOT NULL,
 created_by INTEGER,
 notes TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_receipts_no ON receipts(receipt_no);
CREATE INDEX IF NOT EXISTS idx_receipts_created ON receipts(created_at);
CREATE INDEX IF NOT EXISTS idx_receipts_type ON receipts(tx_type);
CREATE INDEX IF NOT EXISTS idx_items_sample ON receipt_items(sample_type);
'''

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON;')
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
