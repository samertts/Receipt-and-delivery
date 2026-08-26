from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, Integer, String, Text, text

from app.db.session import Base


class SyncLog(Base):
    __tablename__ = "sync_logs"
    __table_args__ = (
        Index(
            "uq_sync_log_idempotency_key",
            "idempotency_key",
            unique=True,
            sqlite_where=text("idempotency_key <> ''"),
            postgresql_where=text("idempotency_key <> ''"),
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)
    idempotency_key = Column(String(160), nullable=False, default="")
    payload = Column(Text, default="")
    device_id = Column(String(100), default="", index=True)
    branch_id = Column(String(100), default="")
    synced_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
