from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class UnitVector:
    x: float
    y: float
    z: float

    @classmethod
    def from_components(cls, x: float, y: float, z: float) -> UnitVector:
        """Build a unit vector from primitive float components."""
        norm = math.sqrt(x * x + y * y + z * z)

        if norm == 0.0:
            raise ValueError("Cannot normalize zero-length vector")

        return cls(
            x / norm,
            y / norm,
            z / norm,
        )

    def to_array(self) -> np.ndarray:
        """Return vector components as ``numpy.ndarray`` with float dtype."""
        return np.array([self.x, self.y, self.z], dtype=float)

    def length(self) -> float:
        """Return Euclidean norm of unit-vector components."""
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def perpendicular(self) -> UnitVector:
        """Return vector rotated by +90 degrees clockwise in XY plane."""
        return UnitVector(self.y, -self.x, self.z)

    def rotate(self, angle_radians: float) -> UnitVector:
        """Rotate unit vector in XY plane (clockwise-positive)."""
        cos_a = math.cos(angle_radians)
        sin_a = math.sin(angle_radians)

        x_new = self.x * cos_a + self.y * sin_a
        y_new = -self.x * sin_a + self.y * cos_a

        return UnitVector(x_new, y_new, self.z)
