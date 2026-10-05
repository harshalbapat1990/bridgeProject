"""Intermediate DTO for raw frame-force data from FEM software.

`ForceResultModel` carries the raw numeric values exactly as they come
from the FEM API — no Pint quantities, no domain logic. The mapper
(`application.mapping.results.force_result_mapper`) is responsible for
applying units and producing the canonical `ForceVector` domain object.

This mirrors the PRE pipeline pattern:
    IDataStoreProvider → ...ParaModel → Mapper → Domain
in the POST pipeline:
    FEM API → ForceResultModel → ForceResultMapper → ForceVector
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ForceResultModel:
    """Raw frame-force values for one station row from the FEM API.

    All numeric fields are bare floats in kN / kN·m (canonical units).
    The importer is responsible for ensuring the FEM session is set to
    canonical units before constructing these objects.

    Attributes
    ----------
    element_name:
        FEM software element name (e.g. ``'10'``, ``'F10'``).
    load_case:
        Load case name as returned by the FEM API.
    step_type:
        ``None`` for single-valued cases; ``'Max'`` or ``'Min'`` for
        combination envelope cases (CSI Bridge / Midas convention).
    elm_station:
        Station distance along the *element* from the I end (metres).
        Must be ElmSta (not ObjSta) for CSI Bridge.
    axial:
        Axial force P in kN. Tension positive.
    shear_y:
        Shear in the element local-2 direction (kN). For a standard
        horizontal bridge girder, this is vertical shear.
    shear_z:
        Shear in the element local-3 direction (kN). For planar
        models this is ~0.
    torsion:
        Torsional moment T in kN·m.
    moment_y:
        Bending moment about local-2 (kN·m). Weak-axis for standard
        bridge girder; ~0 for planar models.
    moment_z:
        Bending moment about local-3 (kN·m). Major/sagging bending.
    """

    element_name: str
    load_case: str
    step_type: str | None
    elm_station: float   # metres — use ElmSta, not ObjSta
    axial: float         # P     → domain Fx  (kN)
    shear_y: float       # V2    → domain Fy  (kN)
    shear_z: float       # V3    → domain Fz  (kN)
    torsion: float       # T     → domain Mx  (kN·m)
    moment_y: float      # M2    → domain My  (kN·m)
    moment_z: float      # M3    → domain Mz  (kN·m)
    unit_system: str     # must equal CANONICAL_UNIT_SYSTEM ("kN-m-C")
                         # asserted by ForceResultMapper before Q_() is applied
