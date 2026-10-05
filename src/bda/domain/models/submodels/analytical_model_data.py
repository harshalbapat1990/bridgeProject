from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

from bda.domain.models.submodels.element import Element, ElementLink
from bda.domain.models.submodels.node import Node


@dataclass
class AnalyticalTypology:
    """Container for analytical-model references assigned to a geometry group.

    Holds FE topology objects that are generated and consumed across PRE/POST
    pipelines. The object is intentionally focused on storage + simple mutation
    so ``GeometryGroup`` can keep hierarchy/domain responsibilities.

    Note:
        Constraints will be added here in a future iteration.
    """

    _free_nodes: list[Node] = field(default_factory=list)
    _elements: list[Element] = field(default_factory=list)
    _links: list[ElementLink] = field(default_factory=list)

    @property
    def free_nodes(self) -> Sequence[Node]:
        return tuple(self._free_nodes)

    @property
    def elements(self) -> Sequence[Element]:
        return tuple(self._elements)

    @property
    def links(self) -> Sequence[ElementLink]:
        return tuple(self._links)


    def add_free_node(self, node: Node) -> None:
        self._free_nodes.append(node)

    def add_free_nodes(self, nodes: Iterable[Node]) -> None:
        for node in nodes:
            self.add_free_node(node)

    def add_element(self, element: Element) -> None:
        self._elements.append(element)

    def add_elements(self, elements: Iterable[Element]) -> None:
        for element in elements:
            self.add_element(element)

    def add_link(self, link: ElementLink) -> None:
        self._links.append(link)

    def add_links(self, links: Iterable[ElementLink]) -> None:
        for link in links:
            self.add_link(link)


