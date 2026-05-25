from datetime import datetime
import sqlite3
from lab_system.app.database.db import get_conn
from lab_system.app.audit.logger import log_action

VALID_STATUSES = {'Draft', 'Approved', 'Rejected', 'Archived', 'Cancelled'}


def _now() -> str:
    return datetime.now().isoformat(timespec='seconds')


def _validate_item(item: dict) -> None:
    nums = ['total_count', 'valid_count', 'damaged_count', 'rejected_count', 'non_conforming_count']
    for n in nums:
        if int(item.get(n, 0)) < 0:
            raise ValueError('قيمة عددية غير صالحة')
    if int(item['total_count']) != int(item['valid_count']) + int(item['damaged_count']) + int(item['rejected_count']) + int(item['non_conforming_count']):
        raise ValueError('مجموع العينة غير مطابق')


def _validate_receipt(data: dict) -> None:
    required = ['tx_type_id', 'sender_org_id', 'receiver_org_id', 'sender_name', 'receiver_name', 'status']
    for field in required:
        if not data.get(field):
            raise ValueError(f'الحقل مطلوب: {field}')
    if data['status'] not in VALID_STATUSES:
        raise ValueError('حالة الإيصال غير صالحة')


def next_receipt_no(conn=None):
    year = datetime.now().year
    managed = conn is None
    if managed:
        ctx = get_conn()
        conn = ctx.__enter__()
    try:
        conn.execute('BEGIN IMMEDIATE')
        row = conn.execute(
            'SELECT receipt_no FROM receipts WHERE receipt_no LIKE ? ORDER BY id DESC LIMIT 1',
            (f'LAB-{year}-%',),
        ).fetchone()
        seq = int(row['receipt_no'].split('-')[-1]) + 1 if row else 1
        return f'LAB-{year}-{seq:06d}'
    finally:
        if managed:
            ctx.__exit__(None, None, None)


def create_receipt(data, items, user_id):
    _validate_receipt(data)
    if not items:
        raise ValueError('يجب إضافة عنصر عينة واحد على الأقل')
    for i in items:
        _validate_item(i)

    with get_conn() as conn:
        try:
            conn.execute('BEGIN IMMEDIATE')
            no = next_receipt_no(conn)
            now = _now()
            cur = conn.execute(
                '''INSERT INTO receipts(receipt_no,tx_type_id,sender_org_id,receiver_org_id,sender_name,receiver_name,sender_job_title,receiver_job_title,auth_doc_no,auth_date,received_at,created_at,updated_at,archived_at,notes,transport_info,additional_comments,status,created_by,updated_by,is_deleted)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)''',
                (
                    no, data['tx_type_id'], data['sender_org_id'], data['receiver_org_id'],
                    data['sender_name'], data['receiver_name'], data.get('sender_job_title', ''), data.get('receiver_job_title', ''),
                    data.get('auth_doc_no', ''), data.get('auth_date', ''), data.get('received_at', now),
                    now, now, '', data.get('notes', ''), data.get('transport_info', ''), data.get('additional_comments', ''),
                    data['status'], user_id, user_id,
                ),
            )
            rid = cur.lastrowid
            for i in items:
                conn.execute(
                    '''INSERT INTO receipt_items(receipt_id,sample_type_id,total_count,valid_count,damaged_count,rejected_count,non_conforming_count,transport_condition,notes,created_at,updated_at,is_deleted)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,0)''',
                    (rid, i['sample_type_id'], i['total_count'], i['valid_count'], i['damaged_count'], i['rejected_count'], i['non_conforming_count'], i.get('transport_condition', ''), i.get('notes', ''), now, now),
                )
            log_action(user_id, 'receipt_created', f'receipt_id={rid};receipt_no={no}')
            return rid, no
        except sqlite3.Error as exc:
            conn.rollback()
            log_action(user_id, 'receipt_save_failed', str(exc))
            raise


def update_receipt(receipt_id, data, items, user_id):
    _validate_receipt(data)
    for i in items:
        _validate_item(i)
    now = _now()
    with get_conn() as conn:
        try:
            conn.execute('BEGIN IMMEDIATE')
            conn.execute(
                '''UPDATE receipts SET tx_type_id=?,sender_org_id=?,receiver_org_id=?,sender_name=?,receiver_name=?,sender_job_title=?,receiver_job_title=?,auth_doc_no=?,auth_date=?,received_at=?,notes=?,transport_info=?,additional_comments=?,status=?,updated_at=?,updated_by=? WHERE id=? AND is_deleted=0''',
                (data['tx_type_id'], data['sender_org_id'], data['receiver_org_id'], data['sender_name'], data['receiver_name'], data.get('sender_job_title', ''), data.get('receiver_job_title', ''), data.get('auth_doc_no', ''), data.get('auth_date', ''), data.get('received_at', now), data.get('notes', ''), data.get('transport_info', ''), data.get('additional_comments', ''), data['status'], now, user_id, receipt_id),
            )
            conn.execute('DELETE FROM receipt_items WHERE receipt_id=?', (receipt_id,))
            for i in items:
                conn.execute(
                    '''INSERT INTO receipt_items(receipt_id,sample_type_id,total_count,valid_count,damaged_count,rejected_count,non_conforming_count,transport_condition,notes,created_at,updated_at,is_deleted)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,0)''',
                    (receipt_id, i['sample_type_id'], i['total_count'], i['valid_count'], i['damaged_count'], i['rejected_count'], i['non_conforming_count'], i.get('transport_condition', ''), i.get('notes', ''), now, now),
                )
            log_action(user_id, 'receipt_updated', f'receipt_id={receipt_id}')
        except sqlite3.Error as exc:
            conn.rollback()
            log_action(user_id, 'receipt_update_failed', str(exc))
            raise


def get_receipt_details(receipt_id):
    with get_conn() as conn:
        header = conn.execute('SELECT * FROM receipts WHERE id=? AND is_deleted=0', (receipt_id,)).fetchone()
        items = conn.execute('SELECT * FROM receipt_items WHERE receipt_id=? AND is_deleted=0 ORDER BY id', (receipt_id,)).fetchall()
    return header, items


def archive_receipt(receipt_id, user_id):
    with get_conn() as conn:
        conn.execute("UPDATE receipts SET status='Archived', archived_at=?, updated_at=?, updated_by=? WHERE id=? AND is_deleted=0", (_now(), _now(), user_id, receipt_id))
    log_action(user_id, 'receipt_archived', f'receipt_id={receipt_id}')


def soft_delete_receipt(receipt_id, user_id):
    with get_conn() as conn:
        conn.execute('UPDATE receipts SET is_deleted=1, updated_at=?, updated_by=? WHERE id=?', (_now(), user_id, receipt_id))
    log_action(user_id, 'receipt_soft_deleted', f'receipt_id={receipt_id}')


def search_receipts(q='', status='', page=1, page_size=50):
    off = (page - 1) * page_size
    key = f'%{q}%'
    where = ["r.is_deleted=0", "(r.receipt_no LIKE ? OR so.name LIKE ? OR ro.name LIKE ? OR t.name LIKE ? OR u.full_name LIKE ?)"]
    params = [key, key, key, key, key]
    if status:
        where.append('r.status=?')
        params.append(status)
    sql = f'''SELECT r.id,r.receipt_no,r.created_at,r.status,so.name sender_org,ro.name receiver_org,t.name tx_type,COALESCE(u.full_name,'') created_user
        FROM receipts r
        JOIN organizations so ON so.id=r.sender_org_id
        JOIN organizations ro ON ro.id=r.receiver_org_id
        JOIN transaction_types t ON t.id=r.tx_type_id
        LEFT JOIN users u ON u.id=r.created_by
        WHERE {' AND '.join(where)}
        ORDER BY r.id DESC LIMIT ? OFFSET ?'''
    params.extend([page_size, off])
    with get_conn() as conn:
        return conn.execute(sql, params).fetchall()
