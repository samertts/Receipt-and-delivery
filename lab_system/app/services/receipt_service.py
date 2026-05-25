from datetime import datetime
from lab_system.app.database.db import get_conn


def next_receipt_no():
    year = datetime.now().year
    with get_conn() as conn:
        row = conn.execute('SELECT receipt_no FROM receipts WHERE receipt_no LIKE ? ORDER BY id DESC LIMIT 1', (f'LAB-{year}-%',)).fetchone()
    seq = int(row['receipt_no'].split('-')[-1]) + 1 if row else 1
    return f'LAB-{year}-{seq:06d}'


def create_receipt(data, items, user_id):
    for i in items:
        if i['total_count'] != i['valid_count'] + i['damaged_count'] + i['rejected_count'] + i['non_conforming_count']:
            raise ValueError('Invalid item totals')
    with get_conn() as conn:
        no = next_receipt_no()
        cur = conn.execute('''INSERT INTO receipts(receipt_no,tx_type_id,sender_org_id,receiver_org_id,sender_name,receiver_name,sender_job_title,receiver_job_title,auth_doc_no,auth_date,created_at,notes,transport_info,additional_comments,status,created_by)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (no, data['tx_type_id'], data['sender_org_id'], data['receiver_org_id'], data['sender_name'], data['receiver_name'], data['sender_job_title'], data['receiver_job_title'], data['auth_doc_no'], data['auth_date'], datetime.now().isoformat(timespec='seconds'), data['notes'], data['transport_info'], data['additional_comments'], data['status'], user_id))
        rid = cur.lastrowid
        for i in items:
            conn.execute('''INSERT INTO receipt_items(receipt_id,sample_type_id,total_count,valid_count,damaged_count,rejected_count,non_conforming_count,transport_condition,notes)
                VALUES(?,?,?,?,?,?,?,?,?)''', (rid, i['sample_type_id'], i['total_count'], i['valid_count'], i['damaged_count'], i['rejected_count'], i['non_conforming_count'], i['transport_condition'], i['notes']))
    return rid, no


def search_receipts(q='', page=1, page_size=20):
    off = (page - 1) * page_size
    key = f'%{q}%'
    with get_conn() as conn:
        return conn.execute('''SELECT r.*, so.name sender_org, ro.name receiver_org, t.name tx_type
        FROM receipts r
        JOIN organizations so ON so.id=r.sender_org_id
        JOIN organizations ro ON ro.id=r.receiver_org_id
        JOIN transaction_types t ON t.id=r.tx_type_id
        WHERE r.receipt_no LIKE ? OR so.name LIKE ? OR ro.name LIKE ?
        ORDER BY r.id DESC LIMIT ? OFFSET ?''', (key, key, key, page_size, off)).fetchall()
