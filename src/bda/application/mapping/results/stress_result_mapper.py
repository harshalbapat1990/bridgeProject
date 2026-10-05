"""Mapper: StressResultModel → ElementStress domain object.

Applies Pint units to raw float values from the FEM API intermediate DTO.
Software-agnostic: both Midas and CSI Bridge fetchers produce the same
`StressResultModel`; this single mapper handles both.
"""
from __future__ import annotations

from bda.contracts.result_models.stress_result_model import StressResultModel
from bda.domain.enums.response_enums import ElementEnd
from bda.domain.results.result_primitives import ElementStress, StressPoint
from bda.infrastructure.utils import CANONICAL_LENGTH, CANONICAL_STRESS, CANONICAL_UNIT_SYSTEM, Q_, ureg

# Midas returns stress in kN/m² when UNIT={"FORCE":"kN", "DIST":"m"}.
# CSI Bridge returns stress in kN/m² when SetPresentUnits(6) (kN·m·C) is active.
# Both fetchers store sigma as kN/m²; this unit string handles the conversion to MPa.
_STRESS_INPUT_UNIT = ureg.kilonewton / ureg.meter ** 2   # kN/m² = kPa


class StressResultMapper:
    """Convert `StressResultModel` → `ElementStress`."""

    @staticmethod
    def to_domain(rm: StressResultModel, element_id: int) -> ElementStress:
        """Apply canonical units and return an `ElementStress`.

        Asserts that `rm.unit_system` equals ``CANONICAL_UNIT_SYSTEM``
        before wrapping values in Pint quantities.

        Args:
            rm: Raw stress data — fiber coordinates in metres, stress
                values in kN/m² (canonical Midas/CSI Bridge output).
            element_id: Domain-layer integer element ID (separate from
                the FEM element name stored in the DTO).

        Returns:
            ``ElementStress`` with all values as Pint quantities in
            canonical units (stress in MPa, length in m).

        Raises:
            AssertionError: If the result model was built under a
                non-canonical unit system.
            ValueError: If ``rm.part`` is not ``'I'`` or ``'J'``.
        """
        assert rm.unit_system == CANONICAL_UNIT_SYSTEM, (
            f"StressResultModel unit_system must be {CANONICAL_UNIT_SYSTEM!r}, "
            f"got {rm.unit_system!r}. Ensure the fetcher sets canonical units "
            "before reading from the FEM API."
        )

        if rm.part == "I":
            end = ElementEnd.I
        elif rm.part == "J":
            end = ElementEnd.J
        else:
            raise ValueError(
                f"StressResultModel.part must be 'I' or 'J', got {rm.part!r}"
            )

        points = tuple(
            StressPoint(
                y=Q_(y_m, CANONICAL_LENGTH),
                z=Q_(z_m, CANONICAL_LENGTH),
                sigma=Q_(sigma_raw, _STRESS_INPUT_UNIT).to(CANONICAL_STRESS),
            )
            for y_m, z_m, sigma_raw in rm.stress_points
        )

        return ElementStress(
            element_id=element_id,
            end=end,
            load_case=rm.load_case,
            points=points,
        )
