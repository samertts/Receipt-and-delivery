"""Local, validated branding settings for printed laboratory receipts."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

from lab_system.app.settings.config import CONFIG
from lab_system.app.utils.errors import ValidationError


DEFAULT_BRANDING = {
    "company_name": "نظام إدارة الاستلام المختبري",
    "subtitle": "إيصال رسمي",
    "footer": "",
    "logo_path": "",
    "primary_color": "#1D4E89",
    "layout": "a4",
}
_ALLOWED_LAYOUTS = {"a4", "a5", "a4-two-up"}
_HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
_ALLOWED_LOGO_EXTENSIONS = {".png", ".jpg", ".jpeg"}


class ReceiptBrandingService:
    """Read and atomically write non-secret local receipt branding settings."""

    def __init__(self, settings_path: Path | None = None) -> None:
        self.settings_path = settings_path or CONFIG.storage_dir / "settings" / "receipt_branding.json"

    def load(self) -> dict[str, str]:
        values = dict(DEFAULT_BRANDING)
        try:
            raw = json.loads(self.settings_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                values.update({key: raw[key] for key in DEFAULT_BRANDING if key in raw})
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass
        try:
            return self.validate(values)
        except ValidationError:
            return dict(DEFAULT_BRANDING)

    def save(self, values: dict[str, str]) -> dict[str, str]:
        normalized = self.validate({**DEFAULT_BRANDING, **values})
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(
            prefix="receipt_branding.", suffix=".tmp", dir=str(self.settings_path.parent)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(normalized, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_name, self.settings_path)
            try:
                self.settings_path.chmod(0o600)
            except OSError:
                pass
        finally:
            Path(temporary_name).unlink(missing_ok=True)
        return normalized

    @staticmethod
    def validate(values: dict[str, str]) -> dict[str, str]:
        normalized = dict(DEFAULT_BRANDING)
        for key in ("company_name", "subtitle", "footer"):
            value = str(values.get(key, "")).strip()
            if len(value) > 240:
                raise ValidationError(f"{key} is too long")
            normalized[key] = value

        logo_path = str(values.get("logo_path", "")).strip()
        if logo_path:
            path = Path(logo_path).expanduser()
            if path.suffix.lower() not in _ALLOWED_LOGO_EXTENSIONS or not path.is_file():
                raise ValidationError("logo must be an existing PNG or JPEG file")
            if path.stat().st_size > 5 * 1024 * 1024:
                raise ValidationError("logo is too large")
            normalized["logo_path"] = str(path.resolve())

        primary_color = str(values.get("primary_color", DEFAULT_BRANDING["primary_color"])).strip()
        if not _HEX_COLOR.fullmatch(primary_color):
            raise ValidationError("primary color must be a six-digit hexadecimal color")
        normalized["primary_color"] = primary_color.upper()

        layout = str(values.get("layout", "a4")).strip().lower()
        if layout not in _ALLOWED_LAYOUTS:
            raise ValidationError("unsupported receipt layout")
        normalized["layout"] = layout
        return normalized
