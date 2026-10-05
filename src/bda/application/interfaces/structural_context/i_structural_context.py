"""IStructuralContext — abstract structural metadata source for POST processing.

The CoordinationModule never talks to the AMM or reads JSON directly. It only
calls ``context.bridge_type`` and ``context.groups()``. Two implementations
satisfy this contract:

- ``AMMContext``   — Route A (AMM-driven, normal post-PRE workflow)
- ``JSONContext``  — Route B (JSON-driven, standalone run)

Both routes produce identical ``BridgeType`` and ``StructuralGroup`` objects,
so the CoordinationModule ``_run()`` body is unchanged regardless of route.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from bda.domain.enums.bridge_type_enums import BridgeType
from bda.domain.models.structural_group import StructuralGroup


class IStructuralContext(ABC):
    """Read-only structural model data consumed by CoordinationModules.

    Implementations must be immutable after construction — no mutation
    methods are allowed on the public interface.
    """

    @property
    @abstractmethod
    def bridge_type(self) -> BridgeType:
        """Bridge type that governs which Profile / CoordinationModules run."""
        ...

    @abstractmethod
    def groups(self) -> List[StructuralGroup]:
        """Return all structural groups in this context.

        CoordinationModules iterate over every group and create a
        ``ResultSetView`` for each, so the list should be ordered
        consistently (e.g. by group id) across calls.
        """
        ...
