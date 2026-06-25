"""
Performance Service — Low Spec Hardware Optimization

Provides lazy loading, background workers, query optimization,
memory optimization, and startup profiling.
"""

import sqlite3
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any


class PerformanceMonitor:
    """Tracks startup time, RAM usage, and query performance."""

    def __init__(self):
        self._start_time: float | None = None
        self._startup_complete: float | None = None
        self._query_times: list[float] = []
        self._background_tasks: int = 0
        self._worker_pool: ThreadPoolExecutor | None = None

    def start_startup_timer(self):
        self._start_time = time.monotonic()

    def end_startup_timer(self):
        self._startup_complete = time.monotonic()

    @property
    def startup_time_ms(self) -> float:
        if self._start_time is None or self._startup_complete is None:
            return 0.0
        return (self._startup_complete - self._start_time) * 1000

    @property
    def startup_time_sec(self) -> float:
        return self.startup_time_ms / 1000

    def record_query_time(self, duration_ms: float):
        self._query_times.append(duration_ms)
        if len(self._query_times) > 1000:
            self._query_times = self._query_times[-500:]

    @property
    def avg_query_time_ms(self) -> float:
        if not self._query_times:
            return 0.0
        return sum(self._query_times) / len(self._query_times)

    @property
    def p95_query_time_ms(self) -> float:
        if not self._query_times:
            return 0.0
        sorted_times = sorted(self._query_times)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[min(idx, len(sorted_times) - 1)]

    def get_memory_usage_mb(self) -> float:
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return usage.ru_maxrss / 1024
        except (ImportError, AttributeError):
            try:
                import psutil
                process = psutil.Process()
                return process.memory_info().rss / (1024 * 1024)
            except (ImportError, Exception):
                return 0.0

    def get_startup_report(self) -> dict:
        return {
            "startup_time_ms": round(self.startup_time_ms, 2),
            "startup_time_sec": round(self.startup_time_sec, 3),
            "startup_target_met": self.startup_time_sec < 2.0,
            "memory_usage_mb": round(self.get_memory_usage_mb(), 2),
            "memory_target_met": self.get_memory_usage_mb() < 200,
            "avg_query_time_ms": round(self.avg_query_time_ms, 2),
            "p95_query_time_ms": round(self.p95_query_time_ms, 2),
            "total_queries_profiled": len(self._query_times),
        }


class BackgroundWorkerPool:
    """Thread pool for background processing tasks."""

    def __init__(self, max_workers: int = 2):
        self._max_workers = max_workers
        self._executor: ThreadPoolExecutor | None = None
        self._tasks_submitted: int = 0
        self._tasks_completed: int = 0
        self._lock = threading.Lock()

    def start(self):
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=self._max_workers)

    def stop(self):
        if self._executor is not None:
            self._executor.shutdown(wait=False)
            self._executor = None

    def submit(self, fn, *args, **kwargs):
        if self._executor is None:
            self.start()
        with self._lock:
            self._tasks_submitted += 1
        future = self._executor.submit(fn, *args, **kwargs)
        future.add_done_callback(self._on_task_done)
        return future

    def _on_task_done(self, future):
        with self._lock:
            self._tasks_completed += 1

    @property
    def pending_tasks(self) -> int:
        return self._tasks_submitted - self._tasks_completed

    def get_stats(self) -> dict:
        return {
            "max_workers": self._max_workers,
            "tasks_submitted": self._tasks_submitted,
            "tasks_completed": self._tasks_completed,
            "pending_tasks": self.pending_tasks,
        }


class QueryOptimizer:
    """Provides query optimization utilities for SQLite."""

    @staticmethod
    def optimize_db(db_path: str | Path):
        try:
            conn = sqlite3.connect(str(db_path))
            conn.execute("PRAGMA optimize;")
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA cache_size=-8000;")
            conn.execute("PRAGMA temp_store=MEMORY;")
            conn.execute("PRAGMA mmap_size=268435456;")
            conn.close()
        except Exception:
            pass

    @staticmethod
    def get_db_stats(db_path: str | Path) -> dict:
        result = {"pages": 0, "page_size": 0, "size_mb": 0.0, "wal_size_mb": 0.0}
        try:
            conn = sqlite3.connect(str(db_path))
            row = conn.execute("PRAGMA page_count;").fetchone()
            result["pages"] = row[0] if row else 0
            row = conn.execute("PRAGMA page_size;").fetchone()
            result["page_size"] = row[0] if row else 0
            result["size_mb"] = round((result["pages"] * result["page_size"]) / (1024 * 1024), 2)
            conn.close()
            wal_path = Path(str(db_path)) + "-wal"
            if Path(wal_path).exists():
                result["wal_size_mb"] = round(Path(wal_path).stat().st_size / (1024 * 1024), 2)
        except Exception:
            pass
        return result

    @staticmethod
    def explain_query(db_path: str | Path, sql: str) -> list[str]:
        lines = []
        try:
            conn = sqlite3.connect(str(db_path))
            for row in conn.execute(f"EXPLAIN QUERY PLAN {sql}"):
                lines.append(str(row))
            conn.close()
        except Exception:
            pass
        return lines


class MemoryOptimizer:
    """Memory optimization utilities."""

    @staticmethod
    def get_process_memory_mb() -> float:
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return usage.ru_maxrss / 1024
        except (ImportError, AttributeError):
            try:
                import psutil
                process = psutil.Process()
                return process.memory_info().rss / (1024 * 1024)
            except (ImportError, Exception):
                return 0.0

    @staticmethod
    def get_memory_report() -> dict:
        mem_mb = MemoryOptimizer.get_process_memory_mb()
        return {
            "current_mb": round(mem_mb, 2),
            "target_mb": 200,
            "target_met": mem_mb < 200,
            "warning": mem_mb > 150,
            "critical": mem_mb > 200,
        }


class LazyLoader:
    """Deferred module initialization for startup optimization."""

    def __init__(self):
        self._loaded: dict[str, Any] = {}
        self._loading: dict[str, bool] = {}
        self._lock = threading.Lock()

    def register(self, name: str, factory):
        with self._lock:
            self._loaded[name] = None
            self._loading[name] = False
            self._factories = getattr(self, "_factories", {})
            self._factories[name] = factory

    def get(self, name: str) -> Any:
        with self._lock:
            if name in self._loaded and self._loaded[name] is not None:
                return self._loaded[name]
            if self._loading.get(name, False):
                return None
            self._loading[name] = True
        factory = getattr(self, "_factories", {}).get(name)
        if factory:
            try:
                instance = factory()
                with self._lock:
                    self._loaded[name] = instance
                    self._loading[name] = False
                return instance
            except Exception:
                with self._lock:
                    self._loading[name] = False
                return None
        return None

    def is_loaded(self, name: str) -> bool:
        with self._lock:
            return self._loaded.get(name) is not None

    def get_loaded_count(self) -> int:
        with self._lock:
            return sum(1 for v in self._loaded.values() if v is not None)


# Module-level singletons
performance_monitor = PerformanceMonitor()
worker_pool = BackgroundWorkerPool(max_workers=2)
lazy_loader = LazyLoader()
query_optimizer = QueryOptimizer()
memory_optimizer = MemoryOptimizer()


def get_performance_report() -> dict:
    return {
        "startup": performance_monitor.get_startup_report(),
        "workers": worker_pool.get_stats(),
        "memory": memory_optimizer.get_memory_report(),
        "lazy_loader_loaded_count": lazy_loader.get_loaded_count(),
    }
