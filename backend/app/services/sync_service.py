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
        for entry in entries:
            action = entry.get("action", "")
            if action not in SYNC_ACTIONS:
                continue
            sync_entry = SyncLog(
                entity_type=entry.get("entity_type", ""),
                entity_id=entry.get("entity_id", 0),
                action=action,
                payload=entry.get("payload", ""),
                device_id=device_id,
                branch_id=branch_id,
            )
            self.db.add(sync_entry)
            accepted += 1

        if accepted:
            self.db.commit()

        log_audit(
            user_id=str(current_user.id) if current_user else "system",
            action_type="sync_push",
            request=request,
            details=f"تم استلام {accepted} عناصر مزامنة من {device_id} ({branch_id})",
            db=self.db,
        )

        return {"accepted": accepted, "device_id": device_id, "branch_id": branch_id}

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

        entries = self.repo.find_since(since_dt=since_dt, device_id=device_id, limit=limit)

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
