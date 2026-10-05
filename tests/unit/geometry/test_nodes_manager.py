import pytest

from bda.domain.units import registry as units
from bda.domain.managers import NodesManager


def test_normalize_tolerance_m_accepts_positive_float():
    tol_m = NodesManager._normalize_tolerance_m(0.001)

    assert tol_m == pytest.approx(0.001)


def test_normalize_tolerance_m_accepts_length_quantity():
    tol_m = NodesManager._normalize_tolerance_m(1.0 * units.mm)

    assert tol_m == pytest.approx(0.001)


def test_normalize_tolerance_m_rejects_non_length_quantity():
    with pytest.raises(ValueError, match="length quantity"):
        NodesManager._normalize_tolerance_m(1.0 * units.kN)


def test_normalize_tolerance_m_rejects_non_positive_value():
    with pytest.raises(ValueError, match="greater than zero"):
        NodesManager._normalize_tolerance_m(0.0)


def test_as_meters_converts_quantity_and_float_values():
    assert NodesManager._as_meters(250.0 * units.cm) == pytest.approx(2.5)
    assert NodesManager._as_meters(2.5) == pytest.approx(2.5)


def test_key_uses_tolerance_grid_in_meters():
    model = NodesManager(tol=1.0 * units.mm)

    key = model._key(1000.0 * units.mm, 2.0 * units.m, 0.0 * units.m)

    assert key == (1000, 2000, 0)


def test_get_or_create_node_reuses_existing_node_for_same_location():
    model = NodesManager(tol=0.1 * units.mm)

    n1 = model.get_or_create_node(1.0 * units.m, 2.0 * units.m)
    n2 = model.get_or_create_node(1000.0 * units.mm, 2000.0 * units.mm, 0.0 * units.m)

    assert n1 is n2
    assert len(model.nodes) == 1


def test_get_or_create_node_defaults_z_to_zero_and_stores_meter_values():
    model = NodesManager()

    node = model.get_or_create_node(1.0 * units.m, 2.0 * units.m)

    assert node.Z.to(units.m).magnitude == pytest.approx(0.0)
    assert node.X.to(units.m).magnitude == pytest.approx(1.0)
    assert node.Y.to(units.m).magnitude == pytest.approx(2.0)


def test_get_or_create_node_assigns_incremental_node_ids():
    model = NodesManager()
    n1 = model.get_or_create_node(0.0 * units.m, 0.0 * units.m, 0.0 * units.m)
    n2 = model.get_or_create_node(1.0 * units.m, 0.0 * units.m, 0.0 * units.m)

    assert n1.node_id == 1
    assert n2.node_id == 2
    assert len(model.nodes) == 2


def test_get_or_create_node_accepts_length_quantity_coordinates():
    model = NodesManager(tol=1e-6)

    node = model.get_or_create_node(1.25 * units.m, 250.0 * units.cm, 0.0 * units.m)

    assert node.X.to(units.m).magnitude == pytest.approx(1.25)
    assert node.Y.to(units.m).magnitude == pytest.approx(2.5)
    assert node.Z.to(units.m).magnitude == pytest.approx(0.0)


def test_get_or_create_node_defaults_z_to_zero_for_length_inputs():
    model = NodesManager(tol=1e-6)

    node = model.get_or_create_node(3000.0 * units.mm, 4.0 * units.m)

    assert node.Z.to(units.m).magnitude == pytest.approx(0.0)


