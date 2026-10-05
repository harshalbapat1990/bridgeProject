"""Global application configuration.

Loads configuration either from a built-in appsettings_dev.json (dev/local mode)
or from an external appsettings.json file under the 'RunConfig' key (production mode).
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

_DEFAULT_CONFIG_PATH = Path(__file__).parent / "appsettings_dev.json"

_instance: Optional["GlobalConfig"] = None

_TIMESTAMP = datetime.now().strftime("%Y%m%d-%H%M%S")

class GlobalConfig:
    """Loads and exposes application-wide configuration.

    Usage:
        # Production – external appsettings.json
        config = GlobalConfig(appsettings_path="C:/project/appsettings.json")

        # Dev/local – built-in appsettings_dev.json
        config = GlobalConfig(load_default=True)
    """

    def __new__(
        cls,
        appsettings_path: Optional[str] = None,
        load_default: bool = True,
    ) -> "GlobalConfig":
        global _instance
        if _instance is None:
            _instance = super().__new__(cls)
            _instance._initialized = False
        assert _instance is not None
        return _instance

    def __init__(
        self,
        appsettings_path: Optional[str] = None,
        load_default: bool = True,
    ) -> None:
        if self._initialized:
            return
        self._initialized = True
        if not appsettings_path:
            if load_default:
                try:
                    raw = self._load_json(_DEFAULT_CONFIG_PATH)
                    self._config: Dict[str, Any] = raw["PythonScriptsConfig"]
                except ValueError as e:
                    raise ValueError(f"Invalid JSON in {_DEFAULT_CONFIG_PATH}: {e}") from e
            else:
                raise ValueError(
                    "appsettings_path must be provided when load_default is False."
                )
        else:
            path = Path(appsettings_path)
            if not path.exists():
                raise FileNotFoundError(
                    f"appsettings file not found: {path}"
                )
            raw = self._load_json(path)
            if "PythonScriptsConfig" not in raw:
                raise ValueError(
                    f"'PythonScriptsConfig' key not found in {path}"
                )
            self._config: Dict[str, Any] = raw["PythonScriptsConfig"]

    # ------------------------------------------------------------------
    # Singleton management
    # ------------------------------------------------------------------

    @classmethod
    def reset(cls) -> None:
        """Clear the singleton instance (useful in tests)."""
        global _instance
        _instance = None

    # ------------------------------------------------------------------
    # Sections
    # ------------------------------------------------------------------

    @property
    def logger(self) -> Dict[str, Any]:
        """Logger configuration section."""
        return self._config.get("logger", {})

    @property
    def csi_bridge(self) -> Dict[str, Any]:
        """CSI Bridge configuration section."""
        return self._config.get("csi_bridge", {})

    @property
    def midas_civil(self) -> Dict[str, Any]:
        """MIDAS Civil configuration section."""
        return self._config.get("midas_civil", {})

    @property
    def config_for_run(self) -> Dict[str, Any]:
        """Run configuration section."""
        return self._config.get("run_config", {})

    @property
    def current_run_directory(self) -> Path:
        """Current run directory."""
        path_str = self.config_for_run.get("working_directory", "C:/temp")
        path = Path(path_str) / f"run_{_TIMESTAMP}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_json(path: Path) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {path}: {e}") from e





