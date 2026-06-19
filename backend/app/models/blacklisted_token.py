from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, Text

from app.db.session import Base


class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(Text, unique=True, nullable=False, index=True)
    blacklisted_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    expires_at = Column(DateTime, nullable=True)
