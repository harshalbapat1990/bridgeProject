from dataclasses import dataclass

@dataclass
class BridgeProjectConfig:
    """Configuration required to build the processing pipeline."""
    config_json_path: str | None
    use_file_data_provider: bool
    data_path: str | None
    speckle_model_url: str | None
    speckle_authentication_token: str | None
