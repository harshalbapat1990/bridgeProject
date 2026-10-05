from dataclasses import dataclass

from bda.modules_pre.m3_geometry.helpers.tools.models.point import Point
from bda.modules_pre.m3_geometry.helpers.tools.models.vector import Vector
from bda.modules_pre.m3_geometry.helpers.tools.models.unit_vector import UnitVector


@dataclass(frozen=True)
class AppliedVector:
    start_point: Point
    vector: Vector

    @classmethod
    def from_points(cls, start_point: Point, end_point: Point):
        return cls(start_point, vector=Vector.from_points(start_point, end_point))

    @property
    def end_point(self) -> Point:
        return Point(
            self.start_point.x + self.vector.x,
            self.start_point.y + self.vector.y,
            self.start_point.z + self.vector.z
        )

    @property
    def unit_vector(self) -> UnitVector:
        return UnitVector.from_components(
            self.vector.x.to("meters").magnitude,
            self.vector.y.to("meters").magnitude,
            self.vector.z.to("meters").magnitude)

    def move_to(self, point: Point):
        return AppliedVector(
            point,
            self.vector,
        )

    def move_by(self, vector: Vector):
        return AppliedVector(
            self.start_point.translate(vector),
            self.vector,
        )