"""Concrete `IResultImporter` for CSI Bridge.

Composes the four fetchers (`forces`, `displacements`, `stresses`) plus
the id mapper and load-case resolver into a single entry point that
matches the `IResultImporter` contract.

The importer does NOT own the CSI session_manager. It is constructed with an
already-open session_manager exposing `sap_model`;
"""
from __future__ import annotations

from typing import List

from bda.application.interfaces.analytical_software.importer import IResultImporter
from bda.infrastructure.adapters.analytical_software.session_managers.csi_bridge_session import CSIBridgeSession
from bda.application.interfaces.analytical_software.session_manager import IAnalyticalSoftwareSession
from bda.domain.enums.output_software_enums import OutputSoftware
from bda.domain.results.data_request import DataRequest
from bda.domain.results.load_case import LoadCase
from bda.domain.results.result_set import ResultSet
from bda.infrastructure.adapters.analytical_software.importers.csi_helpers.csi_displacements_fetcher import CsiDisplacementsFetcher
from bda.infrastructure.adapters.analytical_software.importers.csi_helpers.csi_forces_fetcher import CsiForcesFetcher
from bda.infrastructure.adapters.analytical_software.importers.csi_helpers.csi_id_mapper import CsiIdMapper
from bda.infrastructure.adapters.analytical_software.importers.csi_helpers.csi_load_case_resolver import CsiLoadCaseResolver
from bda.infrastructure.adapters.analytical_software.importers.csi_helpers.csi_stresses_fetcher import CsiStressesFetcher
from bda.infrastructure.adapters.analytical_software.importers.csi_helpers.csi_units_context import CsiUnitsContext


class CsiBridgeResultImporter(IResultImporter):
    """Normalize CSI Bridge analysis results into the shared `ResultSet`."""

    def __init__(self, session: IAnalyticalSoftwareSession) -> None:
        """Construct the importer on top of an already-open CSI session_manager.

        Args:
            session: An `IAnalyticalSoftwareSession` implementation exposing
                an active `sap_model` handle.
        """
        if not isinstance(session, CSIBridgeSession):
            raise TypeError("CsiBridgeResultImporter requires CSIBridgeSession")
        self._session : CSIBridgeSession = session
        self._sap_model = session.sap_model
        self._id_mapper = CsiIdMapper(self._sap_model)
        self._load_case_resolver = CsiLoadCaseResolver(self._sap_model)
        self._forces_fetcher = CsiForcesFetcher(
            self._sap_model, self._id_mapper, self._load_case_resolver
        )
        self._displacements_fetcher = CsiDisplacementsFetcher(
            self._sap_model, self._id_mapper
        )
        self._stresses_fetcher = CsiStressesFetcher(self._sap_model, self._id_mapper)

    # ------------------------------------------------------------------
    # IResultImporter
    # ------------------------------------------------------------------
    def fetch(self, request: DataRequest) -> ResultSet:
        """Run all three fetchers under a single canonical-units context.

        Steps:
            1. Validate every requested load case via the resolver.
            2. Enable the resolved cases for output.
            3. Enter `CsiUnitsContext` (switch to kN-m-C for the block).
            4. Call each fetcher's `fetch_into(request, result_set)`.
            5. Return the populated container.
        """
        result_set = ResultSet(source=OutputSoftware.CSIBRIDGE)

        # Validate and enable load cases up-front so a bad name fails fast.
        all_lcs = sorted(request.all_load_cases())
        self._load_case_resolver.resolve(all_lcs)
        self._load_case_resolver.enable_for_output(all_lcs)

        with CsiUnitsContext(self._sap_model):
            if request.force_loadcases and request.element_ids:
                self._forces_fetcher.fetch_into(request, result_set)
            if request.disp_loadcases and request.node_ids:
                self._displacements_fetcher.fetch_into(request, result_set)
            if request.stress_loadcases and request.element_ids:
                self._stresses_fetcher.fetch_into(request, result_set)

        return result_set

    def available_load_cases(self) -> List[LoadCase]:
        """Delegate to the load-case resolver."""
        return self._load_case_resolver.available()
