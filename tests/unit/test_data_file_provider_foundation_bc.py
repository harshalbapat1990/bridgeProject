import json
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
from pydantic import ValidationError

from bda.contracts.paramodel.foundation.enums import (
    DofTypeEnumParaModel,
    FoundationApplicationTypeEnumParaModel,
    FoundationModelTypeEnumParaModel,
    SoilProfileTypeEnumParaModel,
)
from bda.contracts.paramodel.foundation.foundation_bc_para_model import (
    BearingBasedFoundationApplicationParaModel,
    FoundationBCsBaseParaModel,
    LumpedFoundationBCsParaModel,
    NodeSpringStiffnessParaModel,
    PileInteractionFoundationBCsParaModel,
    PileNodeSpringStiffnessParaModel,
    PileStiffnessUniformDatasetParaModel,
    RotationalStiffnessParaModel,
    SubstructureElementBasedFoundationApplicationParaModel,
    TranslationalStiffnessParaModel,
)
from bda.contracts.paramodel.groups.enums import ElementOrientationParaModel
from bda.contracts.shared import QuantityParaModel
from bda.infrastructure.data_providers.data_file_provider import DataFileProvider


def assert_quantity(q: QuantityParaModel, value: float, unit: str) -> None:
    assert isinstance(q, QuantityParaModel)
    assert q.value == pytest.approx(value)
    assert q.unit == unit


class TestDataFileProvider_FoundationBoundaryConditions:
    """Unit tests for DataFileProvider.get_foundation_boundary_conditions_for_project."""

    @pytest.fixture
    def fixtures_path(self) -> Path:
        return Path(__file__).parent / "fixtures"

    @pytest.fixture
    def provider(self, fixtures_path: Path) -> DataFileProvider:
        return DataFileProvider(folder=str(fixtures_path))

    @pytest.fixture
    def foundations(self, provider: DataFileProvider):
        return provider.get_foundation_boundary_conditions_for_project()

    @pytest.fixture
    def lumped_bearing(self, foundations):
        return foundations[0]

    @pytest.fixture
    def lumped_substructure(self, foundations):
        return foundations[1]

    @pytest.fixture
    def pile_interaction(self, foundations):
        return foundations[2]

    # ------------------------------------------------------------------
    # Collection shape
    # ------------------------------------------------------------------

    def test_foundation_bc_json_exists(self, fixtures_path: Path):
        assert (fixtures_path / "foundation_bc.json").exists()

    def test_returns_list(self, foundations):
        assert isinstance(foundations, list)

    def test_returns_three_foundation_sets(self, foundations):
        assert len(foundations) == 3

    def test_all_items_are_foundation_base_model(self, foundations):
        assert all(isinstance(item, FoundationBCsBaseParaModel) for item in foundations)

    # ------------------------------------------------------------------
    # Lumped foundation (bearing based) - index 0
    # ------------------------------------------------------------------

    def test_lumped_bearing_type(self, lumped_bearing):
        assert isinstance(lumped_bearing, LumpedFoundationBCsParaModel)

    def test_lumped_bearing_base_fields(self, lumped_bearing):
        assert lumped_bearing.support_index == 0
        assert lumped_bearing.foundation_model_type == FoundationModelTypeEnumParaModel.LumpedFoundationModel
        assert lumped_bearing.orientation == ElementOrientationParaModel.ORTHOGONAL

    def test_lumped_bearing_stiffness_definition_type(self, lumped_bearing):
        assert isinstance(lumped_bearing.stiffness_definition, NodeSpringStiffnessParaModel)

    def test_lumped_bearing_translational_sdx_values(self, lumped_bearing):
        sdx = lumped_bearing.stiffness_definition.sdx
        assert isinstance(sdx, TranslationalStiffnessParaModel)
        assert sdx.dof_type == DofTypeEnumParaModel.FREE

    def test_lumped_bearing_translational_sdy_values(self, lumped_bearing):
        sdy = lumped_bearing.stiffness_definition.sdy
        assert isinstance(sdy, TranslationalStiffnessParaModel)
        assert sdy.dof_type == DofTypeEnumParaModel.FIXED

    def test_lumped_bearing_translational_sdz_values(self, lumped_bearing):
        sdz = lumped_bearing.stiffness_definition.sdz
        assert isinstance(sdz, TranslationalStiffnessParaModel)
        assert sdz.dof_type == DofTypeEnumParaModel.CUSTOM
        assert_quantity(sdz.stiffness, 3_000_000, "N/m")

    def test_lumped_bearing_rotational_srx_values(self, lumped_bearing):
        srx = lumped_bearing.stiffness_definition.srx
        assert isinstance(srx, RotationalStiffnessParaModel)
        assert srx.dof_type == DofTypeEnumParaModel.FREE

    def test_lumped_bearing_rotational_sry_values(self, lumped_bearing):
        sry = lumped_bearing.stiffness_definition.sry
        assert isinstance(sry, RotationalStiffnessParaModel)
        assert sry.dof_type == DofTypeEnumParaModel.FIXED

    def test_lumped_bearing_rotational_srz_values(self, lumped_bearing):
        srz = lumped_bearing.stiffness_definition.srz
        assert isinstance(srz, RotationalStiffnessParaModel)
        assert srz.dof_type == DofTypeEnumParaModel.CUSTOM
        assert_quantity(srz.stiffness, 6_000_000, "N*m/rad")

    def test_lumped_bearing_application_type_and_values(self, lumped_bearing):
        app = lumped_bearing.application
        assert isinstance(app, BearingBasedFoundationApplicationParaModel)
        assert app.application_type == FoundationApplicationTypeEnumParaModel.BearingBased
        assert_quantity(app.vertical_offset, 0.5, "m")

    # ------------------------------------------------------------------
    # Lumped foundation (substructure based) - index 1
    # ------------------------------------------------------------------

    def test_lumped_substructure_type(self, lumped_substructure):
        assert isinstance(lumped_substructure, LumpedFoundationBCsParaModel)

    def test_lumped_substructure_base_fields(self, lumped_substructure):
        assert lumped_substructure.support_index == 1
        assert lumped_substructure.foundation_model_type == FoundationModelTypeEnumParaModel.LumpedFoundationModel
        assert lumped_substructure.orientation == ElementOrientationParaModel.ORTHOGONAL

    def test_lumped_substructure_application_type(self, lumped_substructure):
        app = lumped_substructure.application
        assert isinstance(app, SubstructureElementBasedFoundationApplicationParaModel)
        assert app.application_type == FoundationApplicationTypeEnumParaModel.SubstructureElementBased

    # ------------------------------------------------------------------
    # Pile interaction foundation - index 2
    # ------------------------------------------------------------------

    def test_pile_interaction_type(self, pile_interaction):
        assert isinstance(pile_interaction, PileInteractionFoundationBCsParaModel)

    def test_pile_interaction_base_fields(self, pile_interaction):
        assert pile_interaction.support_index == 2
        assert pile_interaction.foundation_model_type == FoundationModelTypeEnumParaModel.PileInteractionModel

    def test_pile_interaction_pile_springs_count(self, pile_interaction):
        assert len(pile_interaction.pile_springs) == 2

    def test_pile_interaction_first_dataset_fields(self, pile_interaction):
        ds = pile_interaction.pile_springs[0]
        assert isinstance(ds, PileStiffnessUniformDatasetParaModel)
        assert ds.soil_profile_type == SoilProfileTypeEnumParaModel.UNIFORM
        assert ds.pile_index == 0

    def test_pile_interaction_first_dataset_top_node_values(self, pile_interaction):
        top_node = pile_interaction.pile_springs[0].top_node
        assert isinstance(top_node, PileNodeSpringStiffnessParaModel)

        assert top_node.sdx.dof_type == DofTypeEnumParaModel.FREE

        assert top_node.sdy.dof_type == DofTypeEnumParaModel.FIXED

        assert top_node.sdz.dof_type == DofTypeEnumParaModel.CUSTOM
        assert_quantity(top_node.sdz.stiffness, 3_000_000, "N/m")

    def test_pile_interaction_first_dataset_bottom_node_values(self, pile_interaction):
        bottom_node = pile_interaction.pile_springs[0].bottom_node
        assert isinstance(bottom_node, PileNodeSpringStiffnessParaModel)

        assert bottom_node.sdx.dof_type == DofTypeEnumParaModel.FREE

        assert bottom_node.sdy.dof_type == DofTypeEnumParaModel.FIXED

        assert bottom_node.sdz.dof_type == DofTypeEnumParaModel.CUSTOM
        assert_quantity(bottom_node.sdz.stiffness, 3_000_000, "N/m")

    def test_pile_interaction_first_dataset_intermediate_values(self, pile_interaction):
        intermediate = pile_interaction.pile_springs[0].intermediate_nodes
        assert isinstance(intermediate, PileNodeSpringStiffnessParaModel)

        assert intermediate.sdx.dof_type == DofTypeEnumParaModel.FREE

        assert intermediate.sdy.dof_type == DofTypeEnumParaModel.FIXED

        assert intermediate.sdz.dof_type == DofTypeEnumParaModel.CUSTOM
        assert_quantity(intermediate.sdz.stiffness, 3_000_000, "N/m")

    def test_pile_interaction_second_dataset_minimal_checks(self, pile_interaction):
        ds = pile_interaction.pile_springs[1]
        assert isinstance(ds, PileStiffnessUniformDatasetParaModel)
        assert ds.soil_profile_type == SoilProfileTypeEnumParaModel.UNIFORM
        assert ds.pile_index == 1
        assert_quantity(ds.top_node.sdx.stiffness, 1_000_000, "N/m")

    # ------------------------------------------------------------------
    # Error handling / negative tests
    # ------------------------------------------------------------------

    def test_file_not_found(self):
        provider = DataFileProvider(folder="/nonexistent/path")
        with pytest.raises(FileNotFoundError):
            provider.get_foundation_boundary_conditions_for_project()

    def test_invalid_json_raises_decode_error(self):
        with patch("builtins.open", mock_open(read_data="{ invalid json }")):
            with pytest.raises(json.JSONDecodeError):
                DataFileProvider(folder=".").get_foundation_boundary_conditions_for_project()

    def test_none_folder_raises_value_error(self):
        with pytest.raises(ValueError, match="Folder not initialized"):
            DataFileProvider(folder=None).get_foundation_boundary_conditions_for_project()

    def test_empty_folder_raises_value_error(self):
        with pytest.raises(ValueError, match="Folder not initialized"):
            DataFileProvider(folder="").get_foundation_boundary_conditions_for_project()

    def test_missing_foundation_bc_key_returns_empty_list(self):
        with patch("builtins.open", mock_open(read_data=json.dumps({"other_key": []}))):
            result = DataFileProvider(folder=".").get_foundation_boundary_conditions_for_project()
            assert result == []

    def test_unknown_foundation_model_type_raises_validation_error(self):
        bad = json.dumps(
            {
                "foundation_bc": [
                    {
                        "support_index": 0,
                        "foundation_model_type": "unknown_model",
                    }
                ]
            }
        )
        with patch("builtins.open", mock_open(read_data=bad)):
            with pytest.raises(ValidationError):
                DataFileProvider(folder=".").get_foundation_boundary_conditions_for_project()

    def test_invalid_application_type_for_lumped_raises_validation_error(self):
        bad = json.dumps(
            {
                "foundation_bc": [
                    {
                        "support_index": 0,
                        "foundation_model_type": "lumped_foundation_model",
                        "stiffness_definition": {
                            "sdx": {"dof_type": "free", "stiffness": {"value": 1, "unit": "N/m"}},
                            "sdy": {"dof_type": "free", "stiffness": {"value": 1, "unit": "N/m"}},
                            "sdz": {"dof_type": "free", "stiffness": {"value": 1, "unit": "N/m"}},
                            "srx": {"dof_type": "free", "stiffness": {"value": 1, "unit": "N*m/rad"}},
                            "sry": {"dof_type": "free", "stiffness": {"value": 1, "unit": "N*m/rad"}},
                            "srz": {"dof_type": "free", "stiffness": {"value": 1, "unit": "N*m/rad"}},
                        },
                        "orientation": "orthogonal",
                        "application": {"application_type": "invalid_app"},
                    }
                ]
            }
        )
        with patch("builtins.open", mock_open(read_data=bad)):
            with pytest.raises(ValidationError):
                DataFileProvider(folder=".").get_foundation_boundary_conditions_for_project()

    def test_invalid_soil_profile_type_for_pile_raises_validation_error(self):
        bad = json.dumps(
            {
                "foundation_bc": [
                    {
                        "support_index": 0,
                        "foundation_model_type": "pile_interaction_model",
                        "pile_springs": [
                            {
                                "soil_profile_type": "layered",
                                "pile_index": 0,
                                "top_node": {
                                    "sdx": {"dof_type": "free", "stiffness": {"value": 1, "unit": "N/m"}},
                                    "sdy": {"dof_type": "free", "stiffness": {"value": 1, "unit": "N/m"}},
                                    "sdz": {"dof_type": "free", "stiffness": {"value": 1, "unit": "N/m"}},
                                },
                                "bottom_node": {
                                    "sdx": {"dof_type": "free", "stiffness": {"value": 1, "unit": "N/m"}},
                                    "sdy": {"dof_type": "free", "stiffness": {"value": 1, "unit": "N/m"}},
                                    "sdz": {"dof_type": "free", "stiffness": {"value": 1, "unit": "N/m"}},
                                },
                                "intermediate_nodes": {
                                    "sdx": {"dof_type": "free", "stiffness": {"value": 1, "unit": "N/m"}},
                                    "sdy": {"dof_type": "free", "stiffness": {"value": 1, "unit": "N/m"}},
                                    "sdz": {"dof_type": "free", "stiffness": {"value": 1, "unit": "N/m"}},
                                },
                            }
                        ],
                    }
                ]
            }
        )
        with patch("builtins.open", mock_open(read_data=bad)):
            with pytest.raises(ValidationError):
                DataFileProvider(folder=".").get_foundation_boundary_conditions_for_project()

    def test_invalid_dof_type_raises_validation_error(self):
        bad = json.dumps(
            {
                "foundation_bc": [
                    {
                        "support_index": 0,
                        "foundation_model_type": "lumped_foundation_model",
                        "stiffness_definition": {
                            "sdx": {"dof_type": "bad_dof", "stiffness": {"value": 1, "unit": "N/m"}},
                            "sdy": {"dof_type": "free", "stiffness": {"value": 1, "unit": "N/m"}},
                            "sdz": {"dof_type": "free", "stiffness": {"value": 1, "unit": "N/m"}},
                            "srx": {"dof_type": "free", "stiffness": {"value": 1, "unit": "N*m/rad"}},
                            "sry": {"dof_type": "free", "stiffness": {"value": 1, "unit": "N*m/rad"}},
                            "srz": {"dof_type": "free", "stiffness": {"value": 1, "unit": "N*m/rad"}},
                        },
                        "orientation": "orthogonal",
                        "application": {"application_type": "substructure_element_based"},
                    }
                ]
            }
        )
        with patch("builtins.open", mock_open(read_data=bad)):
            with pytest.raises(ValidationError):
                DataFileProvider(folder=".").get_foundation_boundary_conditions_for_project()

    def test_free_and_fixed_stiffness_can_be_omitted_and_default_to_none(self):
        payload = json.dumps(
            {
                "foundation_bc": [
                    {
                        "support_index": 0,
                        "foundation_model_type": "lumped_foundation_model",
                        "stiffness_definition": {
                            "sdx": {"dof_type": "free"},
                            "sdy": {"dof_type": "fixed"},
                            "sdz": {"dof_type": "custom", "stiffness": {"value": 3, "unit": "N/m"}},
                            "srx": {"dof_type": "free"},
                            "sry": {"dof_type": "fixed"},
                            "srz": {"dof_type": "custom", "stiffness": {"value": 6, "unit": "N*m/rad"}},
                        },
                        "orientation": "orthogonal",
                        "application": {"application_type": "substructure_element_based"},
                    }
                ]
            }
        )

        with patch("builtins.open", mock_open(read_data=payload)):
            result = DataFileProvider(folder=".").get_foundation_boundary_conditions_for_project()

        lumped = result[0]
        assert isinstance(lumped, LumpedFoundationBCsParaModel)

        assert lumped.stiffness_definition.sdx.stiffness is None
        assert lumped.stiffness_definition.sdy.stiffness is None
        assert lumped.stiffness_definition.srx.stiffness is None
        assert lumped.stiffness_definition.sry.stiffness is None

        assert_quantity(lumped.stiffness_definition.sdz.stiffness, 3, "N/m")
        assert_quantity(lumped.stiffness_definition.srz.stiffness, 6, "N*m/rad")

    # ------------------------------------------------------------------
    # Idempotency
    # ------------------------------------------------------------------

    def test_consistent_results_across_calls(self, provider: DataFileProvider):
        first = provider.get_foundation_boundary_conditions_for_project()
        second = provider.get_foundation_boundary_conditions_for_project()

        assert len(first) == len(second)
        for a, b in zip(first, second):
            assert a.support_index == b.support_index
            assert a.foundation_model_type == b.foundation_model_type

    def test_provider_stores_folder_path(self, fixtures_path: Path):
        provider = DataFileProvider(folder=str(fixtures_path))
        assert provider.Folder == str(fixtures_path)

