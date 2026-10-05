"""Interface for exporter configuration providers.

Defines contract for loading and providing exporter-specific configurations
from various sources (JSON, environment variables, databases, etc.).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class IConfigProvider(ABC):
    """Abstract base class for exporter configuration providers.

    Each exporter may have different configuration requirements. This interface
    defines how configurations should be loaded and accessed, allowing for
    flexible source implementations (JSON, YAML, environment variables, etc.).

    Generic parameter T represents the type of configuration object/dictionary.
    """

    @abstractmethod
    def load_config(self) -> Dict[str, Any]:
        """Load exporter configuration from source.

        Returns:
            Dictionary containing exporter-specific configuration.
            Keys and values depend on the specific exporter implementation.

        Raises:
            FileNotFoundError: If configuration source not found
            ValueError: If configuration is invalid or missing required fields
        """
        pass

    @abstractmethod
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a specific configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        pass

