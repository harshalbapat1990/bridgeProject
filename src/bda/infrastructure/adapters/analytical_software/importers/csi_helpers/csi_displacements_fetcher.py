"""Fetch nodal displacements from CSI Bridge.

Uses `Results.JointDispl(point_name, itemType)` to read six DOFs per
node per load case. The return layout (from the reference example) is
similar to FrameForce — the fetcher encapsulates the exact indices so
the rest of the pipeline only sees the canonical
`NodalDisplacement(UX, UY, UZ, RX, RY, RZ)` primitive. CSI returns
DOFs in the global coordinate system by default, which matches the
domain-layer convention (see result_primitives.py module docstring).

Preconditions: the CSI session_manager is in canonical units (kN, m, C) via
`CsiUnitsContext`, and the relevant load cases have already been
enabled for output by `CsiLoadCaseResolver.enable_for_output`.
"""
from __future__ import annotations

import logging
from typing import Any

from bda.application.mapping.results.csi.csi_displacement_result_mapper import CsiDisplacementResultMapper
from bda.contracts.result_models.csi.displacement_result_model import CsiDisplacementResultModel
from bda.domain.results.data_request import DataRequest
from bda.infrastructure.utils import CANONICAL_UNIT_SYSTEM
from bda.domain.results.result_primitives import (
    NodalDisplacement,
    NodalDisplacementEnvelope,
)
from bda.domain.results.result_set import ResultSet
from bda.infrastructure.adapters.analytical_software.importers.csi_helpers.csi_id_mapper import CsiIdMapper

logger = logging.getLogger(__name__)


class CsiDisplacementsFetcher:
    """Pull nodal displacements from CSI and deposit them in a ResultSet."""

    def __init__(self, sap_model: Any, id_mapper: CsiIdMapper) -> None:
        self._sap_model = sap_model
        self._id_mapper = id_mapper

    def fetch_into(self, request: DataRequest, result_set: ResultSet) -> None:
        """Fetch displacements for every (node, load case) in `request`.

        Deposits one `NodalDisplacement` per (node_id, load_case) into
        `result_set` via `put_displacement_envelope`.

        Args:
            request: Must contain `node_ids` and `disp_loadcases`.
            result_set: Mutated in place.
        """
        requested_load_cases = set(request.disp_loadcases)

        for node_id in request.node_ids:
            # Resolve node ID to CSI name
            try:
                node_name = self._id_mapper.node_name(node_id)
            except KeyError:
                logger.warning(f"Node ID {node_id} not found in mapper")
                continue

            # Call CSI API to fetch displacements
            try:
                info = self._sap_model.Results.JointDispl(node_name, 0)
            except Exception as e:
                logger.warning(
                    f"CSI JointDispl call failed for node '{node_name}': {e}"
                )
                continue

            count = info[0]
            if count == 0:
                continue

            # Confirmed layout (verified against live CSI Bridge session_manager
            # 2026-04-09 — smoke test raw dump, node J10):
            #   info[0]  = count
            #   info[1]  = Obj[]        point object names
            #   info[2]  = Elm[]        element names (same as Obj for nodes)
            #   info[3]  = LoadCase[]   ← load case name
            #   info[4]  = StepType[]   e.g. None / 'Max' / 'Min'
            #   info[5]  = StepNum[]    floats, always 0.0
            #   info[6]  = UX           global X translation (m)
            #   info[7]  = UY           global Y translation (m)
            #   info[8]  = UZ           global Z translation (m)
            #   info[9]  = RX           rotation about global X (rad)
            #   info[10] = RY           rotation about global Y (rad)
            #   info[11] = RZ           rotation about global Z (rad)
            #   info[12] = ret          0 = success
            load_cases = info[3]   # was info[5] (StepNum) — confirmed bug
            displs_ux = info[6]
            displs_uy = info[7]
            displs_uz = info[8]
            displs_rx = info[9]
            displs_ry = info[10]
            displs_rz = info[11]

            # Iterate through results
            for j in range(count):
                lc = load_cases[j]

                # Skip if this load case was not requested
                if lc not in requested_load_cases:
                    continue

                # Build displacement via ResultModel → mapper (POST pipeline pattern)
                result_model = CsiDisplacementResultModel(
                    node_name=node_name,
                    load_case=lc,
                    step_type=info[4][j] if count > 0 else None,
                    ux=displs_ux[j],
                    uy=displs_uy[j],
                    uz=displs_uz[j],
                    rx=displs_rx[j],
                    ry=displs_ry[j],
                    rz=displs_rz[j],
                    unit_system=CANONICAL_UNIT_SYSTEM,
                )
                disp = CsiDisplacementResultMapper.csi_to_domain(result_model, node_id=node_id)

                # Wrap in a degenerate envelope and hand to ResultSet;
                # put_displacement_envelope widens on collision, so
                # combination cases that produce multiple rows per
                # (node, lc) — e.g. StepType Max/Min — have their
                # per-component extremes preserved independently.
                envelope = NodalDisplacementEnvelope.from_single(
                    node_id=node_id,
                    load_case=lc,
                    d=disp,
                )
                result_set.add_displacement_envelope(envelope)

