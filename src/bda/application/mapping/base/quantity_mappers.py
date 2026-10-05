"""
Pint quantity helpers shared across all mappers.
"""
from __future__ import annotations

import re
from typing import Optional

from pint import Quantity

from bda.contracts.shared import QuantityParaModel
from bda.domain.units.registry import ureg

# ---------------------------------------------------------------------------
# Unit string normalisation
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Unicode normalization maps
# ---------------------------------------------------------------------------

# Superscripts → exponent notation
_SUPERSCRIPTS = {
    "¹": "**1",
    "²": "**2",
    "³": "**3",
}

# Temperature-related replacements
_TEMP_ALIASES = {
    "°C": "degC",
    "°F": "degF",
    "Δ°C": "delta_degC",
    "Δ°F": "delta_degF",
}

# Explicit aliases for engineering shorthands that pint does not recognise.
# "C" in pint = coulomb; for temperature-difference units use delta_degC or K.
_UNIT_ALIASES: dict[str, str] = {
    "1/degC": "1/delta_degC",
    "1/degF": "1/delta_degF",
    "1/°C": "1/delta_degC",
    "1/°F": "1/delta_degF",
    "1/Δ°C": "1/delta_degC",
    "1/Δ°F": "1/delta_degF",
}


# Regex: replace trailing digits on a unit token with exponent notation.
# e.g. "kN/m3" → "kN/m**3",  "N/mm2" → "N/mm**2"
_POWER_RE = re.compile(r"([A-Za-z]+)(\d+)")

# Remove weird Unicode spacing
_SPACING_RE = re.compile(r"\s+")



def _fix_encoding(unit: str) -> str:
    """
    Fix common UTF-8 mis-decoding issues (e.g. Â², Î”, Â°).
    """
    if not unit:
        return unit

    # Try proper recovery first
    try:
        fixed = unit.encode("latin1").decode("utf-8")
    except UnicodeError:
        fixed = unit

    # Fallback replacements (defensive)
    return (
        fixed
        .replace("Â²", "²")
        .replace("Â³", "³")
        .replace("Â°", "°")
        .replace("Î”", "Δ")
    )

def _replace_superscripts(unit: str) -> str:
    """Replace Unicode superscripts with pint-compatible exponent notation."""
    for k, v in _SUPERSCRIPTS.items():
        unit = unit.replace(k, v)
    return unit


def _replace_temperature_units(unit: str) -> str:
    """Normalize temperature units and differences."""
    for k, v in _TEMP_ALIASES.items():
        unit = unit.replace(k, v)
    return unit


def _apply_power_regex(unit: str) -> str:
    """
    Replace patterns like 'mm2' → 'mm**2'.
    Safe because it only targets letter+digit sequences.
    """
    return _POWER_RE.sub(r"\1**\2", unit)


def _cleanup_spacing(unit: str) -> str:
    """Remove unnecessary whitespace."""
    return _SPACING_RE.sub("", unit)


def _normalize_unit(unit: str) -> str:
    """
    Return a pint-compatible unit string for engineering notations.

    Handles:
    - Unicode superscripts (², ³)
    - temperature symbols (°C, Δ°C)
    - implicit exponents (mm2)
    - known problematic cases (1/°C)
    """
    if not unit:
        return unit

    # Step 0: fix encoding issues
    unit = _fix_encoding(unit)

    # Step 1: remove spaces
    unit = _cleanup_spacing(unit)

    # Step 2: replace temperature Unicode
    unit = _replace_temperature_units(unit)

    # Step 3: replace superscripts
    unit = _replace_superscripts(unit)

    # Step 4: explicit alias override (highest priority)
    if unit in _UNIT_ALIASES:
        return _UNIT_ALIASES[unit]

    # Step 5: fix patterns like mm2
    unit = _apply_power_regex(unit)

    # Step 6: handle remaining problematic cases
    # Example: "1/degC" → should still be delta
    if unit.startswith("1/degC"):
        return "1/delta_degC"
    if unit.startswith("1/degF"):
        return "1/delta_degF"

    return unit


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def to_pint(q: QuantityParaModel) -> Quantity:  # type: ignore[type-arg]
    """Convert a QuantityParaModel to a pint.Quantity."""
    if q.unit:
        normalized = _normalize_unit(q.unit)
        return ureg.Quantity(q.value, normalized)
    return ureg.Quantity(q.value)


def to_pint_optional(q: Optional[QuantityParaModel]) -> Quantity | None:  # type: ignore[type-arg]
    """Return None when the field is absent."""
    return to_pint(q) if q is not None else None


