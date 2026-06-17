from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.container_deps import get_auth_service
from app.api.deps import get_current_user
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


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    svc = get_auth_service(db)
    data = svc.login(payload.username, payload.password, request=request)
    return wrap_response(
        data=TokenResponse(**data).model_dump(),
        message="تم تسجيل الدخول بنجاح",
    )


@router.post("/refresh")
def refresh_token(
    payload: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    svc = get_auth_service(db)
    data = svc.refresh_token(payload.refresh_token, request=request)
    return wrap_response(
        data=TokenResponse(**data).model_dump(),
        message="تم تحديث رمز الدخول بنجاح",
    )


@router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header else ""
    svc = get_auth_service(db)
    svc.logout(token, current_user, request=request)
    return wrap_response(data=None, message="تم تسجيل الخروج بنجاح")


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header else ""
    svc = get_auth_service(db)
    svc.change_password(
        payload.current_password,
        payload.new_password,
        current_user,
        token=token,
        request=request,
    )
    return wrap_response(data=None, message="تم تغيير كلمة المرور بنجاح")
