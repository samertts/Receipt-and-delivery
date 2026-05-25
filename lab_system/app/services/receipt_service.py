from __future__ import annotations

from datetime import datetime
import sqlite3
from typing import Any

from lab_system.app.database.db import get_conn
from lab_system.app.utils.errors import ValidationError

VALID_STATUSES = {'Draft', 'Approved', 'Rejected', 'Archived', 'Cancelled'}


def _now_iso() -> str:
    return datetime.now().isoformat(timespec='seconds')


def validate_receipt_data(data: dict[str, Any], items: list[dict[str, Any]]) -> None:
    required = ['tx_type_id', 'sender_org_id', 'receiver_org_id', 'sender_name', 'receiver_name', 'status']
    for key in required:
        if not data.get(key):
            raise ValidationError(f'الحقل مطلوب: {key}')

    if data['status'] not in VALID_STATUSES:
        raise ValidationError('حالة الإيصال غير صالحة')

    if not items:
        raise ValidationError('يجب إضافة عنصر عينة واحد على الأقل')

    for i, item in enumerate(items, 1):
        for field in ['total_count', 'valid_count', 'damaged_count', 'rejected_count', 'non_conforming_count']:
            if not isinstance(item.get(field), int) or item[field] < 0:
                raise ValidationError(f'قيمة رقمية غير صالحة في العنصر {i}')
        expected = item['valid_count'] + item['damaged_count'] + item['rejected_count'] + item['non_conforming_count']
        if item['total_count'] != expected:
            raise ValidationError(f'مجموع العنصر {i} غير صحيح')


def next_receipt_no(conn: sqlite3.Connection) -> str:
    year = datetime.now().year
    row = conn.execute(
        'SELECT receipt_no FROM receipts WHERE receipt_no LIKE ? ORDER BY id DESC LIMIT 1',
        (f'LAB-{year}-%',),
    ).fetchone()
    seq = int(row['receipt_no'].split('-')[-1]) + 1 if row else 1
    return f'LAB-{year}-{seq:06d}'


def create_receipt(data: dict[str, Any], items: list[dict[str, Any]], user_id: int):
    validate_receipt_data(data, items)
    now = _now_iso()
    with get_conn() as conn:
        try:
            no = next_receipt_no(conn)
            cur = conn.execute(
                '''INSERT INTO receipts(
                    receipt_no,tx_type_id,sender_org_id,receiver_org_id,
                    sender_name,receiver_name,sender_job_title,receiver_job_title,
                    auth_doc_no,auth_date,received_at,created_at,updated_at,
                    notes,status,created_by,updated_by,is_deleted
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)''',
                (
                    no,
                    data['tx_type_id'],
                    data['sender_org_id'],
                    data['receiver_org_id'],
                    data['sender_name'].strip(),
                    data['receiver_name'].strip(),
                    data.get('sender_job_title', '').strip(),
                    data.get('receiver_job_title', '').strip(),
                    data.get('auth_doc_no', '').strip(),
                    data.get('auth_date', ''),
                    data.get('received_at', now),
                    now,
                    now,
                    data.get('notes', ''),
                    data['status'],
                    user_id,
                    user_id,
                ),
            )
            rid = cur.lastrowid
            for i in items:
                conn.execute(
                    '''INSERT INTO receipt_items(
                        receipt_id,sample_type_id,total_count,valid_count,damaged_count,
                        rejected_count,non_conforming_count,transport_condition,notes,
                        created_at,updated_at,is_deleted
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,0)''',
                    (
                        rid,
                        i['sample_type_id'],
                        i['total_count'],
                        i['valid_count'],
                        i['damaged_count'],
                        i['rejected_count'],
                        i['non_conforming_count'],
                        i.get('transport_condition', '').strip(),
                        i.get('notes', '').strip(),
                        now,
                        now,
                    ),
                )
            return rid, no
        except sqlite3.IntegrityError as exc:
            raise ValidationError('فشل حفظ الإيصال بسبب تعارض بيانات (قد يكون رقم مكرر)') from exc


def update_receipt(receipt_id: int, data: dict[str, Any], items: list[dict[str, Any]], user_id: int) -> None:
    validate_receipt_data(data, items)
    now = _now_iso()
    with get_conn() as conn:
        conn.execute(
            '''UPDATE receipts SET tx_type_id=?, sender_org_id=?, receiver_org_id=?, sender_name=?, receiver_name=?,
               sender_job_title=?, receiver_job_title=?, auth_doc_no=?, auth_date=?, received_at=?, notes=?,
               status=?, updated_at=?, updated_by=? WHERE id=? AND is_deleted=0''',
            (
                data['tx_type_id'], data['sender_org_id'], data['receiver_org_id'], data['sender_name'].strip(), data['receiver_name'].strip(),
                data.get('sender_job_title', '').strip(), data.get('receiver_job_title', '').strip(), data.get('auth_doc_no', '').strip(),
                data.get('auth_date', ''), data.get('received_at', now), data.get('notes', ''), data['status'], now, user_id, receipt_id,
            ),
        )
        conn.execute('UPDATE receipt_items SET is_deleted=1, updated_at=? WHERE receipt_id=?', (now, receipt_id))
        for i in items:
            conn.execute(
                '''INSERT INTO receipt_items(receipt_id,sample_type_id,total_count,valid_count,damaged_count,rejected_count,
                non_conforming_count,transport_condition,notes,created_at,updated_at,is_deleted)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,0)''',
                (receipt_id, i['sample_type_id'], i['total_count'], i['valid_count'], i['damaged_count'], i['rejected_count'],
                 i['non_conforming_count'], i.get('transport_condition', ''), i.get('notes', ''), now, now),
            )


def archive_receipt(receipt_id: int, user_id: int) -> None:
    now = _now_iso()
    with get_conn() as conn:
        conn.execute("UPDATE receipts SET status='Archived', archived_at=?, updated_at=?, updated_by=? WHERE id=? AND is_deleted=0", (now, now, user_id, receipt_id))


def soft_delete_receipt(receipt_id: int, user_id: int) -> None:
    now = _now_iso()
    with get_conn() as conn:
        conn.execute('UPDATE receipts SET is_deleted=1, updated_at=?, updated_by=? WHERE id=?', (now, user_id, receipt_id))


def get_receipt(receipt_id: int):
    with get_conn() as conn:
        receipt = conn.execute(
            '''SELECT r.*, so.name sender_org, ro.name receiver_org, t.name tx_type, u.full_name created_by_name
               FROM receipts r
               JOIN organizations so ON so.id=r.sender_org_id
               JOIN organizations ro ON ro.id=r.receiver_org_id
               JOIN transaction_types t ON t.id=r.tx_type_id
               LEFT JOIN users u ON u.id=r.created_by
               WHERE r.id=? AND r.is_deleted=0''',
            (receipt_id,),
        ).fetchone()
        items = conn.execute(
            '''SELECT ri.*, st.name sample_type_name FROM receipt_items ri
               JOIN sample_types st ON st.id=ri.sample_type_id
               WHERE ri.receipt_id=? AND ri.is_deleted=0 ORDER BY ri.id''',
            (receipt_id,),
        ).fetchall()
        return receipt, items


def search_receipts(filters: dict[str, Any] | None = None, page: int = 1, page_size: int = 50):
    filters = filters or {}
    off = (page - 1) * page_size
    clauses = ['r.is_deleted=0']
    params: list[Any] = []

    q = filters.get('q', '').strip()
    if q:
        clauses.append('(r.receipt_no LIKE ? OR so.name LIKE ? OR ro.name LIKE ? OR t.name LIKE ? OR u.full_name LIKE ?)')
        like = f'%{q}%'
        params.extend([like] * 5)

    if filters.get('status'):
        clauses.append('r.status=?')
        params.append(filters['status'])

    where_sql = ' AND '.join(clauses)
    sql = f'''
        SELECT r.id,r.receipt_no,r.received_at,r.status,r.created_at,
               so.name sender_org, ro.name receiver_org, t.name tx_type, u.full_name created_by_name
        FROM receipts r
        JOIN organizations so ON so.id=r.sender_org_id
        JOIN organizations ro ON ro.id=r.receiver_org_id
        JOIN transaction_types t ON t.id=r.tx_type_id
        LEFT JOIN users u ON u.id=r.created_by
        WHERE {where_sql}
        ORDER BY r.created_at DESC
        LIMIT ? OFFSET ?
    '''
    with get_conn() as conn:
        rows = conn.execute(sql, (*params, page_size, off)).fetchall()
        count = conn.execute(
            f'''SELECT COUNT(*) c FROM receipts r
                JOIN organizations so ON so.id=r.sender_org_id
                JOIN organizations ro ON ro.id=r.receiver_org_id
                JOIN transaction_types t ON t.id=r.tx_type_id
                LEFT JOIN users u ON u.id=r.created_by
                WHERE {where_sql}''',
            params,
        ).fetchone()['c']
    return rows, count
