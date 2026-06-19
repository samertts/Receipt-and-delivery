"""
Platform National — National Scale Readiness

Phase 7: National Scale Readiness
Constitution: Principle 51 (National Scale), Principle 52 (Multi-Tenant)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# ============================================================================
# UUID Strategy
# ============================================================================

class UUIDGenerator:
    """Standardized UUID generation for national scale."""

    @staticmethod
    def generate() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def generate_short() -> str:
        return uuid.uuid4().hex[:12]

    @staticmethod
    def from_namespace(namespace: str, name: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{namespace}.{name}"))

    @staticmethod
    def validate(uuid_str: str) -> bool:
        try:
            uuid.UUID(uuid_str)
            return True
        except ValueError:
            return False


# ============================================================================
# API Versioning
# ============================================================================

class APIVersion:
    """API version management."""

    CURRENT = "v1"
    SUPPORTED = ("v1",)
    DEPRECATED = ()

    @classmethod
    def is_supported(cls, version: str) -> bool:
        return version in cls.SUPPORTED

    @classmethod
    def is_deprecated(cls, version: str) -> bool:
        return version in cls.DEPRECATED

    @classmethod
    def get_latest(cls) -> str:
        return cls.CURRENT


@dataclass
class APIEndpoint:
    """Versioned API endpoint contract."""
    path: str
    method: str
    version: str = "v1"
    description: str = ""
    deprecated: bool = False
    min_client_version: str = ""
    tags: tuple[str, ...] = ()


# ============================================================================
# Contract Versioning
# ============================================================================

@dataclass
class DataContract:
    """Versioned data contract for inter-system communication."""
    name: str
    version: str
    schema: dict[str, Any] = field(default_factory=dict)
    backward_compatible: bool = True
    deprecated: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


class ContractRegistry:
    """Registry for versioned data contracts."""

    def __init__(self) -> None:
        self._contracts: dict[str, list[DataContract]] = {}

    def register(self, contract: DataContract) -> None:
        if contract.name not in self._contracts:
            self._contracts[contract.name] = []
        self._contracts[contract.name].append(contract)

    def get_latest(self, name: str) -> DataContract | None:
        contracts = self._contracts.get(name, [])
        return contracts[-1] if contracts else None

    def get_version(self, name: str, version: str) -> DataContract | None:
        for c in self._contracts.get(name, []):
            if c.version == version:
                return c
        return None

    def list_all(self) -> dict[str, list[str]]:
        return {name: [c.version for c in contracts] for name, contracts in self._contracts.items()}


# ============================================================================
# Multi-Node Synchronization
# ============================================================================

class NodeStatus(Enum):
    ACTIVE = "active"
    SYNCING = "syncing"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass
class NodeInfo:
    """Information about a sync node."""
    node_id: str
    node_name: str
    node_type: str  # regional, national, local
    region: str = ""
    status: NodeStatus = NodeStatus.ACTIVE
    last_sync: datetime | None = None
    endpoint: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class NodeRegistry:
    """Registry for national/regional nodes."""

    def __init__(self) -> None:
        self._nodes: dict[str, NodeInfo] = {}

    def register(self, node: NodeInfo) -> None:
        self._nodes[node.node_id] = node

    def unregister(self, node_id: str) -> bool:
        if node_id in self._nodes:
            del self._nodes[node_id]
            return True
        return False

    def get(self, node_id: str) -> NodeInfo | None:
        return self._nodes.get(node_id)

    def list_all(self) -> list[NodeInfo]:
        return list(self._nodes.values())

    def list_by_type(self, node_type: str) -> list[NodeInfo]:
        return [n for n in self._nodes.values() if n.node_type == node_type]

    def list_by_region(self, region: str) -> list[NodeInfo]:
        return [n for n in self._nodes.values() if n.region == region]

    def list_active(self) -> list[NodeInfo]:
        return [n for n in self._nodes.values() if n.status == NodeStatus.ACTIVE]

    def update_status(self, node_id: str, status: NodeStatus) -> bool:
        if node_id in self._nodes:
            self._nodes[node_id].status = status
            return True
        return False


# ============================================================================
# Multi-Tenant Support
# ============================================================================

@dataclass
class TenantInfo:
    """Tenant configuration for multi-tenant support."""
    tenant_id: str
    name: str
    region: str = ""
    status: str = "active"
    max_users: int = 100
    features: tuple[str, ...] = ()
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


class TenantManager:
    """Multi-tenant management."""

    def __init__(self) -> None:
        self._tenants: dict[str, TenantInfo] = {}

    def register(self, tenant: TenantInfo) -> None:
        self._tenants[tenant.tenant_id] = tenant

    def get(self, tenant_id: str) -> TenantInfo | None:
        return self._tenants.get(tenant_id)

    def list_all(self) -> list[TenantInfo]:
        return list(self._tenants.values())

    def list_by_region(self, region: str) -> list[TenantInfo]:
        return [t for t in self._tenants.values() if t.region == region]


# ============================================================================
# National Scale Manager
# ============================================================================

class NationalScaleManager:
    """Central manager for national scale readiness."""

    def __init__(self) -> None:
        self.uuid = UUIDGenerator()
        self.contracts = ContractRegistry()
        self.nodes = NodeRegistry()
        self.tenants = TenantManager()

    def get_readiness_report(self) -> dict[str, Any]:
        return {
            "uuid_strategy": "UUID v4",
            "api_versioning": APIVersion.CURRENT,
            "supported_api_versions": list(APIVersion.SUPPORTED),
            "registered_contracts": len(self.contracts.list_all()),
            "registered_nodes": len(self.nodes.list_all()),
            "active_nodes": len(self.nodes.list_active()),
            "registered_tenants": len(self.tenants.list_all()),
            "national_ready": True,
        }
