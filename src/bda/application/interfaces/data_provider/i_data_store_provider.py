from abc import ABC, abstractmethod
from typing import List

from bda.contracts.paramodel.bearings.bearing_bc_para_model import BearingBCsSupportParaModel
from bda.contracts.paramodel.deck_appurtenances import BridgeDeckLayoutBaseParaModel
from bda.contracts.paramodel.foundations.foundation_bc_para_model import FoundationBCsParaModel
from bda.contracts.paramodel.groups import GeometryGroupParaModel
from bda.contracts.paramodel.loadings.load_model_base_para_models import LoadModelBaseParaModel
from bda.contracts.paramodel.materials import MaterialBaseParaModel
from bda.contracts.paramodel.sections import SectionBaseParaModel
from bda.contracts.shared.bda_model_config import BdaModelConfig


class IDataStoreProvider(ABC):
    """Abstract base class for data store providers."""
    
    @abstractmethod
    def get_model_config_for_project(self) -> BdaModelConfig:
        """Get model configuration for the project.

        Returns:
            BdaModelConfig instance with project configuration details.
        """
        pass

    @abstractmethod
    def get_materials_for_project(self) -> List[MaterialBaseParaModel]:
        """Get materials for the project.

        Returns:
            List of Material objects
        """
        pass

    @abstractmethod
    def get_sections_for_project(self) -> List[SectionBaseParaModel]:
        """Get sections for the project.

        Returns:
            List of validated SectionParaModel instances.

        Raises:
            FileNotFoundError: If sections file not found
            json.JSONDecodeError: If JSON is invalid
            ValueError: If a section has an unknown family/type combination
        """
        pass

    @abstractmethod
    def get_geometry_groups_for_project(self) -> List[GeometryGroupParaModel]:
        """Load group structure for the project.

        Returns:
            List of GeometryGroupParaModel objects in hierarchy.

        Raises:
            FileNotFoundError: If groups not found
            ValueError: If groups data is invalid
        """
        pass

    @abstractmethod
    def get_foundation_boundary_conditions_for_project(self) -> List[FoundationBCsParaModel]:
        """Load foundation boundary conditions for the project.

        Returns:
            List of FoundationBCsParaModel objects.

        Raises:
            FileNotFoundError: If foundation boundary conditions not found
            ValueError: If foundation boundary conditions data is invalid
        """
        pass

    @abstractmethod
    def get_bearing_boundary_conditions_for_project(self) -> List[BearingBCsSupportParaModel]:
        """Load bearing boundary conditions for the project.

        Returns:
            List of BearingBCsSupportParaModel objects.

        Raises:
            FileNotFoundError: If bearing boundary conditions not found
            ValueError: If bearing boundary conditions data is invalid
        """
        pass

    @abstractmethod
    def get_deck_appurtenances_for_project(self) -> List[BridgeDeckLayoutBaseParaModel]:
        """Load deck appurtenances for the project.

        Returns:
            List of BridgeDeckLayoutBaseParaModel objects.

        Raises:
            FileNotFoundError: If deck appurtenances not found
            ValueError: If deck appurtenances data is invalid
        """
        pass

    @abstractmethod
    def get_loads_for_project(self) -> List[LoadModelBaseParaModel]:
        """Load definitions for the project.

        Returns:
            List of LoadModelBaseParaModel objects.

        Raises:
            FileNotFoundError: If loads file not found
            ValueError: If loads data is invalid
        """
        pass