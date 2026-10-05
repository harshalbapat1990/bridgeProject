"""AMMContext — Route A structural context backed by AnalyticalMultiModel.

The AMM's group-exposure API is not yet finalised. This implementation
provides stub behaviour (raises ``NotImplementedError``) for the pieces
that depend on the unfinished AMM API, so the rest of the POST pipeline
can be built and tested via Route B (JSONContext) in the meantime.

Once the AMM exposes ``bridge_type`` and ``groups()``, the two stubs
below can be filled in without changing any other code.
"""
from __future__ import annotations

from typing import List

from bda.application.interfaces.structural_context.i_structural_context import IStructuralContext
from bda.domain.enums.bridge_type_enums import BridgeType
from bda.domain.models.analytical_multi_model import AnalyticalMultiModel
from bda.domain.models.structural_group import StructuralGroup


class AMMContext(IStructuralContext):
    """Wraps an ``AnalyticalMultiModel`` and exposes it as structural context.

    Args:
        amm: A fully populated ``AnalyticalMultiModel`` produced by the PRE
             pipeline.
    """

    def __init__(self, amm: AnalyticalMultiModel) -> None:
        self._amm = amm

    @property
    def bridge_type(self) -> BridgeType:
        """Bridge type from the AMM.

        .. note::
            ``AnalyticalMultiModel.bridge_type`` is not yet implemented.
            This will raise ``AttributeError`` until it is. Once the AMM
            exposes this field, no changes to this class are needed.
        """
        bridge_type = getattr(self._amm, "bridge_type", None)
        if bridge_type is None:
            raise NotImplementedError(
                "AnalyticalMultiModel.bridge_type is not yet implemented. "
                "Use JSONContext (Route B) for standalone POST runs."
            )
        return bridge_type

    def groups(self) -> List[StructuralGroup]:
        """Structural groups from the AMM.

        .. note::
            ``AnalyticalMultiModel.groups()`` is not yet implemented.
            This will raise ``NotImplementedError`` until it is.
        """
        get_groups = getattr(self._amm, "get_structural_groups", None)
        if get_groups is None:
            raise NotImplementedError(
                "AnalyticalMultiModel.get_structural_groups() is not yet "
                "implemented. Use JSONContext (Route B) for standalone POST runs."
            )
        raw = get_groups()
        # Expected: an iterable of objects with .id, .element_ids, .node_ids.
        return [
            StructuralGroup(
                id=str(g.id),
                element_ids=frozenset(g.element_ids),
                node_ids=frozenset(g.node_ids),
            )
            for g in raw
        ]
