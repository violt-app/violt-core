"""
Violt Core Lite - Logger Configuration

This module configures the application logging system.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
import os

from ..core.config import settings, DEFAULT_LOGS_DIR


def setup_logging():
    """Configure the logging system for the application."""
    # Create logs directory if it doesn't exist
    log_file = Path(settings.LOG_FILE)

    # If log file path is relative, use the default logs directory
    if not log_file.is_absolute():
        log_file = DEFAULT_LOGS_DIR / log_file

    os.makedirs(log_file.parent, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()

    # Set log level based on settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # Clear existing handlers
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)

    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # Create file handler with rotation
    when, interval = parse_rotation_interval(settings.LOG_ROTATION)

    try:
        file_handler = TimedRotatingFileHandler(
            str(log_file),  # Convert Path to string for compatibility
            when=when,
            interval=interval,
            backupCount=int(settings.LOG_RETENTION.split()[0]),
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)
    except Exception as e:
        # Handle potential permission issues on Windows
        console_handler.setLevel(logging.WARNING)
        root_logger.warning(f"Failed to set up log file at {log_file}: {e}")
        root_logger.warning("Logging to console only")

    # Suppress overly verbose logs from libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.WARNING if settings.DEBUG else logging.ERROR
    )

    # Log platform information
    root_logger.info(f"Running on platform: {settings.PLATFORM}")
    root_logger.info(f"Log file location: {log_file}")

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Create a logger instance with the given name."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger


def parse_rotation_interval(rotation_str):
    """Parse rotation interval string into when and interval values."""
    parts = rotation_str.split()
    if len(parts) != 2:
        return "D", 1  # Default to daily rotation

    try:
        interval = int(parts[0])
    except ValueError:
        interval = 1

    unit = parts[1].lower()
    if unit.startswith("hour"):
        return "H", interval
    elif unit.startswith("day"):
        return "D", interval
    elif unit.startswith("week"):
        return "W", interval
    elif unit.startswith("month"):
        return "M", interval
    else:
        return "D", interval  # Default to daily rotation
