"""Loads - container of load cases and FE-level loads owned by the multimodel.

NOTE: do not add ``from __future__ import annotations`` to modules in this
package (see ``load_components.py``).
"""
from dataclasses import dataclass, field
from typing import Callable, Iterable, Iterator, List, NoReturn, Sequence, cast
from uuid import UUID

from bda.domain.models.submodels.element import Element1D
from bda.domain.models.submodels.loads.line_loads import BeamLineLoad
from bda.domain.models.submodels.loads.load_base import AreaLoadElementBase, LineLoadElementBase, LoadElementBase, \
    PointLoadElementBase, LoadBase
from bda.domain.models.submodels.loads.load_case import LoadCase
from bda.domain.models.submodels.loads.load_self_weight import SelfWeightLoad
from bda.domain.models.submodels.loads.load_thermal import ThermalLoadElementBase
from bda.domain.models.submodels.loads.point_loads import BeamPointLoad, NodalPointLoad
from bda.domain.models.submodels.node import Node


@dataclass
class StaticLoads:
    """Container for load cases and loads of an ``AnalyticalMultiModel``.

    Follows the ``AnalyticalTypology`` pattern: private lists, read-only tuple
    views and explicit ``add_*`` mutators. The container owns id assignment:
    ``LoadCase.model_id`` and ``LoadBase.load_id`` are set on registration and
    each form a single increasing sequence (``load_id`` is shared across point,
    line and area loads).

    Rules enforced on registration:
        - load case names are unique (exact, case-sensitive match),
        - a load may only be added if its load case is already registered,
        - objects are deduplicated by ``guid``.

    The container does not verify that a load's node/element belongs to the
    multimodel's geometry; it has no knowledge of the topology.
    """

    _load_cases: List[LoadCase] = field(default_factory=list)
    _point_loads: List[PointLoadElementBase] = field(default_factory=list)
    _line_loads: List[LineLoadElementBase] = field(default_factory=list)
    _area_loads: List[AreaLoadElementBase] = field(default_factory=list)
    _thermal_loads: List[ThermalLoadElementBase] = field(default_factory=list)
    _self_weight_loads: List[SelfWeightLoad] = field(default_factory=list)

    _load_case_id_counter: int = field(default=1, init=False, repr=False)

    #
    # PROPERTIES
    #
    @property
    def load_cases_by_name(self) -> dict[str, LoadCase]:
        """Return a read-only dict mapping load case names to load cases."""
        return {
            lc.name.casefold(): lc
            for lc in self._load_cases
        }

    @property
    def load_cases_by_guid(self) -> dict[UUID, LoadCase]:
        """Return a read-only dict mapping load case GUIDs to load cases."""
        return {
            lc.guid: lc
            for lc in self._load_cases
        }

    @property
    def load_cases(self) -> Sequence[LoadCase]:
        """Return all registered load cases as a read-only tuple view."""
        return tuple(self._load_cases)

    @property
    def point_loads(self) -> Sequence[PointLoadElementBase]:
        """Return all registered point loads as a read-only tuple view."""
        return tuple(self._point_loads)

    @property
    def line_loads(self) -> Sequence[LineLoadElementBase]:
        """Return all registered line loads as a read-only tuple view."""
        return tuple(self._line_loads)

    @property
    def area_loads(self) -> Sequence[AreaLoadElementBase]:
        """Return all registered area loads as a read-only tuple view."""
        return tuple(self._area_loads)

    @property
    def thermal_loads(self) -> Sequence[ThermalLoadElementBase]:
        """Return all registered thermal loads as a read-only tuple view."""
        return tuple(self._thermal_loads)

    @property
    def self_weight_loads(self) -> List[SelfWeightLoad]:
        """Return all registered self-weight loads as a read-only tuple view."""
        return list(self._self_weight_loads)

    @property
    def loads(self) -> Sequence[LoadBase]:
        """All registered loads: point, then line, then area, then thermal loads."""
        return tuple(
            self._point_loads +
            self._line_loads +
            self._area_loads +
            self._thermal_loads +
            self._self_weight_loads
        )

    def __repr__(self) -> str:
        return (f"Loads[{len(self._load_cases)} load cases, {len(self._point_loads)} point, "
                f"{len(self._line_loads)} line, {len(self._area_loads)} area loads]")
    #
    #   load cases
    #

    def add_load_case(self, load_case: LoadCase) -> LoadCase:
        """Register a load case, assign its ``model_id``, and return it."""
        if not isinstance(load_case, LoadCase):
            raise TypeError(f"Expected LoadCase, got {type(load_case).__name__}.")
        if load_case.guid in self.load_cases_by_guid:
            raise ValueError(f"Load case with guid {load_case.guid} and name '{load_case.name}' "
                             f"already exists in the loads container.")
        if load_case.name.casefold() in self.load_cases_by_name:
            raise ValueError(f"Load case with name '{load_case.name}' already exists in the loads container. "
                             f"Load case names must be unique.")

        load_case.set_id(self._load_case_id_counter)
        self._load_case_id_counter += 1

        self._load_cases.append(load_case)

        return load_case

    def add_load_cases(self, load_cases: Iterable[LoadCase]) -> None:
        """Register multiple load cases in order."""
        for load_case in load_cases:
            self.add_load_case(load_case)

    def has_load_case(self, name: str) -> bool:
        """Return ``True`` if a load case with the given name exists."""
        return name.casefold() in self.load_cases_by_name

    def get_load_case(self, name: str) -> LoadCase:
        """Return the load case with the given name or raise ``KeyError``."""
        try:
            return self.load_cases_by_name[name.casefold()]
        except KeyError:
            available = ", ".join(f"'{lc.name}'" for lc in self._load_cases) or "<none>"
            raise KeyError(f"Load case '{name}' not found. Available load cases: {available}.") from None

    #
    #   loads
    #
    def add_load(self, load: LoadBase) -> LoadBase:
        """Register a supported load by dispatching to the matching add method."""
        if isinstance(load, PointLoadElementBase):
            return self.add_point_load(load)
        if isinstance(load, LineLoadElementBase):
            return self.add_line_load(load)
        if isinstance(load, AreaLoadElementBase):
            return self.add_area_load(load)
        if isinstance(load, ThermalLoadElementBase):
            return self.add_thermal_load(load)
        if isinstance(load, SelfWeightLoad):
            return self.add_self_weight_load(load)
        raise TypeError(f"Unsupported load type: {type(load).__name__}.")

    def add_loads(self, loads: Iterable[LoadElementBase]) -> None:
        """Register multiple loads in order."""
        for load in loads:
            self.add_load(load)

    def add_point_load(self, load: PointLoadElementBase) -> PointLoadElementBase:
        """Register a point load and return it."""
        if not isinstance(load, PointLoadElementBase):
            raise TypeError(f"Expected a point load (PointLoadBase), got {type(load).__name__}.")
        return self._register_load(load, self._point_loads)

    def add_line_load(self, load: LineLoadElementBase) -> LineLoadElementBase:
        """Register a line load and return it."""
        if not isinstance(load, LineLoadElementBase):
            raise TypeError(f"Expected a line load (LineLoadBase), got {type(load).__name__}.")
        return self._register_load(load, self._line_loads)

    def add_area_load(self, load: AreaLoadElementBase) -> NoReturn:
        """Reject area loads because panel elements are not implemented yet."""
        raise NotImplementedError("Area (panel) loads are not supported yet.")

    def add_thermal_load(self, load: ThermalLoadElementBase) -> ThermalLoadElementBase:
        """Register a thermal load and return it."""
        if not isinstance(load, ThermalLoadElementBase):
            raise TypeError(f"Expected a thermal load (ThermalLoadBase), got {type(load).__name__}.")
        return self._register_load(load, self._thermal_loads)

    def add_self_weight_load(self, load: SelfWeightLoad) -> SelfWeightLoad:
        """Register a self-weight load and return it."""
        if not isinstance(load, SelfWeightLoad):
            raise TypeError(f"Expected a self-weight load (SelfWeightLoad), got {type(load).__name__}.")
        return self._register_load(load, self._self_weight_loads)

    def _register_load(self, load: LoadBase, collection: list[LoadBase]) -> LoadBase:
        """Validate, assign an id to, and store a load in the target collection."""
        registered_case = next((lc for lc in self._load_cases if lc.guid == load.load_case.guid), None)
        if registered_case is None:
            raise ValueError(f"Load case '{load.load_case.name}' ({load.load_case.guid}) is not registered "
                             f"in the loads container. Call add_load_case first.")
        if any(existing.guid == load.guid for existing in self.loads):
            raise ValueError(f"Load with guid {load.guid} already exists in the loads container.")

        load.set_id(self._next_load_id())
        collection.append(load)
        return load

    def _next_load_id(self) -> int:
        """Return the next sequential load id across all registered loads."""
        return max((load.load_id for load in self.loads), default=0) + 1

    #
    #   queries
    #
    def iter_loads(self, predicate: Callable[[LoadBase], bool] | None = None) -> Iterator[LoadBase]:
        """Yield all loads, optionally filtered by ``predicate``."""
        for load in self.loads:
            if predicate is None or predicate(load):
                yield load

    def get_loads_by_load_case(self, load_case: LoadCase | str) -> List[LoadBase]:
        """Return all loads assigned to the given load case.

        The load case may be provided either as a ``LoadCase`` instance or as
        its name.
        """
        if isinstance(load_case, str):
            load_case = self.get_load_case(load_case)
        if not isinstance(load_case, LoadCase):
            raise TypeError(f"Expected a load case (str), got {type(load_case).__name__}.")
        return [load for load in self.loads if load.load_case.guid == load_case.guid]

    def get_loads_for_node(self, node: Node) -> List[NodalPointLoad]:
        """Return all nodal point loads attached to the given node."""
        return cast(List[NodalPointLoad], [load for load in self._point_loads
                                            if isinstance(load, NodalPointLoad) and load.node.uid == node.uid])

    def get_loads_for_element(self, element: Element1D) -> List[BeamPointLoad | BeamLineLoad]:
        """Return all beam loads attached to the given element."""
        return cast(List[BeamPointLoad | BeamLineLoad], [load for load in self.loads
                                                         if isinstance(load, (BeamPointLoad, BeamLineLoad))
                                                         and load.element.uid == element.uid])
