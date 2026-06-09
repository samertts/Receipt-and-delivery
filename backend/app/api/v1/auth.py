import time

from fastapi import APIRouter, Depends, Request
from jose import jwt
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.audit import log_audit
from app.core.config import settings
from app.core.exceptions import UnauthorizedError, ValidationError
from app.core.security import validate_password_strength
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from app.services.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["المصادقة"])

_blacklisted_tokens: set[str] = set()


def _token_blacklisted(token: str) -> bool:
    return token in _blacklisted_tokens


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

    if user.status != "active":
        log_audit(
            user_id=str(user.id),
            action_type="login_blocked",
            request=request,
            details=f"محاولة دخول من حساب غير نشط: {user.username}",
            db=db,
        )
        raise UnauthorizedError("الحساب غير نشط")

    access_token = create_access_token(sub=user.username, role=user.role)
    refresh_token = create_refresh_token(sub=user.username)
    log_audit(
        user_id=str(user.id),
        action_type="login_success",
        request=request,
        details=f"تسجيل دخول ناجح: {user.username} ({user.role})",
        db=db,
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    if _token_blacklisted(payload.refresh_token):
        raise UnauthorizedError("رمز التحديث غير صالح")

    try:
        token_data = jwt.decode(
            payload.refresh_token,
            settings.effective_secret_key,
            algorithms=[settings.algorithm],
        )
    except Exception as exc:
        raise UnauthorizedError("رمز التحديث غير صالح أو منتهي الصلاحية") from exc

    if token_data.get("type") != "refresh":
        raise UnauthorizedError("نوع الرمز غير صحيح")

    username = token_data.get("sub", "")
    user = db.query(User).filter(User.username == username).first()
    if not user or user.status != "active":
        raise UnauthorizedError("المستخدم غير موجود أو غير نشط")

    _blacklisted_tokens.add(payload.refresh_token)

    new_access = create_access_token(sub=user.username, role=user.role)
    new_refresh = create_refresh_token(sub=user.username)
    log_audit(
        user_id=str(user.id),
        action_type="token_refreshed",
        request=request,
        details=f"تحديث رمز الدخول للمستخدم: {user.username}",
        db=db,
    )
    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


@router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header else ""
    if token:
        _blacklisted_tokens.add(token)

    log_audit(
        user_id=str(current_user.id),
        action_type="logout",
        request=request,
        details=f"تسجيل خروج: {current_user.username}",
        db=db,
    )
    return {"detail": "تم تسجيل الخروج بنجاح"}


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise UnauthorizedError("كلمة المرور الحالية غير صحيحة")

    pwd_error = validate_password_strength(payload.new_password)
    if pwd_error:
        raise ValidationError(pwd_error)

    current_user.password_hash = hash_password(payload.new_password)

    auth_header = request.headers.get("Authorization", "")
    current_token = auth_header.replace("Bearer ", "") if auth_header else ""
    if current_token:
        _blacklisted_tokens.add(current_token)

    log_audit(
        user_id=str(current_user.id),
        action_type="password_changed",
        request=request,
        details=f"تغيير كلمة المرور للمستخدم: {current_user.username}",
        db=db,
    )
    # log_audit calls db.commit(), flushing the password hash and audit entry together
    return {"detail": "تم تغيير كلمة المرور بنجاح"}
