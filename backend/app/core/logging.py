import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.core.config import settings


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "ip_address"):
            log_entry["ip_address"] = record.ip_address
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_entry["stack_info"] = self.formatStack(record.stack_info)
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(log_dir: Optional[Path] = None, level: str = "INFO") -> None:
    if log_dir is None:
        log_dir = Path(settings.storage_root) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)

    file_handler = logging.FileHandler(
        log_dir / f"lab_system_{datetime.now().strftime('%Y%m%d')}.log",
        encoding="utf-8",
    )
    file_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(file_handler)

    logging.getLogger("passlib").setLevel(logging.WARNING)
    logging.getLogger("jose").setLevel(logging.WARNING)


logger = logging.getLogger("lab_system")
