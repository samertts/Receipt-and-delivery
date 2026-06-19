"""
Tests for AI Operations Assistant — Phase 4

Covers: AIRecommendation, ErrorAnalyzer, RootCauseAnalyzer, LogAnalyzer,
        PerformanceRecommender, SecurityRecommender, BackupRecommender,
        RecoveryRecommender, CapacityPlanner, RiskPredictor, AIAssistant,
        AIAnalysisReport.
"""

from __future__ import annotations

from datetime import datetime


from unified_platform.ai import (
    AIRecommendation,
    AIRecommendationType,
    ConfidenceLevel,
)
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
from unified_platform.ai.assistant import AIAnalysisReport, AIAssistant


# ---------------------------------------------------------------------------
# 1. TestAIRecommendation
# ---------------------------------------------------------------------------
class TestAIRecommendation:
    def test_creation_with_defaults(self) -> None:
        rec = AIRecommendation(
            recommendation_id="R-1",
            type=AIRecommendationType.ERROR_ANALYSIS,
            title="t",
            summary="s",
            explanation="e",
        )
        assert rec.recommendation_id == "R-1"
        assert rec.type == AIRecommendationType.ERROR_ANALYSIS
        assert rec.evidence == []
        assert rec.confidence == ConfidenceLevel.MEDIUM
        assert rec.suggested_actions == []
        assert rec.affected_components == []
        assert rec.risk_level == "medium"
        assert isinstance(rec.created_at, datetime)
        assert rec.metadata == {}

    def test_creation_with_all_fields(self) -> None:
        rec = AIRecommendation(
            recommendation_id="R-2",
            type=AIRecommendationType.SECURITY,
            title="Sec",
            summary="Sum",
            explanation="Expl",
            evidence=["e1", "e2"],
            confidence=ConfidenceLevel.HIGH,
            suggested_actions=["a1"],
            affected_components=["svc1"],
            risk_level="critical",
            metadata={"k": "v"},
        )
        assert rec.evidence == ["e1", "e2"]
        assert rec.confidence == ConfidenceLevel.HIGH
        assert rec.risk_level == "critical"
        assert rec.metadata == {"k": "v"}

    def test_to_dict_serialization(self) -> None:
        rec = AIRecommendation(
            recommendation_id="R-3",
            type=AIRecommendationType.PERFORMANCE,
            title="Perf",
            summary="S",
            explanation="E",
            evidence=["ev"],
            confidence=ConfidenceLevel.LOW,
            risk_level="high",
        )
        d = rec.to_dict()
        assert d["id"] == "R-3"
        assert d["type"] == "performance"
        assert d["title"] == "Perf"
        assert d["evidence"] == ["ev"]
        assert d["confidence"] == "low"
        assert d["risk_level"] == "high"
        assert "created_at" in d
        assert isinstance(d["created_at"], str)

    def test_to_dict_default_lists(self) -> None:
        rec = AIRecommendation(
            recommendation_id="R-4",
            type=AIRecommendationType.BACKUP,
            title="B",
            summary="S",
            explanation="E",
        )
        d = rec.to_dict()
        assert d["suggested_actions"] == []
        assert d["affected_components"] == []


# ---------------------------------------------------------------------------
# 2. TestErrorAnalyzer
# ---------------------------------------------------------------------------
class TestErrorAnalyzer:
    def setup_method(self) -> None:
        self.analyzer = ErrorAnalyzer()

    def test_empty_errors(self) -> None:
        rec = self.analyzer.analyze([])
        assert rec.recommendation_id == "EA-000"
        assert rec.type == AIRecommendationType.ERROR_ANALYSIS
        assert "No errors" in rec.title

    def test_single_error(self) -> None:
        errors = [{"type": "ValueError", "service": "api", "severity": "warning"}]
        rec = self.analyzer.analyze(errors)
        assert rec.recommendation_id == "EA-001"
        assert "ValueError" in rec.title
        assert "api" in rec.summary
        assert rec.confidence == ConfidenceLevel.MEDIUM

    def test_multiple_errors_medium_confidence(self) -> None:
        errors = [{"type": "E", "service": "svc", "severity": "info"}] * 10
        rec = self.analyzer.analyze(errors)
        assert rec.confidence == ConfidenceLevel.MEDIUM
        assert len(rec.evidence) == 4

    def test_high_confidence_above_20_errors(self) -> None:
        errors = [{"type": "E", "service": "svc", "severity": "info"}] * 21
        rec = self.analyzer.analyze(errors)
        assert rec.confidence == ConfidenceLevel.HIGH

    def test_critical_severity_sets_risk_critical(self) -> None:
        errors = [{"type": "E", "service": "svc", "severity": "critical"}]
        rec = self.analyzer.analyze(errors)
        assert rec.risk_level == "critical"

    def test_medium_risk_for_few_errors(self) -> None:
        errors = [{"type": "E", "service": "svc", "severity": "info"}] * 3
        rec = self.analyzer.analyze(errors)
        assert rec.risk_level == "medium"

    def test_high_risk_above_50_errors(self) -> None:
        errors = [{"type": "E", "service": "svc", "severity": "info"}] * 51
        rec = self.analyzer.analyze(errors)
        assert rec.risk_level == "high"

    def test_patterns_by_type(self) -> None:
        errors = [
            {"type": "IOError", "service": "svc1", "severity": "info"},
            {"type": "IOError", "service": "svc2", "severity": "info"},
            {"type": "TypeError", "service": "svc1", "severity": "info"},
        ]
        rec = self.analyzer.analyze(errors)
        assert "IOError" in rec.title

    def test_patterns_by_service(self) -> None:
        errors = [
            {"type": "E", "service": "api", "severity": "info"},
            {"type": "E", "service": "api", "severity": "info"},
            {"type": "E", "service": "db", "severity": "info"},
        ]
        rec = self.analyzer.analyze(errors)
        assert "api" in rec.summary


# ---------------------------------------------------------------------------
# 3. TestRootCauseAnalyzer
# ---------------------------------------------------------------------------
class TestRootCauseAnalyzer:
    def setup_method(self) -> None:
        self.analyzer = RootCauseAnalyzer()

    def test_no_symptoms(self) -> None:
        rec = self.analyzer.analyze({})
        assert "No significant issues" in rec.title
        assert rec.risk_level == "medium"

    def test_high_error_rate(self) -> None:
        rec = self.analyzer.analyze({"error_rate": 10})
        assert "High error rate" in rec.title
        assert "Error rate: 10%" in rec.evidence

    def test_slow_response(self) -> None:
        rec = self.analyzer.analyze({"avg_response_ms": 2000})
        assert "Slow response" in rec.title
        assert "Avg response: 2000ms" in rec.evidence

    def test_high_disk(self) -> None:
        rec = self.analyzer.analyze({"disk_usage": 90})
        assert "High disk usage" in rec.title

    def test_high_memory(self) -> None:
        rec = self.analyzer.analyze({"memory_usage": 90})
        assert "High memory usage" in rec.title

    def test_brute_force_logins(self) -> None:
        rec = self.analyzer.analyze({"failed_logins": 100})
        assert "Brute force attack" in rec.title
        assert "Failed logins: 100" in rec.evidence

    def test_multiple_causes_high_confidence(self) -> None:
        symptoms = {
            "error_rate": 10,
            "avg_response_ms": 3000,
            "disk_usage": 90,
            "memory_usage": 90,
        }
        rec = self.analyzer.analyze(symptoms)
        assert rec.confidence == ConfidenceLevel.HIGH
        assert rec.risk_level == "high"
        assert len(rec.evidence) >= 4

    def test_single_cause_medium_confidence(self) -> None:
        rec = self.analyzer.analyze({"error_rate": 7})
        assert rec.confidence == ConfidenceLevel.MEDIUM
        assert rec.risk_level == "medium"


# ---------------------------------------------------------------------------
# 4. TestLogAnalyzer
# ---------------------------------------------------------------------------
class TestLogAnalyzer:
    def setup_method(self) -> None:
        self.analyzer = LogAnalyzer()

    def test_empty_logs(self) -> None:
        rec = self.analyzer.analyze([])
        assert rec.recommendation_id == "LA-000"
        assert "No logs" in rec.title

    def test_logs_with_errors(self) -> None:
        logs = [
            {"level": "error", "message": "Connection failed"},
            {"level": "error", "message": "Timeout"},
            {"level": "info", "message": "Started"},
        ]
        rec = self.analyzer.analyze(logs)
        assert "2" in rec.title
        assert rec.confidence == ConfidenceLevel.HIGH

    def test_logs_with_warnings(self) -> None:
        logs = [
            {"level": "warning", "message": "Disk high"},
            {"level": "info", "message": "OK"},
        ]
        rec = self.analyzer.analyze(logs)
        assert "1 warnings" in rec.title

    def test_most_common_message_pattern(self) -> None:
        logs = [
            {"level": "info", "message": "heartbeat"},
            {"level": "info", "message": "heartbeat"},
            {"level": "info", "message": "heartbeat"},
            {"level": "info", "message": "other"},
        ]
        rec = self.analyzer.analyze(logs)
        assert "heartbeat" in rec.explanation

    def test_critical_included_in_error_count(self) -> None:
        logs = [
            {"level": "critical", "message": "Fatal crash"},
            {"level": "error", "message": "Failure"},
            {"level": "info", "message": "OK"},
        ]
        rec = self.analyzer.analyze(logs)
        assert "2" in rec.title

    def test_high_risk_above_10_errors(self) -> None:
        logs = [{"level": "error", "message": "err"}] * 11
        rec = self.analyzer.analyze(logs)
        assert rec.risk_level == "high"


# ---------------------------------------------------------------------------
# 5. TestPerformanceRecommender
# ---------------------------------------------------------------------------
class TestPerformanceRecommender:
    def setup_method(self) -> None:
        self.analyzer = PerformanceRecommender()

    def test_all_normal(self) -> None:
        rec = self.analyzer.analyze({"avg_query_ms": 10, "avg_api_response_ms": 50})
        assert "within normal" in rec.suggested_actions[0].lower()
        assert "acceptable" in rec.evidence[0].lower()
        assert rec.risk_level == "low"

    def test_slow_queries(self) -> None:
        rec = self.analyzer.analyze({"avg_query_ms": 200})
        assert any("index" in a.lower() for a in rec.suggested_actions)
        assert "Avg query time: 200ms" in rec.evidence

    def test_slow_api(self) -> None:
        rec = self.analyzer.analyze({"avg_api_response_ms": 1000})
        assert any("caching" in a.lower() for a in rec.suggested_actions)

    def test_high_p95(self) -> None:
        rec = self.analyzer.analyze({"p95_response_ms": 5000})
        assert any("slowest" in a.lower() or "optimize" in a.lower() for a in rec.suggested_actions)

    def test_low_cache_hit_rate(self) -> None:
        rec = self.analyzer.analyze({"cache_hit_rate": 0.5})
        assert any("cache" in a.lower() for a in rec.suggested_actions)
        assert "50.0%" in rec.evidence[0]

    def test_low_throughput(self) -> None:
        rec = self.analyzer.analyze({"throughput_per_sec": 20})
        assert any("connection pooling" in a.lower() for a in rec.suggested_actions)

    def test_zero_throughput_ignored(self) -> None:
        rec = self.analyzer.analyze({"throughput_per_sec": 0})
        assert any("normal" in a.lower() or "acceptable" in a.lower() for a in rec.suggested_actions)

    def test_multiple_recommendations_high_risk(self) -> None:
        rec = self.analyzer.analyze({
            "avg_query_ms": 200,
            "avg_api_response_ms": 1000,
            "p95_response_ms": 5000,
            "cache_hit_rate": 0.3,
        })
        assert len(rec.suggested_actions) > 2
        assert rec.risk_level == "medium"


# ---------------------------------------------------------------------------
# 6. TestSecurityRecommender
# ---------------------------------------------------------------------------
class TestSecurityRecommender:
    def setup_method(self) -> None:
        self.analyzer = SecurityRecommender()

    def test_all_secure(self) -> None:
        rec = self.analyzer.analyze({
            "mfa_enabled": True,
            "audit_chain_valid": True,
            "known_vulnerabilities": 0,
        })
        assert "acceptable" in rec.suggested_actions[0].lower()
        assert "passed" in rec.evidence[0].lower()
        assert rec.risk_level == "medium"

    def test_failed_logins(self) -> None:
        rec = self.analyzer.analyze({"failed_logins_24h": 30})
        assert any("lockout" in a.lower() for a in rec.suggested_actions)

    def test_vulnerabilities(self) -> None:
        rec = self.analyzer.analyze({"known_vulnerabilities": 3})
        assert rec.risk_level == "critical"
        assert any("patch" in a.lower() for a in rec.suggested_actions)

    def test_mfa_disabled(self) -> None:
        rec = self.analyzer.analyze({"mfa_enabled": False})
        assert any("multi-factor" in a.lower() for a in rec.suggested_actions)

    def test_audit_chain_invalid(self) -> None:
        rec = self.analyzer.analyze({"audit_chain_valid": False})
        assert rec.risk_level == "critical"
        assert any("audit" in a.lower() for a in rec.suggested_actions)

    def test_old_passwords(self) -> None:
        rec = self.analyzer.analyze({"max_password_age_days": 120})
        assert any("rotation" in a.lower() for a in rec.suggested_actions)

    def test_high_risk_for_failed_logins_above_50(self) -> None:
        rec = self.analyzer.analyze({"failed_logins_24h": 60})
        assert rec.risk_level == "high"


# ---------------------------------------------------------------------------
# 7. TestBackupRecommender
# ---------------------------------------------------------------------------
class TestBackupRecommender:
    def setup_method(self) -> None:
        self.analyzer = BackupRecommender()

    def test_all_healthy(self) -> None:
        rec = self.analyzer.analyze({
            "last_backup_hours_ago": 2,
            "backup_success_rate": 100,
            "retention_compliant": True,
            "total_backups": 30,
        })
        assert "acceptable" in rec.suggested_actions[0].lower()
        assert "passed" in rec.evidence[0].lower()

    def test_overdue_backup(self) -> None:
        rec = self.analyzer.analyze({"last_backup_hours_ago": 30})
        assert any("immediately" in a.lower() for a in rec.suggested_actions)
        assert "30" in rec.evidence[0]

    def test_low_success_rate(self) -> None:
        rec = self.analyzer.analyze({"backup_success_rate": 80})
        assert any("failures" in a.lower() for a in rec.suggested_actions)

    def test_non_compliant_retention(self) -> None:
        rec = self.analyzer.analyze({"retention_compliant": False})
        assert any("retention" in a.lower() for a in rec.suggested_actions)

    def test_few_backups(self) -> None:
        rec = self.analyzer.analyze({"total_backups": 3})
        assert any("frequency" in a.lower() for a in rec.suggested_actions)

    def test_high_risk_overdue_48h(self) -> None:
        rec = self.analyzer.analyze({"last_backup_hours_ago": 50})
        assert rec.risk_level == "high"

    def test_medium_risk_overdue_24h(self) -> None:
        rec = self.analyzer.analyze({"last_backup_hours_ago": 30})
        assert rec.risk_level == "medium"


# ---------------------------------------------------------------------------
# 8. TestRecoveryRecommender
# ---------------------------------------------------------------------------
class TestRecoveryRecommender:
    def setup_method(self) -> None:
        self.analyzer = RecoveryRecommender()

    def test_all_good(self) -> None:
        rec = self.analyzer.analyze({
            "last_recovery_test_hours_ago": 24,
            "recovery_test_success": True,
            "recovery_time_seconds": 60,
            "backup_integrity_valid": True,
        })
        assert "acceptable" in rec.suggested_actions[0].lower()
        assert "passed" in rec.evidence[0].lower()

    def test_overdue_test(self) -> None:
        rec = self.analyzer.analyze({"last_recovery_test_hours_ago": 200})
        assert any("immediately" in a.lower() for a in rec.suggested_actions)

    def test_failed_test(self) -> None:
        rec = self.analyzer.analyze({"recovery_test_success": False})
        assert rec.risk_level == "critical"
        assert any("fix" in a.lower() or "failures" in a.lower() for a in rec.suggested_actions)

    def test_slow_recovery(self) -> None:
        rec = self.analyzer.analyze({"recovery_time_seconds": 500})
        assert any("optimize" in a.lower() for a in rec.suggested_actions)

    def test_invalid_integrity(self) -> None:
        rec = self.analyzer.analyze({"backup_integrity_valid": False})
        assert rec.risk_level == "critical"
        assert any("integrity" in a.lower() for a in rec.suggested_actions)

    def test_multiple_issues(self) -> None:
        rec = self.analyzer.analyze({
            "last_recovery_test_hours_ago": 200,
            "recovery_test_success": False,
            "recovery_time_seconds": 400,
            "backup_integrity_valid": False,
        })
        assert len(rec.suggested_actions) >= 4


# ---------------------------------------------------------------------------
# 9. TestCapacityPlanner
# ---------------------------------------------------------------------------
class TestCapacityPlanner:
    def setup_method(self) -> None:
        self.analyzer = CapacityPlanner()

    def test_all_normal(self) -> None:
        rec = self.analyzer.analyze({
            "disk_usage_percent": 30,
            "database_size_gb": 1,
            "concurrent_users": 10,
            "max_user_capacity": 100,
        })
        assert "acceptable" in rec.suggested_actions[0].lower()
        assert "normal" in rec.evidence[0].lower()

    def test_high_disk(self) -> None:
        rec = self.analyzer.analyze({
            "disk_usage_percent": 80,
            "disk_total_gb": 100,
            "disk_growth_rate_gb_per_day": 1,
        })
        assert any("storage" in a.lower() for a in rec.suggested_actions)

    def test_large_database(self) -> None:
        rec = self.analyzer.analyze({
            "database_size_gb": 10,
            "db_growth_rate_gb_per_day": 0.5,
        })
        assert any("archival" in a.lower() for a in rec.suggested_actions)

    def test_high_user_load(self) -> None:
        rec = self.analyzer.analyze({
            "concurrent_users": 80,
            "max_user_capacity": 100,
        })
        assert any("scaling" in a.lower() for a in rec.suggested_actions)

    def test_high_risk_disk_above_85(self) -> None:
        rec = self.analyzer.analyze({"disk_usage_percent": 90})
        assert rec.risk_level == "high"

    def test_medium_risk_disk_below_85(self) -> None:
        rec = self.analyzer.analyze({"disk_usage_percent": 80})
        assert rec.risk_level == "medium"


# ---------------------------------------------------------------------------
# 10. TestRiskPredictor
# ---------------------------------------------------------------------------
class TestRiskPredictor:
    def setup_method(self) -> None:
        self.analyzer = RiskPredictor()

    def test_no_risks(self) -> None:
        rec = self.analyzer.analyze({})
        assert "All risk indicators within normal ranges" in rec.evidence[0]
        assert rec.risk_level == "medium"
        assert rec.suggested_actions == []

    def test_high_error_rate(self) -> None:
        rec = self.analyzer.analyze({"error_rate": 10})
        assert any("System instability" in a for a in rec.suggested_actions)
        assert "Error rate: 10%" in rec.evidence

    def test_disk_full(self) -> None:
        rec = self.analyzer.analyze({"disk_usage_percent": 90})
        assert any("Storage exhaustion" in a for a in rec.suggested_actions)

    def test_backup_overdue(self) -> None:
        rec = self.analyzer.analyze({"last_backup_hours_ago": 60})
        assert any("Data loss" in a for a in rec.suggested_actions)

    def test_sync_backlog(self) -> None:
        rec = self.analyzer.analyze({"sync_pending_items": 200})
        assert any("Sync backlog" in a for a in rec.suggested_actions)

    def test_failed_logins(self) -> None:
        rec = self.analyzer.analyze({"failed_logins_24h": 100})
        assert any("Security breach" in a for a in rec.suggested_actions)

    def test_multiple_risks_critical_level(self) -> None:
        rec = self.analyzer.analyze({
            "error_rate": 10,
            "disk_usage_percent": 90,
            "last_backup_hours_ago": 60,
            "sync_pending_items": 200,
        })
        assert len(rec.evidence) > 3
        assert rec.risk_level == "critical"

    def test_medium_risk_single_issue(self) -> None:
        rec = self.analyzer.analyze({"error_rate": 10})
        assert rec.risk_level == "medium"

    def test_high_risk_two_issues(self) -> None:
        rec = self.analyzer.analyze({"error_rate": 10, "disk_usage_percent": 90})
        assert rec.risk_level == "high"


# ---------------------------------------------------------------------------
# 11. TestAIAssistant
# ---------------------------------------------------------------------------
class TestAIAssistant:
    def setup_method(self) -> None:
        self.assistant = AIAssistant()

    def test_analyze_errors(self) -> None:
        rec = self.assistant.analyze_errors([{"type": "E", "service": "s", "severity": "info"}])
        assert rec.type == AIRecommendationType.ERROR_ANALYSIS

    def test_analyze_root_cause(self) -> None:
        rec = self.assistant.analyze_root_cause({"error_rate": 10})
        assert rec.type == AIRecommendationType.ROOT_CAUSE

    def test_analyze_logs(self) -> None:
        rec = self.assistant.analyze_logs([{"level": "error", "message": "fail"}])
        assert rec.type == AIRecommendationType.LOG_ANALYSIS

    def test_analyze_performance(self) -> None:
        rec = self.assistant.analyze_performance({"avg_query_ms": 200})
        assert rec.type == AIRecommendationType.PERFORMANCE

    def test_analyze_security(self) -> None:
        rec = self.assistant.analyze_security({"failed_logins_24h": 30})
        assert rec.type == AIRecommendationType.SECURITY

    def test_analyze_backup(self) -> None:
        rec = self.assistant.analyze_backup({"last_backup_hours_ago": 30})
        assert rec.type == AIRecommendationType.BACKUP

    def test_analyze_recovery(self) -> None:
        rec = self.assistant.analyze_recovery({"recovery_test_success": False})
        assert rec.type == AIRecommendationType.RECOVERY

    def test_analyze_capacity(self) -> None:
        rec = self.assistant.analyze_capacity({"disk_usage_percent": 80})
        assert rec.type == AIRecommendationType.CAPACITY

    def test_analyze_risks(self) -> None:
        rec = self.assistant.analyze_risks({"error_rate": 10})
        assert rec.type == AIRecommendationType.RISK_PREDICTION

    def test_full_analysis_empty(self) -> None:
        report = self.assistant.full_analysis()
        assert report.recommendations  # root cause + risk always run
        assert report.summary
        assert len(self.assistant._history) == 1

    def test_full_analysis_with_all_inputs(self) -> None:
        report = self.assistant.full_analysis(
            errors=[{"type": "E", "service": "s", "severity": "critical"}],
            logs=[{"level": "error", "message": "fail"}],
            performance_metrics={"avg_query_ms": 200},
            security_metrics={"failed_logins_24h": 30},
            backup_metrics={"last_backup_hours_ago": 30},
            recovery_metrics={"recovery_test_success": False},
            capacity_metrics={"disk_usage_percent": 80},
        )
        assert len(report.recommendations) >= 9

    def test_full_analysis_summary_critical(self) -> None:
        report = self.assistant.full_analysis(
            security_metrics={"audit_chain_valid": False, "known_vulnerabilities": 1},
        )
        assert report.overall_risk == "critical"
        assert report.critical_count > 0
        assert "CRITICAL" in report.summary

    def test_full_analysis_summary_high(self) -> None:
        report = self.assistant.full_analysis(
            security_metrics={"failed_logins_24h": 100},
        )
        assert "HIGH" in report.summary

    def test_get_recommendations_by_type(self) -> None:
        self.assistant.full_analysis(
            errors=[{"type": "E", "service": "s", "severity": "info"}],
        )
        recs = self.assistant.get_recommendations_by_type(AIRecommendationType.ERROR_ANALYSIS)
        assert len(recs) == 1

    def test_get_recommendations_by_type_no_history(self) -> None:
        recs = self.assistant.get_recommendations_by_type(AIRecommendationType.ERROR_ANALYSIS)
        assert recs == []

    def test_get_critical_recommendations(self) -> None:
        self.assistant.full_analysis(
            security_metrics={"audit_chain_valid": False, "known_vulnerabilities": 1},
        )
        critical = self.assistant.get_critical_recommendations()
        assert len(critical) >= 1
        assert all(r.risk_level == "critical" for r in critical)

    def test_get_critical_recommendations_no_history(self) -> None:
        assert self.assistant.get_critical_recommendations() == []

    def test_get_history(self) -> None:
        self.assistant.full_analysis()
        self.assistant.full_analysis()
        history = self.assistant.get_history(limit=1)
        assert len(history) == 1

    def test_get_history_all(self) -> None:
        self.assistant.full_analysis()
        self.assistant.full_analysis()
        history = self.assistant.get_history()
        assert len(history) == 2

    def test_get_dashboard_data_empty(self) -> None:
        data = self.assistant.get_dashboard_data()
        assert data == {"status": "no_data"}

    def test_get_dashboard_data_populated(self) -> None:
        self.assistant.full_analysis(
            errors=[{"type": "E", "service": "s", "severity": "info"}],
        )
        data = self.assistant.get_dashboard_data()
        assert "overall_risk" in data
        assert "critical_count" in data
        assert "high_count" in data
        assert "medium_count" in data
        assert "total_recommendations" in data
        assert "summary" in data
        assert "timestamp" in data
        assert isinstance(data["total_recommendations"], int)

    def test_ai_analysis_report_counts(self) -> None:
        recs = [
            AIRecommendation(
                recommendation_id="1",
                type=AIRecommendationType.ERROR_ANALYSIS,
                title="a",
                summary="b",
                explanation="c",
                risk_level="critical",
            ),
            AIRecommendation(
                recommendation_id="2",
                type=AIRecommendationType.SECURITY,
                title="a",
                summary="b",
                explanation="c",
                risk_level="high",
            ),
            AIRecommendation(
                recommendation_id="3",
                type=AIRecommendationType.BACKUP,
                title="a",
                summary="b",
                explanation="c",
                risk_level="high",
            ),
            AIRecommendation(
                recommendation_id="4",
                type=AIRecommendationType.PERFORMANCE,
                title="a",
                summary="b",
                explanation="c",
                risk_level="medium",
            ),
        ]
        report = AIAnalysisReport(recommendations=recs)
        assert report.critical_count == 1
        assert report.high_count == 2
        assert report.medium_count == 1
        assert report.overall_risk == "critical"

    def test_ai_analysis_report_overall_risk_high(self) -> None:
        recs = [
            AIRecommendation(
                recommendation_id="1",
                type=AIRecommendationType.ERROR_ANALYSIS,
                title="a",
                summary="b",
                explanation="c",
                risk_level="high",
            ),
        ]
        report = AIAnalysisReport(recommendations=recs)
        assert report.overall_risk == "high"
        assert report.critical_count == 0
        assert report.high_count == 1

    def test_ai_analysis_report_overall_risk_medium(self) -> None:
        recs = [
            AIRecommendation(
                recommendation_id="1",
                type=AIRecommendationType.BACKUP,
                title="a",
                summary="b",
                explanation="c",
                risk_level="medium",
            ),
        ]
        report = AIAnalysisReport(recommendations=recs)
        assert report.overall_risk == "medium"

    def test_ai_analysis_report_overall_risk_low(self) -> None:
        report = AIAnalysisReport(recommendations=[])
        assert report.overall_risk == "low"
