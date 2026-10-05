from typing import Literal

from bda.contracts.speckle_contracts.base_objects import (
    UnitlessParameter,
)

class SupportIndexParameter(
    UnitlessParameter[int]
):
    name: Literal[
        "Support Index"
    ] = "Support Index"

    description: Literal[
        "Index of the support"
    ] = "Index of the support"

    symbol: None = None
    provided_value: int


class BearingIndexParameter(
    UnitlessParameter[int]
):
    name: Literal[
        "Bearing Index"
    ] = "Bearing Index"

    description: Literal[
        "Index of the bearing"
    ] = "Index of the bearing"

    symbol: None = None
    provided_value: int
    