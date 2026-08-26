"""
SyncService — lightweight orchestration for future online synchronization.

This service manages a local sync queue that records entity mutations.
It is fully optional and does NOT activate any network calls.

Queue entries are created by service-layer hooks (to be wired when
sync is enabled). The service provides query, flush, and conflict
resolution stubs ready for future implementation.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from lab_system.app.database import db as _db
from lab_system.app.sync.api_client import APIClient, SyncPayload
from lab_system.app.sync.device import get_branch_id, get_device_id


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


SYNC_QUEUE_TABLE = "sync_queue"
SYNC_STATUS_PENDING = "pending"
SYNC_STATUS_SYNCED = "synced"
SYNC_STATUS_CONFLICT = "conflict"

SYNC_ACTIONS = ("create", "update", "delete")

# Retry policy
SYNC_MAX_RETRIES = 10
SYNC_BACKOFF_BASE_SECONDS = 30
SYNC_MAX_BACKOFF_SECONDS = 3600
SYNC_MAX_PAYLOAD_BYTES = 5 * 1024 * 1024


@dataclass
class SyncQueueEntry:
    id: int = 0
    entity_type: str = ""
    entity_id: int = 0
    action: str = ""
    payload: str = ""
    status: str = SYNC_STATUS_PENDING
    retry_count: int = 0
    created_at: str = ""
    synced_at: str = ""
    idempotency_key: str = ""
    last_error: str = ""


@dataclass
class ConflictResolution:
    strategy: str = "server-wins"
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
        payload: str = "",
        idempotency_key: str = "",
        conn: Any | None = None,
    ) -> int:
        if action not in SYNC_ACTIONS:
            raise ValueError(
                f"Invalid sync action '{action}'. Must be one of {SYNC_ACTIONS}"
            )
        if not entity_type or len(entity_type) > 50:
            raise ValueError("Invalid sync entity type")
        if not isinstance(payload, str) or len(payload.encode("utf-8")) > SYNC_MAX_PAYLOAD_BYTES:
            raise ValueError("Sync payload exceeds the safety limit")
        idempotency_key = idempotency_key.strip() or str(uuid.uuid4())
        if len(idempotency_key) > 160:
            raise ValueError("Idempotency key exceeds the safety limit")
        if conn is not None:
            return self._enqueue_in_connection(
                conn, entity_type, entity_id, action, payload, idempotency_key
            )
        with _db.get_conn() as owned_conn:
            return self._enqueue_in_connection(
                owned_conn, entity_type, entity_id, action, payload, idempotency_key
            )

    @staticmethod
    def _enqueue_in_connection(
        conn: Any,
        entity_type: str,
        entity_id: int,
        action: str,
        payload: str,
        idempotency_key: str,
    ) -> int:
        existing = conn.execute(
            "SELECT id FROM sync_queue WHERE idempotency_key=? LIMIT 1",
            (idempotency_key,),
        ).fetchone()
        if existing:
            return existing[0]
        conn.execute(
            """INSERT INTO sync_queue
                (entity_type, entity_id, action, payload, idempotency_key, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                entity_type,
                entity_id,
                action,
                payload,
                idempotency_key,
                SYNC_STATUS_PENDING,
                _utcnow(),
            ),
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    def get_pending(self, limit: int = 100) -> list[SyncQueueEntry]:
        """Return pending entries whose exponential retry delay has elapsed."""
        if limit < 1:
            return []
        with _db.get_conn() as conn:
            rows = conn.execute(
                """SELECT * FROM sync_queue
                    WHERE status = ? AND retry_count < ?
                    ORDER BY created_at ASC
                    LIMIT ?""",
                (SYNC_STATUS_PENDING, SYNC_MAX_RETRIES, max(limit * 4, limit)),
            ).fetchall()
        now = datetime.now(timezone.utc)
        pending: list[SyncQueueEntry] = []
        for row in rows:
            entry = SyncQueueEntry(**dict(row))
            if not entry.synced_at:
                pending.append(entry)
                continue
            try:
                last_attempt = datetime.fromisoformat(entry.synced_at)
                if last_attempt.tzinfo is None:
                    last_attempt = last_attempt.replace(tzinfo=timezone.utc)
            except ValueError:
                pending.append(entry)
                continue
            delay = min(
                SYNC_BACKOFF_BASE_SECONDS * (2 ** max(entry.retry_count - 1, 0)),
                SYNC_MAX_BACKOFF_SECONDS,
            )
            if now - last_attempt >= timedelta(seconds=delay):
                pending.append(entry)
            if len(pending) >= limit:
                break
        return pending

    def mark_synced(self, entry_id: int) -> None:
        with _db.get_conn() as conn:
            conn.execute(
                "UPDATE sync_queue SET status=?, retry_count=0, synced_at=? WHERE id=?",
                (SYNC_STATUS_SYNCED, _utcnow(), entry_id),
            )

    def mark_synced_batch(self, entry_ids: list[int]) -> None:
        """Mark multiple entries as synced in a single transaction."""
        if not entry_ids:
            return
        with _db.get_conn() as conn:
            try:
                conn.execute("BEGIN")
                for entry_id in entry_ids:
                    conn.execute(
                        "UPDATE sync_queue SET status=?, retry_count=0, synced_at=? WHERE id=?",
                        (SYNC_STATUS_SYNCED, _utcnow(), entry_id),
                    )
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def mark_conflict(self, entry_id: int, details: str = "") -> None:
        with _db.get_conn() as conn:
            columns = {row[1] for row in conn.execute("PRAGMA table_info(sync_queue)")}
            if "last_error" in columns:
                conn.execute(
                    "UPDATE sync_queue SET status=?, last_error=?, synced_at=? WHERE id=?",
                    (SYNC_STATUS_CONFLICT, details[:2000], _utcnow(), entry_id),
                )
            else:
                # Compatibility with an un-migrated local database; retain payload.
                conn.execute(
                    "UPDATE sync_queue SET status=?, synced_at=? WHERE id=?",
                    (SYNC_STATUS_CONFLICT, _utcnow(), entry_id),
                )

    def increment_retry(self, entry_id: int) -> int:
        with _db.get_conn() as conn:
            conn.execute(
                "UPDATE sync_queue SET retry_count = retry_count + 1, synced_at=? WHERE id=?",
                (_utcnow(), entry_id),
            )
            row = conn.execute(
                "SELECT retry_count FROM sync_queue WHERE id=?",
                (entry_id,),
            ).fetchone()
            return row["retry_count"] if row else 0

    def clear_synced(self, older_than_seconds: int = 0) -> int:
        with _db.get_conn() as conn:
            cur = conn.execute(
                """DELETE FROM sync_queue
                    WHERE status = ? AND synced_at < datetime('now', ?)""",
                (SYNC_STATUS_SYNCED, f"-{max(older_than_seconds, 0)} seconds"),
            )
            return cur.rowcount

    def get_stats(self) -> dict[str, int]:
        with _db.get_conn() as conn:
            rows = conn.execute(
                """SELECT status, COUNT(*) as cnt
                    FROM sync_queue
                    GROUP BY status""",
            ).fetchall()
        stats: dict[str, int] = {}
        for r in rows:
            stats[r["status"]] = r["cnt"]
        return stats

    def resolve_conflict(
        self,
        _entry: SyncQueueEntry,
        remote_data: dict[str, Any],
        _local_data: dict[str, Any],
    ) -> ConflictResolution:
        """
        Quarantine chain-of-custody conflicts for human review.

        Timestamp-based last-writer-wins is unsafe for custody records because it
        can silently overwrite a historical event. The caller must preserve both
        payloads and complete a documented correction workflow.
        """
        return ConflictResolution(
            strategy="quarantine",
            resolved=False,
            merged={
                "local": _local_data if isinstance(_local_data, dict) else {},
                "remote": remote_data if isinstance(remote_data, dict) else {},
            },
        )

    def sync_all(self) -> dict[str, int]:
        if not self.is_online:
            return {"error": "API client disabled — sync not available"}
        pending = self.get_pending()
        if not pending:
            return {"synced": 0, "conflicts": 0}
        device_id = get_device_id()
        branch_id = get_branch_id()
        payload = SyncPayload(
            entries=[
                {
                    "entity_type": e.entity_type,
                    "entity_id": e.entity_id,
                    "action": e.action,
                    "payload": e.payload,
                    "idempotency_key": e.idempotency_key,
                }
                for e in pending
            ],
            device_id=device_id,
            branch_id=branch_id,
        )
        response = self._client.push(payload)
        response_data = response.data.get("data", response.data) if response.data else {}
        conflict_items = response_data.get("conflict_items", [])
        conflict_keys = {
            (item.get("entity_type"), item.get("entity_id"))
            for item in conflict_items
            if isinstance(item, dict)
        }
        if response.success:
            conflicts = 0
            for e in pending:
                key = (e.entity_type, e.entity_id)
                if key in conflict_keys:
                    self.mark_conflict(e.id, "Server conflict requires manual review")
                    conflicts += 1
                else:
                    self.mark_synced(e.id)
            return {"synced": len(pending) - conflicts, "conflicts": conflicts}
        if response.status_code == 409:
            detail = response_data.get("detail", response.message)
            for e in pending:
                self.mark_conflict(e.id, str(detail))
            return {"synced": 0, "conflicts": len(pending)}
        for e in pending:
            retries = self.increment_retry(e.id)
            if retries >= SYNC_MAX_RETRIES:
                self.mark_conflict(e.id, f"Max retries ({SYNC_MAX_RETRIES}) exceeded")
        return {"synced": 0, "conflicts": len(pending)}

    def sync_pending(self) -> dict[str, int]:
        """Retry pending entries. Safe to call from a timer."""
        if not self.is_online:
            return {"error": "disabled"}
        return self.sync_all()

    def push_entity(
        self,
        entity_type: str,
        entity_id: int,
        action: str,
        payload: str = "",
        idempotency_key: str = "",
    ) -> dict[str, Any]:
        entry_id = self.enqueue(entity_type, entity_id, action, payload, idempotency_key)
        if self.is_online:
            result = self.sync_all()
            if "error" in result:
                return {
                    "entry_id": entry_id,
                    "status": SYNC_STATUS_PENDING,
                    "sync_error": result["error"],
                }
            if result.get("conflicts", 0) > 0:
                self.mark_conflict(entry_id)
                return {"entry_id": entry_id, "status": "conflict"}
        return {"entry_id": entry_id, "status": SYNC_STATUS_PENDING}

    def get_health(self) -> dict[str, Any]:
        """Return sync health status for dashboard monitoring."""
        stats = self.get_stats()
        pending = stats.get(SYNC_STATUS_PENDING, 0)
        conflicts = stats.get(SYNC_STATUS_CONFLICT, 0)
        total = sum(stats.values()) if stats else 0
        return {
            "enabled": self.is_online,
            "pending": pending,
            "conflicts": conflicts,
            "synced": stats.get(SYNC_STATUS_SYNCED, 0),
            "total": total,
            "healthy": pending == 0 and conflicts == 0,
        }


sync_service = SyncService()
