"""
Platform Pilot — Pilot Deployment Program

Phase 10: Pilot Deployment Program
Constitution: Principle 20 (Pilot Testing), Principle 21 (Staged Rollout)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PilotPhase(Enum):
    """Phases of a pilot deployment."""
    PLANNING = "planning"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    EVALUATION = "evaluation"
    COMPLETED = "completed"


@dataclass
class PilotMetric:
    """A single metric tracked during pilot deployment."""
    name: str
    target: float
    actual: float
    unit: str
    status: str = "pending"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "target": self.target,
            "actual": self.actual,
            "unit": self.unit,
            "status": self.status,
        }


@dataclass
class PilotDeployment:
    """Represents a pilot deployment with its metrics and status."""
    pilot_id: str
    name: str
    phase: PilotPhase = PilotPhase.PLANNING
    start_date: datetime = field(default_factory=datetime.utcnow)
    end_date: datetime | None = None
    metrics: list[PilotMetric] = field(default_factory=list)
    users_enrolled: int = 0
    users_active: int = 0
    error_rate: float = 0.0
    satisfaction_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "pilot_id": self.pilot_id,
            "name": self.name,
            "phase": self.phase.value,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "metrics": [m.to_dict() for m in self.metrics],
            "users_enrolled": self.users_enrolled,
            "users_active": self.users_active,
            "error_rate": self.error_rate,
            "satisfaction_score": self.satisfaction_score,
        }


class PilotDeploymentManager:
    """Manages pilot deployments and tracks their metrics."""

    def __init__(self) -> None:
        self._pilots: dict[str, PilotDeployment] = {}

    def create_pilot(self, pilot_id: str, name: str) -> PilotDeployment:
        """Create a new pilot deployment."""
        pilot = PilotDeployment(pilot_id=pilot_id, name=name)
        self._pilots[pilot_id] = pilot
        return pilot

    def get_pilot(self, pilot_id: str) -> PilotDeployment | None:
        """Get a pilot by ID."""
        return self._pilots.get(pilot_id)

    def list_pilots(self) -> list[PilotDeployment]:
        """List all pilot deployments."""
        return list(self._pilots.values())

    def add_metric(self, pilot_id: str, metric: PilotMetric) -> bool:
        """Add a metric to a pilot."""
        pilot = self.get_pilot(pilot_id)
        if not pilot:
            return False
        pilot.metrics.append(metric)
        return True

    def update_phase(self, pilot_id: str, phase: PilotPhase) -> bool:
        """Update the phase of a pilot."""
        pilot = self.get_pilot(pilot_id)
        if not pilot:
            return False
        pilot.phase = phase
        if phase == PilotPhase.COMPLETED:
            pilot.end_date = datetime.utcnow()
        return True

    def record_adoption(self, pilot_id: str, enrolled: int, active: int) -> bool:
        """Record user adoption metrics for a pilot."""
        pilot = self.get_pilot(pilot_id)
        if not pilot:
            return False
        pilot.users_enrolled = enrolled
        pilot.users_active = active
        return True

    def record_satisfaction(self, pilot_id: str, score: float) -> bool:
        """Record satisfaction score for a pilot."""
        pilot = self.get_pilot(pilot_id)
        if not pilot:
            return False
        pilot.satisfaction_score = score
        return True

    def get_pilot_report(self, pilot_id: str) -> dict[str, Any]:
        """Get a comprehensive report for a pilot."""
        pilot = self.get_pilot(pilot_id)
        if not pilot:
            return {"error": f"Pilot {pilot_id} not found"}

        adoption_rate = (
            (pilot.users_active / pilot.users_enrolled * 100)
            if pilot.users_enrolled > 0
            else 0.0
        )

        metrics_summary = {
            "total_metrics": len(pilot.metrics),
            "metrics_on_track": sum(
                1 for m in pilot.metrics if m.status == "on_track"
            ),
            "metrics_at_risk": sum(
                1 for m in pilot.metrics if m.status == "at_risk"
            ),
            "metrics_off_track": sum(
                1 for m in pilot.metrics if m.status == "off_track"
            ),
        }

        return {
            "pilot_id": pilot.pilot_id,
            "name": pilot.name,
            "phase": pilot.phase.value,
            "start_date": pilot.start_date.isoformat(),
            "end_date": pilot.end_date.isoformat() if pilot.end_date else None,
            "adoption_rate": round(adoption_rate, 2),
            "users_enrolled": pilot.users_enrolled,
            "users_active": pilot.users_active,
            "error_rate": pilot.error_rate,
            "satisfaction_score": pilot.satisfaction_score,
            "metrics_summary": metrics_summary,
            "metrics": [m.to_dict() for m in pilot.metrics],
        }

    def get_readiness_report(self) -> dict[str, Any]:
        """Get overall pilot deployment readiness report."""
        pilots = self.list_pilots()
        if not pilots:
            return {
                "total_pilots": 0,
                "status": "no_pilots",
                "readiness": "not_ready",
            }

        phase_counts: dict[str, int] = {}
        for pilot in pilots:
            phase = pilot.phase.value
            phase_counts[phase] = phase_counts.get(phase, 0) + 1

        total_users_enrolled = sum(p.users_enrolled for p in pilots)
        total_users_active = sum(p.users_active for p in pilots)
        avg_satisfaction = (
            sum(p.satisfaction_score for p in pilots) / len(pilots)
            if pilots
            else 0.0
        )

        completed_count = phase_counts.get("completed", 0)
        readiness = (
            "ready"
            if completed_count == len(pilots)
            else "in_progress"
            if completed_count > 0
            else "not_ready"
        )

        return {
            "total_pilots": len(pilots),
            "phase_distribution": phase_counts,
            "total_users_enrolled": total_users_enrolled,
            "total_users_active": total_users_active,
            "average_satisfaction": round(avg_satisfaction, 2),
            "readiness": readiness,
        }


__all__ = [
    "PilotPhase",
    "PilotMetric",
    "PilotDeployment",
    "PilotDeploymentManager",
]
