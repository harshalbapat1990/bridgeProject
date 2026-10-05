"""Enums describing load case categories."""
from __future__ import annotations

from enum import Enum


class LoadCaseType(str, Enum):
    """High-level classification of a load case as seen by the importer.

    The source program may have finer-grained types (linear static,
    nonlinear static, buffeted, etc.) but for post-processing we only care
    about whether a case produces a single result or a min/max envelope.
    """
    SINGLE_VALUED = "single_valued"  # linear static, single row per (elem, end)
    COMBINATION = "combination"       # linear combo, returns CB:max / CB:min
    ENVELOPE = "envelope"             # explicit envelope combination

    # Note: program-specific case kinds such as Midas Civil NX moving-load
    # cases or time-history max/min results must be reduced to ENVELOPE by
    # the importer. Extend this enum only if a calculator requires per-
    # extreme provenance metadata (e.g. "which truck position governed the
    # shear maximum"); see finding F6 in
    # docs/importer_review_midas_compat.md.
