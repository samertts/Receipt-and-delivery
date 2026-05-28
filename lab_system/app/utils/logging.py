import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


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
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def setup_file_logging(log_dir: Path, level: str = "INFO") -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("lab_system_desktop")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not logger.handlers:
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(StructuredFormatter())
        logger.addHandler(console)

        log_file = log_dir / f"lab_system_{datetime.now().strftime('%Y%m%d')}.log"
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(StructuredFormatter())
        logger.addHandler(fh)

    return logger


desktop_logger = setup_file_logging(Path("storage/logs"))
