from abc import abstractmethod, ABC
from typing import List

from bda.application.interfaces import IAnalyticalSoftwareSession
from bda.domain.results import DataRequest, ResultSet, LoadCase


class IResultImporter(ABC):
    """Abstract contract for pulling analysis results out of a source program.

    Lifecycle:
        1. The caller constructs the concrete importer, passing an already-
           open connection to the source program.
        2. Calculators declare their needs as `DataRequest` objects; the
           orchestrator merges them and calls `fetch()`.
        3. The importer returns a `ResultSet` containing only normalized
           primitives (pint Quantities, no source-specific types).
    """

    @abstractmethod
    def __init__(
            self,
            session: IAnalyticalSoftwareSession
    ):
        ...


    @abstractmethod
    def fetch(self, request: DataRequest) -> ResultSet:
        """Fetch and normalize all results described by `request`.

        Args:
            request: The merged data requirements from all calculators.

        Returns:
            A normalized `ResultSet`. Every physical quantity inside is a
            `pint.Quantity`.

        Raises:
            RuntimeError: If the source program cannot serve the request
                (e.g. analysis has not been run, load case name unknown).
        """
        ...

    @abstractmethod
    def available_load_cases(self) -> List[LoadCase]:
        """Return all load cases currently defined in the source program.

        Useful for validating a calculator's load-case names before the
        more expensive result fetch.
        """
        ...
