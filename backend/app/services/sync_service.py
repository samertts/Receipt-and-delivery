from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import log_audit
from app.models.sync_log import SyncLog
from app.models.user import User
from app.repositories import SyncRepository

SYNC_ACTIONS = ("create", "update", "delete")
MAX_SYNC_PAYLOAD_BYTES = 5 * 1024 * 1024


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
        idempotent = 0
        conflicts: list[dict[str, Any]] = []
        for entry in entries:
            action = entry.get("action", "")
            entity_type = str(entry.get("entity_type", "")).strip()
            entity_id = entry.get("entity_id")
            payload = entry.get("payload", {})
            idempotency_key = str(entry.get("idempotency_key", "")).strip()
            if (
                action not in SYNC_ACTIONS
                or not entity_type
                or not isinstance(entity_id, int)
                or not idempotency_key
                or len(idempotency_key) > 160
            ):
                conflicts.append(
                    {
                        "entity_type": entity_type,
                        "entity_id": entity_id,
                        "reason": "invalid_entry",
                    }
                )
                continue
            try:
                serialized_payload = json.dumps(
                    payload, ensure_ascii=False, separators=(",", ":")
                )
            except (TypeError, ValueError):
                conflicts.append(
                    {"entity_type": entity_type, "entity_id": entity_id, "reason": "invalid_payload"}
                )
                continue
            if len(serialized_payload.encode("utf-8")) > MAX_SYNC_PAYLOAD_BYTES:
                conflicts.append(
                    {"entity_type": entity_type, "entity_id": entity_id, "reason": "payload_too_large"}
                )
                continue

            existing_key = (
                self.db.query(SyncLog)
                .filter(SyncLog.idempotency_key == idempotency_key)
                .first()
            )
            if existing_key:
                if (
                    existing_key.entity_type == entity_type
                    and existing_key.entity_id == entity_id
                    and existing_key.action == action
                    and (existing_key.payload or "{}") == serialized_payload
                ):
                    idempotent += 1
                else:
                    conflicts.append(
                        {
                            "entity_type": entity_type,
                            "entity_id": entity_id,
                            "reason": "idempotency_key_reuse",
                        }
                    )
                continue

            existing = (
                self.db.query(SyncLog)
                .filter(
                    SyncLog.entity_type == entity_type,
                    SyncLog.entity_id == entity_id,
                    SyncLog.branch_id == branch_id,
                )
                .order_by(SyncLog.synced_at.desc())
                .first()
            )
            if existing:
                # A different idempotency key is a distinct event, even when its
                # payload happens to match; never collapse custody history by entity.
                conflicts.append(
                    {
                        "entity_type": entity_type,
                        "entity_id": entity_id,
                        "action": action,
                        "reason": "entity_already_synced",
                    }
                )
                continue

            self.db.add(
                SyncLog(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    action=action,
                    payload=serialized_payload,
                    device_id=device_id,
                    branch_id=branch_id,
                    idempotency_key=idempotency_key,
                    synced_at=datetime.now(timezone.utc),
                )
            )
            accepted += 1

        if accepted:
            try:
                self.db.commit()
            except IntegrityError:
                self.db.rollback()
                conflicts.extend(
                    {
                        "entity_type": entry.get("entity_type", ""),
                        "entity_id": entry.get("entity_id"),
                        "reason": "duplicate_idempotency_key",
                    }
                    for entry in entries
                )
                accepted = 0

        log_audit(
            user_id=str(current_user.id) if current_user else "system",
            action_type="sync_push",
            request=request,
            details=(
                f"تم استلام {accepted} عناصر مزامنة من {device_id} ({branch_id})؛ "
                f"مكرر: {idempotent}، تعارضات للمراجعة: {len(conflicts)}"
            ),
            db=self.db,
        )

        return {
            "accepted": accepted,
            "idempotent": idempotent,
            "conflicts": len(conflicts),
            "conflict_items": conflicts[:100],
            "device_id": device_id,
            "branch_id": branch_id,
        }

    def pull(
        self,
        since: str = "",
        device_id: str = "",
        branch_id: str = "",
        limit: int = 100,
    ) -> dict[str, Any]:
        since_dt = None
        if since:
            try:
                since_dt = datetime.fromisoformat(since)
            except (ValueError, TypeError):
                pass

        entries = self.repo.find_since(
            since_dt=since_dt,
            device_id=device_id,
            branch_id=branch_id,
            limit=min(max(limit, 1), 1000),
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
                    "branch_id": e.branch_id,
                    "synced_at": e.synced_at.isoformat() if e.synced_at else "",
                }
                for e in entries
            ],
            "count": len(entries),
            "since": since,
            "branch_id": branch_id,
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
