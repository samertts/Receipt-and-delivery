from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.container_deps import get_user_service
from app.api.deps import require_permission
from app.core.response_envelope import paginated_response
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["المستخدمين"])


@router.get("")
def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    role: str = Query("", description="تصفية حسب الصلاحية"),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("view_users")),
):
    svc = get_user_service(db)
    items, total = svc.list_users(page=page, limit=limit, role=role)
    return paginated_response(
        items=[UserResponse.model_validate(u).model_dump(mode="json") for u in items],
        total=total,
        page=page,
        per_page=limit,
    )


@router.post("", response_model=UserResponse, status_code=201)
def create_user(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_users")),
):
    svc = get_user_service(db)
    return svc.create_user(
        username=payload.username,
        full_name=payload.full_name,
        password=payload.password,
        role=payload.role,
        request=request,
        current_user=current_user,
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("view_users")),
):
    svc = get_user_service(db)
    return svc.get_user(user_id)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    payload: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_users")),
):
    svc = get_user_service(db)
    return svc.update_user(
        user_id,
        full_name=payload.full_name,
        role=payload.role,
        password=payload.password,
        request=request,
        current_user=current_user,
    )


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_users")),
):
    svc = get_user_service(db)
    svc.delete_user(user_id, request=request, current_user=current_user)
