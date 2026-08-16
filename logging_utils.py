from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="-")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_var.get(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key in ("job_id", "event_type", "route", "status_code", "duration_ms"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(log_path: str | None = None) -> logging.Logger:
    logger = logging.getLogger("print_recovery")
    if logger.handlers:
        return logger
    logger.setLevel(os.getenv("PRINT_RECOVERY_LOG_LEVEL", "INFO").upper())
    formatter = JsonFormatter()
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    logger.addHandler(stream)
    if log_path:
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    logger.propagate = False
    return logger


def new_correlation_id() -> str:
    return uuid.uuid4().hex


def set_correlation_id(value: str | None) -> str:
    correlation_id = value.strip() if value and value.strip() else new_correlation_id()
    correlation_id_var.set(correlation_id)
    return correlation_id
