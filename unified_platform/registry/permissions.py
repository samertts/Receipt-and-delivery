"""
Platform Registry — Permission Registry

Centralized permission management across all modules.
Constitution: Principle 29 (One Identity), Principle 38 (Least Privilege)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from unified_platform.registry.base import RegistryEntry


@dataclass
class PermissionEntry(RegistryEntry):
    """A registered permission in the platform."""
    permission_id: str = ""
    resource: str = ""
    action: str = ""
    module: str = ""
    description: str = ""
    is_system: bool = False
    requires_approval: bool = False
    risk_level: str = "low"  # low, medium, high, critical


class PermissionRegistry:
    """Central registry for all platform permissions."""

    def __init__(self) -> None:
        self._permissions: dict[str, PermissionEntry] = {}
        self._role_permissions: dict[str, set[str]] = {}

    def register(self, permission: PermissionEntry) -> None:
        """Register a permission."""
        self._permissions[permission.name] = permission

    def unregister(self, name: str) -> bool:
        """Unregister a permission."""
        if name in self._permissions:
            del self._permissions[name]
            return True
        return False

    def get(self, name: str) -> PermissionEntry | None:
        """Get a permission by name."""
        return self._permissions.get(name)

    def list_all(self) -> list[PermissionEntry]:
        """List all registered permissions."""
        return list(self._permissions.values())

    def list_by_module(self, module: str) -> list[PermissionEntry]:
        """List all permissions for a module."""
        return [p for p in self._permissions.values() if p.module == module]

    def list_by_risk_level(self, risk_level: str) -> list[PermissionEntry]:
        """List all permissions with a specific risk level."""
        return [p for p in self._permissions.values() if p.risk_level == risk_level]

    def list_system_permissions(self) -> list[PermissionEntry]:
        """List all system permissions."""
        return [p for p in self._permissions.values() if p.is_system]

    def assign_to_role(self, permission_name: str, role: str) -> None:
        """Assign a permission to a role."""
        if role not in self._role_permissions:
            self._role_permissions[role] = set()
        self._role_permissions[role].add(permission_name)

    def revoke_from_role(self, permission_name: str, role: str) -> bool:
        """Revoke a permission from a role."""
        if role in self._role_permissions:
            self._role_permissions[role].discard(permission_name)
            return True
        return False

    def get_role_permissions(self, role: str) -> set[str]:
        """Get all permissions for a role."""
        return self._role_permissions.get(role, set())

    def check_permission(self, role: str, permission: str) -> bool:
        """Check if a role has a specific permission."""
        return permission in self._role_permissions.get(role, set())

    def export_registry(self) -> dict[str, Any]:
        """Export the full registry."""
        return {
            "permissions": {
                name: {
                    "name": p.name,
                    "resource": p.resource,
                    "action": p.action,
                    "module": p.module,
                    "risk_level": p.risk_level,
                    "is_system": p.is_system,
                }
                for name, p in self._permissions.items()
            },
            "role_permissions": {
                role: list(perms)
                for role, perms in self._role_permissions.items()
            },
        }
