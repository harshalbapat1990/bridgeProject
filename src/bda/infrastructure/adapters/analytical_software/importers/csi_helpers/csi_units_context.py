"""Context manager that forces CSI Bridge into canonical units for a fetch.

CSI Bridge exposes a single global "present units" setting via
`SapModel.GetPresentUnits` / `SetPresentUnits`. Every numeric returned
by the OAPI is interpreted in that unit system. To keep the importer
simple and deterministic, we always switch to a known canonical code
for the duration of a fetch, then restore whatever the user had before.

The canonical choice is kN, m, C (CSI unit code 6). Numbers that leave
the fetchers are immediately wrapped in `pint.Quantity` using the
matching canonical unit from `infrastructure.utils.units`, so the rest
of the pipeline never has to think about raw unit codes again.
"""
from __future__ import annotations

from typing import Any

from bda.infrastructure.utils import CSI_UNIT_CODE_KN_M_C


class CsiUnitsContext:
    """Temporarily set CSI's present units to the canonical code.

    Usage:
        with CsiUnitsContext(sap_model):
            # every OAPI numeric returned here is in kN, m, C
            ...

    On `__exit__` the previous unit code is restored even if an
    exception was raised inside the block.
    """

    def __init__(self, sap_model: Any, target_code: int = CSI_UNIT_CODE_KN_M_C) -> None:
        """Store a reference to the CSI SapModel and the target unit code."""
        self._sap_model = sap_model
        self._target_code = target_code
        self._previous_code: int | None = None

    def __enter__(self) -> "CsiUnitsContext":
        """Capture the current unit code and switch to the canonical code."""
        self._previous_code = self._sap_model.GetPresentUnits()
        self._sap_model.SetPresentUnits(self._target_code)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Restore the previously stored unit code, ignoring restore errors."""
        if self._previous_code is not None:
            try:
                self._sap_model.SetPresentUnits(self._previous_code)
            except Exception:
                # Ignore restore errors; the best effort has been made.
                pass
