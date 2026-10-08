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
    EdgeBarrier,
    VergeFootway,
)

SingleCarriagewayAppurtenanceElement = Annotated[
    Union[EdgeBarrier, VergeFootway, Carriageway],
    Field(discriminator="bda_speckle_type"),
]


class SingleCarriagewayStandardAppurtenances(StandardLayoutAppurtenancesCollection):
    name: Literal["Standard Layout Appurtenances"] = "Standard Layout Appurtenances"  # pyright: ignore[reportIncompatibleVariableOverride]

    elements: list[SingleCarriagewayAppurtenanceElement] = Field(  # pyright: ignore[reportIncompatibleVariableOverride]
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
                    "minContains": 1,
                    "maxContains": 1,
                },
                {
                    "contains": {"properties": {"bda_speckle_type": {"const": "Objects.Data.DataObject:BDA_Deck_Appurtenance_Verge_Footway"}}},
                    "minContains": 0,
                    "maxContains": 2,
                },
            ]
        },
    )

    @model_validator(mode="after")  # pyright: ignore[reportArgumentType]
    def _validate_mandatory_appurtenances(self) -> "SingleCarriagewayStandardAppurtenances":
        types = [type(e) for e in self.elements]
        if types.count(EdgeBarrier) != 2:
            raise ValueError(f"elements must contain exactly 2 EdgeBarrier instances, found {types.count(EdgeBarrier)}")
        if types.count(Carriageway) != 1:
            raise ValueError(f"elements must contain exactly 1 Carriageway instance, found {types.count(Carriageway)}")
        if types.count(VergeFootway) > 2:
            raise ValueError(f"elements may contain at most 2 VergeFootway instances, found {types.count(VergeFootway)}")
        return self

    @classmethod
    def create(
        cls,
        application_id: str,
        edge_barrier_1: EdgeBarrier,
        carriageway_1: Carriageway,
        edge_barrier_2: EdgeBarrier,
        verge_footway_1: VergeFootway | None = None,
        verge_footway_2: VergeFootway | None = None,
    ) -> "SingleCarriagewayStandardAppurtenances":
        items: list[SingleCarriagewayAppurtenanceElement] = [edge_barrier_1]
        if verge_footway_1 is not None:
            items.append(verge_footway_1)
        items.append(carriageway_1)
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


SingleCarriagewayLayoutElement = Annotated[
    Union[
        DeckLayoutPropertiesBase,
        SingleCarriagewayStandardAppurtenances,
        MiscellaneousItemsCollection,
    ],
    Field(discriminator="name"),
]


class SingleCarriagewayDeckLayoutCollection(DeckLayoutCollectionBase):
    name: Literal["Single Carriageway"] = "Single Carriageway"

    elements: list[SingleCarriagewayLayoutElement] = Field(default_factory=list)  # pyright: ignore[reportIncompatibleVariableOverride]

    @classmethod
    def create(
        cls,
        application_id: str,
        properties: DeckLayoutPropertiesBase,
        standard_appurtenances: SingleCarriagewayStandardAppurtenances,
        miscellaneous_items: MiscellaneousItemsCollection | None = None,
    ) -> "SingleCarriagewayDeckLayoutCollection":
        items: list[SingleCarriagewayLayoutElement] = [properties, standard_appurtenances]
        if miscellaneous_items is not None:
            items.append(miscellaneous_items)
        return cls(
            applicationId=application_id,
            speckle_type="Speckle.Core.Models.Collections.Collection",
            bda_speckle_type="Speckle.Core.Models.Collections.Collection",
            elements=items,
        )
