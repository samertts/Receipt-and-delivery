from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.container_deps import get_sync_service
from app.api.deps import get_current_user, require_permission
from app.core.response_envelope import wrap_response
from app.db.session import get_db
from app.models.user import User

router = APIRouter(prefix="/sync", tags=["المزامنة"])


@router.post("/push")
def sync_push(
    payload: dict[str, Any],
    request: Any,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("sync_data")),
):
    svc = get_sync_service(db)
    data = svc.push(
        entries=payload.get("entries", []),
        device_id=payload.get("device_id", ""),
        branch_id=payload.get("branch_id", ""),
        request=request,
        current_user=current_user,
    )
    return wrap_response(
        data=data,
        message=f"تم استلام {data['accepted']} عناصر مزامنة",
    )


@router.get("/pull")
def sync_pull(
    since: str = Query("", description="ISO timestamp — return entries after this time"),
    device_id: str = Query("", description="Filter by device ID"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("sync_data")),
):
    svc = get_sync_service(db)
    data = svc.pull(since=since, device_id=device_id, limit=limit)
    return wrap_response(
        data=data,
        message=f"تم سحب {data['count']} عناصر مزامنة",
    )


@router.get("/status")
def sync_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = get_sync_service(db)
    data = svc.status()
    return wrap_response(data=data, message="حالة المزامنة")
