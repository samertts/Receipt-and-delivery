"""
Platform Registry — Module Registry

Tracks all modules in the unified platform ecosystem.
Constitution: Principle 28 (One Platform), Principle 60 (Unified Platform Core)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from unified_platform.registry.base import RegistryEntry, RegistryStatus


@dataclass
class ModuleEntry(RegistryEntry):
    """A registered module in the platform."""
    module_id: str = ""
    entry_point: str = ""
    dependencies: tuple[str, ...] = ()
    permissions_required: tuple[str, ...] = ()
    events_emitted: tuple[str, ...] = ()
    events_consumed: tuple[str, ...] = ()
    is_core: bool = False
    is_national_ready: bool = False


class ModuleRegistry:
    """Central registry for all platform modules."""

    def __init__(self) -> None:
        self._modules: dict[str, ModuleEntry] = {}

    def register(self, module: ModuleEntry) -> None:
        """Register a module."""
        self._modules[module.name] = module

    def unregister(self, name: str) -> bool:
        """Unregister a module."""
        if name in self._modules:
            del self._modules[name]
            return True
        return False

    def get(self, name: str) -> ModuleEntry | None:
        """Get a module by name."""
        return self._modules.get(name)

    def list_all(self) -> list[ModuleEntry]:
        """List all registered modules."""
        return list(self._modules.values())

    def list_active(self) -> list[ModuleEntry]:
        """List all active modules."""
        return [m for m in self._modules.values() if m.status == RegistryStatus.ACTIVE]

    def list_core(self) -> list[ModuleEntry]:
        """List all core modules."""
        return [m for m in self._modules.values() if m.is_core]

    def list_national_ready(self) -> list[ModuleEntry]:
        """List all national-ready modules."""
        return [m for m in self._modules.values() if m.is_national_ready]

    def update_status(self, name: str, status: RegistryStatus) -> bool:
        """Update a module's status."""
        if name in self._modules:
            self._modules[name].status = status
            self._modules[name].updated_at = datetime.utcnow()
            return True
        return False

    def get_dependencies(self, name: str) -> list[str]:
        """Get all dependencies for a module."""
        module = self._modules.get(name)
        if not module:
            return []
        return list(module.dependencies)

    def check_circular_dependencies(self) -> list[str]:
        """Check for circular dependencies between modules."""
        visited: set[str] = set()
        path: list[str] = []
        cycles: list[str] = []

        def dfs(node: str) -> None:
            if node in path:
                cycle_start = path.index(node)
                cycles.append(" -> ".join(path[cycle_start:] + [node]))
                return
            if node in visited:
                return
            path.append(node)
            visited.add(node)
            module = self._modules.get(node)
            if module:
                for dep in module.dependencies:
                    dfs(dep)
            path.pop()

        for name in self._modules:
            dfs(name)

        return cycles

    def export_registry(self) -> dict[str, Any]:
        """Export the full registry as a dictionary."""
        return {
            name: {
                "name": m.name,
                "version": m.version,
                "status": m.status.value,
                "is_core": m.is_core,
                "is_national_ready": m.is_national_ready,
                "dependencies": list(m.dependencies),
                "permissions_required": list(m.permissions_required),
                "events_emitted": list(m.events_emitted),
                "events_consumed": list(m.events_consumed),
            }
            for name, m in self._modules.items()
        }
