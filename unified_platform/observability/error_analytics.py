"""
Platform Observability — Error Analytics

Phase 6: Observability Platform
Constitution: Principle 48 (Operational Awareness)
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any


class ErrorAnalytics:
    """Analyzes error patterns for operational intelligence."""

    def __init__(self) -> None:
        self._errors: list[dict[str, Any]] = []

    def record(self, error: dict[str, Any]) -> None:
        """Record an error for analysis."""
        error.setdefault("timestamp", datetime.utcnow().isoformat())
        self._errors.append(error)

    def record_batch(self, errors: list[dict[str, Any]]) -> int:
        """Record multiple errors."""
        for e in errors:
            e.setdefault("timestamp", datetime.utcnow().isoformat())
        self._errors.extend(errors)
        return len(errors)

    def get_error_rate(self, hours: int = 24) -> float:
        """Get error rate per hour."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        count = 0
        for e in self._errors:
            try:
                if datetime.fromisoformat(e.get("timestamp", "")) >= cutoff:
                    count += 1
            except (ValueError, TypeError):
                pass
        return count / hours if hours > 0 else 0.0

    def get_error_frequency(self, hours: int = 24) -> dict[str, int]:
        """Get error type frequency."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        freq: dict[str, int] = defaultdict(int)
        for e in self._errors:
            try:
                if datetime.fromisoformat(e.get("timestamp", "")) >= cutoff:
                    freq[e.get("type", "unknown")] += 1
            except (ValueError, TypeError):
                pass
        return dict(freq)

    def get_errors_by_service(self, hours: int = 24) -> dict[str, int]:
        """Get errors grouped by service."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        by_service: dict[str, int] = defaultdict(int)
        for e in self._errors:
            try:
                if datetime.fromisoformat(e.get("timestamp", "")) >= cutoff:
                    by_service[e.get("service", "unknown")] += 1
            except (ValueError, TypeError):
                pass
        return dict(by_service)

    def get_critical_errors(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get critical errors."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        critical = []
        for e in self._errors:
            try:
                if (datetime.fromisoformat(e.get("timestamp", "")) >= cutoff
                        and e.get("severity") in ("critical", "error")):
                    critical.append(e)
            except (ValueError, TypeError):
                pass
        return critical

    def detect_error_spikes(self, threshold_multiplier: float = 3.0) -> list[dict[str, Any]]:
        """Detect error rate spikes."""
        hourly: dict[str, int] = defaultdict(int)
        for e in self._errors:
            try:
                hour = datetime.fromisoformat(e.get("timestamp", "")).strftime("%Y-%m-%d-%H")
                hourly[hour] += 1
            except (ValueError, TypeError):
                pass

        if not hourly:
            return []

        values = list(hourly.values())
        mean = sum(values) / len(values)
        std = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
        threshold = mean + (std * threshold_multiplier) if std > 0 else mean * threshold_multiplier

        return [
            {"hour": h, "count": c, "threshold": threshold}
            for h, c in hourly.items()
            if c > threshold
        ]

    def get_summary(self, hours: int = 24) -> dict[str, Any]:
        """Get error summary."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        total = 0
        by_type: dict[str, int] = defaultdict(int)
        by_service: dict[str, int] = defaultdict(int)
        for e in self._errors:
            try:
                if datetime.fromisoformat(e.get("timestamp", "")) >= cutoff:
                    total += 1
                    by_type[e.get("type", "unknown")] += 1
                    by_service[e.get("service", "unknown")] += 1
            except (ValueError, TypeError):
                pass
        return {
            "total_errors": total,
            "error_rate_per_hour": total / hours if hours > 0 else 0,
            "by_type": dict(by_type),
            "by_service": dict(by_service),
            "period_hours": hours,
        }
