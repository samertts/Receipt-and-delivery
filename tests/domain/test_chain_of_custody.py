from datetime import datetime, timezone

import pytest

from backend.app.domain.chain_of_custody import (
    SampleState,
    create_custody_event,
    validate_transition,
)


def test_valid_custody_transition_creates_append_only_event():
    event = create_custody_event(
        sample_id="S-100",
        actor_id="collector-1",
        current=SampleState.CREATED,
        target=SampleState.COLLECTED,
        idempotency_key="S-100:created:collected:1",
        occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert event.sample_id == "S-100"
    assert event.from_state is SampleState.CREATED
    assert event.to_state is SampleState.COLLECTED
    assert event.occurred_at.tzinfo is not None


def test_invalid_transition_fails_closed():
    with pytest.raises(ValueError, match="Invalid sample transition"):
        validate_transition(SampleState.CREATED, SampleState.COMPLETED)


def test_rejection_requires_reason():
    with pytest.raises(ValueError, match="reason is required"):
        create_custody_event(
            sample_id="S-100",
            actor_id="receiver-1",
            current=SampleState.RECEIVED,
            target=SampleState.REJECTED,
            idempotency_key="S-100:received:rejected:1",
        )


def test_terminal_state_cannot_be_reopened():
    with pytest.raises(ValueError, match="Invalid sample transition"):
        validate_transition(SampleState.COMPLETED, SampleState.PROCESSING)
