"""Fetch element fiber stresses from CSI Bridge.

Stresses are calculator-specific: some checks need the extreme fiber
stress at a handful of (y, z) points on a cross-section. CSI does not
return these directly for frames — the fetcher computes them from the
frame forces and the section geometry, or it reads them from an area /
shell result API for shell elements.

The scaffold only defines the entry point; the detailing pass will
decide whether to derive fiber stresses from forces+section or to call
a dedicated CSI API depending on the element kind.
"""
from __future__ import annotations

from typing import Any

from bda.domain.results.data_request import DataRequest
from bda.domain.results.result_set import ResultSet
from bda.infrastructure.adapters.analytical_software.importers.csi_helpers.csi_id_mapper import CsiIdMapper


class CsiStressesFetcher:
    """Produce `ElementStress` records and deposit them in a ResultSet."""

    def __init__(self, sap_model: Any, id_mapper: CsiIdMapper) -> None:
        self._sap_model = sap_model
        self._id_mapper = id_mapper

    def fetch_into(self, request: DataRequest, result_set: ResultSet) -> None:
        """Fetch stresses for every (element, load case) in `request`.

        Deposits one `ElementStress` per (element_id, end, load_case)
        into `result_set` via `put_stress`.

        TODO: Implement stress extraction using one of two strategies:

        1. Derived stresses (for frame elements):
           - Load element forces via `Results.FrameForce` (already available).
           - Fetch section geometry and material properties.
           - Compute bending stresses at extreme fibers using section
             properties (Iyy, Izz, Syy, Szz) and neutral-axis distances.
           - Combine with axial stress (N / A) to get envelope per fiber point.

        2. Direct shell/area stresses (for 2D elements):
           - Call `Results.AreaStress` (if available in CSI Bridge OAPI).
           - Extract membrane and bending stresses per element.
           - Map to fiber points based on shell cross-section definition.

        Decision: Which element types (frame vs. shell) does the current
        calculator need? Start with frame-derived (1) if only beams are
        used; add shell direct fetch (2) only if needed.
        """
        raise NotImplementedError(
            "CsiStressesFetcher.fetch_into — not yet implemented. "
            "See docstring for design options (frame-derived vs. shell-direct)."
        )
