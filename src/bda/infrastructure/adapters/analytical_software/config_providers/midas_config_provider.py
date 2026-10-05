from bda.application.interfaces.config.i_config_provider import IConfigProvider
from bda.config.global_config import GlobalConfig


class MidasConfigProvider(IConfigProvider):
    """Configuration provider for MIDAS Civil.

    Reads the 'midas_civil' section from a GlobalConfig instance.

    Required fields: base_url, mapi_key, program_path
    """

    def __init__(self) -> None:
        """Initialize using the GlobalConfig singleton.

        Raises:
            ValueError: If GlobalConfig is not yet initialized or required fields are missing.
        """
        self.config = GlobalConfig().midas_civil
        self._validate_midas_config()

    def _validate_midas_config(self) -> None:
        """Validate required MIDAS Civil configuration fields.

        Raises:
            ValueError: If required fields are missing.
        """
        required_fields = ["base_url", "mapi_key", "program_path"]
        missing = [f for f in required_fields if f not in self.config]
        if missing:
            raise ValueError(
                f"Missing required MIDAS configuration fields: {', '.join(missing)}"
            )

    def load_config(self):
        return self.config.copy()

    def get_config_value(self, key: str, default=None):
        return self.config.get(key, default)

    @property
    def base_url(self) -> str:
        """Return MIDAS API base URL."""
        return self.config["base_url"]

    @property
    def mapi_key(self) -> str:
        """Return MIDAS API authentication key."""
        return self.config["mapi_key"]

    @property
    def program_path(self) -> str:
        """Return MIDAS Civil executable path."""
        return self.config["program_path"]
