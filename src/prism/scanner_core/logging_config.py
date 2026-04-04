"""Structured logging configuration for scanner core."""

from __future__ import annotations

import contextvars
import logging
from contextlib import contextmanager
from typing import Any


# Context variables for logging
_scan_context: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar(
    "scan_context", default={}
)


class ScanContextFilter(logging.Filter):
    """Filter that adds scan context to log records."""

    def filter(self, record):
        context = _scan_context.get()
        for key, value in context.items():
            setattr(record, key, value)
        return True


@contextmanager
def set_scan_context(**context):
    """Set scan context for logging."""
    token = _scan_context.set(context)
    try:
        yield
    finally:
        _scan_context.reset(token)


class LoggerFactory:
    """Factory for creating structured loggers."""

    def __init__(self):
        """Initialize the logger factory."""
        self._configured = False
        self._configure_once()

    def _configure_once(self):
        """Configure logging once."""
        if self._configured:
            return
        configure_structured_logging()
        self._configured = True

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger with scan context filter."""
        return get_logger(name)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with scan context filter."""
    logger = logging.getLogger(name)
    # Add filter if not already added
    if not any(isinstance(f, ScanContextFilter) for f in logger.filters):
        logger.addFilter(ScanContextFilter())
    return logger


# Configure logging
class SafeFormatter(logging.Formatter):
    """Formatter that handles missing fields gracefully."""

    def format(self, record):
        # Ensure missing fields are set to empty string
        if not hasattr(record, "role_name"):
            record.role_name = ""
        if not hasattr(record, "scan_id"):
            record.scan_id = ""
        return super().format(record)


def configure_structured_logging():
    """Configure logging for structured output."""
    # Set up a formatter that includes extra fields
    formatter = SafeFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s - role_name:%(role_name)s - scan_id:%(scan_id)s"
    )

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    # Add handler if not present
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)


# Initialize
configure_structured_logging()
