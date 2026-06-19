"""
APIClient — HTTP transport for online synchronization.

Provides push / pull / status methods backed by urllib.request.
No external dependencies required.
"""

from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SyncPayload:
    entries: list[dict[str, Any]] = field(default_factory=list)
    device_id: str = ""
    branch_id: str = ""


@dataclass
class SyncResponse:
    success: bool = False
    status_code: int = 0
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)


class APIClient:
    """API client with HTTP transport via urllib."""

    def __init__(self, base_url: str = "", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._enabled = False
        self._token: str = ""

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def enable(self, base_url: str, token: str = "", timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self._token = token
        self.timeout = timeout
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False
        self._token = ""

    def set_token(self, token: str) -> None:
        self._token = token

    def push(self, payload: SyncPayload) -> SyncResponse:
        if not self._enabled:
            return SyncResponse(success=False, message="API client disabled")
        return self._send("POST", "/sync/push", payload.__dict__)

    def pull(self, since: str = "", device_id: str = "") -> SyncResponse:
        if not self._enabled:
            return SyncResponse(success=False, message="API client disabled")
        params = {"since": since, "device_id": device_id}
        return self._send("GET", f"/sync/pull?{urllib.parse.urlencode(params)}", None)

    def status(self) -> SyncResponse:
        if not self._enabled:
            return SyncResponse(success=False, message="API client disabled")
        return self._send("GET", "/sync/status", None)

    def _send(self, method: str, path: str, data: Any) -> SyncResponse:
        url = f"{self.base_url}{path}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")

        max_retries = 3
        for attempt in range(max_retries):
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    resp_body = resp.read().decode("utf-8")
                    resp_data: dict[str, Any] = {}
                    if resp_body:
                        resp_data = json.loads(resp_body)
                    return SyncResponse(
                        success=True,
                        status_code=resp.status,
                        message="OK",
                        data=resp_data,
                    )
            except urllib.error.HTTPError as e:
                if e.code >= 500 and attempt < max_retries - 1:
                    wait_time = (2**attempt) + random.uniform(0, 1)
                    time.sleep(wait_time)
                    continue
                resp_body = e.read().decode("utf-8", errors="replace")
                resp_data = {}
                if resp_body:
                    try:
                        resp_data = json.loads(resp_body)
                    except json.JSONDecodeError:
                        resp_data = {"raw": resp_body}
                return SyncResponse(
                    success=False,
                    status_code=e.code,
                    message=resp_data.get("detail", str(e)),
                    data=resp_data,
                )
            except urllib.error.URLError as e:
                if attempt < max_retries - 1:
                    wait_time = (2**attempt) + random.uniform(0, 1)
                    time.sleep(wait_time)
                    continue
                return SyncResponse(
                    success=False,
                    status_code=0,
                    message=f"Connection failed: {e.reason}",
                )
            except Exception as e:
                return SyncResponse(
                    success=False,
                    status_code=0,
                    message=str(e),
                )
        return SyncResponse(
            success=False, status_code=0, message="Max retries exceeded"
        )


api_client = APIClient()
