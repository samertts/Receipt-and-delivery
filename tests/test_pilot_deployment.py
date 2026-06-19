"""Tests for unified_platform.pilot — PilotDeploymentManager and related classes."""

from __future__ import annotations

from datetime import datetime


from unified_platform.pilot import (
    PilotDeployment,
    PilotDeploymentManager,
    PilotMetric,
    PilotPhase,
)


class TestPilotMetric:
    def test_creation(self):
        m = PilotMetric(name="latency", target=200.0, actual=180.0, unit="ms")
        assert m.name == "latency"
        assert m.target == 200.0
        assert m.actual == 180.0
        assert m.unit == "ms"
        assert m.status == "pending"

    def test_to_dict(self):
        m = PilotMetric(name="uptime", target=99.9, actual=99.5, unit="%", status="on_track")
        d = m.to_dict()
        assert d == {
            "name": "uptime",
            "target": 99.9,
            "actual": 99.5,
            "unit": "%",
            "status": "on_track",
        }

    def test_status_default(self):
        m = PilotMetric(name="err", target=0.0, actual=0.0, unit="count")
        assert m.status == "pending"


class TestPilotDeployment:
    def test_creation_with_defaults(self):
        p = PilotDeployment(pilot_id="p1", name="Alpha")
        assert p.pilot_id == "p1"
        assert p.name == "Alpha"
        assert p.phase == PilotPhase.PLANNING
        assert isinstance(p.start_date, datetime)
        assert p.end_date is None
        assert p.metrics == []
        assert p.users_enrolled == 0
        assert p.users_active == 0
        assert p.error_rate == 0.0
        assert p.satisfaction_score == 0.0

    def test_to_dict(self):
        m = PilotMetric(name="cpu", target=80.0, actual=70.0, unit="%")
        p = PilotDeployment(pilot_id="p2", name="Beta", metrics=[m], users_enrolled=50, users_active=40)
        d = p.to_dict()
        assert d["pilot_id"] == "p2"
        assert d["name"] == "Beta"
        assert d["phase"] == "planning"
        assert len(d["metrics"]) == 1
        assert d["users_enrolled"] == 50
        assert d["users_active"] == 40


class TestPilotDeploymentManager:
    def test_create_pilot(self):
        mgr = PilotDeploymentManager()
        pilot = mgr.create_pilot("p1", "Pilot Alpha")
        assert pilot.pilot_id == "p1"
        assert pilot.name == "Pilot Alpha"
        assert pilot.phase == PilotPhase.PLANNING

    def test_get_pilot(self):
        mgr = PilotDeploymentManager()
        mgr.create_pilot("p1", "Alpha")
        found = mgr.get_pilot("p1")
        assert found is not None
        assert found.pilot_id == "p1"

    def test_get_pilot_nonexistent(self):
        mgr = PilotDeploymentManager()
        assert mgr.get_pilot("missing") is None

    def test_list_pilots_empty(self):
        mgr = PilotDeploymentManager()
        assert mgr.list_pilots() == []

    def test_list_pilots_multiple(self):
        mgr = PilotDeploymentManager()
        mgr.create_pilot("p1", "Alpha")
        mgr.create_pilot("p2", "Beta")
        pilots = mgr.list_pilots()
        assert len(pilots) == 2
        ids = {p.pilot_id for p in pilots}
        assert ids == {"p1", "p2"}

    def test_add_metric(self):
        mgr = PilotDeploymentManager()
        mgr.create_pilot("p1", "Alpha")
        metric = PilotMetric(name="rt", target=100.0, actual=95.0, unit="ms")
        result = mgr.add_metric("p1", metric)
        assert result is True
        assert len(mgr.get_pilot("p1").metrics) == 1

    def test_add_metric_nonexistent(self):
        mgr = PilotDeploymentManager()
        metric = PilotMetric(name="rt", target=100.0, actual=95.0, unit="ms")
        result = mgr.add_metric("missing", metric)
        assert result is False

    def test_update_phase(self):
        mgr = PilotDeploymentManager()
        mgr.create_pilot("p1", "Alpha")
        assert mgr.update_phase("p1", PilotPhase.DEPLOYMENT) is True
        assert mgr.get_pilot("p1").phase == PilotPhase.DEPLOYMENT

    def test_update_phase_completed_sets_end_date(self):
        mgr = PilotDeploymentManager()
        mgr.create_pilot("p1", "Alpha")
        assert mgr.get_pilot("p1").end_date is None
        mgr.update_phase("p1", PilotPhase.COMPLETED)
        assert mgr.get_pilot("p1").end_date is not None

    def test_record_adoption(self):
        mgr = PilotDeploymentManager()
        mgr.create_pilot("p1", "Alpha")
        assert mgr.record_adoption("p1", enrolled=100, active=80) is True
        p = mgr.get_pilot("p1")
        assert p.users_enrolled == 100
        assert p.users_active == 80

    def test_record_satisfaction(self):
        mgr = PilotDeploymentManager()
        mgr.create_pilot("p1", "Alpha")
        assert mgr.record_satisfaction("p1", score=4.5) is True
        assert mgr.get_pilot("p1").satisfaction_score == 4.5

    def test_get_pilot_report(self):
        mgr = PilotDeploymentManager()
        mgr.create_pilot("p1", "Alpha")
        mgr.record_adoption("p1", enrolled=50, active=40)
        mgr.record_satisfaction("p1", score=4.2)
        m1 = PilotMetric(name="a", target=10.0, actual=9.0, unit="ms", status="on_track")
        m2 = PilotMetric(name="b", target=5.0, actual=3.0, unit="ms", status="at_risk")
        mgr.add_metric("p1", m1)
        mgr.add_metric("p1", m2)

        report = mgr.get_pilot_report("p1")
        assert report["pilot_id"] == "p1"
        assert report["name"] == "Alpha"
        assert report["adoption_rate"] == 80.0
        assert report["satisfaction_score"] == 4.2
        assert report["metrics_summary"]["total_metrics"] == 2
        assert report["metrics_summary"]["metrics_on_track"] == 1
        assert report["metrics_summary"]["metrics_at_risk"] == 1

    def test_get_pilot_report_nonexistent(self):
        mgr = PilotDeploymentManager()
        report = mgr.get_pilot_report("missing")
        assert "error" in report

    def test_get_readiness_report_empty(self):
        mgr = PilotDeploymentManager()
        report = mgr.get_readiness_report()
        assert report["total_pilots"] == 0
        assert report["readiness"] == "not_ready"

    def test_get_readiness_report_with_pilots(self):
        mgr = PilotDeploymentManager()
        mgr.create_pilot("p1", "Alpha")
        mgr.record_adoption("p1", enrolled=10, active=8)
        mgr.record_satisfaction("p1", score=4.0)
        mgr.create_pilot("p2", "Beta")
        mgr.record_adoption("p2", enrolled=20, active=20)
        mgr.record_satisfaction("p2", score=5.0)
        mgr.update_phase("p2", PilotPhase.COMPLETED)

        report = mgr.get_readiness_report()
        assert report["total_pilots"] == 2
        assert report["total_users_enrolled"] == 30
        assert report["total_users_active"] == 28
        assert report["average_satisfaction"] == 4.5
        assert report["readiness"] == "in_progress"

    def test_readiness_all_completed(self):
        mgr = PilotDeploymentManager()
        mgr.create_pilot("p1", "Alpha")
        mgr.update_phase("p1", PilotPhase.COMPLETED)
        report = mgr.get_readiness_report()
        assert report["readiness"] == "ready"
