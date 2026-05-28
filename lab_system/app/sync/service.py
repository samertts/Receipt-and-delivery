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
from lab_system.app.sync.api_client import api_client, APIClient, SyncPayload
from lab_system.app.sync.device import get_device_id, get_branch_id


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

SYNC_QUEUE_TABLE = 'sync_queue'
SYNC_STATUS_PENDING = 'pending'
SYNC_STATUS_SYNCED = 'synced'
SYNC_STATUS_CONFLICT = 'conflict'

SYNC_ACTIONS = ('create', 'update', 'delete')


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
        with _db.get_conn() as conn:
            rows = conn.execute(
                f"""SELECT * FROM {SYNC_QUEUE_TABLE}
                    WHERE status = ?
                    ORDER BY created_at ASC
                    LIMIT ?""",
                (SYNC_STATUS_PENDING, limit),
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
                f"UPDATE {SYNC_QUEUE_TABLE} SET retry_count = retry_count + 1 WHERE id=?",
                (entry_id,),
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
                    GROUP BY status"""
            ).fetchall()
        stats: dict[str, int] = {}
        for r in rows:
            stats[r['status']] = r['cnt']
        return stats

    def resolve_conflict(
        self,
        entry: SyncQueueEntry,
        remote_data: dict[str, Any],
        local_data: dict[str, Any],
    ) -> ConflictResolution:
        """
        Conflict resolution stub.
        Default strategy: server-wins.
        Override to implement custom merge logic.
        """
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
        return {'synced': 0, 'conflicts': len(pending)}

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


sync_service = SyncService()
