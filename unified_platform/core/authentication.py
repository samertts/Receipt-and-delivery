"""
Platform Core — Authentication Service

Unified authentication supporting both session-based (desktop) and token-based (API) patterns.
Extracted from: lab_system/app/services/auth_service.py, backend/app/services/auth_service.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from unified_platform.core.base import PlatformService, ServiceHealth, ServiceStatus


@dataclass
class AuthSession:
    """Standardized authentication session."""
    user_id: int
    username: str
    role: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    ip_address: str = ""
    device_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthToken:
    """Standardized authentication token (for API mode)."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    refresh_token: str = ""
    user_id: int = 0
    role: str = ""


class AuthenticationService(PlatformService):
    """Unified authentication service."""

    @property
    def service_name(self) -> str:
        return "platform.authentication"

    def health_check(self) -> ServiceHealth:
        return ServiceHealth(
            service_name=self.service_name,
            status=ServiceStatus.HEALTHY,
        )

    def authenticate(self, username: str, password: str, conn=None) -> AuthSession | None:
        """Authenticate user and create session."""
        ...

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        ...

    def hash_password(self, password: str) -> str:
        """Hash a password."""
        ...

    def change_password(self, user_id: int, old_password: str, new_password: str, conn=None) -> bool:
        """Change user password."""
        ...

    def validate_password_strength(self, password: str) -> tuple[bool, str]:
        """Validate password meets strength requirements."""
        ...

    def logout(self, session_id: str) -> bool:
        """Invalidate a session."""
        ...

    def check_session(self, session: AuthSession) -> bool:
        """Check if a session is still valid."""
        ...

    def create_token(self, user_id: int, role: str) -> AuthToken:
        """Create an API token."""
        ...

    def verify_token(self, token: str) -> AuthSession | None:
        """Verify an API token and return session."""
        ...
