"""
Platform Registry — Event Registry

Tracks all platform events and their handlers.
Constitution: Principle 9 (Event-Driven Readiness), Principle 30 (One Audit)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from unified_platform.registry.base import RegistryEntry


@dataclass
class EventEntry(RegistryEntry):
    """A registered event in the platform."""
    event_id: str = ""
    event_type: str = ""  # receipt, backup, recovery, sync, security, system
    source_module: str = ""
    payload_schema: dict[str, Any] = field(default_factory=dict)
    handlers: tuple[str, ...] = ()
    is_critical: bool = False
    is_auditable: bool = True
    retention_days: int = 90


class EventRegistry:
    """Central registry for all platform events."""

    def __init__(self) -> None:
        self._events: dict[str, EventEntry] = {}
        self._handlers: dict[str, list[Callable]] = {}

    def register(self, event: EventEntry) -> None:
        """Register an event type."""
        self._events[event.name] = event

    def unregister(self, name: str) -> bool:
        """Unregister an event type."""
        if name in self._events:
            del self._events[name]
            return True
        return False

    def get(self, name: str) -> EventEntry | None:
        """Get an event by name."""
        return self._events.get(name)

    def list_all(self) -> list[EventEntry]:
        """List all registered events."""
        return list(self._events.values())

    def list_by_type(self, event_type: str) -> list[EventEntry]:
        """List all events of a specific type."""
        return [e for e in self._events.values() if e.event_type == event_type]

    def list_critical(self) -> list[EventEntry]:
        """List all critical events."""
        return [e for e in self._events.values() if e.is_critical]

    def list_auditable(self) -> list[EventEntry]:
        """List all auditable events."""
        return [e for e in self._events.values() if e.is_auditable]

    def list_by_module(self, module: str) -> list[EventEntry]:
        """List all events from a module."""
        return [e for e in self._events.values() if e.source_module == module]

    def register_handler(self, event_name: str, handler: Callable) -> None:
        """Register a handler for an event."""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)

    def get_handlers(self, event_name: str) -> list[Callable]:
        """Get all handlers for an event."""
        return self._handlers.get(event_name, [])

    def emit(self, event_name: str, payload: dict[str, Any]) -> int:
        """Emit an event to all registered handlers. Returns count of handlers called."""
        handlers = self._handlers.get(event_name, [])
        for handler in handlers:
            handler(payload)
        return len(handlers)

    def export_registry(self) -> dict[str, Any]:
        """Export the full registry."""
        return {
            name: {
                "name": e.name,
                "event_type": e.event_type,
                "source_module": e.source_module,
                "is_critical": e.is_critical,
                "is_auditable": e.is_auditable,
                "retention_days": e.retention_days,
                "handler_count": len(self._handlers.get(name, [])),
            }
            for name, e in self._events.items()
        }
