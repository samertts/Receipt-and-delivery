"""Write the non-secret Ed25519 public key into the release build package."""

from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "lab_system" / "app" / "update_public_key.py"


def main() -> None:
    value = os.getenv("LAB_UPDATE_PUBLIC_KEY_B64", "").strip()
    if "--required" in sys.argv and not value:
        raise SystemExit("LAB_UPDATE_PUBLIC_KEY_B64 is required for tagged releases")
    if value:
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

            Ed25519PublicKey.from_public_bytes(base64.b64decode(value, validate=True))
        except Exception as exc:
            raise SystemExit(f"Invalid LAB_UPDATE_PUBLIC_KEY_B64: {exc}") from exc

    OUTPUT.write_text(
        '"""Generated release public key. Do not add a private key here."""\n\n'
        f'PUBLIC_KEY_B64 = {value!r}\n',
        encoding="utf-8",
    )
    print("Update public key prepared: " + ("configured" if value else "not configured"))


if __name__ == "__main__":
    main()
