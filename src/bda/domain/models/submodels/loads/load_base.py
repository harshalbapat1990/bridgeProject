"""Abstract base classes for FE-level loads.

NOTE: do not add ``from __future__ import annotations`` to modules in this
package. Postponed annotations turn ``Annotated[...]`` field types into
strings and silently disable ``validate_pint_fields`` dimension checks.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import cast
from uuid import UUID, uuid4

from bda.domain.base import MultiModelObjectBase
from bda.domain.enums.load_enums import CoordinateSystem, LoadDistribution, LoadTargetType, LoadType
from bda.domain.models.submodels.element import Element1D
from bda.domain.models.submodels.loads.load_case import LoadCase
from bda.domain.models.submodels.loads.load_components import LineLoadComponents, PointLoadComponents
from bda.domain.models.submodels.node import Node

@dataclass(kw_only=True, eq=False, repr=False)
class LoadBase(MultiModelObjectBase, ABC):
    """Common identity, metadata, and validation shared by all FE-level loads.

    This abstract base class stores the load identifier, the owning load case,
    optional descriptive metadata, and cross-cutting validation rules that
    apply to every concrete load type.
    """

    guid: UUID = field(default_factory=uuid4)
    _load_id: int = field(default=0, init=False)
    load_case: LoadCase
    coordinate_system: CoordinateSystem = CoordinateSystem.GLOBAL
    name: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.load_case, LoadCase):
            raise TypeError(f"load_case must be a LoadCase instance, got {type(self.load_case).__name__}.")
        if self.coordinate_system is not CoordinateSystem.GLOBAL:
            raise NotImplementedError(
                f"Coordinate system '{self.coordinate_system}' is not supported; only GLOBAL is implemented.")

    @property
    @abstractmethod
    def target(self) -> Node | Element1D:  # to be extended for area loadings in future implementations
        """Return the analytical object this load acts on."""

    def set_id(self, load_id: int) -> None:
        """Assign the sequential container-specific identifier of the load."""
        if type(load_id) is not int:
            raise TypeError(f"load_id must be int, got {type(load_id).__name__}.")
        if load_id < 0:
            raise ValueError(f"load_id must be non-negative, got {load_id!r}.")
        self._load_id = load_id

    @property
    def load_id(self) -> int:
        """Return the sequential container-specific identifier of the load."""
        return self._load_id

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}[id: {self.load_id}, "
                f"case: '{self.load_case.name}', target: {self.target!r}]")

    def __hash__(self) -> int:
        return hash(self.guid)

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return NotImplemented
        other_load = cast(LoadBase, other)
        return self.guid == other_load.guid


@dataclass(kw_only=True, eq=False, repr=False)
class LoadElementBase(LoadBase, ABC):
    """Abstract base for loads applied to finite elements or related targets.

    Subclasses define the geometric load type and the type of analytical
    target they can be attached to.
    """

    load_type: LoadType = field(init=False)
    target_type: LoadTargetType = field(init=False)


@dataclass(kw_only=True, repr=False, eq=False)
class PointLoadElementBase(LoadElementBase, ABC):
    """Abstract base for concentrated loads applied at a single location.

    The load components represent forces and moments resolved in the selected
    coordinate system.
    """

    load_type: LoadType = field(default=LoadType.POINT, init=False)
    components: PointLoadComponents = field(default_factory=PointLoadComponents)

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.components, PointLoadComponents):
            raise TypeError(
                f"components must be PointLoadComponents, got {type(self.components).__name__}.")


@dataclass(kw_only=True, repr=False, eq=False)
class LineLoadElementBase(LoadElementBase, ABC):
    """Abstract base for loads distributed along a one-dimensional element.

    The stored components are expressed per unit length. Only uniform line
    distributions are currently supported.
    """

    load_type: LoadType = field(default=LoadType.LINE, init=False)
    distribution: LoadDistribution = LoadDistribution.UNIFORM
    components: LineLoadComponents = field(default_factory=LineLoadComponents)

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.components, LineLoadComponents):
            raise TypeError(
                f"components must be LineLoadComponents, got {type(self.components).__name__}.")
        if self.distribution is not LoadDistribution.UNIFORM:
            raise NotImplementedError(
                f"Load distribution '{self.distribution}' is not supported; only UNIFORM is implemented.")


@dataclass(kw_only=True, repr=False, eq=False)
class AreaLoadElementBase(LoadElementBase, ABC):
    """Placeholder for loads distributed over a panel (plate) element surface.

    Panel elements are not implemented yet. This class reserves the extension
    point so that load containers and exporters can already account for future
    area-load support.
    """

    load_type: LoadType = field(default=LoadType.AREA, init=False)
    target_type: LoadTargetType = field(default=LoadTargetType.PANEL, init=False)
