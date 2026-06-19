"""
Platform Registry — Service Registry

Tracks all services in the unified platform.
Constitution: Principle 61 (Future Module Compatibility)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from unified_platform.registry.base import RegistryEntry, RegistryStatus


@dataclass
class ServiceEntry(RegistryEntry):
    """A registered service in the platform."""
    service_id: str = ""
    service_class: str = ""
    module: str = ""
    interface: str = ""
    is_singleton: bool = True
    health_check_interval: int = 60
    dependencies: tuple[str, ...] = ()
    exposed_via_api: bool = False
    api_version: str = "v1"


class ServiceRegistry:
    """Central registry for all platform services."""

    def __init__(self) -> None:
        self._services: dict[str, ServiceEntry] = {}

    def register(self, service: ServiceEntry) -> None:
        """Register a service."""
        self._services[service.name] = service

    def unregister(self, name: str) -> bool:
        """Unregister a service."""
        if name in self._services:
            del self._services[name]
            return True
        return False

    def get(self, name: str) -> ServiceEntry | None:
        """Get a service by name."""
        return self._services.get(name)

    def list_all(self) -> list[ServiceEntry]:
        """List all registered services."""
        return list(self._services.values())

    def list_by_module(self, module: str) -> list[ServiceEntry]:
        """List all services for a module."""
        return [s for s in self._services.values() if s.module == module]

    def list_api_exposed(self) -> list[ServiceEntry]:
        """List all services exposed via API."""
        return [s for s in self._services.values() if s.exposed_via_api]

    def update_status(self, name: str, status: RegistryStatus) -> bool:
        """Update a service's status."""
        if name in self._services:
            self._services[name].status = status
            self._services[name].updated_at = datetime.utcnow()
            return True
        return False

    def get_health_status(self) -> dict[str, str]:
        """Get health status of all services."""
        return {
            name: s.status.value
            for name, s in self._services.items()
        }

    def export_registry(self) -> dict[str, Any]:
        """Export the full registry."""
        return {
            name: {
                "name": s.name,
                "version": s.version,
                "status": s.status.value,
                "module": s.module,
                "is_singleton": s.is_singleton,
                "exposed_via_api": s.exposed_via_api,
                "api_version": s.api_version,
            }
            for name, s in self._services.items()
        }
