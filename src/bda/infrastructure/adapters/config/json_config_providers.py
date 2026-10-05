"""JSON-based configuration providers for exporters.

Each provider is responsible for loading exporter-specific configuration
from JSON files and providing access to configuration values.
"""

import json
from pathlib import Path
from typing import Dict, Any

from bda.application.interfaces.config.i_config_provider import (
    IConfigProvider,
)
from bda.infrastructure.utils.logger import AppLogger

logger = AppLogger()


class JsonConfigProvider(IConfigProvider):
    """Base class for JSON-based configuration providers.

    Handles common logic for loading and accessing configuration from JSON files.
    """

    def __init__(self, config_file_path: str):
        """Initialize JSON configuration provider.

        Args:
            config_file_path: Absolute path to JSON configuration file

        Raises:
            FileNotFoundError: If configuration file does not exist
        """
        self.config_file_path = Path(config_file_path)
        self.config: Dict[str, Any] = {}

        if not self.config_file_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_file_path}"
            )

        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from JSON file.

        Raises:
            ValueError: If JSON is invalid
        """
        try:
            with open(self.config_file_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
            logger.debug(f"Loaded config from {self.config_file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON in configuration file {self.config_file_path}: {e}"
            )

    def load_config(self) -> Dict[str, Any]:
        """Load and return exporter configuration.

        Returns:
            Dictionary containing exporter configuration
        """
        return self.config.copy()

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a specific configuration value.

        Args:
            key: Configuration key (supports nested access with dot notation, e.g. "db.host")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default
