import pytest

from app.core.config import Settings


DEFAULT_DATABASE_URL = "postgresql+psycopg://lab_user:lab_pass@localhost:5432/lab_txn"


def test_production_rejects_default_database_credentials():
    settings = Settings(
        environment="production",
        secret_key="configured-secret",
        database_url=DEFAULT_DATABASE_URL,
        allowed_origins="https://lab.example",
    )
    with pytest.raises(ValueError, match="DATABASE_URL"):
        settings.validate_runtime_security()


def test_production_rejects_http_or_wildcard_origins():
    for origins in ("http://lab.example", "*"):
        settings = Settings(
            environment="production",
            secret_key="configured-secret",
            database_url="postgresql+psycopg://user:strong-pass@db:5432/lab_txn",
            allowed_origins=origins,
        )
        with pytest.raises(ValueError, match="CORS"):
            settings.validate_runtime_security()


def test_production_accepts_explicit_https_origin_and_database():
    settings = Settings(
        environment="production",
        secret_key="configured-secret",
        database_url="postgresql+psycopg://user:strong-pass@db:5432/lab_txn",
        allowed_origins="https://lab.example",
    )
    settings.validate_runtime_security()
