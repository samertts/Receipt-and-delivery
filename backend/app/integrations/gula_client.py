from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from typing import Any

import httpx


class GulaEventClient:
    def __init__(
        self,
        base_url: str,
        access_token: str,
        timeout: float = 5.0,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self.timeout = timeout
        self.max_retries = max_retries

    def publish_custody_transition(
        self,
        *,
        sample_id: str,
        transaction_id: str,
        actor_id: str,
        from_state: str,
        to_state: str,
        idempotency_key: str,
        occurred_at: datetime,
        tenant_id: str,
        reason: str = "",
    ) -> dict[str, Any]:
        event_id = "evt-" + hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()[:32]
        envelope = {
            "event_id": event_id,
            "event_type": "sample.custody.transitioned",
            "schema_version": 1,
            "source_service": "receipt-and-delivery",
            "tenant_id": tenant_id,
            "occurred_at": occurred_at.astimezone(timezone.utc).isoformat(),
            "actor_id": actor_id,
            "entity_id": sample_id,
            "correlation_id": transaction_id,
            "idempotency_key": idempotency_key,
            "payload": {
                "sample_id": sample_id,
                "transaction_id": transaction_id,
                "from_state": from_state,
                "to_state": to_state,
                "reason": reason,
            },
        }
        headers = {"Authorization": f"Bearer {self.access_token}"}
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = httpx.post(
                    f"{self.base_url}/integrations/events",
                    json=envelope,
                    headers=headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(2 ** (attempt - 1))
        return {"status": "failed", "error": str(last_error) if last_error else "unknown_error"}
