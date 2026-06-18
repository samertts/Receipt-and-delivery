from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.container_deps import get_sync_service
from app.api.deps import get_current_user, require_permission
from app.core.response_envelope import wrap_response
from app.db.session import get_db
from app.models.user import User

router = APIRouter(prefix="/sync", tags=["المزامنة"])


class SyncEntry(BaseModel):
    entity_type: str = Field(..., max_length=50)
    entity_id: int
    action: str = Field(..., pattern="^(create|update|delete)$")
    payload: dict[str, Any] = Field(default_factory=dict)


class SyncPushRequest(BaseModel):
    entries: list[SyncEntry] = Field(..., max_length=1000)
    device_id: str = Field(default="", max_length=100)
    branch_id: str = Field(default="", max_length=100)


@router.post("/push")
def sync_push(
    request: SyncPushRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("sync_data")),
):
    svc = get_sync_service(db)
    data = svc.push(
        entries=[entry.model_dump() for entry in request.entries],
        device_id=request.device_id,
        branch_id=request.branch_id,
        request=None,
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
