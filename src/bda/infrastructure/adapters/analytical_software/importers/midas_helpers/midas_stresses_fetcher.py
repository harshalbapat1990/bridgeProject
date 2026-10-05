"""Fetch element stresses from Midas Civil NX.

Uses ``POST /post/TABLE`` with a stress table type. The exact
``TABLE_TYPE`` value for beam stresses has not yet been confirmed
against a live Midas session_manager.

Candidate TABLE_TYPE values (to be tested):
    - ``"BEAMSTRESS"``
    - ``"BEAMSTRSVBM"``

Midas Civil NX reports stresses at configurable points on the
cross-section. The fetcher must map these to ``StressPoint(y, z, sigma)``
tuples where ``y`` and ``z`` are local-2 and local-3 distances from
the section centroid.

CB:max/CB:min for stresses: TBD — must be verified against a live
session_manager. The current implementation assumes the same suffix convention
as forces.

NOTE: The CSI Bridge stress fetcher is also a scaffold (not yet
implemented), so the Midas stress fetcher mirrors that status: it
provides a complete structural skeleton that can be wired into the
orchestrator, with the actual response parsing ready to fill in once
the endpoint is confirmed.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from bda.domain.results.data_request import DataRequest
from bda.domain.results.result_set import ResultSet
from bda.infrastructure.adapters.analytical_software.importers.midas_helpers.midas_id_mapper import MidasIdMapper
from bda.infrastructure.adapters.analytical_software.importers.midas_helpers.midas_load_case_resolver import (
    MidasLoadCaseResolver,
)
from bda.infrastructure.adapters.analytical_software.exporters.midas_helpers.MidasAPI import MidasAPI
from bda.application.mapping.results.stress_result_mapper import StressResultMapper
from bda.contracts.result_models.stress_result_model import StressResultModel
from bda.infrastructure.utils import CANONICAL_UNIT_SYSTEM

logger = logging.getLogger(__name__)

# Canonical units for the POST body.
MIDAS_CANONICAL_UNIT = {"FORCE": "kN", "DIST": "m"}

# TABLE_TYPE for stresses — to be confirmed against live session_manager.
STRESS_TABLE_TYPE = "BEAMSTRESS"


class MidasStressesFetcher:
    """Pull element stresses from Midas and deposit them in a ResultSet."""

    def __init__(
        self,
        api: MidasAPI,
        id_mapper: MidasIdMapper,
        load_case_resolver: Optional[MidasLoadCaseResolver] = None,
    ) -> None:
        self._api = api
        self._id_mapper = id_mapper
        self._load_case_resolver = load_case_resolver

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def fetch_into(self, request: DataRequest, result_set: ResultSet) -> None:
        """Fetch stresses for every (element, load case) in ``request``.

        Deposits one ``ElementStress`` per (element_id, end, load_case)
        into ``result_set`` via ``put_stress``.

        Args:
            request: Must contain ``element_ids`` and ``stress_loadcases``.
            result_set: Mutated in place.

        TODO: Complete response parsing once the following are confirmed
        against a live Midas session_manager:
            1. The correct TABLE_TYPE string.
            2. The response column layout (which indices hold element id,
               load case, part, and the stress values).
            3. Whether Midas returns fiber-point coordinates (y, z) or
               just top/bottom extreme fiber values.
            4. Whether (CB:max)/(CB:min) applies to stress tables.

        Design options (same as CSI stress fetcher):
            1. Direct stress API: If Midas returns fiber stresses with
               (y, z) coordinates, map directly to StressPoint tuples.
            2. Derived stresses: If Midas only returns forces, derive
               fiber stresses from forces + section properties.
        """
        element_keys = self._resolve_element_keys(request)
        if not element_keys:
            logger.warning("No valid element keys to fetch stresses for")
            return

        lc_names = self._build_load_case_names(request)
        if not lc_names:
            logger.warning("No load case names to fetch stresses for")
            return

        body = self._build_request_body(element_keys, lc_names)

        try:
            resp = self._api.request("POST", "/post/TABLE", body)
            resp_data = resp.json()
        except Exception as e:
            logger.error("Midas /post/TABLE (stresses) call failed: %s", e)
            raise RuntimeError(
                f"Failed to fetch stresses from Midas: {e}"
            )

        self._parse_response(resp_data, request, result_set)

    # ------------------------------------------------------------------
    # Request building
    # ------------------------------------------------------------------
    def _resolve_element_keys(self, request: DataRequest) -> List[int]:
        """Validate and return element ids that exist in the Midas model."""
        valid_keys = []
        for eid in request.element_ids:
            try:
                self._id_mapper.validate_element(eid)
                valid_keys.append(eid)
            except KeyError:
                logger.warning(
                    "Element ID %d not found in Midas model, skipping", eid
                )
        return valid_keys

    def _build_load_case_names(self, request: DataRequest) -> List[str]:
        """Build load case names — TBD whether suffixes apply to stresses.

        NOTE — same LC limitations as ``MidasForcesFetcher``:
            - Non-CB combination types may use different suffix conventions.
            - Static load cases may behave differently depending on
              analysis type. Needs live verification.
        """
        lc_names: List[str] = []
        for lc in sorted(request.stress_loadcases):
            if (self._load_case_resolver is not None
                    and self._load_case_resolver.is_combination(lc)):
                lc_names.append(f"{lc}(CB:max)")
                lc_names.append(f"{lc}(CB:min)")
            else:
                lc_names.append(lc)
                lc_names.append(f"{lc}(CB:max)")
                lc_names.append(f"{lc}(CB:min)")
        return lc_names

    @staticmethod
    def _build_request_body(
        element_keys: List[int], lc_names: List[str]
    ) -> Dict[str, Any]:
        """Construct the JSON body for ``POST /post/TABLE`` (stresses).

        NOTE: COMPONENTS and ITEM_TO_DISPLAY must be adjusted once the
        actual response columns are confirmed.
        """
        return {
            "TABLE_TYPE": STRESS_TABLE_TYPE,
            "UNIT": MIDAS_CANONICAL_UNIT,
            "STYLES": {"FORMAT": "Fixed", "PLACE": 12},
            "COMPONENTS": [
                "Elem", "Load", "Part",
                "Sigma-xx",
            ],
            "NODE_ELEMS": {"KEYS": element_keys},
            "LOAD_CASE_NAMES": lc_names,
            "PARTS": ["PartI", "PartJ"],
            "ITEM_TO_DISPLAY": [
                "Sigma-xx",
            ],
        }

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------
    def _parse_response(
        self,
        resp_data: Dict[str, Any],
        request: DataRequest,
        result_set: ResultSet,
    ) -> None:
        """Walk the response rows and deposit element stresses.

        Current implementation provides a structural skeleton. The column
        index mapping should be adjusted once the actual Midas response
        format is confirmed.
        """
        requested_lcs = set(request.stress_loadcases)

        data_rows = self._extract_data_rows(resp_data)
        if data_rows is None:
            logger.warning(
                "No stress data returned from Midas "
                "(TABLE_TYPE='%s' may need adjustment)", STRESS_TABLE_TYPE
            )
            return

        kept = 0
        skipped_lc = 0

        for row in data_rows:
            try:
                element_id = int(row[1])
                raw_lc = str(row[2])
                part_str = str(row[3])

                lc = self._strip_combo_suffix(raw_lc)
                if lc not in requested_lcs:
                    skipped_lc += 1
                    continue

                part = self._classify_part(part_str)
                if part is None:
                    continue

                # Build stress via ResultModel → mapper (POST pipeline pattern)
                result_model = StressResultModel(
                    element_name=str(element_id),
                    load_case=lc,
                    step_type="Max" if "(CB:max)" in raw_lc else ("Min" if "(CB:min)" in raw_lc else None),
                    part=part,
                    stress_points=self._extract_stress_points(row),
                    unit_system=CANONICAL_UNIT_SYSTEM,
                )
                stress = StressResultMapper.to_domain(result_model, element_id=element_id)

                result_set.add_stress(stress)
                kept += 1

            except (IndexError, ValueError) as e:
                logger.warning(
                    "Skipping malformed stress row: %s — %s", row, e
                )
                continue

        logger.info(
            "MidasStressesFetcher: kept=%d skipped(lc)=%d",
            kept, skipped_lc,
        )

    @staticmethod
    def _extract_data_rows(
        resp_data: Dict[str, Any],
    ) -> Optional[List[List[Any]]]:
        """Find the DATA list in the response."""
        for key, value in resp_data.items():
            if isinstance(value, dict) and "DATA" in value:
                return value["DATA"]
        if "DATA" in resp_data:
            return resp_data["DATA"]
        return None

    @staticmethod
    def _strip_combo_suffix(raw_lc: str) -> str:
        """Strip ``(CB:max)`` or ``(CB:min)`` from a load case name."""
        paren_idx = raw_lc.find("(")
        if paren_idx > 0:
            return raw_lc[:paren_idx]
        return raw_lc

    @staticmethod
    def _classify_part(part_str: str) -> Optional[str]:
        """Map a Midas part string to ``'I'`` or ``'J'``, or ``None``.

        Returns a plain string (not ``ElementEnd``) so the result model
        stays free of domain types. The mapper performs the final
        ``str → ElementEnd`` conversion.
        """
        part_upper = part_str.strip().upper()
        if part_upper.startswith("I") or part_upper == "PARTI":
            return "I"
        if part_upper.startswith("J") or part_upper == "PARTJ":
            return "J"
        return None

    # ------------------------------------------------------------------
    # Stress point extraction
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_stress_points(
        row: List[Any],
    ) -> tuple[tuple[float, float, float], ...]:
        """Extract fiber stress points from a single response row.

        Returns a tuple of ``(y_m, z_m, sigma_kN_per_m2)`` triples.

        TODO: Adjust column indices once the actual Midas response
        format is confirmed (TABLE_TYPE ``"BEAMSTRESS"`` or
        ``"BEAMSTRSVBM"``). The current implementation produces a
        single centroid point (y=0, z=0) using the first available
        stress column (index 4). Once Midas returns fibre-point
        coordinates (y, z), extract all of them here.
        """
        sigma_raw = float(row[4]) if len(row) > 4 else 0.0
        # Single centroid point as placeholder; replace with multi-point
        # extraction once the response layout is confirmed.
        return ((0.0, 0.0, sigma_raw),)
