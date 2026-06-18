from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.container_deps import get_audit_service
from app.api.deps import require_permission
from app.core.response_envelope import paginated_response
from app.db.session import get_db
from app.models.user import User
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
    svc = get_audit_service(db)
    items, total = svc.list_audit_logs(page=page, limit=limit, action_type=action_type)
    return paginated_response(
        items=[AuditLogResponse.model_validate(i).model_dump(mode="json") for i in items],
        total=total,
        page=page,
        per_page=limit,
    )
