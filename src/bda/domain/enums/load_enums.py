"""Enums describing how FE-level loads are typed, targeted and distributed."""
from enum import Enum


class LoadType(str, Enum):
    """Geometric kind of a load."""
    POINT = "point"
    LINE = "line"
    AREA = "area"  # reserved for panel elements, not implemented


class LoadTargetType(str, Enum):
    """Kind of analytical object a load is attached to."""
    NODE = "node"
    BEAM = "beam"
    PANEL = "panel"  # reserved for future panel (plate) elements, not implemented


class LoadDistribution(str, Enum):
    """Variation of a distributed load along/over its target.

    Only ``UNIFORM`` is supported at the moment; the enum exists so that
    trapezoidal or arbitrary distributions can be added without changing
    the load classes' signatures.
    """
    UNIFORM = "uniform"


class LocalAxis(str, Enum):
    """Local axis of a 1D element used to express a load offset."""
    Y = "y"
    Z = "z"


class CoordinateSystem(str, Enum):
    """Coordinate system in which load components are expressed.

    Only ``GLOBAL`` is supported at the moment; ``LOCAL`` is a planned extension.
    """
    GLOBAL = "global"
