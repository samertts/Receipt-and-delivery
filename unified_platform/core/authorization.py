"""
Platform Core — Authorization Service

Unified role-based access control.
Extracted from: lab_system/app/auth/permissions.py, backend/app/api/deps.py
"""

from __future__ import annotations

from dataclasses import dataclass

from unified_platform.core.base import PlatformService, ServiceHealth, ServiceStatus


@dataclass(frozen=True)
class Permission:
    """Standardized permission contract."""
    resource: str
    action: str
    description: str = ""

    def __str__(self) -> str:
        return f"{self.resource}.{self.action}"


@dataclass(frozen=True)
class Role:
    """Standardized role contract."""
    name: str
    permissions: tuple[Permission, ...] = ()
    description: str = ""
    is_system: bool = True


# ============================================================================
# Standard Role Definitions (unified across desktop and backend)
# ============================================================================

ADMIN_ROLE = Role(
    name="Admin",
    description="Full system access",
    is_system=True,
)

SUPERVISOR_ROLE = Role(
    name="Supervisor",
    description="Supervisory access",
    is_system=True,
)

USER_ROLE = Role(
    name="User",
    description="Standard user access",
    is_system=True,
)

AUDITOR_ROLE = Role(
    name="Auditor",
    description="Read-only audit access",
    is_system=True,
)

DEFAULT_ROLES: dict[str, Role] = {
    "admin": ADMIN_ROLE,
    "supervisor": SUPERVISOR_ROLE,
    "user": USER_ROLE,
    "auditor": AUDITOR_ROLE,
}


class AuthorizationService(PlatformService):
    """Unified authorization service."""

    @property
    def service_name(self) -> str:
        return "platform.authorization"

    def health_check(self) -> ServiceHealth:
        return ServiceHealth(
            service_name=self.service_name,
            status=ServiceStatus.HEALTHY,
        )

    def check_permission(self, role: str, permission: str) -> bool:
        """Check if a role has a specific permission."""
        ...

    def get_role_permissions(self, role: str) -> list[str]:
        """Get all permissions for a role."""
        ...

    def register_role(self, role: Role) -> None:
        """Register a new role."""
        ...

    def register_permission(self, permission: Permission) -> None:
        """Register a new permission."""
        ...

    def list_roles(self) -> list[Role]:
        """List all registered roles."""
        ...

    def list_permissions(self) -> list[Permission]:
        """List all registered permissions."""
        ...

    def require_permission(self, role: str, permission: str) -> None:
        """Raise if role does not have permission. Fail-closed."""
        ...
