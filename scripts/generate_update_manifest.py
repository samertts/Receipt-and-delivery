"""Generate a signed update manifest for the Windows installer.

The private key is read only from LAB_UPDATE_PRIVATE_KEY_B64 and is never
written to disk by this script. The matching public key must be embedded in the
application or supplied through LAB_UPDATE_PUBLIC_KEY_B64.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_payload(manifest: dict) -> bytes:
    unsigned = {key: value for key, value in manifest.items() if key != "signature"}
    return json.dumps(
        unsigned,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("installer", type=Path)
    parser.add_argument("--url", required=True, help="HTTPS URL of the installer")
    parser.add_argument("--output", type=Path, default=ROOT / "update.json")
    parser.add_argument("--release-notes", default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    installer = args.installer.resolve()
    if not installer.is_file():
        raise SystemExit(f"Installer not found: {installer}")
    if not args.url.lower().startswith("https://"):
        raise SystemExit("Installer URL must use HTTPS")

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not VERSION_RE.fullmatch(version):
        raise SystemExit(f"Invalid VERSION: {version}")

    private_key_b64 = os.getenv("LAB_UPDATE_PRIVATE_KEY_B64", "").strip()
    if not private_key_b64:
        raise SystemExit("LAB_UPDATE_PRIVATE_KEY_B64 is required for a signed manifest")

    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        private_key = Ed25519PrivateKey.from_private_bytes(
            base64.b64decode(private_key_b64, validate=True)
        )
    except Exception as exc:
        raise SystemExit(f"Invalid Ed25519 private key: {exc}") from exc

    manifest = {
        "version": version,
        "installer_url": args.url,
        "size": installer.stat().st_size,
        "sha256": sha256(installer),
        "release_notes": args.release_notes,
        "published_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "channel": "stable",
    }
    signature = private_key.sign(canonical_payload(manifest))
    manifest["signature"] = base64.b64encode(signature).decode("ascii")

    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Signed update manifest written to {args.output}")
    print(f"Version: {version}")
    print(f"Installer SHA-256: {manifest['sha256']}")
    print(f"Installer bytes: {manifest['size']}")


if __name__ == "__main__":
    main()
