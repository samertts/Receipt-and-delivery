"""
Platform Core — Identity Service

Centralized user identity management.
Extracted from: lab_system/app/services/user_service.py, backend/app/models/user.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from unified_platform.core.base import PlatformService, ServiceHealth, ServiceStatus


@dataclass
class UserIdentity:
    """Standardized user identity contract."""
    id: int
    username: str
    full_name: str
    role: str
    status: str
    created_at: str = ""
    updated_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class IdentityService(PlatformService):
    """Centralized identity management service."""

    @property
    def service_name(self) -> str:
        return "platform.identity"

    def health_check(self) -> ServiceHealth:
        return ServiceHealth(
            service_name=self.service_name,
            status=ServiceStatus.HEALTHY,
        )

    def get_user(self, user_id: int, conn=None) -> UserIdentity | None:
        """Retrieve user identity by ID."""
        ...

    def get_user_by_username(self, username: str, conn=None) -> UserIdentity | None:
        """Retrieve user identity by username."""
        ...

    def list_users(self, active_only: bool = False, conn=None) -> list[UserIdentity]:
        """List all user identities."""
        ...

    def create_user(self, data: dict[str, Any], conn=None) -> UserIdentity:
        """Create a new user identity."""
        ...

    def update_user(self, user_id: int, data: dict[str, Any], conn=None) -> UserIdentity | None:
        """Update an existing user identity."""
        ...

    def deactivate_user(self, user_id: int, conn=None) -> bool:
        """Deactivate a user identity."""
        ...

    def user_exists(self, username: str, conn=None) -> bool:
        """Check if a username already exists."""
        ...
