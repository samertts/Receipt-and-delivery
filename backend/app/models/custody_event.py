from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin, UUIDMixin


class CustodyEvent(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "sample_custody_events"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_sample_custody_idempotency_key"),
    )

    sample_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    transaction_id: Mapped[str | None] = mapped_column(
        ForeignKey("transactions.id"), index=True, nullable=True
    )
    actor_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    from_state: Mapped[str] = mapped_column(String(40), nullable=False)
    to_state: Mapped[str] = mapped_column(String(40), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
