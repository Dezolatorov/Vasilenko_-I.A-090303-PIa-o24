import logging
import sys

from .config import get_settings


def setup_logging() -> None:
    """Настраивает систему логирования в соответствии с настройками приложения."""
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root.addHandler(handler)

    logging.getLogger("uvicorn.access").propagate = False
