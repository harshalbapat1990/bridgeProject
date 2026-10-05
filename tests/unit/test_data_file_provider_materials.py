import json
import re

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from bda.contracts.paramodel.materials import MaterialParaModel, MaterialBaseParaModel
from bda.infrastructure.data_providers.data_file_provider import DataFileProvider


class TestDataFileProvider_Materials:
    """Unit tests for DataFileProvider.get_materials_for_project."""

    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------

    @pytest.fixture
    def fixtures_path(self):
        return Path(__file__).parent / "fixtures"

    @pytest.fixture
    def provider(self, fixtures_path):
        return DataFileProvider(folder=str(fixtures_path))

    @pytest.fixture
    def materials(self, provider):
        return provider.get_materials_for_project()

    # ------------------------------------------------------------------
    # Collection shape
    # ------------------------------------------------------------------

    def test_returns_list(self, materials):
        assert isinstance(materials, list)

    def test_returns_four_materials(self, materials):
        assert len(materials) == 4

    def test_all_items_are_material_base(self, materials):
        for m in materials:
            assert isinstance(m, MaterialBaseParaModel)

    # ------------------------------------------------------------------
    # Material 0 – Concrete
    # ------------------------------------------------------------------

    def test_m0_is_material_para_model(self, materials):
        assert isinstance(materials[0], MaterialParaModel)

    def test_m0_name(self, materials):
        assert materials[0].name == "Deck Slab_C5000"

    def test_m0_material_type(self, materials):
        assert materials[0].material_type == "concrete"

    def test_m0_model_type(self, materials):
        assert materials[0].material_model_type == "isotropic"

    def test_m0_modulus_of_elasticity(self, materials):
        assert materials[0].general_properties.modulus_of_elasticity.value == pytest.approx(2.05e10)

    def test_m0_compressive_strength(self, materials):
        assert materials[0].design_parameters.specified_minimum_compressive_strength.value == pytest.approx(40e6)

    # ------------------------------------------------------------------
    # Material 1 – Steel
    # ------------------------------------------------------------------

    def test_m1_is_material_para_model(self, materials):
        assert isinstance(materials[1], MaterialParaModel)

    def test_m1_name(self, materials):
        assert materials[1].name == "Girders_S355"

    def test_m1_material_type(self, materials):
        assert materials[1].material_type == "steel"

    def test_m1_model_type(self, materials):
        assert materials[1].material_model_type == "isotropic"

    def test_m1_modulus_of_elasticity_magnitude(self, materials):
        assert materials[1].general_properties.modulus_of_elasticity.value == pytest.approx(2.05e11)

    def test_m1_modulus_of_elasticity_unit(self, materials):
        assert materials[1].general_properties.modulus_of_elasticity.unit == "Pa"

    def test_m1_unit_weight_magnitude(self, materials):
        assert materials[1].general_properties.unit_weight.value == pytest.approx(78.5)

    def test_m1_unit_weight_unit(self, materials):
        assert materials[1].general_properties.unit_weight.unit == "kN/m3"

    def test_m1_poissons_ratio(self, materials):
        assert materials[1].general_properties.poissons_ratio.value == pytest.approx(0.3)

    def test_m1_thermal_coefficient_magnitude(self, materials):
        assert materials[1].general_properties.thermal_coefficient.value == pytest.approx(6.667e-6)

    def test_m1_thermal_coefficient_unit(self, materials):
        unit = materials[1].general_properties.thermal_coefficient.unit
        assert re.search(r"1/.*C", str(unit))

    def test_m1_yield_strength(self, materials):
        assert materials[1].design_parameters.specified_minimum_yield_strength.value == pytest.approx(355e6)

    def test_m1_tensile_strength(self, materials):
        assert materials[1].design_parameters.specified_minimum_tensile_strength.value == pytest.approx(470e6)

    # ------------------------------------------------------------------
    # Material 2 – Reinforcement
    # ------------------------------------------------------------------

    def test_m2_is_material_para_model(self, materials):
        assert isinstance(materials[2], MaterialParaModel)

    def test_m2_name(self, materials):
        assert materials[2].name == "Rebar_B500"

    def test_m2_material_type(self, materials):
        assert "reinforcement" in materials[2].material_type

    def test_m2_model_type(self, materials):
        assert materials[2].material_model_type == "isotropic"

    def test_m2_modulus_of_elasticity_magnitude(self, materials):
        assert materials[2].general_properties.modulus_of_elasticity.value == pytest.approx(2.00e11)

    def test_m2_modulus_of_elasticity_unit(self, materials):
        assert materials[2].general_properties.modulus_of_elasticity.unit == "Pa"

    def test_m2_unit_weight_magnitude(self, materials):
        assert materials[2].general_properties.unit_weight.value == pytest.approx(78.5)

    def test_m2_unit_weight_unit(self, materials):
        assert materials[2].general_properties.unit_weight.unit == "kN/m3"

    def test_m2_poissons_ratio(self, materials):
        assert materials[2].general_properties.poissons_ratio.value == pytest.approx(0.3)

    def test_m2_thermal_coefficient_magnitude(self, materials):
        assert materials[2].general_properties.thermal_coefficient.value == pytest.approx(1.2e-5)

    def test_m2_thermal_coefficient_unit(self, materials):
        unit = materials[2].general_properties.thermal_coefficient.unit
        assert re.search(r"1/.*C", str(unit))

    def test_m2_yield_strength(self, materials):
        assert materials[2].design_parameters.specified_minimum_yield_strength.value == pytest.approx(500e6)

    def test_m2_ultimate_strength(self, materials):
        assert materials[2].design_parameters.specified_minimum_tensile_strength.value == pytest.approx(550e6)

    # ------------------------------------------------------------------
    # Material 3 – Tendon
    # ------------------------------------------------------------------

    def test_m3_is_material_para_model(self, materials):
        assert isinstance(materials[3], MaterialParaModel)

    def test_m3_name(self, materials):
        assert materials[3].name == "Tendon_15.2"

    def test_m3_material_type(self, materials):
        assert materials[3].material_type == "tendon"

    def test_m3_yield_strength(self, materials):
        assert materials[3].design_parameters.specified_minimum_yield_strength.value == pytest.approx(1600e6)

    def test_m3_tensile_strength(self, materials):
        assert materials[3].design_parameters.specified_minimum_tensile_strength.value == pytest.approx(1860e6)

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def test_file_not_found(self):
        provider = DataFileProvider(folder="/nonexistent/path")
        with pytest.raises(FileNotFoundError):
            provider.get_materials_for_project()

    def test_invalid_json_raises_decode_error(self):
        with patch("builtins.open", mock_open(read_data="{ invalid json }")):
            with pytest.raises(json.JSONDecodeError):
                DataFileProvider(folder=".").get_materials_for_project()

    def test_none_folder_raises_value_error(self):
        with pytest.raises(ValueError, match="Folder not initialized"):
            DataFileProvider(folder=None).get_materials_for_project()

    def test_empty_folder_raises_value_error(self):
        with pytest.raises(ValueError, match="Folder not initialized"):
            DataFileProvider(folder="").get_materials_for_project()

    def test_missing_materials_key_returns_empty_list(self):
        with patch("builtins.open", mock_open(read_data=json.dumps({"other_key": []}))):
            result = DataFileProvider(folder=".").get_materials_for_project()
            assert result == []

    # ------------------------------------------------------------------
    # Idempotency & initialisation
    # ------------------------------------------------------------------

    def test_consistent_results_across_calls(self, provider):
        first = provider.get_materials_for_project()
        second = provider.get_materials_for_project()
        assert len(first) == len(second)
        for a, b in zip(first, second):
            assert a.name == b.name
            assert a.material_type == b.material_type

    def test_provider_stores_folder_path(self, fixtures_path):
        provider = DataFileProvider(folder=str(fixtures_path))
        assert provider.Folder == str(fixtures_path)

    def test_materials_json_exists_in_fixtures(self, fixtures_path):
        assert (fixtures_path / "materials.json").exists()

# ------------------------------------------------------------------
# Negative & extensibility scenarios (QA additions)
# ------------------------------------------------------------------

def test_missing_design_parameters_for_concrete_raises_error(tmp_path):
    file = tmp_path / "materials.json"
    file.write_text(json.dumps({
        "materials": [
            {
                "name": "Concrete Missing Params",
                "material_type": "concrete",
                "material_model_type": "isotropic",
                "general_properties": {
                    "unit_weight": {"value": 25, "unit": "kN/m3"},
                    "modulus_of_elasticity": {"value": 2.0e10, "unit": "Pa"},
                    "thermal_coefficient": {"value": 1e-5, "unit": "1/C"},
                    "poissons_ratio": {"value": 0.2, "unit": None}
                }
                # design_parameters missing
            }
        ]
    }))

    provider = DataFileProvider(folder=str(tmp_path))

    with pytest.raises(Exception):
        provider.get_materials_for_project()


def test_invalid_material_type_raises_error(tmp_path):
    file = tmp_path / "materials.json"
    file.write_text(json.dumps({
        "materials": [
            {
                "name": "Bad Material",
                "material_type": "wood",  # invalid
                "material_model_type": "isotropic",
                "general_properties": {},
                "design_parameters": {}
            }
        ]
    }))

    provider = DataFileProvider(folder=str(tmp_path))

    with pytest.raises(Exception):
        provider.get_materials_for_project()


def test_invalid_quantity_value_type_raises_error(tmp_path):
    file = tmp_path / "materials.json"
    file.write_text(json.dumps({
        "materials": [
            {
                "name": "Bad Quantity",
                "material_type": "steel",
                "material_model_type": "isotropic",
                "general_properties": {
                    "unit_weight": {"value": "invalid", "unit": "kN/m3"}  # wrong type
                },
                "design_parameters": {
                    "specified_minimum_yield_strength": {"value": 355e6, "unit": "Pa"},
                    "specified_minimum_tensile_strength": {"value": 470e6, "unit": "Pa"}
                }
            }
        ]
    }))

    provider = DataFileProvider(folder=str(tmp_path))

    with pytest.raises(Exception):
        provider.get_materials_for_project()


def test_extra_property_is_accepted(tmp_path):
    import json
    from pathlib import Path

    #Load correct base structure from fixtures
    base_file = Path(__file__).parent / "fixtures" / "materials.json"
    data = json.loads(base_file.read_text())

    # Take first material and modify it
    material = data["materials"][0]

    material["name"] = "Concrete Extra"
    material["general_properties"]["extra_field"] = 999

    # Write modified data
    temp_file = tmp_path / "materials.json"
    temp_file.write_text(json.dumps({"materials": [material]}))

    provider = DataFileProvider(folder=str(tmp_path))

    materials = provider.get_materials_for_project()

    assert len(materials) == 1


def test_missing_material_type_raises_error(tmp_path):
    file = tmp_path / "materials.json"
    file.write_text(json.dumps({
        "materials": [
            {
                "name": "Missing Type",
                "material_model_type": "isotropic",
                "general_properties": {},
                "design_parameters": {}
            }
        ]
    }))

    provider = DataFileProvider(folder=str(tmp_path))

    with pytest.raises(Exception):
        provider.get_materials_for_project()
