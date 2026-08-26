"""Secure update checks for the frozen Windows desktop application.

The updater deliberately separates discovery from installation. It accepts only
HTTPS manifests, verifies an Ed25519 signature over canonical JSON, verifies the
installer SHA-256 after streaming download, and never uses shell=True.

Set UPDATE_PUBLIC_KEY_B64 at build time or replace the empty constant with the
public key produced by the release key-management process. The private signing
key must never be committed to the repository or embedded in the application.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from urllib.parse import urlsplit
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from lab_system.app.settings.config import CONFIG
from lab_system.app.update_public_key import PUBLIC_KEY_B64

DEFAULT_MANIFEST_URL = os.getenv(
    "LAB_UPDATE_MANIFEST_URL",
    "https://github.com/samertts/Receipt-and-delivery/releases/latest/download/update.json",
).strip()
UPDATE_PUBLIC_KEY_B64 = os.getenv("LAB_UPDATE_PUBLIC_KEY_B64", "").strip() or PUBLIC_KEY_B64
MAX_INSTALLER_BYTES = 300 * 1024 * 1024
_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$")


def is_startup_check_enabled(
    platform: str | None = None,
    public_key: str | None = None,
) -> bool:
    """Enable the automatic startup check only for configured Windows builds."""
    effective_platform = os.name if platform is None else platform
    effective_key = public_key if public_key is not None else UPDATE_PUBLIC_KEY_B64
    return effective_platform == "nt" and bool(effective_key)


class UpdateError(RuntimeError):
    """Base class for expected update failures."""


class UpdateSecurityError(UpdateError):
    """Raised when an update cannot be authenticated or validated."""


class UpdateDownloadError(UpdateError):
    """Raised when the installer cannot be downloaded or verified."""


def _parse_version(version: str) -> tuple[int, int, int]:
    match = _VERSION_RE.fullmatch(version.strip())
    if not match:
        raise UpdateSecurityError(f"Invalid version format: {version!r}")
    return tuple(int(part) for part in match.groups())


def is_newer_version(candidate: str, current: str) -> bool:
    """Return whether candidate is a newer stable semantic version."""
    return _parse_version(candidate) > _parse_version(current)


def _canonical_payload(manifest: dict[str, Any]) -> bytes:
    unsigned = {key: value for key, value in manifest.items() if key != "signature"}
    return json.dumps(
        unsigned,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _decode_b64(value: str, label: str) -> bytes:
    try:
        return base64.b64decode(value, validate=True)
    except (ValueError, TypeError) as exc:
        raise UpdateSecurityError(f"Invalid {label} encoding") from exc


def verify_manifest_signature(manifest: dict[str, Any], public_key_b64: str | None = None) -> None:
    """Verify the Ed25519 signature carried in a manifest.

    The cryptographic dependency is imported lazily so the application can still
    start on installations where update support has not been provisioned yet.
    """
    public_key_b64 = (public_key_b64 or UPDATE_PUBLIC_KEY_B64).strip()
    signature_b64 = str(manifest.get("signature", "")).strip()
    if not public_key_b64:
        raise UpdateSecurityError(
            "Update public key is not configured; refusing unsigned update"
        )
    if not signature_b64:
        raise UpdateSecurityError("Update manifest has no signature")

    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        public_key = Ed25519PublicKey.from_public_bytes(
            _decode_b64(public_key_b64, "public key")
        )
        public_key.verify(_decode_b64(signature_b64, "signature"), _canonical_payload(manifest))
    except UpdateSecurityError:
        raise
    except Exception as exc:
        raise UpdateSecurityError("Update manifest signature verification failed") from exc


def _validate_manifest(manifest: Any) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise UpdateSecurityError("Update manifest must be a JSON object")

    required = ("version", "installer_url", "sha256", "signature")
    missing = [key for key in required if not manifest.get(key)]
    if missing:
        raise UpdateSecurityError(f"Update manifest is missing: {', '.join(missing)}")

    version = str(manifest["version"]).strip()
    _parse_version(version)
    installer_url = str(manifest["installer_url"]).strip()
    if not installer_url.lower().startswith("https://"):
        raise UpdateSecurityError("Installer URL must use HTTPS")

    digest = str(manifest["sha256"]).strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise UpdateSecurityError("Installer SHA-256 must be 64 hexadecimal characters")

    verify_manifest_signature(manifest)
    return dict(manifest)


def fetch_manifest(manifest_url: str = DEFAULT_MANIFEST_URL, timeout: float = 10.0) -> dict[str, Any]:
    """Fetch and authenticate an update manifest over HTTPS."""
    parsed_manifest_url = urlsplit(manifest_url)
    if parsed_manifest_url.scheme.lower() != "https" or not parsed_manifest_url.netloc:
        raise UpdateSecurityError("Update manifest URL must use HTTPS")
    request = urllib.request.Request(
        manifest_url,
        headers={"Accept": "application/json", "User-Agent": "LabReceiptSystem-Updater"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310 - HTTPS-only URL and final redirect are validated
            final_url = response.geturl() if hasattr(response, "geturl") else request.full_url
            if urlsplit(final_url).scheme.lower() != "https":
                raise UpdateSecurityError("Update manifest redirect must use HTTPS")
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, UnicodeDecodeError) as exc:
        raise UpdateError(f"Unable to fetch update manifest: {exc}") from exc
    return _validate_manifest(payload)


def check_for_update(
    current_version: str | None = None,
    manifest_url: str = DEFAULT_MANIFEST_URL,
) -> dict[str, Any] | None:
    """Return a verified update manifest only when it is newer than the app."""
    current_version = current_version or CONFIG.app_version
    manifest = fetch_manifest(manifest_url)
    if not is_newer_version(str(manifest["version"]), current_version):
        return None
    return manifest


def download_installer(
    manifest: dict[str, Any],
    destination_dir: Path | None = None,
    timeout: float = 30.0,
) -> Path:
    """Stream a verified installer into the private updates directory."""
    manifest = _validate_manifest(manifest)
    destination_dir = destination_dir or (CONFIG.storage_dir / "updates")
    destination_dir.mkdir(parents=True, exist_ok=True)

    installer_url = str(manifest["installer_url"])
    parsed_installer_url = urlsplit(installer_url)
    if parsed_installer_url.scheme.lower() != "https" or not parsed_installer_url.netloc:
        raise UpdateSecurityError("Installer URL must use HTTPS")
    request = urllib.request.Request(
        installer_url,
        headers={"Accept": "application/octet-stream", "User-Agent": "LabReceiptSystem-Updater"},
    )
    expected_size = int(manifest.get("size", 0) or 0)
    if expected_size < 0 or expected_size > MAX_INSTALLER_BYTES:
        raise UpdateDownloadError("Manifest installer size is invalid")

    temp_path: Path | None = None
    digest = hashlib.sha256()
    total = 0
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310 - signed manifest URL is HTTPS and redirect is checked
            final_url = response.geturl() if hasattr(response, "geturl") else request.full_url
            if urlsplit(final_url).scheme.lower() != "https":
                raise UpdateSecurityError("Installer redirect must use HTTPS")
            with tempfile.NamedTemporaryFile(
                prefix="LabReceiptSetup-",
                suffix=".exe.part",
                dir=destination_dir,
                delete=False,
            ) as output:
                temp_path = Path(output.name)
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_INSTALLER_BYTES:
                        raise UpdateDownloadError("Installer exceeds the maximum allowed size")
                    output.write(chunk)
                    digest.update(chunk)
        if expected_size and total != expected_size:
            raise UpdateDownloadError("Downloaded installer size does not match manifest")
        if digest.hexdigest().lower() != str(manifest["sha256"]).lower():
            raise UpdateSecurityError("Downloaded installer SHA-256 does not match manifest")
        final_path = destination_dir / f"LabReceiptSetup-{manifest['version']}.exe"
        temp_path.replace(final_path)
        return final_path
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise UpdateDownloadError(f"Unable to download update: {exc}") from exc
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)


def launch_installer(installer_path: Path) -> None:
    """Launch a verified Inno Setup installer without shell execution."""
    if os.name != "nt":
        raise UpdateError("Automatic installer launch is available on Windows only")
    installer_path = installer_path.resolve()
    if installer_path.suffix.lower() != ".exe" or not installer_path.is_file():
        raise UpdateSecurityError("Installer path is invalid")
    subprocess.Popen([str(installer_path)], close_fds=True)
