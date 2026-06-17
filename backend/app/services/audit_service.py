"""Audit service — business logic for audit log queries."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories import AuditRepository


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AuditRepository(db)

    def list_audit_logs(
        self,
        page: int = 1,
        limit: int = 50,
        action_type: str = "",
    ) -> tuple[list, int]:
        return self.repo.list_with_filters(page=page, limit=limit, action_type=action_type)
