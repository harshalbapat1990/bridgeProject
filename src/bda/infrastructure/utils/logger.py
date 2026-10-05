"""Singleton application logger.

Usage:
    from bda.infrastructure.utils.logger import AppLogger

    logger = AppLogger(console=True, log_file=True)
    logger.info("Starting export of '%s' to %s", name, software)

    # Anywhere else — same instance:
    logger = AppLogger()
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from bda.application.interfaces.logging.i_app_logger import IAppLogger
from bda.config.global_config import GlobalConfig

_DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "logging" / "logger_config.json"
)
_LOG_TIMESTAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class AppLogger(IAppLogger):
    """Singleton logger implementing IAppLogger.

    First call configures the instance; subsequent calls return it unchanged.

    Args:
        console:  Enable stdout handler.
        log_file: Enable per-run file handler (path from JSON config).
    """

    _instance: AppLogger | None = None

    def __new__(
        cls,
        *,
        console: bool | None = None,
        log_file: bool | None = None,
    ) -> AppLogger:
        if cls._instance is not None:
            return cls._instance

        instance = super().__new__(cls)
        try:
            config = cls._load_config()
        except:
            print("Failed to load AppLogger config from GlobalConfig. Default settings will be used.")
            config = {}

        # Resolve output targets.
        # If caller provides at least one explicit flag, treat the omitted one as False
        # to avoid unintentionally enabling handlers from JSON defaults.
        if console is None and log_file is None:
            console = bool(config.get("console", True))
            log_file = bool(config.get("log_file", False))
        else:
            console = bool(console) if console is not None else False
            log_file = bool(log_file) if log_file is not None else False

        # Troubleshooting mode from config → DEBUG; otherwise INFO
        troubleshooting = config.get("troubleshooting", False)
        level = logging.DEBUG if troubleshooting else logging.INFO

        std_logger = logging.getLogger("BDA")
        std_logger.setLevel(level)
        std_logger.handlers.clear()
        std_logger.propagate = False

        formatter = logging.Formatter(_LOG_FORMAT)

        if console:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            std_logger.addHandler(handler)

        if log_file:
            logs_dir = cls._resolve_logs_dir(config)
            logs_dir.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(
                logs_dir / f"log_{_LOG_TIMESTAMP}.log",
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            std_logger.addHandler(file_handler)

        instance._logger = std_logger
        cls._instance = instance
        return instance

    # -- IAppLogger interface --------------------------------------------------

    def debug(self, msg: str, *args: Any) -> None:
        self._logger.debug(msg, *args)

    def info(self, msg: str, *args: Any) -> None:
        self._logger.info(msg, *args)

    def warning(self, msg: str, *args: Any) -> None:
        self._logger.warning(msg, *args)

    def error(self, msg: str, *args: Any) -> None:
        self._logger.error(msg, *args)

    # -- Configuration helpers -------------------------------------------------

    @staticmethod
    def _load_config() -> dict[str, Any]:
        return GlobalConfig().logger

    @staticmethod
    def _resolve_logs_dir(config: dict[str, Any]) -> Path:
        raw = config.get("logs_directory", "logs")
        path = Path(raw)
        if not path.is_absolute():
            path = Path.cwd() / path
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path
        except OSError:
            return Path.cwd() / "logs"

    # -- Testing helper --------------------------------------------------------

    @classmethod
    def _reset(cls) -> None:
        """Destroy the singleton (for tests only)."""
        cls._instance = None
