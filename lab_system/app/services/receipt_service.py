import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from lab_system.app.audit.logger import log_action
from lab_system.app.auth.permissions import with_permission
from lab_system.app.database import db as _db
from lab_system.app.sync.service import sync_service

logger = logging.getLogger(__name__)


def _compute_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def next_receipt_no(conn=None):
    year = datetime.now().year
    if conn is None:
        with _db.get_conn() as conn:
            return next_receipt_no(conn)
    
    # Ensure meta table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    meta_key = f"last_receipt_no_{year}"
    
    # Use immediate transaction to prevent race condition
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN IMMEDIATE")
        row = cursor.execute(
            "SELECT value FROM meta WHERE key=?",
            (meta_key,),
        ).fetchone()
        if row:
            last_no = int(row[0])
        else:
            # Initialize with max from receipts table
            max_row = cursor.execute(
                "SELECT receipt_no FROM receipts WHERE receipt_no LIKE ? ORDER BY receipt_no DESC LIMIT 1",
                (f"LAB-{year}-%",),
            ).fetchone()
            if max_row:
                last_no = int(max_row[0].split("-")[-1])
            else:
                last_no = 0
        new_no = last_no + 1
        cursor.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES(?, ?)",
            (meta_key, str(new_no)),
        )
        conn.commit()
        return f"LAB-{year}-{new_no:06d}"
    except Exception:
        conn.rollback()
        raise


@with_permission('receipts.create')
def create_receipt(data, items, user_id, user=None):
    for i in items:
        total = int(i["total_count"])
        valid = int(i["valid_count"])
        damaged = int(i["damaged_count"])
        rejected = int(i["rejected_count"])
        non_conf = int(i["non_conforming_count"])
        if total != valid + damaged + rejected + non_conf:
            raise ValueError("Invalid item totals")
    with _db.get_conn() as conn:
        no = next_receipt_no(conn)
        cur = conn.execute(
            """INSERT INTO receipts(receipt_no,tx_type_id,sender_org_id,receiver_org_id,
                sender_name,receiver_name,sender_job_title,receiver_job_title,
                auth_doc_no,auth_date,created_at,notes,transport_info,
                additional_comments,status,created_by)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                no,
                data["tx_type_id"],
                data["sender_org_id"],
                data["receiver_org_id"],
                data["sender_name"],
                data["receiver_name"],
                data["sender_job_title"],
                data["receiver_job_title"],
                data["auth_doc_no"],
                data["auth_date"],
                datetime.now().isoformat(timespec="seconds"),
                data["notes"],
                data["transport_info"],
                data["additional_comments"],
                data["status"],
                user_id,
            ),
        )
        rid = cur.lastrowid
        for i in items:
            conn.execute(
                """INSERT INTO receipt_items(receipt_id,sample_type_id,
                    total_count,valid_count,damaged_count,rejected_count,
                    non_conforming_count,transport_condition,notes)
                    VALUES(?,?,?,?,?,?,?,?,?)""",
                (
                    rid,
                    int(i["sample_type_id"]),
                    int(i["total_count"]),
                    int(i["valid_count"]),
                    int(i["damaged_count"]),
                    int(i["rejected_count"]),
                    int(i["non_conforming_count"]),
                    i["transport_condition"],
                    i["notes"],
                ),
            )
    sync_service.enqueue('receipts', rid, 'create', json.dumps({'receipt_no': no}))
    return rid, no


def get_receipt(receipt_id):
    with _db.get_conn() as conn:
        r = conn.execute(
            """SELECT r.*, so.name sender_org, ro.name receiver_org, t.name tx_type
                FROM receipts r
                JOIN organizations so ON so.id=r.sender_org_id
                JOIN organizations ro ON ro.id=r.receiver_org_id
                JOIN transaction_types t ON t.id=r.tx_type_id
                WHERE r.id=?""",
            (receipt_id,),
        ).fetchone()
        if not r:
            return None, [], []
        items = conn.execute(
            """SELECT ri.*, st.name sample_name
                FROM receipt_items ri
                JOIN sample_types st ON st.id=ri.sample_type_id
                WHERE ri.receipt_id=?""",
            (receipt_id,),
        ).fetchall()
        atts = conn.execute(
            "SELECT * FROM attachments WHERE receipt_id=?", (receipt_id,),
        ).fetchall()
    return dict(r), [dict(i) for i in items], [dict(a) for a in atts]


def get_attachment(attachment_id: int) -> dict:
    """Get attachment with hash verification."""
    conn = _db.get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attachments WHERE id = ?", (attachment_id,))
    att = cursor.fetchone()
    if not att:
        return None
    
    # Verify file integrity
    file_path = att["file_path"]
    if os.path.exists(file_path):
        actual_hash = _compute_hash(file_path)
        if actual_hash != att["file_hash"]:
            logger.warning(f"Attachment {attachment_id} hash mismatch: expected {att['file_hash']}, got {actual_hash}")
    else:
        logger.warning(f"Attachment {attachment_id} file missing: {file_path}")
    
    return dict(att)


@with_permission('receipts.update')
def update_receipt(receipt_id, data, items, user=None):
    for i in items:
        total = int(i["total_count"])
        valid = int(i["valid_count"])
        damaged = int(i["damaged_count"])
        rejected = int(i["rejected_count"])
        non_conf = int(i["non_conforming_count"])
        if total != valid + damaged + rejected + non_conf:
            raise ValueError("Invalid item totals")
    with _db.get_conn() as conn:
        conn.execute(
            """UPDATE receipts SET tx_type_id=?,sender_org_id=?,receiver_org_id=?,
                sender_name=?,receiver_name=?,sender_job_title=?,receiver_job_title=?,
                auth_doc_no=?,auth_date=?,notes=?,transport_info=?,
                additional_comments=?,status=? WHERE id=?""",
            (
                data["tx_type_id"],
                data["sender_org_id"],
                data["receiver_org_id"],
                data["sender_name"],
                data["receiver_name"],
                data["sender_job_title"],
                data["receiver_job_title"],
                data["auth_doc_no"],
                data["auth_date"],
                data["notes"],
                data["transport_info"],
                data["additional_comments"],
                data["status"],
                receipt_id,
            ),
        )
        conn.execute("DELETE FROM receipt_items WHERE receipt_id=?", (receipt_id,))
        for i in items:
            conn.execute(
                """INSERT INTO receipt_items(receipt_id,sample_type_id,
                    total_count,valid_count,damaged_count,rejected_count,
                    non_conforming_count,transport_condition,notes)
                    VALUES(?,?,?,?,?,?,?,?,?)""",
                (
                    receipt_id,
                    int(i["sample_type_id"]),
                    int(i["total_count"]),
                    int(i["valid_count"]),
                    int(i["damaged_count"]),
                    int(i["rejected_count"]),
                    int(i["non_conforming_count"]),
                    i["transport_condition"],
                    i["notes"],
                ),
            )
    sync_service.enqueue('receipts', receipt_id, 'update', '')


@with_permission('receipts.delete')
def soft_delete_receipt(receipt_id, user_id=None, user=None):
    now = datetime.now().isoformat(timespec="seconds")
    with _db.get_conn() as conn:
        conn.execute("UPDATE receipts SET deleted_at=? WHERE id=?", (now, receipt_id))
    log_action(user_id, 'soft_delete', f'Receipt {receipt_id}')
    sync_service.enqueue('receipts', receipt_id, 'update', '{"deleted": true}')


@with_permission('receipts.delete')
def hard_delete_receipt(receipt_id, user_id=None, user=None):
    with _db.get_conn() as conn:
        atts = conn.execute(
            "SELECT file_path, thumbnail_path FROM attachments WHERE receipt_id=?",
            (receipt_id,),
        ).fetchall()
        conn.execute("DELETE FROM receipt_items WHERE receipt_id=?", (receipt_id,))
        conn.execute("DELETE FROM attachments WHERE receipt_id=?", (receipt_id,))
        conn.execute("DELETE FROM receipt_history WHERE receipt_id=?", (receipt_id,))
        conn.execute("DELETE FROM receipts WHERE id=?", (receipt_id,))
        conn.execute("DELETE FROM receipts_fts WHERE rowid=?", (receipt_id,))
    for att in atts:
        for p in (att['file_path'], att['thumbnail_path'] if att['thumbnail_path'] else None):
            if p:
                try:
                    Path(p).unlink(missing_ok=True)
                except Exception:
                    pass
    sync_service.enqueue('receipts', receipt_id, 'delete', json.dumps({'receipt_id': receipt_id}))
    log_action(user_id, 'hard_delete', f'Receipt {receipt_id}')


@with_permission('receipts.restore')
def restore_receipt(receipt_id, user_id=None, user=None):
    with _db.get_conn() as conn:
        conn.execute("UPDATE receipts SET deleted_at=NULL WHERE id=?", (receipt_id,))
    log_action(user_id, 'restore', f'Receipt {receipt_id}')


VALID_TRANSITIONS = {
    'Draft': ['Approved', 'Rejected', 'Cancelled'],
    'Approved': ['Archived', 'Cancelled'],
    'Rejected': ['Draft'],
    'Archived': ['Draft'],
    'Cancelled': ['Draft'],
}


def validate_status_transition(from_status, to_status):
    allowed = VALID_TRANSITIONS.get(from_status, [])
    if to_status not in allowed:
        raise ValueError(
            f'Cannot transition from "{from_status}" to "{to_status}". '
            f'Allowed: {", ".join(allowed) if allowed else "none"}',
        )


def _record_receipt_history(conn, receipt_id, field_name, old_value, new_value, changed_by):
    now = datetime.now().isoformat(timespec='seconds')
    conn.execute(
        """INSERT INTO receipt_history(receipt_id, field_name, old_value, new_value, changed_by, changed_at)
           VALUES(?, ?, ?, ?, ?, ?)""",
        (receipt_id, field_name, old_value, new_value, changed_by, now),
    )


@with_permission('receipts.update')
def change_receipt_status(receipt_id, new_status, user_id=None, user=None):
    with _db.get_conn() as conn:
        row = conn.execute(
            "SELECT status, receipt_no FROM receipts WHERE id=?", (receipt_id,),
        ).fetchone()
        if not row:
            raise ValueError(f'Receipt {receipt_id} not found')
        old_status = row['status']
        if old_status == new_status:
            return
        validate_status_transition(old_status, new_status)
        conn.execute("UPDATE receipts SET status=? WHERE id=?", (new_status, receipt_id))
        _record_receipt_history(
            conn, receipt_id, 'status', old_status, new_status, user_id,
        )
    log_action(user_id, 'status_change',
               f'Receipt {receipt_id}: {old_status} → {new_status}')


def approve_receipt(receipt_id, user_id=None):
    return change_receipt_status(receipt_id, 'Approved', user_id)


def reject_receipt(receipt_id, user_id=None):
    return change_receipt_status(receipt_id, 'Rejected', user_id)


def archive_receipt(receipt_id, user_id=None):
    return change_receipt_status(receipt_id, 'Archived', user_id)


def unarchive_receipt(receipt_id, user_id=None):
    return change_receipt_status(receipt_id, 'Draft', user_id)


def cancel_receipt(receipt_id, user_id=None):
    return change_receipt_status(receipt_id, 'Cancelled', user_id)


def batch_update_status(ids, new_status, user_id=None):
    results = []
    for rid in ids:
        try:
            change_receipt_status(rid, new_status, user_id)
            results.append((rid, 'ok', ''))
        except (ValueError, Exception) as e:
            results.append((rid, 'error', str(e)))
    return results


def batch_soft_delete(ids, user_id=None):
    results = []
    for rid in ids:
        try:
            soft_delete_receipt(rid, user_id)
            results.append((rid, 'ok', ''))
        except Exception as e:
            results.append((rid, 'error', str(e)))
    return results


def get_receipt_history(receipt_id):
    with _db.get_conn() as conn:
        rows = conn.execute(
            """SELECT rh.*, u.full_name changed_by_name
               FROM receipt_history rh
               LEFT JOIN users u ON u.id = rh.changed_by
               WHERE rh.receipt_id = ?
               ORDER BY rh.changed_at ASC""",
            (receipt_id,),
        ).fetchall()
    return [dict(r) for r in rows]


@with_permission('receipts.update')
def set_receipt_status(receipt_id, new_status, user_id=None, user=None):
    """Direct status update with transition validation."""
    with _db.get_conn() as conn:
        row = conn.execute(
            "SELECT status FROM receipts WHERE id=?", (receipt_id,),
        ).fetchone()
        if not row:
            raise ValueError(f'Receipt {receipt_id} not found')
        old_status = row['status']
        if old_status == new_status:
            return
        validate_status_transition(old_status, new_status)
        conn.execute("UPDATE receipts SET status=? WHERE id=?", (new_status, receipt_id))
        _record_receipt_history(
            conn, receipt_id, 'status', old_status, new_status, user_id,
        )
    log_action(user_id, 'status_change',
               f'Receipt {receipt_id}: {old_status} → {new_status}')


def list_receipts(
    q="",
    status="",
    tx_type_id=None,
    date_from="",
    date_to="",
    page=1,
    page_size=20,
    *,
    include_deleted=False,
):
    off = (page - 1) * page_size
    where = ["(r.deleted_at IS NULL OR r.deleted_at = '')"]
    params = []
    if include_deleted:
        where = ["1=1"]
    with _db.get_conn() as conn:
        if q:
            fts_terms = q.strip().replace('"', '""').replace('-', ' ')
            fts_q = " OR ".join(f'{t}*' for t in fts_terms.split() if t)
            fts_rows = conn.execute(
                "SELECT rowid FROM receipts_fts WHERE receipts_fts MATCH ? LIMIT ?",
                (fts_q, page_size * 10),
            ).fetchall()
            fts_rowids = [r[0] for r in fts_rows]
            if fts_rowids:
                where.append(f"r.id IN ({','.join(['?'] * len(fts_rowids))})")
                params.extend(fts_rowids)
            else:
                where.append("(r.receipt_no LIKE ? OR so.name LIKE ? OR ro.name LIKE ?)")
                key = f"%{q}%"
                params.extend([key, key, key])
        if status:
            where.append("r.status=?")
            params.append(status)
        if tx_type_id:
            where.append("r.tx_type_id=?")
            params.append(tx_type_id)
        if date_from:
            where.append("r.created_at >= ?")
            params.append(f"{date_from}T00:00:00")
        if date_to:
            where.append("r.created_at <= ?")
            params.append(f"{date_to}T23:59:59")
        clauses = " AND ".join(where)
        total = conn.execute(
            f"""SELECT COUNT(*) c FROM receipts r
                JOIN organizations so ON so.id=r.sender_org_id
                JOIN organizations ro ON ro.id=r.receiver_org_id
                WHERE {clauses}""",
            params,
        ).fetchone()["c"]
        rows = conn.execute(
            f"""SELECT r.*, so.name sender_org, ro.name receiver_org, t.name tx_type
                FROM receipts r
                JOIN organizations so ON so.id=r.sender_org_id
                JOIN organizations ro ON ro.id=r.receiver_org_id
                JOIN transaction_types t ON t.id=r.tx_type_id
                WHERE {clauses}
                ORDER BY r.id DESC LIMIT ? OFFSET ?""",
            [*params, page_size, off],
        ).fetchall()
    return [dict(r) for r in rows], total


def search_receipts(q="", page=1, page_size=20):
    rows, total = list_receipts(q=q, page=page, page_size=page_size)
    return rows
