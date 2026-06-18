"""Backup listing service for the desktop application."""

from __future__ import annotations

from lab_system.app.database.repository import BaseRepository


class BackupListingService:
    def __init__(self) -> None:
        self._repo = BaseRepository()

    def list_backups(self) -> list[dict]:
        rows = self._repo.fetch_all("SELECT * FROM backups ORDER BY id DESC")
        return [dict(r) for r in rows]
