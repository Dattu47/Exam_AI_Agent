"""
Logging configuration for the application.
Provides consistent logging across all modules.
"""

import logging
import sys
from pathlib import Path

try:
    from exam_ai_agent.config import settings
except ImportError:
    from ..config import settings


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured Logger instance
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logger.level)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
