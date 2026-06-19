"""
Platform Laboratory — National Laboratory Platform Readiness

Phase 13: National Laboratory Platform Readiness
Constitution: Principle 43 (National Laboratory), Principle 44 (Quality Standards)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# ============================================================================
# Enums
# ============================================================================

class LaboratoryType(Enum):
    """Classification of laboratories within the national platform."""
    MEDICAL = "medical"
    PUBLIC_HEALTH = "public_health"
    RESEARCH = "research"
    SURVEILLANCE = "surveillance"


class LaboratoryStatus(Enum):
    """Operational status of a laboratory."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ACCREDITED = "accredited"
    PENDING_ACCREDITATION = "pending_accreditation"


# ============================================================================
# Dataclasses
# ============================================================================

@dataclass
class LaboratoryInfo:
    """Metadata for a registered laboratory."""
    lab_id: str
    name: str
    lab_type: LaboratoryType
    status: LaboratoryStatus
    region: str = ""
    capacity: int = 0
    equipment_count: int = 0
    accreditation_id: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lab_id": self.lab_id,
            "name": self.name,
            "lab_type": self.lab_type.value,
            "status": self.status.value,
            "region": self.region,
            "capacity": self.capacity,
            "equipment_count": self.equipment_count,
            "accreditation_id": self.accreditation_id,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class EquipmentInfo:
    """Metadata for laboratory equipment."""
    equipment_id: str
    lab_id: str
    name: str
    model: str
    status: str = "operational"
    last_calibration: datetime = field(default_factory=datetime.utcnow)
    next_calibration: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "equipment_id": self.equipment_id,
            "lab_id": self.lab_id,
            "name": self.name,
            "model": self.model,
            "status": self.status,
            "last_calibration": self.last_calibration.isoformat(),
            "next_calibration": self.next_calibration.isoformat(),
        }


@dataclass
class QualityStandard:
    """A quality standard applicable to laboratories."""
    standard_id: str
    name: str
    description: str
    version: str = "1.0.0"
    mandatory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "standard_id": self.standard_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "mandatory": self.mandatory,
        }


# ============================================================================
# Registries
# ============================================================================

class LaboratoryRegistry:
    """Registry for managing laboratories."""

    def __init__(self) -> None:
        self._labs: dict[str, LaboratoryInfo] = {}

    def register_lab(self, lab: LaboratoryInfo) -> None:
        """Register or update a laboratory."""
        self._labs[lab.lab_id] = lab

    def get_lab(self, lab_id: str) -> LaboratoryInfo | None:
        """Retrieve a laboratory by its ID."""
        return self._labs.get(lab_id)

    def list_labs(self, lab_type: LaboratoryType | None = None) -> list[LaboratoryInfo]:
        """Return all laboratories, optionally filtered by type."""
        labs = list(self._labs.values())
        if lab_type is not None:
            labs = [lab for lab in labs if lab.lab_type == lab_type]
        return labs

    def list_by_region(self, region: str) -> list[LaboratoryInfo]:
        """Return all laboratories in a given region."""
        return [lab for lab in self._labs.values() if lab.region == region]

    def list_accredited(self) -> list[LaboratoryInfo]:
        """Return all laboratories with accredited status."""
        return [
            lab for lab in self._labs.values()
            if lab.status == LaboratoryStatus.ACCREDITED
        ]


class EquipmentRegistry:
    """Registry for managing laboratory equipment."""

    def __init__(self) -> None:
        self._equipment: dict[str, EquipmentInfo] = {}

    def register_equipment(self, equipment: EquipmentInfo) -> None:
        """Register or update a piece of equipment."""
        self._equipment[equipment.equipment_id] = equipment

    def get_equipment(self, equipment_id: str) -> EquipmentInfo | None:
        """Retrieve equipment by its ID."""
        return self._equipment.get(equipment_id)

    def list_by_lab(self, lab_id: str) -> list[EquipmentInfo]:
        """Return all equipment belonging to a laboratory."""
        return [e for e in self._equipment.values() if e.lab_id == lab_id]

    def list_needing_calibration(self) -> list[EquipmentInfo]:
        """Return all equipment whose next calibration date is in the past."""
        now = datetime.utcnow()
        return [
            e for e in self._equipment.values()
            if e.next_calibration < now
        ]


class QualityRegistry:
    """Registry for managing quality standards."""

    def __init__(self) -> None:
        self._standards: dict[str, QualityStandard] = {}

    def register_standard(self, standard: QualityStandard) -> None:
        """Register or update a quality standard."""
        self._standards[standard.standard_id] = standard

    def get_standard(self, standard_id: str) -> QualityStandard | None:
        """Retrieve a standard by its ID."""
        return self._standards.get(standard_id)

    def list_mandatory(self) -> list[QualityStandard]:
        """Return all mandatory quality standards."""
        return [s for s in self._standards.values() if s.mandatory]


# ============================================================================
# Laboratory Platform Manager
# ============================================================================

class LaboratoryPlatformManager:
    """Central manager for national laboratory platform readiness."""

    def __init__(self) -> None:
        self.labs = LaboratoryRegistry()
        self.equipment = EquipmentRegistry()
        self.quality = QualityRegistry()

    def get_readiness_report(self) -> dict[str, Any]:
        """Generate a readiness report for the laboratory platform."""
        all_labs = self.labs.list_labs()
        accredited_labs = self.labs.list_accredited()
        all_equipment = self.equipment.list_needing_calibration()
        all_standards = self.quality.list_mandatory()

        lab_types: dict[str, int] = {}
        for lab in all_labs:
            key = lab.lab_type.value
            lab_types[key] = lab_types.get(key, 0) + 1

        return {
            "lab_count": len(all_labs),
            "equipment_count": sum(
                len(self.equipment.list_by_lab(lab.lab_id))
                for lab in all_labs
            ),
            "standards_count": len(self.quality._standards),
            "mandatory_standards_count": len(all_standards),
            "accredited_count": len(accredited_labs),
            "calibration_needed_count": len(all_equipment),
            "lab_types": lab_types,
            "platform_ready": len(accredited_labs) > 0,
        }
