import json
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
from pydantic import ValidationError

from bda.contracts.paramodel.bearings.bearing_bc_para_model import (
    BearingBCsGirderBaseParaModel,
    BearingBCsSupportParaModel,
    BearingItemParaModel,
    MultipleBearingsBCsParaModel,
    SingleBearingBCsParaModel,
)
from bda.contracts.paramodel.foundations.foundation_bc_para_model import (
    NodeSpringStiffnessParaModel,
    RotationalStiffnessParaModel,
    TranslationalStiffnessParaModel,
)
from bda.contracts.paramodel.foundations.enums import DofTypeEnumParaModel
from bda.contracts.paramodel.groups.enums import (
    BearingConfigurationTypeParaModel,
    ElementOrientationParaModel,
)
from bda.contracts.shared import QuantityParaModel
from bda.infrastructure.data_providers.data_file_provider import DataFileProvider


def assert_quantity(q: QuantityParaModel, value: float, unit: str) -> None:
    assert isinstance(q, QuantityParaModel)
    assert q.value == pytest.approx(value)
    assert q.unit == unit


class TestDataFileProvider_BearingBoundaryConditions:
    """Unit tests for DataFileProvider.get_bearing_boundary_conditions_for_project."""

    @pytest.fixture
    def fixtures_path(self) -> Path:
        return Path(__file__).parent / "fixtures"

    @pytest.fixture
    def provider(self, fixtures_path: Path) -> DataFileProvider:
        return DataFileProvider(folder=str(fixtures_path))

    @pytest.fixture
    def bearings(self, provider: DataFileProvider):
        return provider.get_bearing_boundary_conditions_for_project()

    @pytest.fixture
    def support_singular(self, bearings):
        return bearings[0]

    @pytest.fixture
    def support_multiple(self, bearings):
        return bearings[1]

    # ------------------------------------------------------------------
    # Collection shape
    # ------------------------------------------------------------------

    def test_bearing_bc_json_exists(self, fixtures_path: Path):
        assert (fixtures_path / "bearing_bc.json").exists()

    def test_returns_list(self, bearings):
        assert isinstance(bearings, list)

    def test_returns_two_support_sets(self, bearings):
        assert len(bearings) == 2

    def test_all_items_are_support_para_model(self, bearings):
        assert all(isinstance(item, BearingBCsSupportParaModel) for item in bearings)

    # ------------------------------------------------------------------
    # Support 0 — singular bearing configuration
    # ------------------------------------------------------------------

    def test_support_singular_index(self, support_singular):
        assert support_singular.support_index == 0

    def test_support_singular_girder_count(self, support_singular):
        assert len(support_singular.bearings_by_girder) == 2

    def test_support_singular_all_girders_are_base_model(self, support_singular):
        assert all(isinstance(g, BearingBCsGirderBaseParaModel) for g in support_singular.bearings_by_girder)

    def test_support_singular_girder0_type(self, support_singular):
        assert isinstance(support_singular.bearings_by_girder[0], SingleBearingBCsParaModel)

    def test_support_singular_girder0_index(self, support_singular):
        assert support_singular.bearings_by_girder[0].girder_index == 0

    def test_support_singular_girder0_configuration_type(self, support_singular):
        assert support_singular.bearings_by_girder[0].bearing_configuration_type == BearingConfigurationTypeParaModel.SINGULAR

    def test_support_singular_girder0_bearing_definition_type(self, support_singular):
        bearing = support_singular.bearings_by_girder[0].bearing_definition
        assert isinstance(bearing, BearingItemParaModel)

    def test_support_singular_girder0_bearing_index(self, support_singular):
        assert support_singular.bearings_by_girder[0].bearing_definition.bearing_index == 0

    def test_support_singular_girder0_orientation(self, support_singular):
        assert support_singular.bearings_by_girder[0].bearing_definition.orientation == ElementOrientationParaModel.ORTHOGONAL

    def test_support_singular_girder0_stiffness_type(self, support_singular):
        stiffness = support_singular.bearings_by_girder[0].bearing_definition.bearing_stiffness_definition
        assert isinstance(stiffness, NodeSpringStiffnessParaModel)

    def test_support_singular_girder0_sdx_free(self, support_singular):
        sdx = support_singular.bearings_by_girder[0].bearing_definition.bearing_stiffness_definition.sdx
        assert isinstance(sdx, TranslationalStiffnessParaModel)
        assert sdx.dof_type == DofTypeEnumParaModel.FREE

    def test_support_singular_girder0_sdy_fixed(self, support_singular):
        sdy = support_singular.bearings_by_girder[0].bearing_definition.bearing_stiffness_definition.sdy
        assert sdy.dof_type == DofTypeEnumParaModel.FIXED

    def test_support_singular_girder0_sdz_custom_stiffness(self, support_singular):
        sdz = support_singular.bearings_by_girder[0].bearing_definition.bearing_stiffness_definition.sdz
        assert sdz.dof_type == DofTypeEnumParaModel.CUSTOM
        assert_quantity(sdz.stiffness, 3_000_000, "N/m")

    def test_support_singular_girder0_srz_custom_stiffness(self, support_singular):
        srz = support_singular.bearings_by_girder[0].bearing_definition.bearing_stiffness_definition.srz
        assert isinstance(srz, RotationalStiffnessParaModel)
        assert srz.dof_type == DofTypeEnumParaModel.CUSTOM
        assert_quantity(srz.stiffness, 6_000_000, "N*m/rad")

    def test_support_singular_girder1_orientation_skewed(self, support_singular):
        assert support_singular.bearings_by_girder[1].bearing_definition.orientation == ElementOrientationParaModel.SKEWED

    # ------------------------------------------------------------------
    # Support 1 — multiple bearing configuration
    # ------------------------------------------------------------------

    def test_support_multiple_index(self, support_multiple):
        assert support_multiple.support_index == 1

    def test_support_multiple_girder_count(self, support_multiple):
        assert len(support_multiple.bearings_by_girder) == 2

    def test_support_multiple_girder0_type(self, support_multiple):
        assert isinstance(support_multiple.bearings_by_girder[0], MultipleBearingsBCsParaModel)

    def test_support_multiple_girder0_configuration_type(self, support_multiple):
        assert support_multiple.bearings_by_girder[0].bearing_configuration_type == BearingConfigurationTypeParaModel.MULTIPLE

    def test_support_multiple_girder0_bearing_definitions_count(self, support_multiple):
        assert len(support_multiple.bearings_by_girder[0].bearing_definitions) == 2

    def test_support_multiple_girder0_bearing_definitions_are_bearing_items(self, support_multiple):
        defs = support_multiple.bearings_by_girder[0].bearing_definitions
        assert all(isinstance(b, BearingItemParaModel) for b in defs)

    def test_support_multiple_girder0_bearing0_index(self, support_multiple):
        assert support_multiple.bearings_by_girder[0].bearing_definitions[0].bearing_index == 0

    def test_support_multiple_girder0_bearing1_index(self, support_multiple):
        assert support_multiple.bearings_by_girder[0].bearing_definitions[1].bearing_index == 1

    def test_support_multiple_girder0_bearing0_sdz_stiffness(self, support_multiple):
        sdz = support_multiple.bearings_by_girder[0].bearing_definitions[0].bearing_stiffness_definition.sdz
        assert sdz.dof_type == DofTypeEnumParaModel.CUSTOM
        assert_quantity(sdz.stiffness, 1_500_000, "N/m")

    # ------------------------------------------------------------------
    # Error handling / negative tests
    # ------------------------------------------------------------------

    def test_file_not_found(self):
        provider = DataFileProvider(folder="/nonexistent/path")
        with pytest.raises(FileNotFoundError):
            provider.get_bearing_boundary_conditions_for_project()

    def test_invalid_json_raises_decode_error(self):
        with patch("builtins.open", mock_open(read_data="{ invalid json }")):
            with pytest.raises(json.JSONDecodeError):
                DataFileProvider(folder=".").get_bearing_boundary_conditions_for_project()

    def test_none_folder_raises_value_error(self):
        with pytest.raises(ValueError, match="Folder not initialized"):
            DataFileProvider(folder=None).get_bearing_boundary_conditions_for_project()

    def test_empty_folder_raises_value_error(self):
        with pytest.raises(ValueError, match="Folder not initialized"):
            DataFileProvider(folder="").get_bearing_boundary_conditions_for_project()

    def test_missing_bearing_bc_key_returns_empty_list(self):
        with patch("builtins.open", mock_open(read_data=json.dumps({"other_key": []}))):
            result = DataFileProvider(folder=".").get_bearing_boundary_conditions_for_project()
            assert result == []

    def test_unknown_bearing_configuration_type_raises_validation_error(self):
        bad = json.dumps(
            {
                "bearing_bc": [
                    {
                        "support_index": 0,
                        "bearings_by_girder": [
                            {
                                "girder_index": 0,
                                "bearing_configuration_type": "unknown_type",
                                "bearing_definition": {
                                    "bearing_index": 0,
                                    "orientation": "orthogonal",
                                    "bearing_stiffness_definition": {
                                        "sdx": {"dof_type": "free"},
                                        "sdy": {"dof_type": "fixed"},
                                        "sdz": {"dof_type": "free"},
                                        "srx": {"dof_type": "free"},
                                        "sry": {"dof_type": "free"},
                                        "srz": {"dof_type": "free"},
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        )
        with patch("builtins.open", mock_open(read_data=bad)):
            with pytest.raises(ValidationError):
                DataFileProvider(folder=".").get_bearing_boundary_conditions_for_project()

    def test_invalid_orientation_raises_validation_error(self):
        bad = json.dumps(
            {
                "bearing_bc": [
                    {
                        "support_index": 0,
                        "bearings_by_girder": [
                            {
                                "girder_index": 0,
                                "bearing_configuration_type": "singular",
                                "bearing_definition": {
                                    "bearing_index": 0,
                                    "orientation": "invalid_orientation",
                                    "bearing_stiffness_definition": {
                                        "sdx": {"dof_type": "free"},
                                        "sdy": {"dof_type": "free"},
                                        "sdz": {"dof_type": "free"},
                                        "srx": {"dof_type": "free"},
                                        "sry": {"dof_type": "free"},
                                        "srz": {"dof_type": "free"},
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        )
        with patch("builtins.open", mock_open(read_data=bad)):
            with pytest.raises(ValidationError):
                DataFileProvider(folder=".").get_bearing_boundary_conditions_for_project()

    def test_invalid_dof_type_raises_validation_error(self):
        bad = json.dumps(
            {
                "bearing_bc": [
                    {
                        "support_index": 0,
                        "bearings_by_girder": [
                            {
                                "girder_index": 0,
                                "bearing_configuration_type": "singular",
                                "bearing_definition": {
                                    "bearing_index": 0,
                                    "orientation": "orthogonal",
                                    "bearing_stiffness_definition": {
                                        "sdx": {"dof_type": "bad_dof"},
                                        "sdy": {"dof_type": "free"},
                                        "sdz": {"dof_type": "free"},
                                        "srx": {"dof_type": "free"},
                                        "sry": {"dof_type": "free"},
                                        "srz": {"dof_type": "free"},
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        )
        with patch("builtins.open", mock_open(read_data=bad)):
            with pytest.raises(ValidationError):
                DataFileProvider(folder=".").get_bearing_boundary_conditions_for_project()

    def test_free_stiffness_can_be_omitted_defaults_to_none(self):
        payload = json.dumps(
            {
                "bearing_bc": [
                    {
                        "support_index": 0,
                        "bearings_by_girder": [
                            {
                                "girder_index": 0,
                                "bearing_configuration_type": "singular",
                                "bearing_definition": {
                                    "bearing_index": 0,
                                    "orientation": "orthogonal",
                                    "bearing_stiffness_definition": {
                                        "sdx": {"dof_type": "free"},
                                        "sdy": {"dof_type": "fixed"},
                                        "sdz": {"dof_type": "custom", "stiffness": {"value": 3, "unit": "N/m"}},
                                        "srx": {"dof_type": "free"},
                                        "sry": {"dof_type": "fixed"},
                                        "srz": {"dof_type": "free"},
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        )

        with patch("builtins.open", mock_open(read_data=payload)):
            result = DataFileProvider(folder=".").get_bearing_boundary_conditions_for_project()

        stiffness = result[0].bearings_by_girder[0].bearing_definition.bearing_stiffness_definition
        assert stiffness.sdx.stiffness is None
        assert stiffness.sdy.stiffness is None
        assert stiffness.srx.stiffness is None
        assert stiffness.srz.stiffness is None
        assert_quantity(stiffness.sdz.stiffness, 3, "N/m")

    # ------------------------------------------------------------------
    # Idempotency
    # ------------------------------------------------------------------

    def test_consistent_results_across_calls(self, provider: DataFileProvider):
        first = provider.get_bearing_boundary_conditions_for_project()
        second = provider.get_bearing_boundary_conditions_for_project()

        assert len(first) == len(second)
        for a, b in zip(first, second):
            assert a.support_index == b.support_index
            assert len(a.bearings_by_girder) == len(b.bearings_by_girder)

    def test_provider_stores_folder_path(self, fixtures_path: Path):
        provider = DataFileProvider(folder=str(fixtures_path))
        assert provider.Folder == str(fixtures_path)
