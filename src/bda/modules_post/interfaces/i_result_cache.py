"""Abstract base class for result caches.

The cache is optional. When provided to the orchestrator it lets reruns
skip re-fetching results that have already been pulled for an identical
model fingerprint.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from bda.domain.results.data_request import DataRequest
from bda.domain.results.result_set import ResultSet


class IResultCache(ABC):
    """Persistent (or in-memory) store of previously fetched results.

    Implementations are keyed by a `model_hash` string that the orchestrator
    computes from the AnalyticalMultiModel fingerprint. Any change to the
    model invalidates the cache entry.
    """

    @abstractmethod
    def available(self, request: DataRequest, model_hash: str) -> DataRequest:
        """Return the subset of `request` that the cache can serve.

        Args:
            request: The total data needed by the calculators.
            model_hash: Fingerprint of the model the results belong to.

        Returns:
            A new DataRequest containing only the ids / load cases for
            which cached data exists. The orchestrator subtracts this from
            the total request before calling the importer.
        """
        ...

    @abstractmethod
    def load(self, request: DataRequest, model_hash: str) -> ResultSet:
        """Load a ResultSet covering exactly the keys described by `request`.

        Precondition: `request` has already been filtered by `available()`
        so every key is guaranteed to exist in the cache.
        """
        ...

    @abstractmethod
    def store(self, result_set: ResultSet, model_hash: str) -> None:
        """Persist every key in `result_set` under `model_hash`.

        Implementations should be idempotent: storing the same keys twice
        is allowed and must not corrupt the cache.
        """
        ...
