"""
Platform Core — Telemetry Service

System metrics, performance monitoring, usage analytics.
Status: NEW — must be created from scratch.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

from unified_platform.core.base import MetricsSnapshot, PlatformService, ServiceHealth, ServiceStatus


class TelemetryService(PlatformService):
    """Unified telemetry and metrics service."""

    @property
    def service_name(self) -> str:
        return "platform.telemetry"

    def __init__(self) -> None:
        self._counters: dict[str, int] = defaultdict(int)
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._gauges: dict[str, float] = {}
        self._start_time = time.time()

    def health_check(self) -> ServiceHealth:
        return ServiceHealth(
            service_name=self.service_name,
            status=ServiceStatus.HEALTHY,
            metadata={"uptime_seconds": time.time() - self._start_time},
        )

    def record_counter(self, name: str, value: int = 1, tags: dict[str, str] | None = None) -> None:
        """Record a counter metric."""
        key = self._make_key(name, tags)
        self._counters[key] += value

    def record_histogram(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record a histogram metric."""
        key = self._make_key(name, tags)
        self._histograms[key].append(value)

    def record_gauge(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record a gauge metric."""
        key = self._make_key(name, tags)
        self._gauges[key] = value

    def get_counter(self, name: str, tags: dict[str, str] | None = None) -> int:
        """Get current counter value."""
        key = self._make_key(name, tags)
        return self._counters.get(key, 0)

    def get_histogram(self, name: str, tags: dict[str, str] | None = None) -> dict[str, float]:
        """Get histogram statistics."""
        key = self._make_key(name, tags)
        values = self._histograms.get(key, [])
        if not values:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0}
        values_sorted = sorted(values)
        count = len(values_sorted)
        return {
            "count": count,
            "min": values_sorted[0],
            "max": values_sorted[-1],
            "avg": sum(values_sorted) / count,
            "p50": values_sorted[count // 2],
            "p95": values_sorted[int(count * 0.95)] if count > 1 else values_sorted[-1],
            "p99": values_sorted[int(count * 0.99)] if count > 1 else values_sorted[-1],
        }

    def get_gauge(self, name: str, tags: dict[str, str] | None = None) -> float:
        """Get current gauge value."""
        key = self._make_key(name, tags)
        return self._gauges.get(key, 0.0)

    def get_all_metrics(self) -> dict[str, Any]:
        """Get all collected metrics."""
        return {
            "counters": dict(self._counters),
            "histograms": {k: self.get_histogram(k) for k in self._histograms},
            "gauges": dict(self._gauges),
            "uptime_seconds": time.time() - self._start_time,
        }

    def get_snapshot(self) -> MetricsSnapshot:
        """Get a snapshot of all metrics."""
        return MetricsSnapshot(
            service=self.service_name,
            metrics=self.get_all_metrics(),
        )

    def reset(self) -> None:
        """Reset all metrics."""
        self._counters.clear()
        self._histograms.clear()
        self._gauges.clear()
        self._start_time = time.time()

    def _make_key(self, name: str, tags: dict[str, str] | None = None) -> str:
        """Create a metric key from name and tags."""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}|{tag_str}"

    def record_action(self, action: str, user_id: int | None = None) -> None:
        """Record a user action for usage analytics."""
        tags = {"action": action}
        if user_id is not None:
            tags["user_id"] = str(user_id)
        self.record_counter("actions.total", tags=tags)
        self.record_counter(f"actions.{action}", tags=tags)

    def record_error(self, error_type: str, service: str = "") -> None:
        """Record an error for error analytics."""
        tags = {"error_type": error_type}
        if service:
            tags["service"] = service
        self.record_counter("errors.total", tags=tags)
        self.record_counter(f"errors.{error_type}", tags=tags)

    def record_performance(self, operation: str, duration_ms: float) -> None:
        """Record performance metric."""
        self.record_histogram(f"performance.{operation}.duration_ms", duration_ms)
        self.record_counter(f"performance.{operation}.count")
