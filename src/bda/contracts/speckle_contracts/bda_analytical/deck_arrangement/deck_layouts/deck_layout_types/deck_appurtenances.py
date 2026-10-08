from bda.contracts.speckle_contracts.bda_analytical.deck_arrangement.deck_layouts.deck_appurtenances.deck_appurtenance_base import (
    LinearFixedDeckAppurtenance,
    SurfaceFixedDeckAppurtenance,
)

from pydantic import Field
from typing import ClassVar, Literal

class EdgeBarrier(LinearFixedDeckAppurtenance):
    NAME_PATTERN: ClassVar[str] = r"^EdgeBarrier ([1-9]\d*)$"
    name: str = Field("EdgeBarrier 1", pattern=NAME_PATTERN)
    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Deck_Appurtenance_Edge_Barrier"
    ] = Field(
        "Objects.Data.DataObject:BDA_Deck_Appurtenance_Edge_Barrier",
        frozen=True,
    )

class VergeFootway(SurfaceFixedDeckAppurtenance):
    NAME_PATTERN: ClassVar[str] = r"^Verge ([1-9]\d*)$"
    name: str = Field("Verge 1", pattern=NAME_PATTERN)
    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Deck_Appurtenance_Verge_Footway"
    ] = Field(
        "Objects.Data.DataObject:BDA_Deck_Appurtenance_Verge_Footway",
        frozen=True,
    )

class Carriageway(SurfaceFixedDeckAppurtenance):
    NAME_PATTERN: ClassVar[str] = r"^Carriageway ([1-9]\d*)$"
    name: str = Field("Carriageway 1", pattern=NAME_PATTERN)
    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Deck_Appurtenance_Carriageway"
    ] = Field(
        "Objects.Data.DataObject:BDA_Deck_Appurtenance_Carriageway",
        frozen=True,
    )

class CentralReserve(SurfaceFixedDeckAppurtenance):
    NAME_PATTERN: ClassVar[str] = r"^CentralReserve ([1-9]\d*)$"
    name: str = Field("Central Reserve 1", pattern=NAME_PATTERN)
    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Deck_Appurtenance_Central_Reserve"
    ] = Field(
        "Objects.Data.DataObject:BDA_Deck_Appurtenance_Central_Reserve",
        frozen=True,
    )