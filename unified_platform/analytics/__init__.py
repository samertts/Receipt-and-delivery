"""
National Analytics Platform

Phase 6: National Analytics Platform
Constitution: Principle 12 (Shared Data Contracts), Principle 13 (National Platform)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class KPITrend(Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    CRITICAL = "critical"


@dataclass
class KPIData:
    """Key Performance Indicator data."""
    kpi_id: str
    name: str
    value: float
    target: float
    unit: str
    trend: KPITrend
    period: str


class DashboardType(Enum):
    EXECUTIVE = "executive"
    PROVINCE = "province"
    ORGANIZATION = "organization"
    OPERATIONAL = "operational"


@dataclass
class Dashboard:
    """Dashboard with KPIs."""
    dashboard_id: str
    dashboard_type: DashboardType
    title: str
    kpis: list[KPIData] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)
    refresh_interval_seconds: int = 300


@dataclass
class TrendData:
    """Trend analysis data for a metric."""
    metric_name: str
    values: list[float] = field(default_factory=list)
    timestamps: list[str] = field(default_factory=list)
    trend: KPITrend = KPITrend.STABLE
    change_percent: float = 0.0


class AnalyticsEngine:
    """National analytics engine for KPI tracking and dashboards."""

    def __init__(self) -> None:
        self._kpis: dict[str, KPIData] = {}
        self._dashboards: list[Dashboard] = []

    def register_kpi(self, kpi: KPIData) -> None:
        self._kpis[kpi.kpi_id] = kpi

    def get_kpi(self, kpi_id: str) -> KPIData | None:
        return self._kpis.get(kpi_id)

    def list_kpis(self) -> list[KPIData]:
        return list(self._kpis.values())

    def calculate_trend(
        self,
        metric_name: str,
        values: list[float],
        timestamps: list[str],
    ) -> TrendData:
        if len(values) < 2:
            return TrendData(
                metric_name=metric_name,
                values=values,
                timestamps=timestamps,
                trend=KPITrend.STABLE,
                change_percent=0.0,
            )

        first = values[0]
        last = values[-1]
        if first == 0:
            change_percent = 100.0 if last > 0 else 0.0
        else:
            change_percent = ((last - first) / first) * 100

        if change_percent > 5.0:
            trend = KPITrend.IMPROVING
        elif change_percent < -5.0:
            if change_percent < -20.0:
                trend = KPITrend.CRITICAL
            else:
                trend = KPITrend.DECLINING
        else:
            trend = KPITrend.STABLE

        return TrendData(
            metric_name=metric_name,
            values=values,
            timestamps=timestamps,
            trend=trend,
            change_percent=change_percent,
        )

    def generate_dashboard(
        self,
        dashboard_type: DashboardType,
        title: str,
        kpi_ids: list[str],
    ) -> Dashboard:
        kpis = [self._kpis[kid] for kid in kpi_ids if kid in self._kpis]
        dashboard = Dashboard(
            dashboard_id=f"DASH-{len(self._dashboards) + 1:04d}",
            dashboard_type=dashboard_type,
            title=title,
            kpis=kpis,
        )
        self._dashboards.append(dashboard)
        return dashboard

    def get_executive_summary(self) -> dict[str, Any]:
        kpis = self.list_kpis()
        if not kpis:
            return {"total_kpis": 0, "summary": "No KPIs registered"}

        on_target = sum(1 for k in kpis if k.value >= k.target)
        critical = sum(1 for k in kpis if k.trend == KPITrend.CRITICAL)
        improving = sum(1 for k in kpis if k.trend == KPITrend.IMPROVING)

        return {
            "total_kpis": len(kpis),
            "on_target": on_target,
            "off_target": len(kpis) - on_target,
            "critical_count": critical,
            "improving_count": improving,
            "health_score": round((on_target / len(kpis)) * 100, 1) if kpis else 0.0,
        }

    def get_province_summary(self, province_id: str) -> dict[str, Any]:
        province_kpis = [
            k for k in self._kpis.values()
            if province_id in k.kpi_id
        ]
        return {
            "province_id": province_id,
            "kpi_count": len(province_kpis),
            "kpis": [
                {"name": k.name, "value": k.value, "target": k.target, "trend": k.trend.value}
                for k in province_kpis
            ],
        }

    def get_organization_summary(self, org_id: str) -> dict[str, Any]:
        org_kpis = [
            k for k in self._kpis.values()
            if org_id in k.kpi_id
        ]
        return {
            "org_id": org_id,
            "kpi_count": len(org_kpis),
            "kpis": [
                {"name": k.name, "value": k.value, "target": k.target, "trend": k.trend.value}
                for k in org_kpis
            ],
        }

    def get_analytics_report(self) -> dict[str, Any]:
        summary = self.get_executive_summary()
        return {
            "report_type": "analytics_summary",
            "generated_at": datetime.utcnow().isoformat(),
            "total_dashboards": len(self._dashboards),
            "executive_summary": summary,
        }
