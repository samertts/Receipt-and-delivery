"""Deterministic, fail-closed sample custody state machine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum


class SampleState(StrEnum):
    CREATED = "created"
    COLLECTED = "collected"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    ACCEPTED = "accepted"
    DELIVERED_TO_LAB = "delivered_to_lab"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    LOST = "lost"
    CANCELLED = "cancelled"


ALLOWED_TRANSITIONS: dict[SampleState, frozenset[SampleState]] = {
    SampleState.CREATED: frozenset({SampleState.COLLECTED, SampleState.CANCELLED}),
    SampleState.COLLECTED: frozenset({SampleState.IN_TRANSIT, SampleState.REJECTED}),
    SampleState.IN_TRANSIT: frozenset({SampleState.RECEIVED, SampleState.LOST}),
    SampleState.RECEIVED: frozenset({SampleState.ACCEPTED, SampleState.REJECTED}),
    SampleState.ACCEPTED: frozenset({SampleState.DELIVERED_TO_LAB}),
    SampleState.DELIVERED_TO_LAB: frozenset({SampleState.PROCESSING}),
    SampleState.PROCESSING: frozenset({SampleState.COMPLETED, SampleState.REJECTED}),
    SampleState.COMPLETED: frozenset(),
    SampleState.REJECTED: frozenset(),
    SampleState.LOST: frozenset(),
    SampleState.CANCELLED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class CustodyEvent:
    sample_id: str
    actor_id: str
    from_state: SampleState
    to_state: SampleState
    occurred_at: datetime
    idempotency_key: str
    reason: str = ""


def validate_transition(current: SampleState, target: SampleState) -> None:
    """Reject every transition not explicitly declared by the workflow."""
    if target not in ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"Invalid sample transition: {current.value} -> {target.value}")


def create_custody_event(
    *,
    sample_id: str,
    actor_id: str,
    current: SampleState,
    target: SampleState,
    idempotency_key: str,
    reason: str = "",
    occurred_at: datetime | None = None,
) -> CustodyEvent:
    """Create a validated append-only event; callers must persist it transactionally."""
    if not sample_id.strip() or not actor_id.strip() or not idempotency_key.strip():
        raise ValueError("sample_id, actor_id, and idempotency_key are required")
    if target in {SampleState.REJECTED, SampleState.LOST} and not reason.strip():
        raise ValueError("A reason is required for rejected or lost samples")
    validate_transition(current, target)
    timestamp = occurred_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        raise ValueError("occurred_at must be timezone-aware")
    return CustodyEvent(
        sample_id=sample_id,
        actor_id=actor_id,
        from_state=current,
        to_state=target,
        occurred_at=timestamp,
        idempotency_key=idempotency_key,
        reason=reason.strip(),
    )
