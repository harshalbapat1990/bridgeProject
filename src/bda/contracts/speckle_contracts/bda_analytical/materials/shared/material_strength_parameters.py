from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, StrictFloat

from bda.contracts.speckle_contracts.base_objects import (
    ParameterGroup,
)
from bda.contracts.speckle_contracts.unit_parameters import StrictPressureParameter


# ==========================================================
# Yield Strength
# ==========================================================

class SpecifiedMinimumYieldStrength(StrictPressureParameter):
    name: Literal[
        "Specified Minimum Yield Strength"
    ] = "Specified Minimum Yield Strength"

    symbol: Literal["fy,min"] = "fy,min"

    description: Literal[
        "Specified minimum yield strength"
    ] = "Specified minimum yield strength"

    provided_value: StrictFloat
    provided_unit: Literal["kN/m²", "lbf/ft²"]

    base_unit: Literal["Pa"] = "Pa"
    base_value: StrictFloat

    isUser: bool


class ExpectedYieldStrength(StrictPressureParameter):
    name: Literal[
        "Expected Yield Strength"
    ] = "Expected Yield Strength"

    symbol: Literal["fy,exp"] = "fy,exp"

    description: Literal[
        "Expected yield strength"
    ] = "Expected yield strength"

    provided_value: StrictFloat
    provided_unit: Literal["kN/m²", "lbf/ft²"]

    base_unit: Literal["Pa"] = "Pa"
    base_value: StrictFloat

    isUser: bool


# ==========================================================
# Tensile Strength
# ==========================================================

class SpecifiedMinimumTensileStrength(StrictPressureParameter):
    name: Literal[
        "Specified Minimum Tensile Strength"
    ] = "Specified Minimum Tensile Strength"

    symbol: Literal["fu,min"] = "fu,min"

    description: Literal[
        "Specified minimum tensile strength"
    ] = "Specified minimum tensile strength"

    provided_value: StrictFloat
    provided_unit: Literal["kN/m²", "lbf/ft²"]

    base_unit: Literal["Pa"] = "Pa"
    base_value: StrictFloat

    isUser: bool


class ExpectedTensileStrength(StrictPressureParameter):
    name: Literal[
        "Expected Tensile Strength"
    ] = "Expected Tensile Strength"

    symbol: Literal["fu,exp"] = "fu,exp"

    description: Literal[
        "Expected tensile strength"
    ] = "Expected tensile strength"

    provided_value: StrictFloat
    provided_unit: Literal["kN/m²", "lbf/ft²"]

    base_unit: Literal["Pa"] = "Pa"
    base_value: StrictFloat

    isUser: bool