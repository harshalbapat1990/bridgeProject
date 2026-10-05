import pytest

from bda.domain.units import registry as units
from bda.modules_pre.m3_geometry.helpers.tools.models import Point
from bda.modules_pre.m3_geometry.helpers.tools.models import Vector
from bda.modules_pre.m3_geometry.helpers.tools.models.unit_vector import UnitVector


def test_from_points_returns_end_minus_start_components():
    start = Point(1 * units.m, 2 * units.m, 0 * units.m)
    end = Point(4 * units.m, 6 * units.m, 1 * units.m)

    vector = Vector.from_points(start, end)

    assert vector.x.to(units.m).magnitude == pytest.approx(3.0)
    assert vector.y.to(units.m).magnitude == pytest.approx(4.0)
    assert vector.z.to(units.m).magnitude == pytest.approx(1.0)


def test_from_angle_creates_unit_vector_from_positive_y_axis():
    vector = Vector.from_angle(90 * units.ureg.degree)

    assert vector.x.to(units.m).magnitude == pytest.approx(1.0)
    assert vector.y.to(units.m).magnitude == pytest.approx(0.0, abs=1e-12)
    assert vector.z.to(units.m).magnitude == pytest.approx(0.0)


def test_vector_length_returns_quantity():
    vector = Vector(3 * units.m, 4 * units.m, 0 * units.m)

    length = vector.length()

    assert length.to(units.m).magnitude == pytest.approx(5.0)


def test_normalize_uses_vector_length():
    vector = Vector(3 * units.m, 4 * units.m, 0 * units.m)

    normalized = vector.normalize()

    assert isinstance(normalized, UnitVector)
    assert normalized.length() == pytest.approx(1.0)
    assert normalized.x == pytest.approx(0.6)
    assert normalized.y == pytest.approx(0.8)
    assert normalized.z == pytest.approx(0.0)


def test_unit_vector_to_array_returns_float_components():
    unit_vector = UnitVector(0.0, 1.0, 0.0)

    arr = unit_vector.to_array()

    assert arr.shape == (3,)
    assert arr[0] == pytest.approx(0.0)
    assert arr[1] == pytest.approx(1.0)
    assert arr[2] == pytest.approx(0.0)


def test_normalize_raises_for_zero_vector():
    vector = Vector(0 * units.m, 0 * units.m, 0 * units.m)

    with pytest.raises(ValueError, match="zero-length vector"):
        vector.normalize()


def test_perpendicular_rotates_clockwise_in_xy_plane():
    vector = Vector(2 * units.m, 5 * units.m, 7 * units.m)

    perpendicular = vector.perpendicular()

    assert perpendicular.x == 5 * units.m
    assert perpendicular.y == -2 * units.m
    assert perpendicular.z == 7 * units.m


def test_unit_vector_perpendicular_rotates_clockwise_in_xy_plane():
    unit_vector = UnitVector(0.2, 0.5, 0.7)

    perpendicular = unit_vector.perpendicular()

    assert perpendicular.x == pytest.approx(0.5)
    assert perpendicular.y == pytest.approx(-0.2)
    assert perpendicular.z == pytest.approx(0.7)


def test_rotate_applies_clockwise_xy_rotation():
    vector = Vector(0 * units.m, 1 * units.m, 2 * units.m)

    rotated = vector.rotate(90 * units.ureg.degree)

    assert rotated.x.to(units.m).magnitude == pytest.approx(1.0)
    assert rotated.y.to(units.m).magnitude == pytest.approx(0.0, abs=1e-12)
    assert rotated.z.to(units.m).magnitude == pytest.approx(2.0)


def test_unit_vector_rotate_applies_clockwise_xy_rotation():
    unit_vector = UnitVector(0.0, 1.0, 0.5)

    rotated = unit_vector.rotate(90 * units.ureg.degree)

    assert rotated.x == pytest.approx(1.0)
    assert rotated.y == pytest.approx(0.0, abs=1e-12)
    assert rotated.z == pytest.approx(0.5)


def test_zero_vector_rotate_and_perpendicular_do_not_raise_and_stay_zero():
    vector = Vector(0 * units.m, 0 * units.m, 0 * units.m)

    rotated = vector.rotate(30 * units.ureg.degree)
    perpendicular = vector.perpendicular()

    assert rotated.x.to(units.m).magnitude == pytest.approx(0.0)
    assert rotated.y.to(units.m).magnitude == pytest.approx(0.0)
    assert rotated.z.to(units.m).magnitude == pytest.approx(0.0)
    assert perpendicular.x.to(units.m).magnitude == pytest.approx(0.0)
    assert perpendicular.y.to(units.m).magnitude == pytest.approx(0.0)
    assert perpendicular.z.to(units.m).magnitude == pytest.approx(0.0)


def test_to_array_returns_quantity_components():
    vector = Vector(1 * units.m, 2 * units.m, 3 * units.m)

    arr = vector.to_array()

    assert arr.shape == (3,)
    assert arr[0] == 1 * units.m
    assert arr[1] == 2 * units.m
    assert arr[2] == 3 * units.m


