"""Settings service for the desktop application — provides settings read/write."""

from __future__ import annotations

from lab_system.app.database.db import DEFAULT_SETTINGS
from lab_system.app.database.repository import BaseRepository


class DesktopSettingsService:
    def __init__(self) -> None:
        self._repo = BaseRepository()

    def get(self, key: str, default: str = "") -> str:
        row = self._repo.fetch_one("SELECT value FROM settings WHERE key=?", (key,))
        return row["value"] if row else default

    def set(self, key: str, value: str) -> None:
        self._repo.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, value))

    def get_all(self) -> dict[str, str]:
        result = {}
        for key, default in DEFAULT_SETTINGS.items():
            result[key] = self.get(key, default)
        return result

    def set_all(self, settings: dict[str, str]) -> None:
        for key, value in settings.items():
            self.set(key, value)

    @staticmethod
    def get_defaults() -> dict[str, str]:
        return dict(DEFAULT_SETTINGS)
