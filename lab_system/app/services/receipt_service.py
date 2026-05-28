from datetime import datetime
from lab_system.app.database import db as _db


def next_receipt_no():
    year = datetime.now().year
    with _db.get_conn() as conn:
        row = conn.execute(
            "SELECT receipt_no FROM receipts WHERE receipt_no LIKE ? ORDER BY id DESC LIMIT 1",
            (f"LAB-{year}-%",),
        ).fetchone()
    if row:
        seq = int(row["receipt_no"].split("-")[-1]) + 1
    else:
        seq = 1
    return f"LAB-{year}-{seq:06d}"


def create_receipt(data, items, user_id):
    for i in items:
        total = int(i["total_count"])
        valid = int(i["valid_count"])
        damaged = int(i["damaged_count"])
        rejected = int(i["rejected_count"])
        non_conf = int(i["non_conforming_count"])
        if total != valid + damaged + rejected + non_conf:
            raise ValueError("Invalid item totals")
    with _db.get_conn() as conn:
        no = next_receipt_no()
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
            "SELECT * FROM attachments WHERE receipt_id=?", (receipt_id,)
        ).fetchall()
    return dict(r), [dict(i) for i in items], [dict(a) for a in atts]


def update_receipt(receipt_id, data, items):
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


def delete_receipt(receipt_id):
    with _db.get_conn() as conn:
        conn.execute("DELETE FROM receipts WHERE id=?", (receipt_id,))


def set_receipt_status(receipt_id, status):
    with _db.get_conn() as conn:
        conn.execute("UPDATE receipts SET status=? WHERE id=?", (status, receipt_id))


def list_receipts(
    q="",
    status="",
    tx_type_id=None,
    date_from="",
    date_to="",
    page=1,
    page_size=20,
):
    off = (page - 1) * page_size
    where = ["1=1"]
    params = []
    if q:
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
    with _db.get_conn() as conn:
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
            params + [page_size, off],
        ).fetchall()
    return [dict(r) for r in rows], total


def search_receipts(q="", page=1, page_size=20):
    rows, total = list_receipts(q=q, page=page, page_size=page_size)
    return rows
