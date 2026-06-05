
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.audit import log_audit
from app.core.exceptions import UnauthorizedError
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["المصادقة"])


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        log_audit(
            user_id="unknown",
            action_type="login_failed",
            request=request,
            details=f"فشل تسجيل الدخول للمستخدم: {payload.username}",
            db=db,
        )
        raise UnauthorizedError("اسم المستخدم أو كلمة المرور غير صحيحة")

    token = create_access_token(sub=user.username, role=user.role)
    log_audit(
        user_id=str(user.id),
        action_type="login_success",
        request=request,
        details=f"تسجيل دخول ناجح: {user.username} ({user.role})",
        db=db,
    )
    return TokenResponse(access_token=token)
