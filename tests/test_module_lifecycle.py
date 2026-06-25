"""Tests for unified_platform/modules/__init__.py — Module Lifecycle Manager."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unified_platform.modules import (
    ModuleState,
    ModuleHealth,
    ModuleManifest,
    ModuleManager,
)


# ============================================================================
# Test ModuleManager Registration
# ============================================================================


class TestModuleManagerRegistration:
    """Tests for register / unregister / list operations."""

    def _make_manifest(self, module_id="mod.a", deps=None, min_ver="1.0.0", max_ver="99.99.99"):
        return ModuleManifest(
            module_id=module_id,
            name=module_id,
            version="1.0.0",
            description="test module",
            author="tester",
            dependencies=deps or [],
            min_platform_version=min_ver,
            max_platform_version=max_ver,
        )

    def test_register_module_returns_true(self):
        mgr = ModuleManager()
        assert mgr.register_module(self._make_manifest()) is True

    def test_register_duplicate_returns_false(self):
        mgr = ModuleManager()
        mgr.register_module(self._make_manifest())
        assert mgr.register_module(self._make_manifest()) is False

    def test_unregister_existing_returns_true(self):
        mgr = ModuleManager()
        mgr.register_module(self._make_manifest())
        assert mgr.unregister_module("mod.a") is True

    def test_unregister_nonexistent_returns_false(self):
        mgr = ModuleManager()
        assert mgr.unregister_module("mod.x") is False

    def test_get_manifest_returns_registered(self):
        mgr = ModuleManager()
        m = self._make_manifest()
        mgr.register_module(m)
        assert mgr.get_manifest("mod.a") is m

    def test_get_manifest_returns_none_for_unknown(self):
        mgr = ModuleManager()
        assert mgr.get_manifest("mod.z") is None

    def test_list_modules_returns_all(self):
        mgr = ModuleManager()
        mgr.register_module(self._make_manifest("a"))
        mgr.register_module(self._make_manifest("b"))
        assert len(mgr.list_modules()) == 2

    def test_list_active_initially_empty(self):
        mgr = ModuleManager()
        mgr.register_module(self._make_manifest())
        assert mgr.list_active() == []


# ============================================================================
# Test Enable / Disable
# ============================================================================


class TestModuleEnableDisable:
    """Tests for enable/disable operations."""

    def _make_manifest(self, module_id="mod.a"):
        return ModuleManifest(
            module_id=module_id, name=module_id, version="1.0.0",
            description="", author="tester",
        )

    def test_disable_existing(self):
        mgr = ModuleManager()
        mgr.register_module(self._make_manifest())
        assert mgr.disable_module("mod.a") is True
        assert mgr.get_status("mod.a").enabled is False

    def test_enable_existing(self):
        mgr = ModuleManager()
        mgr.register_module(self._make_manifest())
        mgr.disable_module("mod.a")
        assert mgr.enable_module("mod.a") is True
        assert mgr.get_status("mod.a").enabled is True

    def test_disable_nonexistent_returns_false(self):
        mgr = ModuleManager()
        assert mgr.disable_module("mod.z") is False


# ============================================================================
# Test Lifecycle
# ============================================================================


class TestModuleLifecycleStartStop:
    """Tests for lifecycle start/stop operations."""

    def _make_manager(self, module_id="mod.a"):
        mgr = ModuleManager()
        mgr.register_module(ModuleManifest(
            module_id=module_id, name=module_id, version="1.0.0",
            description="", author="tester",
        ))
        return mgr

    def test_start_changes_to_active(self):
        mgr = self._make_manager()
        assert mgr.lifecycle.start("mod.a") is True
        assert mgr.get_status("mod.a").state == ModuleState.ACTIVE

    def test_start_nonexistent_returns_false(self):
        mgr = ModuleManager()
        assert mgr.lifecycle.start("mod.z") is False

    def test_stop_changes_to_inactive(self):
        mgr = self._make_manager()
        mgr.lifecycle.start("mod.a")
        assert mgr.lifecycle.stop("mod.a") is True
        assert mgr.get_status("mod.a").state == ModuleState.INACTIVE

    def test_stop_inactive_module_returns_false(self):
        mgr = self._make_manager()
        assert mgr.lifecycle.stop("mod.a") is False

    def test_start_after_error_returns_false(self):
        mgr = self._make_manager()
        mgr.get_status("mod.a").state = ModuleState.ERROR
        assert mgr.lifecycle.start("mod.a") is False

    def test_list_active_after_start(self):
        mgr = self._make_manager()
        mgr.lifecycle.start("mod.a")
        active = mgr.list_active()
        assert len(active) == 1
        assert active[0].module_id == "mod.a"


# ============================================================================
# Test Health Check
# ============================================================================


class TestModuleHealthCheck:
    """Tests for health check operations."""

    def _make_manager(self):
        mgr = ModuleManager()
        mgr.register_module(ModuleManifest(
            module_id="mod.a", name="mod.a", version="1.0.0",
            description="", author="tester",
        ))
        return mgr

    def test_health_check_active_is_healthy(self):
        mgr = self._make_manager()
        mgr.lifecycle.start("mod.a")
        assert mgr.lifecycle.health_check("mod.a") == ModuleHealth.HEALTHY

    def test_health_check_inactive_is_degraded(self):
        mgr = self._make_manager()
        mgr.lifecycle.start("mod.a")
        mgr.lifecycle.stop("mod.a")
        assert mgr.lifecycle.health_check("mod.a") == ModuleHealth.DEGRADED

    def test_health_check_error_is_unhealthy(self):
        mgr = self._make_manager()
        mgr.get_status("mod.a").state = ModuleState.ERROR
        assert mgr.lifecycle.health_check("mod.a") == ModuleHealth.UNHEALTHY

    def test_health_check_unknown_module(self):
        mgr = ModuleManager()
        assert mgr.run_health_check("mod.z") == ModuleHealth.UNKNOWN

    def test_health_check_updates_timestamp(self):
        mgr = self._make_manager()
        mgr.lifecycle.start("mod.a")
        mgr.lifecycle.health_check("mod.a")
        assert mgr.get_status("mod.a").last_health_check is not None


# ============================================================================
# Test Upgrade
# ============================================================================


class TestModuleUpgrade:
    """Tests for upgrade operations."""

    def _make_manager(self):
        mgr = ModuleManager()
        mgr.register_module(ModuleManifest(
            module_id="mod.a", name="mod.a", version="1.0.0",
            description="", author="tester",
        ))
        return mgr

    def test_upgrade_new_version(self):
        mgr = self._make_manager()
        mgr.lifecycle.start("mod.a")
        assert mgr.lifecycle.upgrade("mod.a", "2.0.0") is True
        assert mgr.get_manifest("mod.a").version == "2.0.0"

    def test_upgrade_nonexistent_returns_false(self):
        mgr = ModuleManager()
        assert mgr.lifecycle.upgrade("mod.z", "2.0.0") is False

    def test_upgrade_sets_updating_then_active(self):
        mgr = self._make_manager()
        mgr.lifecycle.start("mod.a")
        mgr.lifecycle.upgrade("mod.a", "1.1.0")
        assert mgr.get_status("mod.a").state == ModuleState.ACTIVE

    def test_upgrade_already_updating_returns_false(self):
        mgr = self._make_manager()
        mgr.get_status("mod.a").state = ModuleState.UPDATING
        assert mgr.lifecycle.upgrade("mod.a", "2.0.0") is False


# ============================================================================
# Test Dependencies & Compatibility
# ============================================================================


class TestDependenciesAndCompatibility:
    """Tests for dependency and version compatibility checks."""

    def _make_manager_with_deps(self):
        mgr = ModuleManager()
        mgr.register_module(ModuleManifest(
            module_id="core", name="core", version="1.0.0",
            description="", author="tester",
        ))
        mgr.register_module(ModuleManifest(
            module_id="plugin", name="plugin", version="1.0.0",
            description="", author="tester",
            dependencies=["core"],
        ))
        return mgr

    def test_check_dependencies_met(self):
        mgr = self._make_manager_with_deps()
        ok, missing = mgr.check_dependencies("plugin")
        assert ok is True
        assert missing == []

    def test_check_dependencies_missing(self):
        mgr = ModuleManager()
        mgr.register_module(ModuleManifest(
            module_id="plugin", name="plugin", version="1.0.0",
            description="", author="tester", dependencies=["core"],
        ))
        ok, missing = mgr.check_dependencies("plugin")
        assert ok is False
        assert "core" in missing

    def test_check_dependencies_unknown_module(self):
        mgr = ModuleManager()
        ok, missing = mgr.check_dependencies("nope")
        assert ok is False
        assert missing == ["nope"]

    def test_version_compatible(self):
        mgr = ModuleManager()
        mgr.register_module(ModuleManifest(
            module_id="m", name="m", version="1.0.0",
            description="", author="tester",
            min_platform_version="1.0.0", max_platform_version="3.0.0",
        ))
        assert mgr.check_version_compatibility("m", "2.0.0") is True

    def test_version_out_of_range(self):
        mgr = ModuleManager()
        mgr.register_module(ModuleManifest(
            module_id="m", name="m", version="1.0.0",
            description="", author="tester",
            min_platform_version="2.0.0", max_platform_version="3.0.0",
        ))
        assert mgr.check_version_compatibility("m", "1.0.0") is False

    def test_version_compatibility_unknown_module(self):
        mgr = ModuleManager()
        assert mgr.check_version_compatibility("nope", "1.0.0") is False


# ============================================================================
# Test Lifecycle Report
# ============================================================================


class TestLifecycleReport:
    """Tests for get_lifecycle_report."""

    def test_empty_report(self):
        mgr = ModuleManager()
        report = mgr.get_lifecycle_report()
        assert report["total_modules"] == 0
        assert report["states"] == {}
        assert report["healths"] == {}

    def test_report_after_start(self):
        mgr = ModuleManager()
        mgr.register_module(ModuleManifest(
            module_id="a", name="a", version="1.0.0",
            description="", author="tester",
        ))
        mgr.lifecycle.start("a")
        report = mgr.get_lifecycle_report()
        assert report["total_modules"] == 1
        assert report["active_count"] == 1
        assert report["error_count"] == 0

    def test_report_with_error_module(self):
        mgr = ModuleManager()
        mgr.register_module(ModuleManifest(
            module_id="a", name="a", version="1.0.0",
            description="", author="tester",
        ))
        mgr.get_status("a").state = ModuleState.ERROR
        report = mgr.get_lifecycle_report()
        assert report["error_count"] == 1
