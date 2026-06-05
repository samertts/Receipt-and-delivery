from typing import Optional

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

ROLE_HIERARCHY = {
    "auditor": ["auditor"],
    "user": ["user", "auditor"],
    "supervisor": ["supervisor", "user", "auditor"],
    "admin": ["admin", "supervisor", "user", "auditor"],
}

PERMISSION_ROLES = {
    "view_dashboard": ["admin", "supervisor", "user", "auditor"],
    "view_transactions": ["admin", "supervisor", "user", "auditor"],
    "create_transaction": ["admin", "supervisor", "user"],
    "edit_transaction": ["admin", "supervisor"],
    "delete_transaction": ["admin"],
    "manage_users": ["admin"],
    "view_users": ["admin", "supervisor"],
    "view_audit_logs": ["admin", "auditor"],
    "manage_organizations": ["admin", "supervisor"],
    "view_organizations": ["admin", "supervisor", "user", "auditor"],
    "view_reports": ["admin", "supervisor"],
    "manage_settings": ["admin"],
    "manage_backups": ["admin"],
}


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if token is None:
        raise UnauthorizedError("لم يتم تسجيل الدخول")
    try:
        payload = jwt.decode(
            token, settings.effective_secret_key, algorithms=[settings.algorithm],
        )
        username: str = payload.get("sub", "")
        if not username:
            raise UnauthorizedError("رمز غير صالح")
    except JWTError as exc:
        raise UnauthorizedError("رمز غير صالح أو منتهي الصلاحية") from exc

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise UnauthorizedError("المستخدم غير موجود")
    return user


def require_permission(permission: str):
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        allowed_roles = PERMISSION_ROLES.get(permission, [])
        if current_user.role not in allowed_roles:
            raise ForbiddenError
        return current_user

    return permission_checker
