"""Fetch nodal displacements from Midas Civil NX.

Uses ``POST /post/TABLE`` with ``TABLE_TYPE: "DISPLACEMENTG"`` to retrieve
six DOFs per node per load case in the Global coordinate system.
Confirmed against a live Midas Civil NX session_manager on 2026-04-15.

Alternate: ``"DISPLACEMENTL"`` returns local-axis displacements (rarely
needed — global is the default).

The fetcher follows the same pattern as ``MidasForcesFetcher``: build
a POST body, call the API, parse the response rows, and construct
``NodalDisplacement`` primitives.

Displacement convention:
    Midas returns displacements in the global coordinate system by
    default, which matches our domain convention. Rotations may be
    returned in degrees depending on user settings — the fetcher must
    convert to radians before constructing ``NodalDisplacement``.

    NOTE: Whether the ``UNIT`` field in the POST body controls rotation
    units is TBD. If Midas always returns radians when we specify
    ``"DIST": "m"``, no conversion is needed. If it returns degrees,
    a ``math.radians()`` call must be added.

CB:max/CB:min for displacements: TBD — must be verified against a
live session_manager. The current implementation assumes the same suffix
convention as forces.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from bda.domain.results.data_request import DataRequest
from bda.domain.results.result_primitives import (
    NodalDisplacement,
    NodalDisplacementEnvelope,
)
from bda.domain.results.result_set import ResultSet
from bda.infrastructure.adapters.analytical_software.importers.midas_helpers.midas_id_mapper import MidasIdMapper
from bda.infrastructure.adapters.analytical_software.importers.midas_helpers.midas_load_case_resolver import (
    MidasLoadCaseResolver,
)
from bda.application.mapping.results.midas.midas_displacement_result_mapper import MidasDisplacementResultMapper
from bda.contracts.result_models.midas.displacement_result_model import MidasDisplacementResultModel
from bda.infrastructure.adapters.analytical_software.exporters.midas_helpers.MidasAPI import MidasAPI
from bda.infrastructure.utils import CANONICAL_UNIT_SYSTEM

logger = logging.getLogger(__name__)

# Canonical units for the POST body.
MIDAS_CANONICAL_UNIT = {"FORCE": "kN", "DIST": "m"}

# TABLE_TYPE for displacements — verified 2026-04-15 against live Midas session_manager.
# "DISPLACEMENTG" = Global axes (our convention). "DISPLACEMENTL" = Local if ever needed.
DISPLACEMENT_TABLE_TYPE = "DISPLACEMENTG"
DISPLACEMENT_TABLE_NAME = "Displacements(Global)"


class MidasDisplacementsFetcher:
    """Pull nodal displacements from Midas and deposit them in a ResultSet."""

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
        """Fetch displacements for every (node, load case) in ``request``.

        Deposits one ``NodalDisplacement`` per (node_id, load_case) into
        ``result_set`` via ``put_displacement_envelope``.

        Args:
            request: Must contain ``node_ids`` and ``disp_loadcases``.
            result_set: Mutated in place.
        """
        node_keys = self._resolve_node_keys(request)
        if not node_keys:
            logger.warning("No valid node keys to fetch displacements for")
            return

        lc_names = self._build_load_case_names(request)
        if not lc_names:
            logger.warning("No load case names to fetch displacements for")
            return

        body = self._build_request_body(node_keys, lc_names)

        try:
            resp = self._api.request("POST", "/post/TABLE", body)
            resp_data = resp.json()
        except Exception as e:
            logger.error("Midas /post/table (displacements) call failed: %s", e)
            raise RuntimeError(
                f"Failed to fetch displacements from Midas: {e}"
            )

        self._parse_response(resp_data, request, result_set)

    # ------------------------------------------------------------------
    # Request building
    # ------------------------------------------------------------------
    def _resolve_node_keys(self, request: DataRequest) -> List[int]:
        """Validate and return node ids that exist in the Midas model."""
        valid_keys = []
        for nid in request.node_ids:
            try:
                self._id_mapper.validate_node(nid)
                valid_keys.append(nid)
            except KeyError:
                logger.warning(
                    "Node ID %d not found in Midas model, skipping", nid
                )
        return valid_keys

    def _build_load_case_names(self, request: DataRequest) -> List[str]:
        """Build load case names with (CB:max)/(CB:min) suffixes for combos.

        TBD: Whether displacements use the same suffix convention as
        forces. Current implementation mirrors forces behaviour.

        NOTE — same LC limitations as ``MidasForcesFetcher``:
            - Non-CB combination types (moving-load, construction-stage,
              time-history) may use different suffix conventions.
            - Static load cases may behave differently depending on
              analysis type. Needs live verification.
        """
        lc_names: List[str] = []
        for lc in sorted(request.disp_loadcases):
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
        node_keys: List[int], lc_names: List[str]
    ) -> Dict[str, Any]:
        """Construct the JSON body for ``POST /post/table`` (displacements)."""
        return {
            "TABLE_TYPE": DISPLACEMENT_TABLE_TYPE,
            "TABLE_NAME": DISPLACEMENT_TABLE_NAME,
            "UNIT": MIDAS_CANONICAL_UNIT,
            "STYLES": {"FORMAT": "Fixed", "PLACE": 12},
            "COMPONENTS": [
                "Node", "Load",
                "DX", "DY", "DZ",
                "RX", "RY", "RZ",
            ],
            "NODE_ELEMS": {"KEYS": node_keys},
            "LOAD_CASE_NAMES": lc_names,
            "ITEM_TO_DISPLAY": [
                "DX", "DY", "DZ",
                "RX", "RY", "RZ",
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
        """Walk the response rows and deposit displacements."""
        requested_lcs = set(request.disp_loadcases)

        data_rows = self._extract_data_rows(resp_data)
        if data_rows is None:
            logger.warning("No displacement data returned from Midas")
            return

        kept = 0
        skipped_lc = 0

        for row in data_rows:
            try:
                node_id = int(row[1])
                raw_lc = str(row[2])

                # Strip combo suffix
                lc = self._strip_combo_suffix(raw_lc)

                if lc not in requested_lcs:
                    skipped_lc += 1
                    continue

                # Build displacement via ResultModel → mapper (POST pipeline pattern)
                result_model = MidasDisplacementResultModel(
                    node_name=str(node_id),
                    load_case=lc,
                    step_type="Max" if "(CB:max)" in raw_lc else ("Min" if "(CB:min)" in raw_lc else None),
                    ux=float(row[3]),
                    uy=float(row[4]),
                    uz=float(row[5]),
                    rx=float(row[6]),
                    ry=float(row[7]),
                    rz=float(row[8]),
                    unit_system=CANONICAL_UNIT_SYSTEM,
                )
                disp = MidasDisplacementResultMapper.midas_to_domain(result_model, node_id=node_id)

                # Wrap in a degenerate envelope and hand to ResultSet;
                # put_displacement_envelope widens on collision, so both
                # CB:max and CB:min rows contribute their per-component
                # extremes independently.
                envelope = NodalDisplacementEnvelope.from_single(
                    node_id=node_id,
                    load_case=lc,
                    d=disp,
                )
                result_set.add_displacement_envelope(envelope)
                kept += 1

            except (IndexError, ValueError) as e:
                logger.warning(
                    "Skipping malformed displacement row: %s — %s", row, e
                )
                continue

        logger.info(
            "MidasDisplacementsFetcher: kept=%d skipped(lc)=%d",
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

