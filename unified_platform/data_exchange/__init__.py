"""
Platform Data Exchange — National Data Exchange Bus

Phase 3: National Data Exchange Bus
Constitution: Principle 51 (National Scale), Principle 9 (Event-Driven Readiness)
"""

from __future__ import annotations

import fnmatch
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class EventType(Enum):
    SYSTEM = "system"
    DOMAIN = "domain"
    INTEGRATION = "integration"
    AUDIT = "audit"


class EventSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PersistedEvent:
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.SYSTEM
    severity: EventSeverity = EventSeverity.INFO
    source: str = ""
    topic: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processed: bool = False
    retry_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingRule:
    rule_id: str
    source_pattern: str
    topic_pattern: str
    target_handler: str
    priority: int = 0
    enabled: bool = True


@dataclass
class EventCheckpoint:
    checkpoint_id: str
    last_event_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    position: int = 0


class DataExchangeBus:
    """National Data Exchange Bus with persistence, replay, and routing."""

    def __init__(self) -> None:
        self._events: dict[str, PersistedEvent] = {}
        self._event_order: list[str] = []
        self._routing_rules: dict[str, RoutingRule] = {}
        self._checkpoints: dict[str, EventCheckpoint] = {}

    def publish_event(self, event: PersistedEvent) -> bool:
        self._events[event.event_id] = event
        self._event_order.append(event.event_id)
        return True

    def get_event(self, event_id: str) -> PersistedEvent | None:
        return self._events.get(event_id)

    def list_events(
        self, topic: str | None = None, event_type: EventType | None = None
    ) -> list[PersistedEvent]:
        events = [self._events[eid] for eid in self._event_order if eid in self._events]
        if topic is not None:
            events = [e for e in events if e.topic == topic]
        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]
        return events

    def add_routing_rule(self, rule: RoutingRule) -> bool:
        self._routing_rules[rule.rule_id] = rule
        return True

    def remove_routing_rule(self, rule_id: str) -> bool:
        if rule_id in self._routing_rules:
            del self._routing_rules[rule_id]
            return True
        return False

    def route_event(self, event: PersistedEvent) -> list[str]:
        handlers: list[str] = []
        rules = sorted(
            [r for r in self._routing_rules.values() if r.enabled],
            key=lambda r: r.priority,
            reverse=True,
        )
        for rule in rules:
            source_match = fnmatch.fnmatch(event.source, rule.source_pattern)
            topic_match = fnmatch.fnmatch(event.topic, rule.topic_pattern)
            if source_match and topic_match:
                handlers.append(rule.target_handler)
        return handlers

    def create_checkpoint(self, checkpoint_id: str) -> EventCheckpoint:
        position = len(self._event_order)
        last_id = self._event_order[-1] if self._event_order else ""
        checkpoint = EventCheckpoint(
            checkpoint_id=checkpoint_id,
            last_event_id=last_id,
            position=position,
        )
        self._checkpoints[checkpoint_id] = checkpoint
        return checkpoint

    def get_checkpoint(self, checkpoint_id: str) -> EventCheckpoint | None:
        return self._checkpoints.get(checkpoint_id)

    def replay_from_checkpoint(
        self, checkpoint_id: str, handler_callback: Callable[[PersistedEvent], bool]
    ) -> int:
        checkpoint = self._checkpoints.get(checkpoint_id)
        if checkpoint is None:
            return 0
        count = 0
        for eid in self._event_order[checkpoint.position:]:
            event = self._events.get(eid)
            if event is not None:
                if handler_callback(event):
                    event.processed = True
                    count += 1
        checkpoint.position = len(self._event_order)
        checkpoint.last_event_id = self._event_order[-1] if self._event_order else ""
        checkpoint.timestamp = datetime.utcnow()
        return count

    def get_bus_report(self) -> dict[str, Any]:
        events = [self._events[eid] for eid in self._event_order if eid in self._events]
        return {
            "total_events": len(events),
            "processed_events": sum(1 for e in events if e.processed),
            "pending_events": sum(1 for e in events if not e.processed),
            "routing_rules": len(self._routing_rules),
            "active_rules": sum(1 for r in self._routing_rules.values() if r.enabled),
            "checkpoints": len(self._checkpoints),
            "event_types": {
                et.value: sum(1 for e in events if e.event_type == et)
                for et in EventType
            },
        }


__all__ = [
    "EventType",
    "EventSeverity",
    "PersistedEvent",
    "RoutingRule",
    "EventCheckpoint",
    "DataExchangeBus",
]
