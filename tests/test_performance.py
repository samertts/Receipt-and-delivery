"""Performance tests — Benchmarks for critical operations."""

import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


ADMIN_USER = {"id": 1, "username": "admin", "role": "Admin", "status": "Active"}


class TestPerformance:
    """Performance benchmarks — must complete within thresholds."""

    def test_database_schema_creation_time(self):
        from lab_system.app.database.db import SCHEMA

        start = time.perf_counter()
        db_path = Path(tempfile.mkdtemp()) / "perf.db"
        conn = sqlite3.connect(str(db_path))
        conn.executescript(SCHEMA)
        conn.commit()
        conn.close()
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0, f"Schema creation took {elapsed:.2f}s (threshold: 2.0s)"

    def test_concurrent_connections(self, fresh_db):
        import threading

        errors = []

        def worker():
            try:
                conn = sqlite3.connect(str(fresh_db))
                conn.execute("SELECT 1")
                conn.close()
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=worker) for _ in range(10)]
        start = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        elapsed = time.perf_counter() - start

        assert len(errors) == 0, f"Errors: {errors}"
        assert elapsed < 5.0, f"10 concurrent connections took {elapsed:.2f}s"

    def test_query_performance_simple(self, fresh_db, seed_data):
        conn = sqlite3.connect(str(fresh_db))
        start = time.perf_counter()
        for _ in range(100):
            conn.execute("SELECT * FROM users").fetchall()
        elapsed = time.perf_counter() - start
        conn.close()
        assert elapsed < 1.0, f"100 queries took {elapsed:.2f}s (threshold: 1.0s)"

    def test_insert_performance(self, fresh_db):
        conn = sqlite3.connect(str(fresh_db))
        start = time.perf_counter()
        for i in range(1000):
            conn.execute(
                "INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)",
                (f"perf.key.{i}", f"perf.value.{i}"),
            )
        conn.commit()
        elapsed = time.perf_counter() - start
        conn.close()
        assert elapsed < 2.0, f"1000 inserts took {elapsed:.2f}s (threshold: 2.0s)"

    def test_dashboard_stats_performance(self, fresh_db, seed_data):
        from lab_system.app.services.dashboard_service import DashboardService

        svc = DashboardService()
        start = time.perf_counter()
        for _ in range(50):
            svc.get_stats()
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0, f"50 dashboard stats took {elapsed:.2f}s"

    def test_large_dataset_query(self, fresh_db):
        conn = sqlite3.connect(str(fresh_db))
        # Insert large dataset
        for i in range(5000):
            conn.execute(
                "INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)",
                (f"large.{i}", f"value.{i}"),
            )
        conn.commit()

        start = time.perf_counter()
        conn.execute("SELECT COUNT(*) FROM settings").fetchone()
        elapsed = time.perf_counter() - start
        conn.close()
        assert elapsed < 0.5, f"Count on 5000 rows took {elapsed:.3f}s"

    def test_memory_usage_reasonable(self):
        import sys
        data = [dict(key=f"k{i}", value=f"v{i}") for i in range(1000)]
        final = sys.getsizeof(data)
        # Should not use excessive memory
        assert final < 10_000_000, f"Memory usage: {final} bytes"
