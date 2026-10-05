"""Mapper: DisplacementResultModel → NodalDisplacement (Midas Civil NX).

Applies Pint units to raw float values from the Midas Civil NX intermediate DTO.

NOTE: Midas may return rotations in degrees depending on user settings.
If ``UNIT`` in the POST body does not control rotation units, add a
``math.radians()`` conversion here before constructing ``NodalDisplacement``.
"""
from __future__ import annotations

from bda.contracts.result_models.midas.displacement_result_model import MidasDisplacementResultModel
from bda.domain.results.result_primitives import NodalDisplacement
from bda.infrastructure.utils import CANONICAL_LENGTH, CANONICAL_UNIT_SYSTEM, Q_, ureg


class MidasDisplacementResultMapper:
    """Convert ``DisplacementResultModel`` → ``NodalDisplacement`` for Midas Civil NX results."""

    @staticmethod
    def midas_to_domain(rm: MidasDisplacementResultModel, node_id: int) -> NodalDisplacement:
        """Apply canonical units and return a ``NodalDisplacement``.

        Asserts that ``rm.unit_system`` equals ``CANONICAL_UNIT_SYSTEM``
        before wrapping values in Pint quantities.

        Args:
            rm: Raw displacement values in metres and radians from Midas Civil NX.
            node_id: Domain-layer integer node ID (separate from the FEM
                node name stored in the DTO).

        Raises:
            AssertionError: If the result model was built under a
                non-canonical unit system.
        """
        assert rm.unit_system == CANONICAL_UNIT_SYSTEM, (
            f"DisplacementResultModel unit_system must be {CANONICAL_UNIT_SYSTEM!r}, "
            f"got {rm.unit_system!r}. Ensure the Midas fetcher sets canonical units "
            "before reading from the FEM API."
        )
        return NodalDisplacement(
            node_id=node_id,
            load_case=rm.load_case,
            UX=Q_(rm.ux, CANONICAL_LENGTH),
            UY=Q_(rm.uy, CANONICAL_LENGTH),
            UZ=Q_(rm.uz, CANONICAL_LENGTH),
            RX=Q_(rm.rx, ureg.radian),
            RY=Q_(rm.ry, ureg.radian),
            RZ=Q_(rm.rz, ureg.radian),
        )
