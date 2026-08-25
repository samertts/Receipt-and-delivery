"""Public key embedded into release builds by CI.

The checked-in value is intentionally empty. Release CI writes the public key
from a non-secret configuration value before PyInstaller runs. Never place the
Ed25519 private key in this file or in the repository.
"""

PUBLIC_KEY_B64 = ""
