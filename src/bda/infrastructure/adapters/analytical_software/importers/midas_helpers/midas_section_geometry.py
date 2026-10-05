"""Parse section geometry from raw Midas Civil NX /db/sect response data.

Midas API response structure (confirmed from live model, 2026-05-04)
--------------------------------------------------------------------
Each entry in the ``"SECT"`` dict has this shape::

    {
        "SECTTYPE":   "TAPERED" | "GENERAL" | ...,   ← top-level
        "SECT_NAME":  "PSC1",                         ← top-level name
        "SECT_BEFORE": {                              ← ALL section geometry lives here
            "SHAPE":  "1CEL",
            "TYPE":   11,
            # Tapered sections (SECTTYPE == "TAPERED"):
            "SECT_I": {"vSIZE_PSC_A": [...], "vSIZE_PSC_C": [...], "vSIZE_PSC_D": [...]},
            "SECT_J": {"vSIZE_PSC_A": [...], ...},
            "Y_VAR":  1,   # 1=linear, 2=parabolic
            "Z_VAR":  2,
            # Constant sections (SECTTYPE != "TAPERED"):
            # vSIZE arrays may be under SECT_I (confirmed from live model)
            # or directly under SECT_BEFORE in some Midas versions.
            "SECT_I": {"vSIZE_PSC_A": [...], ...},   ← observed layout
        }
    }

Supported section shapes
------------------------
``1CEL``  — single-cell PSC box section. Returns ``None`` for any other shape.

Dimension index conventions (values in Midas are **millimetres**)
-----------------------------------------------------------------
``vSIZE_PSC_A``  (6 elements):
    [0] top-slab thickness
    [1] bottom-slab thickness
    [4] inner-web height  (between inner faces of top and bottom slabs)
    → total height  h = A[0] + A[4] + A[1]

``vSIZE_PSC_C``  (10 elements):
    [6] top-flange (inner slab) thickness    → top_hf
    [9] bottom-flange outer-edge thickness   → bot_hf

``vSIZE_PSC_D``  (8 elements):
    [2] individual web thickness             → bw  (one web)

All returned values are converted to **metres**.

Tapered section variation laws (Z_VAR / Y_VAR inside SECT_BEFORE)
-----------------------------------------------------------------
    1 — Linear
    2 — Parabolic  h(t) = h_start + (h_end - h_start) × t²

``z_var`` / ``y_var`` are returned in the dict for tapered sections so the
coordinator can apply the correct interpolation formula in ``_height_at_node``.
"""
from __future__ import annotations

from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe(arr: List[float], idx: int) -> float:
    """Return ``arr[idx]`` as float, or 0.0 if out of bounds."""
    return float(arr[idx]) if idx < len(arr) else 0.0


def _extract_1cel_dims(size_props: dict) -> Dict[str, float]:
    """Extract cross-section dimensions from a ``1CEL`` size-array dict.

    Args:
        size_props: Dict containing ``vSIZE_PSC_A``, ``vSIZE_PSC_C``, and
                    ``vSIZE_PSC_D`` arrays with values in **millimetres**.

    Returns:
        ``{h, top_hf, bw, bot_hf}`` — all in **metres**.
    """
    A: List[float] = size_props.get("vSIZE_PSC_A", [])
    C: List[float] = size_props.get("vSIZE_PSC_C", [])
    D: List[float] = size_props.get("vSIZE_PSC_D", [])

    h      = (_safe(A, 0) + _safe(A, 4) + _safe(A, 1)) / 1000.0
    top_hf = _safe(C, 6) / 1000.0
    bot_hf = _safe(C, 9) / 1000.0
    bw     = _safe(D, 2) / 1000.0

    return {"h": h, "top_hf": top_hf, "bw": bw, "bot_hf": bot_hf}


def _find_size_source(sect_def: dict) -> dict:
    """Return the dict that contains vSIZE_PSC_A for a constant section.

    Midas stores the size arrays under ``SECT_I`` inside ``SECT_BEFORE``
    even for constant (non-tapered) sections.  This helper checks for the
    arrays directly on ``sect_def`` first (forward-compatibility), then
    falls back to ``sect_def["SECT_I"]``.
    """
    if sect_def.get("vSIZE_PSC_A"):
        return sect_def
    sect_i = sect_def.get("SECT_I", {})
    if sect_i.get("vSIZE_PSC_A"):
        return sect_i
    # Nothing found — return sect_def so caller gets zero dims rather than crash
    return sect_def


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_section_geometry(
    sect_props: dict,
) -> Optional[Dict]:
    """Return cross-section geometric dimensions from a raw Midas SECT entry.

    The Midas REST API wraps all geometric data under a ``"SECT_BEFORE"``
    sub-dict.  ``SECTTYPE`` (tapered vs constant) lives at the top level;
    everything else (``SHAPE``, ``SECT_I``, ``SECT_J``, ``Y_VAR``,
    ``Z_VAR``, ``vSIZE_*``) lives inside ``SECT_BEFORE``.

    For both constant and tapered sections, the ``vSIZE_PSC_*`` arrays
    live inside ``SECT_BEFORE.SECT_I`` (and ``SECT_BEFORE.SECT_J`` for
    tapered).  ``vSIZE`` arrays directly under ``SECT_BEFORE`` are also
    checked as a fallback for forward-compatibility.

    Args:
        sect_props: Single section value-dict from ``GET /db/sect``
                    (the value for one section id key, not the outer
                    ``"SECT"`` wrapper).

    Returns:
        For **constant** sections::

            {"h": float, "top_hf": float, "bw": float, "bot_hf": float}

        For **tapered** sections (``SECTTYPE == "TAPERED"``)::

            {
                "h_start": float,   # height at SECT_I (I-end / first node)
                "h_end":   float,   # height at SECT_J (J-end / last node)
                "top_hf":  float,   # from SECT_I
                "bw":      float,   # from SECT_I
                "bot_hf":  float,   # from SECT_I
                "z_var":   int,     # 1=linear, 2=parabolic  ← governs h
                "y_var":   int,     # 1=linear (informational)
            }

        ``None`` if ``SHAPE`` is not ``"1CEL"`` or required sub-dicts are absent.
    """
    # All geometry lives inside SECT_BEFORE.
    # Fall back to top level for forward-compatibility.
    sect_def: dict = sect_props.get("SECT_BEFORE", sect_props)

    shape: str = sect_def.get("SHAPE", "").strip()
    if shape != "1CEL":
        return None

    # SECTTYPE is at the top level (outside SECT_BEFORE)
    sect_type: str = (sect_props.get("SECTTYPE") or "GENERAL").upper()

    if sect_type == "TAPERED":
        i_props = sect_def.get("SECT_I", {})
        j_props = sect_def.get("SECT_J", {})
        if not i_props or not j_props:
            return None
        dims_i = _extract_1cel_dims(i_props)
        dims_j = _extract_1cel_dims(j_props)
        z_var = int(sect_def.get("Z_VAR", 1))
        y_var = int(sect_def.get("Y_VAR", 1))
        return {
            "h_start": dims_i["h"],
            "h_end":   dims_j["h"],
            "top_hf":  dims_i["top_hf"],
            "bw":      dims_i["bw"],
            "bot_hf":  dims_i["bot_hf"],
            "z_var":   z_var,
            "y_var":   y_var,
        }

    # Constant section — vSIZE arrays may be directly under SECT_BEFORE
    # or under SECT_BEFORE.SECT_I (observed in live Midas model).
    size_src = _find_size_source(sect_def)
    dims = _extract_1cel_dims(size_src)
    return {
        "h":      dims["h"],
        "top_hf": dims["top_hf"],
        "bw":     dims["bw"],
        "bot_hf": dims["bot_hf"],
    }
