"""Bidirectional integer-id <-> CSI string-name lookup.

The rest of the post-processing pipeline works in integer ids (element
ids, node ids, section ids, material ids). CSI Bridge, however, works
in string names such as "F12", "P7", "M3", "S44". The exporter writes
these names with a single-character prefix followed by the integer id,
so the mapping is reversible by stripping the first character.

The mapper probes CSI at construction time (nothing is pre-stored by
the exporter) and caches both directions for O(1) lookup. It is built
fresh for every import run so renames inside CSI cannot stale-cache.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class CsiIdMapper:
    """Build and expose bidirectional id<->name maps for CSI entities.

    Entities covered:
        - frame elements       (FrameObj.GetNameList)
        - point / node objects (PointObj.GetNameList)
        - frame sections       (PropFrame.GetNameList)
        - materials            (PropMaterial.GetNameList)

    The integer id is obtained by `int(name[1:])`, i.e. the single
    prefix character is dropped. Any name that does not match this
    pattern is skipped with a warning (to be logged by the caller).
    """

    def __init__(self, sap_model: Any) -> None:
        """Probe CSI immediately and populate the internal caches."""
        self._sap_model = sap_model
        self._element_id_to_name: Dict[int, str] = {}
        self._element_name_to_id: Dict[str, int] = {}
        self._node_id_to_name: Dict[int, str] = {}
        self._node_name_to_id: Dict[str, int] = {}
        self._section_id_to_name: Dict[int, str] = {}
        self._section_name_to_id: Dict[str, int] = {}
        self._material_id_to_name: Dict[int, str] = {}
        self._material_name_to_id: Dict[str, int] = {}
        self._build()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_id(name: str) -> int | None:
        """Return the integer id encoded in a CSI name, or None.

        Two naming conventions are handled:
            - Prefixed:   'F12', 'J7', 'P4', 'S1', 'M3'  → int(name[1:])
            - Unprefixed: '12', '7', '4'                  → int(name)

        The unprefixed style occurs when a model was created directly in
        CSI Bridge (not exported via our exporter). The prefixed style is
        what our exporter writes.
        """
        # Try plain integer first (unprefixed names, e.g. '10')
        try:
            return int(name)
        except ValueError:
            pass
        # Fall back to single-character prefix strip (e.g. 'F10' → 10)
        try:
            return int(name[1:])
        except (ValueError, IndexError):
            return None

    def _build(self) -> None:
        """Populate every cache by calling the four GetNameList endpoints."""
        # Load frame elements
        frame_result = self._sap_model.FrameObj.GetNameList()
        frame_count = frame_result[0]
        frame_names = frame_result[1] if frame_count > 0 else ()
        for name in frame_names:
            eid = self._parse_id(name)
            if eid is None:
                logger.warning("Could not parse frame element name '%s'", name)
                continue
            self._element_id_to_name[eid] = name
            self._element_name_to_id[name] = eid

        # Load point objects (nodes)
        point_result = self._sap_model.PointObj.GetNameList()
        point_count = point_result[0]
        point_names = point_result[1] if point_count > 0 else ()
        for name in point_names:
            nid = self._parse_id(name)
            if nid is None:
                logger.warning("Could not parse point name '%s'", name)
                continue
            self._node_id_to_name[nid] = name
            self._node_name_to_id[name] = nid

        # Load frame sections
        section_result = self._sap_model.PropFrame.GetNameList()
        section_count = section_result[0]
        section_names = section_result[1] if section_count > 0 else ()
        for name in section_names:
            sid = self._parse_id(name)
            if sid is None:
                logger.debug(
                    "Could not parse section name '%s' as integer id "
                    "(non-integer section names are normal in hand-built models)",
                    name,
                )
                continue
            self._section_id_to_name[sid] = name
            self._section_name_to_id[name] = sid

        # Load materials
        material_result = self._sap_model.PropMaterial.GetNameList()
        material_count = material_result[0]
        material_names = material_result[1] if material_count > 0 else ()
        for name in material_names:
            mid = self._parse_id(name)
            if mid is None:
                logger.debug(
                    "Could not parse material name '%s' as integer id "
                    "(non-integer material names are normal in hand-built models)",
                    name,
                )
                continue
            self._material_id_to_name[mid] = name
            self._material_name_to_id[name] = mid

    # ------------------------------------------------------------------
    # Element lookups
    # ------------------------------------------------------------------
    def element_name(self, element_id: int) -> str:
        """Return the CSI frame name for an integer element id."""
        return self._element_id_to_name[element_id]

    def element_id(self, name: str) -> int:
        """Return the integer element id for a CSI frame name."""
        return self._element_name_to_id[name]

    # ------------------------------------------------------------------
    # Node lookups
    # ------------------------------------------------------------------
    def node_name(self, node_id: int) -> str:
        """Return the CSI point name for an integer node id."""
        return self._node_id_to_name[node_id]

    def node_id(self, name: str) -> int:
        """Return the integer node id for a CSI point name."""
        return self._node_name_to_id[name]

    # ------------------------------------------------------------------
    # Section lookups
    # ------------------------------------------------------------------
    def section_name(self, section_id: int) -> str:
        """Return the CSI frame-section name for an integer section id."""
        return self._section_id_to_name[section_id]

    def section_id(self, name: str) -> int:
        """Return the integer section id for a CSI frame-section name."""
        return self._section_name_to_id[name]

    # ------------------------------------------------------------------
    # Material lookups
    # ------------------------------------------------------------------
    def material_name(self, material_id: int) -> str:
        """Return the CSI material name for an integer material id."""
        return self._material_id_to_name[material_id]

    def material_id(self, name: str) -> int:
        """Return the integer material id for a CSI material name."""
        return self._material_name_to_id[name]
