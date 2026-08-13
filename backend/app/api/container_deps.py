"""Container-based FastAPI dependency providers.

These functions resolve services from the centralized container,
ensuring consistent dependency injection across all API routes.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.container import get_container, ServiceContainer


def get_container_instance() -> ServiceContainer:
    return get_container()


def get_auth_service(db: Session):
    container = get_container_instance()
    container.override("db", db)
    from app.services.auth_service import AuthService

    return AuthService(db)


def get_user_service(db: Session):
    from app.services.user_service import UserService

    return UserService(db)


def get_organization_service(db: Session):
    from app.services.organization_service import OrganizationService

    return OrganizationService(db)


def get_transaction_service(db: Session):
    from app.services.transaction_service import TransactionService
    from app.core.config import settings

    gula_client = None
    if settings.gula_base_url and settings.gula_access_token:
        from app.integrations.gula_client import GulaEventClient

        gula_client = GulaEventClient(
            base_url=settings.gula_base_url,
            access_token=settings.gula_access_token,
            timeout=settings.gula_timeout_seconds,
            max_retries=settings.gula_max_retries,
        )
    return TransactionService(db, gula_client=gula_client, tenant_id=settings.gula_tenant_id)


def get_audit_service(db: Session):
    from app.services.audit_service import AuditService

    return AuditService(db)


def get_sync_service(db: Session):
    from app.services.sync_service import SyncService

    return SyncService(db)
