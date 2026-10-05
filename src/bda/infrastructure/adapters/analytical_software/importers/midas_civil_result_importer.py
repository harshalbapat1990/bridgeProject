"""Concrete ``IResultImporter`` for Midas Civil NX.

Composes the three fetchers (forces, displacements, stresses) plus
the id mapper and load-case resolver into a single entry point that
matches the ``IResultImporter`` contract.

The importer does NOT own the Midas session_manager. It is constructed
with an already-open session_manager; closing the Midas session_manager remains the
caller's responsibility. ``close()`` is a no-op
because, unlike CSI Bridge, Midas has no output-selection state to
restore.

Connection strategy:
    Uses the raw ``MidasAPI`` class from
    ``infrastructure.adapters.exporters.midas_helpers``, which is the
    same transport used by the Midas exporter. This keeps the
    connection approach consistent across the project.
"""
from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional

from bda.application.interfaces.analytical_software.importer import IResultImporter
from bda.domain.enums.output_software_enums import OutputSoftware
from bda.infrastructure.adapters.analytical_software.session_managers.midas_civil_session import MidasCivilSession
from bda.application.interfaces.analytical_software.session_manager import IAnalyticalSoftwareSession
from bda.domain.results.data_request import DataRequest
from bda.domain.results.load_case import LoadCase
from bda.domain.results.result_set import ResultSet
from bda.infrastructure.adapters.analytical_software.importers.midas_helpers.midas_displacements_fetcher import MidasDisplacementsFetcher
from bda.infrastructure.adapters.analytical_software.importers.midas_helpers.midas_forces_fetcher import MidasForcesFetcher
from bda.infrastructure.adapters.analytical_software.importers.midas_helpers.midas_id_mapper import MidasIdMapper
from bda.infrastructure.adapters.analytical_software.importers.midas_helpers.midas_load_case_resolver import MidasLoadCaseResolver
from bda.infrastructure.adapters.analytical_software.importers.midas_helpers.midas_section_geometry import parse_section_geometry
from bda.infrastructure.adapters.analytical_software.importers.midas_helpers.midas_section_properties_fetcher import MidasSectionPropertiesFetcher
from bda.infrastructure.adapters.analytical_software.importers.midas_helpers.midas_stresses_fetcher import MidasStressesFetcher
from bda.application.mapping.results.post_result_import_config import PostResultImportConfig
from bda.application.mapping.results.section_properties_mapper import SectionPropertiesMapper
from bda.domain.results.section_properties import SectionProperties

logger = logging.getLogger(__name__)


class MidasCivilResultImporter(IResultImporter):
    """Normalize Midas Civil NX analysis results into the shared ``ResultSet``.

    Usage (manual — for testing or custom connections)::

        session_manager = MidasCivilSession(MidasConfigProvider())
        importer = MidasCivilResultImporter(session_manager)
        result_set = importer.fetch(merged_data_request)
    """

    def __init__(
        self,
        session: IAnalyticalSoftwareSession,
        post_config: PostResultImportConfig | None = None,
    ) -> None:
        """Construct the importer on top of an already-open Midas session_manager.

        Args:
            session:     A ``MidasCivilSession`` instance.
            post_config: Optional POST import settings.  When provided and
                         ``post_config.results_dir`` is non-empty,
                         ``fetch_section_properties()`` is available.
        """
        if not isinstance(session, MidasCivilSession):
            raise TypeError("MidasCivilResultImporter requires MidasCivilSession")

        self._session: MidasCivilSession = session
        self._api = session.api()
        self._id_mapper = MidasIdMapper(self._api)
        self._load_case_resolver = MidasLoadCaseResolver(self._api)
        self._forces_fetcher = MidasForcesFetcher(
            self._api, self._id_mapper, self._load_case_resolver
        )
        self._displacements_fetcher = MidasDisplacementsFetcher(
            self._api, self._id_mapper, self._load_case_resolver
        )
        self._stresses_fetcher = MidasStressesFetcher(
            self._api, self._id_mapper, self._load_case_resolver
        )
        results_dir = post_config.results_dir if post_config else ""
        if results_dir:
            self._section_props_fetcher: MidasSectionPropertiesFetcher | None = (
                MidasSectionPropertiesFetcher(self._api, results_dir)
            )
        else:
            self._section_props_fetcher = None
            logger.warning(
                "results_dir not set in PostResultImportConfig — "
                "fetch_section_properties() will be unavailable."
            )
        logger.info("MidasCivilResultImporter initialized")


    # ------------------------------------------------------------------
    # IResultImporter
    # ------------------------------------------------------------------
    def fetch(self, request: DataRequest) -> ResultSet:
        """Run all three fetchers and return a normalized ResultSet.

        Steps:
            1. Validate every requested load case via the resolver.
            2. Call each fetcher's ``fetch_into(request, result_set)``.
            3. Return the populated result set.

        Unlike the CSI importer, there is no unit-switching context
        manager — Midas accepts per-request unit specifications in
        the POST body.
        """
        result_set = ResultSet(source=OutputSoftware.MIDAS)

        # Validate load cases up-front so a bad name fails fast.
        all_lcs = sorted(request.all_load_cases())
        if all_lcs:
            self._load_case_resolver.resolve(all_lcs)

        # Fetch forces
        if request.force_loadcases and request.element_ids:
            logger.info(
                "Fetching forces for %d elements, %d load cases",
                len(request.element_ids),
                len(request.force_loadcases),
            )
            self._forces_fetcher.fetch_into(request, result_set)

        # Fetch displacements
        if request.disp_loadcases and request.node_ids:
            logger.info(
                "Fetching displacements for %d nodes, %d load cases",
                len(request.node_ids),
                len(request.disp_loadcases),
            )
            self._displacements_fetcher.fetch_into(request, result_set)

        # Fetch stresses
        if request.stress_loadcases and request.element_ids:
            logger.info(
                "Fetching stresses for %d elements, %d load cases",
                len(request.element_ids),
                len(request.stress_loadcases),
            )
            self._stresses_fetcher.fetch_into(request, result_set)

        logger.info(
            "MidasCivilResultImporter.fetch complete: "
            "%d force envelopes, %d displacements, %d stresses",
            len(result_set.force_envelopes),
            len(result_set.displacement_envelopes),
            len(result_set.stresses),
        )
        return result_set

    def available_load_cases(self) -> List[LoadCase]:
        """Delegate to the load-case resolver."""
        return self._load_case_resolver.available()

    def fetch_node_geometry(
        self, node_ids: Optional[Iterable[int]] = None
    ) -> Dict[int, tuple]:
        """Return ``{node_id: (x, y, z)}`` for the requested nodes.

        Coordinates come from the already-cached ``MidasIdMapper`` built at
        importer construction time — no extra API call is made.

        Args:
            node_ids: Ids to look up. ``None`` returns all cached nodes.

        Returns:
            Dict mapping each requested node id to its ``(x, y, z)`` tuple
            in model units (metres when using canonical unit system).
            Nodes not in the model are silently omitted.
        """
        all_coords = self._id_mapper.all_node_coords
        if node_ids is None:
            return dict(all_coords)
        return {nid: all_coords[nid] for nid in node_ids if nid in all_coords}

    def fetch_element_section_names(
        self, element_ids: Optional[Iterable[int]] = None
    ) -> Dict[int, str]:
        """Return ``{element_id: section_name}`` for the requested elements.

        Section names come from the already-cached ``MidasIdMapper``.

        Args:
            element_ids: Ids to look up. ``None`` returns all cached elements.

        Returns:
            Dict mapping element id to its Midas section name string.
            Elements with no section assignment are silently omitted.
        """
        sec_ids = self._id_mapper.element_section_ids
        sec_names = self._id_mapper.section_names
        eids = element_ids if element_ids is not None else list(sec_ids.keys())
        result: Dict[int, str] = {}
        for eid in eids:
            sid = sec_ids.get(eid)
            if sid is not None:
                result[eid] = sec_names.get(sid, f"SECT_{sid}")
        return result

    def fetch_section_geometry(
        self, section_names: Optional[Iterable[str]] = None
    ) -> Dict[str, Dict]:
        """Return cross-section geometric dimensions for Midas sections.

        Parses the raw ``/db/sect`` data already cached by ``MidasIdMapper``
        (no extra API call) using ``parse_section_geometry``.

        Currently supports ``SHAPE: "1CEL"`` (single-cell PSC box).  Sections
        of other shapes are silently omitted from the result.

        Args:
            section_names: Section names to look up.  ``None`` returns all
                           parseable sections in the model.

        Returns:
            ``{section_name: geometry_dict}`` where each geometry dict is one of:

            Constant section::

                {"h": float, "top_hf": float, "bw": float, "bot_hf": float}

            Tapered section::

                {"h_start": float, "h_end": float,
                 "top_hf": float, "bw": float, "bot_hf": float}

            All values are in **metres**.

        Notes:
            Sections whose shape is not supported (non-1CEL) are omitted
            from the returned dict without raising an error.  The caller
            should treat missing entries as "geometry unknown — fall back
            to run-spec values".
        """
        raw_props = self._id_mapper.all_section_raw_props

        names_to_fetch = (
            list(section_names) if section_names is not None
            else list(raw_props.keys())
        )

        result: Dict[str, Dict] = {}
        unsupported: List[str] = []

        for name in names_to_fetch:
            props = raw_props.get(name)
            if props is None:
                logger.debug(
                    "fetch_section_geometry: section %r not in mapper cache — skipped.",
                    name,
                )
                continue
            geom = parse_section_geometry(props)
            if geom is None:
                unsupported.append(name)
            else:
                result[name] = geom

        if unsupported:
            logger.debug(
                "fetch_section_geometry: %d section(s) skipped "
                "(unsupported shape): %s",
                len(unsupported),
                ", ".join(unsupported),
            )

        logger.info(
            "fetch_section_geometry: parsed geometry for %d / %d section(s).",
            len(result),
            len(names_to_fetch),
        )
        return result

    def fetch_section_properties(self) -> dict:
        """Fetch computed section geometric properties for all sections.

        Calls POST /post/TABLE SECTIONALL, reads the exported file,
        and returns a dict keyed by section name.

        Returns:
            ``{section_name: SectionProperties}`` for every section
            defined in the Midas model.

        Raises:
            RuntimeError: If results_dir is not configured or the export
                file cannot be found/parsed.
        """
        if self._section_props_fetcher is None:
            raise RuntimeError(
                "Section properties fetcher is not configured. "
                "Set 'results_dir' in PostResultImportConfig."
            )
        result_models = self._section_props_fetcher.fetch()
        from bda.application.mapping.results.section_properties_mapper import SectionPropertiesMapper
        return SectionPropertiesMapper.to_domain_dict(result_models)
