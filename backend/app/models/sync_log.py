from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.db.session import Base


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)
    payload = Column(Text, default="")
    device_id = Column(String(100), default="", index=True)
    branch_id = Column(String(100), default="")
    synced_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
