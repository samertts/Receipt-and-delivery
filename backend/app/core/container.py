"""Centralized dependency injection container for the backend API.

Registers all repositories and services, providing consistent dependency
resolution and lifecycle management across the application.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.db.session import SessionLocal


class ServiceContainer:
    """Lightweight DI container with lazy singleton resolution.

    Services are registered as factory callables and resolved on first access.
    Once resolved, instances are cached as singletons for the lifetime of the
    container.  The container may be reset (e.g. between test cases).
    """

    def __init__(self) -> None:
        self._factories: dict[str, callable] = {}
        self._instances: dict[str, Any] = {}

    def register(self, name: str, factory: callable) -> None:
        self._factories[name] = factory
        self._instances.pop(name, None)

    def resolve(self, name: str) -> Any:
        if name not in self._instances:
            if name not in self._factories:
                raise KeyError(f"Service '{name}' is not registered")
            self._instances[name] = self._factories[name](self)
        return self._instances[name]

    def override(self, name: str, instance: Any) -> None:
        self._instances[name] = instance

    def reset(self) -> None:
        self._instances.clear()

    def registered(self) -> list[str]:
        return list(self._factories.keys())


_container: ServiceContainer | None = None


def get_container() -> ServiceContainer:
    global _container
    if _container is None:
        _container = ServiceContainer()
        _register_defaults(_container)
    return _container


def reset_container() -> None:
    global _container
    _container = None


def _register_defaults(container: ServiceContainer) -> None:
    from app.repositories import (
        AuditRepository,
        OrganizationRepository,
        SyncRepository,
        TransactionRepository,
        UserRepository,
    )

    def _db_session_factory(_container: ServiceContainer) -> Session:
        return SessionLocal()

    container.register("db", _db_session_factory)

    container.register(
        "user_repository",
        lambda c: UserRepository(c.resolve("db")),
    )
    container.register(
        "organization_repository",
        lambda c: OrganizationRepository(c.resolve("db")),
    )
    container.register(
        "transaction_repository",
        lambda c: TransactionRepository(c.resolve("db")),
    )
    container.register(
        "audit_repository",
        lambda c: AuditRepository(c.resolve("db")),
    )
    container.register(
        "sync_repository",
        lambda c: SyncRepository(c.resolve("db")),
    )

    from app.services.auth_service import AuthService
    from app.services.user_service import UserService
    from app.services.organization_service import OrganizationService
    from app.services.transaction_service import TransactionService
    from app.services.audit_service import AuditService
    from app.services.sync_service import SyncService

    container.register(
        "auth_service",
        lambda c: AuthService(c.resolve("db")),
    )
    container.register(
        "user_service",
        lambda c: UserService(c.resolve("db")),
    )
    container.register(
        "organization_service",
        lambda c: OrganizationService(c.resolve("db")),
    )
    container.register(
        "transaction_service",
        lambda c: TransactionService(c.resolve("db")),
    )
    container.register(
        "audit_service",
        lambda c: AuditService(c.resolve("db")),
    )
    container.register(
        "sync_service",
        lambda c: SyncService(c.resolve("db")),
    )
