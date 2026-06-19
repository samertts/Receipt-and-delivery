"""
Platform Core — Audit Service

Tamper-evident audit logging with chain verification.
Extracted from: lab_system/app/audit/logger.py, backend/app/core/audit.py
"""

from __future__ import annotations

import hashlib
import platform
from datetime import datetime
from typing import Any

from unified_platform.core.base import AuditEntry, PlatformService, ServiceHealth, ServiceStatus


class AuditService(PlatformService):
    """Unified audit logging service with tamper-evident hash chain."""

    @property
    def service_name(self) -> str:
        return "platform.audit"

    def health_check(self) -> ServiceHealth:
        return ServiceHealth(
            service_name=self.service_name,
            status=ServiceStatus.HEALTHY,
        )

    def log(self, entry: AuditEntry, conn=None) -> None:
        """Log an audit entry with hash chain."""
        ...

    def verify_chain(self, conn=None) -> tuple[bool, int, str]:
        """Verify the integrity of the audit chain."""
        ...

    def query(
        self,
        user_id: int | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        limit: int = 200,
        conn=None,
    ) -> list[dict[str, Any]]:
        """Query audit logs with filters."""
        ...

    def get_latest(self, limit: int = 10, conn=None) -> list[dict[str, Any]]:
        """Get most recent audit entries."""
        ...

    def compute_hash(self, entry: dict[str, Any]) -> str:
        """Compute SHA-256 hash for an audit entry."""
        raw = f"{entry.get('id', '')}|{entry.get('user_id', '')}|{entry.get('action', '')}|{entry.get('machine_name', '')}|{entry.get('timestamp', '')}|{entry.get('details', '')}|{entry.get('prev_hash', '')}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def log_action(self, user_id: int, action: str, details: str = "", conn=None) -> None:
        """Convenience method to log an action."""
        entry = AuditEntry(
            user_id=user_id,
            action=action,
            details=details,
            machine_name=platform.node(),
            timestamp=datetime.now(),
        )
        self.log(entry, conn=conn)
