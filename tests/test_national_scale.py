"""Tests for unified_platform/national/__init__.py — National Scale Readiness."""

import sys
import os
from uuid import UUID
from datetime import datetime


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unified_platform.national import (
    UUIDGenerator,
    APIVersion,
    APIEndpoint,
    DataContract,
    ContractRegistry,
    NodeStatus,
    NodeInfo,
    NodeRegistry,
    TenantInfo,
    TenantManager,
    NationalScaleManager,
)


# ============================================================================
# TestUUIDGenerator
# ============================================================================


class TestUUIDGenerator:
    """Tests for UUIDGenerator class."""

    def test_generate_returns_valid_uuid_format(self):
        result = UUIDGenerator.generate()
        assert isinstance(result, str)
        parts = result.split("-")
        assert len(parts) == 5

    def test_generate_returns_unique_values(self):
        results = {UUIDGenerator.generate() for _ in range(100)}
        assert len(results) == 100

    def test_generate_short_returns_12_chars(self):
        result = UUIDGenerator.generate_short()
        assert isinstance(result, str)
        assert len(result) == 12

    def test_generate_short_returns_unique_values(self):
        results = {UUIDGenerator.generate_short() for _ in range(100)}
        assert len(results) == 100

    def test_from_namespace_returns_valid_uuid(self):
        result = UUIDGenerator.from_namespace("example.com", "test")
        assert isinstance(result, str)
        UUID(result)  # should not raise

    def test_from_namespace_deterministic(self):
        r1 = UUIDGenerator.from_namespace("ns", "name")
        r2 = UUIDGenerator.from_namespace("ns", "name")
        assert r1 == r2

    def test_from_namespace_different_inputs_differ(self):
        r1 = UUIDGenerator.from_namespace("ns1", "name")
        r2 = UUIDGenerator.from_namespace("ns2", "name")
        assert r1 != r2

    def test_validate_valid_uuid(self):
        valid = UUIDGenerator.generate()
        assert UUIDGenerator.validate(valid) is True

    def test_validate_invalid_string(self):
        assert UUIDGenerator.validate("not-a-uuid") is False

    def test_validate_empty_string(self):
        assert UUIDGenerator.validate("") is False

    def test_validate_with_hyphens(self):
        assert UUIDGenerator.validate("550e8400-e29b-41d4-a716-446655440000") is True


# ============================================================================
# TestAPIVersion
# ============================================================================


class TestAPIVersion:
    """Tests for APIVersion class."""

    def test_current_version(self):
        assert APIVersion.CURRENT == "v1"

    def test_supported_versions(self):
        assert APIVersion.SUPPORTED == ("v1",)

    def test_deprecated_versions(self):
        assert APIVersion.DEPRECATED == ()

    def test_is_supported_v1(self):
        assert APIVersion.is_supported("v1") is True

    def test_is_supported_v2_false(self):
        assert APIVersion.is_supported("v2") is False

    def test_is_deprecated_empty(self):
        assert APIVersion.is_deprecated("v1") is False

    def test_get_latest(self):
        assert APIVersion.get_latest() == "v1"


# ============================================================================
# TestAPIEndpoint
# ============================================================================


class TestAPIEndpoint:
    """Tests for APIEndpoint dataclass."""

    def test_creation_with_defaults(self):
        ep = APIEndpoint(path="/api/test", method="GET")
        assert ep.path == "/api/test"
        assert ep.method == "GET"
        assert ep.version == "v1"
        assert ep.description == ""
        assert ep.deprecated is False
        assert ep.min_client_version == ""
        assert ep.tags == ()

    def test_creation_with_custom_values(self):
        ep = APIEndpoint(
            path="/api/v2/test",
            method="POST",
            version="v2",
            description="Test endpoint",
            deprecated=True,
            min_client_version="1.5.0",
            tags=("admin", "write"),
        )
        assert ep.version == "v2"
        assert ep.deprecated is True
        assert ep.tags == ("admin", "write")


# ============================================================================
# TestDataContract
# ============================================================================


class TestDataContract:
    """Tests for DataContract dataclass."""

    def test_creation_with_defaults(self):
        contract = DataContract(name="test", version="1.0")
        assert contract.name == "test"
        assert contract.version == "1.0"
        assert contract.schema == {}
        assert contract.backward_compatible is True
        assert contract.deprecated is False
        assert isinstance(contract.created_at, datetime)

    def test_creation_with_custom_values(self):
        contract = DataContract(
            name="receipt",
            version="2.0",
            schema={"fields": ["id", "amount"]},
            backward_compatible=False,
            deprecated=True,
        )
        assert contract.schema == {"fields": ["id", "amount"]}
        assert contract.backward_compatible is False
        assert contract.deprecated is True


# ============================================================================
# TestContractRegistry
# ============================================================================


class TestContractRegistry:
    """Tests for ContractRegistry class."""

    def setup_method(self):
        self.registry = ContractRegistry()

    def test_register_contract(self):
        c = DataContract(name="test", version="1.0")
        self.registry.register(c)
        result = self.registry.get_latest("test")
        assert result is not None
        assert result.version == "1.0"

    def test_get_latest_returns_none_for_unknown(self):
        assert self.registry.get_latest("unknown") is None

    def test_get_version(self):
        c = DataContract(name="test", version="1.0")
        self.registry.register(c)
        result = self.registry.get_version("test", "1.0")
        assert result is not None
        assert result.version == "1.0"

    def test_get_version_returns_none_for_missing(self):
        c = DataContract(name="test", version="1.0")
        self.registry.register(c)
        assert self.registry.get_version("test", "2.0") is None

    def test_list_all_empty(self):
        assert self.registry.list_all() == {}

    def test_list_all_with_contracts(self):
        self.registry.register(DataContract(name="a", version="1.0"))
        self.registry.register(DataContract(name="a", version="2.0"))
        self.registry.register(DataContract(name="b", version="1.0"))
        result = self.registry.list_all()
        assert result == {"a": ["1.0", "2.0"], "b": ["1.0"]}

    def test_multiple_versions_latest_is_last(self):
        self.registry.register(DataContract(name="x", version="1.0"))
        self.registry.register(DataContract(name="x", version="2.0"))
        self.registry.register(DataContract(name="x", version="3.0"))
        latest = self.registry.get_latest("x")
        assert latest.version == "3.0"


# ============================================================================
# TestNodeRegistry
# ============================================================================


class TestNodeRegistry:
    """Tests for NodeRegistry class."""

    def setup_method(self):
        self.registry = NodeRegistry()

    def _make_node(self, node_id="n1", node_type="regional", region="Baghdad", status=NodeStatus.ACTIVE):
        return NodeInfo(
            node_id=node_id,
            node_name=f"Node {node_id}",
            node_type=node_type,
            region=region,
            status=status,
        )

    def test_register_node(self):
        node = self._make_node()
        self.registry.register(node)
        assert self.registry.get("n1") is not None

    def test_unregister_existing(self):
        node = self._make_node()
        self.registry.register(node)
        assert self.registry.unregister("n1") is True
        assert self.registry.get("n1") is None

    def test_unregister_nonexistent(self):
        assert self.registry.unregister("missing") is False

    def test_get_returns_none_for_missing(self):
        assert self.registry.get("missing") is None

    def test_list_all(self):
        self.registry.register(self._make_node("n1"))
        self.registry.register(self._make_node("n2"))
        result = self.registry.list_all()
        assert len(result) == 2

    def test_list_all_empty(self):
        assert self.registry.list_all() == []

    def test_list_by_type(self):
        self.registry.register(self._make_node("n1", node_type="regional"))
        self.registry.register(self._make_node("n2", node_type="national"))
        self.registry.register(self._make_node("n3", node_type="regional"))
        result = self.registry.list_by_type("regional")
        assert len(result) == 2

    def test_list_by_region(self):
        self.registry.register(self._make_node("n1", region="Baghdad"))
        self.registry.register(self._make_node("n2", region="Basra"))
        self.registry.register(self._make_node("n3", region="Baghdad"))
        result = self.registry.list_by_region("Baghdad")
        assert len(result) == 2

    def test_list_active(self):
        self.registry.register(self._make_node("n1", status=NodeStatus.ACTIVE))
        self.registry.register(self._make_node("n2", status=NodeStatus.OFFLINE))
        self.registry.register(self._make_node("n3", status=NodeStatus.ACTIVE))
        result = self.registry.list_active()
        assert len(result) == 2

    def test_update_status_existing(self):
        self.registry.register(self._make_node("n1", status=NodeStatus.ACTIVE))
        assert self.registry.update_status("n1", NodeStatus.SYNCING) is True
        assert self.registry.get("n1").status == NodeStatus.SYNCING

    def test_update_status_nonexistent(self):
        assert self.registry.update_status("missing", NodeStatus.ACTIVE) is False


# ============================================================================
# TestTenantManager
# ============================================================================


class TestTenantManager:
    """Tests for TenantManager class."""

    def setup_method(self):
        self.manager = TenantManager()

    def test_register_tenant(self):
        t = TenantInfo(tenant_id="t1", name="Tenant One", region="Baghdad")
        self.manager.register(t)
        result = self.manager.get("t1")
        assert result is not None
        assert result.name == "Tenant One"

    def test_get_returns_none_for_missing(self):
        assert self.manager.get("missing") is None

    def test_list_all(self):
        self.manager.register(TenantInfo(tenant_id="t1", name="A"))
        self.manager.register(TenantInfo(tenant_id="t2", name="B"))
        assert len(self.manager.list_all()) == 2

    def test_list_all_empty(self):
        assert self.manager.list_all() == []

    def test_list_by_region(self):
        self.manager.register(TenantInfo(tenant_id="t1", name="A", region="Baghdad"))
        self.manager.register(TenantInfo(tenant_id="t2", name="B", region="Basra"))
        self.manager.register(TenantInfo(tenant_id="t3", name="C", region="Baghdad"))
        result = self.manager.list_by_region("Baghdad")
        assert len(result) == 2


# ============================================================================
# TestNationalScaleManager
# ============================================================================


class TestNationalScaleManager:
    """Tests for NationalScaleManager class."""

    def setup_method(self):
        self.manager = NationalScaleManager()

    def test_readiness_report_structure(self):
        report = self.manager.get_readiness_report()
        assert isinstance(report, dict)
        assert "uuid_strategy" in report
        assert "api_versioning" in report
        assert "supported_api_versions" in report
        assert "registered_contracts" in report
        assert "registered_nodes" in report
        assert "active_nodes" in report
        assert "registered_tenants" in report
        assert "national_ready" in report

    def test_readiness_report_values(self):
        report = self.manager.get_readiness_report()
        assert report["uuid_strategy"] == "UUID v4"
        assert report["api_versioning"] == "v1"
        assert report["supported_api_versions"] == ["v1"]
        assert report["registered_contracts"] == 0
        assert report["registered_nodes"] == 0
        assert report["active_nodes"] == 0
        assert report["registered_tenants"] == 0
        assert report["national_ready"] is True

    def test_readiness_report_after_registration(self):
        self.manager.contracts.register(DataContract(name="c1", version="1.0"))
        self.manager.contracts.register(DataContract(name="c2", version="1.0"))
        self.manager.nodes.register(NodeInfo(node_id="n1", node_name="N1", node_type="regional"))
        self.manager.tenants.register(TenantInfo(tenant_id="t1", name="T1"))
        report = self.manager.get_readiness_report()
        assert report["registered_contracts"] == 2
        assert report["registered_nodes"] == 1
        assert report["registered_tenants"] == 1

    def test_integration_full_workflow(self):
        self.manager.contracts.register(DataContract(name="receipt", version="1.0"))
        self.manager.contracts.register(DataContract(name="receipt", version="2.0"))
        assert self.manager.contracts.get_latest("receipt").version == "2.0"

        node = NodeInfo(node_id="n1", node_name="Main", node_type="national", region="Baghdad")
        self.manager.nodes.register(node)
        self.manager.nodes.update_status("n1", NodeStatus.SYNCING)
        assert self.manager.nodes.get("n1").status == NodeStatus.SYNCING

        self.manager.tenants.register(TenantInfo(tenant_id="t1", name="Lab1", region="Baghdad"))
        report = self.manager.get_readiness_report()
        assert report["national_ready"] is True
        assert report["registered_contracts"] == 1  # 2 versions under 1 name
        assert report["registered_nodes"] == 1
