"""Unit tests for FE-level loads: LoadCase, load classes and the Loads container."""
from dataclasses import fields

import pytest

from bda.domain import units
from bda.domain.enums import (
    CoordinateSystem,
    LoadDistribution,
    LoadTargetType,
    LoadType,
    LocalAxis,
    UnitSystem, OffsetReference,
)
from bda.domain.models import AnalyticalMultiModel
from bda.domain.models.submodels.element import Element1D, ElementLink, LinkType
from bda.domain.models.submodels.loads import (
    AreaLoadElementBase,
    BeamLineLoad,
    BeamPointLoad,
    LineLoadComponents,
    LoadCase,
    LoadOffset,
    NodalPointLoad,
    PointLoadComponents, Loads,
)
from bda.domain.models.submodels.loads.load_thermal import ThermalLoadGradient, GradientDefinition
from bda.domain.models.submodels.loads.static_loads import StaticLoads
from bda.domain.models.submodels.node import Node
from bda.domain.models.submodels.section_base import Offset
from bda.domain.units.registry import kN, m


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_LOAD_NATURES = [
    "DC",  # dead load of structural components and nonstructural attachments
    "DW",  # dead load of wearing surfaces and utilities
    "LL",  # vehicular live load
    "PL",  # pedestrian live load
    "BR",  # vehicular braking force
    "CE",  # vehicular centrifugal force
    "WS",  # wind load on structure
    "WL",  # wind on live load
    "TU",  # uniform temperature
    "TG",  # temperature gradient
    "EQ",  # earthquake load
    "PS",  # secondary forces from post-tensioning
    "SE",  # force effect due to settlement
    "SH",  # force effects due to shrinkage
    "CR",  # force effects due to creep
    "CS",  # construction stage loads
]


@pytest.fixture
def n1() -> Node:
    n = Node(0 * m, 0 * m)
    n.node_id = 0
    return n


@pytest.fixture
def n2() -> Node:
    n = Node(10 * m, 0 * m)
    n.node_id = 1
    return n


@pytest.fixture
def beam(n1, n2) -> Element1D:
    return Element1D(n1, n2)


@pytest.fixture
def lc() -> LoadCase:
    return LoadCase(name="DC1", load_nature="DC")


@pytest.fixture
def static_loads(lc: LoadCase) -> StaticLoads:
    container = Loads()
    container.static.add_load_case(lc)
    return container.static

@pytest.fixture
def vertical_gradient():
    """ThermalLoadGradient with 5 vertical gradient definitions."""
    ref = OffsetReference.CENTER_TOP
    return ThermalLoadGradient(
        gradient_definitions=[
            GradientDefinition(
                offset=Offset(vertical_value=0.50 * m, offset_reference=ref),
                value=10 * units.ureg.delta_degC,
            ),
            GradientDefinition(
                offset=Offset(vertical_value=0.25 * m, offset_reference=ref),
                value=15 * units.ureg.delta_degC,
            ),
            GradientDefinition(
                offset=Offset(vertical_value=0.00 * m, offset_reference=ref),
                value=30 * units.ureg.delta_degC,
            ),
            GradientDefinition(
                offset=Offset(vertical_value=-0.25 * m, offset_reference=ref),
                value=25 * units.ureg.delta_degC,
            ),
            GradientDefinition(
                offset=Offset(vertical_value=-0.50 * m, offset_reference=ref),
                value=20 * units.ureg.delta_degC,
            ),
        ]
    )


@pytest.fixture
def horizontal_gradient():
    """ThermalLoadGradient with 5 horizontal gradient definitions."""
    from bda.domain.models.submodels.loads.load_thermal import ThermalLoadGradient, GradientDefinition
    from bda.domain.models.submodels.section_base import Offset
    from bda.domain.enums import OffsetReference
    from bda.domain.units.registry import delta_degC

    ref = OffsetReference.CENTER_CENTER
    return ThermalLoadGradient(
        gradient_definitions=[
            GradientDefinition(
                offset=Offset(horizontal_value=-1.0 * m, offset_reference=ref),
                value=10 * delta_degC,
            ),
            GradientDefinition(
                offset=Offset(horizontal_value=-0.5 * m, offset_reference=ref),
                value=18 * delta_degC,
            ),
            GradientDefinition(
                offset=Offset(horizontal_value=0.0 * m, offset_reference=ref),
                value=35 * delta_degC,
            ),
            GradientDefinition(
                offset=Offset(horizontal_value=0.5 * m, offset_reference=ref),
                value=22 * delta_degC,
            ),
            GradientDefinition(
                offset=Offset(horizontal_value=1.0 * m, offset_reference=ref),
                value=15 * delta_degC,
            ),
        ]
    )

class _DummyAreaLoad(AreaLoadElementBase):
    """Concrete stand-in for a future panel load, used only to exercise the placeholder path."""

    @property
    def target(self):
        return None


# ---------------------------------------------------------------------------
# Multimodel wiring
# ---------------------------------------------------------------------------
class TestMultiModelWiring:
    def test_amm_has_empty_loads_container(self):
        amm = AnalyticalMultiModel(unit_system=UnitSystem.SI)
        assert isinstance(amm.loads, Loads)
        assert isinstance(amm.loads.static, StaticLoads)
        assert amm.loads.static.loads == ()
        assert amm.loads.static.load_cases == ()

    def test_each_amm_gets_its_own_container(self, lc):
        #TODO: this one could be deleted, as there is only one multimodel

        amm_a = AnalyticalMultiModel(unit_system=UnitSystem.SI)
        amm_b = AnalyticalMultiModel(unit_system=UnitSystem.SI)
        amm_a.loads.static.add_load_case(lc)
        assert amm_b.loads.static.load_cases == ()

    def test_enum_exports(self):
        assert {e.value for e in LoadType} == {"point", "line", "area"}
        assert {e.value for e in LoadTargetType} == {"node", "beam", "panel"}
        assert [e.value for e in LoadDistribution] == ["uniform"]
        assert {e.value for e in LocalAxis} == {"y", "z"}
        assert [e.value for e in CoordinateSystem] == ["global"]


# ---------------------------------------------------------------------------
# Load cases
# ---------------------------------------------------------------------------
class TestLoadCases:
    def test_add_load_case_assigns_incrementing_model_id(self):
        container = StaticLoads()
        cases = [container.add_load_case(LoadCase(name=f"LC{i}")) for i in range(3)]
        assert [c.model_id for c in cases] == [1, 2, 3]
        assert container.load_cases == tuple(cases)

    def test_add_load_case_duplicate_name_raises(self, static_loads):
        with pytest.raises(ValueError, match="already exists"):
            static_loads.add_load_case(LoadCase(name="DC1"))

    def test_add_load_case_duplicate_guid_raises(self, static_loads, lc):
        with pytest.raises(ValueError, match="guid"):
            static_loads.add_load_case(lc)

    def test_add_load_case_wrong_type_raises(self, static_loads):
        with pytest.raises(TypeError):
            static_loads.add_load_case("DC1")

    @pytest.mark.parametrize("name", ["", "   "])
    def test_load_case_empty_name_raises(self, name):
        with pytest.raises(ValueError):
            LoadCase(name=name)

    def test_get_load_case_and_has_load_case(self, static_loads, lc):
        # case-insensitive match
        assert static_loads.has_load_case("DC1")
        assert static_loads.has_load_case("dc1")

        assert static_loads.get_load_case("DC1") is lc
        assert static_loads.get_load_case("dc1") is lc
        assert static_loads.get_load_case("Dc1") is lc

    def test_get_load_case_missing_raises_keyerror(self, static_loads):
        with pytest.raises(KeyError, match="DC1"):
            static_loads.get_load_case("LL1")

    def test_load_case_defaults(self, lc):
        assert lc.description is None
        assert lc.load_nature == "DC"
        assert "DC1" in repr(lc)

    def test_load_case_empty_description_is_allowed(self):
        lc = LoadCase(name="DC1", description="")
        assert lc.description == ""

    def test_load_case_none_description_is_allowed(self):
        lc = LoadCase(name="DC1", description=None)
        assert lc.description is None

    def test_model_id_defaults_to_zero_unregistered(self):
        lc = LoadCase(name="DC1")
        assert lc.model_id == 0

    def test_model_id_is_read_only_property(self, lc):
        with pytest.raises(AttributeError):
            lc.model_id = 5

    def test_set_id_accepts_zero(self, lc):
        lc.set_id(0)
        assert lc.model_id == 0

    @pytest.mark.parametrize("model_id", [-1, -100])
    def test_set_id_negative_raises(self, lc, model_id):
        with pytest.raises(ValueError, match=">= 0"):
            lc.set_id(model_id)

    @pytest.mark.parametrize("model_id", [1.0, "1", None, 1.5])
    def test_set_id_wrong_type_raises(self, lc, model_id):
        with pytest.raises(TypeError, match="integer"):
            lc.set_id(model_id)

    def test_set_id_can_be_called_again_to_reassign(self, lc):
        lc.set_id(1)
        lc.set_id(2)
        assert lc.model_id == 2

    @pytest.mark.parametrize("nature", _LOAD_NATURES)
    def test_load_case_accepts_all_load_nature_values(self, nature):
        lc = LoadCase(name="LC", load_nature=nature)
        assert lc.load_nature == nature
        assert nature in repr(lc)

    def test_load_case_load_nature_none_is_allowed(self):
        lc = LoadCase(name="LC", load_nature=None)
        assert lc.load_nature is None
        assert "None" in repr(lc)


# ---------------------------------------------------------------------------
# Adding loads
# ---------------------------------------------------------------------------
class TestAddingLoads:
    def test_add_load_with_unregistered_case_raises(self, static_loads, n1):
        load = NodalPointLoad(node=n1, load_case=LoadCase(name="X"))
        with pytest.raises(ValueError, match="not registered"):
            static_loads.add_load(load)
        assert static_loads.loads == ()

    def test_load_ids_increment_across_types(self, static_loads, lc, n1, beam):
        p1 = static_loads.add_load(NodalPointLoad(node=n1, load_case=lc))
        l1 = static_loads.add_load(BeamLineLoad(element=beam, load_case=lc))
        p2 = static_loads.add_load(BeamPointLoad(element=beam, load_case=lc, relative_position=0.25))
        assert (p1.load_id, l1.load_id, p2.load_id) == (1, 2, 3)
        assert static_loads.point_loads == (p1, p2)
        assert static_loads.line_loads == (l1,)
        assert static_loads.loads == (p1, p2, l1)

    def test_add_duplicate_load_guid_raises(self, static_loads, lc, n1):
        load = static_loads.add_load(NodalPointLoad(node=n1, load_case=lc))
        with pytest.raises(ValueError, match="already exists"):
            static_loads.add_load(load)

    def test_typed_adders_reject_wrong_kind(self, static_loads, lc, n1, beam):
        with pytest.raises(TypeError):
            static_loads.add_line_load(NodalPointLoad(node=n1, load_case=lc))
        with pytest.raises(TypeError):
            static_loads.add_point_load(BeamLineLoad(element=beam, load_case=lc))
        with pytest.raises(TypeError):
            static_loads.add_load("not a load")

    def test_add_area_load_not_implemented(self, static_loads, lc):
        with pytest.raises(NotImplementedError):
            static_loads.add_area_load(_DummyAreaLoad(load_case=lc))
        with pytest.raises(NotImplementedError):
            static_loads.add_load(_DummyAreaLoad(load_case=lc))
        assert static_loads.area_loads == ()

    def test_add_loads_bulk(self, static_loads, lc, n1, beam):
        static_loads.add_loads([NodalPointLoad(node=n1, load_case=lc), BeamLineLoad(element=beam, load_case=lc)])
        assert len(static_loads.loads) == 2

    def test_views_are_immutable_tuples(self, static_loads, lc, n1):
        static_loads.add_load(NodalPointLoad(node=n1, load_case=lc))
        for view in (static_loads.load_cases, static_loads.point_loads, static_loads.line_loads, static_loads.area_loads, static_loads.loads):
            assert isinstance(view, tuple)


# ---------------------------------------------------------------------------
# Load classes
# ---------------------------------------------------------------------------
class TestPointLoads:
    def test_nodal_point_load_metadata(self, lc, n1):
        load = NodalPointLoad(node=n1, load_case=lc)
        assert load.load_type is LoadType.POINT
        assert load.target_type is LoadTargetType.NODE
        assert load.coordinate_system is CoordinateSystem.GLOBAL
        assert load.target is n1
        assert load.load_id == 0
        assert load.components.is_zero

    def test_nodal_point_load_has_no_offset(self, lc, n1):
        with pytest.raises(TypeError):
            NodalPointLoad(node=n1, load_case=lc, offset=LoadOffset(axis=LocalAxis.Z, value=0.1 * m))

    def test_nodal_point_load_requires_node(self, lc, beam):
        with pytest.raises(TypeError):
            NodalPointLoad(node=beam, load_case=lc)

    def test_load_case_must_be_load_case(self, n1):
        with pytest.raises(TypeError):
            NodalPointLoad(node=n1, load_case="DC1")

    @pytest.mark.parametrize("position", [0.0, 0.5, 1.0])
    def test_beam_point_load_valid_positions(self, lc, beam, position):
        load = BeamPointLoad(element=beam, load_case=lc, relative_position=position)
        assert load.target_type is LoadTargetType.BEAM
        assert load.target is beam
        assert load.absolute_position.to("m").magnitude == pytest.approx(10 * position)

    @pytest.mark.parametrize("position", [-0.1, 1.1, 2])
    def test_beam_point_load_position_out_of_bounds(self, lc, beam, position):
        with pytest.raises(ValueError, match=r"\[0, 1\]"):
            BeamPointLoad(element=beam, load_case=lc, relative_position=position)

    def test_beam_point_load_position_wrong_type(self, lc, beam):
        with pytest.raises(TypeError):
            BeamPointLoad(element=beam, load_case=lc, relative_position="0.5")

    def test_beam_point_load_with_offset(self, lc, beam):
        offset = LoadOffset(axis=LocalAxis.Y, value=-0.25 * m)
        load = BeamPointLoad(element=beam, load_case=lc, relative_position=0.5, offset=offset)
        assert load.offset is offset
        assert load.offset.axis is LocalAxis.Y

    def test_beam_point_load_rejects_link_element(self, lc, n1, n2):
        link = ElementLink(n1, n2, link_type=LinkType.RIGID)
        with pytest.raises(TypeError, match="Element1D"):
            BeamPointLoad(element=link, load_case=lc, relative_position=0.5)

    def test_point_load_wrong_components_type(self, lc, n1):
        with pytest.raises(TypeError):
            NodalPointLoad(node=n1, load_case=lc, components=LineLoadComponents())


class TestLineLoads:
    def test_beam_line_load_metadata(self, lc, beam):
        load = BeamLineLoad(element=beam, load_case=lc, components=LineLoadComponents(Fz=-3 * kN / m))
        assert load.load_type is LoadType.LINE
        assert load.target_type is LoadTargetType.BEAM
        assert load.distribution is LoadDistribution.UNIFORM
        assert load.target is beam
        assert load.offset is None
        assert not load.components.is_zero

    def test_beam_line_load_rejects_link_element(self, lc, n1, n2):
        link = ElementLink(n1, n2, link_type=LinkType.ELASTIC)
        with pytest.raises(TypeError, match="Element1D"):
            BeamLineLoad(element=link, load_case=lc)

    def test_line_load_wrong_components_type(self, lc, beam):
        with pytest.raises(TypeError):
            BeamLineLoad(element=beam, load_case=lc, components=PointLoadComponents())

    def test_line_load_with_offset(self, lc, beam):
        load = BeamLineLoad(element=beam, load_case=lc, offset=LoadOffset(axis=LocalAxis.Z, value=0.5 * m))
        assert load.offset.value.to("m").magnitude == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Components and dimension validation
# ---------------------------------------------------------------------------
class TestComponents:
    def test_point_components_default_zero(self):
        c = PointLoadComponents()
        assert c.is_zero
        assert all(getattr(c, n).magnitude == 0 for n in ("Fx", "Fy", "Fz", "Mx", "My", "Mz"))

    def test_point_components_are_not_shared(self):
        a, b = PointLoadComponents(), PointLoadComponents()
        assert a.Fx is not b.Fx

    def test_point_components_accept_force_and_moment(self):
        c = PointLoadComponents(Fx=1 * kN, Fz=-10 * kN, Mx=3 * kN * m)
        assert not c.is_zero
        assert c.Fz.to("N").magnitude == pytest.approx(-10_000)

    def test_point_load_rejects_force_per_length(self):
        with pytest.raises(TypeError, match=r"\[force\]"):
            PointLoadComponents(Fz=5 * kN / m)

    def test_point_load_moment_dimension(self):
        with pytest.raises(TypeError, match="Mx"):
            PointLoadComponents(Mx=3 * kN)

    def test_line_components_accept_per_length(self):
        c = LineLoadComponents(Fz=-3 * kN / m, Mx=2 * kN * m / m)
        assert c.Fz.check("[force]/[length]")

    def test_line_load_rejects_force_units(self):
        with pytest.raises(TypeError, match="Fz"):
            LineLoadComponents(Fz=5 * kN)

    def test_components_reject_plain_numbers(self):
        with pytest.raises(TypeError):
            PointLoadComponents(Fz=5.0)

    def test_offset_requires_length(self):
        with pytest.raises(TypeError, match=r"\[length\]"):
            LoadOffset(axis=LocalAxis.Z, value=2 * kN)

    def test_offset_requires_local_axis(self):
        with pytest.raises(TypeError):
            LoadOffset(axis="z", value=1 * m)

    def test_annotations_are_not_strings(self):
        """Guard: `from __future__ import annotations` would turn field types into strings
        and silently disable pint dimension validation in validate_pint_fields."""
        for cls in (PointLoadComponents, LineLoadComponents, LoadOffset):
            assert all(not isinstance(f.type, str) for f in fields(cls)), cls.__name__

# ---------------------------------------------------------------------------
# Thermal loads
# ---------------------------------------------------------------------------

class TestThermalGradient:
    """Tests for thermal load gradients and components."""

    def test_vertical_gradient_vertical_profile(self, vertical_gradient):
        """Vertical gradient returns sorted vertical profiles."""
        z_coords, t_values = vertical_gradient.get_vertical_profile()
        assert len(z_coords) == 5
        assert len(t_values) == 5
        # Should be sorted from lowest to highest
        assert z_coords[0].to("m").magnitude == pytest.approx(0.5)
        assert z_coords[4].to("m").magnitude == pytest.approx(-0.5)
        # Check temperature values match the order
        assert t_values[0].magnitude == 10  # at 0.5
        assert t_values[2].magnitude == 30  # at 0.0
        assert t_values[4].magnitude == 20  # at -0.5

    def test_horizontal_gradient_horizontal_profile(self, horizontal_gradient):
        """Horizontal gradient returns sorted horizontal profiles."""
        x_coords, t_values = horizontal_gradient.get_horizontal_profile()
        assert len(x_coords) == 5
        assert len(t_values) == 5
        # Should be sorted from lowest to highest
        assert x_coords[0].to("m").magnitude == pytest.approx(-1.0)
        assert x_coords[4].to("m").magnitude == pytest.approx(1.0)
        # Check temperature values match the order
        assert t_values[0].magnitude == 10  # at -1.0
        assert t_values[2].magnitude == 35  # at 0.0
        assert t_values[4].magnitude == 15  # at 1.0

    def test_vertical_gradient_reverse(self, vertical_gradient):
        """get_vertical_profile with reverse=True sorts from highest to lowest."""
        z_coords, t_values = vertical_gradient.get_vertical_profile(reverse=True)
        assert len(z_coords) == 5
        # Should be sorted from highest to lowest
        assert z_coords[0].to("m").magnitude == pytest.approx(0.5)
        assert z_coords[4].to("m").magnitude == pytest.approx(-0.5)

    def test_horizontal_gradient_reverse(self, horizontal_gradient):
        """get_horizontal_profile with reverse=True sorts from highest to lowest."""
        x_coords, t_values = horizontal_gradient.get_horizontal_profile(reverse=True)
        assert len(x_coords) == 5
        # Should be sorted from highest to lowest
        assert x_coords[0].to("m").magnitude == pytest.approx(1.0)
        assert x_coords[4].to("m").magnitude == pytest.approx(-1.0)

    def test_thermal_load_uniform_creation(self):
        """ThermalLoadUniform stores temperature change."""
        from bda.domain.models.submodels.loads.load_thermal import ThermalLoadUniform

        thermal = ThermalLoadUniform(temperature_change=25 * units.ureg.delta_degC)
        assert thermal.temperature_change.magnitude == 25

    def test_thermal_load_gradient_empty(self):
        """ThermalLoadGradient starts with empty definitions."""
        gradient = ThermalLoadGradient()
        assert gradient.gradient_definitions == []

    def test_gradient_definition_properties(self):
        """GradientDefinition stores offset and temperature."""
        ref = OffsetReference.CENTER_TOP
        offset = Offset(vertical_value=0.5 * m, offset_reference=ref)
        grad = GradientDefinition(offset=offset, value=20 * units.ureg.delta_degC)
        assert grad.value.magnitude == 20
        assert grad.offset.vertical_value.to("m").magnitude == pytest.approx(0.5)

# ---------------------------------------------------------------------------
# Self-Weight Loads in Container
# ---------------------------------------------------------------------------
class TestSelfWeightInContainer:
    """Tests for self-weight loads in the Loads container."""

    def test_self_weight_load_basics(self, static_loads, lc, beam):
        """SelfWeightLoad can be added to container."""
        from bda.domain.models.submodels.loads.load_self_weight import SelfWeightLoad

        load = SelfWeightLoad(element=beam, load_case=lc)
        registered = static_loads.add_load(load)
        assert registered is load
        assert load.load_id == 1
        assert load.target is beam

    def test_self_weight_custom_factor(self, static_loads, lc, beam):
        """SelfWeightLoad with custom factor increments load ids."""
        from bda.domain.models.submodels.loads.load_self_weight import SelfWeightLoad, SelfWeightFactors

        factor = SelfWeightFactors(x=0.1, y=-0.2, z=-1.0)
        load = SelfWeightLoad(element=beam, load_case=lc, self_weight_factors=factor)

        registered = static_loads.add_load(load)
        assert isinstance(registered, SelfWeightLoad)
        assert registered.self_weight_factors.x == 0.1
        assert registered.self_weight_factors.z == -1.0

    def test_self_weight_increments_across_types(self, static_loads, lc, n1, beam):
        """Self-weight IDs increment across all load types."""
        from bda.domain.models.submodels.loads.load_self_weight import SelfWeightLoad

        p = static_loads.add_load(NodalPointLoad(node=n1, load_case=lc))
        sw = static_loads.add_load(SelfWeightLoad(element=beam, load_case=lc))
        ll = static_loads.add_load(BeamLineLoad(element=beam, load_case=lc))
        assert (p.load_id, sw.load_id, ll.load_id) == (1, 2, 3)


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------
class TestQueries:
    @pytest.fixture
    def populated(self, static_loads, lc, n1, n2, beam):
        lc_ll = static_loads.add_load_case(LoadCase(name="LL1", load_nature="LL"))
        p_node = static_loads.add_load(NodalPointLoad(node=n1, load_case=lc))
        p_beam = static_loads.add_load(BeamPointLoad(element=beam, load_case=lc_ll, relative_position=0.5))
        l_beam = static_loads.add_load(BeamLineLoad(element=beam, load_case=lc))
        return static_loads, lc, lc_ll, p_node, p_beam, l_beam

    def test_get_loads_by_load_case_object_and_name(self, populated):
        loads, lc, lc_ll, p_node, p_beam, l_beam = populated
        assert loads.get_loads_by_load_case(lc) == [p_node, l_beam]
        assert loads.get_loads_by_load_case("LL1") == [p_beam]

    def test_get_loads_by_load_case_unknown_name_raises(self, populated):
        loads = populated[0]
        with pytest.raises(KeyError):
            loads.get_loads_by_load_case("WS1")

    def test_get_loads_for_node(self, populated, n1, n2):
        loads, _, _, p_node, _, _ = populated
        assert loads.get_loads_for_node(n1) == [p_node]
        assert loads.get_loads_for_node(n2) == []

    def test_get_loads_for_element(self, populated, beam, n1, n2):
        loads, _, _, _, p_beam, l_beam = populated
        assert loads.get_loads_for_element(beam) == [p_beam, l_beam]
        assert loads.get_loads_for_element(Element1D(n1, n2)) == []

    def test_iter_loads_with_predicate(self, populated):
        loads, _, _, p_node, p_beam, l_beam = populated
        assert list(loads.iter_loads()) == [p_node, p_beam, l_beam]
        assert list(loads.iter_loads(lambda l: isinstance(l, BeamLineLoad))) == [l_beam]
        assert list(loads.iter_loads(lambda l: l.load_type is LoadType.POINT)) == [p_node, p_beam]

    def test_repr_is_compact(self, populated):
        loads, _, _, p_node, _, _ = populated
        assert repr(loads) == "Loads[2 load cases, 2 point, 1 line, 0 area loads]"
        assert repr(p_node).startswith("NodalPointLoad[id: 1, case: 'DC1'")
