"""
Platform Core — Backup Service

Unified backup management supporting SQLite and PostgreSQL.
Extracted from: lab_system/app/services/backup_service.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from unified_platform.core.base import BackupResult, PlatformService, ServiceHealth, ServiceStatus


class BackupService(PlatformService):
    """Unified backup management service."""

    @property
    def service_name(self) -> str:
        return "platform.backup"

    def health_check(self) -> ServiceHealth:
        return ServiceHealth(
            service_name=self.service_name,
            status=ServiceStatus.HEALTHY,
        )

    def create_backup(self, notes: str = "", conn=None) -> BackupResult:
        """Create a database backup."""
        ...

    def list_backups(self, limit: int = 50, conn=None) -> list[dict[str, Any]]:
        """List available backups."""
        ...

    def verify_backup(self, backup_path: Path) -> dict[str, Any]:
        """Verify backup integrity."""
        ...

    def delete_backup(self, backup_path: Path, conn=None) -> BackupResult:
        """Delete a backup file."""
        ...

    def restore_from_backup(self, backup_path: Path, conn=None) -> BackupResult:
        """Restore database from a backup."""
        ...

    def enforce_retention(self, max_backups: int = 30, conn=None) -> int:
        """Enforce backup retention policy. Returns count of deleted backups."""
        ...

    def get_backup_info(self, backup_path: Path) -> dict[str, Any]:
        """Get detailed information about a backup."""
        ...

    def auto_backup(self, notes: str = "", conn=None) -> BackupResult:
        """Perform automatic backup."""
        ...

    def get_latest_backup(self, conn=None) -> dict[str, Any] | None:
        """Get the most recent backup."""
        ...

    def backup_size(self, backup_path: Path) -> int:
        """Get backup file size in bytes."""
        ...
