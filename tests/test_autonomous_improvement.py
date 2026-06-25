"""
Tests for Autonomous Improvement Engine — Phase 8
"""

from __future__ import annotations

from unified_platform.intelligence.advanced_improvement import (
    AutonomousImprovementEngine,
    ImprovementCategory,
    ImprovementPriority,
    ImprovementRecommendation,
)


class TestArchitectureRecommender:
    def setup_method(self) -> None:
        self.engine = AutonomousImprovementEngine()

    def test_high_coupling(self) -> None:
        recs = self.engine.architecture.analyze({"coupling_score": 85})
        assert len(recs) == 1
        assert recs[0].category == ImprovementCategory.ARCHITECTURE
        assert recs[0].priority == ImprovementPriority.HIGH
        assert "coupling" in recs[0].title.lower()

    def test_low_cohesion(self) -> None:
        recs = self.engine.architecture.analyze({"cohesion_score": 25})
        assert len(recs) == 1
        assert recs[0].category == ImprovementCategory.ARCHITECTURE

    def test_deep_dependency_chain(self) -> None:
        recs = self.engine.architecture.analyze({"dependency_depth": 15})
        assert len(recs) == 1
        assert recs[0].priority == ImprovementPriority.MEDIUM

    def test_clean_architecture(self) -> None:
        recs = self.engine.architecture.analyze({
            "coupling_score": 30,
            "cohesion_score": 80,
            "dependency_depth": 5,
            "module_count": 10,
            "interface_complexity": 50,
        })
        assert len(recs) == 0


class TestPerformanceRecommender:
    def setup_method(self) -> None:
        self.engine = AutonomousImprovementEngine()

    def test_n_plus_one_queries(self) -> None:
        recs = self.engine.performance.analyze({"query_patterns": {"n_plus_one_count": 10}})
        assert len(recs) == 1
        assert recs[0].category == ImprovementCategory.PERFORMANCE
        assert recs[0].priority == ImprovementPriority.HIGH

    def test_low_cache_efficiency(self) -> None:
        recs = self.engine.performance.analyze({"cache_efficiency": 0.4})
        assert len(recs) == 1
        assert recs[0].priority == ImprovementPriority.MEDIUM

    def test_connection_pool_exhaustion(self) -> None:
        recs = self.engine.performance.analyze({"connection_pool_usage": 90})
        assert len(recs) == 1
        assert recs[0].priority == ImprovementPriority.HIGH

    def test_high_memory_pressure(self) -> None:
        recs = self.engine.performance.analyze({"memory_pressure": 85})
        assert len(recs) == 1
        assert recs[0].category == ImprovementCategory.PERFORMANCE

    def test_slow_io_operations(self) -> None:
        recs = self.engine.performance.analyze({"io_patterns": {"slow_operations": 20}})
        assert len(recs) == 1


class TestSecurityRecommender:
    def setup_method(self) -> None:
        self.engine = AutonomousImprovementEngine()

    def test_weak_auth(self) -> None:
        recs = self.engine.security.analyze({"auth_strength": 30})
        assert len(recs) == 1
        assert recs[0].priority == ImprovementPriority.CRITICAL

    def test_low_encryption(self) -> None:
        recs = self.engine.security.analyze({"encryption_coverage": 50})
        assert len(recs) == 1
        assert recs[0].priority == ImprovementPriority.HIGH

    def test_aging_vulnerabilities(self) -> None:
        recs = self.engine.security.analyze({"vulnerability_age_days": 60})
        assert len(recs) == 1
        assert recs[0].priority == ImprovementPriority.CRITICAL

    def test_clean_security(self) -> None:
        recs = self.engine.security.analyze({
            "auth_strength": 95,
            "encryption_coverage": 100,
            "audit_compliance": 100,
            "vulnerability_age_days": 5,
            "access_control_score": 90,
        })
        assert len(recs) == 0


class TestRefactoringRecommender:
    def setup_method(self) -> None:
        self.engine = AutonomousImprovementEngine()

    def test_high_duplication(self) -> None:
        recs = self.engine.refactoring.analyze({"code_duplication_percent": 25})
        assert len(recs) == 1
        assert recs[0].category == ImprovementCategory.REFACTORING

    def test_oversized_functions(self) -> None:
        recs = self.engine.refactoring.analyze({"max_function_length": 150})
        assert len(recs) == 1

    def test_low_test_coverage(self) -> None:
        recs = self.engine.refactoring.analyze({"test_coverage": 50})
        assert len(recs) == 1
        assert recs[0].priority == ImprovementPriority.CRITICAL

    def test_high_complexity(self) -> None:
        recs = self.engine.refactoring.analyze({"cyclomatic_complexity": 40})
        assert len(recs) == 1
        assert recs[0].priority == ImprovementPriority.HIGH


class TestDebtReductionPlanner:
    def setup_method(self) -> None:
        self.engine = AutonomousImprovementEngine()

    def test_high_debt_volume(self) -> None:
        recs = self.engine.debt.analyze({"debt_items": 100})
        assert len(recs) == 1
        assert recs[0].category == ImprovementCategory.DEBT_REDUCTION

    def test_aging_debt(self) -> None:
        recs = self.engine.debt.analyze({"debt_age_days": 300})
        assert len(recs) == 1
        assert recs[0].priority == ImprovementPriority.CRITICAL

    def test_low_remediation(self) -> None:
        recs = self.engine.debt.analyze({"remediation_rate": 0.1})
        assert len(recs) == 1

    def test_clean_debt(self) -> None:
        recs = self.engine.debt.analyze({
            "debt_items": 10,
            "debt_age_days": 30,
            "remediation_rate": 0.8,
            "business_impact_score": 20,
            "technical_risk_score": 15,
        })
        assert len(recs) == 0


class TestAutonomousImprovementEngine:
    def setup_method(self) -> None:
        self.engine = AutonomousImprovementEngine()

    def test_generate_all_recommendations(self) -> None:
        metrics = {
            "coupling_score": 80,
            "query_patterns": {"n_plus_one_count": 8},
            "auth_strength": 40,
            "test_coverage": 50,
            "debt_items": 75,
        }
        recs = self.engine.generate_all_recommendations(metrics)
        assert len(recs) >= 5

    def test_prioritize_recommendations(self) -> None:
        recs = [
            ImprovementRecommendation(
                rec_id="low", category=ImprovementCategory.ARCHITECTURE,
                priority=ImprovementPriority.LOW, title="Low", description="",
                impact_score=3.0, effort_score=2.0,
            ),
            ImprovementRecommendation(
                rec_id="crit", category=ImprovementCategory.SECURITY,
                priority=ImprovementPriority.CRITICAL, title="Crit", description="",
                impact_score=9.0, effort_score=5.0,
            ),
        ]
        prioritized = self.engine.prioritize_recommendations(recs)
        assert prioritized[0].rec_id == "crit"
        assert prioritized[1].rec_id == "low"

    def test_improvement_plan(self) -> None:
        plan = self.engine.get_improvement_plan({
            "coupling_score": 80,
            "auth_strength": 40,
        })
        assert "total_recommendations" in plan
        assert "by_category" in plan
        assert "recommendations" in plan
        assert plan["total_recommendations"] >= 2

    def test_history_accumulates(self) -> None:
        self.engine.generate_all_recommendations({"coupling_score": 80})
        self.engine.generate_all_recommendations({"auth_strength": 40})
        history = self.engine.get_improvement_history()
        assert len(history) == 2

    def test_empty_metrics(self) -> None:
        recs = self.engine.generate_all_recommendations({})
        assert recs == []
