"""
Platform AI — AI Operations Assistant Engine

Phase 4: AI Operations Assistant
Constitution: Principle 33 (AI Governance), Principle 36 (Human Authority)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from unified_platform.ai import AIRecommendation, AIRecommendationType
from unified_platform.ai.capabilities import (
    BackupRecommender,
    CapacityPlanner,
    ErrorAnalyzer,
    LogAnalyzer,
    PerformanceRecommender,
    RecoveryRecommender,
    RiskPredictor,
    RootCauseAnalyzer,
    SecurityRecommender,
)


@dataclass
class AIAnalysisReport:
    """Comprehensive AI analysis report."""
    recommendations: list[AIRecommendation] = field(default_factory=list)
    overall_risk: str = "low"
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    summary: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        for r in self.recommendations:
            if r.risk_level == "critical":
                self.critical_count += 1
            elif r.risk_level == "high":
                self.high_count += 1
            elif r.risk_level == "medium":
                self.medium_count += 1
        if self.critical_count > 0:
            self.overall_risk = "critical"
        elif self.high_count > 0:
            self.overall_risk = "high"
        elif self.medium_count > 0:
            self.overall_risk = "medium"


class AIAssistant:
    """AI Operations Assistant with 9 analysis capabilities."""

    def __init__(self) -> None:
        self._error_analyzer = ErrorAnalyzer()
        self._root_cause = RootCauseAnalyzer()
        self._log_analyzer = LogAnalyzer()
        self._perf_recommender = PerformanceRecommender()
        self._security_recommender = SecurityRecommender()
        self._backup_recommender = BackupRecommender()
        self._recovery_recommender = RecoveryRecommender()
        self._capacity_planner = CapacityPlanner()
        self._risk_predictor = RiskPredictor()
        self._history: list[AIAnalysisReport] = []

    def analyze_errors(self, errors: list[dict[str, Any]]) -> AIRecommendation:
        return self._error_analyzer.analyze(errors)

    def analyze_root_cause(self, symptoms: dict[str, Any]) -> AIRecommendation:
        return self._root_cause.analyze(symptoms)

    def analyze_logs(self, logs: list[dict[str, Any]]) -> AIRecommendation:
        return self._log_analyzer.analyze(logs)

    def analyze_performance(self, metrics: dict[str, Any]) -> AIRecommendation:
        return self._perf_recommender.analyze(metrics)

    def analyze_security(self, metrics: dict[str, Any]) -> AIRecommendation:
        return self._security_recommender.analyze(metrics)

    def analyze_backup(self, metrics: dict[str, Any]) -> AIRecommendation:
        return self._backup_recommender.analyze(metrics)

    def analyze_recovery(self, metrics: dict[str, Any]) -> AIRecommendation:
        return self._recovery_recommender.analyze(metrics)

    def analyze_capacity(self, metrics: dict[str, Any]) -> AIRecommendation:
        return self._capacity_planner.analyze(metrics)

    def analyze_risks(self, metrics: dict[str, Any]) -> AIRecommendation:
        return self._risk_predictor.analyze(metrics)

    def full_analysis(
        self,
        errors: list[dict[str, Any]] | None = None,
        logs: list[dict[str, Any]] | None = None,
        performance_metrics: dict[str, Any] | None = None,
        security_metrics: dict[str, Any] | None = None,
        backup_metrics: dict[str, Any] | None = None,
        recovery_metrics: dict[str, Any] | None = None,
        capacity_metrics: dict[str, Any] | None = None,
    ) -> AIAnalysisReport:
        """Run all 9 analysis capabilities and generate a combined report."""
        recommendations: list[AIRecommendation] = []

        if errors:
            recommendations.append(self.analyze_errors(errors))
        if logs:
            recommendations.append(self.analyze_logs(logs))
        if performance_metrics:
            recommendations.append(self.analyze_performance(performance_metrics))
        if security_metrics:
            recommendations.append(self.analyze_security(security_metrics))
        if backup_metrics:
            recommendations.append(self.analyze_backup(backup_metrics))
        if recovery_metrics:
            recommendations.append(self.analyze_recovery(recovery_metrics))
        if capacity_metrics:
            recommendations.append(self.analyze_capacity(capacity_metrics))

        # Always run root cause and risk prediction
        all_metrics = {}
        if performance_metrics:
            all_metrics.update(performance_metrics)
        if security_metrics:
            all_metrics.update(security_metrics)
        if backup_metrics:
            all_metrics.update(backup_metrics)

        recommendations.append(self.analyze_root_cause(all_metrics))
        recommendations.append(self.analyze_risks(all_metrics))

        report = AIAnalysisReport(recommendations=recommendations)

        critical_recs = [r for r in recommendations if r.risk_level == "critical"]
        if critical_recs:
            report.summary = f"CRITICAL: {len(critical_recs)} critical findings require immediate attention"
        elif report.high_count > 0:
            report.summary = f"HIGH: {report.high_count} high-priority findings"
        else:
            report.summary = f"Analysis complete: {len(recommendations)} recommendations"

        self._history.append(report)
        return report

    def get_recommendations_by_type(self, rec_type: AIRecommendationType) -> list[AIRecommendation]:
        if not self._history:
            return []
        latest = self._history[-1]
        return [r for r in latest.recommendations if r.type == rec_type]

    def get_critical_recommendations(self) -> list[AIRecommendation]:
        if not self._history:
            return []
        latest = self._history[-1]
        return [r for r in latest.recommendations if r.risk_level == "critical"]

    def get_history(self, limit: int = 5) -> list[AIAnalysisReport]:
        return self._history[-limit:]

    def get_dashboard_data(self) -> dict[str, Any]:
        if not self._history:
            return {"status": "no_data"}
        latest = self._history[-1]
        return {
            "overall_risk": latest.overall_risk,
            "critical_count": latest.critical_count,
            "high_count": latest.high_count,
            "medium_count": latest.medium_count,
            "total_recommendations": len(latest.recommendations),
            "summary": latest.summary,
            "timestamp": latest.timestamp.isoformat(),
        }
