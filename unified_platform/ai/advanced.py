"""
Platform AI — Advanced Operational AI

Phase 5: Advanced Operational AI
Constitution: Principle 33 (AI Governance), Principle 34 (Explainable AI)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PredictionConfidence(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class PredictionResult:
    """A prediction result with confidence and evidence."""
    prediction_id: str
    prediction_type: str
    description: str
    confidence: PredictionConfidence
    predicted_at: datetime
    probability: float
    time_horizon_hours: int
    evidence: list[str] = field(default_factory=list)
    suggested_actions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class PredictiveFailureAnalyzer:
    """Analyzes metrics to predict potential system failures."""

    def analyze(self, metrics: dict[str, Any]) -> PredictionResult:
        evidence: list[str] = []
        issues: list[str] = []

        error_rate_trend = metrics.get("error_rate_trend", 0.0)
        if error_rate_trend > 0.1:
            issues.append(f"Error rate increasing at {error_rate_trend*100:.1f}%/hour")
            evidence.append(f"Error rate trend: {error_rate_trend*100:.1f}%/hour")

        response_time_degradation = metrics.get("response_time_degradation", 0.0)
        if response_time_degradation > 0.2:
            issues.append(f"Response time degrading at {response_time_degradation*100:.1f}%/hour")
            evidence.append(f"Response time degradation: {response_time_degradation*100:.1f}%/hour")

        disk_growth_rate = metrics.get("disk_growth_rate_gb_per_day", 0.0)
        if disk_growth_rate > 5.0:
            issues.append(f"Disk growing at {disk_growth_rate:.1f} GB/day")
            evidence.append(f"Disk growth rate: {disk_growth_rate:.1f} GB/day")

        memory_leak_patterns = metrics.get("memory_leak_patterns", 0)
        if memory_leak_patterns > 0:
            issues.append(f"Detected {memory_leak_patterns} memory leak pattern(s)")
            evidence.append(f"Memory leak patterns: {memory_leak_patterns}")

        if not issues:
            issues.append("No failure patterns detected")
            evidence.append("All failure indicators within normal ranges")

        probability = min(0.95, len(issues) * 0.2)
        confidence = (
            PredictionConfidence.VERY_HIGH if len(issues) >= 4
            else PredictionConfidence.HIGH if len(issues) >= 3
            else PredictionConfidence.MEDIUM if len(issues) >= 2
            else PredictionConfidence.LOW
        )

        return PredictionResult(
            prediction_id="PFA-001",
            prediction_type="failure_prediction",
            description=f"Failure analysis: {len(issues)} risk factors identified",
            confidence=confidence,
            predicted_at=datetime.utcnow(),
            probability=probability,
            time_horizon_hours=24,
            evidence=evidence,
            suggested_actions=[
                f"Investigate: {i}" for i in issues if "No failure" not in i
            ] or ["Continue monitoring"],
        )


class CapacityForecastingEngine:
    """Forecasts capacity needs based on current metrics."""

    def analyze(self, metrics: dict[str, Any]) -> PredictionResult:
        evidence: list[str] = []
        issues: list[str] = []

        disk_forecast_days = metrics.get("disk_forecast_days", 365)
        if disk_forecast_days < 30:
            issues.append(f"Disk full in {disk_forecast_days} days")
            evidence.append(f"Disk forecast: {disk_forecast_days} days to full")

        database_growth = metrics.get("database_growth_rate_gb_per_day", 0.0)
        if database_growth > 1.0:
            issues.append(f"Database growing at {database_growth:.1f} GB/day")
            evidence.append(f"DB growth: {database_growth:.1f} GB/day")

        user_growth = metrics.get("user_growth_rate_percent", 0.0)
        if user_growth > 10.0:
            issues.append(f"User base growing at {user_growth:.0f}%/month")
            evidence.append(f"User growth: {user_growth:.0f}%/month")

        concurrent_connections = metrics.get("concurrent_connections", 0)
        max_connections = metrics.get("max_connections", 100)
        if max_connections > 0 and concurrent_connections / max_connections > 0.7:
            issues.append(f"Connection pool at {concurrent_connections}/{max_connections}")
            evidence.append(f"Connections: {concurrent_connections}/{max_connections}")

        if not issues:
            issues.append("Capacity within acceptable limits")
            evidence.append("All capacity metrics normal")

        probability = min(0.95, len(issues) * 0.25)
        confidence = (
            PredictionConfidence.VERY_HIGH if len(issues) >= 3
            else PredictionConfidence.HIGH if len(issues) >= 2
            else PredictionConfidence.MEDIUM
        )

        return PredictionResult(
            prediction_id="CFE-001",
            prediction_type="capacity_forecast",
            description=f"Capacity forecast: {len(issues)} concerns identified",
            confidence=confidence,
            predicted_at=datetime.utcnow(),
            probability=probability,
            time_horizon_hours=72,
            evidence=evidence,
            suggested_actions=[
                f"Plan for: {i}" for i in issues if "within acceptable" not in i
            ] or ["Continue monitoring capacity"],
        )


class IncidentPredictor:
    """Predicts potential incidents based on system metrics."""

    def analyze(self, metrics: dict[str, Any]) -> PredictionResult:
        evidence: list[str] = []
        issues: list[str] = []

        error_rate = metrics.get("error_rate", 0.0)
        if error_rate > 5.0:
            issues.append(f"High error rate: {error_rate:.1f}%")
            evidence.append(f"Error rate: {error_rate:.1f}%")

        uptime_hours = metrics.get("uptime_hours", 0)
        if uptime_hours > 720:
            issues.append(f"System running {uptime_hours}h without restart")
            evidence.append(f"Uptime: {uptime_hours} hours")

        recent_incidents = metrics.get("recent_incidents", 0)
        if recent_incidents > 3:
            issues.append(f"{recent_incidents} incidents in last 24 hours")
            evidence.append(f"Recent incidents: {recent_incidents}")

        system_load = metrics.get("system_load", 0.0)
        if system_load > 0.9:
            issues.append(f"System load critically high: {system_load:.2f}")
            evidence.append(f"System load: {system_load:.2f}")

        if not issues:
            issues.append("No incident risks detected")
            evidence.append("All incident indicators within normal ranges")

        probability = min(0.95, len(issues) * 0.22)
        confidence = (
            PredictionConfidence.VERY_HIGH if len(issues) >= 3
            else PredictionConfidence.HIGH if len(issues) >= 2
            else PredictionConfidence.MEDIUM
        )

        return PredictionResult(
            prediction_id="IP-001",
            prediction_type="incident_prediction",
            description=f"Incident prediction: {len(issues)} risk factors",
            confidence=confidence,
            predicted_at=datetime.utcnow(),
            probability=probability,
            time_horizon_hours=12,
            evidence=evidence,
            suggested_actions=[
                f"Address: {i}" for i in issues if "No incident" not in i
            ] or ["Continue monitoring"],
        )


class SecurityRiskForecaster:
    """Forecasts security risks based on current indicators."""

    def analyze(self, metrics: dict[str, Any]) -> PredictionResult:
        evidence: list[str] = []
        issues: list[str] = []

        failed_logins_trend = metrics.get("failed_logins_trend", 0.0)
        if failed_logins_trend > 0.15:
            issues.append(f"Failed logins increasing at {failed_logins_trend*100:.0f}%/hour")
            evidence.append(f"Failed login trend: {failed_logins_trend*100:.0f}%/hour")

        vulnerability_count = metrics.get("vulnerability_count", 0)
        if vulnerability_count > 0:
            issues.append(f"{vulnerability_count} known vulnerabilities")
            evidence.append(f"Vulnerabilities: {vulnerability_count}")

        patch_age_days = metrics.get("patch_age_days", 0)
        if patch_age_days > 30:
            issues.append(f"Patches {patch_age_days} days overdue")
            evidence.append(f"Patch age: {patch_age_days} days")

        access_pattern_anomaly = metrics.get("access_pattern_anomaly", 0.0)
        if access_pattern_anomaly > 0.5:
            issues.append(f"Access pattern anomaly score: {access_pattern_anomaly:.2f}")
            evidence.append(f"Access anomaly: {access_pattern_anomaly:.2f}")

        if not issues:
            issues.append("No security risks forecasted")
            evidence.append("All security indicators within normal ranges")

        probability = min(0.95, len(issues) * 0.25)
        confidence = (
            PredictionConfidence.VERY_HIGH if len(issues) >= 3
            else PredictionConfidence.HIGH if len(issues) >= 2
            else PredictionConfidence.MEDIUM
        )

        return PredictionResult(
            prediction_id="SRF-001",
            prediction_type="security_risk_forecast",
            description=f"Security forecast: {len(issues)} risks identified",
            confidence=confidence,
            predicted_at=datetime.utcnow(),
            probability=probability,
            time_horizon_hours=48,
            evidence=evidence,
            suggested_actions=[
                f"Mitigate: {i}" for i in issues if "No security" not in i
            ] or ["Continue security monitoring"],
        )


class SyncRiskForecaster:
    """Forecasts synchronization risks."""

    def analyze(self, metrics: dict[str, Any]) -> PredictionResult:
        evidence: list[str] = []
        issues: list[str] = []

        sync_failure_rate = metrics.get("sync_failure_rate", 0.0)
        if sync_failure_rate > 0.05:
            issues.append(f"Sync failure rate: {sync_failure_rate*100:.1f}%")
            evidence.append(f"Sync failure rate: {sync_failure_rate*100:.1f}%")

        sync_lag_minutes = metrics.get("sync_lag_minutes", 0)
        if sync_lag_minutes > 30:
            issues.append(f"Sync lag: {sync_lag_minutes} minutes")
            evidence.append(f"Sync lag: {sync_lag_minutes} minutes")

        pending_items = metrics.get("pending_items", 0)
        if pending_items > 500:
            issues.append(f"{pending_items} items pending sync")
            evidence.append(f"Pending items: {pending_items}")

        conflict_rate = metrics.get("conflict_rate", 0.0)
        if conflict_rate > 0.1:
            issues.append(f"Conflict rate: {conflict_rate*100:.1f}%")
            evidence.append(f"Conflict rate: {conflict_rate*100:.1f}%")

        if not issues:
            issues.append("No sync risks detected")
            evidence.append("All sync indicators within normal ranges")

        probability = min(0.95, len(issues) * 0.25)
        confidence = (
            PredictionConfidence.VERY_HIGH if len(issues) >= 3
            else PredictionConfidence.HIGH if len(issues) >= 2
            else PredictionConfidence.MEDIUM
        )

        return PredictionResult(
            prediction_id="SRF-002",
            prediction_type="sync_risk_forecast",
            description=f"Sync risk forecast: {len(issues)} concerns",
            confidence=confidence,
            predicted_at=datetime.utcnow(),
            probability=probability,
            time_horizon_hours=24,
            evidence=evidence,
            suggested_actions=[
                f"Address: {i}" for i in issues if "No sync" not in i
            ] or ["Continue sync monitoring"],
        )


class InfrastructureRecommender:
    """Generates infrastructure recommendations based on metrics."""

    def analyze(self, metrics: dict[str, Any]) -> PredictionResult:
        evidence: list[str] = []
        issues: list[str] = []

        cpu_usage = metrics.get("cpu_usage", 0.0)
        if cpu_usage > 80.0:
            issues.append(f"CPU usage high: {cpu_usage:.1f}%")
            evidence.append(f"CPU: {cpu_usage:.1f}%")

        memory_usage = metrics.get("memory_usage", 0.0)
        if memory_usage > 80.0:
            issues.append(f"Memory usage high: {memory_usage:.1f}%")
            evidence.append(f"Memory: {memory_usage:.1f}%")

        disk_iops = metrics.get("disk_iops", 0)
        if disk_iops > 10000:
            issues.append(f"Disk IOPS elevated: {disk_iops}")
            evidence.append(f"Disk IOPS: {disk_iops}")

        network_latency = metrics.get("network_latency_ms", 0)
        if network_latency > 100:
            issues.append(f"Network latency high: {network_latency}ms")
            evidence.append(f"Network latency: {network_latency}ms")

        connection_pool_usage = metrics.get("connection_pool_usage", 0.0)
        if connection_pool_usage > 0.8:
            issues.append(f"Connection pool at {connection_pool_usage*100:.0f}%")
            evidence.append(f"Connection pool: {connection_pool_usage*100:.0f}%")

        if not issues:
            issues.append("Infrastructure within acceptable limits")
            evidence.append("All infrastructure metrics normal")

        probability = min(0.95, len(issues) * 0.2)
        confidence = (
            PredictionConfidence.VERY_HIGH if len(issues) >= 4
            else PredictionConfidence.HIGH if len(issues) >= 3
            else PredictionConfidence.MEDIUM if len(issues) >= 2
            else PredictionConfidence.LOW
        )

        return PredictionResult(
            prediction_id="IR-001",
            prediction_type="infrastructure_recommendation",
            description=f"Infrastructure recommendations: {len(issues)} items",
            confidence=confidence,
            predicted_at=datetime.utcnow(),
            probability=probability,
            time_horizon_hours=168,
            evidence=evidence,
            suggested_actions=[
                f"Optimize: {i}" for i in issues if "within acceptable" not in i
            ] or ["Continue infrastructure monitoring"],
        )


class AdvancedAIAssistant:
    """Advanced AI assistant with 6 prediction capabilities."""

    def __init__(self) -> None:
        self._failure_analyzer = PredictiveFailureAnalyzer()
        self._capacity_engine = CapacityForecastingEngine()
        self._incident_predictor = IncidentPredictor()
        self._security_forecaster = SecurityRiskForecaster()
        self._sync_forecaster = SyncRiskForecaster()
        self._infra_recommender = InfrastructureRecommender()
        self._history: list[PredictionResult] = []

    def predict_failures(self, metrics: dict[str, Any]) -> PredictionResult:
        result = self._failure_analyzer.analyze(metrics)
        self._history.append(result)
        return result

    def forecast_capacity(self, metrics: dict[str, Any]) -> PredictionResult:
        result = self._capacity_engine.analyze(metrics)
        self._history.append(result)
        return result

    def predict_incidents(self, metrics: dict[str, Any]) -> PredictionResult:
        result = self._incident_predictor.analyze(metrics)
        self._history.append(result)
        return result

    def forecast_security_risks(self, metrics: dict[str, Any]) -> PredictionResult:
        result = self._security_forecaster.analyze(metrics)
        self._history.append(result)
        return result

    def forecast_sync_risks(self, metrics: dict[str, Any]) -> PredictionResult:
        result = self._sync_forecaster.analyze(metrics)
        self._history.append(result)
        return result

    def get_infrastructure_recommendations(self, metrics: dict[str, Any]) -> PredictionResult:
        result = self._infra_recommender.analyze(metrics)
        self._history.append(result)
        return result

    def full_prediction(self, metrics: dict[str, Any]) -> list[PredictionResult]:
        results = [
            self.predict_failures(metrics),
            self.forecast_capacity(metrics),
            self.predict_incidents(metrics),
            self.forecast_security_risks(metrics),
            self.forecast_sync_risks(metrics),
            self.get_infrastructure_recommendations(metrics),
        ]
        return results

    def get_prediction_history(self) -> list[PredictionResult]:
        return list(self._history)
