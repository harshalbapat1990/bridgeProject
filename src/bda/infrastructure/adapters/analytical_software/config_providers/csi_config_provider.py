from bda.application.interfaces.config.i_config_provider import IConfigProvider
from bda.config.global_config import GlobalConfig


class CSIBridgeConfigProvider(IConfigProvider):
    """Configuration provider for CSI Bridge.

    Reads the 'csi_bridge' section from a GlobalConfig instance.

    Required fields: helper_object, program_id, program_path, headless_mode
    """

    def __init__(self) -> None:
        """Initialize using the GlobalConfig singleton.

        Raises:
            ValueError: If GlobalConfig is not yet initialized or required fields are missing.
        """
        self.config = GlobalConfig().csi_bridge
        self._validate_csi_config()

    def _validate_csi_config(self) -> None:
        """Validate required CSI Bridge configuration fields.

        Raises:
            ValueError: If required fields are missing.
        """
        required_fields = ["helper_object", "program_id", "program_path", "headless_mode"]
        missing = [f for f in required_fields if f not in self.config]
        if missing:
            raise ValueError(
                f"Missing required CSI Bridge configuration fields: {', '.join(missing)}"
            )

    def load_config(self):
        return self.config.copy()

    def get_config_value(self, key: str, default=None):
        return self.config.get(key, default)

    @property
    def helper_object(self) -> str:
        """Return CSI Bridge helper object."""
        return self.config["helper_object"]

    @property
    def program_id(self) -> str:
        """Return CSI Bridge program ID."""
        return self.config["program_id"]

    @property
    def program_path(self) -> str:
        """Return CSI Bridge executable path."""
        return self.config["program_path"]

    @property
    def headless_mode(self) -> bool:
        """Return whether CSI Bridge runs in headless mode."""
        return self.config["headless_mode"]
