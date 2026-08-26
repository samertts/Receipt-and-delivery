import json
import os
import secrets
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


_SECRET_KEY_FILE = Path(
    os.getenv(
        "SECRET_KEY_FILE",
        str(Path.home() / ".lab_receipt_system" / "generated_secret_key.json"),
    )
).expanduser()


def _load_or_persist_secret_key() -> str:
    """Load persisted auto-generated key, or generate and persist one."""
    if _SECRET_KEY_FILE.exists():
        try:
            data = json.loads(_SECRET_KEY_FILE.read_text())
            if isinstance(data, dict) and "secret_key" in data:
                return data["secret_key"]
        except (json.JSONDecodeError, OSError):
            pass
    key = secrets.token_hex(32)
    try:
        _SECRET_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        file_descriptor = os.open(_SECRET_KEY_FILE, flags, 0o600)
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as stream:
            stream.write(json.dumps({"secret_key": key}))
        try:
            _SECRET_KEY_FILE.chmod(0o600)
        except OSError:
            pass
    except OSError:
        pass
    return key


def _read_app_version() -> str:
    version_file = Path(__file__).resolve().parent.parent.parent.parent / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip() or "0.0.0"
    return "0.0.0"


class Settings(BaseSettings):
    app_name: str = "نظام إدارة المعاملات المختبرية"
    app_version: str = _read_app_version()
    debug: bool = False
    environment: str = "development"

    secret_key: str = ""
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    database_url: str = "postgresql+psycopg://lab_user:lab_pass@localhost:5432/lab_txn"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    storage_root: str = "storage"
    log_level: str = "INFO"

    allowed_origins: str = "http://localhost:5173,http://localhost:8000"
    cors_allow_credentials: bool = True

    rate_limit_login_max: int = 5
    rate_limit_login_window: int = 60
    rate_limit_api_max: int = 100
    rate_limit_api_window: int = 60

    password_min_length: int = 8

    redis_url: str = ""

    gula_base_url: str = ""
    gula_access_token: str = ""
    gula_tenant_id: str = ""
    gula_timeout_seconds: float = 5.0
    gula_max_retries: int = 3

    backup_retention_days: int = 30
    auto_backup_enabled: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def effective_secret_key(self) -> str:
        if not self.secret_key or self.secret_key == "change-me":  # nosec B105 - development sentinel only
            if self.environment.lower() in {"prod", "production", "staging"}:
                raise ValueError("SECRET_KEY must be configured securely outside development")
            # Persist auto-generated key only for local development so it survives restarts.
            return _load_or_persist_secret_key()
        return self.secret_key

    @property
    def origin_list(self) -> list[str]:
        origins = [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
        if not origins:
            raise ValueError("ALLOWED_ORIGINS must be configured")
        return origins

    def validate_runtime_security(self) -> None:
        """Reject known-insecure production defaults before serving requests."""
        if self.environment.lower() not in {"prod", "production", "staging"}:
            return
        if "lab_user:lab_pass@" in self.database_url:
            raise ValueError("DATABASE_URL must be configured with non-default credentials")
        origins = self.origin_list
        if "*" in origins or any(origin.startswith("http://") for origin in origins):
            raise ValueError("Production CORS origins must be explicit HTTPS origins")


settings = Settings()
settings.validate_runtime_security()
