
from unified_platform.digital_twin import (
    SimulationEngine,
    SimulationParameter,
    SimulationStatus,
    SimulationType,
)


class TestEnums:
    def test_simulation_type_values(self):
        assert SimulationType.ORGANIZATION.value == "organization"
        assert SimulationType.WORKFORCE.value == "workforce"
        assert SimulationType.LABORATORY.value == "laboratory"
        assert SimulationType.CAPACITY.value == "capacity"

    def test_simulation_status_values(self):
        assert SimulationStatus.READY.value == "ready"
        assert SimulationStatus.RUNNING.value == "running"
        assert SimulationStatus.COMPLETED.value == "completed"
        assert SimulationStatus.FAILED.value == "failed"


class TestSimulationParameter:
    def test_defaults(self):
        p = SimulationParameter(name="throughput", value=100.0)
        assert p.unit == ""
        assert p.min_val == 0.0
        assert p.max_val == float("inf")

    def test_custom_values(self):
        p = SimulationParameter(name="latency", value=5.0, unit="ms", min_val=0.0, max_val=50.0)
        assert p.name == "latency"
        assert p.value == 5.0
        assert p.unit == "ms"
        assert p.max_val == 50.0


class TestSimulationEngine:
    def _make_engine(self):
        return SimulationEngine()

    def _params(self):
        return [SimulationParameter(name="staff", value=10.0)]

    def test_create_simulation(self):
        engine = self._make_engine()
        result = engine.create_simulation("sim-1", SimulationType.WORKFORCE, self._params())
        assert result.simulation_id == "sim-1"
        assert result.sim_type == SimulationType.WORKFORCE
        assert result.status == SimulationStatus.READY
        assert len(result.parameters) == 1

    def test_get_simulation(self):
        engine = self._make_engine()
        engine.create_simulation("sim-1", SimulationType.ORGANIZATION, self._params())
        found = engine.get_simulation("sim-1")
        assert found is not None
        assert found.simulation_id == "sim-1"

    def test_get_simulation_missing(self):
        engine = self._make_engine()
        assert engine.get_simulation("nonexistent") is None

    def test_run_simulation_success(self):
        engine = self._make_engine()
        engine.create_simulation("sim-1", SimulationType.CAPACITY, self._params())
        assert engine.run_simulation("sim-1") is True
        sim = engine.get_simulation("sim-1")
        assert sim.status == SimulationStatus.COMPLETED
        assert sim.results["efficiency_score"] == 0.87
        assert sim.duration_seconds == 1.23

    def test_run_simulation_not_ready(self):
        engine = self._make_engine()
        engine.create_simulation("sim-1", SimulationType.LABORATORY, self._params())
        engine.run_simulation("sim-1")
        assert engine.run_simulation("sim-1") is False

    def test_run_simulation_nonexistent(self):
        engine = self._make_engine()
        assert engine.run_simulation("nope") is False

    def test_list_simulations_all(self):
        engine = self._make_engine()
        engine.create_simulation("a", SimulationType.ORGANIZATION, [])
        engine.create_simulation("b", SimulationType.WORKFORCE, [])
        assert len(engine.list_simulations()) == 2

    def test_list_simulations_by_type(self):
        engine = self._make_engine()
        engine.create_simulation("a", SimulationType.ORGANIZATION, [])
        engine.create_simulation("b", SimulationType.WORKFORCE, [])
        org_sims = engine.list_simulations(SimulationType.ORGANIZATION)
        assert len(org_sims) == 1
        assert org_sims[0].simulation_id == "a"

    def test_readiness_report_empty(self):
        engine = self._make_engine()
        report = engine.get_readiness_report()
        assert report["total_simulations"] == 0
        assert report["by_status"]["ready"] == 0
        assert "organization" in report["by_type"]

    def test_readiness_report_populated(self):
        engine = self._make_engine()
        engine.create_simulation("s1", SimulationType.ORGANIZATION, [])
        engine.create_simulation("s2", SimulationType.ORGANIZATION, [])
        engine.run_simulation("s2")
        report = engine.get_readiness_report()
        assert report["total_simulations"] == 2
        assert report["by_type"]["organization"] == 2
        assert report["by_status"]["completed"] == 1

    def test_rerun_after_failure(self):
        engine = self._make_engine()
        engine.create_simulation("s1", SimulationType.CAPACITY, [])
        engine.run_simulation("s1")
        sim = engine.get_simulation("s1")
        sim.status = SimulationStatus.FAILED
        assert engine.run_simulation("s1") is True
        assert engine.get_simulation("s1").status == SimulationStatus.COMPLETED
