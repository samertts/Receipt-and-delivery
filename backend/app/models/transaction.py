from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.common import TimestampMixin, UUIDMixin


class Transaction(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "transactions"

    transaction_no: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    transaction_type: Mapped[str] = mapped_column(String(60), index=True)
    sender_organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    receiver_organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    sender_name: Mapped[str] = mapped_column(String(180))
    receiver_name: Mapped[str] = mapped_column(String(180))
    authorization_no: Mapped[str] = mapped_column(String(100), index=True)
    authorization_date: Mapped[str] = mapped_column(String(20))
    transaction_date: Mapped[str] = mapped_column(String(30), index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(Enum("draft", "approved", "rejected", "archived", "cancelled", name="transaction_status"), index=True)

    items = relationship("TransactionItem", back_populates="transaction", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="transaction", cascade="all, delete-orphan")
