import json
from typing import List, Type

from pydantic import BaseModel

from bda.contracts.paramodel.bearings.bearing_bc_para_model import BearingBCsSupportParaModel
from bda.contracts.paramodel.deck_appurtenances import BridgeDeckLayoutBaseParaModel
from bda.contracts.paramodel.foundations.foundation_bc_para_model import FoundationBCsParaModel
from bda.contracts.paramodel.foundations.adapter import FoundationBCsParaModelAdapter
from bda.contracts.paramodel.bearings.adapter import BearingBCsParaModelAdapter
from bda.contracts.paramodel.loadings.load_model_base_para_models import LoadModelBaseParaModel
from bda.contracts.paramodel.materials.materials_para_model import MaterialBaseParaModel
from bda.contracts.shared.bda_model_config import BdaModelConfig

from bda.contracts.paramodel.groups import GeometryGroupParaModel
from bda.contracts.paramodel.groups.adapter import GroupsParaModelAdapter
from bda.contracts.paramodel.materials import MaterialParaModel
from bda.contracts.paramodel.sections import SectionParaModel, SectionParaModelAdapter

from bda.contracts.speckle_contracts.bda_analytical.materials.materials_collection import MaterialsCollection
from bda.contracts.speckle_contracts.bda_analytical.model_config_data.model_config_data_DataObject import \
    BDA_ModelDataDataObject
from bda.contracts.speckle_contracts.bda_analytical.model_root import ModelRootCollection
from bda.contracts.speckle_contracts.bda_analytical.sections.section_collection import SectionsCollection
from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.boundary_conditions_collection import BoundaryConditionsCollection
from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.bearings.bearing_bc_collection import BearingBCCollection
from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.foundations.foundation_bc_collection import FoundationBCCollection

from bda.application.interfaces.data_provider.i_data_store_provider import IDataStoreProvider

from bda.infrastructure.data_providers.speckle_helpers.speckle_connector import \
    BridgeDataPlatformSpeckleConnector, parse_speckle_url
from bda.infrastructure.data_providers.speckle_helpers.data_provider_converters.speckle_object_transformations.speckle_ingestion_pipeline \
    import validate_speckle_payload


from bda.infrastructure.utils import AppLogger


class DataSpeckleProvider(IDataStoreProvider):
    """Concrete implementation that uses Speckle credentials."""


    def __init__(self,
                 speckle_model_url: str,
                 model_schema: Type[BaseModel] = ModelRootCollection,
                 authentication_token: str|None = None):
        """Initialize DataSpeckleProvider with Speckle credentials.

        Args:
            speckle_model_url (str): Full Speckle URL identifying a specific model
                version (optional), e.g.
                ``"https://speckle.example.com/projects/<pid>/models/<mid>@<vid>"``.
            model_schema (Type[BaseModel]): Pydantic model class used to validate the
                downloaded Speckle payload.  Defaults to :class:`ModelRootCollection`.
            authentication_token (str | None): Personal-access token for authenticated
                Speckle servers.  Pass ``None`` for public servers.
        """
        # initialization variable assignment
        self.SpeckleModelUrl = speckle_model_url
        self.ModelSchema = model_schema
        self.AuthenticationToken = authentication_token

        # unpack the speckle url
        speckle_url_components = parse_speckle_url(self.SpeckleModelUrl)
        
        # retrieve speckle object from specified model location
        AppLogger().info(f"Establishing Speckle Connection to {speckle_model_url}...")
        self.SpeckleConnector = BridgeDataPlatformSpeckleConnector(
            speckle_url_components=speckle_url_components,
            token=self.AuthenticationToken) #Create connector class instance
        self.SpeckleConnector.select_project(speckle_url_components.project_id)
        self.SpeckleConnector.select_model(speckle_url_components.model_id)
        self.SpeckleObject = self.SpeckleConnector.read_version_object(
            project_id=speckle_url_components.project_id,
            model_id=speckle_url_components.model_id,
            version_id=speckle_url_components.version_id,
        )

        self.ModelDataValidated = validate_speckle_payload(self.SpeckleObject, schema=self.ModelSchema)
    
    def get_model_config_for_project(self) -> BdaModelConfig:
        """Get model configuration for the project.

        Returns:
            BdaModelConfig instance with project configuration details.
        """
        AppLogger().info(f"Parsing model config data from {self.SpeckleModelUrl}...")

        config_data = next(
            (
                e
                for e in self.ModelDataValidated.elements
                if isinstance(e, BDA_ModelDataDataObject)
            ),
            None,
        )

        if config_data is None:
            raise ValueError(
                f"No valid model configuration data found in {self.SpeckleModelUrl}."
            )

        raw_config = config_data.model_dump(mode="json", by_alias=True)
        return BdaModelConfig.model_validate(raw_config)


    def get_materials_for_project(self) -> List[MaterialParaModel]:
        """Get materials for the project."""

        AppLogger().info(
            f"Parsing materials from {self.SpeckleModelUrl}..."
        )

        mat_collection = next(
            (
                e
                for e in self.ModelDataValidated.elements
                if isinstance(e, MaterialsCollection)
            ),
            None,
        )

        if mat_collection is None:
            raise ValueError(
                f"No valid materials found in {self.SpeckleModelUrl}."
            )

        materials = [
            MaterialBaseParaModel.model_validate(
                material.model_dump(mode="json", by_alias=True)
            )
            for material in mat_collection.elements
        ]

        AppLogger().info(
            f"Successfully extracted {len(materials)} materials."
        )

        return materials


    def get_sections_for_project(self) -> List[SectionParaModel]:
        """Get sections for the project.

        Returns:
            List of validated SectionParaModel instances.
        """
        AppLogger().info(f"Parsing sections from {self.SpeckleModelUrl}...")

        sec_collection = next(
            (e for e in self.ModelDataValidated.elements
             if isinstance(e, SectionsCollection)),
            None)

        if sec_collection is None:
            raise ValueError(
                f"No valid sections found in {self.SpeckleModelUrl}."
            )

        sections = [
            SectionParaModelAdapter.parse(
                section.model_dump(mode="json", by_alias=True)
            )
            for section in sec_collection.elements
        ]

        AppLogger().info(
            f"Successfully extracted {len(sections)} sections."
        )

        return sections


    def get_geometry_groups_for_project(self) -> List[GeometryGroupParaModel]:
        """Load group structure for the project.
        
        Returns:
            List of GeometryGroupParaModel objects flattened from the hierarchy.
        """
        from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_bridge import GeometryGroupBridge
        
        AppLogger().info(f"Parsing geometry groups from {self.SpeckleModelUrl}...")
        
        # Find the GeometryGroupBridge in validated data
        geo_bridge = next(
            (e for e in self.ModelDataValidated.elements
             if isinstance(e, GeometryGroupBridge)),
            None,
        )
        
        if geo_bridge is None:
            raise ValueError(f"No valid geometry groups found in {self.SpeckleModelUrl}.")
        
        # Validate the Speckle collection through the existing Paramodel
        # adapter, which understands its grouped properties and child groups.
        all_geometry_groups = []

        def flatten_geometry_hierarchy(geometry_group):
            """Return each validated ParaModel group in hierarchy order."""
            all_geometry_groups.append(geometry_group)
            for nested_group in geometry_group.nested_groups:
                flatten_geometry_hierarchy(nested_group)

        group_data = geo_bridge.model_dump(mode="json", by_alias=True)
        parsed_groups = GroupsParaModelAdapter.parse_list([group_data])
        for geometry_group in parsed_groups:
            flatten_geometry_hierarchy(geometry_group)
        AppLogger().info(f"Successfully extracted {len(all_geometry_groups)} geometry groups.")
        return all_geometry_groups


    def get_foundation_boundary_conditions_for_project(self) -> List[FoundationBCsParaModel]:
        """Load foundation boundary conditions for the project.

        Returns:
            List of foundation boundary conditions objects.
        """
        AppLogger().info(
            f"Parsing foundation boundary conditions from {self.SpeckleModelUrl}..."
        )
        boundary_conditions = next(
            (
                element for element in self.ModelDataValidated.elements
                if isinstance(element, BoundaryConditionsCollection)
            ),
            None,
        )
        collection = next(
            (
                element for element in boundary_conditions.elements
                if isinstance(element, FoundationBCCollection)
            ) if boundary_conditions is not None else (),
            None,
        )
        if collection is None:
            AppLogger().info("No foundation boundary conditions collection found.")
            results = []
        else:
            raw_data = collection.model_dump(mode="json", by_alias=True)
            results = FoundationBCsParaModelAdapter.parse_list(raw_data)
        AppLogger().info(f"Successfully extracted {len(results)} foundation boundary conditions.")
        return results

    def get_bearing_boundary_conditions_for_project(self) -> List[BearingBCsSupportParaModel]:
        """Load bearing boundary conditions for the project.

        Returns:
            List of bearing boundary conditions objects.
        """
        AppLogger().info(
            f"Parsing bearing boundary conditions from {self.SpeckleModelUrl}..."
        )
        boundary_conditions = next(
            (
                element for element in self.ModelDataValidated.elements
                if isinstance(element, BoundaryConditionsCollection)
            ),
            None,
        )
        collection = next(
            (
                element for element in boundary_conditions.elements
                if isinstance(element, BearingBCCollection)
            ) if boundary_conditions is not None else (),
            None,
        )
        if collection is None:
            AppLogger().info("No bearing boundary conditions collection found.")
            results = []
        else:
            raw_data = collection.model_dump(mode="json", by_alias=True)
            results = BearingBCsParaModelAdapter.parse_list(raw_data)
        AppLogger().info(f"Successfully extracted {len(results)} bearing supports.")
        return results

    def get_deck_appurtenances_for_project(self) -> List[BridgeDeckLayoutBaseParaModel]:
        """Load deck appurtenances for the project.

        Returns:
            List of BridgeDeckLayoutBaseParaModel objects.

        Raises:
            FileNotFoundError: If deck appurtenances not found
            ValueError: If deck appurtenances data is invalid
        """
        raise NotImplementedError("The method get_deck_appurtenances_for_project "
                                  "not yet implemented for data Speckle provider.")

    def get_loads_for_project(self) -> List[LoadModelBaseParaModel]:
        """Load loads definitions for the project.

        Returns:
            List of LoadModelBaseParaModel objects.

        Raises:
            FileNotFoundError: If loads file not found
            ValueError: If loads data is invalid
        """
        raise NotImplementedError("The method get_loads_for_project "
                                  "not yet implemented for data Speckle provider.")


if __name__ == "__main__":
    # Example usage
    model = "https://design.jacobs.com/projects/8f0d636aa6/models/4799a9bc6e"

    # read authorization token from local settings
    from pathlib import Path

    config_path = (
        Path(__file__).resolve().parents[2]
        / "config"
        / "init_params_dev.json"
    )

    with open(config_path) as config:
        token = json.load(config)["speckle_authentication_token"]

    provider = DataSpeckleProvider(speckle_model_url=model, authentication_token=token)
    AppLogger().info("Outputting validated model data from Speckle:")
    # AppLogger().info(provider.ModelDataValidated.model_dump_json(indent=2))

    config_data = provider.get_model_config_for_project()
    # AppLogger().info("Outputting model config data:")
    # AppLogger().info(config_data.model_dump_json(indent=2))

    materials = provider.get_materials_for_project()
    # print("\n=== MATERIALS ===")

    if materials:
        # print("\n=== MATERIALS ===")
        for m in materials:
            if m is None:
                continue  # ✅ skip invalid entries
            # print(m.model_dump_json(indent=2))

    AppLogger().info("Outputting validated model data from Speckle:")
    # AppLogger().info(provider.ModelDataValidated.model_dump_json(indent=2))

    sections = provider.get_sections_for_project()

