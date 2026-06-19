"""
EXPLAIN QUERY PLAN analysis against the large dataset.
Run with: python scripts/analyze_queries.py [/tmp/lab_large_dataset.db]
"""

import sqlite3
import sys
from pathlib import Path

DB = sys.argv[1] if len(sys.argv) > 1 else "/tmp/lab_large_dataset.db"

QUERIES = {
    "1a. list_receipts (with FTS, COUNT)": """
        SELECT COUNT(*) c
        FROM receipts r
        JOIN organizations so ON so.id = r.sender_org_id
        JOIN organizations ro ON ro.id = r.receiver_org_id
        WHERE (r.deleted_at IS NULL OR r.deleted_at = '')
          AND r.id IN (SELECT rowid FROM receipts_fts WHERE receipts_fts MATCH 'مختبر*')
          AND r.status = 'Approved'
          AND r.tx_type_id = 1
          AND r.created_at >= '2019-01-01'
          AND r.created_at <= '2024-01-01'
    """,
    "1b. list_receipts (with FTS, DATA)": """
        SELECT r.*, so.name AS sender_org, ro.name AS receiver_org, t.name AS tx_type
        FROM receipts r
        JOIN organizations so ON so.id = r.sender_org_id
        JOIN organizations ro ON ro.id = r.receiver_org_id
        JOIN transaction_types t ON t.id = r.tx_type_id
        WHERE (r.deleted_at IS NULL OR r.deleted_at = '')
          AND r.id IN (SELECT rowid FROM receipts_fts WHERE receipts_fts MATCH 'مختبر*')
          AND r.status = 'Approved'
          AND r.tx_type_id = 1
          AND r.created_at >= '2019-01-01'
          AND r.created_at <= '2024-01-01'
        ORDER BY r.id DESC
        LIMIT 20 OFFSET 0
    """,
    "1c. list_receipts (LIKE fallback, COUNT)": """
        SELECT COUNT(*) c
        FROM receipts r
        JOIN organizations so ON so.id = r.sender_org_id
        JOIN organizations ro ON ro.id = r.receiver_org_id
        WHERE (r.deleted_at IS NULL OR r.deleted_at = '')
          AND (r.receipt_no LIKE '%REC%' OR so.name LIKE '%مختبر%' OR ro.name LIKE '%مختبر%')
          AND r.status = 'Approved'
          AND r.tx_type_id = 1
          AND r.created_at >= '2019-01-01'
          AND r.created_at <= '2024-01-01'
    """,
    "1d. list_receipts (LIKE fallback, DATA)": """
        SELECT r.*, so.name AS sender_org, ro.name AS receiver_org, t.name AS tx_type
        FROM receipts r
        JOIN organizations so ON so.id = r.sender_org_id
        JOIN organizations ro ON ro.id = r.receiver_org_id
        JOIN transaction_types t ON t.id = r.tx_type_id
        WHERE (r.deleted_at IS NULL OR r.deleted_at = '')
          AND (r.receipt_no LIKE '%REC%' OR so.name LIKE '%مختبر%' OR ro.name LIKE '%مختبر%')
          AND r.status = 'Approved'
          AND r.tx_type_id = 1
          AND r.created_at >= '2019-01-01'
          AND r.created_at <= '2024-01-01'
        ORDER BY r.id DESC
        LIMIT 20 OFFSET 0
    """,
    "2a. receipt_summary (by status)": """
        SELECT r.status, COUNT(*) AS cnt
        FROM receipts r
        WHERE (r.deleted_at IS NULL OR r.deleted_at = '')
          AND r.created_at >= '2019-01-01'
          AND r.created_at <= '2024-01-01'
        GROUP BY r.status
    """,
    "2b. receipt_summary (by tx_type)": """
        SELECT t.name AS tx_type, COUNT(*) AS cnt
        FROM receipts r
        JOIN transaction_types t ON t.id = r.tx_type_id
        WHERE (r.deleted_at IS NULL OR r.deleted_at = '')
          AND r.created_at >= '2019-01-01'
          AND r.created_at <= '2024-01-01'
        GROUP BY t.name
    """,
    "3. sample_summary": """
        SELECT st.name AS sample_name,
               SUM(ri.total_count) AS total,
               SUM(ri.valid_count) AS valid,
               SUM(ri.damaged_count) AS damaged,
               SUM(ri.rejected_count) AS rejected,
               SUM(ri.non_conforming_count) AS non_conf
        FROM receipt_items ri
        JOIN receipts r ON r.id = ri.receipt_id
        JOIN sample_types st ON st.id = ri.sample_type_id
        WHERE (r.deleted_at IS NULL OR r.deleted_at = '')
          AND r.created_at >= '2019-01-01'
          AND r.created_at <= '2024-01-01'
        GROUP BY st.name
        ORDER BY total DESC
    """,
    "4. export_receipts_csv (no filters, all rows)": """
        SELECT r.*, so.name AS sender_org, ro.name AS receiver_org, t.name AS tx_type
        FROM receipts r
        JOIN organizations so ON so.id = r.sender_org_id
        JOIN organizations ro ON ro.id = r.receiver_org_id
        JOIN transaction_types t ON t.id = r.tx_type_id
        WHERE (r.deleted_at IS NULL OR r.deleted_at = '')
          AND r.created_at >= '2019-01-01'
          AND r.created_at <= '2024-01-01'
        ORDER BY r.id DESC
        LIMIT 999999 OFFSET 0
    """,
    "5. institution_statistics (by sender)": """
        SELECT so.name AS org_name, COUNT(*) AS cnt
        FROM receipts r
        JOIN organizations so ON so.id = r.sender_org_id
        WHERE (r.deleted_at IS NULL OR r.deleted_at = '')
          AND r.created_at >= '2019-01-01'
          AND r.created_at <= '2024-01-01'
        GROUP BY so.name
        ORDER BY cnt DESC
    """,
    "6. daily_report": """
        SELECT DATE(r.created_at) AS day,
               COUNT(*) AS total,
               SUM(CASE WHEN r.status = 'Approved' THEN 1 ELSE 0 END) AS approved,
               SUM(CASE WHEN r.status = 'Rejected' THEN 1 ELSE 0 END) AS rejected
        FROM receipts r
        WHERE (r.deleted_at IS NULL OR r.deleted_at = '')
          AND r.created_at >= '2019-01-01'
          AND r.created_at <= '2024-01-01'
        GROUP BY day
        ORDER BY day DESC
    """,
    "7. monthly_report": """
        SELECT SUBSTR(r.created_at, 1, 7) AS month,
               COUNT(*) AS total,
               SUM(CASE WHEN r.status = 'Approved' THEN 1 ELSE 0 END) AS approved,
               SUM(CASE WHEN r.status = 'Rejected' THEN 1 ELSE 0 END) AS rejected
        FROM receipts r
        WHERE (r.deleted_at IS NULL OR r.deleted_at = '')
          AND SUBSTR(r.created_at, 1, 4) = '2023'
        GROUP BY month
        ORDER BY month DESC
    """,
    "8. rejection_statistics": """
        SELECT st.name AS sample_name,
               SUM(ri.rejected_count) AS total_rejected,
               SUM(ri.total_count) AS total_samples,
               ROUND(CAST(SUM(ri.rejected_count) AS REAL) / NULLIF(SUM(ri.total_count), 0) * 100, 1) AS rejection_pct
        FROM receipt_items ri
        JOIN receipts r ON r.id = ri.receipt_id
        JOIN sample_types st ON st.id = ri.sample_type_id
        WHERE (r.deleted_at IS NULL OR r.deleted_at = '')
          AND r.created_at >= '2019-01-01'
          AND r.created_at <= '2024-01-01'
        GROUP BY st.name
        ORDER BY total_rejected DESC
    """,
}


def fmt_plan(plan_rows):
    lines = []
    for row in plan_rows:
        detail = row["detail"]
        lines.append(f"  {detail}")
    return "\n".join(lines)


conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

print("=" * 72)
print("EXPLAIN QUERY PLAN — Large Dataset Analysis")
print(f"Database: {DB}")
print(f"File size: {Path(DB).stat().st_size / 1024 / 1024:.1f} MB")
print("=" * 72)

for label, sql in QUERIES.items():
    print(f"\n{'─' * 72}")
    print(f"Query: {label}")
    print(f"{'─' * 72}")
    try:
        plan = conn.execute(f"EXPLAIN QUERY PLAN {sql}").fetchall()
        print("EXPLAIN QUERY PLAN:")
        print(fmt_plan(plan))
    except Exception as e:
        print(f"  PLAN ERROR: {e}")

print(f"\n{'=' * 72}")
print("INDEX LIST")
print(f"{'=' * 72}")
indexes = conn.execute(
    "SELECT name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL ORDER BY name"
).fetchall()
for idx in indexes:
    print(f"  {idx['sql']}")

table_info = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()
print("\nROW COUNTS:")
for t in table_info:
    name = t["name"]
    if (
        not name.startswith("sqlite")
        and not name.endswith("_fts")
        and not name.endswith("_fts_data")
        and not name.endswith("_fts_idx")
        and not name.endswith("_fts_config")
        and not name.endswith("_fts_docsize")
    ):
        cnt = conn.execute(f'SELECT COUNT(*) AS c FROM "{name}"').fetchone()["c"]
        print(f"  {name}: {cnt:,}")

conn.close()
