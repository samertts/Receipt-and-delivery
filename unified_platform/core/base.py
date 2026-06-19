"""
Platform Core — Base interfaces and contracts for all platform services.

All platform services must implement these base interfaces.
This ensures consistency, testability, and future AI integration readiness.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol


# ============================================================================
# Core Enums
# ============================================================================

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class EventType(Enum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    RESTORED = "restored"
    FAILED = "failed"
    COMPLETED = "completed"
    STARTED = "started"


class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================================
# Core Data Contracts
# ============================================================================

@dataclass(frozen=True)
class ServiceHealth:
    """Standardized health status for any platform service."""
    service_name: str
    status: ServiceStatus
    message: str = ""
    latency_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PlatformEvent:
    """Standardized event contract for all platform events."""
    event_type: EventType
    source: str
    entity_type: str
    entity_id: int | str
    user_id: int | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
    idempotency_key: str = ""


@dataclass(frozen=True)
class AuditEntry:
    """Standardized audit entry contract."""
    user_id: int
    action: str
    entity_type: str = ""
    entity_id: int | str = ""
    details: str = ""
    machine_name: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    prev_hash: str = ""
    entry_hash: str = ""


@dataclass(frozen=True)
class NotificationMessage:
    """Standardized notification contract."""
    user_id: int
    title: str
    message: str
    severity: Severity = Severity.INFO
    channel: str = "toast"
    read: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BackupResult:
    """Standardized backup result contract."""
    success: bool
    backup_path: str = ""
    backup_size: int = 0
    duration_ms: float = 0.0
    error: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class RecoveryResult:
    """Standardized recovery result contract."""
    success: bool
    actions: list[str] = field(default_factory=list)
    error: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class SyncResult:
    """Standardized sync result contract."""
    success: bool
    synced: int = 0
    conflicts: int = 0
    failed: int = 0
    duration_ms: float = 0.0
    error: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class MetricsSnapshot:
    """Standardized metrics snapshot contract."""
    service: str
    metrics: dict[str, float | int | str]
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# Base Service Interface
# ============================================================================

class PlatformService(ABC):
    """Base interface for all platform services."""

    @property
    @abstractmethod
    def service_name(self) -> str:
        """Unique name of this service."""
        ...

    @abstractmethod
    def health_check(self) -> ServiceHealth:
        """Return current health status of this service."""
        ...

    def get_metrics(self) -> MetricsSnapshot:
        """Return current metrics for this service."""
        return MetricsSnapshot(
            service=self.service_name,
            metrics={"status": "ok"},
        )


# ============================================================================
# Event Emitter Interface
# ============================================================================

class EventEmitter(Protocol):
    """Interface for services that emit platform events."""

    def emit(self, event: PlatformEvent) -> None: ...


class EventHandler(Protocol):
    """Interface for services that handle platform events."""

    def handle(self, event: PlatformEvent) -> None: ...


# ============================================================================
# Telemetry Hooks
# ============================================================================

class TelemetryProvider(Protocol):
    """Interface for telemetry data providers."""

    def record_counter(self, name: str, value: int = 1, tags: dict[str, str] | None = None) -> None: ...

    def record_histogram(self, name: str, value: float, tags: dict[str, str] | None = None) -> None: ...

    def record_gauge(self, name: str, value: float, tags: dict[str, str] | None = None) -> None: ...
