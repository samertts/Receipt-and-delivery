from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import WebSocket


class NotificationManager:
    """Manage authenticated WebSocket subscribers in the current process."""

    MAX_CONNECTIONS_PER_USER = 5

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, websocket: WebSocket, *, accepted=False) -> None:
        if not accepted:
            await websocket.accept()
        async with self._lock:
            subscribers = self._connections[user_id]
            if len(subscribers) >= self.MAX_CONNECTIONS_PER_USER:
                return False
            subscribers.add(websocket)
            return True

    async def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            subscribers = self._connections.get(user_id)
            if not subscribers:
                return
            subscribers.discard(websocket)
            if not subscribers:
                self._connections.pop(user_id, None)

    async def publish(self, notification: dict[str, Any]) -> None:
        """Broadcast a notification to all subscribers without blocking writers."""
        async with self._lock:
            subscribers = [
                (user_id, websocket)
                for user_id, sockets in self._connections.items()
                for websocket in sockets
            ]

        stale: list[tuple[str, WebSocket]] = []
        for user_id, websocket in subscribers:
            try:
                await websocket.send_json(notification)
            except Exception:
                stale.append((user_id, websocket))

        for user_id, websocket in stale:
            await self.disconnect(user_id, websocket)

    async def publish_to_users(
        self,
        user_ids: set[str],
        notification: dict[str, Any],
    ) -> None:
        async with self._lock:
            subscribers = [
                (user_id, websocket)
                for user_id in user_ids
                for websocket in self._connections.get(user_id, set())
            ]

        stale: list[tuple[str, WebSocket]] = []
        for user_id, websocket in subscribers:
            try:
                await websocket.send_json(notification)
            except Exception:
                stale.append((user_id, websocket))

        for user_id, websocket in stale:
            await self.disconnect(user_id, websocket)

    def subscriber_count(self) -> int:
        return sum(len(sockets) for sockets in self._connections.values())


notification_manager = NotificationManager()


def build_transaction_notification(
    *,
    event: str,
    transaction_id: str,
    transaction_no: str,
    status: str,
    actor_username: str = "",
) -> dict[str, Any]:
    labels = {
        "created": "تم إنشاء معاملة جديدة",
        "updated": "تم تحديث معاملة",
        "deleted": "تم حذف معاملة",
        "status_changed": "تغيرت حالة معاملة",
    }
    return {
        "id": str(uuid4()),
        "type": "transaction",
        "event": event,
        "title": labels.get(event, "تحديث في المعاملات"),
        "message": f"{transaction_no} — الحالة: {status or 'غير محددة'}",
        "transaction_id": str(transaction_id),
        "transaction_no": transaction_no,
        "status": status,
        "actor_username": actor_username,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
