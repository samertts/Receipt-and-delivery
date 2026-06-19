"""Tests for unified_platform/consolidation/__init__.py — Phase 12: Ecosystem Consolidation."""

from __future__ import annotations

from datetime import datetime

import pytest

from unified_platform.consolidation import (
    ComponentStatus,
    EcosystemConsolidator,
    EcosystemModule,
    SharedComponent,
    SharedComponentInfo,
)


# ============================================================================
# SharedComponentInfo
# ============================================================================

class TestSharedComponentInfo:
    def test_creation(self):
        info = SharedComponentInfo(
            component_id="identity",
            name="Identity",
            description="User identity management",
            status=ComponentStatus.ACTIVE,
        )
        assert info.component_id == "identity"
        assert info.name == "Identity"
        assert info.description == "User identity management"
        assert info.status == ComponentStatus.ACTIVE
        assert info.module_count == 0
        assert info.version == "1.0.0"
        assert isinstance(info.last_updated, datetime)

    def test_to_dict(self):
        info = SharedComponentInfo(
            component_id="audit",
            name="Audit",
            description="Immutable audit trail",
            status=ComponentStatus.ACTIVE,
            module_count=5,
            version="2.0.0",
        )
        d = info.to_dict()
        assert d["component_id"] == "audit"
        assert d["status"] == "active"
        assert d["module_count"] == 5
        assert d["version"] == "2.0.0"
        assert "last_updated" in d

    def test_defaults(self):
        info = SharedComponentInfo(
            component_id="x", name="X", description="X", status=ComponentStatus.PLANNED
        )
        assert info.module_count == 0
        assert info.version == "1.0.0"


# ============================================================================
# EcosystemModule
# ============================================================================

class TestEcosystemModule:
    def test_creation(self):
        mod = EcosystemModule(
            module_id="mod-1",
            name="Receipt Module",
            description="Handles receipts",
            version="1.0.0",
            shared_components=("identity", "audit"),
            dependencies=(),
            status=ComponentStatus.ACTIVE,
        )
        assert mod.module_id == "mod-1"
        assert mod.name == "Receipt Module"
        assert mod.shared_components == ("identity", "audit")
        assert mod.dependencies == ()
        assert mod.status == ComponentStatus.ACTIVE

    def test_to_dict(self):
        mod = EcosystemModule(
            module_id="mod-2",
            name="Delivery Module",
            description="Handles deliveries",
            version="1.1.0",
            shared_components=("identity", "synchronization"),
            dependencies=("mod-1",),
            status=ComponentStatus.ACTIVE,
        )
        d = mod.to_dict()
        assert d["module_id"] == "mod-2"
        assert d["shared_components"] == ["identity", "synchronization"]
        assert d["dependencies"] == ["mod-1"]
        assert d["status"] == "active"

    def test_defaults(self):
        mod = EcosystemModule(
            module_id="x", name="X", description="X", version="1.0.0"
        )
        assert mod.shared_components == ()
        assert mod.dependencies == ()
        assert mod.status == ComponentStatus.ACTIVE


# ============================================================================
# SharedComponent enum
# ============================================================================

class TestSharedComponentEnum:
    def test_has_13_values(self):
        assert len(SharedComponent) == 13

    def test_expected_values(self):
        expected = {
            "identity", "authentication", "authorization", "audit", "reporting",
            "notifications", "synchronization", "intelligence", "ai_assistant",
            "configuration", "backup", "recovery", "telemetry",
        }
        actual = {sc.value for sc in SharedComponent}
        assert actual == expected


# ============================================================================
# ComponentStatus enum
# ============================================================================

class TestComponentStatusEnum:
    def test_values(self):
        vals = {s.value for s in ComponentStatus}
        assert vals == {"active", "deprecated", "pending", "planned"}


# ============================================================================
# EcosystemConsolidator
# ============================================================================

class TestEcosystemConsolidator:
    def test_init_registers_13_defaults(self):
        cons = EcosystemConsolidator()
        components = cons.list_components()
        assert len(components) == 13

    def test_register_component(self):
        cons = EcosystemConsolidator()
        custom = SharedComponentInfo(
            component_id="custom-comp",
            name="Custom",
            description="Custom component",
            status=ComponentStatus.PENDING,
        )
        cons.register_component(custom)
        retrieved = cons.get_component("custom-comp")
        assert retrieved is not None
        assert retrieved.name == "Custom"
        assert retrieved.status == ComponentStatus.PENDING

    def test_get_component_existing(self):
        cons = EcosystemConsolidator()
        comp = cons.get_component("identity")
        assert comp is not None
        assert comp.name == "Identity"

    def test_get_component_missing(self):
        cons = EcosystemConsolidator()
        assert cons.get_component("nonexistent") is None

    def test_list_components_default(self):
        cons = EcosystemConsolidator()
        components = cons.list_components()
        ids = {c.component_id for c in components}
        assert "identity" in ids
        assert "telemetry" in ids
        assert len(components) == 13

    def test_register_module(self):
        cons = EcosystemConsolidator()
        mod = EcosystemModule(
            module_id="m1",
            name="Module 1",
            description="Test module",
            version="1.0.0",
        )
        cons.register_module(mod)
        retrieved = cons.get_module("m1")
        assert retrieved is not None
        assert retrieved.name == "Module 1"

    def test_get_module_missing(self):
        cons = EcosystemConsolidator()
        assert cons.get_module("nope") is None

    def test_list_modules(self):
        cons = EcosystemConsolidator()
        assert cons.list_modules() == []
        mod1 = EcosystemModule(
            module_id="m1", name="M1", description="D", version="1.0.0"
        )
        mod2 = EcosystemModule(
            module_id="m2", name="M2", description="D", version="1.0.0"
        )
        cons.register_module(mod1)
        cons.register_module(mod2)
        modules = cons.list_modules()
        assert len(modules) == 2
        ids = {m.module_id for m in modules}
        assert ids == {"m1", "m2"}

    def test_validate_dependencies_met(self):
        cons = EcosystemConsolidator()
        mod_a = EcosystemModule(
            module_id="a", name="A", description="D", version="1.0.0"
        )
        mod_b = EcosystemModule(
            module_id="b", name="B", description="D", version="1.0.0",
            dependencies=("a",),
        )
        cons.register_module(mod_a)
        cons.register_module(mod_b)
        valid, missing = cons.validate_module_dependencies("b")
        assert valid is True
        assert missing == []

    def test_validate_dependencies_missing(self):
        cons = EcosystemConsolidator()
        mod_b = EcosystemModule(
            module_id="b", name="B", description="D", version="1.0.0",
            dependencies=("a",),
        )
        cons.register_module(mod_b)
        valid, missing = cons.validate_module_dependencies("b")
        assert valid is False
        assert missing == ["a"]

    def test_validate_dependencies_module_not_found(self):
        cons = EcosystemConsolidator()
        valid, missing = cons.validate_module_dependencies("ghost")
        assert valid is False
        assert missing == ["ghost"]

    def test_get_consolidation_report_empty(self):
        cons = EcosystemConsolidator()
        # Only default components registered, no modules
        report = cons.get_consolidation_report()
        assert report["component_count"] == 13
        assert report["module_count"] == 0
        assert report["active_component_count"] == 13
        assert report["active_module_count"] == 0
        assert report["shared_component_coverage"] == 0.0
        assert report["shared_components_used"] == []
        assert report["total_shared_component_types"] == 13

    def test_get_consolidation_report_with_modules(self):
        cons = EcosystemConsolidator()
        mod = EcosystemModule(
            module_id="m1",
            name="M1",
            description="D",
            version="1.0.0",
            shared_components=("identity", "audit", "reporting"),
            status=ComponentStatus.ACTIVE,
        )
        cons.register_module(mod)
        report = cons.get_consolidation_report()
        assert report["module_count"] == 1
        assert report["active_module_count"] == 1
        assert report["shared_component_coverage"] == pytest.approx(3 / 13, abs=1e-4)
        assert report["shared_components_used"] == ["audit", "identity", "reporting"]

    def test_register_component_overwrites(self):
        cons = EcosystemConsolidator()
        info_v1 = SharedComponentInfo(
            component_id="identity",
            name="Identity v1",
            description="D",
            status=ComponentStatus.ACTIVE,
            version="1.0.0",
        )
        cons.register_component(info_v1)
        assert cons.get_component("identity").name == "Identity v1"

        info_v2 = SharedComponentInfo(
            component_id="identity",
            name="Identity v2",
            description="D",
            status=ComponentStatus.ACTIVE,
            version="2.0.0",
        )
        cons.register_component(info_v2)
        assert cons.get_component("identity").name == "Identity v2"
        assert cons.get_component("identity").version == "2.0.0"
