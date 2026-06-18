"""Dependency injection container for the desktop application.

Registers all services and provides centralized dependency resolution.
"""

from __future__ import annotations

from typing import Any


class Container:
    """Simple dependency injection container.

    Services are registered as factory callables and resolved on first access.
    Once resolved, a service instance is cached as a singleton.
    """

    def __init__(self):
        self._factories: dict[str, callable] = {}
        self._instances: dict[str, Any] = {}

    def register(self, name: str, factory: callable) -> None:
        self._factories[name] = factory
        if name in self._instances:
            del self._instances[name]

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


_container: Container | None = None


def get_container() -> Container:
    global _container
    if _container is None:
        _container = Container()
        _register_defaults(_container)
    return _container


def reset_container() -> None:
    global _container
    _container = None


class OrgService:
    def __init__(self, db):
        self._db = db

    def list(self, *, active_only=False):
        from lab_system.app.services.org_service import list_organizations
        return list_organizations(active_only=active_only)

    def upsert(self, payload, user=None):
        from lab_system.app.services.org_service import upsert_organization
        return upsert_organization(payload, user=user)


class ReportService:
    def __init__(self, db):
        self._db = db

    def receipt_summary(self, date_from="", date_to="", group_by="day"):
        from lab_system.app.services.report_service import receipt_summary
        return receipt_summary(date_from, date_to, group_by)

    def daily_report(self, date_from="", date_to=""):
        from lab_system.app.services.report_service import daily_report
        return daily_report(date_from, date_to)

    def monthly_report(self, year=None):
        from lab_system.app.services.report_service import monthly_report
        return monthly_report(year)

    def institution_statistics(self, date_from="", date_to=""):
        from lab_system.app.services.report_service import institution_statistics
        return institution_statistics(date_from, date_to)

    def rejection_statistics(self, date_from="", date_to=""):
        from lab_system.app.services.report_service import rejection_statistics
        return rejection_statistics(date_from, date_to)

    def export_receipts_csv(self, file_path, q="", status="", date_from="", date_to=""):
        from lab_system.app.services.report_service import export_receipts_csv
        return export_receipts_csv(file_path, q, status, date_from, date_to)

    def receipt_count(self) -> int:
        from lab_system.app.database.repository import BaseRepository
        repo = BaseRepository()
        row = repo.fetch_one(
            "SELECT COUNT(*) FROM receipts WHERE deleted_at IS NULL OR deleted_at = ''",
        )
        return row[0] if row else 0

    def recent_audit_logs(self, limit: int = 10):
        from lab_system.app.database.repository import BaseRepository
        repo = BaseRepository()
        return repo.fetch_all(
            "SELECT action, timestamp, details FROM audit_logs ORDER BY id DESC LIMIT ?",
            (limit,),
        )

    def recent_backups(self, limit: int = 5):
        from lab_system.app.database.repository import BaseRepository
        repo = BaseRepository()
        return repo.fetch_all(
            "SELECT backup_file, created_at FROM backups ORDER BY id DESC LIMIT ?",
            (limit,),
        )


class RecoveryService:
    def __init__(self, db):
        self._db = db

    def verify_backup(self, path):
        from lab_system.app.services.recovery_service import verify_backup
        return verify_backup(path)

    def list_backups(self):
        from lab_system.app.services.recovery_service import list_backups
        return list_backups()

    def restore_from_backup(self, backup_path, user=None):
        from lab_system.app.services.recovery_service import restore_from_backup
        return restore_from_backup(backup_path, user=user)

    def delete_backup(self, backup_path, user=None):
        from lab_system.app.services.recovery_service import delete_backup
        return delete_backup(backup_path, user=user)

    def validate_recovery(self, backup_path, user=None):
        from lab_system.app.services.recovery_service import validate_recovery
        return validate_recovery(backup_path, user=user)

    def attempt_recovery(self, user=None):
        from lab_system.app.services.recovery_service import attempt_recovery
        return attempt_recovery(user=user)

    def list_snapshots(self):
        from lab_system.app.services.recovery_service import list_snapshots
        return list_snapshots()


class BackupService:
    def __init__(self, db):
        self._db = db

    def create_backup(self, user_id=None, notes="", user=None):
        from lab_system.app.services.backup_service import create_backup
        return create_backup(user_id, notes, user=user)


class CatalogService:
    def __init__(self, db):
        self._db = db

    def list_transaction_types(self):
        from lab_system.app.services.catalog_service import list_transaction_types
        return list_transaction_types()

    def list_sample_types(self):
        from lab_system.app.services.catalog_service import list_sample_types
        return list_sample_types()

    def seed_defaults(self):
        from lab_system.app.services.catalog_service import seed_defaults
        return seed_defaults()


class SettingsService:
    def __init__(self, db):
        self._db = db
        from lab_system.app.database.db import DEFAULT_SETTINGS
        self._defaults = DEFAULT_SETTINGS

    def get(self, key: str, default: str = "") -> str:
        from lab_system.app.database.repository import BaseRepository
        repo = BaseRepository()
        row = repo.fetch_one("SELECT value FROM settings WHERE key=?", (key,))
        return row[0] if row else default

    def set(self, key: str, value: str) -> None:
        from lab_system.app.database.repository import BaseRepository
        repo = BaseRepository()
        repo.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, value))

    def all(self) -> dict[str, str]:
        from lab_system.app.database.repository import BaseRepository
        repo = BaseRepository()
        rows = repo.fetch_all("SELECT key, value FROM settings")
        return {r[0]: r[1] for r in rows}


def _register_defaults(container: Container) -> None:
    from lab_system.app.database import db as _db
    from lab_system.app.database.repository import BaseRepository

    from lab_system.app.services.receipt_service import (
        ReceiptService,
    )
    from lab_system.app.services.user_service import (
        UserService,
    )

    container.register("db", lambda c: _db)
    container.register("base_repository", lambda c: BaseRepository())

    container.register("receipt_service", lambda c: ReceiptService(c.resolve("db")))
    container.register("user_service", lambda c: UserService(c.resolve("db")))
    container.register("org_service", lambda c: OrgService(c.resolve("db")))
    container.register("report_service", lambda c: ReportService(c.resolve("db")))
    container.register("recovery_service", lambda c: RecoveryService(c.resolve("db")))
    container.register("backup_service", lambda c: BackupService(c.resolve("db")))
    container.register("catalog_service", lambda c: CatalogService(c.resolve("db")))
