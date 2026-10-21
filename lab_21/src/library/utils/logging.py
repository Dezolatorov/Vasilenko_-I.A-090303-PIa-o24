"""Централизованное логирование приложения."""
from __future__ import annotations

import logging
import sys

from ..config import settings

APP_LOGGER_NAME = "libraryapi"


def get_logger(name: str | None = None) -> logging.Logger:
    logger = logging.getLogger(name or APP_LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
        logger.propagate = False
    return logger