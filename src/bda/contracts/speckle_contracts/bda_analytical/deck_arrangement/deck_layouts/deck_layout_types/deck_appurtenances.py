from bda.contracts.speckle_contracts.bda_analytical.deck_arrangement.deck_layouts.deck_appurtenances.deck_appurtenance_base import (
    LinearFixedDeckAppurtenance,
    SurfaceFixedDeckAppurtenance,
)

from pydantic import Field
from typing import ClassVar, Literal
from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes

class EdgeBarrier(LinearFixedDeckAppurtenance):
    NAME_PATTERN: ClassVar[str] = r"^EdgeBarrier ([1-9]\d*)$"
    name: str = Field("EdgeBarrier 1", pattern=NAME_PATTERN)
    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_DECK_APPURTENANCE_EDGE_BARRIER.value
    ] = Field(
        SpeckleTypes.DATA_OBJECT_BDA_DECK_APPURTENANCE_EDGE_BARRIER.value,
        frozen=True,
    )

class VergeFootway(SurfaceFixedDeckAppurtenance):
    NAME_PATTERN: ClassVar[str] = r"^Verge ([1-9]\d*)$"
    name: str = Field("Verge 1", pattern=NAME_PATTERN)
    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_DECK_APPURTENANCE_VERGE_FOOTWAY.value
    ] = Field(
        SpeckleTypes.DATA_OBJECT_BDA_DECK_APPURTENANCE_VERGE_FOOTWAY.value,
        frozen=True,
    )

class Carriageway(SurfaceFixedDeckAppurtenance):
    NAME_PATTERN: ClassVar[str] = r"^Carriageway ([1-9]\d*)$"
    name: str = Field("Carriageway 1", pattern=NAME_PATTERN)
    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_DECK_APPURTENANCE_CARRIAGEWAY.value
    ] = Field(
        SpeckleTypes.DATA_OBJECT_BDA_DECK_APPURTENANCE_CARRIAGEWAY.value,
        frozen=True,
    )

class CentralReserve(SurfaceFixedDeckAppurtenance):
    NAME_PATTERN: ClassVar[str] = r"^CentralReserve ([1-9]\d*)$"
    name: str = Field("Central Reserve 1", pattern=NAME_PATTERN)
    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_DECK_APPURTENANCE_CENTRAL_RESERVE.value
    ] = Field(
        SpeckleTypes.DATA_OBJECT_BDA_DECK_APPURTENANCE_CENTRAL_RESERVE.value,
        frozen=True,
    )
