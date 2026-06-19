"""
Platform Events — Mandatory Event Definitions

Phase 5: Event Platform
Constitution: Principle 9 (Event-Driven Readiness)
"""

from __future__ import annotations

from unified_platform.events.bus import Event, EventPriority


# ============================================================================
# Receipt Events
# ============================================================================

class ReceiptEvents:
    """Receipt-related events."""
    CREATED = "ReceiptCreated"
    UPDATED = "ReceiptUpdated"
    DELETED = "ReceiptDeleted"
    RESTORED = "ReceiptRestored"

    @staticmethod
    def created(entity_id: int, user_id: int, **payload) -> Event:
        return Event(
            event_id="",
            event_type=ReceiptEvents.CREATED,
            source="receipt_service",
            entity_type="receipt",
            entity_id=entity_id,
            user_id=user_id,
            payload=payload,
            priority=EventPriority.HIGH,
        )

    @staticmethod
    def updated(entity_id: int, user_id: int, **payload) -> Event:
        return Event(
            event_id="",
            event_type=ReceiptEvents.UPDATED,
            source="receipt_service",
            entity_type="receipt",
            entity_id=entity_id,
            user_id=user_id,
            payload=payload,
        )

    @staticmethod
    def deleted(entity_id: int, user_id: int, **payload) -> Event:
        return Event(
            event_id="",
            event_type=ReceiptEvents.DELETED,
            source="receipt_service",
            entity_type="receipt",
            entity_id=entity_id,
            user_id=user_id,
            payload=payload,
            priority=EventPriority.HIGH,
        )

    @staticmethod
    def restored(entity_id: int, user_id: int, **payload) -> Event:
        return Event(
            event_id="",
            event_type=ReceiptEvents.RESTORED,
            source="receipt_service",
            entity_type="receipt",
            entity_id=entity_id,
            user_id=user_id,
            payload=payload,
            priority=EventPriority.HIGH,
        )


# ============================================================================
# Backup Events
# ============================================================================

class BackupEvents:
    """Backup-related events."""
    CREATED = "BackupCreated"
    VERIFIED = "BackupVerified"
    FAILED = "BackupFailed"

    @staticmethod
    def created(entity_id: str, user_id: int | None = None, **payload) -> Event:
        return Event(
            event_id="",
            event_type=BackupEvents.CREATED,
            source="backup_service",
            entity_type="backup",
            entity_id=entity_id,
            user_id=user_id,
            payload=payload,
            priority=EventPriority.HIGH,
        )

    @staticmethod
    def verified(entity_id: str, **payload) -> Event:
        return Event(
            event_id="",
            event_type=BackupEvents.VERIFIED,
            source="backup_service",
            entity_type="backup",
            entity_id=entity_id,
            payload=payload,
        )

    @staticmethod
    def failed(entity_id: str, error: str = "", **payload) -> Event:
        return Event(
            event_id="",
            event_type=BackupEvents.FAILED,
            source="backup_service",
            entity_type="backup",
            entity_id=entity_id,
            payload={**payload, "error": error},
            priority=EventPriority.CRITICAL,
        )


# ============================================================================
# Recovery Events
# ============================================================================

class RecoveryEvents:
    """Recovery-related events."""
    STARTED = "RecoveryStarted"
    COMPLETED = "RecoveryCompleted"
    FAILED = "RecoveryFailed"

    @staticmethod
    def started(entity_id: str, user_id: int | None = None, **payload) -> Event:
        return Event(
            event_id="",
            event_type=RecoveryEvents.STARTED,
            source="recovery_service",
            entity_type="recovery",
            entity_id=entity_id,
            user_id=user_id,
            payload=payload,
            priority=EventPriority.CRITICAL,
        )

    @staticmethod
    def completed(entity_id: str, **payload) -> Event:
        return Event(
            event_id="",
            event_type=RecoveryEvents.COMPLETED,
            source="recovery_service",
            entity_type="recovery",
            entity_id=entity_id,
            payload=payload,
            priority=EventPriority.HIGH,
        )

    @staticmethod
    def failed(entity_id: str, error: str = "", **payload) -> Event:
        return Event(
            event_id="",
            event_type=RecoveryEvents.FAILED,
            source="recovery_service",
            entity_type="recovery",
            entity_id=entity_id,
            payload={**payload, "error": error},
            priority=EventPriority.CRITICAL,
        )


# ============================================================================
# Sync Events
# ============================================================================

class SyncEvents:
    """Synchronization-related events."""
    STARTED = "SyncStarted"
    COMPLETED = "SyncCompleted"
    FAILED = "SyncFailed"

    @staticmethod
    def started(entity_id: str = "", user_id: int | None = None, **payload) -> Event:
        return Event(
            event_id="",
            event_type=SyncEvents.STARTED,
            source="sync_service",
            entity_type="sync",
            entity_id=entity_id,
            user_id=user_id,
            payload=payload,
        )

    @staticmethod
    def completed(entity_id: str = "", **payload) -> Event:
        return Event(
            event_id="",
            event_type=SyncEvents.COMPLETED,
            source="sync_service",
            entity_type="sync",
            entity_id=entity_id,
            payload=payload,
        )

    @staticmethod
    def failed(entity_id: str = "", error: str = "", **payload) -> Event:
        return Event(
            event_id="",
            event_type=SyncEvents.FAILED,
            source="sync_service",
            entity_type="sync",
            entity_id=entity_id,
            payload={**payload, "error": error},
            priority=EventPriority.HIGH,
        )


# ============================================================================
# Security Events
# ============================================================================

class SecurityEvents:
    """Security-related events."""
    PERMISSION_DENIED = "PermissionDenied"
    AUTHENTICATION_FAILED = "AuthenticationFailed"
    AUDIT_VIOLATION = "AuditViolationDetected"

    @staticmethod
    def permission_denied(user_id: int | None = None, permission: str = "", **payload) -> Event:
        return Event(
            event_id="",
            event_type=SecurityEvents.PERMISSION_DENIED,
            source="authorization_service",
            entity_type="security",
            user_id=user_id,
            payload={**payload, "permission": permission},
            priority=EventPriority.HIGH,
        )

    @staticmethod
    def authentication_failed(username: str = "", **payload) -> Event:
        return Event(
            event_id="",
            event_type=SecurityEvents.AUTHENTICATION_FAILED,
            source="authentication_service",
            entity_type="security",
            payload={**payload, "username": username},
            priority=EventPriority.HIGH,
        )

    @staticmethod
    def audit_violation(user_id: int | None = None, details: str = "", **payload) -> Event:
        return Event(
            event_id="",
            event_type=SecurityEvents.AUDIT_VIOLATION,
            source="audit_service",
            entity_type="security",
            user_id=user_id,
            payload={**payload, "details": details},
            priority=EventPriority.CRITICAL,
        )


# ============================================================================
# All Mandatory Events
# ============================================================================

MANDATORY_EVENTS = [
    # Receipt Events
    ReceiptEvents.CREATED,
    ReceiptEvents.UPDATED,
    ReceiptEvents.DELETED,
    ReceiptEvents.RESTORED,
    # Backup Events
    BackupEvents.CREATED,
    BackupEvents.VERIFIED,
    BackupEvents.FAILED,
    # Recovery Events
    RecoveryEvents.STARTED,
    RecoveryEvents.COMPLETED,
    RecoveryEvents.FAILED,
    # Sync Events
    SyncEvents.STARTED,
    SyncEvents.COMPLETED,
    SyncEvents.FAILED,
    # Security Events
    SecurityEvents.PERMISSION_DENIED,
    SecurityEvents.AUTHENTICATION_FAILED,
    SecurityEvents.AUDIT_VIOLATION,
]
