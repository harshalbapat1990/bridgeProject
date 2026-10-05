"""StructuralGroup — a flat collection of element/node IDs for POST processing.

Distinct from ``Group`` (which mirrors the domain model hierarchy). A
``StructuralGroup`` is deliberately simple: a named set of integer element and
node IDs that a CoordinationModule will pass to the importer and use to filter
``ResultSetView``.

Origin
------
- Route A (AMM-driven): populated by ``AMMContext.groups()`` from the AMM.
- Route B (JSON-driven): populated by ``JSONContext.groups()`` from the run-spec.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StructuralGroup:
    """Immutable group of element and node IDs for one structural component.

    Attributes:
        id:          Human-readable identifier, e.g. ``"Girder_1"``.
        element_ids: Integer element IDs in span order (I-end to J-end along
                     the girder). Order is preserved from the JSON run-spec or
                     AMM so that CoordinationModules can pair node positions
                     with element ends for per-node governing calculations.
        node_ids:    Integer node IDs in span order (first node to last node).
                     Each node sits between element[i-1] J-end and element[i]
                     I-end; this ordering is what the per-node column writes
                     into Excel templates depend on.

    Notes:
        Both sequences are stored as ``tuple[int, ...]`` so iteration order
        is guaranteed. For O(1) membership testing use the ``element_id_set``
        and ``node_id_set`` properties.
    """

    id: str
    element_ids: tuple
    node_ids: tuple

    def __post_init__(self) -> None:
        # Normalise to tuple[int, ...], preserving declaration order.
        object.__setattr__(self, "element_ids", tuple(int(x) for x in self.element_ids))
        object.__setattr__(self, "node_ids", tuple(int(x) for x in self.node_ids))

    @property
    def element_id_set(self) -> frozenset:
        """Frozenset of element IDs for O(1) membership testing."""
        return frozenset(self.element_ids)

    @property
    def node_id_set(self) -> frozenset:
        """Frozenset of node IDs for O(1) membership testing."""
        return frozenset(self.node_ids)
