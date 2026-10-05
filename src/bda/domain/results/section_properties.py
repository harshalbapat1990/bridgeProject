"""Section geometric properties — computed by FEM software after analysis.

`SectionProperties` is a domain Value Object that holds the computed
cross-sectional properties for a named section, as returned by the FEM
software (Midas Civil, CSI Bridge). These are distinct from the section
*definition* (geometry, material) stored in `SectionBase` — they are
derived quantities that the FEM solver computes from the definition.

All quantities are `pint.Quantity` objects in SI units.
"""
from __future__ import annotations

from dataclasses import dataclass

import pint

from bda.infrastructure.utils import Q_, ureg

# Derived unit aliases for readability
_m2 = ureg.meter ** 2
_m4 = ureg.meter ** 4
_m3 = ureg.meter ** 3
_m  = ureg.meter


@dataclass(frozen=True)
class SectionProperties:
    """Computed cross-sectional properties for one named section.

    All numeric fields are `pint.Quantity` objects.

    Attributes
    ----------
    name:
        Section name matching the FEM model definition.
    area:
        Cross-sectional area A (m²).
    shear_area_y:
        Effective shear area in the local-2 direction Asy (m²).
    shear_area_z:
        Effective shear area in the local-3 direction Asz (m²).
    torsional_inertia:
        Torsional constant J (m⁴).
    moment_inertia_y:
        Second moment of area about local-2 Iyy (m⁴). Weak-axis.
    moment_inertia_z:
        Second moment of area about local-3 Izz (m⁴). Major axis.
    czp:
        Distance from centroid to +local-3 extreme fibre (m).
        Elastic section modulus: Wz+ = Izz / czp.
    czm:
        Distance from centroid to -local-3 extreme fibre (m).
    cyp:
        Distance from centroid to +local-2 extreme fibre (m).
    cym:
        Distance from centroid to -local-2 extreme fibre (m).
    """

    name: str
    area: pint.Quantity           # m²
    shear_area_y: pint.Quantity   # m²
    shear_area_z: pint.Quantity   # m²
    torsional_inertia: pint.Quantity  # m⁴
    moment_inertia_y: pint.Quantity   # m⁴
    moment_inertia_z: pint.Quantity   # m⁴
    czp: pint.Quantity            # m
    czm: pint.Quantity            # m
    cyp: pint.Quantity            # m
    cym: pint.Quantity            # m

    # ------------------------------------------------------------------
    # Derived properties (computed from stored quantities)
    # ------------------------------------------------------------------

    @property
    def elastic_modulus_z_pos(self) -> pint.Quantity:
        """Elastic section modulus about local-3, positive side (m³)."""
        return self.moment_inertia_z / self.czp

    @property
    def elastic_modulus_z_neg(self) -> pint.Quantity:
        """Elastic section modulus about local-3, negative side (m³)."""
        return self.moment_inertia_z / self.czm

    @property
    def elastic_modulus_y_pos(self) -> pint.Quantity:
        """Elastic section modulus about local-2, positive side (m³)."""
        return self.moment_inertia_y / self.cyp

    @property
    def elastic_modulus_y_neg(self) -> pint.Quantity:
        """Elastic section modulus about local-2, negative side (m³)."""
        return self.moment_inertia_y / self.cym
