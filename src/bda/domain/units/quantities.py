from __future__ import annotations

from pint import Quantity
from bda.domain.units.registry import ureg


class _BaseQuantity(Quantity):
    """Shared base for strongly-typed quantity markers."""


# --- Base quantities ---
class Length(_BaseQuantity):
    """Marker type for length quantities."""
    pass


class Force(_BaseQuantity):
    """Marker type for force quantities."""
    pass


class Temperature(_BaseQuantity):
    """Marker type for temperature quantities."""
    pass


class TemperatureCoefficient(_BaseQuantity):
    """Marker type for thermal expansion coefficient quantities."""
    pass



class Pressure(_BaseQuantity):
    """Marker type for pressure quantities."""
    pass


class Area(_BaseQuantity):
    """Marker type for area quantities."""
    pass


class Volume(_BaseQuantity):
    """Marker type for volume quantities."""
    pass


class Mass(_BaseQuantity):
    """Marker type for mass quantities."""
    pass


class Time(_BaseQuantity):
    """Marker type for time quantities."""
    pass


class MassDensity(_BaseQuantity):
    """Marker type for mass density quantities."""
    pass


class WeightDensity(_BaseQuantity):
    """Marker type for unit weight quantities."""
    pass


class Angle(_BaseQuantity):
    """Marker type for angular quantities."""
    pass


# --- Derived / engineering quantities ---
class Moment(_BaseQuantity):
    """Marker type for bending/torsional moment quantities."""
    pass


class Stress(Pressure):
    """Marker type for stress quantities (pressure semantics)."""


class Energy(_BaseQuantity):
    """Marker type for energy quantities."""
    pass


__all__ = [
    "Length", "Force", "Temperature", "Pressure",
    "Area", "Volume", "Mass", "Time", 'MassDensity',
    'WeightDensity', 'TemperatureCoefficient',
    "Moment", "Stress", "Energy", "Angle",
    "ureg",
]
