"""Normalized, program-agnostic result primitives.

Every physical quantity held by these dataclasses is a `pint.Quantity`
built against the shared application registry in
`infrastructure.utils.units`. Using bare floats here is a bug.

====================================================================
Conventions (binding contract for every importer)
====================================================================

These rules are the contract that every importer — CSI Bridge, Midas
Civil NX, any future source — must satisfy before it hands a primitive
to the normalized layer. Downstream calculators assume the conventions
below unconditionally. An importer that cannot meet them must flip
signs, swap components or transform coordinates itself before writing
into the `ResultSet`.

Force components (`ForceVector` / `ElementForceEnvelope`)
---------------------------------------------------------
- Values are expressed in the **element local coordinate system**.
- Local axis 1 runs from the I end to the J end of the element.
- Local axis 2 lies in the global-Z-up vertical plane containing the
  element axis, pointing "upward" (positive global Z component).
  Horizontal elements get the standard CSI default local 2.
- Local axis 3 is the cross product 1 x 2 (right-handed frame).
- Sign conventions:
    * ``Fx`` — axial force; tension positive, compression negative.
    * ``Fy`` — shear acting in the +local-2 direction on the J-end
      face is positive.
    * ``Fz`` — shear acting in the +local-3 direction on the J-end
      face is positive.
    * ``Mx`` — torque about +local-1 is positive (right-hand rule).
    * ``My`` — bending about +local-2 is positive (right-hand rule);
      this is the "weak-axis" bending for most bridge girders.
    * ``Mz`` — bending about +local-3 is positive (right-hand rule);
      sagging of a simply-supported beam under gravity produces
      positive ``Mz`` at mid-span.

Displacement components (`NodalDisplacement`)
---------------------------------------------
- Values are expressed in the **global coordinate system** (X, Y, Z).
- ``UX``/``UY``/``UZ`` are translations along the global axes.
- ``RX``/``RY``/``RZ`` are rotations about the global axes in radians
  (right-hand rule). Degrees are forbidden: the importer must convert.
- Calculators that need displacements in a member-local frame are
  responsible for transforming from global themselves using the
  node's local-axis definition.

Stress points (`StressPoint` / `ElementStress`)
-----------------------------------------------
- ``y`` and ``z`` are cross-section coordinates in the element local
  2 and 3 directions respectively, measured from the section centroid.
- ``sigma`` is normal stress along the element axis; tension positive.

Importer responsibility
-----------------------
If a source program disagrees with any of the above by default (for
example, uses global-Z-down, or reports degrees, or flips shear
signs), the importer for that source must perform the transform
before constructing the primitive. The normalized layer does no
implicit conversion.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Tuple

import pint

from bda.domain.enums.response_enums import ElementEnd


# ---------------------------------------------------------------------------
# Force primitives
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ForceVector:
    """Local-axis frame forces at a single point.

    See the module docstring for the sign and axis convention. All six
    components are `pint.Quantity`. Fx/Fy/Fz must have dimensions of
    force; Mx/My/Mz must have dimensions of force*length. Dimensional
    correctness is asserted in `__post_init__`.
    """
    Fx: pint.Quantity
    Fy: pint.Quantity
    Fz: pint.Quantity
    Mx: pint.Quantity
    My: pint.Quantity
    Mz: pint.Quantity

    #TODO: zaimplementować jednostko a'la materiały

    def __post_init__(self) -> None:
        if not self.Fx.check("[force]"):
            raise ValueError(f"Fx must have dimensions of [force], got {self.Fx.units}")
        if not self.Fy.check("[force]"):
            raise ValueError(f"Fy must have dimensions of [force], got {self.Fy.units}")
        if not self.Fz.check("[force]"):
            raise ValueError(f"Fz must have dimensions of [force], got {self.Fz.units}")
        if not self.Mx.check("[force] * [length]"):
            raise ValueError(f"Mx must have dimensions of [force]*[length], got {self.Mx.units}")
        if not self.My.check("[force] * [length]"):
            raise ValueError(f"My must have dimensions of [force]*[length], got {self.My.units}")
        if not self.Mz.check("[force] * [length]"):
            raise ValueError(f"Mz must have dimensions of [force]*[length], got {self.Mz.units}")


@dataclass(frozen=True)
class ElementForceEnvelope:
    """Envelope of force results for a single (element, end, load case) key.

    For every component (Fx, Fy, Fz, Mx, My, Mz) we store the maximum and the
    minimum observed value — and with each extreme we keep the full force
    vector from the row that produced it. So `Fx_max` can come from a
    different raw row than `Mz_max`; this matches the per-component
    independent-extremes convention used in the reference
    `Data_normalization/main.py`.

    For a single-valued load case, use `from_single()` to construct a
    degenerate envelope where every `*_max` and `*_min` points at the same
    vector. Then call `updated_with()` for every subsequent row returned by
    the source program.
    """
    element_id: int
    end: ElementEnd
    load_case: str

    Fx_max: ForceVector
    Fx_min: ForceVector
    Fy_max: ForceVector
    Fy_min: ForceVector
    Fz_max: ForceVector
    Fz_min: ForceVector
    Mx_max: ForceVector
    Mx_min: ForceVector
    My_max: ForceVector
    My_min: ForceVector
    Mz_max: ForceVector
    Mz_min: ForceVector

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    @classmethod
    def from_single(
        cls,
        element_id: int,
        end: ElementEnd,
        load_case: str,
        f: ForceVector,
    ) -> "ElementForceEnvelope":
        """Build a degenerate envelope from a single force reading.

        All twelve extremes are set to `f`. Subsequent `updated_with` calls
        will widen the envelope as new rows arrive.
        """
        return cls(
            element_id=element_id,
            end=end,
            load_case=load_case,
            Fx_max=f, Fx_min=f,
            Fy_max=f, Fy_min=f,
            Fz_max=f, Fz_min=f,
            Mx_max=f, Mx_min=f,
            My_max=f, My_min=f,
            Mz_max=f, Mz_min=f,
        )

    # ------------------------------------------------------------------
    # Extension
    # ------------------------------------------------------------------
    def updated_with(self, f: ForceVector) -> "ElementForceEnvelope":
        """Return a new envelope whose per-component extremes include `f`.

        For each of the six force/moment components, if the incoming value
        exceeds the current max (or falls below the current min), the whole
        `ForceVector` `f` is stored as the new extreme — not just that one
        component. This preserves the correlated values of the other
        components at the moment the extreme was observed, which is what
        design checks typically need.
        """
        return replace(
            self,
            Fx_max=f if f.Fx > self.Fx_max.Fx else self.Fx_max,
            Fx_min=f if f.Fx < self.Fx_min.Fx else self.Fx_min,
            Fy_max=f if f.Fy > self.Fy_max.Fy else self.Fy_max,
            Fy_min=f if f.Fy < self.Fy_min.Fy else self.Fy_min,
            Fz_max=f if f.Fz > self.Fz_max.Fz else self.Fz_max,
            Fz_min=f if f.Fz < self.Fz_min.Fz else self.Fz_min,
            Mx_max=f if f.Mx > self.Mx_max.Mx else self.Mx_max,
            Mx_min=f if f.Mx < self.Mx_min.Mx else self.Mx_min,
            My_max=f if f.My > self.My_max.My else self.My_max,
            My_min=f if f.My < self.My_min.My else self.My_min,
            Mz_max=f if f.Mz > self.Mz_max.Mz else self.Mz_max,
            Mz_min=f if f.Mz < self.Mz_min.Mz else self.Mz_min,
        )


# ---------------------------------------------------------------------------
# Displacement primitive
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NodalDisplacement:
    """Global-axis translations and rotations at a single node.

    See the module docstring for the frame convention. Field names are
    deliberately ``UX/UY/UZ`` and ``RX/RY/RZ`` (not ``U1..R3``) to make
    the global-frame assumption impossible to miss at a call site.
    """
    node_id: int
    load_case: str
    UX: pint.Quantity
    UY: pint.Quantity
    UZ: pint.Quantity
    RX: pint.Quantity
    RY: pint.Quantity
    RZ: pint.Quantity

    def __post_init__(self) -> None:
        for name in ("UX", "UY", "UZ"):
            q = getattr(self, name)
            if not q.check("[length]"):
                raise ValueError(
                    f"{name} must have dimensions of [length], got {q.units}"
                )
        for name in ("RX", "RY", "RZ"):
            q = getattr(self, name)
            # Rotations must be explicitly in radians. Importers that
            # encounter degrees in the source program must convert
            # before constructing the primitive.
            if not q.check("radian"):
                raise ValueError(
                    f"{name} must have dimensions of radian, got {q.units}"
                )


@dataclass(frozen=True)
class NodalDisplacementEnvelope:
    """Envelope of displacement results for a single (node, load case) key.

    Mirrors the ``ElementForceEnvelope`` pattern: for every component
    (UX, UY, UZ, RX, RY, RZ) we store the maximum and the minimum
    observed value, and with each extreme we keep the full displacement
    vector from the row that produced it. This means ``UX_max`` can
    come from a different raw row than ``UZ_max``; the per-component
    independent-extremes convention matches what design checks need.

    For a single-valued load case, use ``from_single()`` to build a
    degenerate envelope where every ``*_max`` and ``*_min`` point at the
    same vector. Then call ``updated_with()`` for every subsequent row
    returned by the source program.

    This is needed because combination load cases (CSI: multiple rows per
    station per case with StepType 'Max'/'Min'; Midas: ``(CB:max)`` /
    ``(CB:min)`` suffixes) produce per-component independent extremes.
    Without enveloping, whichever row is processed last silently
    overwrites the other, losing data.
    """
    node_id: int
    load_case: str

    UX_max: NodalDisplacement
    UX_min: NodalDisplacement
    UY_max: NodalDisplacement
    UY_min: NodalDisplacement
    UZ_max: NodalDisplacement
    UZ_min: NodalDisplacement
    RX_max: NodalDisplacement
    RX_min: NodalDisplacement
    RY_max: NodalDisplacement
    RY_min: NodalDisplacement
    RZ_max: NodalDisplacement
    RZ_min: NodalDisplacement

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    @classmethod
    def from_single(
        cls,
        node_id: int,
        load_case: str,
        d: NodalDisplacement,
    ) -> "NodalDisplacementEnvelope":
        """Build a degenerate envelope from a single displacement reading.

        All twelve extremes are set to ``d``. Subsequent ``updated_with``
        calls will widen the envelope as new rows arrive.
        """
        return cls(
            node_id=node_id,
            load_case=load_case,
            UX_max=d, UX_min=d,
            UY_max=d, UY_min=d,
            UZ_max=d, UZ_min=d,
            RX_max=d, RX_min=d,
            RY_max=d, RY_min=d,
            RZ_max=d, RZ_min=d,
        )

    # ------------------------------------------------------------------
    # Extension
    # ------------------------------------------------------------------
    def updated_with(self, d: NodalDisplacement) -> "NodalDisplacementEnvelope":
        """Return a new envelope whose per-component extremes include ``d``.

        For each of the six displacement/rotation components, if the
        incoming value exceeds the current max (or falls below the
        current min), the whole ``NodalDisplacement`` ``d`` is stored as
        the new extreme — preserving the correlated values of the other
        components at the moment the extreme was observed.
        """
        return replace(
            self,
            UX_max=d if d.UX > self.UX_max.UX else self.UX_max,
            UX_min=d if d.UX < self.UX_min.UX else self.UX_min,
            UY_max=d if d.UY > self.UY_max.UY else self.UY_max,
            UY_min=d if d.UY < self.UY_min.UY else self.UY_min,
            UZ_max=d if d.UZ > self.UZ_max.UZ else self.UZ_max,
            UZ_min=d if d.UZ < self.UZ_min.UZ else self.UZ_min,
            RX_max=d if d.RX > self.RX_max.RX else self.RX_max,
            RX_min=d if d.RX < self.RX_min.RX else self.RX_min,
            RY_max=d if d.RY > self.RY_max.RY else self.RY_max,
            RY_min=d if d.RY < self.RY_min.RY else self.RY_min,
            RZ_max=d if d.RZ > self.RZ_max.RZ else self.RZ_max,
            RZ_min=d if d.RZ < self.RZ_min.RZ else self.RZ_min,
        )


# ---------------------------------------------------------------------------
# Stress primitive
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StressPoint:
    """One (y, z, sigma) triplet inside an ElementStress.

    ``y`` and ``z`` are cross-section coordinates in the element local 2
    and 3 directions, measured from the section centroid. ``sigma`` is
    normal stress along the element axis, tension positive.
    """
    y: pint.Quantity
    z: pint.Quantity
    sigma: pint.Quantity

    def __post_init__(self) -> None:
        if not self.y.check("[length]"):
            raise ValueError(f"y must have dimensions of [length], got {self.y.units}")
        if not self.z.check("[length]"):
            raise ValueError(f"z must have dimensions of [length], got {self.z.units}")
        if not self.sigma.check("[pressure]"):
            raise ValueError(f"sigma must have dimensions of [pressure], got {self.sigma.units}")


@dataclass(frozen=True)
class ElementStress:
    """Stress distribution at one end of an element for a single load case."""
    element_id: int
    end: ElementEnd
    load_case: str
    points: Tuple[StressPoint, ...] = field(default_factory=tuple)
