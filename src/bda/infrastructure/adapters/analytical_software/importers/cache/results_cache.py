"""Parquet-backed implementation of `IResultCache`.

Stores previously fetched `ResultSet` objects on disk so reruns against
an unchanged model fingerprint can skip the CSI roundtrip. The on-disk
layout is one directory per `model_hash`, containing three Parquet
files:

    <cache_root>/<model_hash>/force_envelopes.parquet
    <cache_root>/<model_hash>/displacements.parquet
    <cache_root>/<model_hash>/stresses.parquet

Each row encodes its composite key (element_id/end/load_case or
node_id/load_case) plus the numeric fields converted to canonical
units. On load, numeric columns are re-wrapped as `pint.Quantity`
using the canonical units from `infrastructure.utils.units`.
"""
from __future__ import annotations

from pathlib import Path

from bda.modules_post.interfaces.i_result_cache import IResultCache
from bda.domain.results.data_request import DataRequest
from bda.domain.results.result_set import ResultSet


class ResultsCache(IResultCache):
    """Persistent result cache backed by Parquet files."""

    def __init__(self, cache_root: Path) -> None:
        """Store the root directory; create it if missing.

        Args:
            cache_root: Directory under which per-model subfolders live.
        """
        self._cache_root = Path(cache_root)
        self._cache_root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # IResultCache
    # ------------------------------------------------------------------
    def available(self, request: DataRequest, model_hash: str) -> DataRequest:
        """Return the subset of `request` that this cache can serve.

        Implementation hint: open the three parquet files for
        `model_hash` (if they exist), read just the key columns, and
        build a new `DataRequest` containing the intersection with
        `request`.
        """
        raise NotImplementedError(
            "ResultsCache.available — to be implemented."
        )

    def load(self, request: DataRequest, model_hash: str) -> ResultSet:
        """Load a `ResultSet` matching exactly the keys in `request`.

        Precondition: `request` has already been filtered by
        `available()`.
        """
        raise NotImplementedError(
            "ResultsCache.load — to be implemented."
        )

    def store(self, result_set: ResultSet, model_hash: str) -> None:
        """Persist every key in `result_set` under `model_hash`.

        Implementations must be idempotent: storing the same keys twice
        must not corrupt the cache. Consider writing to a temp file
        then atomic rename.
        """
        raise NotImplementedError(
            "ResultsCache.store — to be implemented."
        )
