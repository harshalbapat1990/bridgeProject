"""Abstract base class for post-processing calculators.

A calculator performs a single design check against a filtered slice of
normalized analysis results (`ResultSetView`). Calculators are source-
agnostic: they never know whether the results came from CSI Bridge,
Midas, or any other program.

Lifecycle:
    1. The orchestrator asks every calculator class for its
       `data_requirements(component)` and merges them into one
       `DataRequest`.
    2. The orchestrator hands the merged request to the importer, which
       returns a full `ResultSet`.
    3. The orchestrator instantiates each calculator and calls `run()`
       with a `ResultSetView` restricted to the calculator's component.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from bda.domain.results.data_request import DataRequest
from bda.domain.results.result_set import ResultSetView

if TYPE_CHECKING:
    from bda.domain.models.submodels import GeometryGroupBase


class ICalculator(ABC):
    """Contract for a single design-check calculator.

    Implementations should be stateless between runs: all per-run state
    belongs on the instance created for that run. The orchestrator is
    free to reuse the class for multiple components.
    """

    @classmethod
    @abstractmethod
    def data_requirements(cls, component: "GeometryGroupBase") -> DataRequest:
        """Declare what result data this calculator needs for `component`.

        Called once per (calculator, component) pair before any fetch.
        The orchestrator merges these into a single `DataRequest` so the
        importer only pulls each key once.

        Args:
            component: The group the calculator will run against.

        Returns:
            A `DataRequest` containing the element ids, node ids and
            load-case names the calculator intends to read from the
            `ResultSetView` passed to `run()`.
        """
        ...

    @abstractmethod
    def run(self, results: ResultSetView) -> Any:
        """Execute the design check against the provided results view.

        Args:
            results: A read-only slice of the full `ResultSet`, filtered
                to the element/node ids of this calculator's component.

        Returns:
            A calculator-specific check result object. The concrete type
            is defined per calculator (not yet part of the shared
            scaffold).
        """
        ...
