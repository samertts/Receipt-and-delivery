"""Tests for unified_platform/identity/__init__.py — National Identity Fabric."""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unified_platform.identity import (
    IdentityProvider,
    IdentityStatus,
    IdentityToken,
    FederatedDomain,
    IdentityProfile,
    ProvinceBoundary,
    OrganizationBoundary,
    NationalIdentityFabric,
)


# ============================================================================
# Test Identity Creation & Retrieval
# ============================================================================


class TestIdentityCreation:
    """Tests for create and get identity operations."""

    def _make_profile(self, user_id="u1", province="p1", org="o1"):
        return IdentityProfile(
            user_id=user_id, username=f"user_{user_id}",
            display_name="Test User", email=f"{user_id}@test.com",
            organization_id=org, province_id=province,
            roles=["viewer"], status=IdentityStatus.ACTIVE,
        )

    def test_create_identity_returns_profile(self):
        fab = NationalIdentityFabric()
        p = self._make_profile()
        assert fab.create_identity(p) is p

    def test_get_identity_returns_profile(self):
        fab = NationalIdentityFabric()
        p = self._make_profile()
        fab.create_identity(p)
        assert fab.get_identity("u1") is p

    def test_get_unknown_identity_returns_none(self):
        fab = NationalIdentityFabric()
        assert fab.get_identity("unknown") is None

    def test_create_multiple_identities(self):
        fab = NationalIdentityFabric()
        fab.create_identity(self._make_profile(user_id="a"))
        fab.create_identity(self._make_profile(user_id="b"))
        assert fab.get_identity("a") is not None
        assert fab.get_identity("b") is not None


# ============================================================================
# Test Suspend / Revoke
# ============================================================================


class TestIdentitySuspendRevoke:
    """Tests for suspend and revoke operations."""

    def _make_profile(self, user_id="u1"):
        return IdentityProfile(
            user_id=user_id, username=f"user_{user_id}",
            display_name="Test User", email=f"{user_id}@test.com",
            organization_id="o1", province_id="p1",
            roles=["viewer"], status=IdentityStatus.ACTIVE,
        )

    def test_suspend_active_identity(self):
        fab = NationalIdentityFabric()
        fab.create_identity(self._make_profile())
        assert fab.suspend_identity("u1") is True
        assert fab.get_identity("u1").status == IdentityStatus.SUSPENDED

    def test_suspend_already_suspended(self):
        fab = NationalIdentityFabric()
        fab.create_identity(self._make_profile())
        fab.suspend_identity("u1")
        assert fab.suspend_identity("u1") is False

    def test_suspend_unknown_returns_false(self):
        fab = NationalIdentityFabric()
        assert fab.suspend_identity("unknown") is False

    def test_revoke_identity(self):
        fab = NationalIdentityFabric()
        fab.create_identity(self._make_profile())
        assert fab.revoke_identity("u1") is True
        assert fab.get_identity("u1").status == IdentityStatus.REVOKED

    def test_revoke_unknown_returns_false(self):
        fab = NationalIdentityFabric()
        assert fab.revoke_identity("unknown") is False


# ============================================================================
# Test Authentication & Tokens
# ============================================================================


class TestAuthentication:
    """Tests for authenticate and validate_token operations."""

    def _make_fabric(self):
        fab = NationalIdentityFabric()
        fab.create_identity(IdentityProfile(
            user_id="u1", username="user1", display_name="User One",
            email="u1@test.com", organization_id="o1", province_id="p1",
            roles=["admin", "viewer"], status=IdentityStatus.ACTIVE,
            provider=IdentityProvider.LOCAL,
        ))
        return fab

    def test_authenticate_returns_token(self):
        fab = self._make_fabric()
        token = fab.authenticate("u1", {"password": "secret"})
        assert token is not None
        assert token.user_id == "u1"
        assert token.provider == IdentityProvider.LOCAL
        assert "admin" in token.scopes

    def test_authenticate_unknown_user_returns_none(self):
        fab = NationalIdentityFabric()
        assert fab.authenticate("unknown", {}) is None

    def test_authenticate_suspended_user_returns_none(self):
        fab = self._make_fabric()
        fab.suspend_identity("u1")
        assert fab.authenticate("u1", {}) is None

    def test_validate_valid_token(self):
        fab = self._make_fabric()
        token = fab.authenticate("u1", {})
        assert fab.validate_token(token) is True

    def test_validate_expired_token(self):
        fab = self._make_fabric()
        token = fab.authenticate("u1", {})
        token.expires_at = datetime.utcnow() - timedelta(hours=1)
        assert fab.validate_token(token) is False

    def test_validate_token_unknown_token_id(self):
        fab = self._make_fabric()
        fake = IdentityToken(
            token_id="fake", user_id="u1", provider=IdentityProvider.LOCAL,
            issued_at=datetime.utcnow(), expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        assert fab.validate_token(fake) is False

    def test_validate_token_revoked_user(self):
        fab = self._make_fabric()
        token = fab.authenticate("u1", {})
        fab.revoke_identity("u1")
        assert fab.validate_token(token) is False


# ============================================================================
# Test Federated Domains
# ============================================================================


class TestFederatedDomains:
    """Tests for federated domain operations."""

    def _make_domain(self, domain_id="d1"):
        return FederatedDomain(
            domain_id=domain_id, domain_name=f"domain-{domain_id}",
            provider=IdentityProvider.FEDERATED,
            endpoint=f"https://{domain_id}.example.com",
            trust_level=5,
        )

    def test_register_domain(self):
        fab = NationalIdentityFabric()
        assert fab.register_federated_domain(self._make_domain()) is True

    def test_register_duplicate_domain(self):
        fab = NationalIdentityFabric()
        fab.register_federated_domain(self._make_domain())
        assert fab.register_federated_domain(self._make_domain()) is False

    def test_get_domain(self):
        fab = NationalIdentityFabric()
        d = self._make_domain()
        fab.register_federated_domain(d)
        assert fab.get_federated_domain("d1") is d

    def test_get_unknown_domain(self):
        fab = NationalIdentityFabric()
        assert fab.get_federated_domain("nope") is None

    def test_list_domains(self):
        fab = NationalIdentityFabric()
        fab.register_federated_domain(self._make_domain("a"))
        fab.register_federated_domain(self._make_domain("b"))
        assert len(fab.list_federated_domains()) == 2


# ============================================================================
# Test Province & Organization Boundaries
# ============================================================================


class TestBoundaries:
    """Tests for province and organization boundary isolation."""

    def _make_fabric_with_boundaries(self):
        fab = NationalIdentityFabric()
        fab.create_province_boundary(ProvinceBoundary(
            province_id="p1", province_name="Province One",
            isolation_level="strict", data_residency="local",
            cross_border_policy="denied",
        ))
        fab.create_province_boundary(ProvinceBoundary(
            province_id="p2", province_name="Province Two",
            isolation_level="relaxed", data_residency="local",
            cross_border_policy="allowed",
        ))
        fab.create_organization_boundary(OrganizationBoundary(
            org_id="o1", org_name="Org One", province_id="p1",
            data_scope="province", access_level="own_org",
        ))
        fab.create_organization_boundary(OrganizationBoundary(
            org_id="o2", org_name="Org Two", province_id="p1",
            data_scope="province", access_level="cross_org",
        ))
        return fab

    def test_province_isolation_same_province(self):
        fab = self._make_fabric_with_boundaries()
        fab.create_identity(IdentityProfile(
            user_id="u1", username="u1", display_name="U1",
            email="u1@test.com", organization_id="o1", province_id="p1",
        ))
        assert fab.check_province_isolation("u1", "p1") is True

    def test_province_isolation_cross_border_denied(self):
        fab = self._make_fabric_with_boundaries()
        fab.create_identity(IdentityProfile(
            user_id="u1", username="u1", display_name="U1",
            email="u1@test.com", organization_id="o1", province_id="p1",
        ))
        assert fab.check_province_isolation("u1", "p2") is False

    def test_province_isolation_cross_border_allowed(self):
        fab = self._make_fabric_with_boundaries()
        fab.create_identity(IdentityProfile(
            user_id="u2", username="u2", display_name="U2",
            email="u2@test.com", organization_id="o1", province_id="p2",
        ))
        assert fab.check_province_isolation("u2", "p1") is True

    def test_province_isolation_unknown_user(self):
        fab = self._make_fabric_with_boundaries()
        assert fab.check_province_isolation("unknown", "p1") is False

    def test_org_isolation_same_org(self):
        fab = self._make_fabric_with_boundaries()
        fab.create_identity(IdentityProfile(
            user_id="u1", username="u1", display_name="U1",
            email="u1@test.com", organization_id="o1", province_id="p1",
        ))
        assert fab.check_organization_isolation("u1", "o1") is True

    def test_org_isolation_cross_org_denied(self):
        fab = self._make_fabric_with_boundaries()
        fab.create_identity(IdentityProfile(
            user_id="u1", username="u1", display_name="U1",
            email="u1@test.com", organization_id="o1", province_id="p1",
        ))
        assert fab.check_organization_isolation("u1", "o2") is False

    def test_org_isolation_cross_org_allowed(self):
        fab = self._make_fabric_with_boundaries()
        fab.create_identity(IdentityProfile(
            user_id="u3", username="u3", display_name="U3",
            email="u3@test.com", organization_id="o2", province_id="p1",
        ))
        assert fab.check_organization_isolation("u3", "o1") is True

    def test_org_isolation_unknown_user(self):
        fab = self._make_fabric_with_boundaries()
        assert fab.check_organization_isolation("unknown", "o1") is False


# ============================================================================
# Test Identity Report
# ============================================================================


class TestIdentityReport:
    """Tests for get_identity_report."""

    def _make_fabric(self):
        fab = NationalIdentityFabric()
        fab.create_identity(IdentityProfile(
            user_id="u1", username="u1", display_name="U1",
            email="u1@test.com", organization_id="o1", province_id="p1",
            provider=IdentityProvider.LOCAL, status=IdentityStatus.ACTIVE,
        ))
        fab.create_identity(IdentityProfile(
            user_id="u2", username="u2", display_name="U2",
            email="u2@test.com", organization_id="o1", province_id="p1",
            provider=IdentityProvider.FEDERATED, status=IdentityStatus.SUSPENDED,
        ))
        fab.register_federated_domain(FederatedDomain(
            domain_id="d1", domain_name="d1", provider=IdentityProvider.FEDERATED,
            endpoint="https://d1.example.com", trust_level=3,
        ))
        return fab

    def test_report_totals(self):
        fab = self._make_fabric()
        r = fab.get_identity_report()
        assert r["total_identities"] == 2
        assert r["federated_domains"] == 1

    def test_report_status_counts(self):
        fab = self._make_fabric()
        r = fab.get_identity_report()
        assert r["status_counts"]["active"] == 1
        assert r["status_counts"]["suspended"] == 1

    def test_report_provider_counts(self):
        fab = self._make_fabric()
        r = fab.get_identity_report()
        assert r["provider_counts"]["local"] == 1
        assert r["provider_counts"]["federated"] == 1

    def test_report_after_token_creation(self):
        fab = self._make_fabric()
        fab.authenticate("u1", {})
        r = fab.get_identity_report()
        assert r["total_tokens"] == 1
