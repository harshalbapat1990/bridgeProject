from __future__ import annotations

import numpy as np
from attr import dataclass
from typing import TYPE_CHECKING, cast
from pint.registry import Quantity

if TYPE_CHECKING:
    from bda.modules_pre.m3_geometry.helpers.tools.models.vector import Vector

@dataclass
class Point:
    x: Quantity
    y: Quantity
    z: Quantity | None = None

    def __attrs_post_init__(self):
        if self.z is None:
            self.z = cast(Quantity, self.x * 0.0)

    def to_array(self):
        return np.array([self.x, self.y, self.z], dtype=object)

    def translate(self, vector: Vector, distance: Quantity | None = None):
        """
        Returns a new point translated by given vector.

        If distance is provided, vector is treated as a direction and
        translation length equals distance.
        """
        if distance is None:
            return Point(
                self.x + vector.x,
                self.y + vector.y,
                self.z + vector.z
            )

        norm = vector.length().to("meters").magnitude

        if norm == 0:
            raise ValueError("Cannot translate by distance along zero-length vector")

        distance_m = distance.to("meters")
        direction_x = vector.x.to("meters").magnitude / norm
        direction_y = vector.y.to("meters").magnitude / norm
        direction_z = vector.z.to("meters").magnitude / norm

        return Point(
            self.x + direction_x * distance_m,
            self.y + direction_y * distance_m,
            self.z + direction_z * distance_m,
        )

