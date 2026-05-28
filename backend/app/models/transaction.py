from typing import List

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.common import TimestampMixin, UUIDMixin


class Transaction(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "transactions"

    transaction_no: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    transaction_type: Mapped[str] = mapped_column(String(60), index=True)
    sender_organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    receiver_organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    sender_name: Mapped[str] = mapped_column(String(180))
    receiver_name: Mapped[str] = mapped_column(String(180))
    sender_job_title: Mapped[str] = mapped_column(String(80), default="")
    receiver_job_title: Mapped[str] = mapped_column(String(80), default="")
    authorization_no: Mapped[str] = mapped_column(String(100), index=True, default="")
    authorization_date: Mapped[str] = mapped_column(String(20), default="")
    transaction_date: Mapped[str] = mapped_column(String(30), index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    transport_info: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(
        String(30), index=True, default="draft"
    )
    created_by: Mapped[str] = mapped_column(String(36), default="")

    items: Mapped[List["TransactionItem"]] = relationship(
        "TransactionItem", back_populates="transaction", cascade="all, delete-orphan"
    )
    attachments: Mapped[List["Attachment"]] = relationship(
        "Attachment", back_populates="transaction", cascade="all, delete-orphan"
    )


from app.models.attachment import Attachment
from app.models.transaction_item import TransactionItem
