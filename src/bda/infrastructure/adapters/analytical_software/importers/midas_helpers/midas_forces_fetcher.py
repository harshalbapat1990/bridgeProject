"""Fetch frame-element forces from Midas Civil NX and build envelopes.

Uses ``POST /post/TABLE`` with ``TABLE_TYPE: "BEAMFORCEVBM"`` to retrieve
beam forces. This endpoint is confirmed from the working Example1 code
(``get_beam_forces`` in ``Analytical_model.py``).

Response layout (confirmed from Example1):
    Each row in ``response[table_key]["DATA"]``:
        row[0]  = row number (auto-generated)
        row[1]  = element key (int as string, e.g. "1")
        row[2]  = load case name (e.g. "ULS_gr5(CB:max)")
        row[3]  = part indicator ("I" or "J" end, e.g. "PartI")
        row[4]  = component (unused in force-only fetch)
        row[5]  = Axial       -> domain Fx
        row[6]  = Shear-y     -> domain Fy
        row[7]  = Shear-z     -> domain Fz
        row[8]  = Torsion     -> domain Mx
        row[9]  = Moment-y    -> domain My
        row[10] = Moment-z    -> domain Mz

Envelope handling:
    Midas appends ``(CB:max)`` / ``(CB:min)`` suffixes to combination
    load cases. The fetcher strips the suffix to get the bare name for
    the ``ResultSet`` key, then feeds both max and min rows into
    ``ElementForceEnvelope`` via ``put_force_envelope`` (which widens
    on collision).

Sign convention:
    The mapping from Midas force columns to the domain ``ForceVector``
    assumes that Midas's local-axis conventions match the domain conventions
    documented in ``result_primitives.py``. If the cross-program validation
    test (Phase 4) reveals sign disagreements, a sign-flip transform should
    be added to ``_build_force_vector``.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from bda.domain.enums.response_enums import ElementEnd
from bda.domain.results.data_request import DataRequest
from bda.domain.results.result_primitives import (
    ElementForceEnvelope,
    ForceVector,
)
from bda.domain.results.result_set import ResultSet
from bda.infrastructure.adapters.analytical_software.importers.midas_helpers.midas_id_mapper import MidasIdMapper
from bda.infrastructure.adapters.analytical_software.importers.midas_helpers.midas_load_case_resolver import (
    MidasLoadCaseResolver,
)
from bda.application.mapping.results.force_result_mapper import ForceResultMapper
from bda.contracts.result_models.force_result_model import ForceResultModel
from bda.infrastructure.adapters.analytical_software.exporters.midas_helpers.MidasAPI import MidasAPI
from bda.infrastructure.utils import CANONICAL_UNIT_SYSTEM

logger = logging.getLogger(__name__)

# Canonical units to request from the Midas API.
# These are passed in the POST body — no need to change the model's units.
MIDAS_CANONICAL_UNIT = {"FORCE": "kN", "DIST": "m"}


class MidasForcesFetcher:
    """Pull beam forces from Midas Civil NX and deposit envelopes into a ResultSet."""

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
        """Fetch forces for every (element, load case) in ``request``.

        Deposits one ``ElementForceEnvelope`` per (element_id, end,
        load_case) into ``result_set`` using ``put_force_envelope``
        (which widens on collision).

        Args:
            request: Must contain ``element_ids`` and ``force_loadcases``.
            result_set: Mutated in place.
        """
        element_keys = self._resolve_element_keys(request)
        if not element_keys:
            logger.warning("No valid element keys to fetch forces for")
            return

        lc_names = self._build_load_case_names(request)
        if not lc_names:
            logger.warning("No load case names to fetch forces for")
            return

        # Build request body
        body = self._build_request_body(element_keys, lc_names)

        # Execute API call
        try:
            resp = self._api.request("POST", "/post/TABLE", body)
            resp_data = resp.json()
        except Exception as e:
            logger.error("Midas /post/TABLE (forces) call failed: %s", e)
            raise RuntimeError(f"Failed to fetch forces from Midas: {e}")

        # Log raw response structure for debugging (top-level keys + first row)
        top_keys = list(resp_data.keys()) if isinstance(resp_data, dict) else repr(resp_data)[:200]
        logger.debug("Forces response top-level keys: %s", top_keys)
        for k, v in (resp_data.items() if isinstance(resp_data, dict) else []):
            if isinstance(v, dict):
                sub_keys = list(v.keys())
                data = v.get("DATA")
                n_rows = len(data) if isinstance(data, list) else "N/A"
                first = data[0] if isinstance(data, list) and data else None
                logger.debug(
                    "  [%s] sub-keys=%s  DATA rows=%s  first=%s",
                    k, sub_keys, n_rows, first,
                )
        # Parse response
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
        """Build the load case name list with (CB:max)/(CB:min) suffixes.

        Combination and envelope load cases need both suffixes.
        Single-valued (static) cases are passed with the bare name.

        NOTE — known limitations to test against live session_managers:
            - Midas supports combination types beyond CB (e.g. moving-load
              envelopes, construction-stage, time-history). These may use
              different suffix conventions or return multiple rows without
              any suffix at all. The cross-program validation test must
              cover at least one non-CB combination type.
            - Static load cases may also return differently depending on
              analysis type (linear static vs. nonlinear static vs.
              staged construction). The bare-name fallback below
              assumes they never produce max/min rows, which must be
              verified.
            - The triple-send pattern (bare + CB:max + CB:min) for
              unknown cases works because the Midas API ignores names
              it doesn't recognise, but this triples the request payload
              unnecessarily. Once the live behaviour is confirmed, this
              should be tightened to send only what's needed.
        """
        lc_names: List[str] = []
        for lc in sorted(request.force_loadcases):
            if (self._load_case_resolver is not None
                    and self._load_case_resolver.is_combination(lc)):
                lc_names.append(f"{lc}(CB:max)")
                lc_names.append(f"{lc}(CB:min)")
            else:
                # Static load case or unknown — try bare name and
                # also with suffixes to be safe. The API ignores names
                # it doesn't recognize.
                # TODO: tighten once live behaviour is confirmed for
                # all analysis types (see note above).
                lc_names.append(lc)
                lc_names.append(f"{lc}(CB:max)")
                lc_names.append(f"{lc}(CB:min)")
        return lc_names

    @staticmethod
    def _build_request_body(
        element_keys: List[int], lc_names: List[str]
    ) -> Dict[str, Any]:
        """Construct the JSON body for ``POST /post/TABLE``."""
        return {
            "TABLE_TYPE": "BEAMFORCEVBM",
            "UNIT": MIDAS_CANONICAL_UNIT,
            "STYLES": {"FORMAT": "Fixed", "PLACE": 12},
            "COMPONENTS": [
                "Elem", "Load", "Part", "Component",
                "Axial", "Shear-y", "Shear-z",
                "Torsion", "Moment-y", "Moment-z",
            ],
            "NODE_ELEMS": {"KEYS": element_keys},
            "LOAD_CASE_NAMES": lc_names,
            "PARTS": ["PartI", "PartJ"],
            "ITEM_TO_DISPLAY": [
                "Axial", "Shear-y", "Shear-z",
                "Torsion", "Moment-y", "Moment-z",
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
        """Walk the response rows and deposit force envelopes."""
        requested_lcs = set(request.force_loadcases)

        # The response key varies; find the first key that has "DATA"
        data_rows = self._extract_data_rows(resp_data)
        if data_rows is None:
            logger.warning("No force data returned from Midas")
            return

        kept = 0
        skipped_lc = 0
        skipped_end = 0

        for row in data_rows:
            try:
                element_id = int(row[1])
                raw_lc = str(row[2])
                part_str = str(row[3])

                # Strip (CB:max)/(CB:min) suffix to get bare load case name
                lc = self._strip_combo_suffix(raw_lc)

                # Skip if this load case was not requested
                if lc not in requested_lcs:
                    skipped_lc += 1
                    continue

                # Classify part as I or J end
                end = self._classify_part(part_str)
                if end is None:
                    skipped_end += 1
                    logger.debug(
                        "Unrecognized part '%s' for element %d, skipping",
                        part_str, element_id,
                    )
                    continue

                # Build force vector via ResultModel → mapper (POST pipeline pattern)
                result_model = ForceResultModel(
                    element_name=str(element_id),
                    load_case=lc,
                    step_type="Max" if "(CB:max)" in raw_lc else ("Min" if "(CB:min)" in raw_lc else None),
                    elm_station=0.0,  # Midas BEAMFORCEVBM reports per-end, not per-station
                    axial=float(row[5]),
                    shear_y=float(row[6]),
                    shear_z=float(row[7]),
                    torsion=float(row[8]),
                    moment_y=float(row[9]),
                    moment_z=float(row[10]),
                    unit_system=CANONICAL_UNIT_SYSTEM,
                )
                force_vec = ForceResultMapper.to_domain(result_model)

                # Build envelope and deposit
                envelope = ElementForceEnvelope.from_single(
                    element_id=element_id,
                    end=end,
                    load_case=lc,
                    f=force_vec,
                )
                result_set.add_force_envelope(envelope)
                kept += 1

            except (IndexError, ValueError) as e:
                logger.warning("Skipping malformed force row: %s — %s", row, e)
                continue

        logger.info(
            "MidasForcesFetcher: kept=%d skipped(lc)=%d skipped(end)=%d",
            kept, skipped_lc, skipped_end,
        )

    @staticmethod
    def _extract_data_rows(
        resp_data: Dict[str, Any],
    ) -> Optional[List[List[Any]]]:
        """Find the DATA list in the response, regardless of top-level key.

        The Midas ``/post/TABLE`` response wraps data under a key that
        may be ``"Empty"`` or the table name. We search for the first
        sub-dict that contains a ``"DATA"`` key.
        """
        for key, value in resp_data.items():
            if isinstance(value, dict) and "DATA" in value:
                return value["DATA"]
        # Fall-back: check if "DATA" is at the top level
        if "DATA" in resp_data:
            return resp_data["DATA"]
        return None

    @staticmethod
    def _strip_combo_suffix(raw_lc: str) -> str:
        """Strip ``(CB:max)`` or ``(CB:min)`` from a load case name.

        Example: ``"ULS_gr5(CB:max)"`` -> ``"ULS_gr5"``
        """
        paren_idx = raw_lc.find("(")
        if paren_idx > 0:
            return raw_lc[:paren_idx]
        return raw_lc

    @staticmethod
    def _classify_part(part_str: str) -> Optional[ElementEnd]:
        """Map a Midas part string to ``ElementEnd.I`` or ``ElementEnd.J``.

        Midas uses ``"PartI"``, ``"I"`` or similar for the I end.
        If the part indicator is not recognized, returns ``None`` — the
        caller should raise ``ConfigurationError`` or skip per invariant I2.
        """
        part_upper = part_str.strip().upper()
        if part_upper.startswith("I") or part_upper == "PARTI":
            return ElementEnd.I
        if part_upper.startswith("J") or part_upper == "PARTJ":
            return ElementEnd.J
        return None

