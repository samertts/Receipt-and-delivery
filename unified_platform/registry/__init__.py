"""
Platform Registry — Centralized registry for all platform components.

Phase 2: Unified Ecosystem Architecture
Constitution Reference: Sections B (Unified Ecosystem), J (Future Consolidation)
"""

from __future__ import annotations

from unified_platform.registry.base import RegistryEntry, RegistryStatus
from unified_platform.registry.modules import ModuleRegistry, ModuleEntry
from unified_platform.registry.services import ServiceRegistry, ServiceEntry
from unified_platform.registry.features import FeatureRegistry, FeatureEntry
from unified_platform.registry.permissions import PermissionRegistry, PermissionEntry
from unified_platform.registry.events import EventRegistry, EventEntry
from unified_platform.registry.policies import PolicyRegistry, PolicyEntry

__all__ = [
    "RegistryStatus",
    "RegistryEntry",
    "ModuleRegistry", "ModuleEntry",
    "ServiceRegistry", "ServiceEntry",
    "FeatureRegistry", "FeatureEntry",
    "PermissionRegistry", "PermissionEntry",
    "EventRegistry", "EventEntry",
    "PolicyRegistry", "PolicyEntry",
]
