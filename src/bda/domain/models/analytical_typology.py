from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Sequence, List, Dict

from bda.domain.models.submodels.boundary_conditions.beam_end_release import BeamEndRelease
from bda.domain.models.submodels.boundary_conditions.supports import NodeBoundaryBase
from bda.domain.models.submodels.element import Element, ElementLink
from bda.domain.models.submodels.node import Node

@dataclass(frozen=True, slots=True)
class BearingKey:
    girder_id: int
    bearing_id: int

@dataclass(slots=True)
class BearingNodes:
    node_top: Node
    node_bottom: Node | None

@dataclass
class AnalyticalTypology:
    """Container for analytical-model references assigned to a geometry group.

    Holds FE topology objects that are generated and consumed across PRE/POST
    pipelines. The object is intentionally focused on storage + simple mutation
    so ``GeometryGroup`` can keep hierarchy/domain responsibilities.

    Note:
        Constraints will be added here in a future iteration.
    """

    _elements: List[Element] = field(default_factory=list)
    _links: List[ElementLink] = field(default_factory=list)
    _bearing_nodes: Dict[BearingKey, BearingNodes] = field(default_factory=defaultdict)
    _beam_end_releases: List[BeamEndRelease] = field(default_factory=list)
    _supports: List[NodeBoundaryBase] = field(default_factory=list)

    @property
    def elements(self) -> Sequence[Element]:
        return tuple(self._elements)

    @property
    def links(self) -> Sequence[ElementLink]:
        return tuple(self._links)

    @property
    def bearing_nodes(self) -> Dict[BearingKey, BearingNodes]:
        return self._bearing_nodes

    @property
    def beam_end_releases(self) -> Sequence[BeamEndRelease]:
        return tuple(self._beam_end_releases)

    @property
    def supports(self) -> Sequence[NodeBoundaryBase]:
        return tuple(self._supports)

    def _add_support(self, support: NodeBoundaryBase) -> None:
        self._supports.append(support)

    def _add_supports(self, supports: Iterable[NodeBoundaryBase]) -> None:
        for support in supports:
            self._add_support(support)

    def _add_element(self, element: Element) -> None:
        self._elements.append(element)

    def _add(self, element: Element) -> None:
        """Route an element to the correct collection by its concrete type."""
        if isinstance(element, ElementLink):
            self._add_link(element)
        else:
            self._add_element(element)

    def _add_elements(self, elements: Iterable[Element]) -> None:
        for element in elements:
            self._add(element)

    def _add_bearing_nodes(self,
                           girder_index: int,
                           bearing_index: int,
                           node_start: Node,
                           node_end: Node | None = None) -> None:
        self._bearing_nodes[BearingKey(girder_index, bearing_index)] = BearingNodes(node_start, node_end)

    def _add_link(self, link: ElementLink) -> None:
        self._links.append(link)

    def _add_links(self, links: Iterable[ElementLink]) -> None:
        for link in links:
            self._add_link(link)

    def _add_beam_end_release(self, beam_end_release: BeamEndRelease) -> None:
        self._beam_end_releases.append(beam_end_release)

    def _add_beam_end_releases(self, beam_end_releases: Iterable[BeamEndRelease]) -> None:
        for beam_end_release in beam_end_releases:
            self._beam_end_releases.append(beam_end_release)

    def _update_bearing_nodes(
            self,
            key: BearingKey,
            node_start: Node | None = None,
            node_end: Node | None = None,
    ) -> None:
        """Updates the start and/or end node of an existing bearing."""

        try:
            current_nodes = self._bearing_nodes[key]
        except KeyError as exc:
            raise KeyError(
                f"Bearing nodes for index [girder_index, bearing_index] {key} not found."
            ) from exc

        self._bearing_nodes[key] = BearingNodes(
            node_top=node_start if node_start is not None else current_nodes.node_top,
            node_bottom=node_end if node_end is not None else current_nodes.node_bottom,
        )