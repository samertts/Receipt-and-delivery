"""
Platform Consolidation — Ecosystem Consolidation

Phase 12: Ecosystem Consolidation
Constitution: Principle 40 (Shared Components), Principle 41 (Module Ecosystem)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# ============================================================================
# Enums
# ============================================================================

class SharedComponent(Enum):
    """Shared components available across the unified platform."""
    IDENTITY = "identity"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    AUDIT = "audit"
    REPORTING = "reporting"
    NOTIFICATIONS = "notifications"
    SYNCHRONIZATION = "synchronization"
    INTELLIGENCE = "intelligence"
    AI_ASSISTANT = "ai_assistant"
    CONFIGURATION = "configuration"
    BACKUP = "backup"
    RECOVERY = "recovery"
    TELEMETRY = "telemetry"


class ComponentStatus(Enum):
    """Status of a shared component within the ecosystem."""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    PENDING = "pending"
    PLANNED = "planned"


# ============================================================================
# Dataclasses
# ============================================================================

@dataclass
class SharedComponentInfo:
    """Metadata for a shared component registered in the ecosystem."""
    component_id: str
    name: str
    description: str
    status: ComponentStatus
    module_count: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "module_count": self.module_count,
            "last_updated": self.last_updated.isoformat(),
            "version": self.version,
        }


@dataclass
class EcosystemModule:
    """A module within the unified platform ecosystem."""
    module_id: str
    name: str
    description: str
    version: str
    shared_components: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    status: ComponentStatus = ComponentStatus.ACTIVE

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_id": self.module_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "shared_components": list(self.shared_components),
            "dependencies": list(self.dependencies),
            "status": self.status.value,
        }


# ============================================================================
# Ecosystem Consolidator
# ============================================================================

class EcosystemConsolidator:
    """Central manager for ecosystem consolidation across all platform modules."""

    def __init__(self) -> None:
        self._components: dict[str, SharedComponentInfo] = {}
        self._modules: dict[str, EcosystemModule] = {}
        self._register_default_components()

    def _register_default_components(self) -> None:
        """Register the 13 shared components defined by the platform constitution."""
        defaults = [
            ("identity", "Identity", "User identity management and resolution"),
            ("authentication", "Authentication", "Credential verification and session management"),
            ("authorization", "Authorization", "Permission and role-based access control"),
            ("audit", "Audit", "Immutable audit trail and event logging"),
            ("reporting", "Reporting", "Analytics, dashboards, and report generation"),
            ("notifications", "Notifications", "Push, email, and in-app notification delivery"),
            ("synchronization", "Synchronization", "Cross-node and offline data synchronization"),
            ("intelligence", "Intelligence", "Operational intelligence and scoring engine"),
            ("ai_assistant", "AI Assistant", "AI-powered recommendations and analysis"),
            ("configuration", "Configuration", "Centralized platform configuration management"),
            ("backup", "Backup", "Automated backup creation and lifecycle management"),
            ("recovery", "Recovery", "Disaster recovery and data restoration"),
            ("telemetry", "Telemetry", "Operational metrics collection and export"),
        ]
        for component_id, name, description in defaults:
            info = SharedComponentInfo(
                component_id=component_id,
                name=name,
                description=description,
                status=ComponentStatus.ACTIVE,
            )
            self._components[component_id] = info

    def register_component(self, component: SharedComponentInfo) -> None:
        """Register or update a shared component."""
        self._components[component.component_id] = component

    def get_component(self, component_id: str) -> SharedComponentInfo | None:
        """Retrieve a shared component by its ID."""
        return self._components.get(component_id)

    def list_components(self) -> list[SharedComponentInfo]:
        """Return all registered shared components."""
        return list(self._components.values())

    def register_module(self, module: EcosystemModule) -> None:
        """Register or update an ecosystem module."""
        self._modules[module.module_id] = module

    def get_module(self, module_id: str) -> EcosystemModule | None:
        """Retrieve a module by its ID."""
        return self._modules.get(module_id)

    def list_modules(self) -> list[EcosystemModule]:
        """Return all registered modules."""
        return list(self._modules.values())

    def validate_module_dependencies(self, module_id: str) -> tuple[bool, list[str]]:
        """Validate that all dependencies of a module exist in the ecosystem.

        Returns a tuple of (is_valid, list_of_missing_dependency_ids).
        """
        module = self._modules.get(module_id)
        if module is None:
            return False, [module_id]

        missing: list[str] = []
        for dep_id in module.dependencies:
            if dep_id not in self._modules:
                missing.append(dep_id)

        return len(missing) == 0, missing

    def get_consolidation_report(self) -> dict[str, Any]:
        """Generate a consolidation report summarising ecosystem state."""
        components = list(self._components.values())
        modules = list(self._modules.values())

        active_components = [c for c in components if c.status == ComponentStatus.ACTIVE]
        active_modules = [m for m in modules if m.status == ComponentStatus.ACTIVE]

        all_shared = set()
        for m in modules:
            all_shared.update(m.shared_components)

        coverage = (
            len(all_shared) / len(SharedComponent)
            if len(SharedComponent) > 0
            else 0.0
        )

        return {
            "component_count": len(components),
            "module_count": len(modules),
            "active_component_count": len(active_components),
            "active_module_count": len(active_modules),
            "shared_component_coverage": round(coverage, 4),
            "shared_components_used": sorted(all_shared),
            "total_shared_component_types": len(SharedComponent),
        }
