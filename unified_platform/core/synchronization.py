"""
Platform Core — Synchronization Service

Unified multi-device data synchronization.
Extracted from: lab_system/app/sync/service.py, backend/app/services/sync_service.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from unified_platform.core.base import PlatformService, ServiceHealth, ServiceStatus, SyncResult


@dataclass
class SyncConflict:
    """Standardized sync conflict contract."""
    entity_type: str
    entity_id: int
    local_data: dict[str, Any]
    remote_data: dict[str, Any]
    strategy: str = "last-writer-wins"
    resolved: bool = False


@dataclass
class SyncQueueEntry:
    """Standardized sync queue entry."""
    id: int | None = None
    entity_type: str = ""
    entity_id: int = 0
    action: str = ""
    payload: str = ""
    status: str = "pending"
    retry_count: int = 0
    created_at: str = ""


class SynchronizationService(PlatformService):
    """Unified synchronization service."""

    @property
    def service_name(self) -> str:
        return "platform.synchronization"

    def health_check(self) -> ServiceHealth:
        return ServiceHealth(
            service_name=self.service_name,
            status=ServiceStatus.HEALTHY,
        )

    def sync_all(self, conn=None) -> SyncResult:
        """Synchronize all pending changes."""
        ...

    def sync_pending(self, conn=None) -> SyncResult:
        """Synchronize only pending changes."""
        ...

    def push_entity(self, entity_type: str, entity_id: int, action: str, payload: str, conn=None) -> dict[str, Any]:
        """Push a single entity to remote."""
        ...

    def pull_entities(self, entity_type: str, since: str = "", conn=None) -> list[dict[str, Any]]:
        """Pull entities from remote."""
        ...

    def enqueue(self, entity_type: str, entity_id: int, action: str, payload: str, conn=None) -> int:
        """Add an entry to the sync queue."""
        ...

    def get_pending(self, conn=None) -> list[SyncQueueEntry]:
        """Get all pending sync entries."""
        ...

    def mark_synced(self, entry_id: int, conn=None) -> bool:
        """Mark a sync entry as synced."""
        ...

    def mark_synced_batch(self, entry_ids: list[int], conn=None) -> int:
        """Mark multiple entries as synced. Returns count."""
        ...

    def mark_conflict(self, entry_id: int, details: str, conn=None) -> bool:
        """Mark a sync entry as conflicted."""
        ...

    def resolve_conflict(self, entry: SyncQueueEntry, remote: dict[str, Any], local: dict[str, Any]) -> SyncConflict:
        """Resolve a sync conflict."""
        ...

    def get_health(self, conn=None) -> dict[str, Any]:
        """Get sync health status."""
        ...

    def get_sync_status(self, conn=None) -> dict[str, Any]:
        """Get overall sync status."""
        ...
