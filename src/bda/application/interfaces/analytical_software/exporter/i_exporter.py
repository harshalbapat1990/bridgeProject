from abc import ABC, abstractmethod

from bda.domain import AnalyticalMultiModel
from bda.domain.enums import UnitSystem
from bda.application.interfaces.analytical_software.session_manager import IAnalyticalSoftwareSession


class IExporter(ABC):
    """Abstract base class for model exporters to external software.

    Defines the interface for exporting AnalyticalMultiModel to various
    structural analysis software (MIDAS Civil, CSI Bridge, etc.).

    Exporters communicate directly with external software and use global logger
    for reporting progress and errors. They do not return values.
    """

    @abstractmethod
    def __init__(
            self,
            session: IAnalyticalSoftwareSession
    ):
        ...

    @abstractmethod
    def export(self, amm: AnalyticalMultiModel) -> None:
        """Export analytical model to external software.

        Orchestrates the export process by calling private methods in the correct
        order specific to the target software. Logs progress and errors via global logger.

        Args:
            amm (AnalyticalMultiModel): The analytical model to export.

        Raises:
            Exception: If export fails at any stage. Details logged via global logger.
        """
        pass

    @abstractmethod
    def set_unit_system(self, unit_system: UnitSystem) -> None:
        """Sets the unit system for the export process, ensuring that all exported
        data is correctly converted to the target software's expected units."""
        pass

    @abstractmethod
    def run_analysis(self) -> None:
        """
        Runs the analysis software.
        """
        pass
