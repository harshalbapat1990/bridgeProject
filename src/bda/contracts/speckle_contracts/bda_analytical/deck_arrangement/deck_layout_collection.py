from bda.contracts.speckle_contracts.base_objects import BridgeCollection
from bda.contracts.speckle_contracts.bda_analytical.deck_arrangement.deck_layouts.deck_layout_base import DeckLayoutCollectionBase
from typing import Annotated, ClassVar, Literal, Union
import re
from pydantic  import Field, field_validator

DeckLayouts = Annotated[
    Union[
        DeckLayoutCollectionBase,
    ],
    Field(discriminator="bda_speckle_type"),
]

class DeckLayoutCollection(BridgeCollection):
    COLLECTION_ID_PATTERN: ClassVar[re.Pattern] = re.compile(
            r"^COL-DECK-LAYOUTS$"
        )
    applicationId: Literal["COL-DECK-LAYOUTS"] = "COL-DECK-LAYOUTS"
    name: Literal["Deck Layouts"] = "Deck Layouts"
    bda_speckle_type: str = "Speckle.Core.Models.Collections.Collection:Deck_Layout"

    elements: list[DeckLayouts] = Field(
            default_factory=list
        )  # type: ignore[reportIncompatibleVariableOverride]
    
    @classmethod
    def create(
        cls,
        deck_layouts: list[DeckLayouts] | None = None,
    ) -> "DeckLayoutCollection":
        return cls(
            elements=deck_layouts or [],
        )

    @field_validator("applicationId")
    @classmethod
    def validate_application_id(
        cls,
        value: str,
    ):

        if not cls.COLLECTION_ID_PATTERN.match(value):
            raise ValueError(
                "Deck Layouts collection applicationId must be COL-DECK-LAYOUTS"
            )

        return value