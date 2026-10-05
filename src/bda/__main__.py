"""
Entry point for:
  - python -m bda
  - bda (console_script after pip install)
"""

import json
import os
from pathlib import Path
from typing import Any

from bda.bootstrap.bridge_type_coordinator import BridgeTypeCoordinator, BridgeProjectConfig
from bda.config.global_config import GlobalConfig
from bda.infrastructure.utils.logger import AppLogger

DEFAULT_INIT_PARAMS_PATH = Path(__file__).resolve().parent / "config" / "init_params_dev.json"


def _load_defaults_from_file() -> dict[str, Any]:
    """Read default init params from config/init_params_dev.json."""

    try:
        with DEFAULT_INIT_PARAMS_PATH.open("r", encoding="utf-8") as file:
            defaults = json.load(file)
    except FileNotFoundError:
        raise ValueError("init_params_dev.json file must be provided to run this program without Orchestrator")
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in defaults file: {exc}") from exc

    if not isinstance(defaults, dict):
        raise ValueError("Defaults file must contain a JSON object.")

    return defaults


def _load_config_from_env() -> dict[str, Any]:
    """Read optional JSON config from the BDA_CONFIG environment variable."""
    raw = os.getenv("BDA_CONFIG")
    if not raw:
        return {}

    try:
        config = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in BDA_CONFIG: {exc}") from exc

    if not isinstance(config, dict):
        raise ValueError("BDA_CONFIG must be a JSON object.")

    return config


def _resolve_config_params(config_params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Merge defaults, environment config, and explicit parameters."""
    defaults = _load_defaults_from_file()

    env_config = _load_config_from_env()
    explicit = config_params or {}

    return {
        **defaults,
        **env_config,
        **explicit,
    }

def main(config_params: dict[str, Any] | None = None) -> None:
    """Run Bridge Automation and Optimisation.

    Args:
        config_params: Optional dict with keys:
                       unit_system, output_software, bridge_type, data_path.
                       Explicit values override BDA_CONFIG, then defaults.
    """

    try:
        resolved = _resolve_config_params(config_params)
    except ValueError as exc:
        print(
            f"[CONFIG ERROR] Failed to resolve configuration parameters.\n"
            f"Reason: {exc}\n"
            f"Input data: {config_params}"
        )
        raise SystemExit(1) from exc

    config_json_path = resolved.get("config_json_path")
    raw_use_file = resolved.get("use_file_data_provider", False)
    if isinstance(raw_use_file, str):
        use_file_data_provider = raw_use_file.strip().lower() in ("true", "1", "yes")
    else:
        use_file_data_provider = bool(raw_use_file)
    data_path = resolved.get("data_path")
    speckle_model_url = resolved.get("speckle_model_url")
    speckle_authentication_token = resolved.get("speckle_authentication_token")

    config = BridgeProjectConfig(
        config_json_path=config_json_path,
        use_file_data_provider=use_file_data_provider,
        data_path=data_path,
        speckle_model_url=speckle_model_url,
        speckle_authentication_token=speckle_authentication_token
    )

    # initialize the global config singleton using path to appsettings json file provided
    GlobalConfig(appsettings_path=config.config_json_path, load_default=False)

    # initialize the logger singleton
    logger = AppLogger()

    config_dict = vars(config).copy()
    config_dict["speckle_authentication_token"] = "*****"

    logger.debug("Starting BDA with config: \n%s", json.dumps(config_dict, indent=2, default=str))

    coordinator = BridgeTypeCoordinator(config, logger)
    success = coordinator.run()

    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
