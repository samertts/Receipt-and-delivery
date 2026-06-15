import hashlib

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.common import TimestampMixin, UUIDMixin


class AuditLog(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"

    user_id: Mapped[str] = mapped_column(String(36), index=True)
    action_type: Mapped[str] = mapped_column(String(80), index=True)
    ip_address: Mapped[str] = mapped_column(String(64), index=True)
    details: Mapped[str] = mapped_column(Text, default="")
    machine_name: Mapped[str] = mapped_column(String(100), default="")
    changes_json: Mapped[str] = mapped_column(Text, default="")
    prev_hash: Mapped[str] = mapped_column(String(64), default="")

    @staticmethod
    def compute_hash(entry_id: str, user_id: str, action_type: str,
                     ip_address: str, details: str, prev_hash: str) -> str:
        raw = f"{entry_id}|{user_id}|{action_type}|{ip_address}|{details}|{prev_hash}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
