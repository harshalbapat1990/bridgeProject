"""Fetch frame-element forces from CSI Bridge and build envelopes.

This is the most delicate fetcher because:

1. CSI's `Results.FrameForce(name, itemType)` returns a tuple where
   the confirmed index layout (verified against live CSI Bridge data,
   2026-04-09) is:

        info[0]  = count
        info[1]  = Obj[]      parent object names
        info[2]  = ObjSta[]   station along parent object
        info[3]  = Elm[]      element names (may differ from Obj for meshed objects)
        info[4]  = ElmSta[]   station along element  ← USE THIS for I/J classification
        info[5]  = LoadCase[]
        info[6]  = StepType[]
        info[7]  = StepNum[]
        info[8]  = P[]   → Fx   (axial)
        info[9]  = V2[]  → Fy   (shear in CSI local-2, vertical for standard girder)
        info[10] = V3[]  → Fz   (shear in CSI local-3, out-of-plane)
        info[11] = T[]   → Mx   (torsion)
        info[12] = M2[]  → My   (bending about local-2, weak-axis for standard girder)
        info[13] = M3[]  → Mz   (bending about local-3, major/sagging for standard girder)
        info[14] = ret

   CSI's local axes for a horizontal bridge girder:
     local-1 = along the element (I→J)
     local-2 = vertical (global-Z component is positive by default)
     local-3 = horizontal transverse (right-hand rule: 1×2)

   The domain `ForceVector` uses the same local-axis convention, so the
   mapping is 1-to-1 with no swaps required for standard CSI Bridge
   orientation.  An importer for a model with a non-standard local-axis
   definition would need to rotate/swap before constructing ForceVector.

   The fetcher must encapsulate this mapping; everything downstream
   sees the canonical `(Fx, Fy, Fz, Mx, My, Mz)` order via `ForceVector`.

2. We only keep station ~ 0.0 (I end) and station ~ element_length
   (J end). Intermediate stations are discarded.

3. For every (element_id, end, load_case) triple we build an
   `ElementForceEnvelope`. A single-valued load case yields a
   degenerate envelope via `ElementForceEnvelope.from_single`; a true
   envelope case widens the envelope via `updated_with` per component.
"""
from __future__ import annotations

import logging
from typing import Any, Iterable

from bda.application.mapping.results.force_result_mapper import ForceResultMapper
from bda.contracts.result_models.force_result_model import ForceResultModel
from bda.domain.enums.response_enums import ElementEnd
from bda.infrastructure.utils import CANONICAL_UNIT_SYSTEM
from bda.domain.results.data_request import DataRequest
from bda.domain.results.result_primitives import (
    ElementForceEnvelope,
    ForceVector,
)
from bda.domain.results.result_set import ResultSet
from bda.infrastructure.adapters.analytical_software.importers.csi_helpers.csi_id_mapper import CsiIdMapper
from bda.infrastructure.adapters.analytical_software.importers.csi_helpers.csi_load_case_resolver import (
    CsiLoadCaseResolver,
)

logger = logging.getLogger(__name__)


# Tolerance (in canonical length units, i.e. meters) for deciding
# whether a station belongs to the I end or the J end of a frame.
_END_TOLERANCE_M: float = 1.0e-4


class CsiForcesFetcher:
    """Pull frame forces from CSI and deposit envelopes into a ResultSet."""

    def __init__(
        self,
        sap_model: Any,
        id_mapper: CsiIdMapper,
        load_case_resolver: CsiLoadCaseResolver,
    ) -> None:
        self._sap_model = sap_model
        self._id_mapper = id_mapper
        self._load_case_resolver = load_case_resolver
        self._element_length_cache: dict[str, float] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def fetch_into(self, request: DataRequest, result_set: ResultSet) -> None:
        """Fetch forces for every (element, load case) in `request`.

        Deposits one `ElementForceEnvelope` per (element_id, end,
        load_case) into `result_set` using `put_force_envelope` (which
        widens on collision).

        Args:
            request: Must contain `element_ids` and `force_loadcases`.
            result_set: Mutated in place.
        """
        requested_load_cases = set(request.force_loadcases)

        for element_id in self._iter_requested_elements(request):
            # Resolve element ID to CSI name
            try:
                element_name = self._id_mapper.element_name(element_id)
            except KeyError:
                logger.warning(f"Element ID {element_id} not found in mapper")
                continue

            # Get element length by fetching the two endpoint names
            try:
                element_length = self._get_element_length(element_name)
            except Exception as e:
                logger.warning(
                    f"Could not compute element length for '{element_name}': {e}"
                )
                continue

            # Call CSI API to fetch forces (returns a tuple)
            try:
                info = self._sap_model.Results.FrameForce(element_name, 0)
            except Exception as e:
                logger.warning(f"CSI FrameForce call failed for '{element_name}': {e}")
                continue

            count = info[0]
            logger.info(
                "  FrameForce('%s'): %d rows returned", element_name, count
            )
            if count == 0:
                logger.warning(
                    "  FrameForce('%s') returned 0 rows — load case not "
                    "enabled for output, or analysis not run.", element_name
                )
                continue

            # info[2] = ObjSta (station along the parent object — can be
            # offset if the object is internally meshed).
            # info[4] = ElmSta (station along THIS element, always 0..L).
            # Always use ElmSta so the I/J classification works correctly.
            elem_names  = info[1]
            stations    = info[4]   # ElmSta — was info[2] (ObjSta), which
                                    # breaks for meshed objects
            load_cases  = info[5]
            step_types  = info[6]
            # Force components at indices 8-13 (confirmed 2026-04-09).
            # No axis swap required — CSI Bridge local-2/3 match the domain
            # Fy/Fz and My/Mz naming for standard horizontal girder orientation.
            forces_fx = info[8]   # P   (axial)          → domain Fx
            forces_fy = info[9]   # V2  (vertical shear) → domain Fy
            forces_fz = info[10]  # V3  (out-of-plane)   → domain Fz
            forces_mx = info[11]  # T   (torsion)        → domain Mx
            forces_my = info[12]  # M2  (weak-axis)      → domain My
            forces_mz = info[13]  # M3  (major/sagging)  → domain Mz

            # Log a sample of the first row so mismatches are visible.
            if count > 0:
                logger.info(
                    "  First row: lc='%s' step='%s' ElmSta=%.4f "
                    "(element_length=%.4f) Fx=%.4f Mz=%.4f",
                    load_cases[0], step_types[0], stations[0],
                    element_length, forces_fx[0], forces_mz[0],
                )

            kept = 0
            skipped_lc = 0
            skipped_sta = 0

            # Iterate through results
            for j in range(count):
                lc = load_cases[j]

                # Skip if this load case was not requested
                if lc not in requested_load_cases:
                    skipped_lc += 1
                    continue

                # Classify station as I end, J end, or neither
                station = stations[j]
                end = self._classify_station(station, element_length)

                # Skip if station is not at an element end
                if end is None:
                    skipped_sta += 1
                    continue

                # Build force vector via ResultModel → mapper (POST pipeline pattern)
                result_model = ForceResultModel(
                    element_name=element_name,
                    load_case=lc,
                    step_type=step_types[j],
                    elm_station=station,
                    axial=forces_fx[j],
                    shear_y=forces_fy[j],
                    shear_z=forces_fz[j],
                    torsion=forces_mx[j],
                    moment_y=forces_my[j],
                    moment_z=forces_mz[j],
                    unit_system=CANONICAL_UNIT_SYSTEM,
                )
                force_vec = ForceResultMapper.to_domain(result_model)

                logger.info(
                    "  Kept: elem=%s end=%s lc='%s' sta=%.4f "
                    "Fx=%.4f Fy=%.4f Fz=%.4f Mx=%.4f My=%.4f Mz=%.4f",
                    element_name, end.name, lc, station,
                    forces_fx[j], forces_fy[j], forces_fz[j],
                    forces_mx[j], forces_my[j], forces_mz[j],
                )

                # Build a degenerate envelope from this row and hand it to
                # the ResultSet; `put_force_envelope` widens on collision,
                # so per-component extremes across rows are handled for us.
                envelope = self._initial_envelope(
                    element_id=element_id,
                    end=end,
                    load_case=lc,
                    first=force_vec,
                )
                result_set.add_force_envelope(envelope)
                kept += 1

            logger.info(
                "  '%s': kept=%d  skipped(lc)=%d  skipped(station)=%d",
                element_name, kept, skipped_lc, skipped_sta,
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _classify_station(
        station: float, element_length: float
    ) -> ElementEnd | None:
        """Return I, J or None depending on where the station sits."""
        if abs(station) <= _END_TOLERANCE_M:
            return ElementEnd.I
        if abs(station - element_length) <= _END_TOLERANCE_M:
            return ElementEnd.J
        return None

    @staticmethod
    def _initial_envelope(
        element_id: int,
        end: ElementEnd,
        load_case: str,
        first: ForceVector,
    ) -> ElementForceEnvelope:
        """Seed a degenerate envelope from the first observed row."""
        return ElementForceEnvelope.from_single(
            element_id=element_id,
            end=end,
            load_case=load_case,
            f=first,
        )

    @staticmethod
    def _iter_requested_elements(request: DataRequest) -> Iterable[int]:
        """Yield element ids for which forces were requested."""
        return iter(request.element_ids)

    def _get_element_length(self, element_name: str) -> float:
        """Compute and cache the length of a frame element.

        Uses GetPoints to fetch endpoint names, then GetCoordCartesian
        for each endpoint, and returns the Euclidean distance.
        """
        if element_name in self._element_length_cache:
            return self._element_length_cache[element_name]

        # Get the two point names
        points_result = self._sap_model.FrameObj.GetPoints(element_name)
        point_i_name = points_result[0]
        point_j_name = points_result[1]

        # Get coordinates for each point
        coord_i = self._sap_model.PointObj.GetCoordCartesian(point_i_name)
        coord_j = self._sap_model.PointObj.GetCoordCartesian(point_j_name)

        # Compute Euclidean distance
        dx = coord_j[0] - coord_i[0]
        dy = coord_j[1] - coord_i[1]
        dz = coord_j[2] - coord_i[2]
        length = (dx**2 + dy**2 + dz**2) ** 0.5

        self._element_length_cache[element_name] = length
        return length
