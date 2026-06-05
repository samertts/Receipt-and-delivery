from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.transaction import AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["سجل التدقيق"])


@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=200),
    action_type: str = Query("", description="تصفية حسب نوع الإجراء"),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("view_audit_logs")),
):
    query = db.query(AuditLog)
    if action_type:
        query = query.filter(AuditLog.action_type == action_type)
    return query.order_by(AuditLog.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
