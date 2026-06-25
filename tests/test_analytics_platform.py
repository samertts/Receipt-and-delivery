"""
Tests for National Analytics Platform — Phase 6

Covers: KPITrend, KPIData, DashboardType, Dashboard, TrendData,
        AnalyticsEngine.
"""

from __future__ import annotations

from datetime import datetime

from unified_platform.analytics import (
    AnalyticsEngine,
    Dashboard,
    DashboardType,
    KPIData,
    KPITrend,
    TrendData,
)


# ---------------------------------------------------------------------------
# 1. TestKPITrend
# ---------------------------------------------------------------------------
class TestKPITrend:
    def test_enum_values(self) -> None:
        assert KPITrend.IMPROVING.value == "improving"
        assert KPITrend.STABLE.value == "stable"
        assert KPITrend.DECLINING.value == "declining"
        assert KPITrend.CRITICAL.value == "critical"

    def test_all_members(self) -> None:
        assert len(KPITrend) == 4


# ---------------------------------------------------------------------------
# 2. TestKPIData
# ---------------------------------------------------------------------------
class TestKPIData:
    def test_creation(self) -> None:
        kpi = KPIData(
            kpi_id="KPI-1",
            name="Uptime",
            value=99.5,
            target=99.0,
            unit="%",
            trend=KPITrend.IMPROVING,
            period="2024-Q1",
        )
        assert kpi.kpi_id == "KPI-1"
        assert kpi.value == 99.5
        assert kpi.target == 99.0
        assert kpi.trend == KPITrend.IMPROVING


# ---------------------------------------------------------------------------
# 3. TestDashboardType
# ---------------------------------------------------------------------------
class TestDashboardType:
    def test_enum_values(self) -> None:
        assert DashboardType.EXECUTIVE.value == "executive"
        assert DashboardType.PROVINCE.value == "province"
        assert DashboardType.ORGANIZATION.value == "organization"
        assert DashboardType.OPERATIONAL.value == "operational"

    def test_all_members(self) -> None:
        assert len(DashboardType) == 4


# ---------------------------------------------------------------------------
# 4. TestDashboard
# ---------------------------------------------------------------------------
class TestDashboard:
    def test_creation_with_defaults(self) -> None:
        dash = Dashboard(
            dashboard_id="D-1",
            dashboard_type=DashboardType.EXECUTIVE,
            title="Executive",
        )
        assert dash.dashboard_id == "D-1"
        assert dash.kpis == []
        assert isinstance(dash.generated_at, datetime)
        assert dash.refresh_interval_seconds == 300

    def test_creation_with_kpis(self) -> None:
        kpi = KPIData("K1", "Uptime", 99.5, 99.0, "%", KPITrend.STABLE, "Q1")
        dash = Dashboard(
            dashboard_id="D-2",
            dashboard_type=DashboardType.PROVINCE,
            title="Province",
            kpis=[kpi],
            refresh_interval_seconds=60,
        )
        assert len(dash.kpis) == 1
        assert dash.refresh_interval_seconds == 60


# ---------------------------------------------------------------------------
# 5. TestTrendData
# ---------------------------------------------------------------------------
class TestTrendData:
    def test_creation_with_defaults(self) -> None:
        trend = TrendData(metric_name="cpu")
        assert trend.metric_name == "cpu"
        assert trend.values == []
        assert trend.timestamps == []
        assert trend.trend == KPITrend.STABLE
        assert trend.change_percent == 0.0

    def test_creation_with_all_fields(self) -> None:
        trend = TrendData(
            metric_name="cpu",
            values=[10.0, 20.0],
            timestamps=["t1", "t2"],
            trend=KPITrend.IMPROVING,
            change_percent=100.0,
        )
        assert trend.values == [10.0, 20.0]
        assert trend.change_percent == 100.0


# ---------------------------------------------------------------------------
# 6. TestAnalyticsEngine — KPI Registration
# ---------------------------------------------------------------------------
class TestAnalyticsEngineKPIs:
    def setup_method(self) -> None:
        self.engine = AnalyticsEngine()

    def test_register_kpi(self) -> None:
        kpi = KPIData("K1", "Uptime", 99.5, 99.0, "%", KPITrend.STABLE, "Q1")
        self.engine.register_kpi(kpi)
        assert self.engine.get_kpi("K1") == kpi

    def test_get_kpi_not_found(self) -> None:
        assert self.engine.get_kpi("NONEXISTENT") is None

    def test_list_kpis_empty(self) -> None:
        assert self.engine.list_kpis() == []

    def test_list_kpis_multiple(self) -> None:
        self.engine.register_kpi(KPIData("K1", "Uptime", 99.5, 99.0, "%", KPITrend.STABLE, "Q1"))
        self.engine.register_kpi(KPIData("K2", "Latency", 45, 50, "ms", KPITrend.IMPROVING, "Q1"))
        assert len(self.engine.list_kpis()) == 2

    def test_register_overwrites(self) -> None:
        self.engine.register_kpi(KPIData("K1", "Uptime", 99.5, 99.0, "%", KPITrend.STABLE, "Q1"))
        self.engine.register_kpi(KPIData("K1", "Uptime", 99.8, 99.0, "%", KPITrend.IMPROVING, "Q2"))
        kpi = self.engine.get_kpi("K1")
        assert kpi is not None
        assert kpi.value == 99.8


# ---------------------------------------------------------------------------
# 7. TestAnalyticsEngine — Trend Calculation
# ---------------------------------------------------------------------------
class TestAnalyticsEngineTrends:
    def setup_method(self) -> None:
        self.engine = AnalyticsEngine()

    def test_empty_values(self) -> None:
        trend = self.engine.calculate_trend("cpu", [], [])
        assert trend.trend == KPITrend.STABLE
        assert trend.change_percent == 0.0

    def test_single_value(self) -> None:
        trend = self.engine.calculate_trend("cpu", [50.0], ["t1"])
        assert trend.trend == KPITrend.STABLE
        assert trend.change_percent == 0.0

    def test_stable_trend(self) -> None:
        trend = self.engine.calculate_trend("cpu", [100.0, 102.0], ["t1", "t2"])
        assert trend.trend == KPITrend.STABLE
        assert abs(trend.change_percent - 2.0) < 0.01

    def test_improving_trend(self) -> None:
        trend = self.engine.calculate_trend("cpu", [100.0, 110.0], ["t1", "t2"])
        assert trend.trend == KPITrend.IMPROVING
        assert trend.change_percent == 10.0

    def test_declining_trend(self) -> None:
        trend = self.engine.calculate_trend("cpu", [100.0, 90.0], ["t1", "t2"])
        assert trend.trend == KPITrend.DECLINING
        assert trend.change_percent == -10.0

    def test_critical_trend(self) -> None:
        trend = self.engine.calculate_trend("cpu", [100.0, 70.0], ["t1", "t2"])
        assert trend.trend == KPITrend.CRITICAL
        assert trend.change_percent == -30.0

    def test_zero_start_positive(self) -> None:
        trend = self.engine.calculate_trend("cpu", [0.0, 5.0], ["t1", "t2"])
        assert trend.change_percent == 100.0

    def test_zero_start_zero_end(self) -> None:
        trend = self.engine.calculate_trend("cpu", [0.0, 0.0], ["t1", "t2"])
        assert trend.change_percent == 0.0
        assert trend.trend == KPITrend.STABLE


# ---------------------------------------------------------------------------
# 8. TestAnalyticsEngine — Dashboard Generation
# ---------------------------------------------------------------------------
class TestAnalyticsEngineDashboards:
    def setup_method(self) -> None:
        self.engine = AnalyticsEngine()
        self.engine.register_kpi(KPIData("K1", "Uptime", 99.5, 99.0, "%", KPITrend.STABLE, "Q1"))
        self.engine.register_kpi(KPIData("K2", "Latency", 45, 50, "ms", KPITrend.IMPROVING, "Q1"))

    def test_generate_dashboard(self) -> None:
        dash = self.engine.generate_dashboard(
            DashboardType.EXECUTIVE, "Executive Summary", ["K1", "K2"]
        )
        assert dash.dashboard_type == DashboardType.EXECUTIVE
        assert dash.title == "Executive Summary"
        assert len(dash.kpis) == 2
        assert dash.dashboard_id.startswith("DASH-")

    def test_dashboard_id_increments(self) -> None:
        d1 = self.engine.generate_dashboard(DashboardType.EXECUTIVE, "D1", ["K1"])
        d2 = self.engine.generate_dashboard(DashboardType.PROVINCE, "D2", ["K2"])
        assert d1.dashboard_id == "DASH-0001"
        assert d2.dashboard_id == "DASH-0002"

    def test_dashboard_filters_invalid_kpi_ids(self) -> None:
        dash = self.engine.generate_dashboard(
            DashboardType.OPERATIONAL, "Ops", ["K1", "NONEXISTENT"]
        )
        assert len(dash.kpis) == 1

    def test_empty_kpi_list(self) -> None:
        dash = self.engine.generate_dashboard(DashboardType.EXECUTIVE, "Empty", [])
        assert len(dash.kpis) == 0


# ---------------------------------------------------------------------------
# 9. TestAnalyticsEngine — Executive Summary
# ---------------------------------------------------------------------------
class TestAnalyticsEngineExecutiveSummary:
    def setup_method(self) -> None:
        self.engine = AnalyticsEngine()

    def test_empty_kpis(self) -> None:
        summary = self.engine.get_executive_summary()
        assert summary["total_kpis"] == 0
        assert "No KPIs" in summary["summary"]

    def test_all_on_target(self) -> None:
        self.engine.register_kpi(KPIData("K1", "Uptime", 99.5, 99.0, "%", KPITrend.IMPROVING, "Q1"))
        self.engine.register_kpi(KPIData("K2", "Revenue", 150, 100, "k", KPITrend.IMPROVING, "Q1"))
        summary = self.engine.get_executive_summary()
        assert summary["on_target"] == 2
        assert summary["off_target"] == 0
        assert summary["health_score"] == 100.0

    def test_mixed_performance(self) -> None:
        self.engine.register_kpi(KPIData("K1", "Uptime", 99.5, 99.0, "%", KPITrend.IMPROVING, "Q1"))
        self.engine.register_kpi(KPIData("K2", "Revenue", 40, 100, "k", KPITrend.DECLINING, "Q1"))
        summary = self.engine.get_executive_summary()
        assert summary["on_target"] == 1
        assert summary["off_target"] == 1

    def test_critical_kpis(self) -> None:
        self.engine.register_kpi(KPIData("K1", "Uptime", 80.0, 99.0, "%", KPITrend.CRITICAL, "Q1"))
        self.engine.register_kpi(KPIData("K2", "Latency", 200, 50, "ms", KPITrend.CRITICAL, "Q1"))
        summary = self.engine.get_executive_summary()
        assert summary["critical_count"] == 2


# ---------------------------------------------------------------------------
# 10. TestAnalyticsEngine — Province & Organization Summaries
# ---------------------------------------------------------------------------
class TestAnalyticsEngineSummaries:
    def setup_method(self) -> None:
        self.engine = AnalyticsEngine()

    def test_province_summary_empty(self) -> None:
        summary = self.engine.get_province_summary("PROV-001")
        assert summary["province_id"] == "PROV-001"
        assert summary["kpi_count"] == 0

    def test_province_summary_with_matching_kpis(self) -> None:
        self.engine.register_kpi(KPIData("PROV-001-upt", "Uptime", 99.5, 99.0, "%", KPITrend.STABLE, "Q1"))
        self.engine.register_kpi(KPIData("PROV-002-lat", "Latency", 45, 50, "ms", KPITrend.IMPROVING, "Q1"))
        summary = self.engine.get_province_summary("PROV-001")
        assert summary["kpi_count"] == 1

    def test_organization_summary_empty(self) -> None:
        summary = self.engine.get_organization_summary("ORG-001")
        assert summary["org_id"] == "ORG-001"
        assert summary["kpi_count"] == 0

    def test_organization_summary_with_matching_kpis(self) -> None:
        self.engine.register_kpi(KPIData("ORG-001-upt", "Uptime", 99.5, 99.0, "%", KPITrend.STABLE, "Q1"))
        self.engine.register_kpi(KPIData("ORG-002-lat", "Latency", 45, 50, "ms", KPITrend.IMPROVING, "Q1"))
        summary = self.engine.get_organization_summary("ORG-001")
        assert summary["kpi_count"] == 1


# ---------------------------------------------------------------------------
# 11. TestAnalyticsEngine — Analytics Report
# ---------------------------------------------------------------------------
class TestAnalyticsEngineReport:
    def setup_method(self) -> None:
        self.engine = AnalyticsEngine()

    def test_report_empty(self) -> None:
        report = self.engine.get_analytics_report()
        assert report["report_type"] == "analytics_summary"
        assert "generated_at" in report
        assert report["total_dashboards"] == 0
        assert report["executive_summary"]["total_kpis"] == 0

    def test_report_with_data(self) -> None:
        self.engine.register_kpi(KPIData("K1", "Uptime", 99.5, 99.0, "%", KPITrend.STABLE, "Q1"))
        self.engine.generate_dashboard(DashboardType.EXECUTIVE, "Exec", ["K1"])
        report = self.engine.get_analytics_report()
        assert report["total_dashboards"] == 1
        assert report["executive_summary"]["total_kpis"] == 1
