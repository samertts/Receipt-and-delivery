from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permission
from app.core.audit import log_audit
from app.db.session import get_db
from app.models.sync_log import SyncLog
from app.models.user import User

router = APIRouter(prefix="/sync", tags=["المزامنة"])

SYNC_ACTIONS = ("create", "update", "delete")


@router.post("/push")
def sync_push(
    payload: dict[str, Any],
    request: Any,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("sync_data")),
):
    """Receive sync payload from desktop clients and store in sync_logs."""
    entries = payload.get("entries", [])
    device_id = payload.get("device_id", "")
    branch_id = payload.get("branch_id", "")

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
        db.add(sync_entry)
        accepted += 1

    if accepted:
        db.commit()

    log_audit(
        user_id=str(current_user.id),
        action_type="sync_push",
        request=request,
        details=f"تم استلام {accepted} عناصر مزامنة من {device_id} ({branch_id})",
        db=db,
    )

    return {
        "accepted": accepted,
        "device_id": device_id,
        "branch_id": branch_id,
    }


@router.get("/pull")
def sync_pull(
    since: str = Query("", description="ISO timestamp — return entries after this time"),
    device_id: str = Query("", description="Filter by device ID"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("sync_data")),
):
    """Return sync log entries since a given timestamp."""
    query = db.query(SyncLog)

    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            query = query.filter(SyncLog.synced_at > since_dt)
        except (ValueError, TypeError):
            pass

    if device_id:
        query = query.filter(SyncLog.device_id == device_id)

    entries = query.order_by(SyncLog.synced_at.asc()).limit(limit).all()

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


@router.get("/status")
def sync_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return sync health status."""
    total = db.query(SyncLog).count()
    latest = (
        db.query(SyncLog)
        .order_by(SyncLog.synced_at.desc())
        .first()
    )

    return {
        "total_syncs": total,
        "latest_sync": latest.synced_at.isoformat() if latest else None,
        "latest_device": latest.device_id if latest else None,
        "healthy": True,
    }
