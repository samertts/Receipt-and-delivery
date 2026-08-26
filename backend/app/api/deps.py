import secrets
from typing import Optional

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.cookie_auth import CSRF_COOKIE, CSRF_HEADER, is_browser_api_request, request_token
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.db.session import get_db
from app.core.rbac import PERMISSION_ROLES
from app.models.blacklisted_token import BlacklistedToken
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def verify_csrf(request: Request) -> None:
    if not is_browser_api_request(request) or request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    # Explicit Bearer clients are non-browser compatibility clients; CSRF is
    # required for cookie-authenticated browser requests only.
    if request.headers.get("Authorization", "").lower().startswith("bearer "):
        return
    cookie_token = request.cookies.get(CSRF_COOKIE, "")
    header_token = request.headers.get(CSRF_HEADER, "")
    if not cookie_token or not header_token or not secrets.compare_digest(cookie_token, header_token):
        raise ForbiddenError("رمز حماية الطلب غير صالح")


def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    verify_csrf(request)
    token = request_token(request, token)
    if not token:
        raise UnauthorizedError("لم يتم تسجيل الدخول")
    try:
        payload = jwt.decode(
            token,
            settings.effective_secret_key,
            algorithms=[settings.algorithm],
        )
        if payload.get("type") != "access":
            raise UnauthorizedError("نوع الرمز غير صحيح")
        username: str = payload.get("sub", "")
        if not username:
            raise UnauthorizedError("رمز غير صالح")
    except JWTError as exc:
        raise UnauthorizedError("رمز غير صالح أو منتهي الصلاحية") from exc

    if db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first():
        raise UnauthorizedError("تم إبطال الرمز")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise UnauthorizedError("المستخدم غير موجود")
    if user.status != "active":
        raise ForbiddenError("الحساب غير نشط")
    return user


def require_permission(permission: str):
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        allowed_roles = PERMISSION_ROLES.get(permission, ())
        if current_user.role not in allowed_roles:
            raise ForbiddenError()
        return current_user

    return permission_checker
