from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field, model_validator

from bda.contracts.speckle_contracts.bda_analytical.deck_arrangement.deck_layouts.deck_layout_base import (
    DeckLayoutCollectionBase,
    DeckLayoutPropertiesBase,
    MiscellaneousItemsCollection,
    StandardLayoutAppurtenancesCollection,
)
from bda.contracts.speckle_contracts.bda_analytical.deck_arrangement.deck_layouts.deck_layout_types.deck_appurtenances import (
    Carriageway,
    CentralReserve,
    EdgeBarrier,
    VergeFootway,
)

DualCarriagewayAppurtenanceElement = Annotated[
    Union[EdgeBarrier, VergeFootway, Carriageway, CentralReserve],
    Field(discriminator="bda_speckle_type"),
]


class DualCarriagewayStandardAppurtenances(StandardLayoutAppurtenancesCollection):
    name: Literal["Standard Layout Appurtenances"] = "Standard Layout Appurtenances"  # pyright: ignore[reportIncompatibleVariableOverride]

    elements: list[DualCarriagewayAppurtenanceElement] = Field(  # pyright: ignore[reportIncompatibleVariableOverride]
        default_factory=list,
        json_schema_extra={
            "allOf": [
                {
                    "contains": {"properties": {"bda_speckle_type": {"const": "Objects.Data.DataObject:BDA_Deck_Appurtenance_Edge_Barrier"}}},
                    "minContains": 2,
                    "maxContains": 2,
                },
                {
                    "contains": {"properties": {"bda_speckle_type": {"const": "Objects.Data.DataObject:BDA_Deck_Appurtenance_Carriageway"}}},
                    "minContains": 2,
                    "maxContains": 2,
                },
                {
                    "contains": {"properties": {"bda_speckle_type": {"const": "Objects.Data.DataObject:BDA_Deck_Appurtenance_Verge_Footway"}}},
                    "minContains": 0,
                    "maxContains": 2,
                },
                {
                    "contains": {"properties": {"bda_speckle_type": {"const": "Objects.Data.DataObject:BDA_Deck_Appurtenance_Central_Reserve"}}},
                    "minContains": 0,
                    "maxContains": 1,
                },
            ]
        },
    )

    @model_validator(mode="after")  # pyright: ignore[reportArgumentType]
    def _validate_mandatory_appurtenances(self) -> "DualCarriagewayStandardAppurtenances":
        types = [type(e) for e in self.elements]
        if types.count(EdgeBarrier) != 2:
            raise ValueError(f"elements must contain exactly 2 EdgeBarrier instances, found {types.count(EdgeBarrier)}")
        if types.count(Carriageway) != 2:
            raise ValueError(f"elements must contain exactly 2 Carriageway instances, found {types.count(Carriageway)}")
        if types.count(VergeFootway) > 2:
            raise ValueError(f"elements may contain at most 2 VergeFootway instances, found {types.count(VergeFootway)}")
        if types.count(CentralReserve) > 1:
            raise ValueError(f"elements may contain at most 1 CentralReserve instance, found {types.count(CentralReserve)}")
        return self

    @classmethod
    def create(
        cls,
        application_id: str,
        edge_barrier_1: EdgeBarrier,
        carriageway_1: Carriageway,
        carriageway_2: Carriageway,
        edge_barrier_2: EdgeBarrier,
        verge_footway_1: VergeFootway | None = None,
        central_reserve: CentralReserve | None = None,
        verge_footway_2: VergeFootway | None = None,
    ) -> "DualCarriagewayStandardAppurtenances":
        items: list[DualCarriagewayAppurtenanceElement] = [edge_barrier_1]
        if verge_footway_1 is not None:
            items.append(verge_footway_1)
        items.append(carriageway_1)
        if central_reserve is not None:
            items.append(central_reserve)
        items.append(carriageway_2)
        if verge_footway_2 is not None:
            items.append(verge_footway_2)
        items.append(edge_barrier_2)
        return cls(
            applicationId=application_id,
            name="Standard Layout Appurtenances",
            speckle_type="Speckle.Core.Models.Collections.Collection",
            bda_speckle_type="Speckle.Core.Models.Collections.Collection",
            elements=items,  # pyright: ignore[reportArgumentType]
        )


DualCarriagewayLayoutElement = Annotated[
    Union[
        DeckLayoutPropertiesBase,
        DualCarriagewayStandardAppurtenances,
        MiscellaneousItemsCollection,
    ],
    Field(discriminator="name"),
]


class DualCarriagewayDeckLayoutCollection(DeckLayoutCollectionBase):
    name: Literal["Dual Carriageway"] = "Dual Carriageway"

    elements: list[DualCarriagewayLayoutElement] = Field(default_factory=list)  # pyright: ignore[reportIncompatibleVariableOverride]

    @classmethod
    def create(
        cls,
        application_id: str,
        properties: DeckLayoutPropertiesBase,
        standard_appurtenances: DualCarriagewayStandardAppurtenances,
        miscellaneous_items: MiscellaneousItemsCollection | None = None,
    ) -> "DualCarriagewayDeckLayoutCollection":
        items: list[DualCarriagewayLayoutElement] = [properties, standard_appurtenances]
        if miscellaneous_items is not None:
            items.append(miscellaneous_items)
        return cls(
            applicationId=application_id,
            speckle_type="Speckle.Core.Models.Collections.Collection",
            bda_speckle_type="Speckle.Core.Models.Collections.Collection",
            elements=items,
        )
