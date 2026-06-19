"""
Platform Observability — Audit Analytics

Phase 6: Observability Platform
Constitution: Principle 30 (One Audit)
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any


class AuditAnalytics:
    """Analyzes audit logs for patterns and anomalies."""

    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def ingest(self, entry: dict[str, Any]) -> None:
        """Ingest an audit entry for analysis."""
        self._entries.append(entry)

    def ingest_batch(self, entries: list[dict[str, Any]]) -> int:
        """Ingest multiple audit entries."""
        self._entries.extend(entries)
        return len(entries)

    def get_action_frequency(self, hours: int = 24) -> dict[str, int]:
        """Get action frequency for the last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        frequency: dict[str, int] = defaultdict(int)
        for entry in self._entries:
            ts = entry.get("timestamp", "")
            try:
                entry_time = datetime.fromisoformat(ts)
                if entry_time >= cutoff:
                    frequency[entry.get("action", "unknown")] += 1
            except (ValueError, TypeError):
                pass
        return dict(frequency)

    def get_user_activity(self, hours: int = 24) -> dict[int, int]:
        """Get user activity counts."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        activity: dict[int, int] = defaultdict(int)
        for entry in self._entries:
            ts = entry.get("timestamp", "")
            try:
                entry_time = datetime.fromisoformat(ts)
                if entry_time >= cutoff:
                    uid = entry.get("user_id", 0)
                    activity[uid] += 1
            except (ValueError, TypeError):
                pass
        return dict(activity)

    def get_privileged_actions(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get privileged actions in the last N hours."""
        privileged = {"delete", "drop", "truncate", "admin", "override", "force"}
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result: list[dict[str, Any]] = []
        for entry in self._entries:
            ts = entry.get("timestamp", "")
            action = entry.get("action", "").lower()
            try:
                entry_time = datetime.fromisoformat(ts)
                if entry_time >= cutoff and any(p in action for p in privileged):
                    result.append(entry)
            except (ValueError, TypeError):
                pass
        return result

    def detect_anomalies(self, threshold_multiplier: float = 3.0) -> list[dict[str, Any]]:
        """Detect anomalous activity spikes."""
        hourly_counts: dict[str, int] = defaultdict(int)
        for entry in self._entries:
            ts = entry.get("timestamp", "")
            try:
                hour = datetime.fromisoformat(ts).strftime("%Y-%m-%d-%H")
                hourly_counts[hour] += 1
            except (ValueError, TypeError):
                pass

        if not hourly_counts:
            return []

        values = list(hourly_counts.values())
        mean = sum(values) / len(values)
        std = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
        threshold = mean + (std * threshold_multiplier)

        anomalies: list[dict[str, Any]] = []
        for hour, count in hourly_counts.items():
            if count > threshold:
                anomalies.append({
                    "hour": hour,
                    "count": count,
                    "threshold": threshold,
                    "deviation": (count - mean) / std if std > 0 else 0,
                })

        return anomalies

    def get_summary(self, hours: int = 24) -> dict[str, Any]:
        """Get audit summary."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        total = 0
        unique_users: set[int] = set()
        actions: dict[str, int] = defaultdict(int)
        for entry in self._entries:
            ts = entry.get("timestamp", "")
            try:
                entry_time = datetime.fromisoformat(ts)
                if entry_time >= cutoff:
                    total += 1
                    unique_users.add(entry.get("user_id", 0))
                    actions[entry.get("action", "unknown")] += 1
            except (ValueError, TypeError):
                pass
        return {
            "total_entries": total,
            "unique_users": len(unique_users),
            "top_actions": dict(sorted(actions.items(), key=lambda x: -x[1])[:10]),
            "period_hours": hours,
        }
