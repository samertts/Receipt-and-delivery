"""
Platform Registry — Feature Registry

Tracks all features across modules.
Constitution: Principle 105 (Modular Expansion)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from unified_platform.registry.base import RegistryEntry


@dataclass
class FeatureEntry(RegistryEntry):
    """A registered feature in the platform."""
    feature_id: str = ""
    module: str = ""
    category: str = ""
    requires_license: bool = False
    is_experimental: bool = False
    is_national_ready: bool = False
    permissions_required: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()


class FeatureRegistry:
    """Central registry for all platform features."""

    def __init__(self) -> None:
        self._features: dict[str, FeatureEntry] = {}

    def register(self, feature: FeatureEntry) -> None:
        """Register a feature."""
        self._features[feature.name] = feature

    def unregister(self, name: str) -> bool:
        """Unregister a feature."""
        if name in self._features:
            del self._features[name]
            return True
        return False

    def get(self, name: str) -> FeatureEntry | None:
        """Get a feature by name."""
        return self._features.get(name)

    def list_all(self) -> list[FeatureEntry]:
        """List all registered features."""
        return list(self._features.values())

    def list_by_module(self, module: str) -> list[FeatureEntry]:
        """List all features for a module."""
        return [f for f in self._features.values() if f.module == module]

    def list_by_category(self, category: str) -> list[FeatureEntry]:
        """List all features in a category."""
        return [f for f in self._features.values() if f.category == category]

    def list_experimental(self) -> list[FeatureEntry]:
        """List all experimental features."""
        return [f for f in self._features.values() if f.is_experimental]

    def list_national_ready(self) -> list[FeatureEntry]:
        """List all national-ready features."""
        return [f for f in self._features.values() if f.is_national_ready]

    def export_registry(self) -> dict[str, Any]:
        """Export the full registry."""
        return {
            name: {
                "name": f.name,
                "version": f.version,
                "status": f.status.value,
                "module": f.module,
                "category": f.category,
                "is_experimental": f.is_experimental,
                "is_national_ready": f.is_national_ready,
            }
            for name, f in self._features.items()
        }
