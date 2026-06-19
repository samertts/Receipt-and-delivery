"""Tests for unified_platform/laboratory/__init__.py — Phase 13: National Laboratory Platform Readiness."""

from __future__ import annotations

from datetime import datetime, timedelta

from unified_platform.laboratory import (
    EquipmentInfo,
    EquipmentRegistry,
    LaboratoryInfo,
    LaboratoryPlatformManager,
    LaboratoryRegistry,
    LaboratoryStatus,
    LaboratoryType,
    QualityRegistry,
    QualityStandard,
)


# ============================================================================
# LaboratoryInfo
# ============================================================================

class TestLaboratoryInfo:
    def test_creation(self):
        lab = LaboratoryInfo(
            lab_id="lab-1",
            name="Central Lab",
            lab_type=LaboratoryType.MEDICAL,
            status=LaboratoryStatus.ACCREDITED,
            region="North",
            capacity=100,
            equipment_count=10,
            accreditation_id="ACC-001",
        )
        assert lab.lab_id == "lab-1"
        assert lab.name == "Central Lab"
        assert lab.lab_type == LaboratoryType.MEDICAL
        assert lab.status == LaboratoryStatus.ACCREDITED
        assert lab.region == "North"
        assert lab.capacity == 100
        assert isinstance(lab.created_at, datetime)

    def test_to_dict(self):
        lab = LaboratoryInfo(
            lab_id="lab-1",
            name="Central Lab",
            lab_type=LaboratoryType.PUBLIC_HEALTH,
            status=LaboratoryStatus.ACTIVE,
        )
        d = lab.to_dict()
        assert d["lab_id"] == "lab-1"
        assert d["lab_type"] == "public_health"
        assert d["status"] == "active"
        assert "created_at" in d


# ============================================================================
# EquipmentInfo
# ============================================================================

class TestEquipmentInfo:
    def test_creation(self):
        eq = EquipmentInfo(
            equipment_id="eq-1",
            lab_id="lab-1",
            name="Spectrophotometer",
            model="UV-1800",
            status="operational",
        )
        assert eq.equipment_id == "eq-1"
        assert eq.lab_id == "lab-1"
        assert eq.name == "Spectrophotometer"
        assert eq.model == "UV-1800"
        assert isinstance(eq.last_calibration, datetime)
        assert isinstance(eq.next_calibration, datetime)

    def test_to_dict(self):
        eq = EquipmentInfo(
            equipment_id="eq-1",
            lab_id="lab-1",
            name="Centrifuge",
            model="CX-200",
            status="maintenance",
        )
        d = eq.to_dict()
        assert d["equipment_id"] == "eq-1"
        assert d["status"] == "maintenance"
        assert "last_calibration" in d
        assert "next_calibration" in d


# ============================================================================
# QualityStandard
# ============================================================================

class TestQualityStandard:
    def test_creation(self):
        qs = QualityStandard(
            standard_id="qs-1",
            name="ISO 15189",
            description="Medical laboratory quality standard",
            version="2023",
            mandatory=True,
        )
        assert qs.standard_id == "qs-1"
        assert qs.name == "ISO 15189"
        assert qs.mandatory is True

    def test_to_dict(self):
        qs = QualityStandard(
            standard_id="qs-1",
            name="ISO 15189",
            description="D",
            mandatory=False,
        )
        d = qs.to_dict()
        assert d["mandatory"] is False
        assert d["version"] == "1.0.0"


# ============================================================================
# LaboratoryRegistry
# ============================================================================

class TestLaboratoryRegistry:
    def test_register_and_get(self):
        reg = LaboratoryRegistry()
        lab = LaboratoryInfo(
            lab_id="lab-1", name="Lab 1",
            lab_type=LaboratoryType.MEDICAL,
            status=LaboratoryStatus.ACTIVE,
        )
        reg.register_lab(lab)
        assert reg.get_lab("lab-1") is lab
        assert reg.get_lab("nonexistent") is None

    def test_list_by_type(self):
        reg = LaboratoryRegistry()
        reg.register_lab(LaboratoryInfo(
            lab_id="l1", name="L1",
            lab_type=LaboratoryType.MEDICAL,
            status=LaboratoryStatus.ACTIVE,
        ))
        reg.register_lab(LaboratoryInfo(
            lab_id="l2", name="L2",
            lab_type=LaboratoryType.RESEARCH,
            status=LaboratoryStatus.ACTIVE,
        ))
        reg.register_lab(LaboratoryInfo(
            lab_id="l3", name="L3",
            lab_type=LaboratoryType.MEDICAL,
            status=LaboratoryStatus.ACTIVE,
        ))
        medical = reg.list_labs(LaboratoryType.MEDICAL)
        assert len(medical) == 2
        assert {lab.lab_id for lab in medical} == {"l1", "l3"}

    def test_list_by_type_none(self):
        reg = LaboratoryRegistry()
        reg.register_lab(LaboratoryInfo(
            lab_id="l1", name="L1",
            lab_type=LaboratoryType.MEDICAL,
            status=LaboratoryStatus.ACTIVE,
        ))
        all_labs = reg.list_labs()
        assert len(all_labs) == 1

    def test_list_by_region(self):
        reg = LaboratoryRegistry()
        reg.register_lab(LaboratoryInfo(
            lab_id="l1", name="L1",
            lab_type=LaboratoryType.MEDICAL,
            status=LaboratoryStatus.ACTIVE,
            region="North",
        ))
        reg.register_lab(LaboratoryInfo(
            lab_id="l2", name="L2",
            lab_type=LaboratoryType.MEDICAL,
            status=LaboratoryStatus.ACTIVE,
            region="South",
        ))
        north = reg.list_by_region("North")
        assert len(north) == 1
        assert north[0].lab_id == "l1"

    def test_list_accredited(self):
        reg = LaboratoryRegistry()
        reg.register_lab(LaboratoryInfo(
            lab_id="l1", name="L1",
            lab_type=LaboratoryType.MEDICAL,
            status=LaboratoryStatus.ACCREDITED,
        ))
        reg.register_lab(LaboratoryInfo(
            lab_id="l2", name="L2",
            lab_type=LaboratoryType.MEDICAL,
            status=LaboratoryStatus.ACTIVE,
        ))
        accredited = reg.list_accredited()
        assert len(accredited) == 1
        assert accredited[0].lab_id == "l1"


# ============================================================================
# EquipmentRegistry
# ============================================================================

class TestEquipmentRegistry:
    def test_register_and_get(self):
        reg = EquipmentRegistry()
        eq = EquipmentInfo(
            equipment_id="eq-1", lab_id="lab-1",
            name="Microscope", model="M-200",
        )
        reg.register_equipment(eq)
        assert reg.get_equipment("eq-1") is eq
        assert reg.get_equipment("nope") is None

    def test_list_by_lab(self):
        reg = EquipmentRegistry()
        reg.register_equipment(EquipmentInfo(
            equipment_id="eq-1", lab_id="lab-1",
            name="E1", model="M1",
        ))
        reg.register_equipment(EquipmentInfo(
            equipment_id="eq-2", lab_id="lab-1",
            name="E2", model="M2",
        ))
        reg.register_equipment(EquipmentInfo(
            equipment_id="eq-3", lab_id="lab-2",
            name="E3", model="M3",
        ))
        lab1_eq = reg.list_by_lab("lab-1")
        assert len(lab1_eq) == 2

    def test_list_needing_calibration(self):
        reg = EquipmentRegistry()
        now = datetime.utcnow()
        reg.register_equipment(EquipmentInfo(
            equipment_id="eq-overdue", lab_id="lab-1",
            name="Old", model="M1",
            next_calibration=now - timedelta(days=10),
        ))
        reg.register_equipment(EquipmentInfo(
            equipment_id="eq-ok", lab_id="lab-1",
            name="New", model="M2",
            next_calibration=now + timedelta(days=10),
        ))
        needs_cal = reg.list_needing_calibration()
        assert len(needs_cal) == 1
        assert needs_cal[0].equipment_id == "eq-overdue"


# ============================================================================
# QualityRegistry
# ============================================================================

class TestQualityRegistry:
    def test_register_and_get(self):
        reg = QualityRegistry()
        qs = QualityStandard(
            standard_id="qs-1", name="ISO 15189",
            description="Medical lab standard", mandatory=True,
        )
        reg.register_standard(qs)
        assert reg.get_standard("qs-1") is qs
        assert reg.get_standard("nope") is None

    def test_list_mandatory(self):
        reg = QualityRegistry()
        reg.register_standard(QualityStandard(
            standard_id="qs-1", name="Mandatory",
            description="D", mandatory=True,
        ))
        reg.register_standard(QualityStandard(
            standard_id="qs-2", name="Optional",
            description="D", mandatory=False,
        ))
        mandatory = reg.list_mandatory()
        assert len(mandatory) == 1
        assert mandatory[0].standard_id == "qs-1"


# ============================================================================
# LaboratoryPlatformManager
# ============================================================================

class TestLaboratoryPlatformManager:
    def test_init_empty(self):
        mgr = LaboratoryPlatformManager()
        report = mgr.get_readiness_report()
        assert report["lab_count"] == 0
        assert report["equipment_count"] == 0
        assert report["standards_count"] == 0
        assert report["mandatory_standards_count"] == 0
        assert report["accredited_count"] == 0
        assert report["calibration_needed_count"] == 0
        assert report["lab_types"] == {}
        assert report["platform_ready"] is False

    def test_readiness_report_with_data(self):
        mgr = LaboratoryPlatformManager()

        mgr.labs.register_lab(LaboratoryInfo(
            lab_id="lab-1", name="Lab 1",
            lab_type=LaboratoryType.MEDICAL,
            status=LaboratoryStatus.ACCREDITED,
            region="North",
        ))
        mgr.labs.register_lab(LaboratoryInfo(
            lab_id="lab-2", name="Lab 2",
            lab_type=LaboratoryType.RESEARCH,
            status=LaboratoryStatus.ACTIVE,
            region="South",
        ))

        now = datetime.utcnow()
        mgr.equipment.register_equipment(EquipmentInfo(
            equipment_id="eq-1", lab_id="lab-1",
            name="E1", model="M1",
            next_calibration=now + timedelta(days=30),
        ))
        mgr.equipment.register_equipment(EquipmentInfo(
            equipment_id="eq-2", lab_id="lab-2",
            name="E2", model="M2",
            next_calibration=now - timedelta(days=5),
        ))

        mgr.quality.register_standard(QualityStandard(
            standard_id="qs-1", name="Mandatory",
            description="D", mandatory=True,
        ))
        mgr.quality.register_standard(QualityStandard(
            standard_id="qs-2", name="Optional",
            description="D", mandatory=False,
        ))

        report = mgr.get_readiness_report()
        assert report["lab_count"] == 2
        assert report["equipment_count"] == 2
        assert report["standards_count"] == 2
        assert report["mandatory_standards_count"] == 1
        assert report["accredited_count"] == 1
        assert report["calibration_needed_count"] == 1
        assert report["lab_types"] == {"medical": 1, "research": 1}
        assert report["platform_ready"] is True

    def test_readiness_report_lab_types(self):
        mgr = LaboratoryPlatformManager()
        for i, ltype in enumerate(LaboratoryType):
            mgr.labs.register_lab(LaboratoryInfo(
                lab_id=f"lab-{i}", name=f"Lab {i}",
                lab_type=ltype, status=LaboratoryStatus.ACTIVE,
            ))
        report = mgr.get_readiness_report()
        assert report["lab_count"] == 4
        assert len(report["lab_types"]) == 4
        assert report["platform_ready"] is False
