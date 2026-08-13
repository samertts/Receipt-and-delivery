from datetime import datetime, timezone

from app.integrations.gula_client import GulaEventClient


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"status": "staged"}


def test_custody_transition_uses_canonical_envelope(monkeypatch):
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse()

    monkeypatch.setattr("app.integrations.gula_client.httpx.post", fake_post)
    client = GulaEventClient("https://gula.example", "token", max_retries=1)

    result = client.publish_custody_transition(
        sample_id="sample-1",
        transaction_id="txn-1",
        actor_id="user-1",
        from_state="created",
        to_state="collected",
        idempotency_key="custody-key-1",
        occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        tenant_id="tenant-1",
        reason="handover",
    )

    assert result == {"status": "staged"}
    url, kwargs = calls[0]
    assert url == "https://gula.example/integrations/events"
    assert kwargs["headers"]["Authorization"] == "Bearer token"
    envelope = kwargs["json"]
    assert envelope["event_type"] == "sample.custody.transitioned"
    assert envelope["tenant_id"] == "tenant-1"
    assert envelope["idempotency_key"] == "custody-key-1"
    assert envelope["payload"]["to_state"] == "collected"



def test_custody_envelope_is_stable_for_replay():
    client = GulaEventClient("https://gula.example", "token")
    occurred_at = datetime(2026, 1, 1, tzinfo=timezone.utc)

    first = client.build_custody_transition_envelope(
        sample_id="sample-2",
        transaction_id="txn-2",
        actor_id="user-2",
        from_state="collected",
        to_state="in_transit",
        idempotency_key="custody-replay-key",
        occurred_at=occurred_at,
        tenant_id="tenant-1",
        reason="dispatch",
    )
    second = client.build_custody_transition_envelope(
        sample_id="sample-2",
        transaction_id="txn-2",
        actor_id="user-2",
        from_state="collected",
        to_state="in_transit",
        idempotency_key="custody-replay-key",
        occurred_at=occurred_at,
        tenant_id="tenant-1",
        reason="dispatch",
    )

    assert first == second
    assert first["event_id"].startswith("evt-")
    assert first["payload"]["to_state"] == "in_transit"
