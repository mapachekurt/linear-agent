"""Logging utilities for the Linear agent.

The module configures JSON structured logging with contextual data, suitable for
collecting audit trails and monitoring signals from the agent.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class LogContext:
    """Context attached to every log message."""

    correlation_id: Optional[str] = None
    linear_issue_id: Optional[str] = None
    github_repo: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the context to a JSON-serializable dictionary."""

        return {key: value for key, value in asdict(self).items() if value is not None}


class JsonFormatter(logging.Formatter):
    """Formatter that outputs logs as JSON strings."""

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        payload = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            **getattr(record, "context", {}),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure the root logger for JSON structured output."""

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("linear_agent")
    logger.setLevel(level)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def log_with_context(logger: logging.Logger, level: int, message: str, context: LogContext) -> None:
    """Emit a log entry with attached :class:`LogContext`.

    Args:
        logger: Configured logger instance.
        level: Logging level (e.g., ``logging.INFO``).
        message: The log message to emit.
        context: Contextual information to include.
    """

    logger.log(level, message, extra={"context": context.to_dict()})
