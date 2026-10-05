"""Cross-program sanity checks — no live connections required.

These tests verify structural properties of the domain primitives and
ResultSet that would catch cross-program inconsistencies before actual
live data is compared. They are unit tests that validate:

1. Envelope consistency: widening is symmetric and idempotent.
2. Sign convention plausibility: force/displacement vectors produced by
   mock data conform to expected physical behaviour.
3. ResultSet merge invariants: merging two result sets produces the
   correct envelope extremes regardless of insertion order.
4. Correlated vector integrity: updating an envelope preserves the
   full correlated vector, not just the governing component.
5. Canonical unit enforcement: all primitives reject wrong dimensions.
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
    return ForceVector(
        Fx=Q_(fx, CANONICAL_FORCE),
        Fy=Q_(fy, CANONICAL_FORCE),
        Fz=Q_(fz, CANONICAL_FORCE),
        Mx=Q_(mx, CANONICAL_MOMENT),
        My=Q_(my, CANONICAL_MOMENT),
        Mz=Q_(mz, CANONICAL_MOMENT),
    )


def _nd(node_id=1, lc="Dead", ux=0, uy=0, uz=0, rx=0, ry=0, rz=0) -> NodalDisplacement:
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
# TestEnvelopeConsistency
# =====================================================================


class TestEnvelopeConsistency:
    """Structural properties of envelope widening that any importer must satisfy."""

    def test_force_envelope_widening_is_commutative(self):
        """Order of insertion should not change the final envelope extremes."""
        fv_a = _fv(fx=100, mz=300)
        fv_b = _fv(fx=200, mz=100)
        fv_c = _fv(fx=-50, mz=500)

        # Order A → B → C
        env_abc = ElementForceEnvelope.from_single(1, ElementEnd.I, "Dead", fv_a)
        env_abc = env_abc.updated_with(fv_b).updated_with(fv_c)

        # Order C → B → A
        env_cba = ElementForceEnvelope.from_single(1, ElementEnd.I, "Dead", fv_c)
        env_cba = env_cba.updated_with(fv_b).updated_with(fv_a)

        # Order B → A → C
        env_bac = ElementForceEnvelope.from_single(1, ElementEnd.I, "Dead", fv_b)
        env_bac = env_bac.updated_with(fv_a).updated_with(fv_c)

        # All three should agree on extremes
        for env in (env_abc, env_cba, env_bac):
            assert env.Fx_max.Fx.magnitude == pytest.approx(200)
            assert env.Fx_min.Fx.magnitude == pytest.approx(-50)
            assert env.Mz_max.Mz.magnitude == pytest.approx(500)
            assert env.Mz_min.Mz.magnitude == pytest.approx(100)

    def test_displacement_envelope_widening_is_commutative(self):
        d_a = _nd(ux=0.001, uz=-0.005)
        d_b = _nd(ux=0.005, uz=-0.001)
        d_c = _nd(ux=-0.003, uz=-0.010)

        env_abc = NodalDisplacementEnvelope.from_single(1, "Dead", d_a)
        env_abc = env_abc.updated_with(d_b).updated_with(d_c)

        env_cba = NodalDisplacementEnvelope.from_single(1, "Dead", d_c)
        env_cba = env_cba.updated_with(d_b).updated_with(d_a)

        for env in (env_abc, env_cba):
            assert env.UX_max.UX.magnitude == pytest.approx(0.005)
            assert env.UX_min.UX.magnitude == pytest.approx(-0.003)
            assert env.UZ_max.UZ.magnitude == pytest.approx(-0.001)
            assert env.UZ_min.UZ.magnitude == pytest.approx(-0.010)

    def test_force_envelope_idempotent(self):
        """Widening with the same vector twice should be a no-op."""
        fv = _fv(fx=100, mz=200)
        env = ElementForceEnvelope.from_single(1, ElementEnd.I, "Dead", fv)
        env2 = env.updated_with(fv)

        assert env2.Fx_max.Fx.magnitude == pytest.approx(100)
        assert env2.Fx_min.Fx.magnitude == pytest.approx(100)
        assert env2.Mz_max.Mz.magnitude == pytest.approx(200)
        assert env2.Mz_min.Mz.magnitude == pytest.approx(200)

    def test_displacement_envelope_idempotent(self):
        d = _nd(ux=0.001, uz=-0.005)
        env = NodalDisplacementEnvelope.from_single(1, "Dead", d)
        env2 = env.updated_with(d)

        assert env2.UX_max.UX.magnitude == pytest.approx(0.001)
        assert env2.UX_min.UX.magnitude == pytest.approx(0.001)
        assert env2.UZ_max.UZ.magnitude == pytest.approx(-0.005)
        assert env2.UZ_min.UZ.magnitude == pytest.approx(-0.005)


# =====================================================================
# TestCorrelatedVectorIntegrity
# =====================================================================


class TestCorrelatedVectorIntegrity:
    """The full correlated vector must be stored with each extreme, not
    just the governing component."""

    def test_force_correlated_vector_preserved(self):
        """When Fx_max is updated, the correlated Fy/Mz from that row are kept."""
        fv1 = _fv(fx=100, fy=10, mz=200)
        fv2 = _fv(fx=200, fy=20, mz=100)

        env = ElementForceEnvelope.from_single(1, ElementEnd.I, "Dead", fv1)
        env = env.updated_with(fv2)

        # fv2 governs Fx_max — check correlated Fy
        assert env.Fx_max.Fy.magnitude == pytest.approx(20)
        # fv1 governs Mz_max — check correlated Fy
        assert env.Mz_max.Fy.magnitude == pytest.approx(10)

    def test_displacement_correlated_vector_preserved(self):
        d1 = _nd(ux=0.001, uy=0.010, uz=-0.005)
        d2 = _nd(ux=0.005, uy=0.020, uz=-0.003)

        env = NodalDisplacementEnvelope.from_single(1, "Dead", d1)
        env = env.updated_with(d2)

        # d2 governs UX_max — correlated UY should be from d2
        assert env.UX_max.UY.magnitude == pytest.approx(0.020)
        # d1 still governs UZ_min — correlated UY should be from d1
        assert env.UZ_min.UY.magnitude == pytest.approx(0.010)

    def test_force_all_six_components_independent(self):
        """Each component should track its own max/min independently."""
        fv_a = _fv(fx=100, fy=-50, fz=10, mx=5, my=-200, mz=300)
        fv_b = _fv(fx=-50, fy=100, fz=-20, mx=-10, my=400, mz=-100)

        env = ElementForceEnvelope.from_single(1, ElementEnd.I, "Dead", fv_a)
        env = env.updated_with(fv_b)

        assert env.Fx_max.Fx.magnitude == pytest.approx(100)   # fv_a
        assert env.Fx_min.Fx.magnitude == pytest.approx(-50)    # fv_b
        assert env.Fy_max.Fy.magnitude == pytest.approx(100)   # fv_b
        assert env.Fy_min.Fy.magnitude == pytest.approx(-50)   # fv_a
        assert env.Fz_max.Fz.magnitude == pytest.approx(10)    # fv_a
        assert env.Fz_min.Fz.magnitude == pytest.approx(-20)   # fv_b
        assert env.Mx_max.Mx.magnitude == pytest.approx(5)     # fv_a
        assert env.Mx_min.Mx.magnitude == pytest.approx(-10)   # fv_b
        assert env.My_max.My.magnitude == pytest.approx(400)   # fv_b
        assert env.My_min.My.magnitude == pytest.approx(-200)  # fv_a
        assert env.Mz_max.Mz.magnitude == pytest.approx(300)   # fv_a
        assert env.Mz_min.Mz.magnitude == pytest.approx(-100)  # fv_b


# =====================================================================
# TestResultSetMergeInvariants
# =====================================================================


class TestResultSetMergeInvariants:
    """Merge invariants that catch cross-program data combination bugs."""

    def test_merge_order_does_not_change_force_extremes(self):
        """rs1.merge(rs2) and rs2.merge(rs1) should give the same extremes."""
        rs1 = ResultSet(source="csi_helpers")
        env1 = ElementForceEnvelope.from_single(1, ElementEnd.I, "Dead", _fv(fx=100, mz=300))
        rs1.add_force_envelope(env1)

        rs2 = ResultSet(source="midas_civil_nx")
        env2 = ElementForceEnvelope.from_single(1, ElementEnd.I, "Dead", _fv(fx=200, mz=100))
        rs2.add_force_envelope(env2)

        merged_12 = rs1.merge(rs2)
        merged_21 = rs2.merge(rs1)

        for merged in (merged_12, merged_21):
            result = merged.force_envelopes[(1, ElementEnd.I, "Dead")]
            assert result.Fx_max.Fx.magnitude == pytest.approx(200)
            assert result.Fx_min.Fx.magnitude == pytest.approx(100)
            assert result.Mz_max.Mz.magnitude == pytest.approx(300)
            assert result.Mz_min.Mz.magnitude == pytest.approx(100)

    def test_merge_order_does_not_change_displacement_extremes(self):
        rs1 = ResultSet()
        d1 = _nd(node_id=1, lc="Dead", ux=0.005, uz=-0.001)
        denv1 = NodalDisplacementEnvelope.from_single(1, "Dead", d1)
        rs1.add_displacement_envelope(denv1)

        rs2 = ResultSet()
        d2 = _nd(node_id=1, lc="Dead", ux=-0.003, uz=-0.008)
        denv2 = NodalDisplacementEnvelope.from_single(1, "Dead", d2)
        rs2.add_displacement_envelope(denv2)

        merged_12 = rs1.merge(rs2)
        merged_21 = rs2.merge(rs1)

        for merged in (merged_12, merged_21):
            result = merged.displacement_envelopes[(1, "Dead")]
            assert result.UX_max.UX.magnitude == pytest.approx(0.005)
            assert result.UX_min.UX.magnitude == pytest.approx(-0.003)
            assert result.UZ_max.UZ.magnitude == pytest.approx(-0.001)
            assert result.UZ_min.UZ.magnitude == pytest.approx(-0.008)

    def test_merge_preserves_disjoint_keys(self):
        """Non-overlapping keys should all survive the merge."""
        rs1 = ResultSet()
        rs1.add_force_envelope(
            ElementForceEnvelope.from_single(1, ElementEnd.I, "Dead", _fv(fx=100))
        )

        rs2 = ResultSet()
        rs2.add_force_envelope(
            ElementForceEnvelope.from_single(2, ElementEnd.I, "Dead", _fv(fx=200))
        )
        rs2.add_force_envelope(
            ElementForceEnvelope.from_single(1, ElementEnd.J, "Dead", _fv(fx=150))
        )

        merged = rs1.merge(rs2)
        assert len(merged.force_envelopes) == 3


# =====================================================================
# TestSignConventionPlausibility
# =====================================================================


class TestSignConventionPlausibility:
    """Plausibility checks for sign conventions using synthetic data that
    mimics physical behaviour.

    These validate that the domain primitives can represent the expected
    physical scenarios — if an importer produces data that violates these
    patterns, the cross-program validation tests will catch it.
    """

    def test_gravity_beam_sagging_moment(self):
        """A simply supported beam under gravity should produce positive
        sagging Mz at the I end (by convention). Both importers must agree."""
        # Simulate what CSI/Midas should produce for a mid-span girder
        fv_i = _fv(fx=0, fy=-50, fz=0, mx=0, my=0, mz=500)  # I end: sagging +
        fv_j = _fv(fx=0, fy=50, fz=0, mx=0, my=0, mz=-500)  # J end: hogging -

        env_i = ElementForceEnvelope.from_single(1, ElementEnd.I, "Dead", fv_i)
        env_j = ElementForceEnvelope.from_single(1, ElementEnd.J, "Dead", fv_j)

        # Sagging at I end should be positive
        assert env_i.Mz_max.Mz.magnitude > 0
        # Hogging at J end should be negative
        assert env_j.Mz_min.Mz.magnitude < 0

    def test_gravity_deflection_downward(self):
        """Under gravity, vertical displacement UZ should be negative
        (Z-up convention)."""
        d = _nd(ux=0.0, uz=-0.005)
        env = NodalDisplacementEnvelope.from_single(1, "Dead", d)
        assert env.UZ_min.UZ.magnitude < 0

    def test_column_axial_compression(self):
        """A column under dead load should have Fx < 0 (compression negative)."""
        fv = _fv(fx=-500)  # compression
        env = ElementForceEnvelope.from_single(1, ElementEnd.I, "Dead", fv)
        assert env.Fx_min.Fx.magnitude < 0

    def test_prestress_tension(self):
        """Post-tensioning typically produces Fx > 0 (tension positive)."""
        fv = _fv(fx=1000)  # tension from PT
        env = ElementForceEnvelope.from_single(1, ElementEnd.I, "PT", fv)
        assert env.Fx_max.Fx.magnitude > 0


# =====================================================================
# TestCanonicalUnitEnforcement
# =====================================================================


class TestCanonicalUnitEnforcement:
    """All primitives must reject wrong physical dimensions — this catches
    unit conversion bugs in importers early."""

    def test_force_vector_rejects_length_for_force(self):
        with pytest.raises(ValueError, match="Fx must have dimensions of"):
            ForceVector(
                Fx=Q_(100, CANONICAL_LENGTH),
                Fy=Q_(0, CANONICAL_FORCE),
                Fz=Q_(0, CANONICAL_FORCE),
                Mx=Q_(0, CANONICAL_MOMENT),
                My=Q_(0, CANONICAL_MOMENT),
                Mz=Q_(0, CANONICAL_MOMENT),
            )

    def test_force_vector_rejects_force_for_moment(self):
        with pytest.raises(ValueError, match="Mx must have dimensions of"):
            ForceVector(
                Fx=Q_(0, CANONICAL_FORCE),
                Fy=Q_(0, CANONICAL_FORCE),
                Fz=Q_(0, CANONICAL_FORCE),
                Mx=Q_(100, CANONICAL_FORCE),
                My=Q_(0, CANONICAL_MOMENT),
                Mz=Q_(0, CANONICAL_MOMENT),
            )

    def test_displacement_rejects_force_for_translation(self):
        with pytest.raises(ValueError, match="UX must have dimensions of"):
            NodalDisplacement(
                node_id=1,
                load_case="Dead",
                UX=Q_(1, CANONICAL_FORCE),
                UY=Q_(0, CANONICAL_LENGTH),
                UZ=Q_(0, CANONICAL_LENGTH),
                RX=Q_(0, ureg.radian),
                RY=Q_(0, ureg.radian),
                RZ=Q_(0, ureg.radian),
            )

    def test_displacement_rejects_length_for_rotation(self):
        with pytest.raises(ValueError, match="RX must have dimensions of radian"):
            NodalDisplacement(
                node_id=1,
                load_case="Dead",
                UX=Q_(0, CANONICAL_LENGTH),
                UY=Q_(0, CANONICAL_LENGTH),
                UZ=Q_(0, CANONICAL_LENGTH),
                RX=Q_(0, CANONICAL_LENGTH),
                RY=Q_(0, ureg.radian),
                RZ=Q_(0, ureg.radian),
            )

    def test_stress_point_rejects_force_for_sigma(self):
        with pytest.raises(ValueError, match="sigma must have dimensions of"):
            StressPoint(
                y=Q_(0, CANONICAL_LENGTH),
                z=Q_(0, CANONICAL_LENGTH),
                sigma=Q_(100, CANONICAL_FORCE),
            )

    def test_stress_point_rejects_force_for_coordinate(self):
        with pytest.raises(ValueError, match="y must have dimensions of"):
            StressPoint(
                y=Q_(0, CANONICAL_FORCE),
                z=Q_(0, CANONICAL_LENGTH),
                sigma=Q_(100, CANONICAL_STRESS),
            )
