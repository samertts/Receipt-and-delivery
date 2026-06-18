"""Organization service — business logic for organization CRUD operations."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.audit import log_audit
from app.core.exceptions import ConflictError, NotFoundError
from app.models.organization import Organization
from app.models.user import User
from app.repositories import OrganizationRepository


class OrganizationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = OrganizationRepository(db)

    def list_organizations(
        self,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Organization], int]:
        return self.repo.list(page=page, limit=limit, order_by="name", desc=False)

    def create_organization(
        self,
        name: str,
        code: str,
        address: str = "",
        phone: str = "",
        email: str = "",
        logo_path: str = "",
        request: Any = None,
        current_user: User | None = None,
    ) -> Organization:
        existing = self.db.query(Organization).filter(Organization.code == code).first()
        if existing:
            raise ConflictError(f"رمز المؤسسة {code} موجود مسبقاً")

        org = self.repo.create(
            name=name,
            code=code,
            address=address,
            phone=phone,
            email=email,
            logo_path=logo_path,
        )

        log_audit(
            user_id=str(current_user.id) if current_user else "system",
            action_type="org_created",
            request=request,
            details=f"إنشاء مؤسسة: {org.name} ({org.code})",
            db=self.db,
        )
        return org

    def get_organization(self, org_id: str) -> Organization:
        org = self.repo.get(org_id)
        if not org:
            raise NotFoundError("المؤسسة غير موجودة")
        return org

    def update_organization(
        self,
        org_id: str,
        name: str | None = None,
        code: str | None = None,
        address: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        request: Any = None,
        current_user: User | None = None,
    ) -> Organization:
        org = self.repo.get(org_id)
        if not org:
            raise NotFoundError("المؤسسة غير موجودة")

        update_kwargs = {}
        if name is not None:
            update_kwargs["name"] = name
        if code is not None:
            existing = self.db.query(Organization).filter(
                Organization.code == code, Organization.id != org_id,
            ).first()
            if existing:
                raise ConflictError(f"رمز المؤسسة {code} موجود مسبقاً")
            update_kwargs["code"] = code
        if address is not None:
            update_kwargs["address"] = address
        if phone is not None:
            update_kwargs["phone"] = phone
        if email is not None:
            update_kwargs["email"] = email

        if update_kwargs:
            org = self.repo.update(org_id, **update_kwargs)

        log_audit(
            user_id=str(current_user.id) if current_user else "system",
            action_type="org_updated",
            request=request,
            details=f"تحديث مؤسسة: {org.name}",
            db=self.db,
        )
        return org

    def delete_organization(
        self,
        org_id: str,
        request: Any = None,
        current_user: User | None = None,
    ) -> None:
        org = self.repo.get(org_id)
        if not org:
            raise NotFoundError("المؤسسة غير موجودة")
        
        # Check for associated transactions
        from app.models.transaction import Transaction
        from sqlalchemy import or_
        
        has_transactions = self.db.query(Transaction).filter(
            or_(
                Transaction.sender_organization_id == org_id,
                Transaction.receiver_organization_id == org_id,
            )
        ).first()
        
        if has_transactions:
            raise ConflictError("Cannot delete organization with associated transactions")
        
        self.repo.delete(org_id)

        log_audit(
            user_id=str(current_user.id) if current_user else "system",
            action_type="org_deleted",
            request=request,
            details=f"حذف مؤسسة: {org.name} ({org.code})",
            db=self.db,
        )
