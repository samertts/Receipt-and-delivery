"""Operational modes for safe degradation and offline field work.

The service is deliberately UI-agnostic. It centralizes policy decisions so the
Qt UI, sync worker, and future hardware adapters do not each invent their own
interpretation of a degraded system.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lab_system.app.services.field_deployment_service import (
    HealthCheckWizard,
    RecoveryWizard,
    SupportPackageGenerator,
)


class OperationalMode:
    NORMAL = "normal"
    SAFE = "safe"
    EMERGENCY = "emergency"
    RESTRICTED = "restricted"


@dataclass
class ModeState:
    mode: str = OperationalMode.NORMAL
    reason: str = ""
    changed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class OperationalModeService:
    """Manage explicit degraded modes and expose an allow-list of operations."""

    _SAFE_OPERATIONS = frozenset(
        {"check_db", "restore_backup", "repair_config", "export_diagnostics", "recover_sync"}
    )
    _EMERGENCY_OPERATIONS = frozenset(
        {"receive", "transfer", "search", "scan", "print", "audit_local", "recover_sync"}
    )

    def __init__(self, state_file: str | Path | None = None):
        self._state_file = Path(state_file) if state_file else None
        self._state = self._load_state()

    def _load_state(self) -> ModeState:
        if self._state_file and self._state_file.exists():
            try:
                data = json.loads(self._state_file.read_text(encoding="utf-8"))
                if data.get("mode") in {
                    OperationalMode.NORMAL,
                    OperationalMode.SAFE,
                    OperationalMode.EMERGENCY,
                    OperationalMode.RESTRICTED,
                }:
                    return ModeState(
                        mode=data["mode"],
                        reason=str(data.get("reason", "")),
                        changed_at=str(data.get("changed_at", "")),
                    )
            except (OSError, json.JSONDecodeError, TypeError):
                pass
        env_mode = os.getenv("LAB_OPERATIONAL_MODE", "").strip().lower()
        if env_mode in {
            OperationalMode.SAFE,
            OperationalMode.EMERGENCY,
            OperationalMode.RESTRICTED,
        }:
            return ModeState(mode=env_mode, reason="configured by environment")
        return ModeState()

    @property
    def state(self) -> ModeState:
        return ModeState(
            mode=self._state.mode,
            reason=self._state.reason,
            changed_at=self._state.changed_at,
        )

    def set_mode(self, mode: str, reason: str) -> ModeState:
        if mode not in {
            OperationalMode.NORMAL,
            OperationalMode.SAFE,
            OperationalMode.EMERGENCY,
            OperationalMode.RESTRICTED,
        }:
            raise ValueError("invalid operational mode")
        if mode != OperationalMode.NORMAL and not reason.strip():
            raise ValueError("a reason is required for degraded mode")
        self._state = ModeState(mode=mode, reason=reason.strip())
        self._persist()
        return self.state

    def _persist(self) -> None:
        if not self._state_file:
            return
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self._state_file.with_suffix(self._state_file.suffix + ".tmp")
        temp_path.write_text(
            json.dumps(self._state.__dict__, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(temp_path, self._state_file)

    def is_allowed(self, operation: str) -> bool:
        if self._state.mode == OperationalMode.NORMAL:
            return True
        if self._state.mode == OperationalMode.SAFE:
            return operation in self._SAFE_OPERATIONS
        if self._state.mode == OperationalMode.EMERGENCY:
            return operation in self._EMERGENCY_OPERATIONS
        return operation in {"check_db", "export_diagnostics", "recover_sync"}

    def run_safe_diagnostics(self, db_path: str | Path) -> dict[str, Any]:
        """Run local checks without network calls or mutating business data."""
        return HealthCheckWizard(db_path).run()

    def restore_backup(self, backup_path: str | Path, target_path: str | Path) -> dict[str, Any]:
        if not self.is_allowed("restore_backup"):
            return {"success": False, "error": "restore is not allowed in current mode"}
        return RecoveryWizard(backup_path, target_path).run()

    def export_diagnostics(self, base_path: str | Path) -> dict[str, Any]:
        """Create a minimal support package; never copy DB, attachments, or tokens."""
        result = SupportPackageGenerator(base_path).generate()
        result["redaction"] = "database, attachments, credentials, and patient data excluded"
        return result
