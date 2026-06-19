"""
Platform AI — 9 AI Operation Assistant Capabilities

Phase 4: AI Operations Assistant
Constitution: Principle 33-36 (AI Governance)
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from unified_platform.ai import (
    AIRecommendation,
    AIRecommendationType,
    ConfidenceLevel,
)


class ErrorAnalyzer:
    """Analyzes errors for patterns and root causes."""

    def analyze(self, errors: list[dict[str, Any]]) -> AIRecommendation:
        if not errors:
            return AIRecommendation(
                recommendation_id="EA-000",
                type=AIRecommendationType.ERROR_ANALYSIS,
                title="No errors to analyze",
                summary="No errors found in the analysis window.",
                explanation="The system appears healthy with no errors.",
            )

        error_types = Counter(e.get("type", "unknown") for e in errors)
        services = Counter(e.get("service", "unknown") for e in errors)
        severity_counts = Counter(e.get("severity", "info") for e in errors)

        most_common_type = error_types.most_common(1)[0]
        most_common_service = services.most_common(1)[0]
        critical_count = severity_counts.get("critical", 0)

        evidence = [
            f"Total errors: {len(errors)}",
            f"Most common type: {most_common_type[0]} ({most_common_type[1]} occurrences)",
            f"Most affected service: {most_common_service[0]} ({most_common_service[1]} occurrences)",
            f"Critical errors: {critical_count}",
        ]

        confidence = ConfidenceLevel.HIGH if len(errors) > 20 else ConfidenceLevel.MEDIUM
        risk = "critical" if critical_count > 0 else "high" if len(errors) > 50 else "medium"

        return AIRecommendation(
            recommendation_id="EA-001",
            type=AIRecommendationType.ERROR_ANALYSIS,
            title=f"Error pattern detected: {most_common_type[0]}",
            summary=f"Found {len(errors)} errors, most common: {most_common_type[0]} in {most_common_service[0]}",
            explanation=(
                f"The system has {len(errors)} errors across {len(services)} services. "
                f"The most frequent error type is '{most_common_type[0]}' with {most_common_type[1]} occurrences, "
                f"primarily affecting the '{most_common_service[0]}' service."
            ),
            evidence=evidence,
            confidence=confidence,
            suggested_actions=[
                f"Investigate {most_common_type[0]} errors in {most_common_service[0]}",
                "Check recent deployments for regressions",
                "Review error logs for patterns",
            ],
            affected_components=[most_common_service[0]],
            risk_level=risk,
        )


class RootCauseAnalyzer:
    """Analyzes root causes of system issues."""

    def analyze(self, symptoms: dict[str, Any]) -> AIRecommendation:
        causes: list[str] = []
        evidence: list[str] = []

        error_rate = symptoms.get("error_rate", 0)
        if error_rate > 5:
            causes.append("High error rate suggests systemic issues")
            evidence.append(f"Error rate: {error_rate}%")

        response_time = symptoms.get("avg_response_ms", 0)
        if response_time > 1000:
            causes.append("Slow response times indicate resource bottleneck")
            evidence.append(f"Avg response: {response_time}ms")

        disk_usage = symptoms.get("disk_usage", 0)
        if disk_usage > 85:
            causes.append("High disk usage may cause I/O bottlenecks")
            evidence.append(f"Disk usage: {disk_usage}%")

        memory_usage = symptoms.get("memory_usage", 0)
        if memory_usage > 85:
            causes.append("High memory usage may cause swapping")
            evidence.append(f"Memory usage: {memory_usage}%")

        failed_logins = symptoms.get("failed_logins", 0)
        if failed_logins > 50:
            causes.append("Brute force attack detected")
            evidence.append(f"Failed logins: {failed_logins}")

        if not causes:
            causes.append("No significant issues detected")
            evidence.append("All metrics within normal ranges")

        primary_cause = causes[0] if causes else "Unknown"
        confidence = ConfidenceLevel.HIGH if len(causes) > 2 else ConfidenceLevel.MEDIUM

        return AIRecommendation(
            recommendation_id="RCA-001",
            type=AIRecommendationType.ROOT_CAUSE,
            title=f"Root cause analysis: {primary_cause}",
            summary=f"Identified {len(causes)} potential causes",
            explanation=(
                f"Analysis identified {len(causes)} potential root causes. "
                f"Primary cause: {primary_cause}. "
                + " ".join(causes[1:]) if len(causes) > 1 else ""
            ),
            evidence=evidence,
            confidence=confidence,
            suggested_actions=[
                "Address highest-priority cause first",
                "Monitor metrics after each change",
                "Implement additional logging if cause unclear",
            ],
            risk_level="high" if len(causes) > 2 else "medium",
        )


class LogAnalyzer:
    """Analyzes logs for patterns and anomalies."""

    def analyze(self, logs: list[dict[str, Any]]) -> AIRecommendation:
        if not logs:
            return AIRecommendation(
                recommendation_id="LA-000",
                type=AIRecommendationType.LOG_ANALYSIS,
                title="No logs to analyze",
                summary="No log entries found.",
                explanation="The log buffer is empty.",
            )

        levels = Counter(entry.get("level", "info") for entry in logs)
        messages = Counter(entry.get("message", "") for entry in logs)

        error_count = levels.get("error", 0) + levels.get("critical", 0)
        warning_count = levels.get("warning", 0)
        most_common_msg = messages.most_common(1)[0]

        evidence = [
            f"Total log entries: {len(logs)}",
            f"Errors: {error_count}, Warnings: {warning_count}",
            f"Most common message: '{most_common_msg[0][:80]}' ({most_common_msg[1]} times)",
        ]

        return AIRecommendation(
            recommendation_id="LA-001",
            type=AIRecommendationType.LOG_ANALYSIS,
            title=f"Log analysis: {error_count} errors, {warning_count} warnings",
            summary=f"Analyzed {len(logs)} log entries",
            explanation=(
                f"Found {error_count} error/critical entries and {warning_count} warnings "
                f"out of {len(logs)} total log entries. "
                f"Most frequent message pattern: '{most_common_msg[0][:80]}'"
            ),
            evidence=evidence,
            confidence=ConfidenceLevel.HIGH,
            suggested_actions=[
                f"Investigate error patterns ({error_count} errors)",
                "Review warning conditions",
                "Check for recurring message patterns",
            ],
            risk_level="high" if error_count > 10 else "medium",
        )


class PerformanceRecommender:
    """Generates performance improvement recommendations."""

    def analyze(self, metrics: dict[str, Any]) -> AIRecommendation:
        recommendations: list[str] = []
        evidence: list[str] = []

        query_time = metrics.get("avg_query_ms", 0)
        if query_time > 100:
            recommendations.append("Add database indexes for frequently queried columns")
            evidence.append(f"Avg query time: {query_time}ms")

        api_time = metrics.get("avg_api_response_ms", 0)
        if api_time > 500:
            recommendations.append("Implement response caching for frequent requests")
            evidence.append(f"Avg API response: {api_time}ms")

        p95 = metrics.get("p95_response_ms", 0)
        if p95 > 2000:
            recommendations.append("Profile and optimize slowest endpoints")
            evidence.append(f"P95 response: {p95}ms")

        cache_rate = metrics.get("cache_hit_rate", 1.0)
        if cache_rate < 0.8:
            recommendations.append("Review cache invalidation strategy")
            evidence.append(f"Cache hit rate: {cache_rate*100:.1f}%")

        throughput = metrics.get("throughput_per_sec", 0)
        if throughput > 0 and throughput < 50:
            recommendations.append("Consider connection pooling optimization")
            evidence.append(f"Throughput: {throughput} ops/sec")

        if not recommendations:
            recommendations.append("Performance metrics are within normal ranges")
            evidence.append("All performance metrics acceptable")

        return AIRecommendation(
            recommendation_id="PR-001",
            type=AIRecommendationType.PERFORMANCE,
            title=f"Performance analysis: {len(recommendations)} recommendations",
            summary=f"Generated {len(recommendations)} performance recommendations",
            explanation=(
                f"Based on current metrics, identified {len(recommendations)} performance "
                f"optimization opportunities."
            ),
            evidence=evidence,
            confidence=ConfidenceLevel.HIGH,
            suggested_actions=recommendations,
            risk_level="medium" if len(recommendations) > 2 else "low",
        )


class SecurityRecommender:
    """Generates security improvement recommendations."""

    def analyze(self, metrics: dict[str, Any]) -> AIRecommendation:
        recommendations: list[str] = []
        evidence: list[str] = []

        failed_logins = metrics.get("failed_logins_24h", 0)
        if failed_logins > 20:
            recommendations.append("Implement account lockout after failed attempts")
            evidence.append(f"Failed logins: {failed_logins}")

        vulns = metrics.get("known_vulnerabilities", 0)
        if vulns > 0:
            recommendations.append("Update dependencies to patch vulnerabilities")
            evidence.append(f"Known vulnerabilities: {vulns}")

        mfa = metrics.get("mfa_enabled", False)
        if not mfa:
            recommendations.append("Enable multi-factor authentication")
            evidence.append("MFA: disabled")

        audit_valid = metrics.get("audit_chain_valid", True)
        if not audit_valid:
            recommendations.append("Investigate audit chain integrity")
            evidence.append("Audit chain: invalid")

        password_age = metrics.get("max_password_age_days", 0)
        if password_age > 90:
            recommendations.append("Enforce password rotation policy")
            evidence.append(f"Max password age: {password_age} days")

        if not recommendations:
            recommendations.append("Security posture is acceptable")
            evidence.append("All security checks passed")

        return AIRecommendation(
            recommendation_id="SR-001",
            type=AIRecommendationType.SECURITY,
            title=f"Security analysis: {len(recommendations)} recommendations",
            summary=f"Generated {len(recommendations)} security recommendations",
            explanation=(
                f"Security analysis identified {len(recommendations)} areas for improvement."
            ),
            evidence=evidence,
            confidence=ConfidenceLevel.HIGH,
            suggested_actions=recommendations,
            risk_level="critical" if vulns > 0 or not audit_valid else "high" if failed_logins > 50 else "medium",
        )


class BackupRecommender:
    """Generates backup improvement recommendations."""

    def analyze(self, metrics: dict[str, Any]) -> AIRecommendation:
        recommendations: list[str] = []
        evidence: list[str] = []

        last_backup_hours = metrics.get("last_backup_hours_ago", 0)
        if last_backup_hours > 24:
            recommendations.append("Create backup immediately - last backup overdue")
            evidence.append(f"Hours since backup: {last_backup_hours}")

        success_rate = metrics.get("backup_success_rate", 100)
        if success_rate < 95:
            recommendations.append("Investigate backup failures")
            evidence.append(f"Success rate: {success_rate}%")

        retention = metrics.get("retention_compliant", True)
        if not retention:
            recommendations.append("Enforce backup retention policy")
            evidence.append("Retention: non-compliant")

        total_backups = metrics.get("total_backups", 0)
        if total_backups < 7:
            recommendations.append("Increase backup frequency")
            evidence.append(f"Total backups: {total_backups}")

        if not recommendations:
            recommendations.append("Backup health is acceptable")
            evidence.append("All backup checks passed")

        return AIRecommendation(
            recommendation_id="BR-001",
            type=AIRecommendationType.BACKUP,
            title=f"Backup analysis: {len(recommendations)} recommendations",
            summary=f"Generated {len(recommendations)} backup recommendations",
            explanation=f"Backup analysis identified {len(recommendations)} improvement areas.",
            evidence=evidence,
            confidence=ConfidenceLevel.HIGH,
            suggested_actions=recommendations,
            risk_level="high" if last_backup_hours > 48 else "medium",
        )


class RecoveryRecommender:
    """Generates recovery improvement recommendations."""

    def analyze(self, metrics: dict[str, Any]) -> AIRecommendation:
        recommendations: list[str] = []
        evidence: list[str] = []

        last_test_hours = metrics.get("last_recovery_test_hours_ago", 0)
        if last_test_hours > 168:
            recommendations.append("Run recovery test immediately")
            evidence.append(f"Hours since test: {last_test_hours}")

        test_success = metrics.get("recovery_test_success", True)
        if not test_success:
            recommendations.append("Fix recovery test failures before production")
            evidence.append("Last test: FAILED")

        recovery_time = metrics.get("recovery_time_seconds", 0)
        if recovery_time > 300:
            recommendations.append("Optimize recovery procedures")
            evidence.append(f"Recovery time: {recovery_time}s")

        integrity = metrics.get("backup_integrity_valid", True)
        if not integrity:
            recommendations.append("Restore backup integrity")
            evidence.append("Backup integrity: INVALID")

        if not recommendations:
            recommendations.append("Recovery readiness is acceptable")
            evidence.append("All recovery checks passed")

        return AIRecommendation(
            recommendation_id="RCR-001",
            type=AIRecommendationType.RECOVERY,
            title=f"Recovery analysis: {len(recommendations)} recommendations",
            summary=f"Generated {len(recommendations)} recovery recommendations",
            explanation=f"Recovery analysis identified {len(recommendations)} areas for improvement.",
            evidence=evidence,
            confidence=ConfidenceLevel.HIGH,
            suggested_actions=recommendations,
            risk_level="critical" if not integrity or not test_success else "high",
        )


class CapacityPlanner:
    """Forecasts capacity needs."""

    def analyze(self, metrics: dict[str, Any]) -> AIRecommendation:
        recommendations: list[str] = []
        evidence: list[str] = []

        disk_usage = metrics.get("disk_usage_percent", 0)
        disk_growth = metrics.get("disk_growth_rate_gb_per_day", 0)
        disk_total = metrics.get("disk_total_gb", 1)

        if disk_usage > 75:
            days_to_full = ((disk_total * (1 - disk_usage / 100)) / disk_growth) if disk_growth > 0 else 999
            recommendations.append(f"Plan storage expansion - {days_to_full:.0f} days to full")
            evidence.append(f"Disk: {disk_usage}% used, {days_to_full:.0f} days to full")

        db_size = metrics.get("database_size_gb", 0)
        db_growth = metrics.get("db_growth_rate_gb_per_day", 0)
        if db_size > 5:
            recommendations.append(f"Plan database archival - {db_size:.1f} GB with {db_growth:.2f} GB/day growth")
            evidence.append(f"DB size: {db_size:.1f} GB")

        users = metrics.get("concurrent_users", 0)
        max_users = metrics.get("max_user_capacity", 100)
        if users / max_users > 0.6 if max_users > 0 else False:
            recommendations.append("Plan horizontal scaling")
            evidence.append(f"Users: {users}/{max_users}")

        if not recommendations:
            recommendations.append("Capacity is within acceptable limits")
            evidence.append("All capacity metrics normal")

        return AIRecommendation(
            recommendation_id="CP-001",
            type=AIRecommendationType.CAPACITY,
            title=f"Capacity forecast: {len(recommendations)} recommendations",
            summary=f"Generated {len(recommendations)} capacity recommendations",
            explanation=f"Capacity analysis identified {len(recommendations)} planning needs.",
            evidence=evidence,
            confidence=ConfidenceLevel.MEDIUM,
            suggested_actions=recommendations,
            risk_level="high" if disk_usage > 85 else "medium",
        )


class RiskPredictor:
    """Predicts operational risks."""

    def analyze(self, metrics: dict[str, Any]) -> AIRecommendation:
        risks: list[str] = []
        evidence: list[str] = []

        error_rate = metrics.get("error_rate", 0)
        if error_rate > 5:
            risks.append(f"System instability risk: {error_rate}% error rate")
            evidence.append(f"Error rate: {error_rate}%")

        disk = metrics.get("disk_usage_percent", 0)
        if disk > 80:
            risks.append(f"Storage exhaustion risk: {disk}% used")
            evidence.append(f"Disk: {disk}%")

        backup_hours = metrics.get("last_backup_hours_ago", 0)
        if backup_hours > 48:
            risks.append(f"Data loss risk: backup overdue by {backup_hours}h")
            evidence.append(f"Backup age: {backup_hours}h")

        sync_pending = metrics.get("sync_pending_items", 0)
        if sync_pending > 100:
            risks.append(f"Sync backlog risk: {sync_pending} items pending")
            evidence.append(f"Sync pending: {sync_pending}")

        failed_logins = metrics.get("failed_logins_24h", 0)
        if failed_logins > 50:
            risks.append(f"Security breach risk: {failed_logins} failed logins")
            evidence.append(f"Failed logins: {failed_logins}")

        if not risks:
            risks.append("No significant risks detected")
            evidence.append("All risk indicators within normal ranges")

        risk_level = "critical" if len(risks) > 3 else "high" if len(risks) > 1 else "medium"

        return AIRecommendation(
            recommendation_id="RP-001",
            type=AIRecommendationType.RISK_PREDICTION,
            title=f"Risk assessment: {len(risks)} risks identified",
            summary=f"Identified {len(risks)} operational risks",
            explanation=f"Risk analysis identified {len(risks)} potential issues that require attention.",
            evidence=evidence,
            confidence=ConfidenceLevel.MEDIUM,
            suggested_actions=[f"Mitigate: {r}" for r in risks if r != "No significant risks detected"],
            risk_level=risk_level,
        )
