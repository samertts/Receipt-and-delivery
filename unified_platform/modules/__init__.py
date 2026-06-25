"""
Unified Platform V7.0 — Phase 1: Multi-Module Runtime — Module Lifecycle Manager

Manages module registration, lifecycle states, health checks, dependency
resolution, and version compatibility for the unified platform ecosystem.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# ============================================================================
# Enums
# ============================================================================

class ModuleState(Enum):
    INSTALLED = "installed"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    UPDATING = "updating"


class ModuleHealth(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


# ============================================================================
# Data Contracts
# ============================================================================

@dataclass
class ModuleManifest:
    """Describes a module's metadata and requirements."""
    module_id: str
    name: str
    version: str
    description: str
    author: str
    dependencies: list[str] = field(default_factory=list)
    min_platform_version: str = "1.0.0"
    max_platform_version: str = "99.99.99"
    entry_point: str = ""
    permissions: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModuleStatus:
    """Tracks a module's runtime state and health."""
    module_id: str
    state: ModuleState = ModuleState.INSTALLED
    health: ModuleHealth = ModuleHealth.UNKNOWN
    enabled: bool = True
    installed_at: datetime = field(default_factory=datetime.utcnow)
    last_health_check: datetime | None = None
    error_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Lifecycle Manager
# ============================================================================

class ModuleLifecycle:
    """Handles start, stop, health, and upgrade operations for a module."""

    def __init__(self, manager: ModuleManager) -> None:
        self._manager = manager

    def start(self, module_id: str) -> bool:
        status = self._manager.get_status(module_id)
        if status is None:
            return False
        if status.state == ModuleState.ERROR:
            return False
        status.state = ModuleState.ACTIVE
        status.health = ModuleHealth.HEALTHY
        status.error_message = ""
        return True

    def stop(self, module_id: str) -> bool:
        status = self._manager.get_status(module_id)
        if status is None:
            return False
        if status.state != ModuleState.ACTIVE:
            return False
        status.state = ModuleState.INACTIVE
        status.health = ModuleHealth.UNKNOWN
        return True

    def health_check(self, module_id: str) -> ModuleHealth:
        status = self._manager.get_status(module_id)
        if status is None:
            return ModuleHealth.UNKNOWN
        status.last_health_check = datetime.utcnow()
        if status.state == ModuleState.ERROR:
            status.health = ModuleHealth.UNHEALTHY
        elif status.state == ModuleState.ACTIVE:
            status.health = ModuleHealth.HEALTHY
        elif status.state == ModuleState.INACTIVE:
            status.health = ModuleHealth.DEGRADED
        else:
            status.health = ModuleHealth.UNKNOWN
        return status.health

    def upgrade(self, module_id: str, new_version: str) -> bool:
        manifest = self._manager.get_manifest(module_id)
        status = self._manager.get_status(module_id)
        if manifest is None or status is None:
            return False
        if status.state == ModuleState.UPDATING:
            return False
        status.state = ModuleState.UPDATING
        manifest.version = new_version
        status.state = ModuleState.ACTIVE
        return True

    def get_status(self, module_id: str) -> ModuleStatus | None:
        return self._manager.get_status(module_id)


# ============================================================================
# Module Manager
# ============================================================================

class ModuleManager:
    """Central manager for all platform modules."""

    def __init__(self) -> None:
        self._modules: dict[str, tuple[ModuleManifest, ModuleStatus]] = {}
        self._lifecycle = ModuleLifecycle(self)

    @property
    def lifecycle(self) -> ModuleLifecycle:
        return self._lifecycle

    def register_module(self, manifest: ModuleManifest) -> bool:
        if manifest.module_id in self._modules:
            return False
        status = ModuleStatus(module_id=manifest.module_id)
        self._modules[manifest.module_id] = (manifest, status)
        return True

    def unregister_module(self, module_id: str) -> bool:
        if module_id not in self._modules:
            return False
        del self._modules[module_id]
        return True

    def enable_module(self, module_id: str) -> bool:
        entry = self._modules.get(module_id)
        if entry is None:
            return False
        entry[1].enabled = True
        return True

    def disable_module(self, module_id: str) -> bool:
        entry = self._modules.get(module_id)
        if entry is None:
            return False
        entry[1].enabled = False
        return True

    def get_manifest(self, module_id: str) -> ModuleManifest | None:
        entry = self._modules.get(module_id)
        return entry[0] if entry else None

    def get_status(self, module_id: str) -> ModuleStatus | None:
        entry = self._modules.get(module_id)
        return entry[1] if entry else None

    def list_modules(self) -> list[ModuleManifest]:
        return [entry[0] for entry in self._modules.values()]

    def list_active(self) -> list[ModuleManifest]:
        return [
            entry[0]
            for entry in self._modules.values()
            if entry[1].state == ModuleState.ACTIVE
        ]

    def check_dependencies(self, module_id: str) -> tuple[bool, list[str]]:
        manifest = self.get_manifest(module_id)
        if manifest is None:
            return False, [module_id]
        missing = [dep for dep in manifest.dependencies if dep not in self._modules]
        return len(missing) == 0, missing

    def check_version_compatibility(self, module_id: str, platform_version: str) -> bool:
        manifest = self.get_manifest(module_id)
        if manifest is None:
            return False
        return manifest.min_platform_version <= platform_version <= manifest.max_platform_version

    def run_health_check(self, module_id: str) -> ModuleHealth:
        return self._lifecycle.health_check(module_id)

    def get_lifecycle_report(self) -> dict[str, Any]:
        states: dict[str, int] = {}
        healths: dict[str, int] = {}
        for _, status in self._modules.values():
            state_key = status.state.value
            health_key = status.health.value
            states[state_key] = states.get(state_key, 0) + 1
            healths[health_key] = healths.get(health_key, 0) + 1
        return {
            "total_modules": len(self._modules),
            "states": states,
            "healths": healths,
            "active_count": states.get(ModuleState.ACTIVE.value, 0),
            "error_count": states.get(ModuleState.ERROR.value, 0),
        }
