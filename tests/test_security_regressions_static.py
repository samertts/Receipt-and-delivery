"""Static regression tests for security hardening decisions.

These tests intentionally avoid importing optional backend/frontend runtime dependencies so
that security regressions are detected during collection even in minimal CI images.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_frontend_does_not_persist_tokens_in_local_storage():
    frontend_files = [
        ROOT / "frontend/src/stores/auth.js",
        ROOT / "frontend/src/api/client.js",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in frontend_files)

    assert "localStorage" not in combined
    assert "setItem('access_token'" not in combined
    assert "setItem('refresh_token'" not in combined


def test_backend_rejects_non_access_and_blacklisted_bearer_tokens():
    deps_source = (ROOT / "backend/app/api/deps.py").read_text(encoding="utf-8")

    assert 'payload.get("type") != "access"' in deps_source
    assert "BlacklistedToken" in deps_source
    assert "BlacklistedToken.token == token" in deps_source


def test_production_requires_explicit_secret_key():
    config_source = (ROOT / "backend/app/core/config.py").read_text(encoding="utf-8")

    assert "environment" in config_source
    assert '{"prod", "production", "staging"}' in config_source
    assert "SECRET_KEY must be configured securely outside development" in config_source


def test_rate_limit_cannot_be_disabled_in_production():
    security_source = (ROOT / "backend/app/core/security.py").read_text(encoding="utf-8")

    assert 'os.environ.get("RATE_LIMIT_DISABLED")' in security_source
    assert "RATE_LIMIT_REQUIRED" in security_source
    assert '{"prod", "production", "staging"}' in security_source
