"""
Performance Benchmark Suite for Receipt-and-delivery.

Measures:
  - Database creation with N receipts
  - FTS search latency
  - Report generation time
  - Backup duration
  - Database file size
  - Query performance

Usage:
    python3 scripts/performance_benchmark.py
"""

import json
import os
import sqlite3
import sys
import time
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BENCH_DIR = Path(__file__).resolve().parent.parent / 'baseline' / 'benchmarks'
BENCH_DIR.mkdir(parents=True, exist_ok=True)


class Benchmark:
    def __init__(self, label: str):
        self.label = label
        self.results = {}

    def measure(self, name: str, fn, warmup: int = 1, runs: int = 3):
        for _ in range(warmup):
            fn()
        times = []
        for _ in range(runs):
            t0 = time.perf_counter()
            fn()
            t1 = time.perf_counter()
            times.append(t1 - t0)
        self.results[name] = {
            'min_s': round(min(times), 4),
            'avg_s': round(sum(times) / len(times), 4),
            'max_s': round(max(times), 4),
            'runs': runs,
        }
        print(f'  {name}: avg={self.results[name]["avg_s"]:.4f}s  min={self.results[name]["min_s"]:.4f}s')

    def report(self) -> dict:
        return {'label': self.label, 'metrics': self.results}


def create_database(db_path: str, num_receipts: int, num_orgs: int = 50):
    """Create a test database with N receipts."""
    from lab_system.app.database import db as _db
    from lab_system.app.auth.security import hash_password

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(_db.SCHEMA)
    cur = conn.cursor()

    # Organizations
    org_ids = []
    for i in range(num_orgs):
        cur.execute(
            "INSERT INTO organizations(name,code,org_type,governorate,status) VALUES(?,?,?,?,?)",
            (f"Org_{i:04d}", f"O-{i:05d}", "Lab", "Baghdad", "Active"),
        )
        org_ids.append(cur.lastrowid)

    # Transaction types
    for name in ["استلام", "تسليم", "إعادة", "تحويل داخلي"]:
        cur.execute("INSERT OR IGNORE INTO transaction_types(name) VALUES(?)", (name,))
    tx_ids = [r[0] for r in cur.execute("SELECT id FROM transaction_types").fetchall()]

    # Sample types
    for name in ["دم كامل", "مصل", "بول", "مسحة أنف", "بلغم", "براز", "سائل نخاعي", "عينة نسيج"]:
        cur.execute("INSERT OR IGNORE INTO sample_types(name,category,status) VALUES(?,?,'Active')",
                    (name, "General"))
    st_ids = [r[0] for r in cur.execute("SELECT id FROM sample_types").fetchall()]

    # Admin user
    cur.execute(
        "INSERT INTO users(full_name,username,password_hash,role,status,password_changed_at) VALUES(?,?,?,?,?,?)",
        ("Admin", "admin", hash_password("Admin@123"), "Admin", "Active",
         datetime.now().isoformat(timespec='seconds')),
    )
    admin_id = cur.lastrowid

    import random
    random.seed(42)
    batch_size = 500
    for batch_start in range(0, num_receipts, batch_size):
        batch_end = min(batch_start + batch_size, num_receipts)
        items_batch = []
        for r in range(batch_start, batch_end):
            ts = datetime(2020, 1, 1, 0, 0, 0).isoformat(timespec='seconds')
            receipt_no = f"BENCH-{r+1:07d}"
            tx = random.choice(tx_ids)
            snd = random.choice(org_ids)
            rcv = random.choice(org_ids)
            cur.execute(
                "INSERT INTO receipts(receipt_no,tx_type_id,sender_org_id,receiver_org_id,sender_name,receiver_name,created_at,status,created_by) VALUES(?,?,?,?,?,?,?,?,?)",
                (receipt_no, tx, snd, rcv, "Sender", "Receiver", ts,
                 random.choice(["Draft", "Approved", "Approved", "Rejected", "Archived"]), admin_id),
            )
            rid = cur.lastrowid
            for _ in range(random.randint(3, 8)):
                st = random.choice(st_ids)
                total = random.randint(10, 500)
                valid = random.randint(int(total * 0.7), total)
                damaged = random.randint(0, total - valid)
                items_batch.append((rid, st, total, valid, damaged,
                                    random.randint(0, max(0, total - valid - damaged)),
                                    random.randint(0, max(0, total - valid - damaged))))
        cur.executemany(
            "INSERT INTO receipt_items(receipt_id,sample_type_id,total_count,valid_count,damaged_count,rejected_count,non_conforming_count) VALUES(?,?,?,?,?,?,?)",
            items_batch,
        )
        conn.commit()

    # Rebuild FTS
    cur.execute("DELETE FROM receipts_fts;")
    cur.execute("INSERT INTO receipts_fts(rowid, receipt_no, sender_name, receiver_name) SELECT id, receipt_no, sender_name, receiver_name FROM receipts WHERE deleted_at IS NULL OR deleted_at = ''")
    cur.execute("DELETE FROM organizations_fts;")
    cur.execute("INSERT INTO organizations_fts(rowid, name, code) SELECT id, name, code FROM organizations")
    conn.commit()
    conn.close()


def run_benchmarks_for_size(num_receipts: int) -> dict:
    """Run all benchmarks for a given dataset size."""
    label = f"{num_receipts}_receipts"
    print(f"\n{'='*60}")
    print(f"BENCHMARK: {label}")
    print(f"{'='*60}")

    db_path = str(BENCH_DIR / f"bench_{num_receipts}.db")
    results = {'dataset_size': num_receipts, 'db_path': db_path}

    # 1. Database creation time
    print("\n[1] Database Creation:")
    t0 = time.perf_counter()
    if not Path(db_path).exists():
        create_database(db_path, num_receipts)
    t1 = time.perf_counter()
    creation_time = t1 - t0
    results['creation_time_s'] = round(creation_time, 2)
    print(f"  Creation time: {creation_time:.2f}s")

    # Get DB file size
    db_size_mb = Path(db_path).stat().st_size / (1024 * 1024)
    results['db_size_mb'] = round(db_size_mb, 1)
    print(f"  DB file size: {db_size_mb:.1f} MB")

    # Count actual rows
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    actual_receipts = conn.execute("SELECT COUNT(*) c FROM receipts").fetchone()['c']
    actual_items = conn.execute("SELECT COUNT(*) c FROM receipt_items").fetchone()['c']
    conn.close()
    results['actual_receipts'] = actual_receipts
    results['actual_items'] = actual_items
    print(f"  Receipts: {actual_receipts}, Items: {actual_items}")

    # 2. Query benchmarks (run 3 times, take min)
    print("\n[2] Query Performance:")
    bm = Benchmark(label)

    def make_query(sql, params=None):
        def _run():
            c = sqlite3.connect(db_path)
            c.row_factory = sqlite3.Row
            c.execute("PRAGMA foreign_keys = ON;")
            if params:
                c.execute(sql, params).fetchall()
            else:
                c.execute(sql).fetchall()
            c.close()
        return _run

    # List receipts (paginated)
    bm.measure("list_receipts_page1", make_query("""
        SELECT r.*, so.name sender_org, ro.name receiver_org, t.name tx_type
        FROM receipts r
        JOIN organizations so ON so.id=r.sender_org_id
        JOIN organizations ro ON ro.id=r.receiver_org_id
        JOIN transaction_types t ON t.id=r.tx_type_id
        WHERE (r.deleted_at IS NULL OR r.deleted_at = '')
        ORDER BY r.id DESC LIMIT 20 OFFSET 0
    """))

    # FTS search
    bm.measure("fts_search", make_query("""
        SELECT rowid FROM receipts_fts WHERE receipts_fts MATCH ? LIMIT 20
    """, ("استلام*",)))

    # Report: monthly summary
    bm.measure("monthly_report", make_query("""
        SELECT SUBSTR(r.created_at,1,7) month, COUNT(*) total
        FROM receipts r WHERE (r.deleted_at IS NULL OR r.deleted_at = '')
        GROUP BY month ORDER BY month DESC
    """))

    # Report: sample summary
    bm.measure("sample_summary", make_query("""
        SELECT st.name, SUM(ri.total_count) total
        FROM receipt_items ri
        JOIN receipts r ON r.id=ri.receipt_id
        JOIN sample_types st ON st.id=ri.sample_type_id
        WHERE (r.deleted_at IS NULL OR r.deleted_at = '')
        GROUP BY st.name ORDER BY total DESC
    """))

    # Report: institution statistics
    bm.measure("institution_stats", make_query("""
        SELECT so.name org, COUNT(*) total
        FROM receipts r
        JOIN organizations so ON so.id=r.sender_org_id
        WHERE (r.deleted_at IS NULL OR r.deleted_at = '')
        GROUP BY so.name ORDER BY total DESC LIMIT 10
    """))

    # Full export (all receipts)
    bm.measure("full_export", make_query("""
        SELECT r.*, so.name sender_org, ro.name receiver_org, t.name tx_type
        FROM receipts r
        JOIN organizations so ON so.id=r.sender_org_id
        JOIN organizations ro ON ro.id=r.receiver_org_id
        JOIN transaction_types t ON t.id=r.tx_type_id
        WHERE (r.deleted_at IS NULL OR r.deleted_at = '')
        ORDER BY r.id DESC
    """))

    # Filter by status
    bm.measure("filter_by_status", make_query("""
        SELECT COUNT(*) c FROM receipts WHERE status=? AND (deleted_at IS NULL OR deleted_at='')
    """, ("Approved",)))

    # Dashboard aggregate
    bm.measure("dashboard_counts", make_query("""
        SELECT
            COUNT(*) total,
            SUM(CASE WHEN status='Draft' THEN 1 ELSE 0 END) draft,
            SUM(CASE WHEN status='Approved' THEN 1 ELSE 0 END) approved,
            SUM(CASE WHEN status='Rejected' THEN 1 ELSE 0 END) rejected,
            SUM(CASE WHEN status='Archived' THEN 1 ELSE 0 END) archived
        FROM receipts WHERE (deleted_at IS NULL OR deleted_at = '')
    """))

    results['query_benchmarks'] = bm.results

    # 3. Backup benchmark
    print("\n[3] Backup Performance:")
    backup_path = str(BENCH_DIR / f"bench_{num_receipts}_backup.db")
    bm2 = Benchmark(label + "_backup")

    def make_backup():
        import shutil
        shutil.copy2(db_path, backup_path)

    bm2.measure("file_copy_backup", make_backup)
    results['backup_benchmarks'] = bm2.results
    # Cleanup backup
    Path(backup_path).unlink(missing_ok=True)

    # 4. FTS search variations
    print("\n[4] FTS Search Variations:")
    bm3 = Benchmark(label + "_fts")

    for term in ["مصل", "دم", "BENCH", "Org"]:
        bm3.measure(f"fts_{term}", make_query(
            "SELECT rowid FROM receipts_fts WHERE receipts_fts MATCH ? LIMIT 10",
            (f"{term}*",),
        ))
    results['fts_benchmarks'] = bm3.results

    return results


def main():
    print("PERFORMANCE BENCHMARK SUITE")
    print("=" * 60)

    all_results = {}
    sizes = [1000, 10000, 100000]

    for size in sizes:
        results = run_benchmarks_for_size(size)
        all_results[str(size)] = results

    # Write final report
    report_path = BENCH_DIR / 'performance_baseline.json'
    with open(report_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n{'='*60}")
    print(f"Benchmark report written to {report_path}")

    # Summary table
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"{'Metric':<35} {'1K':<12} {'10K':<12} {'100K':<12}")
    print(f"{'-'*71}")
    for metric in ['db_size_mb', 'creation_time_s', 'actual_receipts', 'actual_items']:
        v1 = all_results.get('1000', {}).get(metric, '-')
        v2 = all_results.get('10000', {}).get(metric, '-')
        v3 = all_results.get('100000', {}).get(metric, '-')
        print(f"{metric:<35} {str(v1):<12} {str(v2):<12} {str(v3):<12}")

    for q in ['list_receipts_page1', 'fts_search', 'monthly_report', 'sample_summary', 'full_export', 'filter_by_status']:
        v1 = all_results.get('1000', {}).get('query_benchmarks', {}).get(q, {}).get('avg_s', '-')
        v2 = all_results.get('10000', {}).get('query_benchmarks', {}).get(q, {}).get('avg_s', '-')
        v3 = all_results.get('100000', {}).get('query_benchmarks', {}).get(q, {}).get('avg_s', '-')
        print(f"{'query:'+q:<35} {str(v1):<12} {str(v2):<12} {str(v3):<12}")

    print(f"\nDone.")


if __name__ == "__main__":
    main()
