from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import numpy as np
from pint.registry import Quantity

from bda.domain.models.submodels import Node
from bda.modules_pre.m3_geometry.helpers.tools.models.unit_vector import UnitVector

if TYPE_CHECKING:
    from bda.modules_pre.m3_geometry.helpers.tools.models.point import Point


@dataclass(frozen=True)
class Vector:
    """Immutable 3D vector represented by pint length quantities.

    The vector is used as a displacement/direction carrier in geometry helpers.
    Components are expected to be length-compatible quantities.
    """
    x: Quantity
    y: Quantity
    z: Quantity

    @classmethod
    def from_points(cls, n1: Point, n2: Point) -> Vector:
        """Build a vector from point ``n1`` to point ``n2`` (n2 - n1)."""
        return cls(
            n2.x - n1.x,
            n2.y - n1.y,
            n2.z - n1.z,)

    @classmethod
    def from_nodes(cls, n1: Node, n2: Node) -> Vector:
        """Build a vector from Node ``n1`` to Node ``n2`` (n2 - n1)."""
        return cls(
            n2.X - n1.X,
            n2.Y - n1.Y,
            n2.Z - n1.Z,
        )

    @classmethod
    def from_unit_vector_and_length(cls, vector: UnitVector, length: Quantity) -> Vector:
        """Build a vector from unit vector ``vector`` and length ``length``."""
        return cls(
            cast(Quantity, vector.x * length),
            cast(Quantity, vector.y * length),
            cast(Quantity, vector.z * length),
        )

    @classmethod
    def from_angle(cls, angle: Quantity) -> Vector:
        """
        Create XY unit vector from an angle measured from +Y axis.

        Positive rotation is clockwise. Z component is always zero.

        Parameters
        ----------
        angle:
            Angular quantity, e.g. ``30 * ureg.degree``.
        """

        # convert to radians (dimensionless float)
        angle_rad = angle.to("radian").magnitude
        meter = cast(Quantity, 1.0 * angle.to("radian")._REGISTRY.meter)

        # since angle is measured from Y axis:
        # x = sin(angle)
        # y = cos(angle)
        x = cast(Quantity, math.sin(angle_rad) * meter)
        y = cast(Quantity, math.cos(angle_rad) * meter)
        z = cast(Quantity, 0.0 * meter)

        return cls(x, y, z)

    def length(self) -> Quantity:
        """Return Euclidean vector norm as a length quantity."""
        return float(np.linalg.norm([
            self.x.to("meters").magnitude,
            self.y.to("meters").magnitude,
            self.z.to("meters").magnitude,
        ])) * self.x.to("meters").units

    def normalize(self) -> UnitVector:
        """
        Normalize vector to unit length.

        Returns
        -------
        UnitVector
            New normalized vector instance.

        Raises
        ------
        ValueError
            If the vector has zero length.
        """
        return UnitVector.from_components(
            self.x.to("meters").magnitude,
            self.y.to("meters").magnitude,
            self.z.to("meters").magnitude,
        )

    def perpendicular(self) -> Vector:
        """
        Return vector rotated by +90 degrees clockwise in XY plane.

        Z component remains unchanged.
        """
        norm = self.length()
        if norm.to("meters").magnitude == 0.0:
            return Vector(self.y, -self.x, self.z)

        perpendicular_unit = self.normalize().perpendicular()

        return Vector(
            cast(Quantity, perpendicular_unit.x * norm),
            cast(Quantity, perpendicular_unit.y * norm),
            cast(Quantity, perpendicular_unit.z * norm),
        )

    def rotate(self, angle: Quantity) -> Vector:
        """
        Rotate vector by the provided angle in XY plane.

        Angle is defined relative to +Y axis with clockwise-positive
        orientation (same convention as :meth:`from_angle`).
        """
        norm = self.length()
        if norm.to("meters").magnitude == 0.0:
            return Vector(self.x, self.y, self.z)

        rotated_unit = self.normalize().rotate(angle.to("radian").magnitude)

        return Vector(
            cast(Quantity, rotated_unit.x * norm),
            cast(Quantity, rotated_unit.y * norm),
            cast(Quantity, rotated_unit.z * norm),
        )

    def to_array(self):
        """Return vector components as ``numpy.ndarray`` with object dtype."""
        return np.array([self.x, self.y, self.z], dtype=object)

    def dot(self, other: Vector) -> Quantity:
        """Returns the dot product of two vectors."""
        return (
                self.x * other.x
                + self.y * other.y
                + self.z * other.z
        )
