"""
Tests for AI Capabilities — v6

Covers: ArchitectureAnalyzer, TechnicalDebtAnalyzer, DeploymentReadinessAnalyzer
"""

from __future__ import annotations

from unified_platform.ai import AIRecommendationType
from unified_platform.ai.capabilities import (
    ArchitectureAnalyzer,
    DeploymentReadinessAnalyzer,
    TechnicalDebtAnalyzer,
)


# ---------------------------------------------------------------------------
# 1. TestArchitectureAnalyzer
# ---------------------------------------------------------------------------
class TestArchitectureAnalyzer:
    def setup_method(self) -> None:
        self.analyzer = ArchitectureAnalyzer()

    def test_healthy_architecture(self) -> None:
        rec = self.analyzer.analyze({
            "service_count": 5,
            "circular_dependencies": 0,
            "api_version_count": 1,
            "contract_violations": 0,
            "module_count": 10,
            "shared_component_coverage": 0.9,
        })
        assert rec.type == AIRecommendationType.ARCHITECTURE
        assert rec.risk_level == "medium"
        assert any("Services: 5" in e for e in rec.evidence)

    def test_circular_dependencies(self) -> None:
        rec = self.analyzer.analyze({
            "service_count": 5,
            "circular_dependencies": 2,
            "api_version_count": 1,
            "contract_violations": 0,
            "module_count": 10,
            "shared_component_coverage": 0.9,
        })
        assert rec.risk_level == "critical"
        assert any("Circular" in a for a in rec.suggested_actions)

    def test_contract_violations(self) -> None:
        rec = self.analyzer.analyze({
            "service_count": 5,
            "circular_dependencies": 0,
            "api_version_count": 1,
            "contract_violations": 3,
            "module_count": 10,
            "shared_component_coverage": 0.9,
        })
        assert rec.risk_level == "critical"
        assert any("Contract" in a for a in rec.suggested_actions)

    def test_low_shared_coverage(self) -> None:
        rec = self.analyzer.analyze({
            "service_count": 5,
            "circular_dependencies": 0,
            "api_version_count": 1,
            "contract_violations": 0,
            "module_count": 10,
            "shared_component_coverage": 0.4,
        })
        assert any("critically low" in a.lower() for a in rec.suggested_actions)

    def test_multiple_api_versions(self) -> None:
        rec = self.analyzer.analyze({
            "service_count": 5,
            "circular_dependencies": 0,
            "api_version_count": 5,
            "contract_violations": 0,
            "module_count": 10,
            "shared_component_coverage": 0.9,
        })
        assert any("API versions" in a for a in rec.suggested_actions)

    def test_evidence_populated(self) -> None:
        rec = self.analyzer.analyze({
            "service_count": 3,
            "circular_dependencies": 0,
            "api_version_count": 1,
            "contract_violations": 0,
            "module_count": 7,
            "shared_component_coverage": 0.85,
        })
        assert any("Services: 3" in e for e in rec.evidence)


# ---------------------------------------------------------------------------
# 2. TestTechnicalDebtAnalyzer
# ---------------------------------------------------------------------------
class TestTechnicalDebtAnalyzer:
    def setup_method(self) -> None:
        self.analyzer = TechnicalDebtAnalyzer()

    def test_healthy_debt(self) -> None:
        rec = self.analyzer.analyze({
            "total_debt_items": 5,
            "critical_debt": 0,
            "high_debt": 0,
            "debt_age_days": 10,
            "remediation_rate": 0.8,
        })
        assert rec.type == AIRecommendationType.TECHNICAL_DEBT
        assert rec.risk_level == "medium"
        assert any("Total debt items: 5" in e for e in rec.evidence)

    def test_critical_debt(self) -> None:
        rec = self.analyzer.analyze({
            "total_debt_items": 20,
            "critical_debt": 3,
            "high_debt": 0,
            "debt_age_days": 5,
            "remediation_rate": 0.8,
        })
        assert rec.risk_level == "critical"
        assert any("Critical debt" in a for a in rec.suggested_actions)

    def test_old_debt(self) -> None:
        rec = self.analyzer.analyze({
            "total_debt_items": 10,
            "critical_debt": 0,
            "high_debt": 2,
            "debt_age_days": 100,
            "remediation_rate": 0.6,
        })
        assert any("critically high" in a.lower() for a in rec.suggested_actions)

    def test_low_remediation_rate(self) -> None:
        rec = self.analyzer.analyze({
            "total_debt_items": 10,
            "critical_debt": 0,
            "high_debt": 0,
            "debt_age_days": 10,
            "remediation_rate": 0.2,
        })
        assert any("critically low" in a.lower() for a in rec.suggested_actions)

    def test_high_debt_items(self) -> None:
        rec = self.analyzer.analyze({
            "total_debt_items": 15,
            "critical_debt": 0,
            "high_debt": 8,
            "debt_age_days": 20,
            "remediation_rate": 0.6,
        })
        assert any("elevated" in a.lower() for a in rec.suggested_actions)

    def test_evidence_populated(self) -> None:
        rec = self.analyzer.analyze({
            "total_debt_items": 12,
            "critical_debt": 0,
            "high_debt": 0,
            "debt_age_days": 5,
            "remediation_rate": 0.7,
        })
        assert any("Total debt items: 12" in e for e in rec.evidence)


# ---------------------------------------------------------------------------
# 3. TestDeploymentReadinessAnalyzer
# ---------------------------------------------------------------------------
class TestDeploymentReadinessAnalyzer:
    def setup_method(self) -> None:
        self.analyzer = DeploymentReadinessAnalyzer()

    def test_ready_for_deployment(self) -> None:
        rec = self.analyzer.analyze({
            "tests_passing": True,
            "lint_clean": True,
            "coverage_percent": 95.0,
            "security_clear": True,
            "backup_verified": True,
            "recovery_tested": True,
            "rollback_available": True,
        })
        assert rec.type == AIRecommendationType.DEPLOYMENT_READINESS
        assert rec.risk_level == "low"
        assert any("Tests: passing" in e for e in rec.evidence)
        assert any("Lint: clean" in e for e in rec.evidence)
        assert any("Coverage: 95.0%" in e for e in rec.evidence)

    def test_tests_failing(self) -> None:
        rec = self.analyzer.analyze({
            "tests_passing": False,
            "lint_clean": True,
            "coverage_percent": 95.0,
            "security_clear": True,
            "backup_verified": True,
            "recovery_tested": True,
            "rollback_available": True,
        })
        assert rec.risk_level == "high"
        assert any("Tests" in a for a in rec.suggested_actions)

    def test_multiple_blockers_critical(self) -> None:
        rec = self.analyzer.analyze({
            "tests_passing": False,
            "lint_clean": False,
            "coverage_percent": 50.0,
            "security_clear": False,
            "backup_verified": True,
            "recovery_tested": True,
            "rollback_available": True,
        })
        assert rec.risk_level == "critical"
        assert len(rec.suggested_actions) >= 3

    def test_low_coverage(self) -> None:
        rec = self.analyzer.analyze({
            "tests_passing": True,
            "lint_clean": True,
            "coverage_percent": 60.0,
            "security_clear": True,
            "backup_verified": True,
            "recovery_tested": True,
            "rollback_available": True,
        })
        assert any("Coverage" in a for a in rec.suggested_actions)

    def test_security_not_clear(self) -> None:
        rec = self.analyzer.analyze({
            "tests_passing": True,
            "lint_clean": True,
            "coverage_percent": 95.0,
            "security_clear": False,
            "backup_verified": True,
            "recovery_tested": True,
            "rollback_available": True,
        })
        assert any("Security" in a for a in rec.suggested_actions)

    def test_no_backup_no_rollback(self) -> None:
        rec = self.analyzer.analyze({
            "tests_passing": True,
            "lint_clean": True,
            "coverage_percent": 95.0,
            "security_clear": True,
            "backup_verified": False,
            "recovery_tested": True,
            "rollback_available": False,
        })
        assert rec.risk_level == "high"
        assert any("Backup" in a for a in rec.suggested_actions)
        assert any("Rollback" in a for a in rec.suggested_actions)

    def test_evidence_populated(self) -> None:
        rec = self.analyzer.analyze({
            "tests_passing": True,
            "lint_clean": True,
            "coverage_percent": 92.0,
            "security_clear": True,
            "backup_verified": True,
            "recovery_tested": True,
            "rollback_available": True,
        })
        assert any("Tests: passing" in e for e in rec.evidence)
        assert any("Lint: clean" in e for e in rec.evidence)
        assert any("Coverage: 92.0%" in e for e in rec.evidence)
