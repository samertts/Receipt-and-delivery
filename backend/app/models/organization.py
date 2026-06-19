from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin, UUIDMixin


class Organization(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    org_type: Mapped[str] = mapped_column(String(80), default="")
    governorate: Mapped[str] = mapped_column(String(80), default="")
    address: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    email: Mapped[str] = mapped_column(String(150), default="")
    logo_path: Mapped[str] = mapped_column(String(255), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        index=True,
    )
