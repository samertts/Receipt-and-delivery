from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, text

from app.core.config import settings
from app.db.base import Base  # noqa: F401 - imports every ORM model into metadata

MIGRATION_LOCK_KEY = 827341

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# DATABASE_URL is read from the same settings object as the application. It is
# never committed to alembic.ini and may be supplied by a deployment secret.
database_url = settings.database_url
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
target_metadata = Base.metadata


def include_name(name, type_, parent_names):
    """Limit autogenerate to the application's default PostgreSQL schema."""
    if type_ == "schema":
        return name is None
    return True


def configure_context(connection=None, url=None):
    options = {
        "target_metadata": target_metadata,
        "compare_type": True,
        "compare_server_default": False,
        "include_schemas": False,
        "include_name": include_name,
        "transaction_per_migration": True,
    }
    if connection is not None:
        options["connection"] = connection
    else:
        options["url"] = url
        options["literal_binds"] = True
        options["dialect_opts"] = {"paramstyle": "named"}
    context.configure(**options)


def run_migrations_offline() -> None:
    configure_context(url=database_url)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        {"sqlalchemy.url": database_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )
    with connectable.connect() as connection:
        if connection.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_lock(:lock_key)"), {"lock_key": MIGRATION_LOCK_KEY})
        try:
            configure_context(connection=connection)
            with context.begin_transaction():
                context.run_migrations()
        finally:
            if connection.dialect.name == "postgresql":
                connection.execute(text("SELECT pg_advisory_unlock(:lock_key)"), {"lock_key": MIGRATION_LOCK_KEY})


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
