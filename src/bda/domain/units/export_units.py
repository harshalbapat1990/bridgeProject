"""
Export unit sets for each supported UnitSystem.

Usage pattern
-------------
In the main ``export()`` method of every exporter::

    eu = get_export_units(amm.unit_system)

Pass ``eu`` down to every helper so Quantity values are converted to plain
``float`` before being sent to the API::

    to_float(material.E, eu.pressure)          # → float in kPa / kip·ft⁻²
    to_float(dim.height, eu.length)             # → float in m / ft
"""
from __future__ import annotations

from dataclasses import dataclass
from pint import Unit

from bda.domain.enums import UnitSystem
from bda.domain.units.registry import ureg


@dataclass(frozen=True)
class ExportUnits:
    """Target physical units when serialising Quantity fields for export APIs."""
    length: Unit            # section dimensions
    force: Unit
    pressure: Unit          # E, strengths            → kPa  | kip ft⁻²
    weight_density: Unit    # material unit weight    → kN m⁻³ | kip ft⁻³
    temperature_coef: Unit  # thermal expansion coef → °C⁻¹ | °F⁻¹


# ---------------------------------------------------------------------------
# Canonical unit sets
# ---------------------------------------------------------------------------

_SI = ExportUnits(
    length=ureg.meter,
    force=ureg.kilonewton,
    pressure=ureg.kilopascal,
    weight_density=ureg.kilonewton / ureg.meter ** 3,
    temperature_coef=ureg.delta_degC ** -1,
)

_IM = ExportUnits(
    length=ureg.foot,
    force=ureg.kip,
    pressure=ureg.kip / ureg.foot ** 2,
    weight_density=ureg.kip / ureg.foot ** 3,
    temperature_coef=ureg.delta_degF ** -1,
)

_MAP: dict[UnitSystem, ExportUnits] = {
    UnitSystem.SI: _SI,
    UnitSystem.IM: _IM,
}


def get_export_units(unit_system: UnitSystem) -> ExportUnits:
    """Return the :class:`ExportUnits` for *unit_system*.

    Raises:
        ValueError: if *unit_system* has no registered unit set.
    """
    units = _MAP.get(unit_system)
    if units is None:
        raise ValueError(f"No export unit set registered for {unit_system!r}")
    return units


def to_float(quantity, unit) -> float:
    """Convert *quantity* (pint Quantity) to *unit* and return the plain magnitude."""
    if quantity is None:
        raise TypeError(f"Expected Quantity convertible to {unit!r}, got None")
    return float(quantity.to(unit).magnitude)

