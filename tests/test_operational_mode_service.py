from __future__ import annotations

import sqlite3

from lab_system.app.services.operational_mode_service import (
    OperationalMode,
    OperationalModeService,
)


def test_degraded_mode_requires_reason_and_persists(tmp_path):
    state_file = tmp_path / "mode.json"
    service = OperationalModeService(state_file)

    try:
        service.set_mode(OperationalMode.SAFE, "")
    except ValueError:
        pass
    else:
        raise AssertionError("degraded mode must require a reason")

    state = service.set_mode(OperationalMode.EMERGENCY, "API unavailable")
    assert state.mode == OperationalMode.EMERGENCY
    assert service.is_allowed("receive")
    assert not service.is_allowed("delete")

    restored = OperationalModeService(state_file)
    assert restored.state.mode == OperationalMode.EMERGENCY
    assert restored.state.reason == "API unavailable"


def test_safe_diagnostics_and_redacted_support_package(tmp_path):
    db_path = tmp_path / "lab.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE health_marker (id INTEGER PRIMARY KEY)")
        conn.commit()

    service = OperationalModeService(tmp_path / "mode.json")
    service.set_mode(OperationalMode.SAFE, "startup integrity failure")
    diagnostics = service.run_safe_diagnostics(db_path)
    assert diagnostics["checks"]

    package = service.export_diagnostics(tmp_path)
    assert package["success"] is True
    assert "patient data excluded" in package["redaction"]


def test_normal_mode_allows_operations_without_persisting_state():
    service = OperationalModeService()
    assert service.state.mode == OperationalMode.NORMAL
    assert service.is_allowed("receive")
    assert service.is_allowed("restore_backup")
