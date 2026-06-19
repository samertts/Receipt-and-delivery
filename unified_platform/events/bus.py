"""
Platform Events — Event Bus for the unified platform.

Phase 5: Event-Driven Architecture
Constitution: Principle 9 (Event-Driven Readiness), Section C (AI Governance)
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class EventPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class EventStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class Event:
    """A platform event."""
    event_id: str
    event_type: str
    source: str
    entity_type: str = ""
    entity_id: int | str = ""
    user_id: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    status: EventStatus = EventStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: datetime | None = None
    error: str = ""
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class EventHandler:
    """A registered event handler."""
    handler_id: str
    event_type: str
    callback: Callable[[Event], None]
    priority: int = 0
    is_async: bool = False
    max_retries: int = 3


class EventBus:
    """Central event bus for the unified platform."""

    _instance: EventBus | None = None
    _lock = threading.Lock()

    def __new__(cls) -> EventBus:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._event_log: list[Event] = []
        self._event_count: dict[str, int] = defaultdict(int)
        self._error_count: dict[str, int] = defaultdict(int)
        self._processing_lock = threading.Lock()

    def subscribe(self, event_type: str, callback: Callable[[Event], None], priority: int = 0, handler_id: str = "") -> str:
        """Subscribe to an event type."""
        if not handler_id:
            handler_id = f"{event_type}_{int(time.time() * 1000)}"
        handler = EventHandler(
            handler_id=handler_id,
            event_type=event_type,
            callback=callback,
            priority=priority,
        )
        self._handlers[event_type].append(handler)
        self._handlers[event_type].sort(key=lambda h: h.priority, reverse=True)
        return handler_id

    def unsubscribe(self, handler_id: str) -> bool:
        """Unsubscribe from events."""
        for event_type in list(self._handlers.keys()):
            original_count = len(self._handlers[event_type])
            self._handlers[event_type] = [
                h for h in self._handlers[event_type]
                if h.handler_id != handler_id
            ]
            if len(self._handlers[event_type]) < original_count:
                return True
        return False

    def emit(self, event: Event) -> Event:
        """Emit an event to all registered handlers."""
        self._event_log.append(event)
        self._event_count[event.event_type] += 1

        handlers = self._handlers.get(event.event_type, [])
        if not handlers:
            # Also check for wildcard handlers
            handlers = self._handlers.get("*", [])

        event.status = EventStatus.PROCESSING

        for handler in handlers:
            try:
                handler.callback(event)
            except Exception as e:
                event.retry_count += 1
                if event.retry_count <= event.max_retries:
                    event.status = EventStatus.RETRYING
                    event.error = str(e)
                    self._error_count[event.event_type] += 1
                else:
                    event.status = EventStatus.FAILED
                    event.error = str(e)
                    self._error_count[event.event_type] += 1
                    break

        if event.status == EventStatus.PROCESSING:
            event.status = EventStatus.COMPLETED

        event.processed_at = datetime.utcnow()
        return event

    def emit_simple(self, event_type: str, source: str, entity_type: str = "", entity_id: int | str = "", **payload: Any) -> Event:
        """Emit a simple event with minimal parameters."""
        import uuid
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            source=source,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
        )
        return self.emit(event)

    def get_event_log(self, event_type: str | None = None, limit: int = 100) -> list[Event]:
        """Get event log, optionally filtered by type."""
        if event_type:
            events = [e for e in self._event_log if e.event_type == event_type]
        else:
            events = self._event_log
        return events[-limit:]

    def get_event_count(self, event_type: str | None = None) -> int:
        """Get event count."""
        if event_type:
            return self._event_count.get(event_type, 0)
        return sum(self._event_count.values())

    def get_error_count(self, event_type: str | None = None) -> int:
        """Get error count."""
        if event_type:
            return self._error_count.get(event_type, 0)
        return sum(self._error_count.values())

    def get_handler_count(self, event_type: str | None = None) -> int:
        """Get handler count."""
        if event_type:
            return len(self._handlers.get(event_type, []))
        return sum(len(handlers) for handlers in self._handlers.values())

    def get_health(self) -> dict[str, Any]:
        """Get event bus health status."""
        return {
            "total_events": self.get_event_count(),
            "total_errors": self.get_error_count(),
            "total_handlers": self.get_handler_count(),
            "event_types": dict(self._event_count),
            "error_types": dict(self._error_count),
        }

    def clear_log(self) -> int:
        """Clear event log. Returns count of events cleared."""
        count = len(self._event_log)
        self._event_log.clear()
        return count

    def reset(self) -> None:
        """Reset the event bus."""
        self._handlers.clear()
        self._event_log.clear()
        self._event_count.clear()
        self._error_count.clear()
