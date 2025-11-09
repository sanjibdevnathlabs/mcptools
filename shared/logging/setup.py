"""
Common logging setup and formatters for MCP servers.

Provides consistent logging configuration across all MCP servers.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Optional, Union


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Enhanced text formatter for human-readable logs."""

    def __init__(self):
        """Initialize text formatter with standard format."""
        format_string = "%(asctime)s - %(levelname)-8s - %(name)s - %(message)s"
        super().__init__(format_string, datefmt="%Y-%m-%d %H:%M:%S")


def setup_logging(
    config: Any, logger_name: str, transport_mode: Optional[str] = None
) -> logging.Logger:
    """
    Setup logging based on configuration.

    Args:
        config: Application configuration object with logger.* attributes
        logger_name: Name for the logger (e.g., "calculator", "database")
        transport_mode: Transport mode ("stdio", "sse", "streamable-http")
                       If "stdio", logging will be forced to file to avoid conflicts

    Returns:
        Configured logger instance

    Example:
        from shared.logging import setup_logging
        from myapp.config import Config

        config = Config()
        logger = setup_logging(config, "myapp", transport_mode="stdio")
        logger.info("Application started")
    """
    # Get root logger
    root_logger = logging.getLogger()

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set log level
    log_level = getattr(logging, config.logger.level.upper())
    root_logger.setLevel(log_level)

    # Create formatter
    formatter: Union[JSONFormatter, TextFormatter] = (
        JSONFormatter() if config.logger.format == "json" else TextFormatter()
    )

    # CRITICAL: If stdio transport, force file logging to avoid protocol conflicts
    log_destination = config.logger.destination
    if transport_mode == "stdio":
        log_destination = "file"
        # Create a temporary basic logger to log the warning
        temp_handler = logging.StreamHandler(sys.stderr)
        temp_handler.setFormatter(formatter)
        root_logger.addHandler(temp_handler)
        root_logger.warning(
            "stdio transport detected - forcing log output to file to avoid protocol conflicts"
        )
        root_logger.removeHandler(temp_handler)

    # Configure handlers based on destination
    if log_destination in ("stdout", "both"):
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        stdout_handler.setLevel(log_level)
        root_logger.addHandler(stdout_handler)

    if log_destination in ("stderr",):
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setFormatter(formatter)
        stderr_handler.setLevel(logging.ERROR)  # Only errors to stderr
        root_logger.addHandler(stderr_handler)

    if log_destination in ("file", "both"):
        # Create log directory if it doesn't exist
        from pathlib import Path

        log_file = Path(config.logger.file_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(str(log_file))
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)

    # Create service-specific logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    # Log configuration
    logger.info(
        f"Logging configured: level={config.logger.level}, "
        f"format={config.logger.format}, "
        f"destination={log_destination}"
        + (f", file={config.logger.file_path}" if "file" in log_destination else "")
    )

    return logger
