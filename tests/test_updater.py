import base64
import hashlib
import json
import pytest

from lab_system.app import updater


class _Response:
    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        if size == -1:
            payload, self.payload = self.payload, b""
            return payload
        payload, self.payload = self.payload[:size], self.payload[size:]
        return payload


def _signed_manifest(private_key, *, payload=b"installer"):
    from cryptography.hazmat.primitives import serialization

    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    manifest = {
        "version": "1.3.0",
        "installer_url": "https://downloads.example.test/LabReceiptSetup.exe",
        "size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "release_notes": "Security and stability improvements.",
        "channel": "stable",
    }
    signature = private_key.sign(updater._canonical_payload(manifest))
    manifest["signature"] = base64.b64encode(signature).decode("ascii")
    return manifest, base64.b64encode(public_key).decode("ascii")


def test_newer_version_comparison():
    assert updater.is_newer_version("1.3.0", "1.2.0")
    assert not updater.is_newer_version("1.2.0", "1.2.0")
    assert not updater.is_newer_version("1.1.9", "1.2.0")


def test_manifest_signature_is_verified():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    private_key = Ed25519PrivateKey.generate()
    manifest, public_key = _signed_manifest(private_key)
    updater.verify_manifest_signature(manifest, public_key)

    manifest["version"] = "1.4.0"
    with pytest.raises(updater.UpdateSecurityError):
        updater.verify_manifest_signature(manifest, public_key)


def test_fetch_manifest_rejects_http_and_accepts_signed_https(monkeypatch):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    manifest, public_key = _signed_manifest(Ed25519PrivateKey.generate())
    monkeypatch.setattr(updater, "UPDATE_PUBLIC_KEY_B64", public_key)
    payload = json.dumps(manifest).encode("utf-8")
    monkeypatch.setattr(updater.urllib.request, "urlopen", lambda *args, **kwargs: _Response(payload))

    with pytest.raises(updater.UpdateSecurityError):
        updater.fetch_manifest("http://downloads.example.test/update.json")
    assert updater.fetch_manifest()["version"] == "1.3.0"


def test_download_installer_verifies_hash_and_removes_partial_file(tmp_path, monkeypatch):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    payload = b"trusted-installer-bytes"
    manifest, public_key = _signed_manifest(Ed25519PrivateKey.generate(), payload=payload)
    monkeypatch.setattr(updater, "UPDATE_PUBLIC_KEY_B64", public_key)
    monkeypatch.setattr(updater.urllib.request, "urlopen", lambda *args, **kwargs: _Response(payload))

    installer = updater.download_installer(manifest, tmp_path)
    assert installer == tmp_path / "LabReceiptSetup-1.3.0.exe"
    assert installer.read_bytes() == payload
    assert not list(tmp_path.glob("*.part"))

    bad_manifest = dict(manifest, sha256="0" * 64)
    with pytest.raises(updater.UpdateSecurityError):
        updater.download_installer(bad_manifest, tmp_path)
    assert not list(tmp_path.glob("*.part"))


def test_launch_installer_is_windows_only(tmp_path, monkeypatch):
    installer = tmp_path / "LabReceiptSetup.exe"
    installer.write_bytes(b"not executed in unit tests")
    monkeypatch.setattr(updater.os, "name", "posix")
    with pytest.raises(updater.UpdateError, match="Windows only"):
        updater.launch_installer(installer)
