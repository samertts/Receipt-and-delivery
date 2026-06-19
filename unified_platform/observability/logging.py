"""
Platform Observability — Structured Logging

Phase 6: Observability Platform
Constitution: Principle 19 (Observability First)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class StructuredLogger:
    """Structured logging with JSON output for machine readability."""

    def __init__(self, name: str, level: LogLevel = LogLevel.INFO) -> None:
        self._name = name
        self._level = level
        self._entries: list[dict[str, Any]] = []
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, level.value.upper(), logging.INFO))

    def _log(self, level: LogLevel, message: str, **context: Any) -> dict[str, Any]:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.value,
            "logger": self._name,
            "message": message,
            "context": context,
        }
        self._entries.append(entry)
        log_method = getattr(self._logger, level.value, self._logger.info)
        log_method(json.dumps(entry, default=str, ensure_ascii=False))
        return entry

    def debug(self, message: str, **context: Any) -> dict[str, Any]:
        return self._log(LogLevel.DEBUG, message, **context)

    def info(self, message: str, **context: Any) -> dict[str, Any]:
        return self._log(LogLevel.INFO, message, **context)

    def warning(self, message: str, **context: Any) -> dict[str, Any]:
        return self._log(LogLevel.WARNING, message, **context)

    def error(self, message: str, **context: Any) -> dict[str, Any]:
        return self._log(LogLevel.ERROR, message, **context)

    def critical(self, message: str, **context: Any) -> dict[str, Any]:
        return self._log(LogLevel.CRITICAL, message, **context)

    def get_entries(self, level: LogLevel | None = None, limit: int = 100) -> list[dict[str, Any]]:
        """Get log entries, optionally filtered by level."""
        if level:
            entries = [e for e in self._entries if e["level"] == level.value]
        else:
            entries = self._entries
        return entries[-limit:]

    def get_error_count(self) -> int:
        return len([e for e in self._entries if e["level"] in ("error", "critical")])

    def clear(self) -> int:
        count = len(self._entries)
        self._entries.clear()
        return count
