"""
Plugin Service — Plugin Architecture for Future Ecosystem

Provides plugin registry, loader, and isolation for future platform expansion.
"""

import importlib.util
import os
from typing import Any


class PluginRegistry:
    """Manages plugin registration, lifecycle, and versioning."""

    def __init__(self):
        self._plugins: dict[str, dict] = {}

    def register(self, name: str, config: dict) -> bool:
        """Register a new plugin."""
        if name in self._plugins:
            return False
        self._plugins[name] = {
            "name": name,
            "version": config.get("version", "0.0.0"),
            "status": config.get("status", "inactive"),
            "contracts": config.get("contracts", []),
            "config": config,
        }
        return True

    def unregister(self, name: str) -> bool:
        """Unregister a plugin."""
        if name not in self._plugins:
            return False
        del self._plugins[name]
        return True

    def is_registered(self, name: str) -> bool:
        """Check if a plugin is registered."""
        return name in self._plugins

    def get_plugin(self, name: str) -> dict | None:
        """Get plugin configuration."""
        return self._plugins.get(name)

    def update_plugin(self, name: str, updates: dict) -> bool:
        """Update plugin configuration."""
        if name not in self._plugins:
            return False
        self._plugins[name].update(updates)
        return True

    def list_plugins(self) -> list[dict]:
        """List all registered plugins."""
        return list(self._plugins.values())

    def get_active_plugins(self) -> list[dict]:
        """Get all active plugins."""
        return [p for p in self._plugins.values() if p.get("status") == "active"]


class PluginLoader:
    """Safely loads and validates plugin modules."""

    def __init__(self):
        self._loaded_modules: dict[str, Any] = {}

    def validate_plugin_path(self, path: str) -> dict:
        """Validate that a plugin path exists and is loadable."""
        result = {"valid": False, "error": None}
        if not os.path.exists(path):
            result["error"] = f"Path does not exist: {path}"
            return result
        if not os.path.isfile(path):
            result["error"] = f"Path is not a file: {path}"
            return result
        if not path.endswith(".py"):
            result["error"] = f"Not a Python file: {path}"
            return result
        result["valid"] = True
        return result

    def load_plugin(self, name: str, path: str) -> dict:
        """Load a plugin module safely."""
        result = {"success": False, "module": None, "error": None}
        validation = self.validate_plugin_path(path)
        if not validation["valid"]:
            result["error"] = validation["error"]
            return result
        try:
            spec = importlib.util.spec_from_file_location(name, path)
            if spec is None or spec.loader is None:
                result["error"] = f"Cannot load module spec: {path}"
                return result
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self._loaded_modules[name] = module
            result["success"] = True
            result["module"] = module
        except Exception as e:
            result["error"] = str(e)
        return result

    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin module."""
        if name in self._loaded_modules:
            del self._loaded_modules[name]
            return True
        return False

    def get_loaded_plugins(self) -> list[str]:
        """Get list of loaded plugin names."""
        return list(self._loaded_modules.keys())
