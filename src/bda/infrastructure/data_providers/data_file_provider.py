import json
from pathlib import Path
from typing import List

from bda.contracts.paramodel.bearings.adapter import BearingBCsParaModelAdapter
from bda.contracts.paramodel.bearings.bearing_bc_para_model import BearingBCsSupportParaModel
from bda.contracts.paramodel.foundation.adapter import FoundationBCsParaModelAdapter
from bda.contracts.paramodel.foundation.foundation_bc_para_model import FoundationBCsParaModel
from bda.contracts.paramodel.groups.adapter import GroupsParaModelAdapter
from bda.contracts.paramodel.materials import MaterialParaModel
from bda.contracts.paramodel.sections import SectionParaModelAdapter, SectionParaModel
from bda.contracts.paramodel.groups import GeometryGroupParaModel
from bda.application.interfaces.data_provider.i_data_store_provider import IDataStoreProvider
from bda.contracts.shared.bda_model_config import BdaModelConfig, BdaModelConfigAdapter


class DataFileProvider(IDataStoreProvider):
    """Concrete implementation that reads materials from a JSON file."""

    def __init__(self, folder: str):
        """Initialize DataFileProvider with a folder path.

        Args:
            folder: Path to the folder containing materials.json
        """
        self.Folder = folder

    def get_model_config_for_project(self, file_name: str = "model_config.json") -> BdaModelConfig:
        """Reads the model configuration from a JSON file.

        Args:
            file_name: Name of the JSON file containing the model configuration.
        """
        if not self.Folder:
            raise ValueError("Folder not initialized. Call the constructor with a folder path.")

        model_config_file = Path(self.Folder) / file_name

        with open(model_config_file, 'r') as f:
            data = json.load(f)

        return BdaModelConfigAdapter.parse(data)

    def get_materials_for_project(self, file_name: str = "materials.json") -> List[MaterialParaModel]:
        """Read materials from materials.json in the folder.

        Returns:
            List of Material objects parsed from the JSON file

        Raises:
            FileNotFoundError: If materials.json is not found
            json.JSONDecodeError: If JSON is invalid
        """

        if not self.Folder:
            raise ValueError("Folder not initialized. Call the constructor with a folder path.")

        materials_file = Path(self.Folder) / file_name

        with open(materials_file, 'r') as f:
            data = json.load(f)

        mat_list = data.get("materials", [])

        para_models = []

        for mat in mat_list:
            para_model = MaterialParaModel.model_validate(mat)
            if para_model is not None:
                para_models.append(para_model)

        return para_models

    def get_sections_for_project(self, file_name: str = "sections.json") -> List[SectionParaModel]:
        """Read sections from sections.json in the folder.

        Returns:
            List of validated SectionParaModel instances (one per section entry).

        Raises:
            FileNotFoundError: If sections.json is not found
            json.JSONDecodeError: If JSON is invalid
            ValueError: If a section has an unknown family/type combination
        """
        if not self.Folder:
            raise ValueError("Folder not initialized. Call the constructor with a folder path.")

        sections_file = Path(self.Folder) / file_name

        with open(sections_file, 'r') as f:
            data = json.load(f)

        sec_list = data.get("sections", [])

        para_models = []

        for sec in sec_list:
            para_model = SectionParaModelAdapter.parse(sec)
            if para_model is not None:
                para_models.append(para_model)

        return para_models

    def get_geometry_groups_for_project(self, file_name: str = "geometry_groups.json") -> List[GeometryGroupParaModel]:
        """Read groups from geometry_groups.json in the folder.

        Returns:
            List of geometry objects parsed from the JSON file

        Raises:
            FileNotFoundError: If gropus.json is not found
            json.JSONDecodeError: If JSON is invalid
        """
        if not self.Folder:
            raise ValueError("Folder not initialized. Call the constructor with a folder path.")

        groups_file = Path(self.Folder) / file_name

        with open(groups_file, 'r') as f:
            data = json.load(f)

        group_list = data.get("geometry_groups", [])
        para_models = GroupsParaModelAdapter.parse_list(group_list)

        return para_models

    def get_foundation_boundary_conditions_for_project(self, file_name: str = "foundation_bc.json") \
            -> List[FoundationBCsParaModel]:
        """Read foundation boundary conditions from foundation_bc.json in the folder.

        Returns:
            List of foundation boundary conditions parsed from the JSON file

        Raises:
            FileNotFoundError: If foundation_bc.json is not found
            json.JSONDecodeError: If JSON is invalid
        """
        if not self.Folder:
            raise ValueError("Folder not initialized. Call the constructor with a folder path.")

        file = Path(self.Folder) / file_name

        with open(file, 'r') as f:
            data = json.load(f)

        raw_results = data.get("foundation_bc", [])
        para_models = FoundationBCsParaModelAdapter.parse_list(raw_results)

        return para_models


    def get_bearing_boundary_conditions_for_project(self, file_name: str = "bearing_bc.json") \
            -> List[BearingBCsSupportParaModel]:
        """Read bearing boundary conditions from bearing_bc.json in the folder.

        Returns:
            List of bearing boundary conditions parsed from the JSON file

        Raises:
            FileNotFoundError: If bearing_bc.json is not found
            json.JSONDecodeError: If JSON is invalid
        """
        if not self.Folder:
            raise ValueError("Folder not initialized. Call the constructor with a folder path.")

        file = Path(self.Folder) / file_name

        with open(file, 'r') as f:
            data = json.load(f)

        raw_results = data.get("bearing_bc", [])
        para_models = BearingBCsParaModelAdapter.parse_list(raw_results)

        return para_models


if __name__ == "__main__":
    # Example usage
    # provider = DataFileProvider(folder="..\\..\\tests\\unit\\fixtures")
    provider = DataFileProvider(folder=r"C:\Users\TS040198\GitHub\DesignAutomation.BridgeAutomationAndOptimisation\tests\unit\fixtures")
    elements = provider.get_foundation_boundary_conditions_for_project()
    for e in elements:
        print(e.model_dump_json(indent=2))

