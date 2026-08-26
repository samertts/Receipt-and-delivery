"""Identity matching and risk-based approval decisions for sensitive workflows."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class IdentityRecord:
    patient_id: str = ""
    specimen_id: str = ""
    order_id: str = ""
    facility_id: str = ""
    collection_data: str = ""
    barcode: str = ""


def _normalize(value: str) -> str:
    return " ".join(str(value).strip().casefold().split())


@dataclass(frozen=True, slots=True)
class IdentityMatchResult:
    matched: bool
    mismatches: tuple[str, ...]
    hard_warning: bool
    requires_dual_verification: bool


def match_identity(expected: IdentityRecord, observed: IdentityRecord) -> IdentityMatchResult:
    """Compare non-empty expected identity fields; mismatches are never silent."""
    fields = (
        "patient_id",
        "specimen_id",
        "order_id",
        "facility_id",
        "collection_data",
        "barcode",
    )
    mismatches = tuple(
        field
        for field in fields
        if _normalize(getattr(expected, field))
        and _normalize(getattr(expected, field)) != _normalize(getattr(observed, field))
    )
    return IdentityMatchResult(
        matched=not mismatches,
        mismatches=mismatches,
        hard_warning=bool(mismatches),
        requires_dual_verification=bool(mismatches),
    )


@dataclass(frozen=True, slots=True)
class RiskDecision:
    score: int
    level: RiskLevel
    requires_confirmation: bool
    requires_dual_verification: bool
    reasons: tuple[str, ...]


class RiskEngine:
    """Deterministic policy for choosing proportionate workflow controls."""

    _WEIGHTS = {
        "identity_mismatch": 60,
        "temperature_breach": 45,
        "missing_specimen": 90,
        "unauthorized_device": 100,
        "duplicate_event": 35,
        "unexpected_receipt": 55,
        "discrepancy": 45,
    }

    def assess(self, **signals: bool) -> RiskDecision:
        reasons = tuple(
            name for name, active in signals.items() if active and name in self._WEIGHTS
        )
        score = min(100, sum(self._WEIGHTS[name] for name in reasons))
        if score >= 90:
            level = RiskLevel.CRITICAL
        elif score >= 45:
            level = RiskLevel.HIGH
        elif score > 0:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW
        return RiskDecision(
            score=score,
            level=level,
            requires_confirmation=level in {RiskLevel.HIGH, RiskLevel.CRITICAL},
            requires_dual_verification=level == RiskLevel.CRITICAL
            or "identity_mismatch" in reasons,
            reasons=reasons,
        )
