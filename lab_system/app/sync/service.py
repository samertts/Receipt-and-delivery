"""
SyncService — lightweight orchestration for future online synchronization.

This service manages a local sync queue that records entity mutations.
It is fully optional and does NOT activate any network calls.

Queue entries are created by service-layer hooks (to be wired when
sync is enabled). The service provides query, flush, and conflict
resolution stubs ready for future implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from lab_system.app.database import db as _db
from lab_system.app.sync.api_client import APIClient, SyncPayload
from lab_system.app.sync.device import get_branch_id, get_device_id


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


SYNC_QUEUE_TABLE = 'sync_queue'
SYNC_STATUS_PENDING = 'pending'
SYNC_STATUS_SYNCED = 'synced'
SYNC_STATUS_CONFLICT = 'conflict'

SYNC_ACTIONS = ('create', 'update', 'delete')

# Retry policy
SYNC_MAX_RETRIES = 10
SYNC_BACKOFF_BASE_SECONDS = 30


@dataclass
class SyncQueueEntry:
    id: int = 0
    entity_type: str = ''
    entity_id: int = 0
    action: str = ''
    payload: str = ''
    status: str = SYNC_STATUS_PENDING
    retry_count: int = 0
    created_at: str = ''
    synced_at: str = ''


@dataclass
class ConflictResolution:
    strategy: str = 'server-wins'
    resolved: bool = False
    merged: dict[str, Any] = field(default_factory=dict)


class SyncService:
    def __init__(self, client: APIClient | None = None):
        self._client = client if client is not None else APIClient()

    @property
    def is_online(self) -> bool:
        return self._client.is_enabled

    def enqueue(
        self,
        entity_type: str,
        entity_id: int,
        action: str,
        payload: str = '',
    ) -> int:
        if action not in SYNC_ACTIONS:
            raise ValueError(f"Invalid sync action '{action}'. Must be one of {SYNC_ACTIONS}")
        now = _utcnow()
        with _db.get_conn() as conn:
            conn.execute(
                f"""INSERT INTO {SYNC_QUEUE_TABLE}
                    (entity_type, entity_id, action, payload, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                (entity_type, entity_id, action, payload, SYNC_STATUS_PENDING, now),
            )
            return conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    def get_pending(self, limit: int = 100) -> list[SyncQueueEntry]:
        """Return pending entries that have not exceeded max retries and are eligible for retry."""
        with _db.get_conn() as conn:
            rows = conn.execute(
                f"""SELECT * FROM {SYNC_QUEUE_TABLE}
                    WHERE status = ?
                      AND retry_count < ?
                      AND (synced_at = '' OR
                           CAST(julianday('now') - julianday(synced_at) AS REAL) * 86400 > ?)
                    ORDER BY created_at ASC
                    LIMIT ?""",
                (SYNC_STATUS_PENDING, SYNC_MAX_RETRIES, SYNC_BACKOFF_BASE_SECONDS, limit),
            ).fetchall()
        return [SyncQueueEntry(**dict(r)) for r in rows]

    def mark_synced(self, entry_id: int) -> None:
        with _db.get_conn() as conn:
            conn.execute(
                f"UPDATE {SYNC_QUEUE_TABLE} SET status=?, retry_count=0, synced_at=? WHERE id=?",
                (SYNC_STATUS_SYNCED, _utcnow(), entry_id),
            )

    def mark_conflict(self, entry_id: int, details: str = '') -> None:
        with _db.get_conn() as conn:
            conn.execute(
                f"UPDATE {SYNC_QUEUE_TABLE} SET status=?, payload=? WHERE id=?",
                (SYNC_STATUS_CONFLICT, details, entry_id),
            )

    def increment_retry(self, entry_id: int) -> int:
        with _db.get_conn() as conn:
            conn.execute(
                f"UPDATE {SYNC_QUEUE_TABLE} SET retry_count = retry_count + 1, synced_at=? WHERE id=?",
                (_utcnow(), entry_id),
            )
            row = conn.execute(
                f"SELECT retry_count FROM {SYNC_QUEUE_TABLE} WHERE id=?",
                (entry_id,),
            ).fetchone()
            return row['retry_count'] if row else 0

    def clear_synced(self, older_than_seconds: int = 0) -> int:
        with _db.get_conn() as conn:
            cur = conn.execute(
                f"""DELETE FROM {SYNC_QUEUE_TABLE}
                    WHERE status = ? AND synced_at < datetime('now', ?)""",
                (SYNC_STATUS_SYNCED, f'-{max(older_than_seconds, 1)} seconds'),
            )
            return cur.rowcount

    def get_stats(self) -> dict[str, int]:
        with _db.get_conn() as conn:
            rows = conn.execute(
                f"""SELECT status, COUNT(*) as cnt
                    FROM {SYNC_QUEUE_TABLE}
                    GROUP BY status""",
            ).fetchall()
        stats: dict[str, int] = {}
        for r in rows:
            stats[r['status']] = r['cnt']
        return stats

    def resolve_conflict(
        self,
        _entry: SyncQueueEntry,
        remote_data: dict[str, Any],
        _local_data: dict[str, Any],
    ) -> ConflictResolution:
        """
        Conflict resolution: last-writer-wins based on timestamp comparison.

        If both sides have timestamps, the later one wins.
        Otherwise, defaults to server-wins.
        """
        remote_ts = remote_data.get('updated_at') or remote_data.get('created_at', '')
        local_ts = _local_data.get('updated_at') or _local_data.get('created_at', '') if isinstance(_local_data, dict) else ''
        if remote_ts and local_ts and local_ts > remote_ts:
            return ConflictResolution(
                strategy='last-writer-wins',
                resolved=True,
                merged=_local_data,
            )
        return ConflictResolution(
            strategy='server-wins',
            resolved=True,
            merged=remote_data,
        )

    def sync_all(self) -> dict[str, int]:
        if not self.is_online:
            return {'error': 'API client disabled — sync not available'}
        pending = self.get_pending()
        if not pending:
            return {'synced': 0, 'conflicts': 0}
        device_id = get_device_id()
        branch_id = get_branch_id()
        payload = SyncPayload(
            entries=[{
                'entity_type': e.entity_type,
                'entity_id': e.entity_id,
                'action': e.action,
                'payload': e.payload,
            } for e in pending],
            device_id=device_id,
            branch_id=branch_id,
        )
        response = self._client.push(payload)
        if response.success:
            for e in pending:
                self.mark_synced(e.id)
            return {'synced': len(pending), 'conflicts': 0}
        if response.status_code == 409:
            for e in pending:
                self.mark_conflict(e.id, response.data.get('detail', ''))
            return {'synced': 0, 'conflicts': len(pending)}
        for e in pending:
            retries = self.increment_retry(e.id)
            if retries >= SYNC_MAX_RETRIES:
                self.mark_conflict(e.id, f'Max retries ({SYNC_MAX_RETRIES}) exceeded')
        return {'synced': 0, 'conflicts': len(pending)}

    def sync_pending(self) -> dict[str, int]:
        """Retry pending entries. Safe to call from a timer."""
        if not self.is_online:
            return {'error': 'disabled'}
        return self.sync_all()

    def push_entity(
        self,
        entity_type: str,
        entity_id: int,
        action: str,
        payload: str = '',
    ) -> dict[str, Any]:
        entry_id = self.enqueue(entity_type, entity_id, action, payload)
        if self.is_online:
            result = self.sync_all()
            if 'error' in result:
                return {'entry_id': entry_id, 'status': SYNC_STATUS_PENDING, 'sync_error': result['error']}
            if result.get('conflicts', 0) > 0:
                self.mark_conflict(entry_id)
                return {'entry_id': entry_id, 'status': 'conflict'}
        return {'entry_id': entry_id, 'status': SYNC_STATUS_PENDING}

    def get_health(self) -> dict[str, Any]:
        """Return sync health status for dashboard monitoring."""
        stats = self.get_stats()
        pending = stats.get(SYNC_STATUS_PENDING, 0)
        conflicts = stats.get(SYNC_STATUS_CONFLICT, 0)
        total = sum(stats.values()) if stats else 0
        return {
            'enabled': self.is_online,
            'pending': pending,
            'conflicts': conflicts,
            'synced': stats.get(SYNC_STATUS_SYNCED, 0),
            'total': total,
            'healthy': pending == 0 and conflicts == 0,
        }


sync_service = SyncService()
