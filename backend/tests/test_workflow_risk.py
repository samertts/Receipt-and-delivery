from app.domain.workflow_risk import (
    IdentityRecord,
    RiskEngine,
    RiskLevel,
    match_identity,
)


def test_identity_matching_normalizes_safe_whitespace_but_rejects_mismatch():
    expected = IdentityRecord(
        patient_id=" P-100 ",
        specimen_id="S-200",
        order_id="O-300",
        facility_id="F-1",
        collection_data="2026-08-26T10:00Z",
        barcode="QR-200",
    )
    observed = IdentityRecord(
        patient_id="p-100",
        specimen_id="S-201",
        order_id="O-300",
        facility_id="F-1",
        collection_data="2026-08-26T10:00Z",
        barcode="QR-200",
    )

    result = match_identity(expected, observed)

    assert result.matched is False
    assert result.mismatches == ("specimen_id",)
    assert result.hard_warning is True
    assert result.requires_dual_verification is True


def test_identity_matching_does_not_require_empty_optional_expected_fields():
    result = match_identity(
        IdentityRecord(specimen_id="S-1"),
        IdentityRecord(specimen_id="S-1", patient_id="not-collected"),
    )
    assert result.matched is True


def test_risk_engine_uses_proportionate_controls():
    engine = RiskEngine()
    assert engine.assess().level == RiskLevel.LOW

    mismatch = engine.assess(identity_mismatch=True)
    assert mismatch.level == RiskLevel.HIGH
    assert mismatch.requires_confirmation is True
    assert mismatch.requires_dual_verification is True

    critical = engine.assess(missing_specimen=True, unauthorized_device=True)
    assert critical.level == RiskLevel.CRITICAL
    assert critical.score == 100
    assert critical.requires_dual_verification is True
