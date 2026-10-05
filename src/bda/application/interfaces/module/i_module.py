from abc import ABC, abstractmethod

from bda.application.interfaces.logging import IAppLogger, NullLogger
from bda.application.interfaces.data_provider.i_data_store_provider import IDataStoreProvider
from bda.domain import AnalyticalMultiModel


class IModule(ABC):

    def __init__(self, amm: AnalyticalMultiModel, data_provider: IDataStoreProvider, logger: IAppLogger | None = None):
        self.amm = amm
        self.data_provider = data_provider
        self.logger = logger or NullLogger()

    @property
    @abstractmethod
    def module_name(self) -> str:
        """Unique module name."""
        ...

    @abstractmethod
    def _run(self):
        ...

    def run(self) -> bool:
        self.logger.info("Starting module: '%s'", self.module_name)

        try:
            self._run()
        except Exception as e:
            self.logger.error("Exception raised while running module: '%s'", e)
            return False

        self.logger.info("Finished module: '%s'", self.module_name)
        return True

