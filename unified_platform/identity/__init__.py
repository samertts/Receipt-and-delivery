"""
Unified Platform V7.0 — Phase 2: National Identity Fabric

Provides identity management, federated authentication, province-level
isolation, and organization-level data boundary enforcement for national
scale deployment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4


# ============================================================================
# Enums
# ============================================================================

class IdentityProvider(Enum):
    LOCAL = "local"
    FEDERATED = "federated"
    SSO = "sso"
    EXTERNAL = "external"


class IdentityStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    PENDING = "pending"


# ============================================================================
# Data Contracts
# ============================================================================

@dataclass
class IdentityToken:
    """An authentication token issued to a user."""
    token_id: str
    user_id: str
    provider: IdentityProvider
    issued_at: datetime
    expires_at: datetime
    scopes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FederatedDomain:
    """A federated identity domain configuration."""
    domain_id: str
    domain_name: str
    provider: IdentityProvider
    endpoint: str
    trust_level: int
    status: IdentityStatus = IdentityStatus.ACTIVE
    last_sync: datetime | None = None


@dataclass
class IdentityProfile:
    """A user's identity profile within the fabric."""
    user_id: str
    username: str
    display_name: str
    email: str
    organization_id: str
    province_id: str
    roles: list[str] = field(default_factory=list)
    status: IdentityStatus = IdentityStatus.ACTIVE
    provider: IdentityProvider = IdentityProvider.LOCAL
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ProvinceBoundary:
    """Defines a province's data isolation boundaries."""
    province_id: str
    province_name: str
    isolation_level: str
    data_residency: str
    cross_border_policy: str


@dataclass
class OrganizationBoundary:
    """Defines an organization's data access boundaries within a province."""
    org_id: str
    org_name: str
    province_id: str
    data_scope: str
    access_level: str


# ============================================================================
# National Identity Fabric
# ============================================================================

class NationalIdentityFabric:
    """Central identity fabric supporting local, federated, SSO, and external
    providers with province and organization level isolation."""

    def __init__(self) -> None:
        self._identities: dict[str, IdentityProfile] = {}
        self._tokens: dict[str, IdentityToken] = {}
        self._federated_domains: dict[str, FederatedDomain] = {}
        self._province_boundaries: dict[str, ProvinceBoundary] = {}
        self._org_boundaries: dict[str, OrganizationBoundary] = {}

    # -- Identity management ------------------------------------------------

    def create_identity(self, profile: IdentityProfile) -> IdentityProfile:
        self._identities[profile.user_id] = profile
        return profile

    def get_identity(self, user_id: str) -> IdentityProfile | None:
        return self._identities.get(user_id)

    def suspend_identity(self, user_id: str) -> bool:
        profile = self._identities.get(user_id)
        if profile is None:
            return False
        if profile.status != IdentityStatus.ACTIVE:
            return False
        profile.status = IdentityStatus.SUSPENDED
        return True

    def revoke_identity(self, user_id: str) -> bool:
        profile = self._identities.get(user_id)
        if profile is None:
            return False
        profile.status = IdentityStatus.REVOKED
        return True

    # -- Authentication & Tokens --------------------------------------------

    def authenticate(self, user_id: str, credentials: dict[str, Any]) -> IdentityToken | None:
        profile = self._identities.get(user_id)
        if profile is None:
            return None
        if profile.status != IdentityStatus.ACTIVE:
            return None
        token_id = uuid4().hex
        now = datetime.utcnow()
        token = IdentityToken(
            token_id=token_id,
            user_id=user_id,
            provider=profile.provider,
            issued_at=now,
            expires_at=now + timedelta(hours=1),
            scopes=list(profile.roles),
            metadata={"org_id": profile.organization_id, "province_id": profile.province_id},
        )
        self._tokens[token_id] = token
        return token

    def validate_token(self, token: IdentityToken) -> bool:
        if token.token_id not in self._tokens:
            return False
        stored = self._tokens[token.token_id]
        if stored.expires_at < datetime.utcnow():
            return False
        profile = self._identities.get(token.user_id)
        if profile is None or profile.status != IdentityStatus.ACTIVE:
            return False
        return True

    # -- Federated domains --------------------------------------------------

    def register_federated_domain(self, domain: FederatedDomain) -> bool:
        if domain.domain_id in self._federated_domains:
            return False
        self._federated_domains[domain.domain_id] = domain
        return True

    def get_federated_domain(self, domain_id: str) -> FederatedDomain | None:
        return self._federated_domains.get(domain_id)

    def list_federated_domains(self) -> list[FederatedDomain]:
        return list(self._federated_domains.values())

    # -- Province & Organization boundaries ---------------------------------

    def create_province_boundary(self, boundary: ProvinceBoundary) -> bool:
        self._province_boundaries[boundary.province_id] = boundary
        return True

    def create_organization_boundary(self, boundary: OrganizationBoundary) -> bool:
        self._org_boundaries[boundary.org_id] = boundary
        return True

    def check_province_isolation(self, user_id: str, target_province_id: str) -> bool:
        profile = self._identities.get(user_id)
        if profile is None:
            return False
        boundary = self._province_boundaries.get(profile.province_id)
        if boundary is None:
            return True
        if profile.province_id == target_province_id:
            return True
        if boundary.cross_border_policy == "allowed":
            return True
        return False

    def check_organization_isolation(self, user_id: str, target_org_id: str) -> bool:
        profile = self._identities.get(user_id)
        if profile is None:
            return False
        if profile.organization_id == target_org_id:
            return True
        boundary = self._org_boundaries.get(profile.organization_id)
        if boundary is None:
            return True
        if boundary.access_level == "cross_org":
            return True
        return False

    # -- Reporting ----------------------------------------------------------

    def get_identity_report(self) -> dict[str, Any]:
        status_counts: dict[str, int] = {}
        provider_counts: dict[str, int] = {}
        for p in self._identities.values():
            s = p.status.value
            pr = p.provider.value
            status_counts[s] = status_counts.get(s, 0) + 1
            provider_counts[pr] = provider_counts.get(pr, 0) + 1
        return {
            "total_identities": len(self._identities),
            "total_tokens": len(self._tokens),
            "status_counts": status_counts,
            "provider_counts": provider_counts,
            "federated_domains": len(self._federated_domains),
            "province_boundaries": len(self._province_boundaries),
            "org_boundaries": len(self._org_boundaries),
        }
