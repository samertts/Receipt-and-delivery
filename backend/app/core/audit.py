from typing import Optional

from app.core.logging import logger
from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from fastapi import Request
from sqlalchemy.orm import Session


def log_audit(
    user_id: str,
    action_type: str,
    request: Optional[Request] = None,
    details: str = "",
    changes_json: str = "",
    db: Optional[Session] = None,
) -> None:
    ip_address = request.client.host if request and request.client else "0.0.0.0"
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        audit = AuditLog(
            user_id=user_id,
            action_type=action_type,
            ip_address=ip_address,
            details=details,
            changes_json=changes_json,
        )
        db.add(audit)
        db.commit()
        logger.info(
            f"Audit: {action_type} by user {user_id}",
            extra={"user_id": user_id, "ip_address": ip_address, "action": action_type},
        )
    except Exception as e:
        logger.error(f"Failed to log audit: {e}")
        if close_db:
            db.rollback()
    finally:
        if close_db:
            db.close()
