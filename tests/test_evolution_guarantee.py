"""Tests for Evolution Guarantee Engine (Phase 15)."""

from __future__ import annotations

import pytest

from unified_platform.evolution import (
    ArchitectureFitnessEngine,
    EvolutionCapability,
    EvolutionDimension,
    EvolutionGuaranteeManager,
    FitnessLevel,
    FitnessMetric,
    FutureReadinessEngine,
    TechnicalDebtEngine,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fitness_engine() -> ArchitectureFitnessEngine:
    return ArchitectureFitnessEngine()


@pytest.fixture
def debt_engine() -> TechnicalDebtEngine:
    return TechnicalDebtEngine()


@pytest.fixture
def future_engine() -> FutureReadinessEngine:
    return FutureReadinessEngine()


@pytest.fixture
def manager() -> EvolutionGuaranteeManager:
    return EvolutionGuaranteeManager()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cap(
    cap_id: str = "cap-1",
    dimension: EvolutionDimension = EvolutionDimension.HORIZONTAL_EXPANSION,
    status: str = "inactive",
) -> EvolutionCapability:
    return EvolutionCapability(
        capability_id=cap_id,
        dimension=dimension,
        description=f"Capability {cap_id}",
        status=status,
    )


# ---------------------------------------------------------------------------
# 1. TestArchitectureFitnessEngine
# ---------------------------------------------------------------------------

class TestArchitectureFitnessEngine:
    def test_assess_fitness_excellent(self, fitness_engine: ArchitectureFitnessEngine) -> None:
        metric = fitness_engine.assess_fitness(
            dimension=EvolutionDimension.HORIZONTAL_EXPANSION,
            score=95.0,
            description="Excellent scaling",
            recommendations=["Keep it up"],
        )
        assert metric.level == FitnessLevel.EXCELLENT
        assert metric.score == 95.0
        assert metric.dimension == EvolutionDimension.HORIZONTAL_EXPANSION

    def test_assess_fitness_good(self, fitness_engine: ArchitectureFitnessEngine) -> None:
        metric = fitness_engine.assess_fitness(
            dimension=EvolutionDimension.VERTICAL_EXPANSION,
            score=80.0,
            description="Good vertical scaling",
            recommendations=[],
        )
        assert metric.level == FitnessLevel.GOOD

    def test_assess_fitness_needs_improvement(self, fitness_engine: ArchitectureFitnessEngine) -> None:
        metric = fitness_engine.assess_fitness(
            dimension=EvolutionDimension.MODULE_ADDITION,
            score=60.0,
            description="Needs work",
            recommendations=["Refactor module system"],
        )
        assert metric.level == FitnessLevel.NEEDS_IMPROVEMENT

    def test_assess_fitness_poor(self, fitness_engine: ArchitectureFitnessEngine) -> None:
        metric = fitness_engine.assess_fitness(
            dimension=EvolutionDimension.NATIONAL_DEPLOYMENT,
            score=30.0,
            description="Poor readiness",
            recommendations=[],
        )
        assert metric.level == FitnessLevel.POOR

    def test_assess_fitness_critical(self, fitness_engine: ArchitectureFitnessEngine) -> None:
        metric = fitness_engine.assess_fitness(
            dimension=EvolutionDimension.AI_INTEGRATION,
            score=10.0,
            description="Critical",
            recommendations=[],
        )
        assert metric.level == FitnessLevel.CRITICAL

    def test_get_fitness(self, fitness_engine: ArchitectureFitnessEngine) -> None:
        fitness_engine.assess_fitness(
            dimension=EvolutionDimension.HORIZONTAL_EXPANSION,
            score=85.0,
            description="d",
            recommendations=[],
        )
        result = fitness_engine.get_fitness(EvolutionDimension.HORIZONTAL_EXPANSION)
        assert result is not None
        assert result.score == 85.0

    def test_get_fitness_not_assessed(self, fitness_engine: ArchitectureFitnessEngine) -> None:
        assert fitness_engine.get_fitness(EvolutionDimension.HORIZONTAL_EXPANSION) is None

    def test_list_fitness(self, fitness_engine: ArchitectureFitnessEngine) -> None:
        fitness_engine.assess_fitness(EvolutionDimension.HORIZONTAL_EXPANSION, 90, "d", [])
        fitness_engine.assess_fitness(EvolutionDimension.AI_INTEGRATION, 70, "d", [])
        metrics = fitness_engine.list_fitness()
        assert len(metrics) == 2

    def test_list_fitness_empty(self, fitness_engine: ArchitectureFitnessEngine) -> None:
        assert fitness_engine.list_fitness() == []

    def test_get_overall_fitness(self, fitness_engine: ArchitectureFitnessEngine) -> None:
        fitness_engine.assess_fitness(EvolutionDimension.HORIZONTAL_EXPANSION, 80, "d", [])
        fitness_engine.assess_fitness(EvolutionDimension.VERTICAL_EXPANSION, 60, "d", [])
        overall = fitness_engine.get_overall_fitness()
        assert overall == 70.0

    def test_get_overall_fitness_empty(self, fitness_engine: ArchitectureFitnessEngine) -> None:
        assert fitness_engine.get_overall_fitness() == 0.0

    def test_assess_fitness_overwrites_previous(self, fitness_engine: ArchitectureFitnessEngine) -> None:
        fitness_engine.assess_fitness(EvolutionDimension.HORIZONTAL_EXPANSION, 50, "old", [])
        fitness_engine.assess_fitness(EvolutionDimension.HORIZONTAL_EXPANSION, 95, "new", [])
        m = fitness_engine.get_fitness(EvolutionDimension.HORIZONTAL_EXPANSION)
        assert m is not None
        assert m.score == 95.0
        assert m.description == "new"

    def test_fitness_metric_to_dict(self, fitness_engine: ArchitectureFitnessEngine) -> None:
        metric = fitness_engine.assess_fitness(
            EvolutionDimension.HORIZONTAL_EXPANSION, 88, "desc", ["rec1"],
        )
        d = metric.to_dict()
        assert d["metric_name"] == "horizontal_expansion_fitness"
        assert d["dimension"] == "horizontal_expansion"
        assert d["level"] == "good"
        assert d["score"] == 88
        assert d["recommendations"] == ["rec1"]
        assert "timestamp" in d


# ---------------------------------------------------------------------------
# 2. TestTechnicalDebtEngine
# ---------------------------------------------------------------------------

class TestTechnicalDebtEngine:
    def test_register_debt(self, debt_engine: TechnicalDebtEngine) -> None:
        debt_engine.register_debt("d-1", "Legacy auth", "high", "auth")
        debts = debt_engine.list_debts()
        assert len(debts) == 1
        assert debts[0].debt_id == "d-1"
        assert debts[0].resolved is False

    def test_resolve_debt(self, debt_engine: TechnicalDebtEngine) -> None:
        debt_engine.register_debt("d-1", "Legacy auth", "high", "auth")
        ok = debt_engine.resolve_debt("d-1")
        assert ok is True
        debt = debt_engine.list_debts()[0]
        assert debt.resolved is True
        assert debt.resolved_at is not None

    def test_resolve_debt_not_found(self, debt_engine: TechnicalDebtEngine) -> None:
        assert debt_engine.resolve_debt("nope") is False

    def test_resolve_debt_already_resolved(self, debt_engine: TechnicalDebtEngine) -> None:
        debt_engine.register_debt("d-1", "desc", "low", "comp")
        debt_engine.resolve_debt("d-1")
        assert debt_engine.resolve_debt("d-1") is False

    def test_list_debts_all(self, debt_engine: TechnicalDebtEngine) -> None:
        debt_engine.register_debt("d-1", "a", "high", "comp")
        debt_engine.register_debt("d-2", "b", "low", "comp")
        assert len(debt_engine.list_debts()) == 2

    def test_list_debts_by_severity(self, debt_engine: TechnicalDebtEngine) -> None:
        debt_engine.register_debt("d-1", "a", "high", "comp")
        debt_engine.register_debt("d-2", "b", "low", "comp")
        debt_engine.register_debt("d-3", "c", "high", "comp")
        high = debt_engine.list_debts(severity="high")
        assert len(high) == 2
        low = debt_engine.list_debts(severity="low")
        assert len(low) == 1

    def test_list_debts_empty(self, debt_engine: TechnicalDebtEngine) -> None:
        assert debt_engine.list_debts() == []

    def test_get_debt_summary_empty(self, debt_engine: TechnicalDebtEngine) -> None:
        summary = debt_engine.get_debt_summary()
        assert summary["total"] == 0
        assert summary["resolved"] == 0
        assert summary["unresolved"] == 0

    def test_get_debt_summary_with_debts(self, debt_engine: TechnicalDebtEngine) -> None:
        debt_engine.register_debt("d-1", "a", "high", "comp")
        debt_engine.register_debt("d-2", "b", "low", "comp")
        debt_engine.register_debt("d-3", "c", "high", "comp")
        debt_engine.resolve_debt("d-1")
        summary = debt_engine.get_debt_summary()
        assert summary["total"] == 3
        assert summary["resolved"] == 1
        assert summary["unresolved"] == 2
        assert summary["by_severity"]["high"] == 2
        assert summary["by_severity"]["low"] == 1


# ---------------------------------------------------------------------------
# 3. TestFutureReadinessEngine
# ---------------------------------------------------------------------------

class TestFutureReadinessEngine:
    def test_register_capability(self, future_engine: FutureReadinessEngine) -> None:
        cap = _cap("cap-1", status="active")
        future_engine.register_capability(cap)
        result = future_engine.get_capability("cap-1")
        assert result is cap

    def test_get_capability_not_found(self, future_engine: FutureReadinessEngine) -> None:
        assert future_engine.get_capability("nope") is None

    def test_list_capabilities_all(self, future_engine: FutureReadinessEngine) -> None:
        future_engine.register_capability(_cap("c1"))
        future_engine.register_capability(_cap("c2", dimension=EvolutionDimension.AI_INTEGRATION))
        caps = future_engine.list_capabilities()
        assert len(caps) == 2

    def test_list_capabilities_by_dimension(self, future_engine: FutureReadinessEngine) -> None:
        future_engine.register_capability(_cap("c1", dimension=EvolutionDimension.HORIZONTAL_EXPANSION))
        future_engine.register_capability(_cap("c2", dimension=EvolutionDimension.AI_INTEGRATION))
        ai = future_engine.list_capabilities(dimension=EvolutionDimension.AI_INTEGRATION)
        assert len(ai) == 1
        assert ai[0].capability_id == "c2"

    def test_list_capabilities_empty(self, future_engine: FutureReadinessEngine) -> None:
        assert future_engine.list_capabilities() == []

    def test_get_readiness_score_all_active(self, future_engine: FutureReadinessEngine) -> None:
        future_engine.register_capability(_cap("c1", status="active"))
        future_engine.register_capability(_cap("c2", status="active"))
        assert future_engine.get_readiness_score() == 100.0

    def test_get_readiness_score_none_active(self, future_engine: FutureReadinessEngine) -> None:
        future_engine.register_capability(_cap("c1", status="inactive"))
        assert future_engine.get_readiness_score() == 0.0

    def test_get_readiness_score_partial(self, future_engine: FutureReadinessEngine) -> None:
        future_engine.register_capability(_cap("c1", status="active"))
        future_engine.register_capability(_cap("c2", status="inactive"))
        future_engine.register_capability(_cap("c3", status="inactive"))
        assert future_engine.get_readiness_score() == pytest.approx(33.333333333)

    def test_get_readiness_score_empty(self, future_engine: FutureReadinessEngine) -> None:
        assert future_engine.get_readiness_score() == 0.0

    def test_capability_to_dict(self) -> None:
        cap = _cap("cap-d", status="active")
        d = cap.to_dict()
        assert d["capability_id"] == "cap-d"
        assert d["status"] == "active"
        assert d["dimension"] == "horizontal_expansion"
        assert "created_at" in d

    def test_fitness_metric_to_dict(self) -> None:
        m = FitnessMetric(
            metric_name="test_metric",
            dimension=EvolutionDimension.AI_INTEGRATION,
            level=FitnessLevel.GOOD,
            score=82.0,
            description="Test",
            recommendations=["rec1"],
        )
        d = m.to_dict()
        assert d["metric_name"] == "test_metric"
        assert d["level"] == "good"
        assert d["recommendations"] == ["rec1"]


# ---------------------------------------------------------------------------
# 4. TestEvolutionGuaranteeManager
# ---------------------------------------------------------------------------

class TestEvolutionGuaranteeManager:
    def test_get_evolution_report_empty(self, manager: EvolutionGuaranteeManager) -> None:
        report = manager.get_evolution_report()
        assert report["overall_fitness"] == 0.0
        assert report["debt_summary"]["total"] == 0
        assert report["readiness_score"] == 0.0
        assert isinstance(report["recommendations"], list)

    def test_get_evolution_report_recommendations_low_fitness(
        self, manager: EvolutionGuaranteeManager,
    ) -> None:
        manager.fitness.assess_fitness(
            EvolutionDimension.HORIZONTAL_EXPANSION, 50, "d", [],
        )
        report = manager.get_evolution_report()
        assert any("fitness" in r.lower() for r in report["recommendations"])

    def test_get_evolution_report_recommendations_high_debt(
        self, manager: EvolutionGuaranteeManager,
    ) -> None:
        for i in range(15):
            manager.debt.register_debt(f"d{i}", f"desc{i}", "high", "comp")
        report = manager.get_evolution_report()
        assert any("debt" in r.lower() for r in report["recommendations"])

    def test_get_evolution_report_recommendations_low_readiness(
        self, manager: EvolutionGuaranteeManager,
    ) -> None:
        for i in range(3):
            manager.future.register_capability(_cap(f"c{i}", status="inactive"))
        report = manager.get_evolution_report()
        assert any("readiness" in r.lower() for r in report["recommendations"])

    def test_get_evolution_report_no_recommendations(
        self, manager: EvolutionGuaranteeManager,
    ) -> None:
        manager.fitness.assess_fitness(
            EvolutionDimension.HORIZONTAL_EXPANSION, 95, "d", [],
        )
        for i in range(5):
            manager.future.register_capability(_cap(f"c{i}", status="active"))
        report = manager.get_evolution_report()
        assert report["recommendations"] == []

    def test_manager_composes_all_engines(
        self, manager: EvolutionGuaranteeManager,
    ) -> None:
        assert isinstance(manager.fitness, ArchitectureFitnessEngine)
        assert isinstance(manager.debt, TechnicalDebtEngine)
        assert isinstance(manager.future, FutureReadinessEngine)

    def test_integration_full_lifecycle(self, manager: EvolutionGuaranteeManager) -> None:
        manager.fitness.assess_fitness(EvolutionDimension.HORIZONTAL_EXPANSION, 88, "scaling ok", [])
        manager.fitness.assess_fitness(EvolutionDimension.AI_INTEGRATION, 72, "needs work", ["Improve ML pipeline"])

        manager.debt.register_debt("td-1", "Old ORM", "medium", "database")
        manager.debt.resolve_debt("td-1")

        manager.future.register_capability(_cap("fc-1", EvolutionDimension.HORIZONTAL_EXPANSION, "active"))
        manager.future.register_capability(_cap("fc-2", EvolutionDimension.AI_INTEGRATION, "inactive"))

        report = manager.get_evolution_report()
        assert report["overall_fitness"] == 80.0
        assert report["debt_summary"]["resolved"] == 1
        assert report["readiness_score"] == 50.0
