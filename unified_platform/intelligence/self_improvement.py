"""
Platform Intelligence — Self-Improvement Framework

Phase 9: Self-Improvement Framework
Constitution: Principle 41 (Continuous Self Assessment), Principle 42 (Improvement Engine)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecommendationType(Enum):
    TECHNICAL_DEBT = "technical_debt"
    PERFORMANCE = "performance"
    SECURITY = "security"
    RELIABILITY = "reliability"
    CAPACITY = "capacity"
    ARCHITECTURE = "architecture"


@dataclass
class Recommendation:
    """An improvement recommendation."""
    recommendation_id: str
    category: RecommendationType
    title: str
    description: str
    risk_level: RiskLevel
    affected_components: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    suggested_actions: list[str] = field(default_factory=list)
    estimated_effort: str = ""
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


class TechnicalDebtDetector:
    """Detects technical debt patterns."""

    def analyze(self, code_metrics: dict[str, Any] | None = None) -> list[Recommendation]:
        recommendations: list[Recommendation] = []
        metrics = code_metrics or {}

        # Check for high cyclomatic complexity
        complexity = metrics.get("cyclomatic_complexity", 0)
        if complexity > 20:
            recommendations.append(Recommendation(
                recommendation_id="TD-001",
                category=RecommendationType.TECHNICAL_DEBT,
                title="High cyclomatic complexity detected",
                description=f"Cyclomatic complexity of {complexity} exceeds threshold of 20.",
                risk_level=RiskLevel.HIGH,
                evidence=[f"Measured complexity: {complexity}"],
                suggested_actions=["Refactor into smaller functions", "Extract complex logic into services"],
                estimated_effort="medium",
            ))

        # Check for long functions
        max_function_length = metrics.get("max_function_length", 0)
        if max_function_length > 200:
            recommendations.append(Recommendation(
                recommendation_id="TD-002",
                category=RecommendationType.TECHNICAL_DEBT,
                title="Functions exceeding 200 lines",
                description=f"Found functions with {max_function_length} lines.",
                risk_level=RiskLevel.MEDIUM,
                evidence=[f"Longest function: {max_function_length} lines"],
                suggested_actions=["Break into smaller functions", "Extract helper functions"],
                estimated_effort="low",
            ))

        # Check for duplicated code
        duplication_rate = metrics.get("code_duplication_rate", 0)
        if duplication_rate > 15:
            recommendations.append(Recommendation(
                recommendation_id="TD-003",
                category=RecommendationType.TECHNICAL_DEBT,
                title="High code duplication rate",
                description=f"Code duplication rate of {duplication_rate}% exceeds 15% threshold.",
                risk_level=RiskLevel.MEDIUM,
                evidence=[f"Duplication rate: {duplication_rate}%"],
                suggested_actions=["Extract common logic", "Create shared utilities"],
                estimated_effort="medium",
            ))

        # Check for missing type hints
        type_coverage = metrics.get("type_hint_coverage", 100)
        if type_coverage < 80:
            recommendations.append(Recommendation(
                recommendation_id="TD-004",
                category=RecommendationType.TECHNICAL_DEBT,
                title="Low type hint coverage",
                description=f"Type hint coverage at {type_coverage}% (target: 80%).",
                risk_level=RiskLevel.LOW,
                evidence=[f"Coverage: {type_coverage}%"],
                suggested_actions=["Add type hints to public APIs", "Enable mypy strict mode"],
                estimated_effort="low",
            ))

        # Check for test coverage
        test_coverage = metrics.get("test_coverage", 100)
        if test_coverage < 90:
            recommendations.append(Recommendation(
                recommendation_id="TD-005",
                category=RecommendationType.TECHNICAL_DEBT,
                title="Test coverage below threshold",
                description=f"Test coverage at {test_coverage}% (target: 90%).",
                risk_level=RiskLevel.HIGH if test_coverage < 70 else RiskLevel.MEDIUM,
                evidence=[f"Coverage: {test_coverage}%"],
                suggested_actions=["Add unit tests for uncovered modules", "Add integration tests"],
                estimated_effort="high",
            ))

        return recommendations


class PerformanceBottleneckDetector:
    """Detects performance bottlenecks."""

    def analyze(self, perf_metrics: dict[str, Any] | None = None) -> list[Recommendation]:
        recommendations: list[Recommendation] = []
        metrics = perf_metrics or {}

        avg_response_ms = metrics.get("avg_response_ms", 0)
        if avg_response_ms > 500:
            recommendations.append(Recommendation(
                recommendation_id="PB-001",
                category=RecommendationType.PERFORMANCE,
                title="High average response time",
                description=f"Average response time {avg_response_ms}ms exceeds 500ms threshold.",
                risk_level=RiskLevel.HIGH,
                evidence=[f"Average: {avg_response_ms}ms"],
                suggested_actions=["Add database indexing", "Implement caching", "Optimize queries"],
                estimated_effort="medium",
            ))

        p95_ms = metrics.get("p95_response_ms", 0)
        if p95_ms > 2000:
            recommendations.append(Recommendation(
                recommendation_id="PB-002",
                category=RecommendationType.PERFORMANCE,
                title="High P95 response time",
                description=f"P95 response time {p95_ms}ms exceeds 2000ms threshold.",
                risk_level=RiskLevel.HIGH,
                evidence=[f"P95: {p95_ms}ms"],
                suggested_actions=["Profile slow queries", "Add connection pooling"],
                estimated_effort="high",
            ))

        slow_queries = metrics.get("slow_query_count", 0)
        if slow_queries > 10:
            recommendations.append(Recommendation(
                recommendation_id="PB-003",
                category=RecommendationType.PERFORMANCE,
                title="Multiple slow queries detected",
                description=f"Found {slow_queries} queries exceeding 1 second.",
                risk_level=RiskLevel.MEDIUM,
                evidence=[f"Slow queries: {slow_queries}"],
                suggested_actions=["Add EXPLAIN analysis", "Create missing indexes"],
                estimated_effort="medium",
            ))

        cache_hit_rate = metrics.get("cache_hit_rate", 1.0)
        if cache_hit_rate < 0.8:
            recommendations.append(Recommendation(
                recommendation_id="PB-004",
                category=RecommendationType.PERFORMANCE,
                title="Low cache hit rate",
                description=f"Cache hit rate {cache_hit_rate*100:.1f}% below 80% threshold.",
                risk_level=RiskLevel.LOW,
                evidence=[f"Hit rate: {cache_hit_rate*100:.1f}%"],
                suggested_actions=["Review cache invalidation strategy", "Increase cache TTL"],
                estimated_effort="low",
            ))

        return recommendations


class SecurityWeaknessDetector:
    """Detects security weaknesses."""

    def analyze(self, sec_metrics: dict[str, Any] | None = None) -> list[Recommendation]:
        recommendations: list[Recommendation] = []
        metrics = sec_metrics or {}

        failed_logins = metrics.get("failed_logins_24h", 0)
        if failed_logins > 50:
            recommendations.append(Recommendation(
                recommendation_id="SW-001",
                category=RecommendationType.SECURITY,
                title="High number of failed logins",
                description=f"{failed_logins} failed logins in 24h indicates possible brute force.",
                risk_level=RiskLevel.HIGH,
                evidence=[f"Failed logins: {failed_logins}"],
                suggested_actions=["Implement account lockout", "Add CAPTCHA", "Enable IP blocking"],
                estimated_effort="medium",
            ))

        vulns = metrics.get("known_vulnerabilities", 0)
        if vulns > 0:
            recommendations.append(Recommendation(
                recommendation_id="SW-002",
                category=RecommendationType.SECURITY,
                title="Known vulnerabilities detected",
                description=f"{vulns} known vulnerabilities in dependencies.",
                risk_level=RiskLevel.CRITICAL,
                evidence=[f"Vulnerabilities: {vulns}"],
                suggested_actions=["Update dependencies", "Apply security patches"],
                estimated_effort="medium",
            ))

        password_age = metrics.get("max_password_age_days", 0)
        if password_age > 90:
            recommendations.append(Recommendation(
                recommendation_id="SW-003",
                category=RecommendationType.SECURITY,
                title="Old passwords detected",
                description=f"Some passwords older than {password_age} days.",
                risk_level=RiskLevel.MEDIUM,
                evidence=[f"Max age: {password_age} days"],
                suggested_actions=["Enforce password rotation", "Enable MFA"],
                estimated_effort="low",
            ))

        audit_chain_valid = metrics.get("audit_chain_valid", True)
        if not audit_chain_valid:
            recommendations.append(Recommendation(
                recommendation_id="SW-004",
                category=RecommendationType.SECURITY,
                title="Audit chain integrity compromised",
                description="Audit chain verification failed.",
                risk_level=RiskLevel.CRITICAL,
                evidence=["Audit chain invalid"],
                suggested_actions=["Investigate tampering", "Restore from backup"],
                estimated_effort="high",
            ))

        return recommendations


class ReliabilityRiskDetector:
    """Detects reliability risks."""

    def analyze(self, rel_metrics: dict[str, Any] | None = None) -> list[Recommendation]:
        recommendations: list[Recommendation] = []
        metrics = rel_metrics or {}

        uptime_hours = metrics.get("uptime_hours", 0)
        if uptime_hours > 720 and not metrics.get("recent_restart"):
            recommendations.append(Recommendation(
                recommendation_id="RR-001",
                category=RecommendationType.RELIABILITY,
                title="Long uptime without restart",
                description=f"System running for {uptime_hours} hours without restart.",
                risk_level=RiskLevel.LOW,
                evidence=[f"Uptime: {uptime_hours}h"],
                suggested_actions=["Schedule maintenance restart", "Check for memory leaks"],
                estimated_effort="low",
            ))

        error_rate = metrics.get("error_rate", 0)
        if error_rate > 5:
            recommendations.append(Recommendation(
                recommendation_id="RR-002",
                category=RecommendationType.RELIABILITY,
                title="High error rate",
                description=f"Error rate {error_rate}% exceeds 5% threshold.",
                risk_level=RiskLevel.HIGH,
                evidence=[f"Error rate: {error_rate}%"],
                suggested_actions=["Investigate error sources", "Add error handling"],
                estimated_effort="medium",
            ))

        last_backup_hours = metrics.get("last_backup_hours_ago", 0)
        if last_backup_hours > 48:
            recommendations.append(Recommendation(
                recommendation_id="RR-003",
                category=RecommendationType.RELIABILITY,
                title="Backup overdue",
                description=f"Last backup was {last_backup_hours} hours ago.",
                risk_level=RiskLevel.HIGH,
                evidence=[f"Hours since backup: {last_backup_hours}"],
                suggested_actions=["Create backup immediately", "Check backup service"],
                estimated_effort="low",
            ))

        recovery_test_hours = metrics.get("last_recovery_test_hours_ago", 0)
        if recovery_test_hours > 720:
            recommendations.append(Recommendation(
                recommendation_id="RR-004",
                category=RecommendationType.RELIABILITY,
                title="Recovery test overdue",
                description=f"Last recovery test was {recovery_test_hours} hours ago.",
                risk_level=RiskLevel.MEDIUM,
                evidence=[f"Hours since test: {recovery_test_hours}"],
                suggested_actions=["Run recovery test", "Validate backup restore"],
                estimated_effort="medium",
            ))

        return recommendations


class CapacityForecaster:
    """Forecasts capacity needs."""

    def analyze(self, capacity_metrics: dict[str, Any] | None = None) -> list[Recommendation]:
        recommendations: list[Recommendation] = []
        metrics = capacity_metrics or {}

        disk_usage = metrics.get("disk_usage_percent", 0)
        disk_growth_rate = metrics.get("disk_growth_rate_gb_per_day", 0)
        disk_total_gb = metrics.get("disk_total_gb", 1)

        if disk_usage > 80:
            days_to_full = ((disk_total_gb * (1 - disk_usage / 100)) / disk_growth_rate) if disk_growth_rate > 0 else 999
            recommendations.append(Recommendation(
                recommendation_id="CF-001",
                category=RecommendationType.CAPACITY,
                title="Disk usage high",
                description=f"Disk usage at {disk_usage}%. Estimated {days_to_full:.0f} days to full.",
                risk_level=RiskLevel.HIGH if days_to_full < 30 else RiskLevel.MEDIUM,
                evidence=[f"Usage: {disk_usage}%", f"Growth: {disk_growth_rate} GB/day", f"Days to full: {days_to_full:.0f}"],
                suggested_actions=["Expand storage", "Clean old data", "Archive old records"],
                estimated_effort="low",
            ))

        db_size_gb = metrics.get("database_size_gb", 0)
        db_growth_rate = metrics.get("db_growth_rate_gb_per_day", 0)
        if db_size_gb > 10:
            recommendations.append(Recommendation(
                recommendation_id="CF-002",
                category=RecommendationType.CAPACITY,
                title="Database size significant",
                description=f"Database size {db_size_gb:.1f} GB with {db_growth_rate:.2f} GB/day growth.",
                risk_level=RiskLevel.MEDIUM,
                evidence=[f"Size: {db_size_gb:.1f} GB", f"Growth: {db_growth_rate:.2f} GB/day"],
                suggested_actions=["Implement archival", "Partition old data", "Optimize queries"],
                estimated_effort="medium",
            ))

        concurrent_users = metrics.get("concurrent_users", 0)
        max_capacity = metrics.get("max_user_capacity", 100)
        usage_ratio = concurrent_users / max_capacity if max_capacity > 0 else 0
        if usage_ratio > 0.7:
            recommendations.append(Recommendation(
                recommendation_id="CF-003",
                category=RecommendationType.CAPACITY,
                title="High user capacity utilization",
                description=f"User capacity at {usage_ratio*100:.0f}% ({concurrent_users}/{max_capacity}).",
                risk_level=RiskLevel.HIGH if usage_ratio > 0.9 else RiskLevel.MEDIUM,
                evidence=[f"Current: {concurrent_users}", f"Max: {max_capacity}"],
                suggested_actions=["Scale infrastructure", "Optimize connection pooling"],
                estimated_effort="high",
            ))

        return recommendations


class SelfImprovementEngine:
    """Central engine for self-improvement recommendations."""

    def __init__(self) -> None:
        self._debt_detector = TechnicalDebtDetector()
        self._perf_detector = PerformanceBottleneckDetector()
        self._security_detector = SecurityWeaknessDetector()
        self._reliability_detector = ReliabilityRiskDetector()
        self._capacity_forecaster = CapacityForecaster()
        self._history: list[list[Recommendation]] = []

    def generate_recommendations(
        self,
        code_metrics: dict[str, Any] | None = None,
        perf_metrics: dict[str, Any] | None = None,
        sec_metrics: dict[str, Any] | None = None,
        rel_metrics: dict[str, Any] | None = None,
        capacity_metrics: dict[str, Any] | None = None,
    ) -> list[Recommendation]:
        """Generate all improvement recommendations."""
        all_recommendations: list[Recommendation] = []
        all_recommendations.extend(self._debt_detector.analyze(code_metrics))
        all_recommendations.extend(self._perf_detector.analyze(perf_metrics))
        all_recommendations.extend(self._security_detector.analyze(sec_metrics))
        all_recommendations.extend(self._reliability_detector.analyze(rel_metrics))
        all_recommendations.extend(self._capacity_forecaster.analyze(capacity_metrics))

        # Sort by priority (higher = more critical)
        priority_map = {RiskLevel.CRITICAL: 4, RiskLevel.HIGH: 3, RiskLevel.MEDIUM: 2, RiskLevel.LOW: 1}
        all_recommendations.sort(key=lambda r: -priority_map.get(r.risk_level, 0))

        self._history.append(all_recommendations)
        return all_recommendations

    def get_history(self, limit: int = 5) -> list[list[Recommendation]]:
        return self._history[-limit:]

    def get_summary(self) -> dict[str, Any]:
        if not self._history:
            return {"total_recommendations": 0}
        latest = self._history[-1]
        by_category: dict[str, int] = {}
        by_risk: dict[str, int] = {}
        for r in latest:
            by_category[r.category.value] = by_category.get(r.category.value, 0) + 1
            by_risk[r.risk_level.value] = by_risk.get(r.risk_level.value, 0) + 1
        return {
            "total_recommendations": len(latest),
            "by_category": by_category,
            "by_risk_level": by_risk,
            "critical_count": by_risk.get("critical", 0),
            "high_count": by_risk.get("high", 0),
        }
