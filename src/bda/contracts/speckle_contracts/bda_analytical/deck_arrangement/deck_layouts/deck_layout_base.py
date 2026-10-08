from __future__ import annotations

from bda.contracts.speckle_contracts.base_objects import BridgeCollection, BridgeDataObject, Parameter, BridgeDataObjectProperties, EnumParameter
import re
from bda.contracts.speckle_contracts.unit_parameters import LengthParameter
from bda.contracts.paramodel.deck_appurtenances.enums import BridgeDeckLayoutTypeParaModel
from bda.contracts.speckle_contracts.bda_analytical.deck_arrangement.deck_layouts.deck_appurtenances.deck_appurtenance_base import (
    DeckAppurtenance,
    DeckAppurtenanceByOffest,
    LinearByOffsetDeckAppurtenance,
    SurfaceByOffsetDeckAppurtenance,
)
from typing import Annotated, ClassVar, Literal, Union
from pydantic import Field, field_validator, model_validator

# Deck Properties Parameters

class DeckLayoutType(
    EnumParameter[BridgeDeckLayoutTypeParaModel]
):
    name: Literal["Deck Layout Type"] = "Deck Layout Type"

    description: Literal[
        "Type of deck layout (e.g., single Carriageway, Dual Carriageway, etc.)"
    ] = "Type of deck layout (e.g., single Carriageway, Dual Carriageway, etc.)"

    provided_value: BridgeDeckLayoutTypeParaModel
    
class LayoutIndex(Parameter[int]):
    name: Literal["Layout Index"] = "Layout Index"

    description: Literal[
        "Index of the deck layout in the collection"
    ] = "Index of the deck layout in the collection"

    provided_value: int = Field(0,ge=0)

class StartXPoint(LengthParameter):
    name: Literal["Start X Point"] = "Start X Point"

    description: Literal[
        "X-coordinate of the start point of the deck layout"
    ] = "X-coordinate of the start point of the deck layout"

    provided_value: float = Field(0.0,ge=0.0)
    base_value: float = Field(0.0,ge=0.0)

class DeckLayoutDataObjectPropertiesBase(BridgeDataObjectProperties):
    """Shared metadata for deck layout properties."""

    deck_layout_type: DeckLayoutType = Field(alias="Deck Layout Type")
    layout_index: LayoutIndex = Field(alias="Layout Index")

class DeckLayoutPropertiesBase(BridgeDataObject):
    """Shared metadata for deck layout properties."""

    name: Literal["Deck Layout Properties"] = "Deck Layout Properties"

    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Deck_Layout_Properties"
    ] = "Objects.Data.DataObject:BDA_Deck_Layout_Properties"

    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Deck_Layout_Properties"
    ] = Field(..., frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = (
        r"^PROP-DECK-LAYOUT-\d{4}-[A-Z0-9]+(?:-[A-Z0-9]+)*$"
    )
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)
    properties: DeckLayoutDataObjectPropertiesBase


class StandardLayoutAppurtenancesCollection(BridgeCollection):
    """Mandatory sub-collection holding the fixed-position deck appurtenances."""

    STD_LAYOUT_ID_PATTERN: ClassVar[re.Pattern] = re.compile(
        r"^STD-DECK-LAYOUT-\d{4}-[A-Z0-9]+(?:-[A-Z0-9]+)*$"
    )

    applicationId: str = Field(pattern=STD_LAYOUT_ID_PATTERN)
    name: Literal["Standard Layout Appurtenances"] = "Standard Layout Appurtenances"

    speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection"
    ] = "Speckle.Core.Models.Collections.Collection"

    bda_speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection"
    ] = Field(..., frozen=True)

    elements: list[DeckAppurtenance] = Field(default_factory=list)

    @field_validator("applicationId")
    @classmethod
    def validate_std_layout_application_id(cls, value: str) -> str:
        if not cls.STD_LAYOUT_ID_PATTERN.match(value):
            raise ValueError(
                "StandardLayoutAppurtenancesCollection applicationId must match "
                "STD-DECK-LAYOUT-<INDEX>-<DECK LAYOUT TYPE>"
            )
        return value

    @classmethod
    def create(
        cls,
        application_id: str,
        appurtenances: list[DeckAppurtenance] | None = None,
    ) -> "StandardLayoutAppurtenancesCollection":
        return cls(
            applicationId=application_id,
            bda_speckle_type="Speckle.Core.Models.Collections.Collection",
            elements=appurtenances or [],
        )


class MiscellaneousItemsCollection(BridgeCollection):
    """Optional child collection of a deck layout holding freely-placed appurtenances."""

    MISC_ITEMS_ID_PATTERN: ClassVar[re.Pattern] = re.compile(
        r"^MISC-DECK-LAYOUT-\d{4}-[A-Z0-9]+(?:-[A-Z0-9]+)*$"
    )

    applicationId: str = Field(pattern=MISC_ITEMS_ID_PATTERN)

    name: Literal["Miscellaneous Items"] = "Miscellaneous Items"

    speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection"
    ] = "Speckle.Core.Models.Collections.Collection"

    bda_speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection"
    ] = Field(..., frozen=True)

    elements: list[DeckAppurtenanceByOffest] = Field(default_factory=list)

    @field_validator("applicationId")
    @classmethod
    def validate_misc_items_application_id(cls, value: str) -> str:
        if not cls.MISC_ITEMS_ID_PATTERN.match(value):
            raise ValueError(
                "MiscellaneousItemsCollection applicationId must match "
                "MISC-DECK-LAYOUT-<INDEX>-<DECK LAYOUT TYPE>"
            )
        return value

    @classmethod
    def create(
        cls,
        application_id: str,
        items: list[LinearByOffsetDeckAppurtenance | SurfaceByOffsetDeckAppurtenance] | None = None,
    ) -> "MiscellaneousItemsCollection":
        return cls(
            applicationId=application_id,
            bda_speckle_type="Speckle.Core.Models.Collections.Collection",
            elements=items or [],
        )


DeckLayoutCollectionElement = Annotated[
    Union[
        DeckLayoutPropertiesBase,
        StandardLayoutAppurtenancesCollection,
        MiscellaneousItemsCollection,
    ],
    Field(discriminator="name"),
]

DeckLayout = DeckLayoutPropertiesBase


class DeckLayoutCollectionBase(BridgeCollection):
    DECK_LAYOUT_ID_PATTERN: ClassVar[re.Pattern] = re.compile(
        r"^COL-DECK-LAYOUT-\d{4}-[A-Z0-9]+(?:-[A-Z0-9]+)*$"
    )

    applicationId: str = Field(pattern=DECK_LAYOUT_ID_PATTERN)

    elements: list[DeckLayoutCollectionElement] = Field(default_factory=list)

    @field_validator("applicationId")
    @classmethod
    def validate_deck_layout_application_id(
        cls,
        value: str,
    ):
        if not cls.DECK_LAYOUT_ID_PATTERN.match(value):
            raise ValueError(
                "Deck layout applicationId must match COL-DECK-LAYOUT-<INDEX>-<DECK LAYOUT TYPE>"
            )
        return value

    @model_validator(mode="after")
    def validate_single_properties_object(self) -> "DeckLayoutCollectionBase":
        props = [e for e in self.elements if isinstance(e, DeckLayoutPropertiesBase)]
        if len(props) != 1:
            raise ValueError(
                f"DeckLayoutCollectionBase must contain exactly one DeckLayoutPropertiesBase, "
                f"found {len(props)}"
            )
        expected_prop_id = self.applicationId.replace("COL-", "PROP-", 1)
        if props[0].applicationId != expected_prop_id:
            raise ValueError(
                f"DeckLayoutPropertiesBase applicationId must be '{expected_prop_id}' "
                f"(collection id with 'COL' replaced by 'PROP'), "
                f"got '{props[0].applicationId}'"
            )
        return self

    @model_validator(mode="after")
    def validate_single_standard_layout_appurtenances(self) -> "DeckLayoutCollectionBase":
        std = [e for e in self.elements if isinstance(e, StandardLayoutAppurtenancesCollection)]
        if len(std) != 1:
            raise ValueError(
                f"DeckLayoutCollectionBase must contain exactly one "
                f"StandardLayoutAppurtenancesCollection, found {len(std)}"
            )
        expected_std_id = self.applicationId.replace("COL-", "STD-", 1)
        if std[0].applicationId != expected_std_id:
            raise ValueError(
                f"StandardLayoutAppurtenancesCollection applicationId must be '{expected_std_id}' "
                f"(collection id with 'COL' replaced by 'STD'), "
                f"got '{std[0].applicationId}'"
            )
        return self

    @model_validator(mode="after")
    def validate_single_miscellaneous_items_collection(self) -> "DeckLayoutCollectionBase":
        misc = [e for e in self.elements if isinstance(e, MiscellaneousItemsCollection)]
        if len(misc) > 1:
            raise ValueError(
                f"DeckLayoutCollectionBase may contain at most one MiscellaneousItemsCollection, found {len(misc)}"
            )
        if misc:
            expected_misc_id = self.applicationId.replace("COL-", "MISC-", 1)
            if misc[0].applicationId != expected_misc_id:
                raise ValueError(
                    f"MiscellaneousItemsCollection applicationId must be '{expected_misc_id}' "
                    f"(collection id with 'COL' replaced by 'MISC'), "
                    f"got '{misc[0].applicationId}'"
                )
        return self


