"""Concentrated loads applied to nodes and beam elements.

NOTE: do not add ``from __future__ import annotations`` to modules in this
package (see ``load_components.py``).
"""
from dataclasses import dataclass, field
from typing import cast

from pint.registry import Quantity

from bda.domain.enums.load_enums import LoadTargetType
from bda.domain.models.submodels.element import Element1D
from bda.domain.models.submodels.loads.load_base import PointLoadElementBase
from bda.domain.models.submodels.loads.load_components import LoadOffset
from bda.domain.models.submodels.node import Node
from bda.domain.units.quantities import Length


@dataclass(kw_only=True, repr=False)
class NodalPointLoad(PointLoadElementBase):
    """Concentrated load applied directly at a node.

    Attributes:
        node (Node): Node the load acts on.
    """

    target_type: LoadTargetType = field(default=LoadTargetType.NODE, init=False)
    node: Node

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.node, Node):
            raise TypeError(f"node must be a Node instance, got {type(self.node).__name__}.")

    @property
    def target(self) -> Node:
        return self.node


@dataclass(kw_only=True, repr=False)
class BeamPointLoad(PointLoadElementBase):
    """Concentrated load applied at a position along a beam element.

    Attributes:
        element (Element1D): Beam element the load acts on (links are rejected).
        relative_position (float): Position along the element measured from
            ``node_start`` as a fraction of the element length, in ``[0, 1]``
            (``0.5`` is mid-span).
        offset (LoadOffset | None): Optional eccentricity in the element's
            local ``y`` or ``z`` axis.
    """

    target_type: LoadTargetType = field(default=LoadTargetType.BEAM, init=False)
    element: Element1D
    relative_position: float
    offset: LoadOffset | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        _validate_beam_element(self.element)
        _validate_offset(self.offset)
        if isinstance(self.relative_position, bool) or not isinstance(self.relative_position, (int, float)):
            raise TypeError(
                f"relative_position must be a number in [0, 1], got {type(self.relative_position).__name__}.")
        if not 0.0 <= self.relative_position <= 1.0:
            raise ValueError(f"relative_position must be within [0, 1], got {self.relative_position}.")

    @property
    def target(self) -> Element1D:
        return self.element

    @property
    def absolute_position(self) -> Length:
        """Distance from ``node_start`` to the load along the element axis."""
        return cast(Quantity, self.element.length * self.relative_position)


#
#   helpers
#

def _validate_beam_element(element: object) -> None:
    if not isinstance(element, Element1D):
        raise TypeError(
            f"element must be a beam (Element1D), got {type(element).__name__}. "
            f"Loads on link elements are not supported.")


def _validate_offset(offset: object) -> None:
    if offset is not None and not isinstance(offset, LoadOffset):
        raise TypeError(f"offset must be a LoadOffset or None, got {type(offset).__name__}.")
