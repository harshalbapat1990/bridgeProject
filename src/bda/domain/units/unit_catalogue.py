"""Curated catalogue of engineering units, grouped by physical dimension.

Why this module exists
----------------------
``UnitParameter`` subclasses declare a physical dimension (``UNIT_DIMENSION``),
and the generated JSON schema needs to tell upstream consumers which units they
are actually allowed to send. Pint cannot answer that question:

* ``ureg.get_compatible_units("[length]")`` omits prefixed and imperial units --
  it does not return ``mm``, ``cm``, ``ft`` or ``in``, which are exactly the
  units the contracts use.
* For compound dimensions such as ``[force] / [length] ** 3`` and
  ``[temperature] ** -1`` it returns an empty set.

So *enumeration* comes from this hand-curated table, while *validation* still
comes from pint, which is entirely reliable for dimensional checks. Nothing here
is trusted blindly: ``validate_catalogue`` re-checks every entry against pint,
and ``UnitParameter``'s import-time guard re-checks the entries actually in use.

Maintenance
-----------
To widen the units a consumer may send for a dimension, add them to
``_CATALOGUE_SOURCE`` below -- every parameter class on that dimension picks them
up in its schema automatically, with no per-class edit.

Entries are ordered most-preferred first; that order is what a UI dropdown will
show, so put the unit most authors should pick at the front.
"""

from __future__ import annotations

from bda.domain.units.registry import ureg

# Dimension string -> allowable units, most-preferred first.
#
# Keys are written for readability; they are normalised through pint below, so
# "[force] / [length]**3" and "[force] / [length] ** 3" resolve to one entry.
#
# Deliberately absent: "[force] * [length]". Pint cannot distinguish a moment
# from an energy -- both reduce to the same dimensionality -- so a shared default
# would offer joules where a bending moment belongs. Those two classes declare
# ALLOWED_UNITS explicitly instead.
#
# Also absent: angles. Pint treats radians as dimensionless, so a dimension key
# would collide with strains and ratios. AngleParameter declares ALLOWED_UNITS.
_CATALOGUE_SOURCE: dict[str, tuple[str, ...]] = {
    "[length]": (
        "m",
        "mm",
        "cm",
        "km",
        "ft",
        "in",
        "yd",
    ),
    "[length] ** 2": (
        "m²",
        "mm²",
        "cm²",
        "ft²",
        "in²",
    ),
    "[length] ** 3": (
        "m³",
        "mm³",
        "cm³",
        "ft³",
        "in³",
    ),
    "[force]": (
        "kN",
        "N",
        "MN",
        "kip",
        "lbf",
    ),
    # Covers pressure, stress and elastic modulus -- all the same dimension.
    "[pressure]": (
        "Pa",
        "kPa",
        "MPa",
        "GPa",
        "N/mm²",
        "kN/m²",
        "psi",
        "ksi",
        "kips/in²",
        "lbf/ft²",
    ),
    "[force] / [length]": (
        "kN/m",
        "N/m",
        "kip/ft",
        "lbf/ft",
    ),
    # Weight density (unit weight).
    "[force] / [length] ** 3": (
        "kN/m³",
        "N/m³",
        "kips/ft³",
        "lbf/ft³",
    ),
    "[mass]": (
        "kg",
        "g",
        "t",
        "lb",
    ),
    # Mass density.
    "[mass] / [length] ** 3": (
        "kg/m³",
        "g/cm³",
        "lb/ft³",
    ),
    "[time]": (
        "s",
        "min",
        "hr",
        "day",
    ),
    "[temperature]": (
        "degC",
        "degF",
        "K",
    ),
    # Coefficient of thermal expansion. These are *delta* units: a coefficient
    # is per temperature interval, not per absolute temperature.
    "[temperature] ** -1": (
        "1/Δ°C",
        "1/Δ°F",
        "1/K",
    ),
    "[length] / [time]": (
        "m/s",
        "km/hr",
        "ft/s",
        "mph",
    ),
    "[length] / [time] ** 2": (
        "m/s²",
        "ft/s²",
    ),
}


def canonical_dimension(dimension: str):
    """Normalise a dimension string to pint's canonical dimensionality.

    Returns a hashable ``UnitsContainer``. Raises ``ValueError`` if pint cannot
    parse the dimension, so a typo in a ``UNIT_DIMENSION`` surfaces immediately.
    """
    try:
        return ureg.get_dimensionality(dimension)
    except Exception as exc:
        raise ValueError(
            f"Not a valid pint dimension: {dimension!r} ({exc})"
        ) from exc


def _build_index() -> dict[object, tuple[str, ...]]:
    index: dict[object, tuple[str, ...]] = {}

    for dimension, units in _CATALOGUE_SOURCE.items():
        key = canonical_dimension(dimension)

        if key in index:
            raise ValueError(
                f"Duplicate catalogue dimension {dimension!r}: it reduces to "
                f"{key}, which is already populated. Merge the two entries."
            )

        index[key] = units

    return index


_BY_DIMENSIONALITY = _build_index()


def units_for_dimension(dimension: str | None) -> tuple[str, ...] | None:
    """Catalogued units for a dimension, or None if there is no entry.

    None means nothing can be published for the dimension. Lenient by design: an
    unparseable dimension returns None rather than raising, so a lookup is always
    safe. Rejecting a bad dimension is the job of the import-time guard in
    ``UnitParameter``, which reports it against the offending class.
    """
    if not dimension:
        return None

    try:
        key = canonical_dimension(dimension)
    except ValueError:
        return None

    return _BY_DIMENSIONALITY.get(key)


def is_compatible(unit: str, dimension: str) -> bool:
    """True if ``unit`` is dimensionally compatible with ``dimension``."""
    return ureg.Quantity(1.0, unit).check(dimension)


def validate_catalogue() -> None:
    """Assert every catalogued unit parses and matches its dimension.

    Called by the test suite. Keeps a typo in this table from being published as
    an allowable unit that then fails at payload validation.
    """
    problems: list[str] = []

    for dimension, units in _CATALOGUE_SOURCE.items():
        for unit in units:
            try:
                compatible = is_compatible(unit, dimension)
            except Exception as exc:
                problems.append(
                    f"{dimension}: {unit!r} is not parseable by pint ({exc})"
                )
                continue

            if not compatible:
                problems.append(
                    f"{dimension}: {unit!r} is not dimensionally compatible"
                )

    if problems:
        raise ValueError(
            "Invalid unit catalogue entries:\n  "
            + "\n  ".join(problems)
        )
