"""Structured logging configuration."""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from uuid import UUID

from rich.console import Console
from rich.logging import RichHandler

from app.config import get_settings

# Context variables for request tracing
correlation_id_var: ContextVar[UUID | None] = ContextVar("correlation_id", default=None)
agent_role_var: ContextVar[str | None] = ContextVar("agent_role", default=None)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add correlation ID if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_data["correlation_id"] = str(correlation_id)

        # Add agent role if available
        agent_role = agent_role_var.get()
        if agent_role:
            log_data["agent_role"] = agent_role

        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging() -> None:
    """Configure logging based on settings."""
    settings = get_settings()
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    if settings.log_format == "json":
        # JSON file handler
        file_handler = logging.FileHandler(
            log_dir / f"app_{datetime.utcnow().strftime('%Y%m%d')}.json"
        )
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
        
        # JSON console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(console_handler)
    else:
        # Rich text handler for development
        console = Console()
        rich_handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
        )
        rich_handler.setFormatter(
            logging.Formatter("%(message)s", datefmt="[%X]")
        )
        root_logger.addHandler(rich_handler)
        
        # Text file handler
        file_handler = logging.FileHandler(
            log_dir / f"app_{datetime.utcnow().strftime('%Y%m%d')}.log"
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding context to logs."""

    def __init__(
        self,
        correlation_id: UUID | None = None,
        agent_role: str | None = None,
        **extra: Any
    ):
        self.correlation_id = correlation_id
        self.agent_role = agent_role
        self.extra = extra
        self._correlation_token = None
        self._agent_token = None

    def __enter__(self) -> "LogContext":
        if self.correlation_id:
            self._correlation_token = correlation_id_var.set(self.correlation_id)
        if self.agent_role:
            self._agent_token = agent_role_var.set(self.agent_role)
        return self

    def __exit__(self, *args: Any) -> None:
        if self._correlation_token:
            correlation_id_var.reset(self._correlation_token)
        if self._agent_token:
            agent_role_var.reset(self._agent_token)


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    **extra: Any
) -> None:
    """Log with additional context."""
    record = logger.makeRecord(
        logger.name,
        level,
        "(unknown file)",
        0,
        message,
        (),
        None,
    )
    record.extra = extra
    logger.handle(record)

