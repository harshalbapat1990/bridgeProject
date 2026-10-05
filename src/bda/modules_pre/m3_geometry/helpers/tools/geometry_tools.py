from typing import Iterable

import numpy as np
from pint.registry import Quantity

from bda.modules_pre.m3_geometry.helpers.tools.models import Vector
from bda.modules_pre.m3_geometry.helpers.tools.models.applied_vector import AppliedVector
from bda.modules_pre.m3_geometry.helpers.tools.models.point import Point


class GeometryTools:
    _DENOM_TOL = 1e-12
    _PARAM_TOL = 1e-12

    @staticmethod
    def _extract_geometry_in_meters(v1: AppliedVector, v2: AppliedVector) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        p1 = (v1.start_point.x, v1.start_point.y, v1.start_point.z)
        p2 = (v2.start_point.x, v2.start_point.y, v2.start_point.z)
        d1 = (v1.vector.x, v1.vector.y, v1.vector.z)
        d2 = (v2.vector.x, v2.vector.y, v2.vector.z)

        # Convert all values to meters for stable numeric computation.
        p1m = np.array([coord.to("meters").magnitude for coord in p1], dtype=float)
        p2m = np.array([coord.to("meters").magnitude for coord in p2], dtype=float)
        d1m = np.array([coord.to("meters").magnitude for coord in d1], dtype=float)
        d2m = np.array([coord.to("meters").magnitude for coord in d2], dtype=float)
        return p1m, p2m, d1m, d2m

    @staticmethod
    def _closest_points_on_lines(
        v1: AppliedVector,
        v2: AppliedVector,
    ) -> tuple[float, float, np.ndarray, np.ndarray, float] | None:
        p1m, p2m, d1m, d2m = GeometryTools._extract_geometry_in_meters(v1, v2)

        r = p1m - p2m

        a = np.dot(d1m, d1m)
        b = np.dot(d1m, d2m)
        c = np.dot(d2m, d2m)
        d = np.dot(d1m, r)
        e = np.dot(d2m, r)

        denom = a * c - b * b
        if abs(denom) < GeometryTools._DENOM_TOL:
            return None

        t = (b * e - c * d) / denom
        s = (a * e - b * d) / denom

        p_on_l1 = p1m + t * d1m
        p_on_l2 = p2m + s * d2m
        dist = np.linalg.norm(p_on_l1 - p_on_l2)

        return t, s, p_on_l1, p_on_l2, dist

    @staticmethod
    def _point_from_meters(reference: AppliedVector, point_m: np.ndarray) -> Point:
        out_unit = reference.start_point.x.units
        meter_unit = reference.start_point.x.to("meters").units
        return Point(
            (point_m[0] * meter_unit).to(out_unit),
            (point_m[1] * meter_unit).to(out_unit),
            (point_m[2] * meter_unit).to(out_unit)
        )

    @staticmethod
    def _is_param_on_segment(param: float) -> bool:
        return -GeometryTools._PARAM_TOL <= param <= 1.0 + GeometryTools._PARAM_TOL

    @staticmethod
    def intersect_lines(v1: AppliedVector, v2: AppliedVector, tol: Quantity) -> Point | None:
        """
        Calculate the intersection point of two lines defined by AppliedVectors v1 and v2.
        If the lines are skew or parallel, return None.
        If the lines intersect, return the intersection point as a Point object.
        """

        closest_points = GeometryTools._closest_points_on_lines(v1, v2)
        if closest_points is None:
            return None

        _, _, p_on_l1, _, dist = closest_points
        if dist <= tol.to("meters").magnitude:
            return GeometryTools._point_from_meters(v1, p_on_l1)

        return None

    @staticmethod
    def intersect_segments(v1: AppliedVector, v2: AppliedVector, tol: Quantity) -> Point | None:
        """
        Calculate intersection for two finite segments defined by AppliedVectors v1 and v2.
        Returns point only when the closest-point intersection lies on both segment lengths.
        """

        closest_points = GeometryTools._closest_points_on_lines(v1, v2)
        if closest_points is None:
            return None

        t, s, p_on_l1, _, dist = closest_points
        if dist > tol.to("meters").magnitude:
            return None

        if not (GeometryTools._is_param_on_segment(t) and GeometryTools._is_param_on_segment(s)):
            return None

        return GeometryTools._point_from_meters(v1, p_on_l1)

    @staticmethod
    def project_node_on_segment(line: AppliedVector, segment: AppliedVector, tol: Quantity) -> Point | None:
        """
        Calculate intersection between an infinite line and a finite segment.
        Returns point only when intersection lies on the segment length.
        """

        closest_points = GeometryTools._closest_points_on_lines(line, segment)
        if closest_points is None:
            return None

        _, s, p_on_line, _, dist = closest_points
        if dist > tol.to("meters").magnitude:
            return None

        if not GeometryTools._is_param_on_segment(s):
            return None

        return GeometryTools._point_from_meters(line, p_on_line)

    @staticmethod
    def project_node_on_line_along_x_asix(line: AppliedVector, point: Point, tol: Quantity) -> Point | None:
        """
        Calculate intersection between an infinite line (provided)
        and a line parallel to x-axis going through provided point.
        """
        unit = point.x.units
        point_vector = AppliedVector(
            start_point=point,
            vector=Vector(1*unit, 0*unit, 0*unit)
        )
        return GeometryTools.intersect_lines(line, point_vector, tol=tol)

    @staticmethod
    def unique_quantity_with_tolerance(values: Iterable[Quantity], tol: Quantity) -> list[Quantity]:
        """Return sorted quantities with near-duplicates removed by tolerance.

        Values are first sorted by base-unit magnitude. A value is appended to the
        output only when its distance from the last accepted value exceeds `tol`.

        Args:
            values: Input quantities, potentially with mixed compatible units.
            tol: Tolerance used for uniqueness filtering.

        Returns:
            A sorted list of representative quantities after tolerance-based
            deduplication.
        """
        # Convert to base units for consistent comparison
        sorted_vals = sorted(values, key=lambda q: q.to_base_units().magnitude)

        result = []
        for q in sorted_vals:
            if not result:
                result.append(q)
                continue

            last = result[-1]

            # Compare in base units
            diff = abs(
                q.to_base_units().magnitude -
                last.to_base_units().magnitude
            )

            if diff > tol.to_base_units().magnitude:
                result.append(q)

        return result

    @staticmethod
    def project_point_on_line(
            line: AppliedVector,
            point: Point,
            clamp: bool = True,
    ) -> Point:
        """
        Project a point onto a line or line segment.

        Parameters
        ----------
        line : AppliedVector
            Line defined by a start point and a direction vector.
        point : Point
            Point to be projected onto the line.
        clamp : bool, optional
            If True, the projection is constrained to the line segment
            defined by the start point and the end point of the applied
            vector. If False, the projection is performed on the infinite
            line. Default is True.

        Returns
        -------
        Point
            Projected point lying on the line or line segment.

        Notes
        -----
        The projection parameter ``t`` is computed as:

            t = dot(point - start_point, direction) / dot(direction, direction)

        When ``clamp=True``, ``t`` is restricted to the range [0, 1],
        ensuring that the returned point lies on the line segment.
        """

        p0 = np.array([
            line.start_point.x.to("meters").magnitude,
            line.start_point.y.to("meters").magnitude,
            line.start_point.z.to("meters").magnitude,
        ])

        d = np.array([
            line.vector.x.to("meters").magnitude,
            line.vector.y.to("meters").magnitude,
            line.vector.z.to("meters").magnitude,
        ])

        p = np.array([
            point.x.to("meters").magnitude,
            point.y.to("meters").magnitude,
            point.z.to("meters").magnitude,
        ])

        t = np.dot(p - p0, d) / np.dot(d, d)

        # parameter t = 0.0 - 1.0 means that the projected point is on the segment, otherwise it is outside the segment
        # clamping this parameter to 0.0 - 1.0 will force the projected point to be on the segment

        if clamp:
            t = np.clip(t, 0.0, 1.0)

        p_proj = p0 + t * d

        return GeometryTools._point_from_meters(
            line,
            p_proj
        )
