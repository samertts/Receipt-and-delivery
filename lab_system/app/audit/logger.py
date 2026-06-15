import hashlib
import platform
import sqlite3
from datetime import datetime

from lab_system.app.database import db as _db


def _row_hash(row):
    raw = f"{row['id']}|{row['user_id']}|{row['action']}|{row['machine_name']}|{row['timestamp']}|{row['details']}|{row['prev_hash']}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def log_action(user_id, action, details=''):
    with _db.get_conn() as conn:
        prev = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 1").fetchone()
        prev_hash = _row_hash(prev) if prev else ''
        conn.execute(
            'INSERT INTO audit_logs(user_id,action,machine_name,timestamp,details,prev_hash) VALUES(?,?,?,?,?,?)',
            (user_id, action, platform.node(), datetime.now().isoformat(timespec='seconds'), details, prev_hash),
        )


def verify_audit_chain(conn=None):
    if conn is None:
        with _db.get_conn() as c:
            return _verify(c)
    return _verify(conn)


def _verify(conn):
    rows = conn.execute("SELECT * FROM audit_logs ORDER BY id").fetchall()
    for i, row in enumerate(rows):
        expected_prev = ''
        if i > 0:
            expected_prev = _row_hash(rows[i - 1])
        actual_prev = row['prev_hash'] or ''
        if actual_prev != expected_prev:
            return False, i, f"Hash mismatch at row {row['id']}"
    return True, len(rows), f"Chain intact: {len(rows)} entries"
