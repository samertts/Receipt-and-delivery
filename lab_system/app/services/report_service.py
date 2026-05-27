import csv
from datetime import datetime
from pathlib import Path

from lab_system.app.database.db import get_conn
from lab_system.app.settings.config import STORAGE_DIR


def receipt_summary(date_from="", date_to="", group_by="day"):
    where = ["1=1"]
    params = []
    if date_from:
        where.append("r.created_at >= ?")
        params.append(f"{date_from}T00:00:00")
    if date_to:
        where.append("r.created_at <= ?")
        params.append(f"{date_to}T23:59:59")

    clauses = " AND ".join(where)
    if group_by == "day":
        date_col = "DATE(r.created_at)"
    elif group_by == "month":
        date_col = "SUBSTR(r.created_at,1,7)"
    elif group_by == "type":
        date_col = "t.name"

    with get_conn() as conn:
        by_status = conn.execute(
            f"""SELECT r.status, COUNT(*) cnt
                FROM receipts r WHERE {clauses}
                GROUP BY r.status""",
            params,
        ).fetchall()

        by_type = conn.execute(
            f"""SELECT t.name tx_type, COUNT(*) cnt
                FROM receipts r
                JOIN transaction_types t ON t.id=r.tx_type_id
                WHERE {clauses}
                GROUP BY t.name""",
            params,
        ).fetchall()

        total = conn.execute(
            f"SELECT COUNT(*) c FROM receipts r WHERE {clauses}", params
        ).fetchone()["c"]

    return {
        "total": total,
        "by_status": {r["status"]: r["cnt"] for r in by_status},
        "by_type": {r["tx_type"]: r["cnt"] for r in by_type},
    }


def sample_summary(date_from="", date_to=""):
    where = ["1=1"]
    params = []
    if date_from:
        where.append("r.created_at >= ?")
        params.append(f"{date_from}T00:00:00")
    if date_to:
        where.append("r.created_at <= ?")
        params.append(f"{date_to}T23:59:59")
    clauses = " AND ".join(where)

    with get_conn() as conn:
        rows = conn.execute(
            f"""SELECT st.name sample_name,
                    SUM(ri.total_count) total,
                    SUM(ri.valid_count) valid,
                    SUM(ri.damaged_count) damaged,
                    SUM(ri.rejected_count) rejected,
                    SUM(ri.non_conforming_count) non_conf
                FROM receipt_items ri
                JOIN receipts r ON r.id=ri.receipt_id
                JOIN sample_types st ON st.id=ri.sample_type_id
                WHERE {clauses}
                GROUP BY st.name
                ORDER BY total DESC""",
            params,
        ).fetchall()
    return [dict(r) for r in rows]


def export_receipts_csv(file_path, q="", status="", date_from="", date_to=""):
    from lab_system.app.services.receipt_service import list_receipts

    rows, _ = list_receipts(
        q=q, status=status, date_from=date_from, date_to=date_to, page=1, page_size=999999
    )
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "رقم الإيصال",
                "النوع",
                "الجهة المرسلة",
                "الجهة المستقبلة",
                "اسم المرسل",
                "اسم المستلم",
                "التاريخ",
                "الحالة",
                "ملاحظات",
            ]
        )
        for r in rows:
            writer.writerow(
                [
                    r["receipt_no"],
                    r["tx_type"],
                    r.get("sender_org", ""),
                    r.get("receiver_org", ""),
                    r.get("sender_name", ""),
                    r.get("receiver_name", ""),
                    r["created_at"],
                    r["status"],
                    r.get("notes", ""),
                ]
            )
    return path
