"""
Platform Observability — Operational Analytics

Phase 6: Observability Platform
Constitution: Principle 48 (Operational Awareness), Principle 49 (Predictive Operations)
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any


class OperationalAnalytics:
    """Aggregated operational analytics for platform intelligence."""

    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []

    def record(self, event: dict[str, Any]) -> None:
        """Record an operational event."""
        event.setdefault("timestamp", datetime.utcnow().isoformat())
        self._events.append(event)

    def record_batch(self, events: list[dict[str, Any]]) -> int:
        for e in events:
            e.setdefault("timestamp", datetime.utcnow().isoformat())
        self._events.extend(events)
        return len(events)

    def get_event_frequency(self, hours: int = 24) -> dict[str, int]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        freq: dict[str, int] = defaultdict(int)
        for e in self._events:
            try:
                if datetime.fromisoformat(e.get("timestamp", "")) >= cutoff:
                    freq[e.get("type", "unknown")] += 1
            except (ValueError, TypeError):
                pass
        return dict(freq)

    def get_module_activity(self, hours: int = 24) -> dict[str, int]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        activity: dict[str, int] = defaultdict(int)
        for e in self._events:
            try:
                if datetime.fromisoformat(e.get("timestamp", "")) >= cutoff:
                    activity[e.get("module", "unknown")] += 1
            except (ValueError, TypeError):
                pass
        return dict(activity)

    def get_user_activity(self, hours: int = 24) -> dict[int, int]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        activity: dict[int, int] = defaultdict(int)
        for e in self._events:
            try:
                if datetime.fromisoformat(e.get("timestamp", "")) >= cutoff:
                    uid = e.get("user_id")
                    if uid is not None:
                        activity[uid] += 1
            except (ValueError, TypeError):
                pass
        return dict(activity)

    def get_operation_distribution(self, hours: int = 24) -> dict[str, int]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        dist: dict[str, int] = defaultdict(int)
        for e in self._events:
            try:
                if datetime.fromisoformat(e.get("timestamp", "")) >= cutoff:
                    op = e.get("operation", e.get("action", "unknown"))
                    dist[op] += 1
            except (ValueError, TypeError):
                pass
        return dict(dist)

    def get_peak_hours(self, hours: int = 168) -> list[dict[str, Any]]:
        """Get peak activity hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        hourly: dict[str, int] = defaultdict(int)
        for e in self._events:
            try:
                if datetime.fromisoformat(e.get("timestamp", "")) >= cutoff:
                    hour = datetime.fromisoformat(e.get("timestamp", "")).strftime("%Y-%m-%d-%H")
                    hourly[hour] += 1
            except (ValueError, TypeError):
                pass

        return sorted(
            [{"hour": h, "count": c} for h, c in hourly.items()],
            key=lambda x: -x["count"],
        )[:24]

    def get_daily_summary(self, days: int = 7) -> list[dict[str, Any]]:
        """Get daily operational summary."""
        summaries: list[dict[str, Any]] = []
        for d in range(days):
            day = datetime.utcnow().date() - timedelta(days=d)
            day_start = datetime.combine(day, datetime.min.time())
            day_end = datetime.combine(day, datetime.max.time())

            day_events = [
                e for e in self._events
                if self._parse_ts(e.get("timestamp", "")) and
                day_start <= self._parse_ts(e.get("timestamp", "")) <= day_end
            ]

            events_by_type: dict[str, int] = defaultdict(int)
            for e in day_events:
                events_by_type[e.get("type", "unknown")] += 1

            summaries.append({
                "date": day.isoformat(),
                "total_events": len(day_events),
                "by_type": dict(events_by_type),
            })

        return list(reversed(summaries))

    def get_summary(self, hours: int = 24) -> dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        total = 0
        by_type: dict[str, int] = defaultdict(int)
        by_module: dict[str, int] = defaultdict(int)
        for e in self._events:
            try:
                if datetime.fromisoformat(e.get("timestamp", "")) >= cutoff:
                    total += 1
                    by_type[e.get("type", "unknown")] += 1
                    by_module[e.get("module", "unknown")] += 1
            except (ValueError, TypeError):
                pass
        return {
            "total_events": total,
            "by_type": dict(by_type),
            "by_module": dict(by_module),
            "period_hours": hours,
        }

    def _parse_ts(self, ts: str) -> datetime | None:
        try:
            return datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            return None
