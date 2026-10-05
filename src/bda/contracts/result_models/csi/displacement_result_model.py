"""Intermediate DTO for raw nodal-displacement data from CSI Bridge.

`CsiDisplacementResultModel` carries raw numeric values directly from the
CSI Bridge COM API — no Pint quantities, no domain logic. The mapper
(`application.mapping.results.csi.csi_displacement_result_mapper`) applies
units and produces the canonical `NodalDisplacement` domain object.

POST pipeline pattern:
    CSI API → CsiDisplacementResultModel → CsiDisplacementResultMapper → NodalDisplacement

Precondition: the CSI session is in canonical units (kN, m, C) via
`CsiUnitsContext` before `Results.JointDispl` is called.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CsiDisplacementResultModel:
    """Raw nodal-displacement values for one result row from the CSI Bridge API.

    All numeric fields are bare floats in metres / radians (canonical
    units). The importer is responsible for ensuring the CSI session is
    set to canonical units before constructing these objects.

    Displacements are in the **global coordinate system**, consistent
    with the `NodalDisplacement` domain convention.

    Confirmed layout (verified against live CSI Bridge session 2026-04-09):
        JointDispl returns UX, UY, UZ in metres and RX, RY, RZ in radians
        when the session unit system is kN·m·C.

    Attributes
    ----------
    node_name:
        CSI Bridge point object name (e.g. ``'J10'``).
    load_case:
        Load case name as returned by the CSI API.
    step_type:
        ``None`` for single-valued cases; ``'Max'`` or ``'Min'`` for
        combination envelope cases.
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
                         # asserted by CsiDisplacementResultMapper before Q_() is applied
