import numpy as np
import pytest

from bda.domain.units import registry as units
from bda.modules_pre.m3_geometry.helpers.tools.models import Point
from bda.modules_pre.m3_geometry.helpers.tools.models import Vector


def test_point_sets_default_z_to_zero_with_same_registry():
    point = Point(5 * units.m, 2 * units.m)

    assert point.z is not None
    assert point.z.to("meter").magnitude == pytest.approx(0.0)


def test_point_to_array_returns_xyz_values():
    point = Point(1 * units.m, 2 * units.m, 3 * units.m)

    arr = point.to_array()

    assert isinstance(arr, np.ndarray)
    assert arr.shape == (3,)
    assert arr[0] == 1 * units.m
    assert arr[1] == 2 * units.m
    assert arr[2] == 3 * units.m


def test_translate_without_distance_uses_raw_vector_components():
    point = Point(1 * units.m, 2 * units.m, 3 * units.m)
    vector = Vector(2 * units.m, -1 * units.m, 0.5 * units.m)

    translated = point.translate(vector)

    assert translated.x == 3 * units.m
    assert translated.y == 1 * units.m
    assert translated.z == 3.5 * units.m


def test_translate_with_distance_moves_along_vector_direction():
    point = Point(0 * units.m, 0 * units.m, 0 * units.m)
    vector = Vector(3 * units.m, 4 * units.m, 0 * units.m)

    translated = point.translate(vector, distance=10 * units.m)

    assert translated.x.to(units.m).magnitude == pytest.approx(6.0)
    assert translated.y.to(units.m).magnitude == pytest.approx(8.0)
    assert translated.z.to(units.m).magnitude == pytest.approx(0.0)


def test_translate_with_distance_raises_for_zero_vector():
    point = Point(0 * units.m, 0 * units.m, 0 * units.m)
    vector = Vector(0 * units.m, 0 * units.m, 0 * units.m)

    with pytest.raises(ValueError, match="zero-length vector"):
        point.translate(vector, distance=1 * units.m)

