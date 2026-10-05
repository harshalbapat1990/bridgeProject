from __future__ import annotations

from bda.domain.models.submodels import Node


def are_same_node(node_a: Node, node_b: Node) -> bool:
    return node_a.node_id == node_b.node_id
