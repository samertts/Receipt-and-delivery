"""
Platform Observability — Performance Analytics

Phase 6: Observability Platform
Constitution: Principle 50 (Health Scoring)
"""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any


class PerformanceAnalytics:
    """Analyzes performance metrics for operational intelligence."""

    def __init__(self) -> None:
        self._measurements: list[dict[str, Any]] = []
        self._start_time = time.time()

    def record(self, operation: str, duration_ms: float, **tags: str) -> None:
        """Record a performance measurement."""
        self._measurements.append({
            "operation": operation,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat(),
            "tags": tags,
        })

    def record_batch(self, measurements: list[dict[str, Any]]) -> int:
        """Record multiple measurements."""
        self._measurements.extend(measurements)
        return len(measurements)

    def get_operation_stats(self, operation: str, hours: int = 24) -> dict[str, Any]:
        """Get statistics for a specific operation."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        durations: list[float] = []
        for m in self._measurements:
            if m.get("operation") == operation:
                try:
                    if datetime.fromisoformat(m.get("timestamp", "")) >= cutoff:
                        durations.append(m.get("duration_ms", 0))
                except (ValueError, TypeError):
                    pass

        if not durations:
            return {"operation": operation, "count": 0}

        s = sorted(durations)
        n = len(s)
        return {
            "operation": operation,
            "count": n,
            "min": s[0],
            "max": s[-1],
            "avg": sum(s) / n,
            "p50": s[n // 2],
            "p95": s[int(n * 0.95)] if n > 1 else s[-1],
            "p99": s[int(n * 0.99)] if n > 1 else s[-1],
        }

    def get_slowest_operations(self, limit: int = 10, hours: int = 24) -> list[dict[str, Any]]:
        """Get the slowest operations."""
        stats: dict[str, list[float]] = defaultdict(list)
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        for m in self._measurements:
            try:
                if datetime.fromisoformat(m.get("timestamp", "")) >= cutoff:
                    stats[m.get("operation", "unknown")].append(m.get("duration_ms", 0))
            except (ValueError, TypeError):
                pass

        result: list[dict[str, Any]] = []
        for op, durations in stats.items():
            s = sorted(durations)
            n = len(s)
            result.append({
                "operation": op,
                "count": n,
                "avg_ms": sum(s) / n,
                "p95_ms": s[int(n * 0.95)] if n > 1 else s[-1],
            })

        return sorted(result, key=lambda x: -x["avg_ms"])[:limit]

    def get_throughput(self, hours: int = 24) -> dict[str, int]:
        """Get operation throughput."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        throughput: dict[str, int] = defaultdict(int)
        for m in self._measurements:
            try:
                if datetime.fromisoformat(m.get("timestamp", "")) >= cutoff:
                    throughput[m.get("operation", "unknown")] += 1
            except (ValueError, TypeError):
                pass
        return dict(throughput)

    def get_performance_trend(self, operation: str, hours: int = 24, bucket_minutes: int = 60) -> list[dict[str, Any]]:
        """Get performance trend for an operation."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        buckets: dict[str, list[float]] = defaultdict(list)
        for m in self._measurements:
            if m.get("operation") == operation:
                try:
                    ts = datetime.fromisoformat(m.get("timestamp", ""))
                    if ts >= cutoff:
                        bucket_key = ts.strftime("%Y-%m-%d-%H") + f":{(ts.minute // bucket_minutes) * bucket_minutes:02d}"
                        buckets[bucket_key].append(m.get("duration_ms", 0))
                except (ValueError, TypeError):
                    pass

        trend: list[dict[str, Any]] = []
        for bucket, durations in sorted(buckets.items()):
            n = len(durations)
            trend.append({
                "period": bucket,
                "count": n,
                "avg_ms": sum(durations) / n,
                "max_ms": max(durations),
            })
        return trend

    def detect_slowdowns(self, threshold_multiplier: float = 2.0) -> list[dict[str, Any]]:
        """Detect performance slowdowns."""
        stats: dict[str, list[float]] = defaultdict(list)
        for m in self._measurements:
            stats[m.get("operation", "unknown")].append(m.get("duration_ms", 0))

        slowdowns: list[dict[str, Any]] = []
        for op, durations in stats.items():
            if len(durations) < 10:
                continue
            recent = durations[-10:]
            older = durations[:-10]
            if not older:
                continue
            recent_avg = sum(recent) / len(recent)
            older_avg = sum(older) / len(older)
            if older_avg > 0 and recent_avg > older_avg * threshold_multiplier:
                slowdowns.append({
                    "operation": op,
                    "recent_avg_ms": recent_avg,
                    "baseline_avg_ms": older_avg,
                    "degradation_factor": recent_avg / older_avg,
                })

        return sorted(slowdowns, key=lambda x: -x["degradation_factor"])

    def get_summary(self, hours: int = 24) -> dict[str, Any]:
        """Get performance summary."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        total = 0
        operations: dict[str, int] = defaultdict(int)
        for m in self._measurements:
            try:
                if datetime.fromisoformat(m.get("timestamp", "")) >= cutoff:
                    total += 1
                    operations[m.get("operation", "unknown")] += 1
            except (ValueError, TypeError):
                pass
        return {
            "total_measurements": total,
            "unique_operations": len(operations),
            "throughput_per_hour": total / hours if hours > 0 else 0,
            "period_hours": hours,
        }
