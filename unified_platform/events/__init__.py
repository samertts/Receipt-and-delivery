"""
Platform Events — Event bus and event registry for the unified platform.
"""

from unified_platform.events.bus import EventBus, Event, EventPriority, EventStatus, EventHandler
from unified_platform.events.registry import (
    ReceiptEvents,
    BackupEvents,
    RecoveryEvents,
    SyncEvents,
    SecurityEvents,
    MANDATORY_EVENTS,
)

__all__ = [
    "EventBus",
    "Event",
    "EventPriority",
    "EventStatus",
    "EventHandler",
    "ReceiptEvents",
    "BackupEvents",
    "RecoveryEvents",
    "SyncEvents",
    "SecurityEvents",
    "MANDATORY_EVENTS",
]
