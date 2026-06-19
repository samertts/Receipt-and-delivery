"""
Platform Mobile — Mobile Ecosystem Readiness

Phase 8: Mobile Ecosystem Readiness
Constitution: Principle 54 (Offline First)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class MobilePlatform(Enum):
    ANDROID = "android"
    IOS = "ios"
    TABLET = "tablet"
    WEB = "web"


class SyncMode(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    MANUAL = "manual"
    REALTIME = "realtime"


class OfflineCapability(Enum):
    FULL = "full"           # Full offline support
    PARTIAL = "partial"     # Limited offline support
    VIEW_ONLY = "view_only" # Can view cached data only
    NONE = "none"           # No offline support


# ============================================================================
# Android Contracts
# ============================================================================

@dataclass
class AndroidContract:
    """API contract for Android mobile clients."""
    min_version: str = "1.0.0"
    max_version: str = ""
    api_base: str = "/api/v1"
    auth_method: str = "jwt"
    sync_mode: SyncMode = SyncMode.INCREMENTAL
    offline_capability: OfflineCapability = OfflineCapability.FULL
    supported_features: tuple[str, ...] = (
        "receipts",
        "organizations",
        "search",
        "scan_qr",
        "attachments",
    )
    push_notifications: bool = True
    camera_integration: bool = True
    barcode_scanning: bool = True
    gps_location: bool = False


# ============================================================================
# Tablet Contracts
# ============================================================================

@dataclass
class TabletContract:
    """API contract for tablet clients."""
    min_version: str = "1.0.0"
    api_base: str = "/api/v1"
    auth_method: str = "jwt"
    sync_mode: SyncMode = SyncMode.REALTIME
    offline_capability: OfflineCapability = OfflineCapability.FULL
    supported_features: tuple[str, ...] = (
        "receipts",
        "organizations",
        "reports",
        "search",
        "scan_qr",
        "attachments",
        "dashboard",
        "settings",
    )
    push_notifications: bool = True
    camera_integration: bool = True
    printer_support: bool = True
    large_screen_optimized: bool = True


# ============================================================================
# Offline Contracts
# ============================================================================

@dataclass
class OfflineContract:
    """Contract for offline-first operations."""
    max_offline_hours: int = 72
    max_cached_records: int = 10000
    auto_sync_on_reconnect: bool = True
    conflict_resolution: str = "last-writer-wins"
    offline_queue_limit: int = 500
    supported_operations: tuple[str, ...] = (
        "create_receipt",
        "update_receipt",
        "view_receipt",
        "search",
        "view_organization",
        "create_attachment",
    )
    blocked_operations: tuple[str, ...] = (
        "delete_receipt",
        "user_management",
        "system_settings",
    )
    sync_priority: tuple[str, ...] = (
        "receipts",
        "organizations",
        "attachments",
        "audit_logs",
    )


# ============================================================================
# Sync Contracts
# ============================================================================

@dataclass
class SyncContract:
    """Contract for mobile synchronization."""
    protocol: str = "rest"
    transport: str = "https"
    compression: str = "gzip"
    batch_size: int = 100
    max_payload_mb: int = 10
    retry_strategy: str = "exponential_backoff"
    max_retries: int = 5
    conflict_resolution: str = "last-writer-wins"
    incremental_sync: bool = True
    delta_compression: bool = True


# ============================================================================
# Attachment Contracts
# ============================================================================

@dataclass
class AttachmentContract:
    """Contract for mobile attachment handling."""
    max_file_size_mb: int = 50
    supported_formats: tuple[str, ...] = (".pdf", ".jpg", ".jpeg", ".png")
    thumbnail_generation: bool = True
    thumbnail_max_size: tuple[int, int] = (200, 200)
    image_compression: bool = True
    image_quality: int = 80
    max_image_resolution: tuple[int, int] = (4000, 4000)
    offline_upload_queue: bool = True
    auto_upload_on_wifi: bool = True


# ============================================================================
# Authentication Contracts
# ============================================================================

@dataclass
class MobileAuthContract:
    """Contract for mobile authentication."""
    auth_methods: tuple[str, ...] = ("jwt", "biometric", "pin")
    jwt_expiry_hours: int = 24
    refresh_token_expiry_days: int = 30
    biometric_enabled: bool = True
    pin_code_enabled: bool = True
    pin_length: int = 6
    max_failed_attempts: int = 5
    lockout_duration_minutes: int = 30
    remember_device: bool = True
    device_limit: int = 3


# ============================================================================
# Notification Contracts
# ============================================================================

@dataclass
class MobileNotificationContract:
    """Contract for mobile notifications."""
    push_enabled: bool = True
    push_provider: str = "fcm"  # Firebase Cloud Messaging
    notification_types: tuple[str, ...] = (
        "receipt_created",
        "receipt_updated",
        "receipt_approved",
        "sync_complete",
        "backup_complete",
        "security_alert",
    )
    quiet_hours_enabled: bool = True
    quiet_hours_start: int = 22
    quiet_hours_end: int = 6
    batch_notifications: bool = True
    offline_notification_queue: bool = True


# ============================================================================
# Mobile Readiness Manager
# ============================================================================

class MobileReadinessManager:
    """Central manager for mobile ecosystem readiness."""

    def __init__(self) -> None:
        self.android = AndroidContract()
        self.tablet = TabletContract()
        self.offline = OfflineContract()
        self.sync = SyncContract()
        self.attachment = AttachmentContract()
        self.auth = MobileAuthContract()
        self.notification = MobileNotificationContract()

    def get_readiness_report(self) -> dict[str, Any]:
        return {
            "android": {
                "min_version": self.android.min_version,
                "offline_capability": self.android.offline_capability.value,
                "sync_mode": self.android.sync_mode.value,
                "features": list(self.android.supported_features),
            },
            "tablet": {
                "min_version": self.tablet.min_version,
                "offline_capability": self.tablet.offline_capability.value,
                "features": list(self.tablet.supported_features),
            },
            "offline": {
                "max_offline_hours": self.offline.max_offline_hours,
                "max_cached_records": self.offline.max_cached_records,
                "auto_sync": self.offline.auto_sync_on_reconnect,
            },
            "sync": {
                "protocol": self.sync.protocol,
                "batch_size": self.sync.batch_size,
                "conflict_resolution": self.sync.conflict_resolution,
            },
            "attachment": {
                "max_file_size_mb": self.attachment.max_file_size_mb,
                "formats": list(self.attachment.supported_formats),
            },
            "auth": {
                "methods": list(self.auth.auth_methods),
                "jwt_expiry_hours": self.auth.jwt_expiry_hours,
                "biometric": self.auth.biometric_enabled,
            },
            "notification": {
                "push_enabled": self.notification.push_enabled,
                "provider": self.notification.push_provider,
                "types": list(self.notification.notification_types),
            },
            "mobile_ready": True,
        }
