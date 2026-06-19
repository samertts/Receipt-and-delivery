"""
Platform Core — Notification Service

Multi-channel notification delivery.
Status: NEW — must be created from scratch.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from unified_platform.core.base import (
    NotificationMessage,
    PlatformService,
    ServiceHealth,
    ServiceStatus,
    Severity,
)


@dataclass
class NotificationPreference:
    """User notification preferences."""
    user_id: int
    channels: tuple[str, ...] = ("toast",)
    enabled: bool = True
    quiet_hours_start: int = 22
    quiet_hours_end: int = 6


class NotificationService(PlatformService):
    """Multi-channel notification service."""

    @property
    def service_name(self) -> str:
        return "platform.notification"

    def health_check(self) -> ServiceHealth:
        return ServiceHealth(
            service_name=self.service_name,
            status=ServiceStatus.HEALTHY,
        )

    def send(self, notification: NotificationMessage, conn=None) -> bool:
        """Send a notification through appropriate channels."""
        ...

    def send_toast(self, user_id: int, title: str, message: str, severity: Severity = Severity.INFO) -> bool:
        """Send a desktop toast notification."""
        ...

    def send_bulk(self, notifications: list[NotificationMessage], conn=None) -> int:
        """Send multiple notifications. Returns count of successfully sent."""
        ...

    def get_user_notifications(self, user_id: int, unread_only: bool = False, limit: int = 50, conn=None) -> list[dict[str, Any]]:
        """Get notifications for a user."""
        ...

    def mark_read(self, notification_id: int, conn=None) -> bool:
        """Mark a notification as read."""
        ...

    def mark_all_read(self, user_id: int, conn=None) -> int:
        """Mark all notifications as read for a user. Returns count."""
        ...

    def get_unread_count(self, user_id: int, conn=None) -> int:
        """Get count of unread notifications for a user."""
        ...

    def set_preference(self, preference: NotificationPreference, conn=None) -> None:
        """Set notification preferences for a user."""
        ...

    def get_preference(self, user_id: int, conn=None) -> NotificationPreference:
        """Get notification preferences for a user."""
        ...

    def cleanup_old(self, days: int = 90, conn=None) -> int:
        """Remove notifications older than N days. Returns count removed."""
        ...
