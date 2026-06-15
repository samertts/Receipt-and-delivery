from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.response_envelope import paginated_response
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.transaction import AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["سجل التدقيق"])


@router.get("")
def list_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=200),
    action_type: str = Query("", description="تصفية حسب نوع الإجراء"),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("view_audit_logs")),
):
    repo = BaseRepository(AuditLog, db)
    filters = {}
    if action_type:
        filters["action_type"] = action_type
    items, total = repo.list(page=page, limit=limit, filters=filters, order_by="created_at", desc=True)
    return paginated_response(
        items=[AuditLogResponse.model_validate(i).model_dump(mode="json") for i in items],
        total=total,
        page=page,
        per_page=limit,
    )
