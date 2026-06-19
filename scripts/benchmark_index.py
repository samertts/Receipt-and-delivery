"""
Benchmark query times with and without proposed `receipt_items(receipt_id)` index.
"""

import sqlite3
import time
import sys
from pathlib import Path

DB = sys.argv[1] if len(sys.argv) > 1 else "/tmp/lab_large_dataset.db"

QUERIES = {
    "sample_summary": """
        SELECT st.name AS sample_name,
               SUM(ri.total_count) AS total,
               SUM(ri.valid_count) AS valid
        FROM receipt_items ri
        JOIN receipts r ON r.id = ri.receipt_id
        JOIN sample_types st ON st.id = ri.sample_type_id
        WHERE (r.deleted_at IS NULL OR r.deleted_at = '')
          AND r.created_at >= '2019-01-01'
          AND r.created_at <= '2024-01-01'
        GROUP BY st.name
        ORDER BY total DESC
    """,
    "rejection_statistics": """
        SELECT st.name AS sample_name,
               SUM(ri.rejected_count) AS total_rejected
        FROM receipt_items ri
        JOIN receipts r ON r.id = ri.receipt_id
        JOIN sample_types st ON st.id = ri.sample_type_id
        WHERE (r.deleted_at IS NULL OR r.deleted_at = '')
          AND r.created_at >= '2019-01-01'
          AND r.created_at <= '2024-01-01'
        GROUP BY st.name
        ORDER BY total_rejected DESC
    """,
    "monthly_report_2023": """
        SELECT SUBSTR(r.created_at, 1, 7) AS month, COUNT(*) AS total
        FROM receipts r
        WHERE (r.deleted_at IS NULL OR r.deleted_at = '')
          AND SUBSTR(r.created_at, 1, 4) = '2023'
        GROUP BY month
        ORDER BY month DESC
    """,
    "list_receipts_all_statuses": """
        SELECT r.*, so.name AS sender_org, ro.name AS receiver_org, t.name AS tx_type
        FROM receipts r
        JOIN organizations so ON so.id = r.sender_org_id
        JOIN organizations ro ON ro.id = r.receiver_org_id
        JOIN transaction_types t ON t.id = r.tx_type_id
        WHERE (r.deleted_at IS NULL OR r.deleted_at = '')
          AND r.created_at >= '2019-01-01'
          AND r.created_at <= '2024-01-01'
        ORDER BY r.id DESC
        LIMIT 20
    """,
    "export_all_receipts": """
        SELECT r.*, so.name AS sender_org, ro.name AS receiver_org, t.name AS tx_type
        FROM receipts r
        JOIN organizations so ON so.id = r.sender_org_id
        JOIN organizations ro ON ro.id = r.receiver_org_id
        JOIN transaction_types t ON t.id = r.tx_type_id
        WHERE (r.deleted_at IS NULL OR r.deleted_at = '')
          AND r.created_at >= '2019-01-01'
          AND r.created_at <= '2024-01-01'
        ORDER BY r.id DESC
    """,
}


def run(label, sql, conn):
    times = []
    for _ in range(3):
        t0 = time.perf_counter()
        conn.execute(sql).fetchall()
        t1 = time.perf_counter()
        times.append(t1 - t0)
    return min(times)


print(f"Database: {DB} ({Path(DB).stat().st_size / 1024 / 1024:.1f} MB)")
print(f"{'Query':<40} {'Before (s)':<12}")
print("-" * 52)

conn = sqlite3.connect(DB)
conn.execute("PRAGMA busy_timeout = 5000;")
conn.execute("PRAGMA foreign_keys = ON;")

for label, sql in QUERIES.items():
    t = run(label, sql, conn)
    print(f"{label:<40} {t:<12.4f}")

conn.close()

# Now add the proposed index and re-benchmark
print("\nAdding index idx_receipt_items_receipt_id ...")
conn2 = sqlite3.connect(DB)
conn2.execute("PRAGMA busy_timeout = 5000;")
conn2.execute("PRAGMA foreign_keys = ON;")
t0 = time.perf_counter()
conn2.execute(
    "CREATE INDEX IF NOT EXISTS idx_receipt_items_receipt_id ON receipt_items(receipt_id)"
)
conn2.commit()
t_idx = time.perf_counter() - t0
print(f"Index created in {t_idx:.2f}s")
print(f"\n{'Query':<40} {'After (s)':<12}")
print("-" * 52)

for label, sql in QUERIES.items():
    t = run(label, sql, conn2)
    print(f"{label:<40} {t:<12.4f}")

conn2.close()
