"""
Platform Observability — Metrics Collection

Phase 6: Observability Platform
Constitution: Principle 50 (Health Scoring)
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Any


class MetricsCollector:
    """Collects and stores metrics for observability."""

    def __init__(self) -> None:
        self._counters: dict[str, int] = defaultdict(int)
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._gauges: dict[str, float] = {}
        self._labels: dict[str, dict[str, str]] = {}
        self._start_time = time.time()
        self._lock = threading.Lock()

    def counter(self, name: str, value: int = 1, labels: dict[str, str] | None = None) -> None:
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] += value

    def histogram(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        with self._lock:
            key = self._make_key(name, labels)
            self._histograms[key].append(value)

    def gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = value

    def get_counter(self, name: str, labels: dict[str, str] | None = None) -> int:
        key = self._make_key(name, labels)
        return self._counters.get(key, 0)

    def get_histogram(self, name: str, labels: dict[str, str] | None = None) -> dict[str, float]:
        key = self._make_key(name, labels)
        values = self._histograms.get(key, [])
        if not values:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0}
        s = sorted(values)
        n = len(s)
        return {
            "count": n, "min": s[0], "max": s[-1],
            "avg": sum(s) / n,
            "p50": s[n // 2],
            "p95": s[int(n * 0.95)] if n > 1 else s[-1],
            "p99": s[int(n * 0.99)] if n > 1 else s[-1],
        }

    def get_gauge(self, name: str, labels: dict[str, str] | None = None) -> float:
        key = self._make_key(name, labels)
        return self._gauges.get(key, 0.0)

    def export(self) -> dict[str, Any]:
        with self._lock:
            return {
                "counters": dict(self._counters),
                "histograms": {k: self.get_histogram(k) for k in self._histograms},
                "gauges": dict(self._gauges),
                "uptime_seconds": time.time() - self._start_time,
            }

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._histograms.clear()
            self._gauges.clear()
            self._start_time = time.time()

    def _make_key(self, name: str, labels: dict[str, str] | None = None) -> str:
        if not labels:
            return name
        return f"{name}|{','.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
