"""
Platform Evolution — Evolution Guarantee Engine

Phase 15: Evolution Guarantee
Constitution: Principle 24 (Continuous Architecture Evolution), Principle 10 (Long-Term Vision)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EvolutionDimension(Enum):
    """Dimensions of platform evolution."""
    HORIZONTAL_EXPANSION = "horizontal_expansion"
    VERTICAL_EXPANSION = "vertical_expansion"
    MODULE_ADDITION = "module_addition"
    NATIONAL_DEPLOYMENT = "national_deployment"
    AI_INTEGRATION = "ai_integration"


class FitnessLevel(Enum):
    """Architecture fitness levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"
    CRITICAL = "critical"


def _fitness_level_from_score(score: float) -> FitnessLevel:
    """Convert numeric score to fitness level."""
    if score >= 90:
        return FitnessLevel.EXCELLENT
    elif score >= 75:
        return FitnessLevel.GOOD
    elif score >= 50:
        return FitnessLevel.NEEDS_IMPROVEMENT
    elif score >= 25:
        return FitnessLevel.POOR
    return FitnessLevel.CRITICAL


@dataclass
class FitnessMetric:
    """An architecture fitness metric."""
    metric_name: str
    dimension: EvolutionDimension
    level: FitnessLevel
    score: float
    description: str
    recommendations: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "dimension": self.dimension.value,
            "level": self.level.value,
            "score": self.score,
            "description": self.description,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class EvolutionCapability:
    """A capability for platform evolution."""
    capability_id: str
    dimension: EvolutionDimension
    description: str
    status: str = "inactive"
    fitness_level: FitnessLevel = FitnessLevel.NEEDS_IMPROVEMENT
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "dimension": self.dimension.value,
            "description": self.description,
            "status": self.status,
            "fitness_level": self.fitness_level.value,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class TechnicalDebt:
    """A technical debt item."""
    debt_id: str
    description: str
    severity: str
    component: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None
    resolved: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "debt_id": self.debt_id,
            "description": self.description,
            "severity": self.severity,
            "component": self.component,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved": self.resolved,
        }


class ArchitectureFitnessEngine:
    """Engine for assessing architecture fitness across evolution dimensions."""

    def __init__(self) -> None:
        self._metrics: dict[EvolutionDimension, FitnessMetric] = {}

    def assess_fitness(
        self,
        dimension: EvolutionDimension,
        score: float,
        description: str,
        recommendations: list[str],
    ) -> FitnessMetric:
        """Assess fitness for a specific dimension."""
        level = _fitness_level_from_score(score)
        metric = FitnessMetric(
            metric_name=f"{dimension.value}_fitness",
            dimension=dimension,
            level=level,
            score=score,
            description=description,
            recommendations=recommendations,
        )
        self._metrics[dimension] = metric
        return metric

    def get_fitness(self, dimension: EvolutionDimension) -> FitnessMetric | None:
        """Get fitness metric for a specific dimension."""
        return self._metrics.get(dimension)

    def list_fitness(self) -> list[FitnessMetric]:
        """List all fitness metrics."""
        return list(self._metrics.values())

    def get_overall_fitness(self) -> float:
        """Get average fitness score across all dimensions."""
        if not self._metrics:
            return 0.0
        total = sum(m.score for m in self._metrics.values())
        return total / len(self._metrics)


class TechnicalDebtEngine:
    """Engine for tracking and managing technical debt."""

    def __init__(self) -> None:
        self._debts: dict[str, TechnicalDebt] = {}

    def register_debt(
        self,
        debt_id: str,
        description: str,
        severity: str,
        component: str,
    ) -> None:
        """Register a new technical debt item."""
        debt = TechnicalDebt(
            debt_id=debt_id,
            description=description,
            severity=severity,
            component=component,
        )
        self._debts[debt_id] = debt

    def resolve_debt(self, debt_id: str) -> bool:
        """Mark a debt item as resolved."""
        debt = self._debts.get(debt_id)
        if not debt:
            return False
        if debt.resolved:
            return False
        debt.resolved = True
        debt.resolved_at = datetime.utcnow()
        return True

    def list_debts(self, severity: str | None = None) -> list[TechnicalDebt]:
        """List all debts, optionally filtered by severity."""
        debts = list(self._debts.values())
        if severity:
            debts = [d for d in debts if d.severity == severity]
        return debts

    def get_debt_summary(self) -> dict[str, Any]:
        """Get summary of technical debt."""
        debts = list(self._debts.values())
        total = len(debts)
        resolved = sum(1 for d in debts if d.resolved)
        by_severity: dict[str, int] = {}
        for debt in debts:
            by_severity[debt.severity] = by_severity.get(debt.severity, 0) + 1

        return {
            "total": total,
            "resolved": resolved,
            "unresolved": total - resolved,
            "by_severity": by_severity,
        }


class FutureReadinessEngine:
    """Engine for tracking future readiness capabilities."""

    def __init__(self) -> None:
        self._capabilities: dict[str, EvolutionCapability] = {}

    def register_capability(self, cap: EvolutionCapability) -> None:
        """Register a new capability."""
        self._capabilities[cap.capability_id] = cap

    def get_capability(self, capability_id: str) -> EvolutionCapability | None:
        """Get a capability by ID."""
        return self._capabilities.get(capability_id)

    def list_capabilities(
        self,
        dimension: EvolutionDimension | None = None,
    ) -> list[EvolutionCapability]:
        """List all capabilities, optionally filtered by dimension."""
        caps = list(self._capabilities.values())
        if dimension:
            caps = [c for c in caps if c.dimension == dimension]
        return caps

    def get_readiness_score(self) -> float:
        """Get readiness score as percentage of ACTIVE capabilities."""
        if not self._capabilities:
            return 0.0
        active_count = sum(
            1 for c in self._capabilities.values() if c.status == "active"
        )
        return (active_count / len(self._capabilities)) * 100.0


class EvolutionGuaranteeManager:
    """Central manager for evolution guarantee operations."""

    def __init__(self) -> None:
        self.fitness = ArchitectureFitnessEngine()
        self.debt = TechnicalDebtEngine()
        self.future = FutureReadinessEngine()

    def get_evolution_report(self) -> dict[str, Any]:
        """Generate comprehensive evolution report."""
        overall_fitness = self.fitness.get_overall_fitness()
        debt_summary = self.debt.get_debt_summary()
        readiness_score = self.future.get_readiness_score()

        recommendations: list[str] = []
        if overall_fitness < 75:
            recommendations.append("Architecture fitness below target: review dimensions")
        if debt_summary["unresolved"] > 10:
            recommendations.append("High unresolved debt: prioritize remediation")
        if readiness_score < 50:
            recommendations.append("Low future readiness: activate more capabilities")

        return {
            "overall_fitness": overall_fitness,
            "debt_summary": debt_summary,
            "readiness_score": readiness_score,
            "recommendations": recommendations,
        }


__all__ = [
    "EvolutionDimension",
    "FitnessLevel",
    "FitnessMetric",
    "EvolutionCapability",
    "ArchitectureFitnessEngine",
    "TechnicalDebtEngine",
    "FutureReadinessEngine",
    "EvolutionGuaranteeManager",
]
