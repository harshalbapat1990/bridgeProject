from __future__ import annotations

from typing import Dict, Tuple

from pint.registry import Quantity

from bda.domain.models.submodels.node import Node


class NodesManager:
    def __init__(
        self,
        tol: float | Quantity = 1e-5,
        node_id_start: int = 1,
    ):
        self.nodes: Dict[int, Node] = {}

        self._node_id = node_id_start

        # key: rounded coordinates in meters divided by tolerance
        self.spatial_index: Dict[Tuple[int, int, int], int] = {}
        self._tol_m = self._normalize_tolerance_m(tol)


    @staticmethod
    def _normalize_tolerance_m(tol: float | Quantity) -> float:
        if isinstance(tol, Quantity):
            if not tol.check("[length]"):
                raise ValueError("Tolerance must be a length quantity (e.g. 1e-6 * m).")
            tol_m = float(tol.to("meter").magnitude)
        else:
            tol_m = float(tol)

        if tol_m <= 0.0:
            raise ValueError("Tolerance must be greater than zero.")

        return tol_m

    @staticmethod
    def _as_meters(value: float | Quantity) -> float:
        if isinstance(value, Quantity):
            return float(value.to("meter").magnitude)
        return float(value)

    def _key(
        self,
        x: float | Quantity,
        y: float | Quantity,
        z: float | Quantity,
    ) -> Tuple[int, int, int]:
        xm = self._as_meters(x)
        ym = self._as_meters(y)
        zm = self._as_meters(z)
        return (
            round(xm / self._tol_m),
            round(ym / self._tol_m),
            round(zm / self._tol_m),
        )

    def get_or_create_node(
        self,
        x: Quantity,
        y: Quantity,
        z: Quantity | None = None,
    ) -> Node:
        if z is None:
            z = x * 0.0

        key = self._key(x, y, z)

        existing = self.spatial_index.get(key)
        if existing is not None:
            return self.nodes[existing]

        nid = self._node_id

        node = Node(
            X=x.to("meter"),
            Y=y.to("meter"),
            Z=z.to("meter"),
        )
        node.node_id = nid
        self._node_id += 1

        self.nodes[nid] = node
        self.spatial_index[key] = nid
        return node





