import logging
import sys
from typing import Any, Dict


class StructuredFormatter(logging.Formatter):
    """Custom structured log formatter for development and production observability."""
    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        level = record.levelname.ljust(8)
        message = record.getMessage()
        
        # Format extra structured fields if available
        extras = []
        for key, value in record.__dict__.items():
            if key not in {
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "module", "msecs",
                "message", "msg", "name", "pathname", "process", "processName",
                "relativeCreated", "stack_info", "thread", "threadName"
            }:
                extras.append(f"{key}={value}")
        
        extra_str = f" | {' '.join(extras)}" if extras else ""
        return f"[{timestamp}] [{level}] [{record.name}]: {message}{extra_str}"


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure root and application loggers."""
    logger = logging.getLogger("meetmind")
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.propagate = False

    # Adjust external noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    return logger


logger = setup_logging()
