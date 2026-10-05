import random
import string
from pathlib import Path
from typing import Sequence

from bda.application.interfaces.analytical_software.importer import IResultImporter
from bda.domain.enums import ProcessingStage
from bda.bootstrap.bridge_project_config import BridgeProjectConfig
from bda.application.interfaces.data_provider.i_data_store_provider import IDataStoreProvider
from bda.application.interfaces.analytical_software.exporter import IExporter
from bda.application.interfaces.logging.i_app_logger import IAppLogger
from bda.application.interfaces.module.i_module import IModule
from bda.application.interfaces.analytical_software.session_manager import IAnalyticalSoftwareSession
from bda.domain.models.analytical_multi_model import AnalyticalMultiModel
from bda.infrastructure.adapters.analytical_software.exporters import ExporterFactory
from bda.infrastructure.adapters.analytical_software.importers import ImporterFactory
from bda.infrastructure.adapters.analytical_software.session_managers import SessionFactory
from bda.infrastructure.data_providers.data_file_provider import DataFileProvider
from bda.infrastructure.data_providers.data_speckle_provider import DataSpeckleProvider
from bda.bootstrap.bridge_module_factory import BridgeModuleFactory
from bda.domain.enums import UnitSystem, OutputSoftware, BridgeType

ModuleType = type[IModule]


class BridgeTypeCoordinator:
    """Composition root and pipeline orchestrator.

    Infrastructure assembly and execution flow live here, while module profiles
    are provided by BridgeModuleFactory.
    """

    def __init__(self, config: BridgeProjectConfig, logger: IAppLogger | None = None):
        self._config = config
        self._logger = logger

    @staticmethod
    def _module_types_pre(bridge_type:BridgeType ) -> Sequence[ModuleType]:
        return BridgeModuleFactory.get_module_types(bridge_type, ProcessingStage.PRE)

    @staticmethod
    def _module_types_post(bridge_type:BridgeType) -> Sequence[ModuleType]:
        return BridgeModuleFactory.get_module_types(bridge_type, ProcessingStage.POST)

    def run(self) -> bool:
        data_path = self._config.data_path or self._default_data_path()

        # Data Provider Selection Logic:

        if self._config.use_file_data_provider:
            if not self._config.data_path:
                raise ValueError("Data path must be provided when use_file_data_provider is True.")
            data_provider: IDataStoreProvider = DataFileProvider(self._config.data_path)
        elif self._config.speckle_model_url and self._config.speckle_authentication_token:
            data_provider: IDataStoreProvider = DataSpeckleProvider(
                speckle_model_url=self._config.speckle_model_url,
                authentication_token=self._config.speckle_authentication_token)
        else:
            raise ValueError("No valid data source provided. "
                             "Please specify either a Speckle model URL with authentication "
                             "token or a local data path.")
        
        model_config_data = data_provider.get_model_config_for_project()

        amm = AnalyticalMultiModel(
            unit_system=model_config_data.unit_system
        )

        # Pre-processing Modules
        modules_pre = [module_type(amm, data_provider, self._logger)
                       for module_type
                       in self._module_types_pre(model_config_data.bridge_type)]

        for module in modules_pre:
            success = module.run()
            if not success:
                if self._logger is not None:
                    self._logger.error("Module '%s' failed. Aborting.", module.module_name)
                return False

        session: IAnalyticalSoftwareSession = SessionFactory.get_session(model_config_data.output_software)

        # Model export
        try:
            session.open_session(create_new_instance=True, template_file_path=None)

            # Generate random name with alphanumeric string (letters + digits)
            random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

            session.save_model_as(Path(f'C:/temp/{random_name}'))

            exporter: IExporter = ExporterFactory.get_exporter(model_config_data.output_software, session)
            exporter.export(amm)

            session.save_model()

        except Exception as e:
            if self._logger is not None:
                self._logger.error("Export to %s failed. Aborting: %s: %s",
                                   model_config_data.output_software.value, type(e).__name__, e)
            return False

        if self._logger is not None:
            self._logger.warning("The model was not ready for the post-processing procedure to be executed. "
                                 "The operation was safely aborted.")

        return False

        # Analysis and post-processing
        try:
            exporter.run_analysis()
            session.save_model()

            importer: IResultImporter = ImporterFactory.get_importer(model_config_data.output_software, session)
            modules_post = [
                module_type(amm, data_provider, self._logger, importer) #TODO: implemnt importer into Module Type interface class
                for module_type in self._module_types_post(model_config_data.bridge_type)
            ]

            for module in modules_post:
                success = module.run()
                if not success:
                    if self._logger is not None:
                        self._logger.error("Module '%s' failed. Aborting.", module.module_name)
                    return False

        except Exception as e:
            if self._logger is not None:
                self._logger.error("Post-processing in %s failed. Aborting: %s: %s",
                                   model_config_data.output_software.value, type(e).__name__, e)
            return False

        # TODO: close the software session (session.close_session()) once the post-processing
        #  procedure is in place

        return True

    @staticmethod
    def _default_data_path() -> str:
        repo_root = Path(__file__).resolve().parents[3]
        return str(repo_root / "tests" / "unit" / "fixtures")

