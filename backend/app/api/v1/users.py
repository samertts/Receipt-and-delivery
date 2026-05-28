from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permission
from app.core.audit import log_audit
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.security import validate_password_strength
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserResponse, UserUpdate
from app.services.security import hash_password

router = APIRouter(prefix="/users", tags=["المستخدمين"])


@router.get("", response_model=list[UserResponse])
def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    role: str = Query("", description="تصفية حسب الصلاحية"),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("view_users")),
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit).all()


@router.post("", response_model=UserResponse, status_code=201)
def create_user(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_users")),
):
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise ConflictError("اسم المستخدم موجود مسبقاً")

    error = validate_password_strength(payload.password)
    if error:
        raise ValidationError(error)

    user = User(
        username=payload.username,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_audit(
        user_id=str(current_user.id),
        action_type="user_created",
        request=request,
        details=f"إنشاء مستخدم: {user.username} ({user.role})",
        db=db,
    )
    return user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("view_users")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("المستخدم غير موجود")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    payload: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_users")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("المستخدم غير موجود")

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role is not None:
        user.role = payload.role
    if payload.password:
        error = validate_password_strength(payload.password)
        if error:
            raise ValidationError(error)
        user.password_hash = hash_password(payload.password)

    db.commit()
    db.refresh(user)

    log_audit(
        user_id=str(current_user.id),
        action_type="user_updated",
        request=request,
        details=f"تحديث مستخدم: {user.username}",
        db=db,
    )
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_users")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("المستخدم غير موجود")
    if str(user.id) == str(current_user.id):
        raise ValidationError("لا يمكن حذف المستخدم الحالي")

    db.delete(user)
    db.commit()

    log_audit(
        user_id=str(current_user.id),
        action_type="user_deleted",
        request=request,
        details=f"حذف مستخدم: {user.username}",
        db=db,
    )
