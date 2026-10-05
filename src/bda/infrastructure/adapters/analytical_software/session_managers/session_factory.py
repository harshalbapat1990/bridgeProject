"""Factory for creating analytical software session_managers."""

from typing import Callable

from bda.application.interfaces.analytical_software.session_manager import IAnalyticalSoftwareSession
from bda.domain.enums import OutputSoftware
from bda.infrastructure.adapters.analytical_software.config_providers.csi_config_provider import CSIBridgeConfigProvider
from bda.infrastructure.adapters.analytical_software.config_providers.midas_config_provider import MidasConfigProvider
from bda.infrastructure.adapters.analytical_software.session_managers.csi_bridge_session import CSIBridgeSession
from bda.infrastructure.adapters.analytical_software.session_managers.midas_civil_session import MidasCivilSession


class SessionFactory:
    """Build a concrete session_manager per target software."""

    @staticmethod
    def get_session(software: OutputSoftware) -> IAnalyticalSoftwareSession:
        factory_by_software: dict[OutputSoftware, Callable[[], IAnalyticalSoftwareSession]] = {
            OutputSoftware.CSIBRIDGE: lambda: CSIBridgeSession(CSIBridgeConfigProvider()),
            OutputSoftware.MIDAS: lambda: MidasCivilSession(MidasConfigProvider()),
        }
        creator = factory_by_software.get(software)
        if creator is None:
            raise ValueError(f"No session_manager available for software: {software.value}")
        return creator()
