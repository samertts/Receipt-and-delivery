import secrets
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _read_app_version() -> str:
    version_file = Path(__file__).resolve().parent.parent.parent.parent / 'VERSION'
    if version_file.exists():
        return version_file.read_text(encoding='utf-8').strip() or '0.0.0'
    return '0.0.0'


class Settings(BaseSettings):
    app_name: str = "نظام إدارة المعاملات المختبرية"
    app_version: str = _read_app_version()
    debug: bool = False

    secret_key: str = ""
    access_token_expire_minutes: int = 120
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

    backup_retention_days: int = 30
    auto_backup_enabled: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def effective_secret_key(self) -> str:
        if not self.secret_key or self.secret_key == "change-me":
            return secrets.token_hex(32)
        return self.secret_key

    @property
    def origin_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()] or ["*"]


settings = Settings()
