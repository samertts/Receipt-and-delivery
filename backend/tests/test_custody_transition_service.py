import pytest

from app.core.exceptions import ValidationError
from app.models.organization import Organization
from app.models.user import User
from app.services.security import hash_password
from app.services.transaction_service import TransactionService


def _create_transaction(db, user):
    sender = Organization(name="Sender Lab", code="SENDER")
    receiver = Organization(name="Receiver Lab", code="RECEIVER")
    db.add_all([sender, receiver])
    db.flush()
    return TransactionService(db).create_transaction(
        {
            "transaction_type": "sample_delivery",
            "sender_organization_id": str(sender.id),
            "receiver_organization_id": str(receiver.id),
            "sender_name": "Sender",
            "receiver_name": "Receiver",
            "transaction_date": "2026-01-01",
            "items": [
                {
                    "sample_type": "blood",
                    "total_count": 1,
                    "valid_count": 1,
                    "damaged_count": 0,
                    "rejected_count": 0,
                    "nonconforming_count": 0,
                }
            ],
        },
        current_user=user,
    )


def test_custody_transition_is_idempotent_and_conflict_safe(db):
    user = User(
        username="custody-admin",
        full_name="Custody Admin",
        password_hash=hash_password("Admin@123"),
        role="admin",
        status="active",
    )
    db.add(user)
    db.flush()
    txn = _create_transaction(db, user)
    service = TransactionService(db)
    payload = {
        "sample_id": "S-100",
        "current_state": "created",
        "target_state": "collected",
        "idempotency_key": "S-100:created:collected:1",
    }

    first = service.transition_custody(str(txn.id), payload, current_user=user)
    second = service.transition_custody(str(txn.id), payload, current_user=user)

    assert first.id == second.id
    assert first.to_state == "collected"

    with pytest.raises(ValidationError, match="تعارض"):
        service.transition_custody(
            str(txn.id),
            {
                **payload,
                "idempotency_key": "S-100:created:in_transit:1",
                "target_state": "in_transit",
            },
            current_user=user,
        )
