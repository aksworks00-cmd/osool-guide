"""Logging utility."""
import logging
import sys
from pathlib import Path
from .config_loader import get_config


def setup_logger(name: str = "nato_codifier") -> logging.Logger:
    """Set up logger with file and console handlers."""
    config = get_config()

    # Create logger
    logger = logging.Logger(name)
    logger.setLevel(config.get('logging.level', 'INFO'))

    # Create formatters
    formatter = logging.Formatter(
        config.get('logging.format',
                  '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (skip if no write permission)
    log_file = config.get_path('logging.file')
    if log_file:
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (PermissionError, OSError):
            # Skip file logging in restricted environments (e.g., Docker)
            pass

    return logger
