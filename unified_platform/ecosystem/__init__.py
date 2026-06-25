"""
Platform Ecosystem — Ecosystem Module Preparation

Phase 9: Ecosystem Module Preparation
Constitution: Principle 10 (Long-Term Vision), Principle 13 (National Platform Compatibility)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EcosystemModuleType(Enum):
    CORE = "core"
    LABORATORY = "laboratory"
    WORKFORCE = "workforce"
    TRAINING = "training"
    INVENTORY = "inventory"
    QUALITY = "quality"
    SURVEILLANCE = "surveillance"
    PUBLIC_HEALTH = "public_health"


class ModuleReadinessStatus(Enum):
    PLANNED = "planned"
    IN_DEVELOPMENT = "in_development"
    TESTING = "testing"
    READY = "ready"
    ACTIVE = "active"


_READINESS_SCORES: dict[ModuleReadinessStatus, float] = {
    ModuleReadinessStatus.PLANNED: 0.0,
    ModuleReadinessStatus.IN_DEVELOPMENT: 0.25,
    ModuleReadinessStatus.TESTING: 0.5,
    ModuleReadinessStatus.READY: 0.75,
    ModuleReadinessStatus.ACTIVE: 1.0,
}


@dataclass
class EcosystemModuleManifest:
    module_id: str
    name: str
    module_type: EcosystemModuleType
    version: str
    description: str
    dependencies: list[str] = field(default_factory=list)
    shared_services: list[str] = field(default_factory=list)
    status: ModuleReadinessStatus = ModuleReadinessStatus.PLANNED
    readiness_score: float = 0.0


@dataclass
class SharedServiceContract:
    service_id: str
    service_name: str
    version: str
    endpoint: str
    capabilities: list[str] = field(default_factory=list)
    backward_compatible: bool = True


class EcosystemRegistry:
    def __init__(self) -> None:
        self._modules: dict[str, EcosystemModuleManifest] = {}
        self._services: dict[str, SharedServiceContract] = {}

    def register_module(self, manifest: EcosystemModuleManifest) -> bool:
        if manifest.module_id in self._modules:
            return False
        manifest.readiness_score = _READINESS_SCORES.get(manifest.status, 0.0)
        self._modules[manifest.module_id] = manifest
        return True

    def get_module(self, module_id: str) -> EcosystemModuleManifest | None:
        return self._modules.get(module_id)

    def list_modules(
        self,
        module_type: EcosystemModuleType | None = None,
        status: ModuleReadinessStatus | None = None,
    ) -> list[EcosystemModuleManifest]:
        modules = list(self._modules.values())
        if module_type is not None:
            modules = [m for m in modules if m.module_type == module_type]
        if status is not None:
            modules = [m for m in modules if m.status == status]
        return modules

    def update_status(self, module_id: str, status: ModuleReadinessStatus) -> bool:
        module = self._modules.get(module_id)
        if module is None:
            return False
        module.status = status
        module.readiness_score = _READINESS_SCORES.get(status, 0.0)
        return True

    def calculate_readiness(self, module_id: str) -> float:
        module = self._modules.get(module_id)
        if module is None:
            return 0.0
        base = _READINESS_SCORES.get(module.status, 0.0)
        deps_met = all(dep_id in self._modules for dep_id in module.dependencies)
        services_met = all(svc in self._services for svc in module.shared_services)
        bonus = 0.1 if deps_met else -0.1
        service_bonus = 0.05 if services_met else -0.05
        score = max(0.0, min(1.0, base + bonus + service_bonus))
        module.readiness_score = score
        return score

    def register_shared_service(self, contract: SharedServiceContract) -> bool:
        if contract.service_id in self._services:
            return False
        self._services[contract.service_id] = contract
        return True

    def get_shared_service(self, service_id: str) -> SharedServiceContract | None:
        return self._services.get(service_id)

    def list_shared_services(self) -> list[SharedServiceContract]:
        return list(self._services.values())

    def validate_module_readiness(self, module_id: str) -> tuple[bool, list[str]]:
        module = self._modules.get(module_id)
        if module is None:
            return False, [f"Module '{module_id}' not found"]
        issues: list[str] = []
        for dep_id in module.dependencies:
            if dep_id not in self._modules:
                issues.append(f"Missing dependency: {dep_id}")
            elif self._modules[dep_id].status == ModuleReadinessStatus.PLANNED:
                issues.append(f"Dependency not ready: {dep_id}")
        for svc_id in module.shared_services:
            if svc_id not in self._services:
                issues.append(f"Missing shared service: {svc_id}")
        if module.status == ModuleReadinessStatus.PLANNED:
            issues.append("Module status is PLANNED")
        return len(issues) == 0, issues

    def get_ecosystem_report(self) -> dict[str, Any]:
        modules = list(self._modules.values())
        services = list(self._services.values())
        by_type: dict[str, int] = {}
        for m in modules:
            key = m.module_type.value
            by_type[key] = by_type.get(key, 0) + 1
        by_status: dict[str, int] = {}
        for m in modules:
            key = m.status.value
            by_status[key] = by_status.get(key, 0) + 1
        avg_readiness = (
            sum(m.readiness_score for m in modules) / len(modules)
            if modules
            else 0.0
        )
        return {
            "total_modules": len(modules),
            "total_shared_services": len(services),
            "by_type": by_type,
            "by_status": by_status,
            "average_readiness_score": round(avg_readiness, 2),
            "ready_modules": len([m for m in modules if m.status in (ModuleReadinessStatus.READY, ModuleReadinessStatus.ACTIVE)]),
        }
