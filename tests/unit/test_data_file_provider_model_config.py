import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from bda.contracts.shared.bda_model_config import (
    BdaModelConfig,
    BdaModelConfigAdapter,
)
from bda.domain.enums import (
    UnitSystem,
    OutputSoftware,
    BridgeType,
    DesignCode,
)
from bda.infrastructure.data_providers import DataFileProvider


class TestBdaModelConfig:
    """Unit tests for BdaModelConfig and BdaModelConfigAdapter."""

    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------

    @pytest.fixture
    def fixtures_filename(self):
        return "model_config.json"

    @pytest.fixture
    def fixtures_path(self):
        return Path(__file__).parent / "fixtures"

    @pytest.fixture
    def provider(self, fixtures_path):
        return DataFileProvider(folder=str(fixtures_path))

    @pytest.fixture
    def config_data(self, provider):
        return provider.get_model_config_for_project()

    @pytest.fixture
    def direct_data(self, fixtures_path, fixtures_filename):
        with open(fixtures_path / fixtures_filename, 'r') as f:
            data = json.load(f)
            print(data)
            return data.get("model_config")

    # ------------------------------------------------------------------
    # Direct mapping
    # ------------------------------------------------------------------

    def test_returns_bda_model_config(self, config_data):
        assert isinstance(config_data, BdaModelConfig)

    def test_unit_system(self, config_data):
        assert config_data.unit_system == UnitSystem.SI

    def test_output_software(self, config_data):
        assert config_data.output_software == OutputSoftware.MIDAS

    def test_design_code(self, config_data):
        assert config_data.design_code == DesignCode.AASHTO

    def test_bridge_type(self, config_data):
        assert config_data.bridge_type == BridgeType.PSC_BOX

    # ------------------------------------------------------------------
    # Adapter
    # ------------------------------------------------------------------

    def test_adapter_returns_config(self, direct_data):
        adapter = BdaModelConfigAdapter.model_validate(
            {"model_config": direct_data}
        )

        assert isinstance(adapter.config, BdaModelConfig)

    def test_adapter_parse_returns_bda_model_config(self, direct_data):
        config = BdaModelConfigAdapter.parse(
            {"model_config": direct_data}
        )

        assert isinstance(config, BdaModelConfig)

    def test_adapter_parse_unit_system(self, direct_data):
        config = BdaModelConfigAdapter.parse(
            {"model_config": direct_data}
        )

        assert config.unit_system == UnitSystem.SI

    def test_adapter_parse_output_software(self, direct_data):
        config = BdaModelConfigAdapter.parse(
            {"model_config": direct_data}
        )

        assert config.output_software == OutputSoftware.MIDAS

    def test_adapter_parse_design_code(self, direct_data):
        config = BdaModelConfigAdapter.parse(
            {"model_config": direct_data}
        )

        assert config.design_code == DesignCode.AASHTO

    def test_adapter_parse_bridge_type(self, direct_data):
        config = BdaModelConfigAdapter.parse(
            {"model_config": direct_data}
        )

        assert config.bridge_type == BridgeType.PSC_BOX

    # ------------------------------------------------------------------
    # Validation errors
    # ------------------------------------------------------------------

    def test_missing_unit_system_raises_validation_error(self):
        with pytest.raises(ValidationError):
            BdaModelConfig.model_validate(
                {
                    "output_software": OutputSoftware.MIDAS,
                    "design_code": DesignCode.AASHTO,
                    "bridge_type": BridgeType.PSC_BOX,
                }
            )

    def test_missing_output_software_raises_validation_error(self):
        with pytest.raises(ValidationError):
            BdaModelConfig.model_validate(
                {
                    "unit_system": UnitSystem.SI,
                    "design_code": DesignCode.AASHTO,
                    "bridge_type": BridgeType.PSC_BOX,
                }
            )

    def test_missing_design_code_raises_validation_error(self):
        with pytest.raises(ValidationError):
            BdaModelConfig.model_validate(
                {
                    "unit_system": UnitSystem.SI,
                    "output_software": OutputSoftware.MIDAS,
                    "bridge_type": BridgeType.PSC_BOX,
                }
            )

    def test_missing_bridge_type_raises_validation_error(self):
        with pytest.raises(ValidationError):
            BdaModelConfig.model_validate(
                {
                    "unit_system": UnitSystem.SI,
                    "output_software": OutputSoftware.MIDAS,
                    "design_code": DesignCode.AASHTO,
                }
            )

    def test_adapter_missing_model_config_raises_validation_error(self):
        with pytest.raises(ValidationError):
            BdaModelConfigAdapter.model_validate({})

    # ------------------------------------------------------------------
    # Invalid enum values
    # ------------------------------------------------------------------

    def test_invalid_unit_system_raises_validation_error(self):
        with pytest.raises(ValidationError):
            BdaModelConfig.model_validate(
                {
                    "unit_system": "INVALID",
                    "output_software": OutputSoftware.MIDAS,
                    "design_code": DesignCode.AASHTO,
                    "bridge_type": BridgeType.PSC_BOX,
                }
            )

    def test_invalid_output_software_raises_validation_error(self):
        with pytest.raises(ValidationError):
            BdaModelConfig.model_validate(
                {
                    "unit_system": UnitSystem.SI,
                    "output_software": "INVALID",
                    "design_code": DesignCode.AASHTO,
                    "bridge_type": BridgeType.PSC_BOX,
                }
            )

    def test_invalid_design_code_raises_validation_error(self):
        with pytest.raises(ValidationError):
            BdaModelConfig.model_validate(
                {
                    "unit_system": UnitSystem.SI,
                    "output_software": OutputSoftware.MIDAS,
                    "design_code": "INVALID",
                    "bridge_type": BridgeType.PSC_BOX,
                }
            )

    def test_invalid_bridge_type_raises_validation_error(self):
        with pytest.raises(ValidationError):
            BdaModelConfig.model_validate(
                {
                    "unit_system": UnitSystem.SI,
                    "output_software": OutputSoftware.MIDAS,
                    "design_code": DesignCode.AASHTO,
                    "bridge_type": "INVALID",
                }
            )

    # ------------------------------------------------------------------
    # Idempotency
    # ------------------------------------------------------------------

    def test_consistent_results_across_calls(self, direct_data):
        first = BdaModelConfig.model_validate(direct_data)
        second = BdaModelConfig.model_validate(direct_data)

        assert first.unit_system == second.unit_system
        assert first.output_software == second.output_software
        assert first.design_code == second.design_code
        assert first.bridge_type == second.bridge_type

    # ------------------------------------------------------------------
    # Extensibility
    # ------------------------------------------------------------------

    def test_extra_fields_are_accepted(self, direct_data):
        direct_data["future_property"] = "some future value"

        config = BdaModelConfig.model_validate(direct_data)

        assert config.unit_system == UnitSystem.SI


    # ------------------------------------------------------------------
    # Exact enum values
    # ------------------------------------------------------------------

    def test_enum_values_are_preserved(self, config_data):
        assert config_data.unit_system.value == "Metric"
        assert config_data.output_software.value == "MIDAS Civil"
        assert config_data.design_code.value == "AASHTO"
        assert config_data.bridge_type.value == "PSC Box"