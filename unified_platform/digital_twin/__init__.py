"""
Platform Digital Twin — Simulation engine for organizational, workforce,
laboratory, and capacity modeling.

Phase 16: Digital Twin Readiness
Constitution: Principle 13 (National Platform Compatibility),
              Principle 24 (Continuous Architecture Evolution)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# ============================================================================
# Enums
# ============================================================================

class SimulationType(Enum):
    """Types of simulations supported by the digital twin engine."""
    ORGANIZATION = "organization"
    WORKFORCE = "workforce"
    LABORATORY = "laboratory"
    CAPACITY = "capacity"


class SimulationStatus(Enum):
    """Lifecycle status of a simulation."""
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# Data Contracts
# ============================================================================

@dataclass
class SimulationParameter:
    """A single tunable parameter for a simulation."""
    name: str
    value: float
    unit: str = ""
    min_val: float = 0.0
    max_val: float = float("inf")


@dataclass
class SimulationResult:
    """Outcome of a simulation run."""
    simulation_id: str
    sim_type: SimulationType
    status: SimulationStatus
    parameters: list[SimulationParameter] = field(default_factory=list)
    results: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    duration_seconds: float = 0.0


# ============================================================================
# Simulation Engine
# ============================================================================

class SimulationEngine:
    """Manages digital twin simulations across the platform.

    Provides creation, execution, and reporting for organizational,
    workforce, laboratory, and capacity simulations.
    """

    def __init__(self) -> None:
        self._simulations: dict[str, SimulationResult] = {}

    def create_simulation(
        self,
        sim_id: str,
        sim_type: SimulationType,
        parameters: list[SimulationParameter],
    ) -> SimulationResult:
        """Create a new simulation in READY status.

        Args:
            sim_id: Unique identifier for the simulation.
            sim_type: The type of simulation to run.
            parameters: Tunable parameters for the simulation.

        Returns:
            The created SimulationResult.
        """
        result = SimulationResult(
            simulation_id=sim_id,
            sim_type=sim_type,
            status=SimulationStatus.READY,
            parameters=parameters,
        )
        self._simulations[sim_id] = result
        return result

    def run_simulation(self, sim_id: str) -> bool:
        """Execute a simulation and populate mock results.

        Args:
            sim_id: The simulation to run.

        Returns:
            True if the simulation completed successfully.
        """
        sim = self._simulations.get(sim_id)
        if sim is None or sim.status not in (SimulationStatus.READY, SimulationStatus.FAILED):
            return False

        sim.status = SimulationStatus.RUNNING
        try:
            sim.results = {
                "efficiency_score": 0.87,
                "resource_utilization": 0.72,
                "risk_level": "low",
                "optimization_suggestions": [
                    "Increase staff allocation by 12%",
                    "Consolidate storage locations",
                ],
            }
            sim.duration_seconds = 1.23
            sim.status = SimulationStatus.COMPLETED
            return True
        except Exception:
            sim.status = SimulationStatus.FAILED
            return False

    def get_simulation(self, sim_id: str) -> SimulationResult | None:
        """Retrieve a simulation by ID."""
        return self._simulations.get(sim_id)

    def list_simulations(self, sim_type: SimulationType | None = None) -> list[SimulationResult]:
        """List simulations, optionally filtered by type."""
        sims = list(self._simulations.values())
        if sim_type is not None:
            sims = [s for s in sims if s.sim_type == sim_type]
        return sims

    def get_readiness_report(self) -> dict[str, Any]:
        """Return a summary report of digital twin readiness.

        Returns:
            Dictionary with simulation counts and supported types.
        """
        sims = list(self._simulations.values())
        return {
            "total_simulations": len(sims),
            "by_status": {
                status.value: sum(1 for s in sims if s.status == status)
                for status in SimulationStatus
            },
            "by_type": {
                stype.value: sum(1 for s in sims if s.sim_type == stype)
                for stype in SimulationType
            },
            "types_supported": [st.value for st in SimulationType],
        }


__all__ = [
    "SimulationType",
    "SimulationStatus",
    "SimulationParameter",
    "SimulationResult",
    "SimulationEngine",
]
