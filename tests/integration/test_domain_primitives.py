"""Unit tests for domain result primitives.

Covers ForceVector, ElementForceEnvelope, NodalDisplacement,
NodalDisplacementEnvelope, StressPoint, and ElementStress — including
dimensional validation, envelope construction, and widening.
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


# =====================================================================
# TestForceVector
# =====================================================================


class TestForceVector:
    """Tests for ForceVector construction and validation."""

    def test_construction(self):
        fv = _fv(100, 50, 10, 5, 200, 300)
        assert fv.Fx.magnitude == pytest.approx(100.0)
        assert fv.Mz.magnitude == pytest.approx(300.0)

    def test_frozen(self):
        fv = _fv(100, 50, 10, 5, 200, 300)
        with pytest.raises(AttributeError):
            fv.Fx = Q_(999, CANONICAL_FORCE)

    def test_force_dimension_check(self):
        """Fx must have [force] dimensions — not [length]."""
        with pytest.raises(ValueError, match="Fx must have dimensions of"):
            ForceVector(
                Fx=Q_(100, CANONICAL_LENGTH),  # wrong!
                Fy=Q_(0, CANONICAL_FORCE),
                Fz=Q_(0, CANONICAL_FORCE),
                Mx=Q_(0, CANONICAL_MOMENT),
                My=Q_(0, CANONICAL_MOMENT),
                Mz=Q_(0, CANONICAL_MOMENT),
            )

    def test_moment_dimension_check(self):
        """Mx must have [force]*[length] dimensions — not [force]."""
        with pytest.raises(ValueError, match="Mx must have dimensions of"):
            ForceVector(
                Fx=Q_(0, CANONICAL_FORCE),
                Fy=Q_(0, CANONICAL_FORCE),
                Fz=Q_(0, CANONICAL_FORCE),
                Mx=Q_(100, CANONICAL_FORCE),  # wrong!
                My=Q_(0, CANONICAL_MOMENT),
                Mz=Q_(0, CANONICAL_MOMENT),
            )

    def test_all_six_components_present(self):
        fv = _fv(1, 2, 3, 4, 5, 6)
        assert fv.Fx.magnitude == pytest.approx(1)
        assert fv.Fy.magnitude == pytest.approx(2)
        assert fv.Fz.magnitude == pytest.approx(3)
        assert fv.Mx.magnitude == pytest.approx(4)
        assert fv.My.magnitude == pytest.approx(5)
        assert fv.Mz.magnitude == pytest.approx(6)


# =====================================================================
# TestElementForceEnvelope
# =====================================================================


class TestElementForceEnvelope:
    """Tests for ElementForceEnvelope construction and widening."""

    def test_from_single(self):
        fv = _fv(100, 50, 10, 5, 200, 300)
        env = ElementForceEnvelope.from_single(
            element_id=1, end=ElementEnd.I, load_case="ULS", f=fv,
        )
        # Degenerate envelope: max == min for all components
        assert env.Fx_max is fv
        assert env.Fx_min is fv
        assert env.Mz_max is fv
        assert env.Mz_min is fv

    def test_widening_updates_max(self):
        fv1 = _fv(fx=100, mz=200)
        fv2 = _fv(fx=150, mz=100)  # higher Fx, lower Mz
        env = ElementForceEnvelope.from_single(1, ElementEnd.I, "ULS", fv1)
        env = env.updated_with(fv2)

        # Fx_max should now be fv2 (150 > 100)
        assert env.Fx_max.Fx.magnitude == pytest.approx(150)
        # Mz_max should still be fv1 (200 > 100)
        assert env.Mz_max.Mz.magnitude == pytest.approx(200)

    def test_widening_updates_min(self):
        fv1 = _fv(fx=100, mz=-200)
        fv2 = _fv(fx=-50, mz=-100)  # lower Fx, higher Mz
        env = ElementForceEnvelope.from_single(1, ElementEnd.I, "ULS", fv1)
        env = env.updated_with(fv2)

        # Fx_min should be fv2 (-50 < 100)
        assert env.Fx_min.Fx.magnitude == pytest.approx(-50)
        # Mz_min should still be fv1 (-200 < -100)
        assert env.Mz_min.Mz.magnitude == pytest.approx(-200)

    def test_widening_preserves_correlated_vector(self):
        """When Fx_max is updated, the full ForceVector is stored (not just Fx)."""
        fv1 = _fv(fx=100, fy=10, mz=200)
        fv2 = _fv(fx=150, fy=20, mz=100)
        env = ElementForceEnvelope.from_single(1, ElementEnd.I, "ULS", fv1)
        env = env.updated_with(fv2)

        # fv2 governs Fx_max — check that the *correlated* Fy is from fv2
        assert env.Fx_max.Fy.magnitude == pytest.approx(20)
        # fv1 still governs Mz_max — correlated Fy is from fv1
        assert env.Mz_max.Fy.magnitude == pytest.approx(10)

    def test_widening_is_immutable(self):
        fv1 = _fv(100)
        fv2 = _fv(200)
        env1 = ElementForceEnvelope.from_single(1, ElementEnd.I, "ULS", fv1)
        env2 = env1.updated_with(fv2)

        # env1 should be unchanged (frozen dataclass)
        assert env1.Fx_max.Fx.magnitude == pytest.approx(100)
        assert env2.Fx_max.Fx.magnitude == pytest.approx(200)

    def test_multiple_widenings(self):
        """Three successive rows should produce correct envelope."""
        fv_a = _fv(fx=100, mz=300)
        fv_b = _fv(fx=200, mz=100)
        fv_c = _fv(fx=-50, mz=500)

        env = ElementForceEnvelope.from_single(1, ElementEnd.I, "ULS", fv_a)
        env = env.updated_with(fv_b)
        env = env.updated_with(fv_c)

        assert env.Fx_max.Fx.magnitude == pytest.approx(200)  # from fv_b
        assert env.Fx_min.Fx.magnitude == pytest.approx(-50)  # from fv_c
        assert env.Mz_max.Mz.magnitude == pytest.approx(500)  # from fv_c
        assert env.Mz_min.Mz.magnitude == pytest.approx(100)  # from fv_b


# =====================================================================
# TestNodalDisplacement
# =====================================================================


class TestNodalDisplacement:
    """Tests for NodalDisplacement construction and validation."""

    def test_construction(self):
        d = _nd(ux=0.001, uz=-0.005, rx=0.0001)
        assert d.UX.magnitude == pytest.approx(0.001)
        assert d.UZ.magnitude == pytest.approx(-0.005)
        assert d.RX.magnitude == pytest.approx(0.0001)

    def test_frozen(self):
        d = _nd()
        with pytest.raises(AttributeError):
            d.UX = Q_(999, CANONICAL_LENGTH)

    def test_translation_dimension_check(self):
        with pytest.raises(ValueError, match="UX must have dimensions of"):
            NodalDisplacement(
                node_id=1, load_case="Dead",
                UX=Q_(1, CANONICAL_FORCE),  # wrong!
                UY=Q_(0, CANONICAL_LENGTH),
                UZ=Q_(0, CANONICAL_LENGTH),
                RX=Q_(0, ureg.radian),
                RY=Q_(0, ureg.radian),
                RZ=Q_(0, ureg.radian),
            )

    def test_rotation_dimension_check(self):
        with pytest.raises(ValueError, match="RX must have dimensions of radian"):
            NodalDisplacement(
                node_id=1, load_case="Dead",
                UX=Q_(0, CANONICAL_LENGTH),
                UY=Q_(0, CANONICAL_LENGTH),
                UZ=Q_(0, CANONICAL_LENGTH),
                RX=Q_(0, CANONICAL_LENGTH),  # wrong!
                RY=Q_(0, ureg.radian),
                RZ=Q_(0, ureg.radian),
            )


# =====================================================================
# TestNodalDisplacementEnvelope
# =====================================================================


class TestNodalDisplacementEnvelope:
    """Tests for NodalDisplacementEnvelope — mirrors TestElementForceEnvelope."""

    def test_from_single(self):
        d = _nd(ux=0.001, uz=-0.005)
        env = NodalDisplacementEnvelope.from_single(node_id=1, load_case="Dead", d=d)
        assert env.UX_max is d
        assert env.UX_min is d
        assert env.UZ_max is d
        assert env.UZ_min is d

    def test_widening_updates_max(self):
        d1 = _nd(ux=0.001, uz=-0.005)
        d2 = _nd(ux=0.003, uz=-0.002)  # higher UX, higher UZ
        env = NodalDisplacementEnvelope.from_single(1, "Dead", d1)
        env = env.updated_with(d2)

        assert env.UX_max.UX.magnitude == pytest.approx(0.003)  # d2
        assert env.UZ_max.UZ.magnitude == pytest.approx(-0.002)  # d2 (closer to 0)

    def test_widening_updates_min(self):
        d1 = _nd(ux=0.001, uz=-0.005)
        d2 = _nd(ux=-0.002, uz=-0.010)  # lower UX, lower UZ
        env = NodalDisplacementEnvelope.from_single(1, "Dead", d1)
        env = env.updated_with(d2)

        assert env.UX_min.UX.magnitude == pytest.approx(-0.002)  # d2
        assert env.UZ_min.UZ.magnitude == pytest.approx(-0.010)  # d2

    def test_widening_preserves_correlated_vector(self):
        d1 = _nd(ux=0.001, uy=0.010, uz=-0.005)
        d2 = _nd(ux=0.005, uy=0.020, uz=-0.003)
        env = NodalDisplacementEnvelope.from_single(1, "Dead", d1)
        env = env.updated_with(d2)

        # d2 governs UX_max — correlated UY should be from d2
        assert env.UX_max.UY.magnitude == pytest.approx(0.020)

    def test_cb_max_min_scenario(self):
        """Simulate what Midas CB:max/CB:min produce — both rows widen."""
        d_max = _nd(ux=0.005, uz=-0.001)  # CB:max row
        d_min = _nd(ux=-0.003, uz=-0.008)  # CB:min row

        env = NodalDisplacementEnvelope.from_single(1, "ULS_gr5", d_max)
        env = env.updated_with(d_min)

        assert env.UX_max.UX.magnitude == pytest.approx(0.005)
        assert env.UX_min.UX.magnitude == pytest.approx(-0.003)
        assert env.UZ_max.UZ.magnitude == pytest.approx(-0.001)
        assert env.UZ_min.UZ.magnitude == pytest.approx(-0.008)

    def test_widening_is_immutable(self):
        d1 = _nd(ux=0.001)
        d2 = _nd(ux=0.005)
        env1 = NodalDisplacementEnvelope.from_single(1, "Dead", d1)
        env2 = env1.updated_with(d2)

        assert env1.UX_max.UX.magnitude == pytest.approx(0.001)
        assert env2.UX_max.UX.magnitude == pytest.approx(0.005)

    def test_rotation_envelope(self):
        """Rotations are enveloped independently just like translations."""
        d1 = _nd(rx=0.001, ry=-0.002)
        d2 = _nd(rx=-0.003, ry=0.004)
        env = NodalDisplacementEnvelope.from_single(1, "Dead", d1)
        env = env.updated_with(d2)

        assert env.RX_max.RX.magnitude == pytest.approx(0.001)
        assert env.RX_min.RX.magnitude == pytest.approx(-0.003)
        assert env.RY_max.RY.magnitude == pytest.approx(0.004)
        assert env.RY_min.RY.magnitude == pytest.approx(-0.002)


# =====================================================================
# TestStressPoint and TestElementStress
# =====================================================================


class TestStressPoint:
    def test_construction(self):
        sp = StressPoint(
            y=Q_(0.5, CANONICAL_LENGTH),
            z=Q_(-0.3, CANONICAL_LENGTH),
            sigma=Q_(150, CANONICAL_STRESS),
        )
        assert sp.sigma.magnitude == pytest.approx(150)

    def test_y_dimension_check(self):
        with pytest.raises(ValueError, match="y must have dimensions of"):
            StressPoint(
                y=Q_(0.5, CANONICAL_FORCE),  # wrong!
                z=Q_(0, CANONICAL_LENGTH),
                sigma=Q_(0, CANONICAL_STRESS),
            )

    def test_sigma_dimension_check(self):
        with pytest.raises(ValueError, match="sigma must have dimensions of"):
            StressPoint(
                y=Q_(0, CANONICAL_LENGTH),
                z=Q_(0, CANONICAL_LENGTH),
                sigma=Q_(100, CANONICAL_FORCE),  # wrong!
            )


class TestElementStress:
    def test_construction(self):
        sp = StressPoint(
            y=Q_(0, CANONICAL_LENGTH),
            z=Q_(0, CANONICAL_LENGTH),
            sigma=Q_(100, CANONICAL_STRESS),
        )
        es = ElementStress(
            element_id=1, end=ElementEnd.I, load_case="Dead", points=(sp,),
        )
        assert len(es.points) == 1
        assert es.element_id == 1

    def test_default_empty_points(self):
        es = ElementStress(element_id=1, end=ElementEnd.I, load_case="Dead")
        assert es.points == ()
