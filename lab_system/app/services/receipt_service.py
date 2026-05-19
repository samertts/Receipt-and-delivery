from datetime import datetime
from lab_system.app.database.db import get_conn

def next_receipt_no():
    year = datetime.now().year
    with get_conn() as conn:
        row = conn.execute("SELECT receipt_no FROM receipts WHERE receipt_no LIKE ? ORDER BY id DESC LIMIT 1",(f'LAB-{year}-%',)).fetchone()
    seq = int(row['receipt_no'].split('-')[-1]) + 1 if row else 1
    return f'LAB-{year}-{seq:06d}'

def create_receipt(data, items, user_id):
    for i in items:
        if i['total_count'] != i['valid_count'] + i['damaged_count'] + i['rejected_count'] + i['non_conforming_count']:
            raise ValueError('Invalid item totals')
    with get_conn() as conn:
        cur = conn.execute('''INSERT INTO receipts(receipt_no,tx_type,sender_org_id,receiver_org_id,sender_name,receiver_name,auth_doc_no,auth_date,created_at,notes,status,created_by)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',
            (next_receipt_no(), data['tx_type'], data['sender_org_id'], data['receiver_org_id'], data['sender_name'], data['receiver_name'], data['auth_doc_no'], data['auth_date'], datetime.now().isoformat(timespec='seconds'), data['notes'], data['status'], user_id))
        rid = cur.lastrowid
        for i in items:
            conn.execute('''INSERT INTO receipt_items(receipt_id,sample_type,total_count,valid_count,damaged_count,rejected_count,non_conforming_count,transport_condition,notes)
                VALUES(?,?,?,?,?,?,?,?,?)''', (rid, i['sample_type'], i['total_count'], i['valid_count'], i['damaged_count'], i['rejected_count'], i['non_conforming_count'], i['transport_condition'], i['notes']))
    return rid
