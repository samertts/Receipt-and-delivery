from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    future=True,
    pool_pre_ping=True,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_recycle=3600,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Development/test bootstrap only; production must run Alembic explicitly."""
    if settings.environment.lower() in {"prod", "production", "staging"}:
        raise RuntimeError(
            "Base.metadata.create_all is disabled in production; run alembic upgrade head"
        )
    Base.metadata.create_all(bind=engine)
