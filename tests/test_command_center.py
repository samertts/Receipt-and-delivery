"""
Tests for National Health Command Center — Phase 7
"""

from __future__ import annotations

from unified_platform.command_center import (
    AlertLevel,
    CommandAlert,
    HealthDomain,
    HealthIndicator,
    HealthStatus,
    NationalHealthCommandCenter,
)


class TestHealthIndicatorStatus:
    def setup_method(self) -> None:
        self.center = NationalHealthCommandCenter()

    def test_register_and_get_indicator(self) -> None:
        indicator = HealthIndicator(
            indicator_id="cpu-001",
            domain=HealthDomain.SYSTEM,
            name="CPU Usage",
            value=50.0,
            threshold_warning=70.0,
            threshold_critical=90.0,
        )
        self.center.register_indicator(indicator)
        result = self.center.get_indicator("cpu-001")
        assert result is not None
        assert result.indicator_id == "cpu-001"
        assert result.name == "CPU Usage"

    def test_update_indicator_healthy(self) -> None:
        indicator = HealthIndicator(
            indicator_id="mem-001",
            domain=HealthDomain.SYSTEM,
            name="Memory",
            value=30.0,
            threshold_warning=70.0,
            threshold_critical=90.0,
        )
        self.center.register_indicator(indicator)
        updated = self.center.update_indicator("mem-001", 40.0)
        assert updated is True
        result = self.center.get_indicator("mem-001")
        assert result is not None
        assert result.value == 40.0
        assert result.status == HealthStatus.HEALTHY

    def test_update_indicator_degraded(self) -> None:
        indicator = HealthIndicator(
            indicator_id="disk-001",
            domain=HealthDomain.SYSTEM,
            name="Disk",
            value=30.0,
            threshold_warning=70.0,
            threshold_critical=90.0,
        )
        self.center.register_indicator(indicator)
        self.center.update_indicator("disk-001", 75.0)
        result = self.center.get_indicator("disk-001")
        assert result is not None
        assert result.status == HealthStatus.DEGRADED

    def test_update_indicator_critical(self) -> None:
        indicator = HealthIndicator(
            indicator_id="net-001",
            domain=HealthDomain.SYNC,
            name="Network",
            value=20.0,
            threshold_warning=70.0,
            threshold_critical=90.0,
        )
        self.center.register_indicator(indicator)
        self.center.update_indicator("net-001", 95.0)
        result = self.center.get_indicator("net-001")
        assert result is not None
        assert result.status == HealthStatus.CRITICAL

    def test_update_nonexistent_returns_false(self) -> None:
        assert self.center.update_indicator("missing", 50.0) is False

    def test_list_indicators_by_domain(self) -> None:
        self.center.register_indicator(HealthIndicator(
            indicator_id="s1", domain=HealthDomain.SYSTEM, name="S1", value=1.0,
            threshold_warning=5.0, threshold_critical=9.0,
        ))
        self.center.register_indicator(HealthIndicator(
            indicator_id="sec1", domain=HealthDomain.SECURITY, name="Sec1", value=1.0,
            threshold_warning=5.0, threshold_critical=9.0,
        ))
        system = self.center.list_indicators(domain=HealthDomain.SYSTEM)
        assert len(system) == 1
        assert system[0].domain == HealthDomain.SYSTEM


class TestDomainHealth:
    def setup_method(self) -> None:
        self.center = NationalHealthCommandCenter()

    def test_domain_health_with_critical(self) -> None:
        self.center.register_indicator(HealthIndicator(
            indicator_id="a", domain=HealthDomain.BACKUP, name="A", value=10.0,
            threshold_warning=30.0, threshold_critical=50.0,
        ))
        self.center.register_indicator(HealthIndicator(
            indicator_id="b", domain=HealthDomain.BACKUP, name="B", value=10.0,
            threshold_warning=30.0, threshold_critical=50.0,
        ))
        self.center.update_indicator("b", 55.0)
        assert self.center.get_domain_health(HealthDomain.BACKUP) == HealthStatus.CRITICAL

    def test_domain_health_empty(self) -> None:
        assert self.center.get_domain_health(HealthDomain.LABORATORY) == HealthStatus.OFFLINE

    def test_overall_health(self) -> None:
        assert self.center.get_overall_health() == HealthStatus.OFFLINE
        self.center.register_indicator(HealthIndicator(
            indicator_id="x", domain=HealthDomain.SYSTEM, name="X", value=10.0,
            threshold_warning=30.0, threshold_critical=50.0,
        ))
        assert self.center.get_overall_health() == HealthStatus.HEALTHY


class TestCommandAlerts:
    def setup_method(self) -> None:
        self.center = NationalHealthCommandCenter()

    def test_create_and_acknowledge_alert(self) -> None:
        alert = CommandAlert(
            alert_id="alert-001",
            level=AlertLevel.WARNING,
            domain=HealthDomain.SECURITY,
            title="Suspicious activity",
            description="Multiple failed logins detected",
        )
        self.center.create_alert(alert)
        assert self.center.acknowledge_alert("alert-001") is True
        alerts = self.center.list_alerts()
        assert len(alerts) == 1
        assert alerts[0].acknowledged is True

    def test_resolve_alert(self) -> None:
        alert = CommandAlert(
            alert_id="alert-002",
            level=AlertLevel.ALERT,
            domain=HealthDomain.SYSTEM,
            title="CPU spike",
            description="CPU usage exceeded threshold",
        )
        self.center.create_alert(alert)
        assert self.center.resolve_alert("alert-002") is True
        alerts = self.center.list_alerts(unresolved_only=True)
        assert len(alerts) == 0

    def test_acknowledge_nonexistent_returns_false(self) -> None:
        assert self.center.acknowledge_alert("missing") is False

    def test_resolve_nonexistent_returns_false(self) -> None:
        assert self.center.resolve_alert("missing") is False

    def test_list_alerts_filtered(self) -> None:
        self.center.create_alert(CommandAlert(
            alert_id="a1", level=AlertLevel.INFO, domain=HealthDomain.SYSTEM,
            title="A1", description="Info alert",
        ))
        self.center.create_alert(CommandAlert(
            alert_id="a2", level=AlertLevel.EMERGENCY, domain=HealthDomain.SECURITY,
            title="A2", description="Emergency alert",
        ))
        assert len(self.center.list_alerts(level=AlertLevel.INFO)) == 1
        assert len(self.center.list_alerts(domain=HealthDomain.SECURITY)) == 1

    def test_command_center_report(self) -> None:
        self.center.register_indicator(HealthIndicator(
            indicator_id="r1", domain=HealthDomain.SYNC, name="R1", value=10.0,
            threshold_warning=30.0, threshold_critical=50.0,
        ))
        self.center.create_alert(CommandAlert(
            alert_id="ra1", level=AlertLevel.WARNING, domain=HealthDomain.SYNC,
            title="RA1", description="Sync warning",
        ))
        report = self.center.get_command_center_report()
        assert report["overall_health"] == HealthStatus.HEALTHY.value
        assert report["total_indicators"] == 1
        assert report["total_alerts"] == 1
        assert report["domain_health"]["sync"] == HealthStatus.HEALTHY.value
