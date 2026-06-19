"""Sync service — business logic for synchronization operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.audit import log_audit
from app.models.sync_log import SyncLog
from app.models.user import User
from app.repositories import SyncRepository

SYNC_ACTIONS = ("create", "update", "delete")


class SyncService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = SyncRepository(db)

    def push(
        self,
        entries: list[dict[str, Any]],
        device_id: str,
        branch_id: str,
        request: Any = None,
        current_user: User | None = None,
    ) -> dict[str, Any]:
        accepted = 0
        conflicts = []
        for entry in entries:
            action = entry.get("action", "")
            if action not in SYNC_ACTIONS:
                continue

            entity_type = entry.get("entity_type", "")
            entity_id = entry.get("entity_id", 0)
            payload = entry.get("payload", "")

            # Check for existing sync log for this entity
            existing = (
                self.db.query(SyncLog)
                .filter(
                    SyncLog.entity_type == entity_type, SyncLog.entity_id == entity_id
                )
                .first()
            )

            if existing:
                # Last-writer-wins conflict resolution
                entry_timestamp = entry.get("timestamp", "")
                existing_timestamp = (
                    existing.synced_at.isoformat() if existing.synced_at else ""
                )
                if (
                    entry_timestamp
                    and existing_timestamp
                    and entry_timestamp > existing_timestamp
                ):
                    existing.payload = payload
                    existing.synced_at = datetime.utcnow()
                    existing.device_id = device_id
                    existing.branch_id = branch_id
                    accepted += 1
                else:
                    conflicts.append(
                        {
                            "entity_type": entity_type,
                            "entity_id": entity_id,
                            "action": action,
                        }
                    )
            else:
                # New entry
                sync_entry = SyncLog(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    action=action,
                    payload=payload,
                    device_id=device_id,
                    branch_id=branch_id,
                )
                self.db.add(sync_entry)
                accepted += 1

        if accepted:
            try:
                self.db.commit()
            except Exception:
                self.db.rollback()
                accepted = 0

        log_audit(
            user_id=str(current_user.id) if current_user else "system",
            action_type="sync_push",
            request=request,
            details=f"تم استلام {accepted} عناصر مزامنة من {device_id} ({branch_id})",
            db=self.db,
        )

        return {
            "accepted": accepted,
            "conflicts": len(conflicts),
            "device_id": device_id,
            "branch_id": branch_id,
        }

    def pull(
        self,
        since: str = "",
        device_id: str = "",
        limit: int = 100,
    ) -> dict[str, Any]:
        since_dt = None
        if since:
            try:
                since_dt = datetime.fromisoformat(since)
            except (ValueError, TypeError):
                pass

        entries = self.repo.find_since(
            since_dt=since_dt, device_id=device_id, limit=limit
        )

        return {
            "entries": [
                {
                    "id": e.id,
                    "entity_type": e.entity_type,
                    "entity_id": e.entity_id,
                    "action": e.action,
                    "payload": e.payload,
                    "device_id": e.device_id,
                    "synced_at": e.synced_at.isoformat() if e.synced_at else "",
                }
                for e in entries
            ],
            "count": len(entries),
            "since": since,
        }

    def status(self) -> dict[str, Any]:
        total = self.repo.count_all()
        latest = self.repo.get_latest()
        return {
            "total_syncs": total,
            "latest_sync": latest.synced_at.isoformat() if latest else None,
            "latest_device": latest.device_id if latest else None,
            "healthy": True,
        }
