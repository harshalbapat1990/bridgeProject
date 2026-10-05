from dataclasses import dataclass, field
from uuid import UUID, uuid4

from bda.domain.units.quantities import Length
from bda.domain.units.registry import m


@dataclass
class Node:
    uid: UUID = field(default_factory=uuid4, init=False)

    node_id: int = field(default=None, init=False)
    X: Length
    Y: Length
    Z: Length = 0*m

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}["
            f"id: {self.node_id}, "
            f"({self.X:.3g~P}, {self.Y:.3g~P}, {self.Z:.3g~P})"
            f"]"
        )