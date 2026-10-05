import pytest

from bda.domain.units import registry as units
from bda.modules_pre.m3_geometry.helpers.tools.models import AppliedVector
from bda.modules_pre.m3_geometry.helpers.tools.models import Point
from bda.modules_pre.m3_geometry.helpers.tools.models import Vector


def test_from_points_uses_start_and_end_points_to_define_vector():
    start = Point(1 * units.m, 2 * units.m, 0 * units.m)
    end = Point(4 * units.m, 6 * units.m, 1 * units.m)

    applied = AppliedVector.from_points(start, end)

    assert applied.start_point == start
    assert applied.vector.x.to(units.m).magnitude == pytest.approx(3.0)
    assert applied.vector.y.to(units.m).magnitude == pytest.approx(4.0)
    assert applied.vector.z.to(units.m).magnitude == pytest.approx(1.0)


def test_end_point_adds_vector_to_start_point():
    applied = AppliedVector(
        start_point=Point(1 * units.m, 2 * units.m, 3 * units.m),
        vector=Vector(2 * units.m, -1 * units.m, 0.5 * units.m),
    )

    end = applied.end_point

    assert end.x.to(units.m).magnitude == pytest.approx(3.0)
    assert end.y.to(units.m).magnitude == pytest.approx(1.0)
    assert end.z.to(units.m).magnitude == pytest.approx(3.5)

