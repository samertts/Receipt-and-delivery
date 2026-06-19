"""
Platform Certification — Certification Governance Engine

Phase 14: Certification Governance
Constitution: Principle 22 (No Release Without Certification), Principle 23 (No Deployment With Critical Findings)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class CertificationType(Enum):
    """Types of certification available."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    RECOVERY = "recovery"
    BACKUP = "backup"
    SYNC = "sync"
    ARCHITECTURE = "architecture"
    AI_GOVERNANCE = "ai_governance"


class CertificationStatus(Enum):
    """Status of a certification."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    CERTIFIED = "certified"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class CertificationFinding:
    """A finding within a certification audit."""
    finding_id: str
    severity: str
    description: str
    component: str
    remediation: str
    resolved: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "severity": self.severity,
            "description": self.description,
            "component": self.component,
            "remediation": self.remediation,
            "resolved": self.resolved,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


@dataclass
class Certification:
    """A certification record."""
    cert_id: str
    cert_type: CertificationType
    status: CertificationStatus
    findings: list[CertificationFinding] = field(default_factory=list)
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    issued_by: str = ""
    version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cert_id": self.cert_id,
            "cert_type": self.cert_type.value,
            "status": self.status.value,
            "findings": [f.to_dict() for f in self.findings],
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "issued_by": self.issued_by,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
        }

    @property
    def is_active(self) -> bool:
        """Check if certification is currently active (certified and not expired)."""
        if self.status != CertificationStatus.CERTIFIED:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True

    @property
    def has_critical_findings(self) -> bool:
        """Check if there are unresolved critical findings."""
        return any(
            f.severity == "critical" and not f.resolved
            for f in self.findings
        )

    @property
    def has_high_findings(self) -> bool:
        """Check if there are unresolved high severity findings."""
        return any(
            f.severity == "high" and not f.resolved
            for f in self.findings
        )


class CertificationEngine:
    """Engine for managing platform certifications."""

    def __init__(self) -> None:
        self._certifications: dict[str, Certification] = {}

    def start_certification(
        self,
        cert_id: str,
        cert_type: CertificationType,
        issued_by: str,
    ) -> Certification:
        """Start a new certification process."""
        cert = Certification(
            cert_id=cert_id,
            cert_type=cert_type,
            status=CertificationStatus.IN_PROGRESS,
            issued_by=issued_by,
        )
        self._certifications[cert_id] = cert
        return cert

    def add_finding(self, cert_id: str, finding: CertificationFinding) -> bool:
        """Add a finding to a certification."""
        cert = self._certifications.get(cert_id)
        if not cert:
            return False
        if cert.status != CertificationStatus.IN_PROGRESS:
            return False
        cert.findings.append(finding)
        return True

    def resolve_finding(self, cert_id: str, finding_id: str) -> bool:
        """Mark a finding as resolved."""
        cert = self._certifications.get(cert_id)
        if not cert:
            return False
        for finding in cert.findings:
            if finding.finding_id == finding_id:
                finding.resolved = True
                finding.resolved_at = datetime.utcnow()
                return True
        return False

    def complete_certification(self, cert_id: str, passed: bool) -> bool:
        """Complete a certification process."""
        cert = self._certifications.get(cert_id)
        if not cert:
            return False
        if cert.status != CertificationStatus.IN_PROGRESS:
            return False

        if passed:
            cert.status = CertificationStatus.CERTIFIED
            cert.issued_at = datetime.utcnow()
            cert.expires_at = datetime.utcnow() + timedelta(days=365)
        else:
            cert.status = CertificationStatus.FAILED
        return True

    def get_certification(self, cert_id: str) -> Certification | None:
        """Get a certification by ID."""
        return self._certifications.get(cert_id)

    def list_certifications(
        self,
        cert_type: CertificationType | None = None,
    ) -> list[Certification]:
        """List all certifications, optionally filtered by type."""
        certs = list(self._certifications.values())
        if cert_type:
            certs = [c for c in certs if c.cert_type == cert_type]
        return certs

    def is_certified(self, cert_type: CertificationType) -> bool:
        """Check if at least one active certification of this type exists."""
        for cert in self._certifications.values():
            if (
                cert.cert_type == cert_type
                and cert.status == CertificationStatus.CERTIFIED
                and not cert.has_critical_findings
                and not cert.has_high_findings
                and cert.is_active
            ):
                return True
        return False

    def get_certification_report(self) -> dict[str, Any]:
        """Generate a certification summary report."""
        certs = list(self._certifications.values())
        total = len(certs)
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}

        for cert in certs:
            type_key = cert.cert_type.value
            status_key = cert.status.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
            by_status[status_key] = by_status.get(status_key, 0) + 1

        certified_count = by_status.get(CertificationStatus.CERTIFIED.value, 0)
        if total == 0:
            overall_status = "no_certifications"
        elif certified_count == total:
            overall_status = "fully_certified"
        elif certified_count > 0:
            overall_status = "partially_certified"
        else:
            overall_status = "not_certified"

        return {
            "total": total,
            "by_type": by_type,
            "by_status": by_status,
            "overall_status": overall_status,
            "certified_count": certified_count,
        }


__all__ = [
    "CertificationType",
    "CertificationStatus",
    "CertificationFinding",
    "Certification",
    "CertificationEngine",
]
