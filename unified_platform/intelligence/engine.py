"""
Platform Intelligence — Operational Intelligence Engine

Phase 3: Operational Intelligence Engine
Constitution: Principle 48 (Operational Awareness), Principle 49 (Predictive Operations)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from unified_platform.intelligence.scores import (
    BackupScoreCalculator,
    DataIntegrityScoreCalculator,
    DeploymentScoreCalculator,
    HealthScoreCalculator,
    PerformanceScoreCalculator,
    RecoveryScoreCalculator,
    ReliabilityScoreCalculator,
    ScoreLevel,
    ScoreResult,
    SecurityScoreCalculator,
    SyncScoreCalculator,
    UserExperienceScoreCalculator,
)


@dataclass
class IntelligenceReport:
    """Aggregated intelligence report with all 10 scores."""
    health: ScoreResult
    reliability: ScoreResult
    security: ScoreResult
    backup: ScoreResult
    recovery: ScoreResult
    synchronization: ScoreResult
    data_integrity: ScoreResult
    performance: ScoreResult
    user_experience: ScoreResult
    deployment: ScoreResult
    overall_score: float = 0.0
    overall_level: ScoreLevel = ScoreLevel.GOOD
    critical_recommendations: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        scores = [
            self.health.score,
            self.reliability.score,
            self.security.score,
            self.backup.score,
            self.recovery.score,
            self.synchronization.score,
            self.data_integrity.score,
            self.performance.score,
            self.user_experience.score,
            self.deployment.score,
        ]
        self.overall_score = sum(scores) / len(scores)
        if self.overall_score >= 90:
            self.overall_level = ScoreLevel.EXCELLENT
        elif self.overall_score >= 75:
            self.overall_level = ScoreLevel.GOOD
        elif self.overall_score >= 50:
            self.overall_level = ScoreLevel.MEDIUM
        elif self.overall_score >= 25:
            self.overall_level = ScoreLevel.LOW
        else:
            self.overall_level = ScoreLevel.CRITICAL

        # Collect all critical recommendations
        for score in [self.health, self.reliability, self.security, self.backup,
                      self.recovery, self.synchronization, self.data_integrity,
                      self.performance, self.user_experience, self.deployment]:
            if score.level in (ScoreLevel.CRITICAL, ScoreLevel.LOW):
                self.critical_recommendations.extend(score.recommendations)


class IntelligenceEngine:
    """Central intelligence engine for operational awareness."""

    def __init__(self) -> None:
        self._health_calc = HealthScoreCalculator()
        self._reliability_calc = ReliabilityScoreCalculator()
        self._security_calc = SecurityScoreCalculator()
        self._backup_calc = BackupScoreCalculator()
        self._recovery_calc = RecoveryScoreCalculator()
        self._sync_calc = SyncScoreCalculator()
        self._integrity_calc = DataIntegrityScoreCalculator()
        self._performance_calc = PerformanceScoreCalculator()
        self._ux_calc = UserExperienceScoreCalculator()
        self._deployment_calc = DeploymentScoreCalculator()
        self._history: list[IntelligenceReport] = []

    def generate_report(
        self,
        # Health params
        cpu_usage: float = 0.0,
        memory_usage: float = 0.0,
        disk_usage: float = 0.0,
        active_connections: int = 0,
        error_rate: float = 0.0,
        # Reliability params
        uptime_hours: float = 0.0,
        total_downtime_minutes: float = 0.0,
        failed_operations: int = 0,
        total_operations: int = 0,
        last_recovery_time_ms: float = 0.0,
        # Security params
        failed_logins_24h: int = 0,
        locked_accounts: int = 0,
        critical_vulnerabilities: int = 0,
        high_vulnerabilities: int = 0,
        audit_chain_valid: bool = True,
        mfa_enabled: bool = False,
        password_policy_enforced: bool = True,
        # Backup params
        last_backup_hours_ago: float = 0.0,
        backup_success_rate: float = 100.0,
        total_backups: int = 0,
        failed_backups: int = 0,
        backup_size_gb: float = 0.0,
        retention_compliant: bool = True,
        # Recovery params
        last_recovery_test_hours_ago: float = 0.0,
        recovery_test_success: bool = True,
        recovery_time_seconds: float = 0.0,
        backup_integrity_valid: bool = True,
        wal_checkpoint_ok: bool = True,
        # Sync params
        pending_items: int = 0,
        conflict_items: int = 0,
        last_sync_hours_ago: float = 0.0,
        sync_success_rate: float = 100.0,
        avg_sync_time_ms: float = 0.0,
        # Data integrity params
        last_checksum_verified: bool = True,
        foreign_key_violations: int = 0,
        orphaned_records: int = 0,
        fts_index_consistent: bool = True,
        schema_version_current: bool = True,
        # Performance params
        avg_query_ms: float = 0.0,
        avg_api_response_ms: float = 0.0,
        p95_response_ms: float = 0.0,
        p99_response_ms: float = 0.0,
        throughput_per_sec: float = 0.0,
        cache_hit_rate: float = 0.0,
        # User experience params
        response_time_ms: float = 0.0,
        error_rate_percent: float = 0.0,
        task_completion_rate: float = 0.0,
        user_satisfaction: float = 0.0,
        load_time_ms: float = 0.0,
        # Deployment params
        test_pass_rate: float = 1.0,
        coverage_percent: float = 100.0,
        lint_errors: int = 0,
        security_findings_high: int = 0,
        security_findings_critical: int = 0,
        rollback_available: bool = True,
        deployment_history_success_rate: float = 1.0,
    ) -> IntelligenceReport:
        """Generate a full intelligence report."""
        health = self._health_calc.calculate(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            active_connections=active_connections,
            error_rate=error_rate,
        )

        reliability = self._reliability_calc.calculate(
            uptime_hours=uptime_hours,
            total_downtime_minutes=total_downtime_minutes,
            failed_operations=failed_operations,
            total_operations=total_operations,
            last_recovery_time_ms=last_recovery_time_ms,
        )

        security = self._security_calc.calculate(
            failed_logins_24h=failed_logins_24h,
            locked_accounts=locked_accounts,
            critical_vulnerabilities=critical_vulnerabilities,
            high_vulnerabilities=high_vulnerabilities,
            audit_chain_valid=audit_chain_valid,
            mfa_enabled=mfa_enabled,
            password_policy_enforced=password_policy_enforced,
        )

        backup = self._backup_calc.calculate(
            last_backup_hours_ago=last_backup_hours_ago,
            backup_success_rate=backup_success_rate,
            total_backups=total_backups,
            failed_backups=failed_backups,
            backup_size_gb=backup_size_gb,
            retention_compliant=retention_compliant,
        )

        recovery = self._recovery_calc.calculate(
            last_recovery_test_hours_ago=last_recovery_test_hours_ago,
            recovery_test_success=recovery_test_success,
            recovery_time_seconds=recovery_time_seconds,
            backup_integrity_valid=backup_integrity_valid,
            wal_checkpoint_ok=wal_checkpoint_ok,
        )

        synchronization = self._sync_calc.calculate(
            pending_items=pending_items,
            conflict_items=conflict_items,
            last_sync_hours_ago=last_sync_hours_ago,
            sync_success_rate=sync_success_rate,
            avg_sync_time_ms=avg_sync_time_ms,
        )

        data_integrity = self._integrity_calc.calculate(
            last_checksum_verified=last_checksum_verified,
            foreign_key_violations=foreign_key_violations,
            orphaned_records=orphaned_records,
            fts_index_consistent=fts_index_consistent,
            schema_version_current=schema_version_current,
        )

        performance = self._performance_calc.calculate(
            avg_query_ms=avg_query_ms,
            avg_api_response_ms=avg_api_response_ms,
            p95_response_ms=p95_response_ms,
            p99_response_ms=p99_response_ms,
            throughput_per_sec=throughput_per_sec,
            cache_hit_rate=cache_hit_rate,
        )

        user_experience = self._ux_calc.calculate(
            response_time_ms=response_time_ms,
            error_rate_percent=error_rate_percent,
            task_completion_rate=task_completion_rate,
            user_satisfaction=user_satisfaction,
            load_time_ms=load_time_ms,
        )

        deployment = self._deployment_calc.calculate(
            test_pass_rate=test_pass_rate,
            coverage_percent=coverage_percent,
            lint_errors=lint_errors,
            security_findings_high=security_findings_high,
            security_findings_critical=security_findings_critical,
            rollback_available=rollback_available,
            deployment_history_success_rate=deployment_history_success_rate,
        )

        report = IntelligenceReport(
            health=health,
            reliability=reliability,
            security=security,
            backup=backup,
            recovery=recovery,
            synchronization=synchronization,
            data_integrity=data_integrity,
            performance=performance,
            user_experience=user_experience,
            deployment=deployment,
        )

        self._history.append(report)
        return report

    def get_history(self, limit: int = 10) -> list[IntelligenceReport]:
        """Get recent intelligence reports."""
        return self._history[-limit:]

    def get_trend(self, category: str) -> list[float]:
        """Get score trend for a category."""
        trend: list[float] = []
        for report in self._history[-20:]:
            score_obj = getattr(report, category, None)
            if score_obj and hasattr(score_obj, "score"):
                trend.append(score_obj.score)
        return trend

    def get_dashboard_data(self) -> dict[str, Any]:
        """Get dashboard-ready data."""
        if not self._history:
            return {"status": "no_data"}
        latest = self._history[-1]
        return {
            "overall_score": latest.overall_score,
            "overall_level": latest.overall_level.value,
            "scores": {
                "health": {"score": latest.health.score, "level": latest.health.level.value},
                "reliability": {"score": latest.reliability.score, "level": latest.reliability.level.value},
                "security": {"score": latest.security.score, "level": latest.security.level.value},
                "backup": {"score": latest.backup.score, "level": latest.backup.level.value},
                "recovery": {"score": latest.recovery.score, "level": latest.recovery.level.value},
                "synchronization": {"score": latest.synchronization.score, "level": latest.synchronization.level.value},
                "data_integrity": {"score": latest.data_integrity.score, "level": latest.data_integrity.level.value},
                "performance": {"score": latest.performance.score, "level": latest.performance.level.value},
                "user_experience": {"score": latest.user_experience.score, "level": latest.user_experience.level.value},
                "deployment": {"score": latest.deployment.score, "level": latest.deployment.level.value},
            },
            "critical_recommendations": latest.critical_recommendations,
            "report_count": len(self._history),
            "timestamp": latest.timestamp.isoformat(),
        }
