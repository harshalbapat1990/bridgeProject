"""Factory for software-specific exporters."""

from typing import Callable

from bda.application.interfaces.analytical_software.exporter import IExporter
from bda.application.interfaces.analytical_software.session_manager import IAnalyticalSoftwareSession
from bda.domain.enums import OutputSoftware
from bda.infrastructure.utils.logger import AppLogger


class ExporterFactory:
    """Factory creating exporters bound to a caller-managed software session_manager."""

    @staticmethod
    def _create_midas_exporter(session: IAnalyticalSoftwareSession) -> IExporter:
        from bda.infrastructure.adapters.analytical_software.exporters.midas_civil_exporter import MidasCivilExporter
        return MidasCivilExporter(session)

    @staticmethod
    def _create_csi_exporter(session: IAnalyticalSoftwareSession) -> IExporter:
        from bda.infrastructure.adapters.analytical_software.exporters.csi_bridge_exporter import CSIBridgeExporter
        return CSIBridgeExporter(session)

    @staticmethod
    def get_exporter(
        software: OutputSoftware,
        session: IAnalyticalSoftwareSession,
    ) -> IExporter:
        factory_by_software: dict[OutputSoftware, Callable[[IAnalyticalSoftwareSession], IExporter]] = {
            OutputSoftware.MIDAS: ExporterFactory._create_midas_exporter,
            OutputSoftware.CSIBRIDGE: ExporterFactory._create_csi_exporter,
        }
        creator = factory_by_software.get(software)
        if creator is None:
            logger = AppLogger()
            logger.error("No exporter available for software: %s", software)
            raise ValueError(f"No exporter available for software: {software.value}")
        return creator(session)
