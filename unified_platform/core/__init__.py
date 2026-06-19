"""
Platform Core — Centralized service exports.

All 11 platform core services are exported from this module.
"""

from unified_platform.core.base import (
    AuditEntry,
    BackupResult,
    EventType,
    MetricsSnapshot,
    NotificationMessage,
    PlatformEvent,
    PlatformService,
    RecoveryResult,
    ServiceHealth,
    ServiceStatus,
    Severity,
    SyncResult,
)
from unified_platform.core.identity import IdentityService
from unified_platform.core.authentication import AuthenticationService
from unified_platform.core.authorization import AuthorizationService
from unified_platform.core.audit import AuditService
from unified_platform.core.notifications import NotificationService
from unified_platform.core.configuration import ConfigurationService
from unified_platform.core.backup import BackupService
from unified_platform.core.recovery import RecoveryService
from unified_platform.core.reporting import ReportingService
from unified_platform.core.synchronization import SynchronizationService
from unified_platform.core.telemetry import TelemetryService

__all__ = [
    # Base contracts
    "AuditEntry",
    "BackupResult",
    "EventType",
    "MetricsSnapshot",
    "NotificationMessage",
    "PlatformEvent",
    "PlatformService",
    "RecoveryResult",
    "ServiceHealth",
    "ServiceStatus",
    "Severity",
    "SyncResult",
    # Services
    "IdentityService",
    "AuthenticationService",
    "AuthorizationService",
    "AuditService",
    "NotificationService",
    "ConfigurationService",
    "BackupService",
    "RecoveryService",
    "ReportingService",
    "SynchronizationService",
    "TelemetryService",
]
