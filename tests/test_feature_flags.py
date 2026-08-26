from __future__ import annotations

from lab_system.app.settings.features import (
    is_feature_enabled,
    telemetry_enabled,
    telemetry_payload,
)


def test_sensitive_features_are_disabled_by_default(monkeypatch):
    for name in ("cloud_sync", "ocr", "nfc", "gps", "temperature"):
        monkeypatch.delenv(f"LAB_FEATURE_{name.upper()}", raising=False)
        assert is_feature_enabled(name) is False


def test_feature_flag_can_be_disabled_or_enabled_explicitly(monkeypatch):
    monkeypatch.setenv("LAB_FEATURE_OCR", "true")
    assert is_feature_enabled("ocr") is True
    monkeypatch.setenv("LAB_FEATURE_OCR", "0")
    assert is_feature_enabled("ocr") is False
    assert is_feature_enabled("unknown") is False


def test_telemetry_is_opt_in_and_redacted(monkeypatch):
    monkeypatch.delenv("LAB_TELEMETRY_ENABLED", raising=False)
    assert telemetry_enabled() is False
    monkeypatch.setenv("LAB_TELEMETRY_ENABLED", "1")
    assert telemetry_enabled() is True
    payload = telemetry_payload(event="sync_failure", duration_ms=-10, success=False)
    assert payload == {"event": "sync_failure", "duration_ms": 0, "success": False}
    assert not any(key in payload for key in ("patient_id", "token", "details"))
