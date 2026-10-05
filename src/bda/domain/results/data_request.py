"""DataRequest — a declarative spec of what results a calculator needs.

Calculators return a `DataRequest` from their `data_requirements()`
classmethod. The post-processing orchestrator merges requests from every
calculator, asks the cache what is already available, subtracts that,
and hands the remainder to the source-specific importer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Iterable


@dataclass(frozen=True)
class DataRequest:
    """Immutable description of the results a calculator (or set of
    calculators) needs from the importer.

    All id sets hold domain-level integer ids. All load case sets hold
    strings (matching the source program's case/combo names).
    """

    element_ids: FrozenSet[int] = field(default_factory=frozenset)
    node_ids: FrozenSet[int] = field(default_factory=frozenset)

    force_loadcases: FrozenSet[str] = field(default_factory=frozenset)
    stress_loadcases: FrozenSet[str] = field(default_factory=frozenset)
    disp_loadcases: FrozenSet[str] = field(default_factory=frozenset)

    # ------------------------------------------------------------------
    # Set operations
    # ------------------------------------------------------------------
    def merge(self, other: "DataRequest") -> "DataRequest":
        """Return the union of two requests."""
        return DataRequest(
            element_ids=self.element_ids | other.element_ids,
            node_ids=self.node_ids | other.node_ids,
            force_loadcases=self.force_loadcases | other.force_loadcases,
            stress_loadcases=self.stress_loadcases | other.stress_loadcases,
            disp_loadcases=self.disp_loadcases | other.disp_loadcases,
        )

    @classmethod
    def merge_all(cls, requests: Iterable["DataRequest"]) -> "DataRequest":
        """Merge an arbitrary iterable of requests into one."""
        merged = cls()
        for r in requests:
            merged = merged.merge(r)
        return merged

    def difference(self, other: "DataRequest") -> "DataRequest":
        """Return the part of `self` that is not covered by `other`.

        Used by the orchestrator to subtract cached coverage from the total
        required work before calling the importer.

        Note: set-wise; if a single load case is partially cached, this
        still treats it as cached. The cache is responsible for its own
        per-key accounting.
        """
        return DataRequest(
            element_ids=self.element_ids - other.element_ids,
            node_ids=self.node_ids - other.node_ids,
            force_loadcases=self.force_loadcases - other.force_loadcases,
            stress_loadcases=self.stress_loadcases - other.stress_loadcases,
            disp_loadcases=self.disp_loadcases - other.disp_loadcases,
        )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def is_empty(self) -> bool:
        """True if there is nothing to fetch."""
        return not (
            self.element_ids
            or self.node_ids
            or self.force_loadcases
            or self.stress_loadcases
            or self.disp_loadcases
        )

    def all_load_cases(self) -> FrozenSet[str]:
        """Union of every load case name referenced by this request."""
        return self.force_loadcases | self.stress_loadcases | self.disp_loadcases
