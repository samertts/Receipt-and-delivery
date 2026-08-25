"""User service — business logic for user CRUD operations."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.audit import log_audit
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.security import validate_password_strength
from app.models.user import User
from app.repositories import UserRepository
from app.services.security import hash_password


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UserRepository(db)

    def list_users(
        self,
        page: int = 1,
        limit: int = 20,
        role: str = "",
        status: str = "",
    ) -> tuple[list[User], int]:
        filters = {}
        if role:
            filters["role"] = role
        if status:
            filters["status"] = status
        return self.repo.list(
            page=page, limit=limit, filters=filters, order_by="created_at", desc=True
        )

    def create_user(
        self,
        username: str,
        full_name: str,
        password: str,
        role: str = "user",
        request: Any = None,
        current_user: User | None = None,
    ) -> User:
        existing = self.repo.find_by_username(username)
        if existing:
            raise ConflictError("اسم المستخدم موجود مسبقاً")

        error = validate_password_strength(password)
        if error:
            raise ValidationError(error)

        user = self.repo.create(
            username=username,
            full_name=full_name,
            password_hash=hash_password(password),
            role=role,
        )

        log_audit(
            user_id=str(current_user.id) if current_user else "system",
            action_type="user_created",
            request=request,
            details=f"إنشاء مستخدم: {user.username} ({user.role})",
            db=self.db,
        )
        return user

    def get_user(self, user_id: str) -> User:
        user = self.repo.get(user_id)
        if not user:
            raise NotFoundError("المستخدم غير موجود")
        return user

    def update_user(
        self,
        user_id: str,
        full_name: str | None = None,
        role: str | None = None,
        status: str | None = None,
        password: str | None = None,
        request: Any = None,
        current_user: User | None = None,
    ) -> User:
        user = self.repo.get(user_id)
        if not user:
            raise NotFoundError("المستخدم غير موجود")

        is_self = current_user is not None and str(user.id) == str(current_user.id)
        if is_self and role is not None and role != current_user.role:
            raise ValidationError("لا يمكن تغيير صلاحية المستخدم الحالي")
        if is_self and status == "inactive":
            raise ValidationError("لا يمكن تعطيل المستخدم الحالي")

        target_role = role or user.role
        target_status = status or user.status
        if user.role == "admin" and user.status == "active" and (
            target_role != "admin" or target_status != "active"
        ):
            active_admins = self.db.query(User).filter(
                User.role == "admin", User.status == "active"
            ).count()
            if active_admins <= 1:
                raise ValidationError("لا يمكن إزالة أو تعطيل آخر مدير نظام")

        update_kwargs = {}
        if full_name is not None:
            update_kwargs["full_name"] = full_name
        if role is not None:
            update_kwargs["role"] = role
        if status is not None:
            update_kwargs["status"] = status
        if password:
            error = validate_password_strength(password)
            if error:
                raise ValidationError(error)
            update_kwargs["password_hash"] = hash_password(password)

        if update_kwargs:
            user = self.repo.update(user_id, **update_kwargs)

        log_audit(
            user_id=str(current_user.id) if current_user else "system",
            action_type="user_updated",
            request=request,
            details=f"تحديث مستخدم: {user.username}",
            db=self.db,
        )
        return user

    def delete_user(
        self,
        user_id: str,
        request: Any = None,
        current_user: User | None = None,
    ) -> None:
        user = self.repo.get(user_id)
        if not user:
            raise NotFoundError("المستخدم غير موجود")
        if current_user and str(user.id) == str(current_user.id):
            raise ValidationError("لا يمكن حذف المستخدم الحالي")

        if user.role == "admin":
            admin_count = (
                self.db.query(User)
                .filter(User.role == "admin", User.status == "active")
                .count()
            )
            if admin_count <= 1:
                raise ValidationError("لا يمكن حذف آخر مدير نظام")

        self.repo.delete(user_id)

        log_audit(
            user_id=str(current_user.id) if current_user else "system",
            action_type="user_deleted",
            request=request,
            details=f"حذف مستخدم: {user.username}",
            db=self.db,
        )
