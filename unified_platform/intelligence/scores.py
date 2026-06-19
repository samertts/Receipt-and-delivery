"""
Platform Intelligence — Score Calculators for 8 health categories.

Phase 3: Operational Intelligence Engine
Constitution: Principle 50 (Health Scoring), Principle 48 (Operational Awareness)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ScoreLevel(Enum):
    CRITICAL = "critical"
    LOW = "low"
    MEDIUM = "medium"
    GOOD = "good"
    EXCELLENT = "excellent"


@dataclass
class ScoreResult:
    """A health score result."""
    category: str
    score: float  # 0.0 - 100.0
    level: ScoreLevel
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    recommendations: list[str] = field(default_factory=list)


def _score_level(score: float) -> ScoreLevel:
    """Convert numeric score to level."""
    if score >= 90:
        return ScoreLevel.EXCELLENT
    elif score >= 75:
        return ScoreLevel.GOOD
    elif score >= 50:
        return ScoreLevel.MEDIUM
    elif score >= 25:
        return ScoreLevel.LOW
    return ScoreLevel.CRITICAL


# ============================================================================
# Health Score Calculator
# ============================================================================

class HealthScoreCalculator:
    """Calculates overall system health score."""

    def calculate(
        self,
        cpu_usage: float = 0.0,
        memory_usage: float = 0.0,
        disk_usage: float = 0.0,
        active_connections: int = 0,
        error_rate: float = 0.0,
    ) -> ScoreResult:
        # Weighted average
        score = 100.0
        details: dict[str, Any] = {}
        recommendations: list[str] = []

        # CPU impact (max -20 points)
        if cpu_usage > 90:
            score -= 20
            recommendations.append("CPU usage critical: investigate high-load processes")
        elif cpu_usage > 70:
            score -= 10
            recommendations.append("CPU usage elevated: monitor for degradation")
        details["cpu_usage"] = cpu_usage

        # Memory impact (max -20 points)
        if memory_usage > 90:
            score -= 20
            recommendations.append("Memory usage critical: risk of OOM")
        elif memory_usage > 70:
            score -= 10
            recommendations.append("Memory usage elevated: monitor for swapping")
        details["memory_usage"] = memory_usage

        # Disk impact (max -25 points)
        if disk_usage > 95:
            score -= 25
            recommendations.append("Disk usage critical: immediate cleanup required")
        elif disk_usage > 80:
            score -= 15
            recommendations.append("Disk usage high: schedule cleanup")
        details["disk_usage"] = disk_usage

        # Connection impact (max -15 points)
        if active_connections > 1000:
            score -= 15
            recommendations.append("Connection count very high: consider load balancing")
        elif active_connections > 500:
            score -= 5
        details["active_connections"] = active_connections

        # Error rate impact (max -20 points)
        if error_rate > 10:
            score -= 20
            recommendations.append("Error rate critical: investigate root cause")
        elif error_rate > 5:
            score -= 10
            recommendations.append("Error rate elevated: check recent changes")
        details["error_rate"] = error_rate

        score = max(0.0, score)

        return ScoreResult(
            category="health",
            score=score,
            level=_score_level(score),
            message=f"System health: {score:.1f}/100",
            details=details,
            recommendations=recommendations,
        )


# ============================================================================
# Reliability Score Calculator
# ============================================================================

class ReliabilityScoreCalculator:
    """Calculates system reliability score."""

    def calculate(
        self,
        uptime_hours: float = 0.0,
        total_downtime_minutes: float = 0.0,
        failed_operations: int = 0,
        total_operations: int = 0,
        last_recovery_time_ms: float = 0.0,
    ) -> ScoreResult:
        score = 100.0
        details: dict[str, Any] = {}
        recommendations: list[str] = []

        # Uptime ratio
        if uptime_hours > 0:
            uptime_ratio = 1 - (total_downtime_minutes / (uptime_hours * 60))
            uptime_ratio = max(0, min(1, uptime_ratio))
            if uptime_ratio < 0.99:
                score -= (1 - uptime_ratio) * 50
                recommendations.append(f"Uptime ratio {uptime_ratio*100:.2f}% below 99%")
            details["uptime_ratio"] = uptime_ratio

        # Failure rate
        if total_operations > 0:
            failure_rate = failed_operations / total_operations
            if failure_rate > 0.05:
                score -= 30
                recommendations.append(f"Failure rate {failure_rate*100:.1f}% exceeds 5%")
            elif failure_rate > 0.01:
                score -= 10
            details["failure_rate"] = failure_rate

        # Recovery time
        if last_recovery_time_ms > 30000:
            score -= 15
            recommendations.append("Recovery time exceeds 30 seconds")
        details["last_recovery_time_ms"] = last_recovery_time_ms

        score = max(0.0, score)

        return ScoreResult(
            category="reliability",
            score=score,
            level=_score_level(score),
            message=f"Reliability: {score:.1f}/100",
            details=details,
            recommendations=recommendations,
        )


# ============================================================================
# Security Score Calculator
# ============================================================================

class SecurityScoreCalculator:
    """Calculates security posture score."""

    def calculate(
        self,
        failed_logins_24h: int = 0,
        locked_accounts: int = 0,
        critical_vulnerabilities: int = 0,
        high_vulnerabilities: int = 0,
        audit_chain_valid: bool = True,
        mfa_enabled: bool = False,
        password_policy_enforced: bool = True,
    ) -> ScoreResult:
        score = 100.0
        details: dict[str, Any] = {}
        recommendations: list[str] = []

        # Failed logins
        if failed_logins_24h > 100:
            score -= 25
            recommendations.append("High number of failed logins: possible brute force")
        elif failed_logins_24h > 20:
            score -= 10
        details["failed_logins_24h"] = failed_logins_24h

        # Locked accounts
        if locked_accounts > 10:
            score -= 15
            recommendations.append("Multiple locked accounts: investigate")
        details["locked_accounts"] = locked_accounts

        # Vulnerabilities
        if critical_vulnerabilities > 0:
            score -= 30 * critical_vulnerabilities
            recommendations.append(f"{critical_vulnerabilities} critical vulnerabilities")
        if high_vulnerabilities > 0:
            score -= 10 * high_vulnerabilities
            recommendations.append(f"{high_vulnerabilities} high vulnerabilities")
        details["critical_vulnerabilities"] = critical_vulnerabilities
        details["high_vulnerabilities"] = high_vulnerabilities

        # Audit chain
        if not audit_chain_valid:
            score -= 20
            recommendations.append("Audit chain integrity compromised")
        details["audit_chain_valid"] = audit_chain_valid

        # MFA
        if not mfa_enabled:
            score -= 5
            recommendations.append("Consider enabling MFA")
        details["mfa_enabled"] = mfa_enabled

        # Password policy
        if not password_policy_enforced:
            score -= 10
            recommendations.append("Password policy not enforced")
        details["password_policy_enforced"] = password_policy_enforced

        score = max(0.0, score)

        return ScoreResult(
            category="security",
            score=score,
            level=_score_level(score),
            message=f"Security: {score:.1f}/100",
            details=details,
            recommendations=recommendations,
        )


# ============================================================================
# Backup Score Calculator
# ============================================================================

class BackupScoreCalculator:
    """Calculates backup health score."""

    def calculate(
        self,
        last_backup_hours_ago: float = 0.0,
        backup_success_rate: float = 100.0,
        total_backups: int = 0,
        failed_backups: int = 0,
        backup_size_gb: float = 0.0,
        retention_compliant: bool = True,
    ) -> ScoreResult:
        score = 100.0
        details: dict[str, Any] = {}
        recommendations: list[str] = []

        # Recency
        if last_backup_hours_ago > 48:
            score -= 30
            recommendations.append("Last backup older than 48 hours")
        elif last_backup_hours_ago > 24:
            score -= 15
            recommendations.append("Last backup older than 24 hours")
        details["last_backup_hours_ago"] = last_backup_hours_ago

        # Success rate
        if backup_success_rate < 90:
            score -= 30
            recommendations.append(f"Backup success rate {backup_success_rate:.1f}% below 90%")
        elif backup_success_rate < 99:
            score -= 10
        details["backup_success_rate"] = backup_success_rate

        # Volume
        if total_backups == 0:
            score -= 20
            recommendations.append("No backups found")
        details["total_backups"] = total_backups
        details["failed_backups"] = failed_backups

        # Retention
        if not retention_compliant:
            score -= 10
            recommendations.append("Backup retention policy non-compliant")
        details["retention_compliant"] = retention_compliant

        score = max(0.0, score)

        return ScoreResult(
            category="backup",
            score=score,
            level=_score_level(score),
            message=f"Backup: {score:.1f}/100",
            details=details,
            recommendations=recommendations,
        )


# ============================================================================
# Recovery Score Calculator
# ============================================================================

class RecoveryScoreCalculator:
    """Calculates recovery readiness score."""

    def calculate(
        self,
        last_recovery_test_hours_ago: float = 0.0,
        recovery_test_success: bool = True,
        recovery_time_seconds: float = 0.0,
        backup_integrity_valid: bool = True,
        wal_checkpoint_ok: bool = True,
    ) -> ScoreResult:
        score = 100.0
        details: dict[str, Any] = {}
        recommendations: list[str] = []

        # Recovery test recency
        if last_recovery_test_hours_ago > 720:  # 30 days
            score -= 30
            recommendations.append("No recovery test in 30 days")
        elif last_recovery_test_hours_ago > 168:  # 7 days
            score -= 15
            recommendations.append("No recovery test in 7 days")
        details["last_recovery_test_hours_ago"] = last_recovery_test_hours_ago

        # Test success
        if not recovery_test_success:
            score -= 30
            recommendations.append("Last recovery test failed")
        details["recovery_test_success"] = recovery_test_success

        # Recovery time
        if recovery_time_seconds > 300:
            score -= 20
            recommendations.append("Recovery time exceeds 5 minutes")
        elif recovery_time_seconds > 60:
            score -= 10
        details["recovery_time_seconds"] = recovery_time_seconds

        # Integrity
        if not backup_integrity_valid:
            score -= 20
            recommendations.append("Backup integrity check failed")
        details["backup_integrity_valid"] = backup_integrity_valid

        # WAL
        if not wal_checkpoint_ok:
            score -= 10
            recommendations.append("WAL checkpoint issues detected")
        details["wal_checkpoint_ok"] = wal_checkpoint_ok

        score = max(0.0, score)

        return ScoreResult(
            category="recovery",
            score=score,
            level=_score_level(score),
            message=f"Recovery: {score:.1f}/100",
            details=details,
            recommendations=recommendations,
        )


# ============================================================================
# Synchronization Score Calculator
# ============================================================================

class SyncScoreCalculator:
    """Calculates synchronization health score."""

    def calculate(
        self,
        pending_items: int = 0,
        conflict_items: int = 0,
        last_sync_hours_ago: float = 0.0,
        sync_success_rate: float = 100.0,
        avg_sync_time_ms: float = 0.0,
    ) -> ScoreResult:
        score = 100.0
        details: dict[str, Any] = {}
        recommendations: list[str] = []

        # Pending items
        if pending_items > 1000:
            score -= 25
            recommendations.append(f"{pending_items} items pending sync")
        elif pending_items > 100:
            score -= 10
        details["pending_items"] = pending_items

        # Conflicts
        if conflict_items > 50:
            score -= 30
            recommendations.append(f"{conflict_items} unresolved conflicts")
        elif conflict_items > 10:
            score -= 15
        details["conflict_items"] = conflict_items

        # Recency
        if last_sync_hours_ago > 24:
            score -= 20
            recommendations.append("Last sync older than 24 hours")
        details["last_sync_hours_ago"] = last_sync_hours_ago

        # Success rate
        if sync_success_rate < 95:
            score -= 20
            recommendations.append(f"Sync success rate {sync_success_rate:.1f}% below 95%")
        details["sync_success_rate"] = sync_success_rate

        # Performance
        if avg_sync_time_ms > 5000:
            score -= 10
            recommendations.append("Average sync time exceeds 5 seconds")
        details["avg_sync_time_ms"] = avg_sync_time_ms

        score = max(0.0, score)

        return ScoreResult(
            category="synchronization",
            score=score,
            level=_score_level(score),
            message=f"Synchronization: {score:.1f}/100",
            details=details,
            recommendations=recommendations,
        )


# ============================================================================
# Data Integrity Score Calculator
# ============================================================================

class DataIntegrityScoreCalculator:
    """Calculates data integrity score."""

    def calculate(
        self,
        last_checksum_verified: bool = True,
        foreign_key_violations: int = 0,
        orphaned_records: int = 0,
        fts_index_consistent: bool = True,
        schema_version_current: bool = True,
    ) -> ScoreResult:
        score = 100.0
        details: dict[str, Any] = {}
        recommendations: list[str] = []

        # Checksum
        if not last_checksum_verified:
            score -= 20
            recommendations.append("Data checksum not verified")
        details["last_checksum_verified"] = last_checksum_verified

        # Foreign keys
        if foreign_key_violations > 0:
            score -= 25 * min(foreign_key_violations, 4)
            recommendations.append(f"{foreign_key_violations} foreign key violations")
        details["foreign_key_violations"] = foreign_key_violations

        # Orphans
        if orphaned_records > 0:
            score -= 10 * min(orphaned_records, 5)
            recommendations.append(f"{orphaned_records} orphaned records")
        details["orphaned_records"] = orphaned_records

        # FTS
        if not fts_index_consistent:
            score -= 15
            recommendations.append("Full-text search index inconsistent")
        details["fts_index_consistent"] = fts_index_consistent

        # Schema
        if not schema_version_current:
            score -= 10
            recommendations.append("Schema version outdated")
        details["schema_version_current"] = schema_version_current

        score = max(0.0, score)

        return ScoreResult(
            category="data_integrity",
            score=score,
            level=_score_level(score),
            message=f"Data Integrity: {score:.1f}/100",
            details=details,
            recommendations=recommendations,
        )


# ============================================================================
# Performance Score Calculator
# ============================================================================

class PerformanceScoreCalculator:
    """Calculates performance score."""

    def calculate(
        self,
        avg_query_ms: float = 0.0,
        avg_api_response_ms: float = 0.0,
        p95_response_ms: float = 0.0,
        p99_response_ms: float = 0.0,
        throughput_per_sec: float = 0.0,
        cache_hit_rate: float = 0.0,
    ) -> ScoreResult:
        score = 100.0
        details: dict[str, Any] = {}
        recommendations: list[str] = []

        # Query performance
        if avg_query_ms > 1000:
            score -= 20
            recommendations.append("Average query time exceeds 1 second")
        elif avg_query_ms > 100:
            score -= 5
        details["avg_query_ms"] = avg_query_ms

        # API response
        if avg_api_response_ms > 2000:
            score -= 20
            recommendations.append("Average API response exceeds 2 seconds")
        elif avg_api_response_ms > 500:
            score -= 10
        details["avg_api_response_ms"] = avg_api_response_ms

        # P95
        if p95_response_ms > 5000:
            score -= 15
            recommendations.append("P95 response time exceeds 5 seconds")
        details["p95_response_ms"] = p95_response_ms

        # P99
        if p99_response_ms > 10000:
            score -= 10
            recommendations.append("P99 response time exceeds 10 seconds")
        details["p99_response_ms"] = p99_response_ms

        # Throughput
        if throughput_per_sec > 0 and throughput_per_sec < 10:
            score -= 10
            recommendations.append("Throughput below 10 ops/sec")
        details["throughput_per_sec"] = throughput_per_sec

        # Cache
        if cache_hit_rate > 0 and cache_hit_rate < 0.8:
            score -= 5
            recommendations.append("Cache hit rate below 80%")
        details["cache_hit_rate"] = cache_hit_rate

        score = max(0.0, score)

        return ScoreResult(
            category="performance",
            score=score,
            level=_score_level(score),
            message=f"Performance: {score:.1f}/100",
            details=details,
            recommendations=recommendations,
        )
