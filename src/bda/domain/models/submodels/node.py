from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from bda.domain.units.quantities import Length, Angle
from bda.domain.units.registry import m, deg


@dataclass
class Node:
    uid: UUID = field(default_factory=uuid4, init=False)

    node_id: int = field(default=0, init=False)
    X: Length
    Y: Length
    Z: Length = 0*m

    rotation_angle_x: Angle | None = None
    rotation_angle_y: Angle | None = None
    rotation_angle_z: Angle | None = None

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}["
            f"id: {self.node_id}, "
            f"({self.X:.4g~P}, {self.Y:.4g~P}, {self.Z:.4g~P})"
            f"]"
        )

    def __hash__(self) -> int:
        return hash(self.uid)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Node) and self.uid == other.uid