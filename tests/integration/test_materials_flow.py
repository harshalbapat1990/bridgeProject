from unittest import result

from bda.application.interfaces import module
from bda.modules_pre.m1_materials.module_materials import MaterialsModule
import pytest
from pathlib import Path

from bda.infrastructure.data_providers.data_file_provider import DataFileProvider
from bda.contracts.paramodel.materials import MaterialParaModel


class TestMaterialsIntegration:
    """
    Materials module integration tests.

    Validates the full pipeline:
    JSON file > DataFileProvider > MaterialParaModel > validated output

    NOTE:
    These are integration tests (NOT unit tests):
    - No mocking
    - Real file interaction
    - Real model parsing
    """

    @pytest.fixture
    def fixtures_path(self):
        # Resolve ensures absolute safe path
        return (Path(__file__).parent / "../unit/fixtures").resolve()

    @pytest.fixture
    def provider(self, fixtures_path):
        return DataFileProvider(folder=str(fixtures_path))

    def test_materials_pipeline_happy_path(self, provider):
        """
        Validates that valid JSON produces valid MaterialParaModel objects.
        """
        materials = provider.get_materials_for_project()

        assert isinstance(materials, list)
        assert len(materials) > 0

        for material in materials:
            assert isinstance(material, MaterialParaModel)
            assert material.material_type is not None
            assert material.general_properties is not None
            assert material.design_parameters is not None
            assert material.standard_code is not None

    def test_materials_pipeline_is_deterministic(self, provider):
        """
        Validates that repeated runs produce identical outputs.
        Ensures no randomness or hidden state.
        """
        first_run = provider.get_materials_for_project()
        second_run = provider.get_materials_for_project()

        assert len(first_run) == len(second_run)

        for mat1, mat2 in zip(first_run, second_run):
            assert mat1.model_dump(mode="json") == mat2.model_dump(mode="json")

    def test_invalid_material_input_fails_pipeline(self, tmp_path):
        """
        Validates that invalid input JSON fails the pipeline.
        """
        invalid_json = """
        {
          "materials": [
            {
              "material_id": "bad-999",
              "name": "Invalid Material",
              "material_type": "wood",
              "material_model_type": "isotropic",
              "general_properties": {
                "unit_weight": {"value": 25, "unit": "kN/m3"},
                "modulus_of_elasticity": {"value": 2.0e10, "unit": "Pa"},
                "thermal_coefficient": {"value": 1e-5, "unit": "1/C"},
                "poissons_ratio": {"value": 0.2, "unit": null}
              },
              "design_parameters": {}
            }
          ]
        }
        """

        (tmp_path / "materials.json").write_text(invalid_json)

        provider = DataFileProvider(folder=str(tmp_path))

        with pytest.raises(Exception):
            provider.get_materials_for_project()

    def test_materials_output_is_json_serializable(self, provider):
        """
        Validates that output can be serialized into JSON-compatible dicts.
        """
        materials = provider.get_materials_for_project()

        output = [m.model_dump(mode="json") for m in materials]

        assert isinstance(output, list)
        assert len(output) > 0

        for material in output:
            assert "material_type" in material
            assert "general_properties" in material
            assert "design_parameters" in material

    def test_empty_materials_returns_empty_list(self, tmp_path):
        """
        Validates behavior when input JSON contains no materials.
        """
        (tmp_path / "materials.json").write_text('{"materials": []}')

        provider = DataFileProvider(folder=str(tmp_path))
        materials = provider.get_materials_for_project()

        assert materials == []

  
    # Dummy AMM 
    class DummyAMM:
        def __init__(self):
            self.materials = []

        def add_material(self, mat):
            self.materials.append(mat)

 #TEST FUNCTION
    def test_materials_full_module_execution(self, provider):
        amm = self.DummyAMM()

      # Create module with required dependencies
      
        from bda.modules_pre.m1_materials.module_materials import MaterialsModule
        module = MaterialsModule(amm=amm, data_provider=provider)


        # Run module logic
        result = module._run()

        # Assertions
        assert result is True
        assert len(amm.materials) > 0