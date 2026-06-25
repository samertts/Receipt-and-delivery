"""
Platform Intelligence — Autonomous Improvement Engine

Phase 8: Autonomous Improvement Engine
Constitution: Principle 41 (Continuous Self Assessment), Principle 42 (Improvement Engine)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ImprovementPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ImprovementCategory(Enum):
    ARCHITECTURE = "architecture"
    PERFORMANCE = "performance"
    SECURITY = "security"
    REFACTORING = "refactoring"
    DEBT_REDUCTION = "debt_reduction"


_PRIORITY_RANK: dict[ImprovementPriority, int] = {
    ImprovementPriority.CRITICAL: 4,
    ImprovementPriority.HIGH: 3,
    ImprovementPriority.MEDIUM: 2,
    ImprovementPriority.LOW: 1,
}


@dataclass
class ImprovementRecommendation:
    rec_id: str
    category: ImprovementCategory
    priority: ImprovementPriority
    title: str
    description: str
    impact_score: float
    effort_score: float
    evidence: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


class ArchitectureRecommender:
    def analyze(self, metrics: dict[str, Any]) -> list[ImprovementRecommendation]:
        recommendations: list[ImprovementRecommendation] = []
        coupling = metrics.get("coupling_score", 0)
        cohesion = metrics.get("cohesion_score", 100)
        dependency_depth = metrics.get("dependency_depth", 0)
        module_count = metrics.get("module_count", 0)
        interface_complexity = metrics.get("interface_complexity", 0)

        if coupling > 70:
            recommendations.append(ImprovementRecommendation(
                rec_id="ARCH-001",
                category=ImprovementCategory.ARCHITECTURE,
                priority=ImprovementPriority.HIGH,
                title="High coupling detected",
                description=f"Coupling score of {coupling} exceeds threshold of 70.",
                impact_score=8.0,
                effort_score=6.0,
                evidence=[f"Coupling score: {coupling}"],
                action_items=["Decouple modules via interfaces", "Introduce mediator pattern"],
            ))

        if cohesion < 40:
            recommendations.append(ImprovementRecommendation(
                rec_id="ARCH-002",
                category=ImprovementCategory.ARCHITECTURE,
                priority=ImprovementPriority.HIGH,
                title="Low cohesion detected",
                description=f"Cohesion score of {cohesion} below threshold of 40.",
                impact_score=7.5,
                effort_score=5.0,
                evidence=[f"Cohesion score: {cohesion}"],
                action_items=["Group related responsibilities", "Split god classes"],
            ))

        if dependency_depth > 10:
            recommendations.append(ImprovementRecommendation(
                rec_id="ARCH-003",
                category=ImprovementCategory.ARCHITECTURE,
                priority=ImprovementPriority.MEDIUM,
                title="Deep dependency chain",
                description=f"Dependency depth of {dependency_depth} exceeds threshold of 10.",
                impact_score=6.0,
                effort_score=7.0,
                evidence=[f"Dependency depth: {dependency_depth}"],
                action_items=["Flatten dependency graph", "Use dependency inversion"],
            ))

        if module_count > 0 and interface_complexity / module_count > 15:
            recommendations.append(ImprovementRecommendation(
                rec_id="ARCH-004",
                category=ImprovementCategory.ARCHITECTURE,
                priority=ImprovementPriority.MEDIUM,
                title="High interface complexity per module",
                description=f"Average interface complexity {interface_complexity / module_count:.1f} exceeds 15.",
                impact_score=5.0,
                effort_score=4.0,
                evidence=[f"Interface complexity: {interface_complexity}", f"Modules: {module_count}"],
                action_items=["Simplify module interfaces", "Apply interface segregation"],
            ))

        return recommendations


class PerformanceRecommenderV2:
    def analyze(self, metrics: dict[str, Any]) -> list[ImprovementRecommendation]:
        recommendations: list[ImprovementRecommendation] = []
        query_patterns = metrics.get("query_patterns", {})
        cache_efficiency = metrics.get("cache_efficiency", 1.0)
        connection_pool = metrics.get("connection_pool_usage", 0)
        memory_pressure = metrics.get("memory_pressure", 0)
        io_patterns = metrics.get("io_patterns", {})

        n_plus_one = query_patterns.get("n_plus_one_count", 0)
        if n_plus_one > 5:
            recommendations.append(ImprovementRecommendation(
                rec_id="PERF-001",
                category=ImprovementCategory.PERFORMANCE,
                priority=ImprovementPriority.HIGH,
                title="N+1 query patterns detected",
                description=f"Found {n_plus_one} N+1 query patterns.",
                impact_score=8.5,
                effort_score=4.0,
                evidence=[f"N+1 queries: {n_plus_one}"],
                action_items=["Use eager loading", "Implement batch queries"],
            ))

        if cache_efficiency < 0.6:
            recommendations.append(ImprovementRecommendation(
                rec_id="PERF-002",
                category=ImprovementCategory.PERFORMANCE,
                priority=ImprovementPriority.MEDIUM,
                title="Low cache efficiency",
                description=f"Cache efficiency at {cache_efficiency * 100:.1f}% below 60% threshold.",
                impact_score=6.0,
                effort_score=3.0,
                evidence=[f"Cache efficiency: {cache_efficiency * 100:.1f}%"],
                action_items=["Review cache strategy", "Increase cache TTL"],
            ))

        if connection_pool > 85:
            recommendations.append(ImprovementRecommendation(
                rec_id="PERF-003",
                category=ImprovementCategory.PERFORMANCE,
                priority=ImprovementPriority.HIGH,
                title="Connection pool near exhaustion",
                description=f"Connection pool usage at {connection_pool}%.",
                impact_score=9.0,
                effort_score=5.0,
                evidence=[f"Pool usage: {connection_pool}%"],
                action_items=["Increase pool size", "Add connection pooling optimization"],
            ))

        if memory_pressure > 75:
            recommendations.append(ImprovementRecommendation(
                rec_id="PERF-004",
                category=ImprovementCategory.PERFORMANCE,
                priority=ImprovementPriority.HIGH,
                title="High memory pressure",
                description=f"Memory pressure at {memory_pressure}%.",
                impact_score=8.0,
                effort_score=6.0,
                evidence=[f"Memory pressure: {memory_pressure}%"],
                action_items=["Profile memory usage", "Optimize data structures"],
            ))

        slow_io = io_patterns.get("slow_operations", 0)
        if slow_io > 10:
            recommendations.append(ImprovementRecommendation(
                rec_id="PERF-005",
                category=ImprovementCategory.PERFORMANCE,
                priority=ImprovementPriority.MEDIUM,
                title="Multiple slow I/O operations",
                description=f"Found {slow_io} slow I/O operations.",
                impact_score=6.5,
                effort_score=5.0,
                evidence=[f"Slow I/O: {slow_io}"],
                action_items=["Use async I/O", "Batch I/O operations"],
            ))

        return recommendations


class SecurityRecommenderV2:
    def analyze(self, metrics: dict[str, Any]) -> list[ImprovementRecommendation]:
        recommendations: list[ImprovementRecommendation] = []
        auth_strength = metrics.get("auth_strength", 100)
        encryption_coverage = metrics.get("encryption_coverage", 100)
        audit_compliance = metrics.get("audit_compliance", 100)
        vulnerability_age = metrics.get("vulnerability_age_days", 0)
        access_control = metrics.get("access_control_score", 100)

        if auth_strength < 60:
            recommendations.append(ImprovementRecommendation(
                rec_id="SEC-001",
                category=ImprovementCategory.SECURITY,
                priority=ImprovementPriority.CRITICAL,
                title="Weak authentication strength",
                description=f"Auth strength score at {auth_strength} (threshold: 60).",
                impact_score=9.5,
                effort_score=5.0,
                evidence=[f"Auth strength: {auth_strength}"],
                action_items=["Enforce MFA", "Strengthen password policy"],
            ))

        if encryption_coverage < 80:
            recommendations.append(ImprovementRecommendation(
                rec_id="SEC-002",
                category=ImprovementCategory.SECURITY,
                priority=ImprovementPriority.HIGH,
                title="Insufficient encryption coverage",
                description=f"Encryption coverage at {encryption_coverage}% (target: 80%).",
                impact_score=8.5,
                effort_score=4.0,
                evidence=[f"Encryption: {encryption_coverage}%"],
                action_items=["Encrypt data at rest", "Enable TLS everywhere"],
            ))

        if audit_compliance < 90:
            recommendations.append(ImprovementRecommendation(
                rec_id="SEC-003",
                category=ImprovementCategory.SECURITY,
                priority=ImprovementPriority.HIGH,
                title="Audit compliance below threshold",
                description=f"Audit compliance at {audit_compliance}% (target: 90%).",
                impact_score=8.0,
                effort_score=3.0,
                evidence=[f"Audit compliance: {audit_compliance}%"],
                action_items=["Enable comprehensive audit logging", "Review audit policies"],
            ))

        if vulnerability_age > 30:
            recommendations.append(ImprovementRecommendation(
                rec_id="SEC-004",
                category=ImprovementCategory.SECURITY,
                priority=ImprovementPriority.CRITICAL,
                title="Unpatched vulnerabilities aging",
                description=f"Oldest vulnerability is {vulnerability_age} days old.",
                impact_score=9.0,
                effort_score=6.0,
                evidence=[f"Vulnerability age: {vulnerability_age} days"],
                action_items=["Apply security patches immediately", "Establish patch cadence"],
            ))

        if access_control < 70:
            recommendations.append(ImprovementRecommendation(
                rec_id="SEC-005",
                category=ImprovementCategory.SECURITY,
                priority=ImprovementPriority.HIGH,
                title="Weak access control",
                description=f"Access control score at {access_control} (threshold: 70).",
                impact_score=8.0,
                effort_score=5.0,
                evidence=[f"Access control: {access_control}"],
                action_items=["Implement RBAC", "Review permissions model"],
            ))

        return recommendations


class RefactoringRecommender:
    def analyze(self, metrics: dict[str, Any]) -> list[ImprovementRecommendation]:
        recommendations: list[ImprovementRecommendation] = []
        code_duplication = metrics.get("code_duplication_percent", 0)
        function_length = metrics.get("max_function_length", 0)
        class_cohesion = metrics.get("class_cohesion", 100)
        test_coverage = metrics.get("test_coverage", 100)
        complexity = metrics.get("cyclomatic_complexity", 0)

        if code_duplication > 15:
            recommendations.append(ImprovementRecommendation(
                rec_id="REF-001",
                category=ImprovementCategory.REFACTORING,
                priority=ImprovementPriority.MEDIUM,
                title="High code duplication",
                description=f"Code duplication at {code_duplication}% exceeds 15% threshold.",
                impact_score=6.0,
                effort_score=4.0,
                evidence=[f"Duplication: {code_duplication}%"],
                action_items=["Extract common logic", "Create shared utilities"],
            ))

        if function_length > 80:
            recommendations.append(ImprovementRecommendation(
                rec_id="REF-002",
                category=ImprovementCategory.REFACTORING,
                priority=ImprovementPriority.MEDIUM,
                title="Oversized functions detected",
                description=f"Longest function is {function_length} lines (threshold: 80).",
                impact_score=5.5,
                effort_score=3.0,
                evidence=[f"Max function length: {function_length}"],
                action_items=["Split into smaller functions", "Extract helper methods"],
            ))

        if class_cohesion < 50:
            recommendations.append(ImprovementRecommendation(
                rec_id="REF-003",
                category=ImprovementCategory.REFACTORING,
                priority=ImprovementPriority.HIGH,
                title="Low class cohesion",
                description=f"Class cohesion at {class_cohesion}% below 50% threshold.",
                impact_score=7.0,
                effort_score=5.0,
                evidence=[f"Class cohesion: {class_cohesion}%"],
                action_items=["Split multi-purpose classes", "Apply single responsibility"],
            ))

        if test_coverage < 80:
            priority = ImprovementPriority.CRITICAL if test_coverage < 60 else ImprovementPriority.HIGH
            recommendations.append(ImprovementRecommendation(
                rec_id="REF-004",
                category=ImprovementCategory.REFACTORING,
                priority=priority,
                title="Low test coverage",
                description=f"Test coverage at {test_coverage}% (target: 80%).",
                impact_score=8.0,
                effort_score=6.0,
                evidence=[f"Test coverage: {test_coverage}%"],
                action_items=["Add unit tests", "Add integration tests"],
            ))

        if complexity > 25:
            recommendations.append(ImprovementRecommendation(
                rec_id="REF-005",
                category=ImprovementCategory.REFACTORING,
                priority=ImprovementPriority.HIGH,
                title="High cyclomatic complexity",
                description=f"Cyclomatic complexity at {complexity} exceeds threshold of 25.",
                impact_score=7.5,
                effort_score=4.0,
                evidence=[f"Complexity: {complexity}"],
                action_items=["Simplify control flow", "Extract complex logic into services"],
            ))

        return recommendations


class DebtReductionPlanner:
    def analyze(self, metrics: dict[str, Any]) -> list[ImprovementRecommendation]:
        recommendations: list[ImprovementRecommendation] = []
        debt_items = metrics.get("debt_items", 0)
        debt_age = metrics.get("debt_age_days", 0)
        remediation_rate = metrics.get("remediation_rate", 1.0)
        business_impact = metrics.get("business_impact_score", 0)
        technical_risk = metrics.get("technical_risk_score", 0)

        if debt_items > 50:
            recommendations.append(ImprovementRecommendation(
                rec_id="DEBT-001",
                category=ImprovementCategory.DEBT_REDUCTION,
                priority=ImprovementPriority.HIGH,
                title="High volume of debt items",
                description=f"Found {debt_items} debt items exceeding threshold of 50.",
                impact_score=7.0,
                effort_score=8.0,
                evidence=[f"Debt items: {debt_items}"],
                action_items=["Prioritize debt by impact", "Allocate sprint capacity"],
            ))

        if debt_age > 180:
            recommendations.append(ImprovementRecommendation(
                rec_id="DEBT-002",
                category=ImprovementCategory.DEBT_REDUCTION,
                priority=ImprovementPriority.CRITICAL,
                title="Aging technical debt",
                description=f"Debt age of {debt_age} days exceeds 180-day threshold.",
                impact_score=8.5,
                effort_score=7.0,
                evidence=[f"Debt age: {debt_age} days"],
                action_items=["Create debt remediation plan", "Schedule dedicated sprints"],
            ))

        if remediation_rate < 0.3:
            recommendations.append(ImprovementRecommendation(
                rec_id="DEBT-003",
                category=ImprovementCategory.DEBT_REDUCTION,
                priority=ImprovementPriority.MEDIUM,
                title="Low remediation rate",
                description=f"Remediation rate at {remediation_rate * 100:.1f}% below 30% threshold.",
                impact_score=5.0,
                effort_score=3.0,
                evidence=[f"Remediation rate: {remediation_rate * 100:.1f}%"],
                action_items=["Increase debt allocation", "Track debt metrics weekly"],
            ))

        if business_impact > 70:
            recommendations.append(ImprovementRecommendation(
                rec_id="DEBT-004",
                category=ImprovementCategory.DEBT_REDUCTION,
                priority=ImprovementPriority.HIGH,
                title="High business impact from debt",
                description=f"Business impact score at {business_impact} (threshold: 70).",
                impact_score=8.0,
                effort_score=6.0,
                evidence=[f"Business impact: {business_impact}"],
                action_items=["Prioritize business-critical debt", "Engage stakeholders"],
            ))

        if technical_risk > 60:
            recommendations.append(ImprovementRecommendation(
                rec_id="DEBT-005",
                category=ImprovementCategory.DEBT_REDUCTION,
                priority=ImprovementPriority.HIGH,
                title="High technical risk from debt",
                description=f"Technical risk score at {technical_risk} (threshold: 60).",
                impact_score=7.5,
                effort_score=5.0,
                evidence=[f"Technical risk: {technical_risk}"],
                action_items=["Mitigate critical risks first", "Add safety nets"],
            ))

        return recommendations


class AutonomousImprovementEngine:
    def __init__(self) -> None:
        self.architecture = ArchitectureRecommender()
        self.performance = PerformanceRecommenderV2()
        self.security = SecurityRecommenderV2()
        self.refactoring = RefactoringRecommender()
        self.debt = DebtReductionPlanner()
        self._history: list[list[ImprovementRecommendation]] = []

    def generate_all_recommendations(self, metrics: dict[str, Any]) -> list[ImprovementRecommendation]:
        all_recs: list[ImprovementRecommendation] = []
        all_recs.extend(self.architecture.analyze(metrics))
        all_recs.extend(self.performance.analyze(metrics))
        all_recs.extend(self.security.analyze(metrics))
        all_recs.extend(self.refactoring.analyze(metrics))
        all_recs.extend(self.debt.analyze(metrics))
        self._history.append(all_recs)
        return all_recs

    def prioritize_recommendations(self, recs: list[ImprovementRecommendation]) -> list[ImprovementRecommendation]:
        return sorted(
            recs,
            key=lambda r: (-_PRIORITY_RANK.get(r.priority, 0), -r.impact_score),
        )

    def get_improvement_plan(self, metrics: dict[str, Any]) -> dict[str, Any]:
        all_recs = self.generate_all_recommendations(metrics)
        prioritized = self.prioritize_recommendations(all_recs)
        by_category: dict[str, list[ImprovementRecommendation]] = {}
        for rec in prioritized:
            cat = rec.category.value
            by_category.setdefault(cat, []).append(rec)
        return {
            "total_recommendations": len(prioritized),
            "by_category": {k: len(v) for k, v in by_category.items()},
            "critical_count": len([r for r in prioritized if r.priority == ImprovementPriority.CRITICAL]),
            "high_count": len([r for r in prioritized if r.priority == ImprovementPriority.HIGH]),
            "recommendations": prioritized,
        }

    def get_improvement_history(self) -> list[list[ImprovementRecommendation]]:
        return self._history
