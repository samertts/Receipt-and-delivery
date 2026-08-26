from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.container_deps import get_auth_service
from app.api.deps import get_current_user, verify_csrf
from app.core.cookie_auth import (
    REFRESH_COOKIE,
    clear_session_cookies,
    is_browser_api_request,
    request_token,
    set_session_cookies,
)
from app.core.rbac import ROLE_PERMISSIONS, ROLES, permissions_for_role
from app.core.response_envelope import wrap_response
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["المصادقة"])


def _auth_response(data: dict, request: Request, response: Response) -> dict:
    if is_browser_api_request(request):
        set_session_cookies(response, data, request)
        return {"authenticated": True}
    return TokenResponse(**data).model_dump()


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    svc = get_auth_service(db)
    data = svc.login(payload.username, payload.password, request=request)
    return wrap_response(
        data=_auth_response(data, request, response),
        message="تم تسجيل الدخول بنجاح",
    )


@router.post("/refresh")
def refresh_token(
    request: Request,
    response: Response,
    payload: RefreshTokenRequest | None = None,
    db: Session = Depends(get_db),
):
    verify_csrf(request)
    token = request_token(
        request,
        payload.refresh_token if payload else None,
        cookie_name=REFRESH_COOKIE,
    )
    if not token:
        from app.core.exceptions import UnauthorizedError

        raise UnauthorizedError("رمز التحديث غير موجود")
    svc = get_auth_service(db)
    data = svc.refresh_token(token, request=request)
    if is_browser_api_request(request):
        set_session_cookies(response, data, request)
        result = {"authenticated": True}
    else:
        result = TokenResponse(**data).model_dump()
    return wrap_response(data=result, message="تم تحديث رمز الدخول بنجاح")


@router.get("/me")
def current_user_profile(current_user: User = Depends(get_current_user)):
    return wrap_response(
        data={
            "id": str(current_user.id),
            "username": current_user.username,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "permissions": permissions_for_role(current_user.role),
            "roles": list(ROLES),
            "role_permissions": {role: list(perms) for role, perms in ROLE_PERMISSIONS.items()},
        },
        message="تم تحميل ملف المستخدم والصلاحيات بنجاح",
    )


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    auth_header = request.headers.get("Authorization", "")
    bearer_token = auth_header[7:] if auth_header.lower().startswith("bearer ") else None
    token = request_token(request, bearer_token)
    svc = get_auth_service(db)
    svc.logout(token, current_user, request=request)
    if is_browser_api_request(request):
        clear_session_cookies(response)
    return wrap_response(data=None, message="تم تسجيل الخروج بنجاح")


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    auth_header = request.headers.get("Authorization", "")
    bearer_token = auth_header[7:] if auth_header.lower().startswith("bearer ") else None
    token = request_token(request, bearer_token)
    svc = get_auth_service(db)
    svc.change_password(
        payload.current_password,
        payload.new_password,
        current_user,
        token=token,
        request=request,
    )
    return wrap_response(data=None, message="تم تغيير كلمة المرور بنجاح")
