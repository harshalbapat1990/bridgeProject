"""Mapper: ForceResultModel → ForceVector domain object.

Applies Pint units to raw float values from the FEM API intermediate DTO.
This is the POST-pipeline equivalent of the PRE material/section mappers.
"""
from __future__ import annotations

from bda.contracts.result_models.force_result_model import ForceResultModel
from bda.domain.results.result_primitives import ForceVector
from bda.infrastructure.utils import CANONICAL_FORCE, CANONICAL_MOMENT, CANONICAL_UNIT_SYSTEM, Q_


class ForceResultMapper:
    """Convert `ForceResultModel` → `ForceVector`."""

    @staticmethod
    def to_domain(rm: ForceResultModel) -> ForceVector:
        """Apply canonical units and return a `ForceVector`.

        Asserts that `rm.unit_system` equals ``CANONICAL_UNIT_SYSTEM``
        before wrapping values in Pint quantities. This guards against a
        fetcher that forgets to set the FEM session to canonical units.

        Raises:
            AssertionError: If the result model was built under a
                non-canonical unit system.
        """
        assert rm.unit_system == CANONICAL_UNIT_SYSTEM, (
            f"ForceResultModel unit_system must be {CANONICAL_UNIT_SYSTEM!r}, "
            f"got {rm.unit_system!r}. Ensure the fetcher sets canonical units "
            "before reading from the FEM API."
        )
        return ForceVector(
            Fx=Q_(rm.axial,    CANONICAL_FORCE),
            Fy=Q_(rm.shear_y,  CANONICAL_FORCE),
            Fz=Q_(rm.shear_z,  CANONICAL_FORCE),
            Mx=Q_(rm.torsion,  CANONICAL_MOMENT),
            My=Q_(rm.moment_y, CANONICAL_MOMENT),
            Mz=Q_(rm.moment_z, CANONICAL_MOMENT),
        )
