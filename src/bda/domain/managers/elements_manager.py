from __future__ import annotations

from typing import Dict, Tuple, TypeVar, List
from uuid import UUID

from bda.domain.models.submodels.element import (
    Element,
    Element1D,
    Element1DBase,
    LinkType,
    ElementLink,
)
from bda.domain.models.submodels.node import Node

TElement = TypeVar("TElement", bound=Element1DBase)

class ElementsManager:
    def __init__(
        self,
        element_id_start: int = 1,
    ):
        self.elements: Dict[UUID, Element] = {}

        self._elements_by_key: Dict[Tuple[UUID, ...], Element] = {}

        self._element_id = element_id_start

    @staticmethod
    def _key(
        *nodes: Node
    ) -> Tuple[UUID, ...]:
        if not 2 <= len(nodes) <= 4:
            raise ValueError("Element must be defined by 2, 3 or 4 nodes.")

        node_uids: List[UUID] = [
            node.uid for node in nodes
        ]

        if len(set(node_uids)) != len(node_uids):
            raise ValueError("Element cannot contain duplicated nodes.")

        return tuple(sorted(node_uids, key=lambda uid: uid.hex))

    def _next_element_id(self) -> int:
        element_id = self._element_id
        self._element_id += 1
        return element_id

    def _get_or_create(self, element: TElement, *nodes: Node) -> TElement:
        """Deduplicate a pre-built 1D element by its node key and assign an id.

        Nodes are expected to be canonical already (created through
        ``NodesManager``/``AnalyticalMultiModel.create_node``); this method does
        not re-canonicalize them. The returned element is the canonical instance
        and callers must use it instead of the one they passed in.
        """
        key = self._key(*nodes)

        existing = self._elements_by_key.get(key)
        if existing is not None:
            if type(existing) is not type(element):
                raise TypeError(
                    f"Connection {key} already exists as "
                    f"{type(existing).__name__}."
                )
            return existing

        if element.element_id:
            self._element_id = max(self._element_id, element.element_id + 1)
        else:
            element.set_id(self._next_element_id())

        self.elements[element.uid] = element
        self._elements_by_key[key] = element

        return element

    def get_or_create_beam(self, node_start: Node, node_end: Node) -> Element1D:
        return self._get_or_create(
            Element1D(node_start=node_start, node_end=node_end),
            node_start,
            node_end,
        )

    def get_or_create_link(self, node_start: Node, node_end: Node, link_type: LinkType) -> ElementLink:
        return self._get_or_create(
            ElementLink(node_start=node_start, node_end=node_end, link_type=link_type),
            node_start,
            node_end,
        )

    def get_or_create_plate(self, *nodes: Node) -> None:
        raise NotImplementedError("Plate elements are not implemented yet.")
