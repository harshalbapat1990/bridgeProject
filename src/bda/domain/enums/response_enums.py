"""Enums describing analysis response types fetched by the importer."""
from __future__ import annotations

from enum import Enum


class ResponseType(str, Enum):
    """Top-level category of an analysis response."""
    ELEMENT_FORCE = "element_force"
    ELEMENT_STRESS = "element_stress"
    NODAL_DISPLACEMENT = "nodal_displacement"


class ForceComponent(str, Enum):
    """Components of a local-axis frame force/moment vector.

    Canonical naming: Fx (axial), Fy/Fz (shear), Mx (torsion), My/Mz (moments).
    This is the ordering the ResultSet uses regardless of the source program.
    """
    Fx = "Fx"
    Fy = "Fy"
    Fz = "Fz"
    Mx = "Mx"
    My = "My"
    Mz = "Mz"


class DisplacementComponent(str, Enum):
    """Components of a nodal displacement vector in global axes.

    Naming is deliberately ``UX/UY/UZ`` and ``RX/RY/RZ`` to make the
    global-frame convention impossible to miss. See the module docstring
    of ``modules_post/domain/results/result_primitives.py`` for the binding
    contract that every importer must satisfy.
    """
    UX = "UX"
    UY = "UY"
    UZ = "UZ"
    RX = "RX"
    RY = "RY"
    RZ = "RZ"


class ElementEnd(str, Enum):
    """End of a 1D element where a result is reported."""
    I = "I"
    J = "J"
