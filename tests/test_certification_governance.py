"""Tests for Certification Governance Engine (Phase 14)."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from unified_platform.certification import (
    Certification,
    CertificationEngine,
    CertificationFinding,
    CertificationStatus,
    CertificationType,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine() -> CertificationEngine:
    return CertificationEngine()


@pytest.fixture
def in_progress_cert(engine: CertificationEngine) -> Certification:
    return engine.start_certification(
        cert_id="cert-1",
        cert_type=CertificationType.SECURITY,
        issued_by="auditor",
    )


@pytest.fixture
def sample_finding() -> CertificationFinding:
    return CertificationFinding(
        finding_id="f-1",
        severity="critical",
        description="Missing encryption",
        component="storage",
        remediation="Enable AES-256",
    )


# ---------------------------------------------------------------------------
# 1. TestCertificationFinding
# ---------------------------------------------------------------------------

class TestCertificationFinding:
    def test_creation(self, sample_finding: CertificationFinding) -> None:
        assert sample_finding.finding_id == "f-1"
        assert sample_finding.severity == "critical"
        assert sample_finding.resolved is False
        assert sample_finding.resolved_at is None
        assert isinstance(sample_finding.created_at, datetime)

    def test_to_dict(self, sample_finding: CertificationFinding) -> None:
        d = sample_finding.to_dict()
        assert d["finding_id"] == "f-1"
        assert d["severity"] == "critical"
        assert d["description"] == "Missing encryption"
        assert d["component"] == "storage"
        assert d["remediation"] == "Enable AES-256"
        assert d["resolved"] is False
        assert d["resolved_at"] is None
        assert "created_at" in d


# ---------------------------------------------------------------------------
# 2. TestCertification
# ---------------------------------------------------------------------------

class TestCertification:
    def test_creation(self, in_progress_cert: Certification) -> None:
        assert in_progress_cert.cert_id == "cert-1"
        assert in_progress_cert.cert_type == CertificationType.SECURITY
        assert in_progress_cert.status == CertificationStatus.IN_PROGRESS
        assert in_progress_cert.findings == []
        assert isinstance(in_progress_cert.created_at, datetime)

    def test_is_active_not_certified(self, in_progress_cert: Certification) -> None:
        assert in_progress_cert.is_active is False

    def test_is_active_certified_no_expiry(self) -> None:
        cert = Certification(
            cert_id="c1",
            cert_type=CertificationType.PERFORMANCE,
            status=CertificationStatus.CERTIFIED,
        )
        assert cert.is_active is True

    def test_is_active_certified_expired(self) -> None:
        cert = Certification(
            cert_id="c2",
            cert_type=CertificationType.PERFORMANCE,
            status=CertificationStatus.CERTIFIED,
            expires_at=datetime.utcnow() - timedelta(days=1),
        )
        assert cert.is_active is False

    def test_has_critical_findings_false(self, in_progress_cert: Certification) -> None:
        assert in_progress_cert.has_critical_findings is False

    def test_has_critical_findings_true(self, in_progress_cert: Certification, sample_finding: CertificationFinding) -> None:
        in_progress_cert.findings.append(sample_finding)
        assert in_progress_cert.has_critical_findings is True

    def test_has_critical_findings_resolved(self, in_progress_cert: Certification, sample_finding: CertificationFinding) -> None:
        sample_finding.resolved = True
        in_progress_cert.findings.append(sample_finding)
        assert in_progress_cert.has_critical_findings is False

    def test_to_dict(self, in_progress_cert: Certification) -> None:
        d = in_progress_cert.to_dict()
        assert d["cert_id"] == "cert-1"
        assert d["status"] == "in_progress"
        assert d["cert_type"] == "security"
        assert isinstance(d["findings"], list)


# ---------------------------------------------------------------------------
# 3. TestCertificationEngine
# ---------------------------------------------------------------------------

class TestCertificationEngine:
    def test_start_certification(self, engine: CertificationEngine) -> None:
        cert = engine.start_certification(
            cert_id="c-100",
            cert_type=CertificationType.RECOVERY,
            issued_by="admin",
        )
        assert cert.cert_id == "c-100"
        assert cert.status == CertificationStatus.IN_PROGRESS
        assert cert.cert_type == CertificationType.RECOVERY

    def test_get_certification(self, engine: CertificationEngine, in_progress_cert: Certification) -> None:
        result = engine.get_certification("cert-1")
        assert result is in_progress_cert

    def test_get_certification_not_found(self, engine: CertificationEngine) -> None:
        assert engine.get_certification("nonexistent") is None

    def test_add_finding(self, engine: CertificationEngine, in_progress_cert: Certification, sample_finding: CertificationFinding) -> None:
        ok = engine.add_finding("cert-1", sample_finding)
        assert ok is True
        assert len(in_progress_cert.findings) == 1

    def test_add_finding_unknown_cert(self, engine: CertificationEngine, sample_finding: CertificationFinding) -> None:
        ok = engine.add_finding("nope", sample_finding)
        assert ok is False

    def test_add_finding_not_in_progress(self, engine: CertificationEngine, sample_finding: CertificationFinding) -> None:
        engine.start_certification("done", CertificationType.BACKUP, "x")
        engine.complete_certification("done", passed=True)
        ok = engine.add_finding("done", sample_finding)
        assert ok is False

    def test_resolve_finding(self, engine: CertificationEngine, in_progress_cert: Certification, sample_finding: CertificationFinding) -> None:
        engine.add_finding("cert-1", sample_finding)
        ok = engine.resolve_finding("cert-1", "f-1")
        assert ok is True
        assert sample_finding.resolved is True
        assert sample_finding.resolved_at is not None

    def test_resolve_finding_unknown_cert(self, engine: CertificationEngine) -> None:
        assert engine.resolve_finding("nope", "f-1") is False

    def test_resolve_finding_unknown_finding(self, engine: CertificationEngine, in_progress_cert: Certification) -> None:
        engine.add_finding("cert-1", CertificationFinding(
            finding_id="exists", severity="low", description="d", component="c", remediation="r",
        ))
        assert engine.resolve_finding("cert-1", "missing") is False

    def test_complete_certification_passed(self, engine: CertificationEngine, in_progress_cert: Certification) -> None:
        ok = engine.complete_certification("cert-1", passed=True)
        assert ok is True
        assert in_progress_cert.status == CertificationStatus.CERTIFIED
        assert in_progress_cert.issued_at is not None
        assert in_progress_cert.expires_at is not None
        assert in_progress_cert.expires_at > datetime.utcnow()

    def test_complete_certification_failed(self, engine: CertificationEngine, in_progress_cert: Certification) -> None:
        ok = engine.complete_certification("cert-1", passed=False)
        assert ok is True
        assert in_progress_cert.status == CertificationStatus.FAILED

    def test_complete_certification_unknown_cert(self, engine: CertificationEngine) -> None:
        assert engine.complete_certification("nope", passed=True) is False

    def test_complete_certification_not_in_progress(self, engine: CertificationEngine) -> None:
        engine.start_certification("x", CertificationType.ARCHITECTURE, "y")
        engine.complete_certification("x", passed=True)
        assert engine.complete_certification("x", passed=False) is False

    def test_list_certifications(self, engine: CertificationEngine, in_progress_cert: Certification) -> None:
        engine.start_certification("c2", CertificationType.BACKUP, "a")
        certs = engine.list_certifications()
        assert len(certs) == 2

    def test_list_certifications_by_type(self, engine: CertificationEngine, in_progress_cert: Certification) -> None:
        engine.start_certification("c2", CertificationType.BACKUP, "a")
        security = engine.list_certifications(cert_type=CertificationType.SECURITY)
        assert len(security) == 1
        assert security[0].cert_type == CertificationType.SECURITY

    def test_is_certified_true(self, engine: CertificationEngine) -> None:
        engine.start_certification("ok", CertificationType.PERFORMANCE, "u")
        engine.complete_certification("ok", passed=True)
        assert engine.is_certified(CertificationType.PERFORMANCE) is True

    def test_is_certified_no_certs(self, engine: CertificationEngine) -> None:
        assert engine.is_certified(CertificationType.SECURITY) is False

    def test_is_certified_failed(self, engine: CertificationEngine) -> None:
        engine.start_certification("f", CertificationType.SYNC, "u")
        engine.complete_certification("f", passed=False)
        assert engine.is_certified(CertificationType.SYNC) is False

    def test_is_certified_with_critical(self, engine: CertificationEngine) -> None:
        engine.start_certification("crit", CertificationType.ARCHITECTURE, "u")
        engine.add_finding("crit", CertificationFinding(
            finding_id="cf", severity="critical", description="d", component="c", remediation="r",
        ))
        engine.complete_certification("crit", passed=True)
        assert engine.is_certified(CertificationType.ARCHITECTURE) is False

    def test_is_certified_with_high(self, engine: CertificationEngine) -> None:
        engine.start_certification("hi", CertificationType.AI_GOVERNANCE, "u")
        engine.add_finding("hi", CertificationFinding(
            finding_id="hf", severity="high", description="d", component="c", remediation="r",
        ))
        engine.complete_certification("hi", passed=True)
        assert engine.is_certified(CertificationType.AI_GOVERNANCE) is False

    def test_get_certification_report_empty(self, engine: CertificationEngine) -> None:
        report = engine.get_certification_report()
        assert report["total"] == 0
        assert report["overall_status"] == "no_certifications"

    def test_get_certification_report_fully_certified(self, engine: CertificationEngine) -> None:
        engine.start_certification("a", CertificationType.SECURITY, "u")
        engine.complete_certification("a", passed=True)
        engine.start_certification("b", CertificationType.BACKUP, "u")
        engine.complete_certification("b", passed=True)
        report = engine.get_certification_report()
        assert report["total"] == 2
        assert report["certified_count"] == 2
        assert report["overall_status"] == "fully_certified"

    def test_get_certification_report_partially_certified(self, engine: CertificationEngine) -> None:
        engine.start_certification("a", CertificationType.SECURITY, "u")
        engine.complete_certification("a", passed=True)
        engine.start_certification("b", CertificationType.BACKUP, "u")
        report = engine.get_certification_report()
        assert report["total"] == 2
        assert report["certified_count"] == 1
        assert report["overall_status"] == "partially_certified"

    def test_get_certification_report_not_certified(self, engine: CertificationEngine) -> None:
        engine.start_certification("a", CertificationType.SECURITY, "u")
        report = engine.get_certification_report()
        assert report["overall_status"] == "not_certified"
