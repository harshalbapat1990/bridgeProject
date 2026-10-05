"""Intermediate DTO for raw nodal-displacement data from Midas Civil NX.

`MidasDisplacementResultModel` carries raw numeric values directly from the
Midas REST API — no Pint quantities, no domain logic. The mapper
(`application.mapping.results.midas.midas_displacement_result_mapper`) applies
units and produces the canonical `NodalDisplacement` domain object.

POST pipeline pattern:
    Midas API → MidasDisplacementResultModel → MidasDisplacementResultMapper → NodalDisplacement

NOTE: Whether Midas returns rotations in radians or degrees depends on user
settings. The fetcher must convert to radians before constructing this DTO
if needed (TBD — see midas_displacements_fetcher.py).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MidasDisplacementResultModel:
    """Raw nodal-displacement values for one result row from the Midas API.

    All numeric fields are bare floats in metres / radians (canonical
    units). The importer is responsible for ensuring the Midas session is
    set to canonical units before constructing these objects.

    Displacements are in the **global coordinate system** (``DISPLACEMENTG``
    table type), consistent with the `NodalDisplacement` domain convention.

    Attributes
    ----------
    node_name:
        Midas node number as a string (e.g. ``'10'``).
    load_case:
        Load case name as returned by the Midas API (combo suffix stripped).
    step_type:
        ``None`` for single-valued cases; ``'Max'`` or ``'Min'`` for
        combination envelope cases (``CB:max`` / ``CB:min``).
    ux:
        Translation along global X (metres).
    uy:
        Translation along global Y (metres).
    uz:
        Translation along global Z (metres).
    rx:
        Rotation about global X (radians).
    ry:
        Rotation about global Y (radians).
    rz:
        Rotation about global Z (radians).
    """

    node_name: str
    load_case: str
    step_type: str | None
    ux: float   # global X translation (m)
    uy: float   # global Y translation (m)
    uz: float   # global Z translation (m)
    rx: float   # rotation about global X (rad)
    ry: float   # rotation about global Y (rad)
    rz: float   # rotation about global Z (rad)
    unit_system: str     # must equal CANONICAL_UNIT_SYSTEM ("kN-m-C")
                         # asserted by MidasDisplacementResultMapper before Q_() is applied
