from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4

from bda.domain import units
from bda.domain.models.submodels.boundary_conditions.spring_stiffness import SpringStiffness
from bda.domain.models.submodels.node import Node
from bda.domain.units.quantities import Angle, Length


class ElementType(str, Enum):
    BEAM = "beam"
    PLATE = "plate" #not implemented
    LINK = "link"


class LinkType(str, Enum):
    RIGID = "rigid"
    ELASTIC = "elastic"


@dataclass
class ElementBase(ABC):
    uid: UUID = field(default_factory=uuid4, init=False)
    element_id: int = field(default=0, init=False)
    element_type: ElementType = field(default=None, init=False)

    def set_id(self, element_id: int):
        self.element_id = element_id

Element = ElementBase

@dataclass
class Element1DBase(ElementBase, ABC):
    node_start: Node
    node_end: Node
    beta_angle: Angle = field(default=0 * units.registry.deg)

    def __post_init__(self):
        if (
                self.node_start.node_id is not None
                and self.node_start.node_id == self.node_end.node_id
        ):
            raise ValueError("Element cannot have identical start and end nodes.")

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}["
            f"id: {self.element_id}, "
            f"start=({self.node_start}), "
            f"end=({self.node_end}), )"
            f"]"
        )

    @property
    def length(self) -> Length:
        """Returns physical length of the element."""
        dx = self.node_end.X - self.node_start.X
        dy = self.node_end.Y - self.node_start.Y
        dz = self.node_end.Z - self.node_start.Z
        return (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5

    @property
    def mid_point(self) -> Node:
        """
        Returns a virtual Node located at the geometric midpoint of the element.

        This node is generated on demand and is not stored in or associated with
        the model topology.
        """
        return Node(
            (self.node_start.X + self.node_end.X) / 2,
            (self.node_start.Y + self.node_end.Y) / 2,
            (self.node_start.Z + self.node_end.Z) / 2,
        )

@dataclass
class Element1D(Element1DBase):
    """
    Represents a standard 1D finite element defined by two nodes.

    This element is typically used to model beam, frame, pile, or other
    linear structural members within the finite element model. The element
    geometry is defined by the start and end nodes inherited from
    ``Element1DBase``.

    Attributes:
        element_type (ElementType):
            Identifier of the element type. Always set to
            ``ElementType.BEAM``.
    """
    element_type: ElementType = field(default= ElementType.BEAM, init=False)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}["
            f"id: {self.element_id}, "
            f"start=({self.node_start}), "
            f"end=({self.node_end}), )"
            f"]"
        )

@dataclass
class ElementLink(Element1DBase):
    """
    Represents a 1D link element connecting two nodes.

    Link elements are typically used to model bearings, springs,
    releases, constraints, or other discrete connections between
    structural components. The mechanical behaviour of the link is
    defined by the selected ``link_type`` and its associated properties.

    Attributes:
        element_type (ElementType):
            Identifier of the element type. Always set to
            ``ElementType.LINK``.

        link_type (LinkType):
            Type of link defining the connection behaviour.

        properties (dict):
            Dictionary containing link-specific properties.
            Reserved for future implementation.
    """

    element_type: ElementType = field(default=ElementType.LINK, init=False)
    link_type: LinkType = field(kw_only=True)
    properties: SpringStiffness = field(kw_only=True, default_factory=SpringStiffness)