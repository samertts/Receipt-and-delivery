"""
Tests for Ecosystem Registry — Phase 9
"""

from __future__ import annotations

from unified_platform.ecosystem import (
    EcosystemModuleManifest,
    EcosystemModuleType,
    EcosystemRegistry,
    ModuleReadinessStatus,
    SharedServiceContract,
)


class TestModuleRegistration:
    def setup_method(self) -> None:
        self.registry = EcosystemRegistry()

    def test_register_module(self) -> None:
        manifest = EcosystemModuleManifest(
            module_id="mod-001",
            name="Core Module",
            module_type=EcosystemModuleType.CORE,
            version="1.0.0",
            description="Core platform module",
        )
        assert self.registry.register_module(manifest) is True
        result = self.registry.get_module("mod-001")
        assert result is not None
        assert result.name == "Core Module"

    def test_duplicate_module_rejected(self) -> None:
        manifest = EcosystemModuleManifest(
            module_id="mod-002",
            name="Duplicate",
            module_type=EcosystemModuleType.CORE,
            version="1.0.0",
            description="Duplicate test",
        )
        assert self.registry.register_module(manifest) is True
        assert self.registry.register_module(manifest) is False

    def test_update_status(self) -> None:
        manifest = EcosystemModuleManifest(
            module_id="mod-003",
            name="Status Test",
            module_type=EcosystemModuleType.LABORATORY,
            version="1.0.0",
            description="Status test",
        )
        self.registry.register_module(manifest)
        assert self.registry.update_status("mod-003", ModuleReadinessStatus.ACTIVE) is True
        result = self.registry.get_module("mod-003")
        assert result is not None
        assert result.status == ModuleReadinessStatus.ACTIVE
        assert result.readiness_score == 1.0

    def test_update_nonexistent_returns_false(self) -> None:
        assert self.registry.update_status("missing", ModuleReadinessStatus.READY) is False


class TestModuleListing:
    def setup_method(self) -> None:
        self.registry = EcosystemRegistry()
        self.registry.register_module(EcosystemModuleManifest(
            module_id="m1", name="M1", module_type=EcosystemModuleType.CORE,
            version="1.0.0", description="Core",
        ))
        self.registry.register_module(EcosystemModuleManifest(
            module_id="m2", name="M2", module_type=EcosystemModuleType.LABORATORY,
            version="1.0.0", description="Lab",
        ))
        self.registry.register_module(EcosystemModuleManifest(
            module_id="m3", name="M3", module_type=EcosystemModuleType.CORE,
            version="2.0.0", description="Core v2",
            status=ModuleReadinessStatus.ACTIVE,
        ))

    def test_list_all_modules(self) -> None:
        modules = self.registry.list_modules()
        assert len(modules) == 3

    def test_list_by_type(self) -> None:
        core = self.registry.list_modules(module_type=EcosystemModuleType.CORE)
        assert len(core) == 2

    def test_list_by_status(self) -> None:
        active = self.registry.list_modules(status=ModuleReadinessStatus.ACTIVE)
        assert len(active) == 1

    def test_list_by_type_and_status(self) -> None:
        result = self.registry.list_modules(
            module_type=EcosystemModuleType.CORE,
            status=ModuleReadinessStatus.PLANNED,
        )
        assert len(result) == 1
        assert result[0].module_id == "m1"


class TestSharedServices:
    def setup_method(self) -> None:
        self.registry = EcosystemRegistry()

    def test_register_service(self) -> None:
        contract = SharedServiceContract(
            service_id="svc-001",
            service_name="Auth Service",
            version="1.0.0",
            endpoint="/api/auth",
            capabilities=["authenticate", "authorize"],
        )
        assert self.registry.register_shared_service(contract) is True
        result = self.registry.get_shared_service("svc-001")
        assert result is not None
        assert result.service_name == "Auth Service"

    def test_duplicate_service_rejected(self) -> None:
        contract = SharedServiceContract(
            service_id="svc-002",
            service_name="Duplicate",
            version="1.0.0",
            endpoint="/api/dup",
        )
        assert self.registry.register_shared_service(contract) is True
        assert self.registry.register_shared_service(contract) is False

    def test_list_services(self) -> None:
        self.registry.register_shared_service(SharedServiceContract(
            service_id="s1", service_name="S1", version="1.0.0", endpoint="/s1",
        ))
        self.registry.register_shared_service(SharedServiceContract(
            service_id="s2", service_name="S2", version="1.0.0", endpoint="/s2",
        ))
        services = self.registry.list_shared_services()
        assert len(services) == 2


class TestReadinessValidation:
    def setup_method(self) -> None:
        self.registry = EcosystemRegistry()

    def test_validate_module_not_found(self) -> None:
        ready, issues = self.registry.validate_module_readiness("missing")
        assert ready is False
        assert "not found" in issues[0]

    def test_validate_missing_dependencies(self) -> None:
        self.registry.register_module(EcosystemModuleManifest(
            module_id="dep-a", name="Dep A", module_type=EcosystemModuleType.CORE,
            version="1.0.0", description="Dep",
        ))
        self.registry.register_module(EcosystemModuleManifest(
            module_id="consumer", name="Consumer", module_type=EcosystemModuleType.CORE,
            version="1.0.0", description="Needs deps",
            dependencies=["dep-a", "dep-missing"],
        ))
        ready, issues = self.registry.validate_module_readiness("consumer")
        assert ready is False
        assert any("dep-missing" in i for i in issues)

    def test_validate_missing_service(self) -> None:
        self.registry.register_module(EcosystemModuleManifest(
            module_id="svc-consumer", name="Svc Consumer",
            module_type=EcosystemModuleType.LABORATORY,
            version="1.0.0", description="Needs service",
            shared_services=["svc-missing"],
        ))
        ready, issues = self.registry.validate_module_readiness("svc-consumer")
        assert ready is False
        assert any("svc-missing" in i for i in issues)

    def test_validate_ready_module(self) -> None:
        self.registry.register_shared_service(SharedServiceContract(
            service_id="auth", service_name="Auth", version="1.0.0", endpoint="/auth",
        ))
        self.registry.register_module(EcosystemModuleManifest(
            module_id="ready-mod", name="Ready Mod",
            module_type=EcosystemModuleType.CORE,
            version="1.0.0", description="Ready",
            shared_services=["auth"],
            status=ModuleReadinessStatus.READY,
        ))
        ready, issues = self.registry.validate_module_readiness("ready-mod")
        assert ready is True
        assert issues == []


class TestEcosystemReport:
    def setup_method(self) -> None:
        self.registry = EcosystemRegistry()

    def test_empty_report(self) -> None:
        report = self.registry.get_ecosystem_report()
        assert report["total_modules"] == 0
        assert report["total_shared_services"] == 0
        assert report["average_readiness_score"] == 0.0

    def test_report_with_modules(self) -> None:
        self.registry.register_module(EcosystemModuleManifest(
            module_id="m1", name="M1", module_type=EcosystemModuleType.CORE,
            version="1.0.0", description="M1",
            status=ModuleReadinessStatus.ACTIVE,
        ))
        self.registry.register_module(EcosystemModuleManifest(
            module_id="m2", name="M2", module_type=EcosystemModuleType.LABORATORY,
            version="1.0.0", description="M2",
            status=ModuleReadinessStatus.PLANNED,
        ))
        report = self.registry.get_ecosystem_report()
        assert report["total_modules"] == 2
        assert report["by_type"]["core"] == 1
        assert report["by_type"]["laboratory"] == 1
        assert report["by_status"]["active"] == 1
        assert report["by_status"]["planned"] == 1
        assert report["average_readiness_score"] == 0.5

    def test_calculate_readiness(self) -> None:
        self.registry.register_module(EcosystemModuleManifest(
            module_id="dep", name="Dep", module_type=EcosystemModuleType.CORE,
            version="1.0.0", description="Dep",
            status=ModuleReadinessStatus.ACTIVE,
        ))
        self.registry.register_shared_service(SharedServiceContract(
            service_id="svc", service_name="Svc", version="1.0.0", endpoint="/svc",
        ))
        self.registry.register_module(EcosystemModuleManifest(
            module_id="target", name="Target", module_type=EcosystemModuleType.CORE,
            version="1.0.0", description="Target",
            dependencies=["dep"],
            shared_services=["svc"],
            status=ModuleReadinessStatus.TESTING,
        ))
        score = self.registry.calculate_readiness("target")
        assert score > 0.5
        assert score <= 1.0
