"""Factory for software-specific result importers."""

from typing import Callable

from bda.application.interfaces.analytical_software.session_manager import IAnalyticalSoftwareSession
from bda.application.interfaces.analytical_software.importer import IResultImporter
from bda.domain.enums import OutputSoftware


class ImporterFactory:
    """Create result importers bound to a shared software session_manager."""

    @staticmethod
    def _create_csi_importer(session: IAnalyticalSoftwareSession) -> IResultImporter:
        from bda.infrastructure.adapters.analytical_software.importers.csi_helpers import CsiBridgeResultImporter
        return CsiBridgeResultImporter(session)

    @staticmethod
    def _create_midas_importer(session: IAnalyticalSoftwareSession) -> IResultImporter:
        from bda.infrastructure.adapters.analytical_software.importers.midas_helpers import MidasCivilResultImporter
        return MidasCivilResultImporter(session)

    @staticmethod
    def get_importer(
        software: OutputSoftware,
        session: IAnalyticalSoftwareSession,
    ) -> IResultImporter:
        factory_by_software: dict[OutputSoftware, Callable[[IAnalyticalSoftwareSession], IResultImporter]] = {
            OutputSoftware.CSIBRIDGE: ImporterFactory._create_csi_importer,
            OutputSoftware.MIDAS: ImporterFactory._create_midas_importer,
        }
        creator = factory_by_software.get(software)
        if creator is None:
            raise ValueError(f"No importer available for software: {software.value}")
        return creator(session)

