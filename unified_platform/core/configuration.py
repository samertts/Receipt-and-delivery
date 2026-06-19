"""
Platform Core — Configuration Service

Unified configuration management with database-backed runtime config and env overrides.
Extracted from: lab_system/app/settings/config.py, backend/app/core/config.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from unified_platform.core.base import PlatformService, ServiceHealth, ServiceStatus


@dataclass
class ConfigValue:
    """A configuration value with metadata."""
    key: str
    value: str
    default: str = ""
    description: str = ""
    category: str = "general"
    is_sensitive: bool = False


class ConfigurationService(PlatformService):
    """Unified configuration management service."""

    @property
    def service_name(self) -> str:
        return "platform.configuration"

    def health_check(self) -> ServiceHealth:
        return ServiceHealth(
            service_name=self.service_name,
            status=ServiceStatus.HEALTHY,
        )

    def get(self, key: str, default: str = "", conn=None) -> str:
        """Get a configuration value."""
        ...

    def set(self, key: str, value: str, conn=None) -> None:
        """Set a configuration value."""
        ...

    def get_all(self, category: str | None = None, conn=None) -> dict[str, str]:
        """Get all configuration values, optionally filtered by category."""
        ...

    def set_all(self, settings: dict[str, str], conn=None) -> None:
        """Set multiple configuration values."""
        ...

    def get_defaults(self) -> dict[str, str]:
        """Get default configuration values."""
        ...

    def register_default(self, key: str, default: str, description: str = "", category: str = "general") -> None:
        """Register a default configuration value."""
        ...

    def get_env_override(self, key: str) -> str | None:
        """Check for environment variable override."""
        ...

    def validate_config(self, config: dict[str, str]) -> tuple[bool, list[str]]:
        """Validate a configuration dictionary."""
        ...

    def export_config(self, include_sensitive: bool = False, conn=None) -> dict[str, Any]:
        """Export all configuration as a dictionary."""
        ...

    def import_config(self, config: dict[str, str], conn=None) -> int:
        """Import configuration from a dictionary. Returns count of values set."""
        ...
