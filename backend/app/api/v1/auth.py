import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from jose import jwt, ExpiredSignatureError, JWTError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.audit import log_audit
from app.core.config import settings
from app.core.exceptions import UnauthorizedError, ValidationError
from app.core.security import validate_password_strength
from app.db.session import get_db
from app.models.blacklisted_token import BlacklistedToken
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


def _token_blacklisted(token: str, db: Session) -> bool:
    return db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first() is not None


def _decode_token_exp(token: str) -> datetime | None:
    try:
        payload = jwt.decode(
            token,
            settings.effective_secret_key,
            algorithms=[settings.algorithm],
            options={"verify_exp": False},
        )
        exp = payload.get("exp")
        if exp:
            return datetime.fromtimestamp(exp, tz=timezone.utc)
    except (ExpiredSignatureError, JWTError):
        pass
    return None


def _blacklist_token(token: str, db: Session, expires_at: datetime | None = None) -> None:
    existing = db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first()
    if existing:
        return
    if expires_at is None:
        expires_at = _decode_token_exp(token)
    entry = BlacklistedToken(
        token=token,
        blacklisted_at=datetime.now(timezone.utc),
        expires_at=expires_at,
    )
    db.add(entry)
    db.commit()


def _purge_expired_blacklisted_tokens(db: Session) -> int:
    now = datetime.now(timezone.utc)
    deleted = db.query(BlacklistedToken).filter(
        BlacklistedToken.expires_at.isnot(None),
        BlacklistedToken.expires_at < now,
    ).delete(synchronize_session=False)
    if deleted:
        db.commit()
    return deleted


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
    if _token_blacklisted(payload.refresh_token, db):
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

    _blacklist_token(payload.refresh_token, db)

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
        _blacklist_token(token, db)

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
        _blacklist_token(current_token, db)

    log_audit(
        user_id=str(current_user.id),
        action_type="password_changed",
        request=request,
        details=f"تغيير كلمة المرور للمستخدم: {current_user.username}",
        db=db,
    )
    # log_audit calls db.commit(), flushing the password hash and audit entry together
    return {"detail": "تم تغيير كلمة المرور بنجاح"}
