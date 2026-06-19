"""Authentication service — business logic for login, token refresh, logout, password change."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from jose import jwt, ExpiredSignatureError, JWTError
from sqlalchemy.orm import Session

from app.core.audit import log_audit
from app.core.config import settings
from app.core.exceptions import UnauthorizedError, ValidationError
from app.core.security import validate_password_strength
from app.models.blacklisted_token import BlacklistedToken
from app.models.user import User
from app.repositories import UserRepository
from app.services.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UserRepository(db)

    def login(
        self, username: str, password: str, request: Any = None
    ) -> dict[str, Any]:
        user = self.user_repo.find_by_username(username)
        if not user or not verify_password(password, user.password_hash):
            log_audit(
                user_id="unknown",
                action_type="login_failed",
                request=request,
                details=f"فشل تسجيل الدخول للمستخدم: {username}",
                db=self.db,
            )
            raise UnauthorizedError("اسم المستخدم أو كلمة المرور غير صحيحة")

        if user.status != "active":
            log_audit(
                user_id=str(user.id),
                action_type="login_blocked",
                request=request,
                details=f"محاولة دخول من حساب غير نشط: {user.username}",
                db=self.db,
            )
            raise UnauthorizedError("الحساب غير نشط")

        access_token = create_access_token(sub=user.username, role=user.role)
        refresh_token = create_refresh_token(sub=user.username)
        log_audit(
            user_id=str(user.id),
            action_type="login_success",
            request=request,
            details=f"تسجيل دخول ناجح: {user.username} ({user.role})",
            db=self.db,
        )
        return {"access_token": access_token, "refresh_token": refresh_token}

    def refresh_token(self, token: str, request: Any = None) -> dict[str, Any]:
        if self._token_blacklisted(token):
            raise UnauthorizedError("رمز التحديث غير صالح")

        try:
            token_data = jwt.decode(
                token,
                settings.effective_secret_key,
                algorithms=[settings.algorithm],
            )
        except Exception as exc:
            raise UnauthorizedError("رمز التحديث غير صالح أو منتهي الصلاحية") from exc

        if token_data.get("type") != "refresh":
            raise UnauthorizedError("نوع الرمز غير صحيح")

        username = token_data.get("sub", "")
        user = self.user_repo.find_by_username(username)
        if not user or user.status != "active":
            raise UnauthorizedError("المستخدم غير موجود أو غير نشط")

        self._blacklist_token(token)

        new_access = create_access_token(sub=user.username, role=user.role)
        new_refresh = create_refresh_token(sub=user.username)
        log_audit(
            user_id=str(user.id),
            action_type="token_refreshed",
            request=request,
            details=f"تحديث رمز الدخول للمستخدم: {user.username}",
            db=self.db,
        )
        return {"access_token": new_access, "refresh_token": new_refresh}

    def logout(self, token: str, current_user: User, request: Any = None) -> None:
        if token:
            self._blacklist_token(token)
        log_audit(
            user_id=str(current_user.id),
            action_type="logout",
            request=request,
            details=f"تسجيل خروج: {current_user.username}",
            db=self.db,
        )

    def change_password(
        self,
        current_password: str,
        new_password: str,
        current_user: User,
        token: str = "",
        request: Any = None,
    ) -> None:
        if not verify_password(current_password, current_user.password_hash):
            raise UnauthorizedError("كلمة المرور الحالية غير صحيحة")

        pwd_error = validate_password_strength(new_password)
        if pwd_error:
            raise ValidationError(pwd_error)

        current_user.password_hash = hash_password(new_password)

        if token:
            self._blacklist_token(token)

        log_audit(
            user_id=str(current_user.id),
            action_type="password_changed",
            request=request,
            details=f"تغيير كلمة المرور للمستخدم: {current_user.username}",
            db=self.db,
        )

    def _token_blacklisted(self, token: str) -> bool:
        return (
            self.db.query(BlacklistedToken)
            .filter(
                BlacklistedToken.token == token,
            )
            .first()
            is not None
        )

    def _blacklist_token(self, token: str, expires_at: datetime | None = None) -> None:
        existing = (
            self.db.query(BlacklistedToken)
            .filter(
                BlacklistedToken.token == token,
            )
            .first()
        )
        if existing:
            return
        if expires_at is None:
            expires_at = self._decode_token_exp(token)
        entry = BlacklistedToken(
            token=token,
            blacklisted_at=datetime.now(timezone.utc),
            expires_at=expires_at,
        )
        self.db.add(entry)
        self.db.commit()

    @staticmethod
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

    @staticmethod
    def purge_expired_blacklisted_tokens(db: Session) -> int:
        now = datetime.now(timezone.utc)
        deleted = (
            db.query(BlacklistedToken)
            .filter(
                BlacklistedToken.expires_at.isnot(None),
                BlacklistedToken.expires_at < now,
            )
            .delete(synchronize_session=False)
        )
        if deleted:
            db.commit()
        return deleted
