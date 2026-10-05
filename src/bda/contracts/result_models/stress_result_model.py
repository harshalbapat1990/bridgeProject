"""Intermediate DTO for raw element-stress data from FEM software.

`StressResultModel` carries the raw numeric values as they come from the
FEM API — no Pint quantities, no domain logic. The mapper
(`application.mapping.results.stress_result_mapper`) applies units and
produces the canonical `ElementStress` domain object.

POST pipeline pattern (mirrors PRE):
    FEM API → StressResultModel → StressResultMapper → ElementStress

Design note — stress points
---------------------------
Unlike forces and displacements, which have a fixed number of scalar
fields per row, stresses may be reported at multiple fiber points on
the cross-section (top, bottom, corners, etc.). The exact format
depends on the FEM software and table type.

`stress_points` is a tuple of ``(y_m, z_m, sigma_raw)`` triples:
    y_m       — local-2 distance from centroid (metres)
    z_m       — local-3 distance from centroid (metres)
    sigma_raw — normal stress in kN/m² (canonical when UNIT={kN, m})

For a scaffold implementation before the API format is confirmed, the
fetcher may produce a single-point tuple at (0.0, 0.0, sigma) using
whatever column is available. Once the response layout is confirmed
(see ``BEAMSTRESS``/``BEAMSTRSVBM`` endpoint research), this should be
updated to extract all reported fiber points.

Status: TABLE_TYPE and column layout TBD — confirmed from probe suite.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StressResultModel:
    """Raw element-stress values for one end-row from the FEM API.

    Attributes
    ----------
    element_name:
        FEM software element name (e.g. ``'10'``, ``'F10'``).
    load_case:
        Load case name as returned by the FEM API (suffix stripped).
    step_type:
        ``None`` for single-valued cases; ``'Max'`` or ``'Min'`` for
        combination envelope cases.
    part:
        ``'I'`` or ``'J'`` — element end, normalised from the FEM
        API part string (e.g. ``'PartI'`` → ``'I'``).
    stress_points:
        Tuple of ``(y_m, z_m, sigma_raw)`` triples. ``y_m`` and
        ``z_m`` are section-centroid offsets in metres (local-2 and
        local-3 respectively). ``sigma_raw`` is the normal stress in
        kN/m² (tension positive), valid when the Midas request body
        specifies ``UNIT: {"FORCE": "kN", "DIST": "m"}``.
    unit_system:
        Must equal ``CANONICAL_UNIT_SYSTEM`` (``"kN-m-C"``).
        Asserted by ``StressResultMapper`` before ``Q_()`` is applied.
    """

    element_name: str
    load_case: str
    step_type: str | None
    part: str                                      # 'I' or 'J'
    stress_points: tuple[tuple[float, float, float], ...]
    unit_system: str   # must equal CANONICAL_UNIT_SYSTEM ("kN-m-C")
                       # asserted by StressResultMapper before Q_() is applied
