"""Dashboard service — provides aggregated statistics for the dashboard page."""

from __future__ import annotations

from datetime import datetime, timedelta

from lab_system.app.database.repository import BaseRepository


class DashboardService:
    def __init__(self) -> None:
        self._repo = BaseRepository()

    def get_stats(self) -> dict:
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        return {
            "total": self._repo.count("SELECT COUNT(*) FROM receipts"),
            "today_count": self._repo.count(
                "SELECT COUNT(*) FROM receipts WHERE date(created_at) = ?", (today,)
            ),
            "week_count": self._repo.count(
                "SELECT COUNT(*) FROM receipts WHERE date(created_at) >= ?", (week_ago,)
            ),
            "month_count": self._repo.count(
                "SELECT COUNT(*) FROM receipts WHERE date(created_at) >= ?",
                (month_ago,),
            ),
            "pending": self._repo.count(
                "SELECT COUNT(*) FROM receipts WHERE status = 'Draft'"
            ),
            "completed": self._repo.count(
                "SELECT COUNT(*) FROM receipts WHERE status = 'Approved'"
            ),
            "org_count": self._repo.count("SELECT COUNT(*) FROM organizations"),
            "user_count": self._repo.count("SELECT COUNT(*) FROM users"),
        }

    def get_recent_activity(self, limit: int = 10) -> list[dict]:
        rows = self._repo.fetch_all(
            "SELECT timestamp, user_id, action FROM audit_logs ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [dict(r) for r in rows]

    def get_recent_backups(self, limit: int = 5) -> list[dict]:
        rows = self._repo.fetch_all(
            "SELECT created_at, notes FROM backups ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [dict(r) for r in rows]
