"""Audit service for the desktop application — provides audit log queries."""

from __future__ import annotations

from lab_system.app.database.repository import BaseRepository


class DesktopAuditService:
    def __init__(self) -> None:
        self._repo = BaseRepository()

    def list_logs(self, limit: int = 200) -> list[dict]:
        rows = self._repo.fetch_all(
            "SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,)
        )
        return [dict(r) for r in rows]
