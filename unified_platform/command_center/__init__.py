"""
Platform Command Center — National Health Command Center

Phase 7: National Health Command Center
Constitution: Principle 19 (Observability First), Principle 24 (Continuous Architecture Evolution)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class HealthDomain(Enum):
    SYSTEM = "system"
    SECURITY = "security"
    OPERATIONAL = "operational"
    WORKFORCE = "workforce"
    LABORATORY = "laboratory"
    SYNC = "sync"
    BACKUP = "backup"


class HealthStatus(Enum):
    OPTIMAL = "optimal"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ALERT = "alert"
    EMERGENCY = "emergency"


@dataclass
class HealthIndicator:
    indicator_id: str
    domain: HealthDomain
    name: str
    value: float
    threshold_warning: float
    threshold_critical: float
    status: HealthStatus = HealthStatus.HEALTHY
    last_checked: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CommandAlert:
    alert_id: str
    level: AlertLevel
    domain: HealthDomain
    title: str
    description: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    resolved: bool = False


_STATUS_PRIORITY: dict[HealthStatus, int] = {
    HealthStatus.OPTIMAL: 5,
    HealthStatus.HEALTHY: 4,
    HealthStatus.DEGRADED: 2,
    HealthStatus.CRITICAL: 1,
    HealthStatus.OFFLINE: 0,
}


class NationalHealthCommandCenter:
    def __init__(self) -> None:
        self._indicators: dict[str, HealthIndicator] = {}
        self._alerts: dict[str, CommandAlert] = {}

    def register_indicator(self, indicator: HealthIndicator) -> None:
        self._indicators[indicator.indicator_id] = indicator

    def update_indicator(self, indicator_id: str, value: float) -> bool:
        indicator = self._indicators.get(indicator_id)
        if indicator is None:
            return False
        indicator.value = value
        indicator.last_checked = datetime.utcnow()
        if value >= indicator.threshold_critical:
            indicator.status = HealthStatus.CRITICAL
        elif value >= indicator.threshold_warning:
            indicator.status = HealthStatus.DEGRADED
        else:
            indicator.status = HealthStatus.HEALTHY
        return True

    def get_indicator(self, indicator_id: str) -> HealthIndicator | None:
        return self._indicators.get(indicator_id)

    def list_indicators(self, domain: HealthDomain | None = None) -> list[HealthIndicator]:
        indicators = list(self._indicators.values())
        if domain is not None:
            indicators = [i for i in indicators if i.domain == domain]
        return indicators

    def get_domain_health(self, domain: HealthDomain) -> HealthStatus:
        domain_indicators = self.list_indicators(domain=domain)
        if not domain_indicators:
            return HealthStatus.OFFLINE
        worst = min(domain_indicators, key=lambda i: _STATUS_PRIORITY.get(i.status, -1))
        return worst.status

    def get_overall_health(self) -> HealthStatus:
        all_indicators = list(self._indicators.values())
        if not all_indicators:
            return HealthStatus.OFFLINE
        worst = min(all_indicators, key=lambda i: _STATUS_PRIORITY.get(i.status, -1))
        return worst.status

    def create_alert(self, alert: CommandAlert) -> None:
        self._alerts[alert.alert_id] = alert

    def acknowledge_alert(self, alert_id: str) -> bool:
        alert = self._alerts.get(alert_id)
        if alert is None:
            return False
        alert.acknowledged = True
        return True

    def resolve_alert(self, alert_id: str) -> bool:
        alert = self._alerts.get(alert_id)
        if alert is None:
            return False
        alert.resolved = True
        return True

    def list_alerts(
        self,
        level: AlertLevel | None = None,
        domain: HealthDomain | None = None,
        unresolved_only: bool = False,
    ) -> list[CommandAlert]:
        alerts = list(self._alerts.values())
        if level is not None:
            alerts = [a for a in alerts if a.level == level]
        if domain is not None:
            alerts = [a for a in alerts if a.domain == domain]
        if unresolved_only:
            alerts = [a for a in alerts if not a.resolved]
        return alerts

    def get_command_center_report(self) -> dict[str, Any]:
        domain_health: dict[str, str] = {}
        for domain in HealthDomain:
            domain_health[domain.value] = self.get_domain_health(domain).value

        all_indicators = list(self._indicators.values())
        status_counts: dict[str, int] = {}
        for indicator in all_indicators:
            key = indicator.status.value
            status_counts[key] = status_counts.get(key, 0) + 1

        all_alerts = list(self._alerts.values())
        unresolved = [a for a in all_alerts if not a.resolved]
        return {
            "overall_health": self.get_overall_health().value,
            "domain_health": domain_health,
            "total_indicators": len(all_indicators),
            "indicator_status_counts": status_counts,
            "total_alerts": len(all_alerts),
            "unresolved_alerts": len(unresolved),
            "alert_levels": {
                level.value: len([a for a in all_alerts if a.level == level])
                for level in AlertLevel
            },
        }
