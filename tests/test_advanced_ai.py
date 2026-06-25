"""
Tests for Advanced Operational AI — Phase 5

Covers: PredictionConfidence, PredictionResult, PredictiveFailureAnalyzer,
        CapacityForecastingEngine, IncidentPredictor, SecurityRiskForecaster,
        SyncRiskForecaster, InfrastructureRecommender, AdvancedAIAssistant.
"""

from __future__ import annotations

from datetime import datetime

from unified_platform.ai.advanced import (
    AdvancedAIAssistant,
    CapacityForecastingEngine,
    IncidentPredictor,
    InfrastructureRecommender,
    PredictionConfidence,
    PredictionResult,
    PredictiveFailureAnalyzer,
    SecurityRiskForecaster,
    SyncRiskForecaster,
)


# ---------------------------------------------------------------------------
# 1. TestPredictionConfidence
# ---------------------------------------------------------------------------
class TestPredictionConfidence:
    def test_enum_values(self) -> None:
        assert PredictionConfidence.LOW.value == "low"
        assert PredictionConfidence.MEDIUM.value == "medium"
        assert PredictionConfidence.HIGH.value == "high"
        assert PredictionConfidence.VERY_HIGH.value == "very_high"

    def test_all_members(self) -> None:
        assert len(PredictionConfidence) == 4


# ---------------------------------------------------------------------------
# 2. TestPredictionResult
# ---------------------------------------------------------------------------
class TestPredictionResult:
    def test_creation_with_defaults(self) -> None:
        result = PredictionResult(
            prediction_id="P-1",
            prediction_type="test",
            description="desc",
            confidence=PredictionConfidence.MEDIUM,
            predicted_at=datetime.utcnow(),
            probability=0.5,
            time_horizon_hours=24,
        )
        assert result.prediction_id == "P-1"
        assert result.evidence == []
        assert result.suggested_actions == []
        assert result.metadata == {}

    def test_creation_with_all_fields(self) -> None:
        result = PredictionResult(
            prediction_id="P-2",
            prediction_type="test",
            description="desc",
            confidence=PredictionConfidence.HIGH,
            predicted_at=datetime.utcnow(),
            probability=0.8,
            time_horizon_hours=48,
            evidence=["e1"],
            suggested_actions=["a1"],
            metadata={"k": "v"},
        )
        assert result.evidence == ["e1"]
        assert result.suggested_actions == ["a1"]
        assert result.metadata == {"k": "v"}


# ---------------------------------------------------------------------------
# 3. TestPredictiveFailureAnalyzer
# ---------------------------------------------------------------------------
class TestPredictiveFailureAnalyzer:
    def setup_method(self) -> None:
        self.analyzer = PredictiveFailureAnalyzer()

    def test_no_issues(self) -> None:
        result = self.analyzer.analyze({})
        assert result.prediction_id == "PFA-001"
        assert result.prediction_type == "failure_prediction"
        assert result.confidence == PredictionConfidence.LOW
        assert "All failure indicators" in result.evidence[0]

    def test_error_rate_trend(self) -> None:
        result = self.analyzer.analyze({"error_rate_trend": 0.15})
        assert result.confidence == PredictionConfidence.LOW
        assert any("Error rate trend" in e for e in result.evidence)

    def test_response_time_degradation(self) -> None:
        result = self.analyzer.analyze({"response_time_degradation": 0.25})
        assert any("Response time degradation" in e for e in result.evidence)

    def test_disk_growth_rate(self) -> None:
        result = self.analyzer.analyze({"disk_growth_rate_gb_per_day": 10.0})
        assert any("Disk growth rate" in e for e in result.evidence)

    def test_memory_leak_patterns(self) -> None:
        result = self.analyzer.analyze({"memory_leak_patterns": 3})
        assert any("Memory leak" in e for e in result.evidence)
        assert result.confidence == PredictionConfidence.LOW

    def test_all_issues_very_high_confidence(self) -> None:
        result = self.analyzer.analyze({
            "error_rate_trend": 0.15,
            "response_time_degradation": 0.25,
            "disk_growth_rate_gb_per_day": 10.0,
            "memory_leak_patterns": 2,
        })
        assert result.confidence == PredictionConfidence.VERY_HIGH
        assert result.probability > 0.5


# ---------------------------------------------------------------------------
# 4. TestCapacityForecastingEngine
# ---------------------------------------------------------------------------
class TestCapacityForecastingEngine:
    def setup_method(self) -> None:
        self.analyzer = CapacityForecastingEngine()

    def test_no_issues(self) -> None:
        result = self.analyzer.analyze({})
        assert result.prediction_type == "capacity_forecast"
        assert result.confidence == PredictionConfidence.MEDIUM
        assert "All capacity metrics normal" in result.evidence[0]

    def test_disk_forecast(self) -> None:
        result = self.analyzer.analyze({"disk_forecast_days": 15})
        assert any("Disk forecast" in e for e in result.evidence)

    def test_database_growth(self) -> None:
        result = self.analyzer.analyze({"database_growth_rate_gb_per_day": 2.0})
        assert any("DB growth" in e for e in result.evidence)

    def test_user_growth(self) -> None:
        result = self.analyzer.analyze({"user_growth_rate_percent": 15.0})
        assert any("User growth" in e for e in result.evidence)

    def test_high_connections(self) -> None:
        result = self.analyzer.analyze({
            "concurrent_connections": 80,
            "max_connections": 100,
        })
        assert any("Connections" in e for e in result.evidence)

    def test_multiple_issues_high_confidence(self) -> None:
        result = self.analyzer.analyze({
            "disk_forecast_days": 10,
            "database_growth_rate_gb_per_day": 3.0,
            "user_growth_rate_percent": 20.0,
        })
        assert result.confidence == PredictionConfidence.VERY_HIGH


# ---------------------------------------------------------------------------
# 5. TestIncidentPredictor
# ---------------------------------------------------------------------------
class TestIncidentPredictor:
    def setup_method(self) -> None:
        self.analyzer = IncidentPredictor()

    def test_no_issues(self) -> None:
        result = self.analyzer.analyze({})
        assert result.prediction_type == "incident_prediction"
        assert "All incident indicators" in result.evidence[0]

    def test_high_error_rate(self) -> None:
        result = self.analyzer.analyze({"error_rate": 8.0})
        assert any("Error rate" in e for e in result.evidence)

    def test_long_uptime(self) -> None:
        result = self.analyzer.analyze({"uptime_hours": 800})
        assert any("Uptime" in e for e in result.evidence)

    def test_many_recent_incidents(self) -> None:
        result = self.analyzer.analyze({"recent_incidents": 5})
        assert any("Recent incidents" in e for e in result.evidence)

    def test_high_system_load(self) -> None:
        result = self.analyzer.analyze({"system_load": 0.95})
        assert any("System load" in e for e in result.evidence)

    def test_multiple_factors_high_confidence(self) -> None:
        result = self.analyzer.analyze({
            "error_rate": 8.0,
            "recent_incidents": 5,
            "system_load": 0.95,
        })
        assert result.confidence == PredictionConfidence.VERY_HIGH


# ---------------------------------------------------------------------------
# 6. TestSecurityRiskForecaster
# ---------------------------------------------------------------------------
class TestSecurityRiskForecaster:
    def setup_method(self) -> None:
        self.analyzer = SecurityRiskForecaster()

    def test_no_issues(self) -> None:
        result = self.analyzer.analyze({})
        assert result.prediction_type == "security_risk_forecast"
        assert "All security indicators" in result.evidence[0]

    def test_failed_logins_trend(self) -> None:
        result = self.analyzer.analyze({"failed_logins_trend": 0.2})
        assert any("Failed login trend" in e for e in result.evidence)

    def test_vulnerabilities(self) -> None:
        result = self.analyzer.analyze({"vulnerability_count": 5})
        assert any("Vulnerabilities" in e for e in result.evidence)

    def test_old_patches(self) -> None:
        result = self.analyzer.analyze({"patch_age_days": 60})
        assert any("Patch age" in e for e in result.evidence)

    def test_access_anomaly(self) -> None:
        result = self.analyzer.analyze({"access_pattern_anomaly": 0.7})
        assert any("Access anomaly" in e for e in result.evidence)

    def test_all_security_risks(self) -> None:
        result = self.analyzer.analyze({
            "failed_logins_trend": 0.2,
            "vulnerability_count": 3,
            "patch_age_days": 45,
            "access_pattern_anomaly": 0.8,
        })
        assert result.confidence == PredictionConfidence.VERY_HIGH
        assert len(result.suggested_actions) == 4


# ---------------------------------------------------------------------------
# 7. TestSyncRiskForecaster
# ---------------------------------------------------------------------------
class TestSyncRiskForecaster:
    def setup_method(self) -> None:
        self.analyzer = SyncRiskForecaster()

    def test_no_issues(self) -> None:
        result = self.analyzer.analyze({})
        assert result.prediction_type == "sync_risk_forecast"
        assert "All sync indicators" in result.evidence[0]

    def test_sync_failure_rate(self) -> None:
        result = self.analyzer.analyze({"sync_failure_rate": 0.1})
        assert any("Sync failure rate" in e for e in result.evidence)

    def test_sync_lag(self) -> None:
        result = self.analyzer.analyze({"sync_lag_minutes": 45})
        assert any("Sync lag" in e for e in result.evidence)

    def test_pending_items(self) -> None:
        result = self.analyzer.analyze({"pending_items": 600})
        assert any("Pending items" in e for e in result.evidence)

    def test_conflict_rate(self) -> None:
        result = self.analyzer.analyze({"conflict_rate": 0.15})
        assert any("Conflict rate" in e for e in result.evidence)

    def test_all_sync_risks(self) -> None:
        result = self.analyzer.analyze({
            "sync_failure_rate": 0.1,
            "sync_lag_minutes": 45,
            "pending_items": 600,
            "conflict_rate": 0.15,
        })
        assert result.confidence == PredictionConfidence.VERY_HIGH


# ---------------------------------------------------------------------------
# 8. TestInfrastructureRecommender
# ---------------------------------------------------------------------------
class TestInfrastructureRecommender:
    def setup_method(self) -> None:
        self.analyzer = InfrastructureRecommender()

    def test_no_issues(self) -> None:
        result = self.analyzer.analyze({})
        assert result.prediction_type == "infrastructure_recommendation"
        assert "All infrastructure metrics normal" in result.evidence[0]

    def test_high_cpu(self) -> None:
        result = self.analyzer.analyze({"cpu_usage": 85.0})
        assert any("CPU" in e for e in result.evidence)

    def test_high_memory(self) -> None:
        result = self.analyzer.analyze({"memory_usage": 90.0})
        assert any("Memory" in e for e in result.evidence)

    def test_high_disk_iops(self) -> None:
        result = self.analyzer.analyze({"disk_iops": 15000})
        assert any("Disk IOPS" in e for e in result.evidence)

    def test_high_network_latency(self) -> None:
        result = self.analyzer.analyze({"network_latency_ms": 150})
        assert any("Network latency" in e for e in result.evidence)

    def test_connection_pool_full(self) -> None:
        result = self.analyzer.analyze({"connection_pool_usage": 0.9})
        assert any("Connection pool" in e for e in result.evidence)

    def test_all_infra_issues(self) -> None:
        result = self.analyzer.analyze({
            "cpu_usage": 85.0,
            "memory_usage": 90.0,
            "disk_iops": 15000,
            "network_latency_ms": 150,
            "connection_pool_usage": 0.9,
        })
        assert result.confidence == PredictionConfidence.VERY_HIGH
        assert len(result.suggested_actions) == 5


# ---------------------------------------------------------------------------
# 9. TestAdvancedAIAssistant
# ---------------------------------------------------------------------------
class TestAdvancedAIAssistant:
    def setup_method(self) -> None:
        self.assistant = AdvancedAIAssistant()

    def test_predict_failures(self) -> None:
        result = self.assistant.predict_failures({"error_rate_trend": 0.15})
        assert result.prediction_type == "failure_prediction"
        assert len(self.assistant.get_prediction_history()) == 1

    def test_forecast_capacity(self) -> None:
        result = self.assistant.forecast_capacity({"disk_forecast_days": 10})
        assert result.prediction_type == "capacity_forecast"
        assert len(self.assistant.get_prediction_history()) == 1

    def test_predict_incidents(self) -> None:
        result = self.assistant.predict_incidents({"error_rate": 8.0})
        assert result.prediction_type == "incident_prediction"

    def test_forecast_security_risks(self) -> None:
        result = self.assistant.forecast_security_risks({"vulnerability_count": 3})
        assert result.prediction_type == "security_risk_forecast"

    def test_forecast_sync_risks(self) -> None:
        result = self.assistant.forecast_sync_risks({"sync_lag_minutes": 45})
        assert result.prediction_type == "sync_risk_forecast"

    def test_get_infrastructure_recommendations(self) -> None:
        result = self.assistant.get_infrastructure_recommendations({"cpu_usage": 85.0})
        assert result.prediction_type == "infrastructure_recommendation"

    def test_full_prediction(self) -> None:
        results = self.assistant.full_prediction({
            "error_rate_trend": 0.15,
            "disk_forecast_days": 10,
            "error_rate": 8.0,
            "vulnerability_count": 3,
            "sync_lag_minutes": 45,
            "cpu_usage": 85.0,
        })
        assert len(results) == 6
        assert len(self.assistant.get_prediction_history()) == 6

    def test_get_prediction_history(self) -> None:
        self.assistant.predict_failures({})
        self.assistant.forecast_capacity({})
        history = self.assistant.get_prediction_history()
        assert len(history) == 2
        assert history[0].prediction_type == "failure_prediction"
        assert history[1].prediction_type == "capacity_forecast"

    def test_prediction_history_returns_copy(self) -> None:
        self.assistant.predict_failures({})
        history = self.assistant.get_prediction_history()
        history.clear()
        assert len(self.assistant.get_prediction_history()) == 1
