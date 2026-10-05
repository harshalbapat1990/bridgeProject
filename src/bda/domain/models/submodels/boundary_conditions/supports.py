from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field

from bda.domain.models.submodels.node import Node
from bda.domain.models.submodels.boundary_conditions.spring_stiffness import SpringStiffness


@dataclass
class NodeConstraints:
    dx: bool = field(default=True)
    dy: bool = field(default=True)
    dz: bool = field(default=True)
    rx: bool = field(default=True)
    ry: bool = field(default=True)
    rz: bool = field(default=True)


@dataclass
class NodeBoundaryBase(ABC):
    node: Node

    def __hash__(self) -> int:
        return self.node.__hash__()


@dataclass
class NodeSupport(NodeBoundaryBase):
    """
    Represents a support condition applied to a node in a structural model.
    This class encapsulates the node to which the support is applied and the constraints
    that define the degrees of freedom (DOF) that are restrained.
    By default, all translational and rotational DOFs are restrained (fixed support).
    The constraints can be modified to represent different types of supports, such as pinned or roller supports.
    Attributes:
        node (Node): The node to which the support is applied.
        constraints (NodeConstraints): The constraints defining the restrained DOFs.
    """
    constraints: NodeConstraints =field(default_factory=NodeConstraints)

    def __hash__(self) -> int:
        return super().__hash__()

@dataclass
class NodeSpring(NodeBoundaryBase):
    """
    Represents a spring support condition applied to a node in a structural model.
    This class encapsulates the node to which the spring is applied and the stiffness values
    for each degree of freedom (DOF) that the spring affects.
    Attributes:
        node (Node): The node to which the spring is applied.
        spring_stiffness (SpringStiffness): The stiffness values for each DOF of the spring support.
    """
    spring_stiffness: SpringStiffness

    def __hash__(self) -> int:
        return super().__hash__()