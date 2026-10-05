"""Unit tests for ResultSet — add, merge, and view operations.

Covers:
    - add_force_envelope: insert and widening semantics
    - add_displacement_envelope: insert and widening semantics
    - add_stress: overwrite semantics
    - merge: union of two ResultSets with source tagging
    - view_for: element/node filtering via ResultSetView
"""
from __future__ import annotations

import pytest

from bda.infrastructure.utils import (
    CANONICAL_FORCE,
    CANONICAL_LENGTH,
    CANONICAL_MOMENT,
    CANONICAL_STRESS,
    Q_,
    ureg,
)
from bda.domain.enums.response_enums import ElementEnd
from bda.domain.results import (
    ElementForceEnvelope,
    ElementStress,
    ForceVector,
    NodalDisplacement,
    NodalDisplacementEnvelope,
    StressPoint,
)
from bda.domain.results.result_set import ResultSet


# =====================================================================
# Helpers
# =====================================================================


def _fv(fx=0, fy=0, fz=0, mx=0, my=0, mz=0) -> ForceVector:
    """Quick ForceVector from plain numbers (kN / kN*m)."""
    return ForceVector(
        Fx=Q_(fx, CANONICAL_FORCE),
        Fy=Q_(fy, CANONICAL_FORCE),
        Fz=Q_(fz, CANONICAL_FORCE),
        Mx=Q_(mx, CANONICAL_MOMENT),
        My=Q_(my, CANONICAL_MOMENT),
        Mz=Q_(mz, CANONICAL_MOMENT),
    )


def _nd(node_id=1, lc="Dead", ux=0, uy=0, uz=0, rx=0, ry=0, rz=0) -> NodalDisplacement:
    """Quick NodalDisplacement from plain numbers (m / rad)."""
    return NodalDisplacement(
        node_id=node_id,
        load_case=lc,
        UX=Q_(ux, CANONICAL_LENGTH),
        UY=Q_(uy, CANONICAL_LENGTH),
        UZ=Q_(uz, CANONICAL_LENGTH),
        RX=Q_(rx, ureg.radian),
        RY=Q_(ry, ureg.radian),
        RZ=Q_(rz, ureg.radian),
    )


def _env(element_id=1, end=ElementEnd.I, lc="Dead", fx=0, mz=0) -> ElementForceEnvelope:
    """Build a degenerate force envelope."""
    return ElementForceEnvelope.from_single(element_id, end, lc, _fv(fx=fx, mz=mz))


def _denv(node_id=1, lc="Dead", ux=0, uz=0) -> NodalDisplacementEnvelope:
    """Build a degenerate displacement envelope."""
    return NodalDisplacementEnvelope.from_single(
        node_id, lc, _nd(node_id=node_id, lc=lc, ux=ux, uz=uz)
    )


def _stress(element_id=1, end=ElementEnd.I, lc="Dead", sigma=100) -> ElementStress:
    """Build a simple ElementStress with one stress point."""
    sp = StressPoint(
        y=Q_(0, CANONICAL_LENGTH),
        z=Q_(0, CANONICAL_LENGTH),
        sigma=Q_(sigma, CANONICAL_STRESS),
    )
    return ElementStress(element_id=element_id, end=end, load_case=lc, points=(sp,))


class _FakeNode:
    """Minimal node stub for view_for tests."""
    def __init__(self, node_id):
        self.node_id = node_id


class _FakeElement:
    """Minimal element stub for view_for tests."""
    def __init__(self, element_id):
        self.element_id = element_id


class _FakeGroup:
    """Minimal Group stub for view_for tests."""
    def __init__(self, elements=None, nodes=None, nested_groups=None):
        self.elements = elements or []
        self.nodes = nodes or []
        self.nested_groups = nested_groups or []


# =====================================================================
# TestPutForceEnvelope
# =====================================================================


class TestPutForceEnvelope:
    """Tests for ResultSet.put_force_envelope insert and widening."""

    def test_insert_new(self):
        rs = ResultSet()
        env = _env(element_id=1, end=ElementEnd.I, lc="Dead", fx=100)
        rs.add_force_envelope(env)

        key = (1, ElementEnd.I, "Dead")
        assert key in rs.force_envelopes
        assert rs.force_envelopes[key].Fx_max.Fx.magnitude == pytest.approx(100)

    def test_widening_on_collision(self):
        """Second insert with same key should widen, not overwrite."""
        rs = ResultSet()
        env1 = _env(element_id=1, end=ElementEnd.I, lc="Dead", fx=100, mz=200)
        env2 = _env(element_id=1, end=ElementEnd.I, lc="Dead", fx=200, mz=50)

        rs.add_force_envelope(env1)
        rs.add_force_envelope(env2)

        result = rs.force_envelopes[(1, ElementEnd.I, "Dead")]
        # Fx_max should be from env2 (200 > 100)
        assert result.Fx_max.Fx.magnitude == pytest.approx(200)
        # Mz_max should be from env1 (200 > 50)
        assert result.Mz_max.Mz.magnitude == pytest.approx(200)

    def test_widening_min(self):
        rs = ResultSet()
        env1 = _env(element_id=1, end=ElementEnd.I, lc="Dead", fx=100)
        env2 = _env(element_id=1, end=ElementEnd.I, lc="Dead", fx=-50)

        rs.add_force_envelope(env1)
        rs.add_force_envelope(env2)

        result = rs.force_envelopes[(1, ElementEnd.I, "Dead")]
        assert result.Fx_min.Fx.magnitude == pytest.approx(-50)
        assert result.Fx_max.Fx.magnitude == pytest.approx(100)

    def test_different_keys_no_collision(self):
        """Different (element, end, lc) should produce separate entries."""
        rs = ResultSet()
        rs.add_force_envelope(_env(element_id=1, end=ElementEnd.I, lc="Dead", fx=100))
        rs.add_force_envelope(_env(element_id=1, end=ElementEnd.J, lc="Dead", fx=200))
        rs.add_force_envelope(_env(element_id=2, end=ElementEnd.I, lc="Dead", fx=300))
        rs.add_force_envelope(_env(element_id=1, end=ElementEnd.I, lc="Live", fx=400))

        assert len(rs.force_envelopes) == 4


# =====================================================================
# TestPutDisplacementEnvelope
# =====================================================================


class TestPutDisplacementEnvelope:
    """Tests for ResultSet.put_displacement_envelope insert and widening."""

    def test_insert_new(self):
        rs = ResultSet()
        denv = _denv(node_id=1, lc="Dead", ux=0.001)
        rs.add_displacement_envelope(denv)

        key = (1, "Dead")
        assert key in rs.displacement_envelopes
        assert rs.displacement_envelopes[key].UX_max.UX.magnitude == pytest.approx(0.001)

    def test_widening_on_collision(self):
        """CB:max / CB:min scenario — two rows for same (node, lc)."""
        rs = ResultSet()
        denv_max = _denv(node_id=1, lc="ULS", ux=0.005, uz=-0.001)
        denv_min = _denv(node_id=1, lc="ULS", ux=-0.003, uz=-0.008)

        rs.add_displacement_envelope(denv_max)
        rs.add_displacement_envelope(denv_min)

        result = rs.displacement_envelopes[(1, "ULS")]
        assert result.UX_max.UX.magnitude == pytest.approx(0.005)
        assert result.UX_min.UX.magnitude == pytest.approx(-0.003)
        assert result.UZ_max.UZ.magnitude == pytest.approx(-0.001)
        assert result.UZ_min.UZ.magnitude == pytest.approx(-0.008)

    def test_different_keys_no_collision(self):
        rs = ResultSet()
        rs.add_displacement_envelope(_denv(node_id=1, lc="Dead"))
        rs.add_displacement_envelope(_denv(node_id=2, lc="Dead"))
        rs.add_displacement_envelope(_denv(node_id=1, lc="Live"))

        assert len(rs.displacement_envelopes) == 3


# =====================================================================
# TestPutStress
# =====================================================================


class TestPutStress:
    """Tests for ResultSet.put_stress — overwrite semantics."""

    def test_insert(self):
        rs = ResultSet()
        s = _stress(element_id=1, end=ElementEnd.I, lc="Dead", sigma=100)
        rs.add_stress(s)

        key = (1, ElementEnd.I, "Dead")
        assert key in rs.stresses
        assert rs.stresses[key].points[0].sigma.magnitude == pytest.approx(100)

    def test_overwrite(self):
        """Second insert with same key overwrites (not widening for stresses)."""
        rs = ResultSet()
        s1 = _stress(element_id=1, end=ElementEnd.I, lc="Dead", sigma=100)
        s2 = _stress(element_id=1, end=ElementEnd.I, lc="Dead", sigma=999)

        rs.add_stress(s1)
        rs.add_stress(s2)

        result = rs.stresses[(1, ElementEnd.I, "Dead")]
        assert result.points[0].sigma.magnitude == pytest.approx(999)


# =====================================================================
# TestMerge
# =====================================================================


class TestMerge:
    """Tests for ResultSet.merge — union of two ResultSets."""

    def test_merge_disjoint(self):
        """Merging two non-overlapping ResultSets produces the union."""
        rs1 = ResultSet(source="csi_helpers")
        rs1.add_force_envelope(_env(element_id=1, lc="Dead", fx=100))

        rs2 = ResultSet(source="midas_civil_nx")
        rs2.add_force_envelope(_env(element_id=2, lc="Dead", fx=200))

        merged = rs1.merge(rs2)
        assert len(merged.force_envelopes) == 2
        assert merged.source == "mixed"

    def test_merge_overlapping_forces_widen(self):
        """Overlapping force keys should be widened, not overwritten."""
        rs1 = ResultSet(source="a")
        rs1.add_force_envelope(_env(element_id=1, lc="Dead", fx=100))

        rs2 = ResultSet(source="a")
        rs2.add_force_envelope(_env(element_id=1, lc="Dead", fx=200))

        merged = rs1.merge(rs2)
        assert len(merged.force_envelopes) == 1
        result = merged.force_envelopes[(1, ElementEnd.I, "Dead")]
        assert result.Fx_max.Fx.magnitude == pytest.approx(200)
        assert result.Fx_min.Fx.magnitude == pytest.approx(100)

    def test_merge_overlapping_displacements_widen(self):
        rs1 = ResultSet()
        rs1.add_displacement_envelope(_denv(node_id=1, lc="Dead", ux=0.001))

        rs2 = ResultSet()
        rs2.add_displacement_envelope(_denv(node_id=1, lc="Dead", ux=0.005))

        merged = rs1.merge(rs2)
        assert len(merged.displacement_envelopes) == 1
        result = merged.displacement_envelopes[(1, "Dead")]
        assert result.UX_max.UX.magnitude == pytest.approx(0.005)
        assert result.UX_min.UX.magnitude == pytest.approx(0.001)

    def test_merge_stresses_overwrite(self):
        rs1 = ResultSet()
        rs1.add_stress(_stress(element_id=1, lc="Dead", sigma=100))

        rs2 = ResultSet()
        rs2.add_stress(_stress(element_id=1, lc="Dead", sigma=999))

        merged = rs1.merge(rs2)
        result = merged.stresses[(1, ElementEnd.I, "Dead")]
        assert result.points[0].sigma.magnitude == pytest.approx(999)

    def test_merge_does_not_mutate_originals(self):
        rs1 = ResultSet()
        rs1.add_force_envelope(_env(element_id=1, lc="Dead", fx=100))

        rs2 = ResultSet()
        rs2.add_force_envelope(_env(element_id=2, lc="Dead", fx=200))

        merged = rs1.merge(rs2)
        # rs1 should still only have element 1
        assert len(rs1.force_envelopes) == 1
        assert len(merged.force_envelopes) == 2

    def test_merge_source_same(self):
        """Same source on both sides → keep the source."""
        rs1 = ResultSet(source="csi_helpers")
        rs2 = ResultSet(source="csi_helpers")
        merged = rs1.merge(rs2)
        assert merged.source == "csi_helpers"

    def test_merge_source_empty_other(self):
        """Empty source on self → use other's source."""
        rs1 = ResultSet(source="")
        rs2 = ResultSet(source="midas_civil_nx")
        merged = rs1.merge(rs2)
        assert merged.source == "midas_civil_nx"

    def test_merge_source_empty_self(self):
        """Empty source on other → keep self's source."""
        rs1 = ResultSet(source="csi_helpers")
        rs2 = ResultSet(source="")
        merged = rs1.merge(rs2)
        assert merged.source == "csi_helpers"

    def test_merge_source_different(self):
        """Different sources → 'mixed'."""
        rs1 = ResultSet(source="csi_helpers")
        rs2 = ResultSet(source="midas_civil_nx")
        merged = rs1.merge(rs2)
        assert merged.source == "mixed"


# =====================================================================
# TestResultSetView
# =====================================================================


class TestResultSetView:
    """Tests for ResultSetView — filtered access via view_for."""

    def _populated_result_set(self) -> ResultSet:
        """Build a ResultSet with data for elements 1,2 and nodes 1,2,3."""
        rs = ResultSet()
        # Force envelopes for elements 1 and 2
        rs.add_force_envelope(_env(element_id=1, end=ElementEnd.I, lc="Dead", fx=100))
        rs.add_force_envelope(_env(element_id=1, end=ElementEnd.J, lc="Dead", fx=110))
        rs.add_force_envelope(_env(element_id=2, end=ElementEnd.I, lc="Dead", fx=200))

        # Displacement envelopes for nodes 1, 2, 3
        rs.add_displacement_envelope(_denv(node_id=1, lc="Dead", ux=0.001))
        rs.add_displacement_envelope(_denv(node_id=2, lc="Dead", ux=0.002))
        rs.add_displacement_envelope(_denv(node_id=3, lc="Dead", ux=0.003))

        # Stresses for elements 1 and 2
        rs.add_stress(_stress(element_id=1, end=ElementEnd.I, lc="Dead", sigma=50))
        rs.add_stress(_stress(element_id=2, end=ElementEnd.I, lc="Dead", sigma=80))

        return rs

    def test_view_for_filters_elements(self):
        rs = self._populated_result_set()
        group = _FakeGroup(
            elements=[_FakeElement(1)],
            nodes=[_FakeNode(1), _FakeNode(2)],
        )
        view = rs.view_for(group)

        # Should see element 1 but not element 2
        env = view.force_envelope(1, ElementEnd.I, "Dead")
        assert env.Fx_max.Fx.magnitude == pytest.approx(100)

        with pytest.raises(KeyError, match="not part of this view"):
            view.force_envelope(2, ElementEnd.I, "Dead")

    def test_view_for_filters_nodes(self):
        rs = self._populated_result_set()
        group = _FakeGroup(
            elements=[_FakeElement(1)],
            nodes=[_FakeNode(1)],
        )
        view = rs.view_for(group)

        # Should see node 1 but not nodes 2 or 3
        denv = view.displacement_envelope(1, "Dead")
        assert denv.UX_max.UX.magnitude == pytest.approx(0.001)

        with pytest.raises(KeyError, match="not part of this view"):
            view.displacement_envelope(2, "Dead")

    def test_iter_force_envelopes_filtered(self):
        rs = self._populated_result_set()
        group = _FakeGroup(
            elements=[_FakeElement(1)],
            nodes=[],
        )
        view = rs.view_for(group)

        envs = list(view.iter_force_envelopes())
        # Element 1 has two entries (I and J ends)
        assert len(envs) == 2
        assert all(e.element_id == 1 for e in envs)

    def test_iter_displacement_envelopes_filtered(self):
        rs = self._populated_result_set()
        group = _FakeGroup(
            elements=[],
            nodes=[_FakeNode(2), _FakeNode(3)],
        )
        view = rs.view_for(group)

        denvs = list(view.iter_displacement_envelopes())
        assert len(denvs) == 2
        node_ids = {d.node_id for d in denvs}
        assert node_ids == {2, 3}

    def test_iter_stresses_filtered(self):
        rs = self._populated_result_set()
        group = _FakeGroup(
            elements=[_FakeElement(2)],
            nodes=[],
        )
        view = rs.view_for(group)

        stresses = list(view.iter_stresses())
        assert len(stresses) == 1
        assert stresses[0].element_id == 2

    def test_stress_access_filtered(self):
        rs = self._populated_result_set()
        group = _FakeGroup(
            elements=[_FakeElement(1)],
            nodes=[],
        )
        view = rs.view_for(group)

        s = view.stress(1, ElementEnd.I, "Dead")
        assert s.points[0].sigma.magnitude == pytest.approx(50)

        with pytest.raises(KeyError, match="not part of this view"):
            view.stress(2, ElementEnd.I, "Dead")

    def test_nested_groups(self):
        """Nested groups should contribute their ids to the view."""
        rs = self._populated_result_set()
        inner = _FakeGroup(
            elements=[_FakeElement(2)],
            nodes=[_FakeNode(3)],
        )
        outer = _FakeGroup(
            elements=[_FakeElement(1)],
            nodes=[_FakeNode(1)],
            nested_groups=[inner],
        )
        view = rs.view_for(outer)

        # Both element 1 and 2 should be visible
        view.force_envelope(1, ElementEnd.I, "Dead")
        view.force_envelope(2, ElementEnd.I, "Dead")

        # Both node 1 and 3 should be visible
        view.displacement_envelope(1, "Dead")
        view.displacement_envelope(3, "Dead")

        # Node 2 should NOT be visible
        with pytest.raises(KeyError, match="not part of this view"):
            view.displacement_envelope(2, "Dead")

    def test_missing_key_raises_key_error(self):
        """Accessing a key that is in the view but not in the data → KeyError."""
        rs = ResultSet()
        group = _FakeGroup(
            elements=[_FakeElement(99)],
            nodes=[_FakeNode(99)],
        )
        view = rs.view_for(group)

        # Element 99 is in the view, but no data exists for it
        with pytest.raises(KeyError):
            view.force_envelope(99, ElementEnd.I, "Dead")

    def test_node_without_node_id_raises(self):
        """Node object missing node_id attribute should raise AttributeError."""

        class _BadNode:
            pass

        rs = ResultSet()
        group = _FakeGroup(nodes=[_BadNode()])

        with pytest.raises(AttributeError, match="no 'node_id' attribute"):
            rs.view_for(group)
