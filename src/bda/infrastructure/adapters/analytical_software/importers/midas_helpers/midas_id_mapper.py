"""Bidirectional integer-id validation for Midas Civil NX.

Unlike CSI Bridge (which encodes element ids as prefixed strings like
``"F12"`` or plain ``"12"``), Midas Civil NX uses plain integer keys in
its REST API JSON responses. Our exporter writes domain ids directly
(``id=element.id``), so the Midas key IS the domain id.

The mapper still exists for:
    - Validation: confirm that a domain id actually exists in the
      running Midas model before attempting to fetch results.
    - Symmetry with the CSI path, so the orchestrator and fetchers
      have the same dependency shape regardless of source program.
    - Node coordinate lookup for element-length computation (needed
      by the forces fetcher for any future intermediate-station work).
    - Element→section name mapping for per-node geometry injection.
    - Raw section props cache for geometric dimension extraction
      (``all_section_raw_props`` → ``parse_section_geometry``).
"""
from __future__ import annotations

import logging
from typing import Dict, Optional, Set

from bda.infrastructure.adapters.analytical_software.exporters.midas_helpers.MidasAPI import MidasAPI

logger = logging.getLogger(__name__)

# Midas distance-unit string → factor to convert to metres
_DIST_TO_METRES: Dict[str, float] = {
    "mm":   1.0 / 1000.0,
    "cm":   1.0 / 100.0,
    "m":    1.0,
    "ft":   0.3048,
    "in":   0.0254,
}


def _dist_unit_factor(api: MidasAPI) -> float:
    """Query ``GET /db/unit`` and return the factor needed to convert
    Midas distance values to **metres**.

    Midas model coordinates and the node ``X``/``Y``/``Z`` fields from
    ``GET /db/node`` are in whatever unit the model is currently set to.
    The canonical unit for BDA is always metres, so we must convert.

    Tries multiple key names for the distance unit to handle different
    Midas Civil NX API versions:
        UNIT.DIST, UNIT.LENGTH, UNIT.LEN  (nested under "UNIT")
        DIST, LENGTH, LEN                 (top-level fallback)

    Returns 1.0 on any failure (assumes metres) with a warning logged.
    """
    try:
        resp = api.request("GET", "/db/unit")
        data = resp.json()
        logger.info("MidasIdMapper: /db/unit response: %s", data)

        # Midas wraps unit data under "UNIT", sometimes with an extra numeric
        # index level: {"UNIT": {"1": {"FORCE": "KN", "DIST": "MM", ...}}}
        # Unwrap up to two levels to find the dict that has "DIST".
        unit_block = data.get("UNIT", data)

        # If the block has no recognised dist key, try unwrapping one more level
        # (handles the {"1": {FORCE, DIST, ...}} pattern observed in live models)
        _dist_keys = ("DIST", "dist", "LENGTH", "length", "LEN", "len")
        if not any(k in unit_block for k in _dist_keys):
            for v in unit_block.values():
                if isinstance(v, dict) and any(k in v for k in _dist_keys):
                    unit_block = v
                    break

        dist_str: str = ""
        for key in _dist_keys:
            val = unit_block.get(key)
            if val:
                dist_str = str(val).strip().lower()
                break

        if not dist_str:
            # Last resort: scan top level directly
            for key in _dist_keys:
                val = data.get(key)
                if val:
                    dist_str = str(val).strip().lower()
                    break

        if not dist_str:
            logger.warning(
                "MidasIdMapper: /db/unit response has no recognisable distance "
                "key — full response: %s — assuming metres.", data
            )
            dist_str = "m"

        factor = _DIST_TO_METRES.get(dist_str, 1.0)
        logger.info(
            "MidasIdMapper: model distance unit=%r → factor=%.6f (to metres)",
            dist_str, factor,
        )
        return factor
    except Exception as exc:
        logger.warning(
            "MidasIdMapper: could not query /db/unit (%s) — assuming metres.",
            exc,
        )
        return 1.0


class MidasIdMapper:
    """Validate domain ids against the running Midas Civil NX model.

    Built fresh at the start of every import run by querying
    ``GET /db/elem``, ``GET /db/node``, and ``GET /db/sect``.

    Node coordinates are stored in **metres** regardless of the model's
    native unit system.  The conversion factor is read from ``GET /db/unit``
    during construction.
    """

    def __init__(self, api: MidasAPI) -> None:
        """Probe Midas and populate the internal caches."""
        self._api = api
        self._element_keys: Set[int] = set()
        self._node_keys: Set[int] = set()
        self._node_coords: Dict[int, tuple] = {}        # {node_id: (x, y, z)} in metres
        self._element_section_ids: Dict[int, int] = {}  # {element_id: section_id}
        self._section_names: Dict[int, str] = {}        # {section_id: section_name}
        self._section_raw_props: Dict[str, dict] = {}   # {section_name: raw props dict}
        self._build()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def _build(self) -> None:
        """Populate caches by querying the Midas REST API."""
        # ── Distance unit factor (must come first) ────────────────────────────
        dist_factor = _dist_unit_factor(self._api)

        # Elements: GET /db/elem -> {"ELEM": {"1": {"ISEC": 1, ...}, ...}}
        try:
            elem_resp = self._api.request("GET", "/db/elem")
            elem_data = elem_resp.json()
            for key, props in elem_data.get("ELEM", {}).items():
                eid = int(key)
                self._element_keys.add(eid)
                # Section id field: Midas uses "ISEC" (integer section number)
                sec_id = props.get("ISEC") or props.get("iSEC") or props.get("SECT")
                if sec_id is not None:
                    try:
                        self._element_section_ids[eid] = int(sec_id)
                    except (TypeError, ValueError):
                        pass
            logger.info(
                "MidasIdMapper: loaded %d elements (%d with section ids)",
                len(self._element_keys),
                len(self._element_section_ids),
            )
        except Exception as e:
            logger.error("MidasIdMapper: failed to load elements: %s", e)
            raise RuntimeError(f"Cannot build element map from Midas: {e}")

        # Nodes: GET /db/node -> {"NODE": {"1": {"X":..,"Y":..,"Z":..}, ...}}
        try:
            node_resp = self._api.request("GET", "/db/node")
            node_data = node_resp.json()
            for key, props in node_data.get("NODE", {}).items():
                nid = int(key)
                self._node_keys.add(nid)
                # Convert to metres using the model's distance unit factor
                self._node_coords[nid] = (
                    props.get("X", 0.0) * dist_factor,
                    props.get("Y", 0.0) * dist_factor,
                    props.get("Z", 0.0) * dist_factor,
                )
            logger.info("MidasIdMapper: loaded %d nodes", len(self._node_keys))
        except Exception as e:
            logger.error("MidasIdMapper: failed to load nodes: %s", e)
            raise RuntimeError(f"Cannot build node map from Midas: {e}")

        # Sections: GET /db/sect -> {"SECT": {"1": {"NAME": "Box_1m", ...}, ...}}
        try:
            sect_resp = self._api.request("GET", "/db/sect")
            sect_data = sect_resp.json()
            for key, props in sect_data.get("SECT", {}).items():
                sid = int(key)
                # Section name field: try "NAME" then "SECT_NAME"
                name = props.get("NAME") or props.get("SECT_NAME") or f"SECT_{sid}"
                name = str(name)
                self._section_names[sid] = name
                # Store raw props keyed by section name for geometry extraction
                self._section_raw_props[name] = props
            logger.info(
                "MidasIdMapper: loaded %d sections", len(self._section_names)
            )
        except Exception as exc:
            # Non-fatal — section name lookup will fall back to id-based names
            logger.warning(
                "MidasIdMapper: could not load section names (%s) — "
                "element_section_name() will return id-based fallbacks.",
                exc,
            )

    # ------------------------------------------------------------------
    # Element lookups
    # ------------------------------------------------------------------
    def validate_element(self, element_id: int) -> None:
        """Raise ``KeyError`` if the element id is not in the Midas model."""
        if element_id not in self._element_keys:
            raise KeyError(
                f"Element {element_id} not found in Midas model "
                f"(known: {len(self._element_keys)} elements)"
            )

    @property
    def element_ids(self) -> Set[int]:
        """All element ids known to the Midas model."""
        return set(self._element_keys)

    # ------------------------------------------------------------------
    # Node lookups
    # ------------------------------------------------------------------
    def validate_node(self, node_id: int) -> None:
        """Raise ``KeyError`` if the node id is not in the Midas model."""
        if node_id not in self._node_keys:
            raise KeyError(
                f"Node {node_id} not found in Midas model "
                f"(known: {len(self._node_keys)} nodes)"
            )

    @property
    def node_ids(self) -> Set[int]:
        """All node ids known to the Midas model."""
        return set(self._node_keys)

    def node_coordinates(self, node_id: int) -> tuple:
        """Return ``(x, y, z)`` for a node, in **metres**."""
        if node_id not in self._node_coords:
            raise KeyError(f"Node {node_id} not found in Midas model")
        return self._node_coords[node_id]

    @property
    def all_node_coords(self) -> Dict[int, tuple]:
        """Read-only copy of the full node-coordinate cache (metres)."""
        return dict(self._node_coords)

    # ------------------------------------------------------------------
    # Section lookups
    # ------------------------------------------------------------------
    def element_section_id(self, element_id: int) -> int:
        """Return the section id assigned to *element_id*.

        Raises ``KeyError`` if the element has no section assignment cached.
        """
        if element_id not in self._element_section_ids:
            raise KeyError(
                f"No section id cached for element {element_id}. "
                "Check that the Midas model has sections assigned."
            )
        return self._element_section_ids[element_id]

    def element_section_name(self, element_id: int) -> str:
        """Return the section NAME for *element_id*.

        Falls back to ``"SECT_{id}"`` when the name lookup failed at build time.
        Raises ``KeyError`` if the element has no section assignment at all.
        """
        sec_id = self.element_section_id(element_id)
        return self._section_names.get(sec_id, f"SECT_{sec_id}")

    @property
    def element_section_ids(self) -> Dict[int, int]:
        """Read-only copy of the element -> section-id mapping."""
        return dict(self._element_section_ids)

    @property
    def section_names(self) -> Dict[int, str]:
        """Read-only copy of the section-id -> name mapping."""
        return dict(self._section_names)

    @property
    def all_section_raw_props(self) -> Dict[str, dict]:
        """Read-only copy of the section-name -> raw props mapping.

        The raw props dict is the value from the ``GET /db/sect`` response
        for that section.  Pass individual entries to
        ``midas_section_geometry.parse_section_geometry()`` to extract
        cross-section dimensions (h, top_hf, bw, bot_hf, etc.).
        """
        return dict(self._section_raw_props)

    def section_raw_props_for(self, name: str) -> Optional[dict]:
        """Return the raw props dict for section *name*, or ``None``."""
        return self._section_raw_props.get(name)
