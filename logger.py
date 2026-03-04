import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

_initialized = False

_LEVEL_ALIASES = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "WARN": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}


def _coerce_level(level: Optional[object]) -> int:
    if level is None:
        # Env overrides
        env = os.getenv("LOG_LEVEL") or os.getenv("APP_LOG_LEVEL")
        if env:
            level = env
        else:
            return logging.INFO
    if isinstance(level, int):
        return level
    try:
        if isinstance(level, str):
            return _LEVEL_ALIASES.get(level.strip().upper(), logging.INFO)
    except Exception:
        pass
    return logging.INFO


def setup_logging(log_path: str = "app.log", level: Optional[object] = None) -> None:
    """
    Idempotent logging setup with a rotating file handler.

    - log_path: path to the log file (created in project root by default)
    - level: logging level or string (DEBUG/INFO/...). If None, reads LOG_LEVEL/APP_LOG_LEVEL.
    """
    global _initialized
    if _initialized:
        return

    os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)

    root = logging.getLogger()
    root.setLevel(_coerce_level(level))

    # Avoid duplicate handlers if setup is called more than once
    has_file = any(isinstance(h, RotatingFileHandler) for h in root.handlers)
    if not has_file:
        file_handler = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
        fmt = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(fmt)
        file_handler.setLevel(_coerce_level(level))
        root.addHandler(file_handler)

    # Also ensure a simple console handler exists only once (INFO by default)
    has_console = any(isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler) for h in root.handlers)
    if not has_console:
        ch = logging.StreamHandler()
        ch.setLevel(_coerce_level(level))
        ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        root.addHandler(ch)

    _initialized = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a module-scoped logger."""
    return logging.getLogger(name or __name__)
