from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.common import TimestampMixin, UUIDMixin


class TransactionItem(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "transaction_items"

    transaction_id: Mapped[str] = mapped_column(ForeignKey("transactions.id"), index=True)
    sample_type: Mapped[str] = mapped_column(String(80), index=True)
    total_count: Mapped[int] = mapped_column(Integer)
    valid_count: Mapped[int] = mapped_column(Integer)
    damaged_count: Mapped[int] = mapped_column(Integer)
    rejected_count: Mapped[int] = mapped_column(Integer)
    nonconforming_count: Mapped[int] = mapped_column(Integer)
    transport_condition: Mapped[str] = mapped_column(String(100), default="")
    notes: Mapped[str] = mapped_column(Text, default="")

    transaction: Mapped["Transaction"] = relationship(  # noqa: F821
        "Transaction", back_populates="items",
    )

