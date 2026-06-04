"""
Future API client abstraction for online synchronization.

This module provides a clean interface for communicating with
a remote synchronization server. It is intentionally kept as a
standalone abstraction — no actual HTTP calls are made.

To activate, implement _send() and register the concrete subclass
in SyncService.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SyncPayload:
    entries: list[dict[str, Any]] = field(default_factory=list)
    device_id: str = ''
    branch_id: str = ''


@dataclass
class SyncResponse:
    success: bool = False
    status_code: int = 0
    message: str = ''
    data: dict[str, Any] = field(default_factory=dict)


class APIClient:
    """Base API client. Subclass and override _send to activate."""

    def __init__(self, base_url: str = '', timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._enabled = False

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def enable(self, base_url: str, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False

    def push(self, payload: SyncPayload) -> SyncResponse:
        if not self._enabled:
            return SyncResponse(success=False, message='API client disabled')
        return self._send('POST', '/sync/push', payload)

    def pull(self, since: str = '', device_id: str = '') -> SyncResponse:
        if not self._enabled:
            return SyncResponse(success=False, message='API client disabled')
        return self._send('GET', '/sync/pull', {'since': since, 'device_id': device_id})

    def status(self) -> SyncResponse:
        if not self._enabled:
            return SyncResponse(success=False, message='API client disabled')
        return self._send('GET', '/sync/status', {})

    def _send(self, method: str, path: str, data: Any) -> SyncResponse:
        """
        Override this method to implement actual HTTP transport.
        Default returns a placeholder indicating the client is not activated.
        """
        return SyncResponse(
            success=False,
            status_code=501,
            message='APIClient._send() not implemented — sync is not yet activated',
        )


api_client = APIClient()
