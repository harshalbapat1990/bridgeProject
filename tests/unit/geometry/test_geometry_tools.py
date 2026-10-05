import pytest

from bda.domain.units import registry as units
from bda.modules_pre.m3_geometry.helpers.tools.geometry_tools import GeometryTools
from bda.modules_pre.m3_geometry.helpers.tools.models import AppliedVector
from bda.modules_pre.m3_geometry.helpers.tools.models import Point
from bda.modules_pre.m3_geometry.helpers.tools.models import Vector


def test_intersect_lines_returns_intersection_point_for_crossing_lines():
    line_1 = AppliedVector(
        start_point=Point(0 * units.m, 0 * units.m, 0 * units.m),
        vector=Vector(1 * units.m, 0 * units.m, 0 * units.m),
    )
    line_2 = AppliedVector(
        start_point=Point(1 * units.m, -1 * units.m, 0 * units.m),
        vector=Vector(0 * units.m, 1 * units.m, 0 * units.m),
    )

    intersection = GeometryTools.intersect_lines(line_1, line_2, tol=1e-9 * units.m)

    assert intersection is not None
    assert intersection.x.to(units.m).magnitude == pytest.approx(1.0)
    assert intersection.y.to(units.m).magnitude == pytest.approx(0.0)
    assert intersection.z.to(units.m).magnitude == pytest.approx(0.0)


def test_intersect_lines_returns_none_for_parallel_lines():
    line_1 = AppliedVector(
        start_point=Point(0 * units.m, 0 * units.m, 0 * units.m),
        vector=Vector(1 * units.m, 0 * units.m, 0 * units.m),
    )
    line_2 = AppliedVector(
        start_point=Point(0 * units.m, 1 * units.m, 0 * units.m),
        vector=Vector(1 * units.m, 0 * units.m, 0 * units.m),
    )

    intersection = GeometryTools.intersect_lines(line_1, line_2, tol=1e-9 * units.m)

    assert intersection is None


def test_intersect_lines_returns_none_for_skew_lines_outside_tolerance():
    line_1 = AppliedVector(
        start_point=Point(0 * units.m, 0 * units.m, 0 * units.m),
        vector=Vector(1 * units.m, 0 * units.m, 0 * units.m),
    )
    line_2 = AppliedVector(
        start_point=Point(0 * units.m, 1 * units.m, 1 * units.m),
        vector=Vector(0 * units.m, 1 * units.m, 0 * units.m),
    )

    intersection = GeometryTools.intersect_lines(line_1, line_2, tol=1e-6 * units.m)

    assert intersection is None


def test_intersect_segments_returns_intersection_point_when_inside_both_segments():
    segment_1 = AppliedVector(
        start_point=Point(0 * units.m, 0 * units.m, 0 * units.m),
        vector=Vector(2 * units.m, 0 * units.m, 0 * units.m),
    )
    segment_2 = AppliedVector(
        start_point=Point(1 * units.m, -1 * units.m, 0 * units.m),
        vector=Vector(0 * units.m, 2 * units.m, 0 * units.m),
    )

    intersection = GeometryTools.intersect_segments(segment_1, segment_2, tol=1e-9 * units.m)

    assert intersection is not None
    assert intersection.x.to(units.m).magnitude == pytest.approx(1.0)
    assert intersection.y.to(units.m).magnitude == pytest.approx(0.0)
    assert intersection.z.to(units.m).magnitude == pytest.approx(0.0)


def test_intersect_segments_returns_none_when_intersection_is_outside_segment_length():
    segment_1 = AppliedVector(
        start_point=Point(0 * units.m, 0 * units.m, 0 * units.m),
        vector=Vector(0.5 * units.m, 0 * units.m, 0 * units.m),
    )
    segment_2 = AppliedVector(
        start_point=Point(1 * units.m, -1 * units.m, 0 * units.m),
        vector=Vector(0 * units.m, 2 * units.m, 0 * units.m),
    )

    intersection = GeometryTools.intersect_segments(segment_1, segment_2, tol=1e-9 * units.m)

    assert intersection is None


def test_project_node_on_segment_returns_intersection_for_line_and_segment():
    line = AppliedVector(
        start_point=Point(0 * units.m, 0 * units.m, 0 * units.m),
        vector=Vector(1 * units.m, 0 * units.m, 0 * units.m),
    )
    segment = AppliedVector(
        start_point=Point(1 * units.m, -1 * units.m, 0 * units.m),
        vector=Vector(0 * units.m, 2 * units.m, 0 * units.m),
    )

    intersection = GeometryTools.project_node_on_segment(line, segment, tol=1e-9 * units.m)

    assert intersection is not None
    assert intersection.x.to(units.m).magnitude == pytest.approx(1.0)
    assert intersection.y.to(units.m).magnitude == pytest.approx(0.0)
    assert intersection.z.to(units.m).magnitude == pytest.approx(0.0)


def test_project_node_on_segment_returns_none_when_hit_is_outside_segment_length():
    line = AppliedVector(
        start_point=Point(0 * units.m, 0 * units.m, 0 * units.m),
        vector=Vector(1 * units.m, 0 * units.m, 0 * units.m),
    )
    segment = AppliedVector(
        start_point=Point(1 * units.m, 1 * units.m, 0 * units.m),
        vector=Vector(0 * units.m, 1 * units.m, 0 * units.m),
    )

    intersection = GeometryTools.project_node_on_segment(line, segment, tol=1e-9 * units.m)

    assert intersection is None


def test_project_node_on_segment_accepts_intersection_exactly_at_segment_endpoint():
    line = AppliedVector(
        start_point=Point(0 * units.m, 1 * units.m, 0 * units.m),
        vector=Vector(1 * units.m, 0 * units.m, 0 * units.m),
    )
    segment = AppliedVector(
        start_point=Point(1 * units.m, 0 * units.m, 0 * units.m),
        vector=Vector(0 * units.m, 1 * units.m, 0 * units.m),
    )

    intersection = GeometryTools.project_node_on_segment(line, segment, tol=1e-9 * units.m)

    assert intersection is not None
    assert intersection.x.to(units.m).magnitude == pytest.approx(1.0)
    assert intersection.y.to(units.m).magnitude == pytest.approx(1.0)
    assert intersection.z.to(units.m).magnitude == pytest.approx(0.0)


