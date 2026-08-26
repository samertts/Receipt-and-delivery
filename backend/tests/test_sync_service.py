from app.models.sync_log import SyncLog
from app.services.sync_service import SyncService


def _entry(payload=None, action="create", entity_id=1, idempotency_key=None):
    return {
        "entity_type": "receipts",
        "entity_id": entity_id,
        "action": action,
        "idempotency_key": idempotency_key or f"receipt-{entity_id}-{action}",
        "payload": payload if payload is not None else {"status": "draft"},
    }


def test_push_is_idempotent_and_does_not_overwrite_conflicting_payload(db):
    svc = SyncService(db)
    first = svc.push([_entry()], device_id="device-a", branch_id="branch-a")
    duplicate = svc.push([_entry()], device_id="device-a", branch_id="branch-a")
    conflict = svc.push(
        [_entry(
            {"status": "approved"},
            action="update",
            idempotency_key="receipt-1-update",
        )],
        device_id="device-a",
        branch_id="branch-a",
    )

    assert first["accepted"] == 1
    assert duplicate["idempotent"] == 1
    assert conflict["conflicts"] == 1
    row = db.query(SyncLog).filter(SyncLog.branch_id == "branch-a").one()
    assert row.payload == '{"status":"draft"}'

    reused = svc.push(
        [_entry({"status": "other"}, idempotency_key="receipt-1-create")],
        device_id="device-a",
        branch_id="branch-a",
    )
    assert reused["conflict_items"][0]["reason"] == "idempotency_key_reuse"


def test_push_and_pull_are_scoped_to_branch(db):
    svc = SyncService(db)
    svc.push([_entry(entity_id=10)], device_id="device-a", branch_id="branch-a")
    svc.push(
        [_entry(entity_id=10, idempotency_key="branch-b-receipt-10")],
        device_id="device-b",
        branch_id="branch-b",
    )

    branch_a = svc.pull(branch_id="branch-a")
    branch_b = svc.pull(branch_id="branch-b")

    assert branch_a["count"] == 1
    assert branch_a["entries"][0]["branch_id"] == "branch-a"
    assert branch_b["count"] == 1
    assert branch_b["entries"][0]["branch_id"] == "branch-b"


def test_push_rejects_oversized_or_non_serializable_payload(db):
    svc = SyncService(db)
    oversized = svc.push(
        [_entry("x" * (5 * 1024 * 1024 + 1))],
        device_id="device-a",
        branch_id="branch-a",
    )
    invalid = svc.push(
        [_entry({"value": object()}, entity_id=2)],
        device_id="device-a",
        branch_id="branch-a",
    )

    assert oversized["accepted"] == 0
    assert oversized["conflict_items"][0]["reason"] == "payload_too_large"
    assert invalid["accepted"] == 0
    assert invalid["conflict_items"][0]["reason"] == "invalid_payload"
