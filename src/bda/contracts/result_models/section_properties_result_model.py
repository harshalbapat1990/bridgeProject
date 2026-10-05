"""Intermediate DTO for section geometric properties from FEM software.

`SectionPropertiesResultModel` carries raw numeric values from the FEM
API — no Pint quantities, no domain logic. The mapper
(`application.mapping.results.section_properties_mapper`) applies
units and produces the domain section properties object.

POST pipeline pattern (mirrors PRE):
    FEM API → SectionPropertiesResultModel → SectionPropertiesMapper → domain
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SectionPropertiesResultModel:
    """Raw section geometric properties from the FEM API.

    All numeric fields are bare floats in SI units (m², m⁴, m³).
    The importer is responsible for ensuring canonical units are active.

    These properties are software-agnostic: both Midas Civil and CSI
    Bridge fetchers produce this same DTO. Only the mapper and the
    fetcher differ per software; the DTO and mapper are shared.

    Attributes
    ----------
    section_name:
        Section name as defined in the FEM model.
    area:
        Cross-sectional area A (m²).
    shear_area_y:
        Effective shear area in the local-2 direction Asy (m²).
    shear_area_z:
        Effective shear area in the local-3 direction Asz (m²).
    torsional_inertia:
        Torsional constant J / Ixx (m⁴).
    moment_inertia_y:
        Second moment of area about the local-2 axis Iyy (m⁴).
        Weak-axis for standard bridge girder sections.
    moment_inertia_z:
        Second moment of area about the local-3 axis Izz (m⁴).
        Major axis for standard bridge girder sections.
    czp:
        Distance from centroid to extreme fibre on positive local-3
        side (m). Used to compute elastic section modulus Wz = Izz / czp.
    czm:
        Distance from centroid to extreme fibre on negative local-3
        side (m).
    cyp:
        Distance from centroid to extreme fibre on positive local-2
        side (m).
    cym:
        Distance from centroid to extreme fibre on negative local-2
        side (m).
    """

    section_name: str
    area: float              # A   (m²)
    shear_area_y: float      # Asy (m²)
    shear_area_z: float      # Asz (m²)
    torsional_inertia: float # J   (m⁴)
    moment_inertia_y: float  # Iyy (m⁴)
    moment_inertia_z: float  # Izz (m⁴)
    czp: float               # distance to +z fibre (m)
    czm: float               # distance to -z fibre (m)
    cyp: float               # distance to +y fibre (m)
    cym: float               # distance to -y fibre (m)
    unit_system: str         # must equal CANONICAL_UNIT_SYSTEM ("kN-m-C")
                             # asserted by SectionPropertiesMapper before Q_() is applied
