"""Default-off feature flags and privacy-preserving telemetry policy."""

from __future__ import annotations

import os


FEATURE_FLAGS = {
    "cloud_sync": False,
    "ocr": False,
    "nfc": False,
    "gps": False,
    "temperature": False,
    "advanced_reports": False,
}


def _env_key(name: str) -> str:
    return "LAB_FEATURE_" + name.upper().replace("-", "_")


def is_feature_enabled(name: str) -> bool:
    """Read a flag from environment; unknown flags are disabled."""
    if name not in FEATURE_FLAGS:
        return False
    raw = os.getenv(_env_key(name))
    if raw is None:
        return FEATURE_FLAGS[name]
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def telemetry_enabled() -> bool:
    """Telemetry is opt-in and emits only redacted operational metrics."""
    return os.getenv("LAB_TELEMETRY_ENABLED", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def telemetry_payload(*, event: str, duration_ms: int | None = None, success: bool | None = None) -> dict:
    """Build a non-PHI telemetry payload with no identifiers or free text."""
    payload: dict[str, object] = {"event": event[:80]}
    if duration_ms is not None:
        payload["duration_ms"] = max(0, int(duration_ms))
    if success is not None:
        payload["success"] = bool(success)
    return payload
