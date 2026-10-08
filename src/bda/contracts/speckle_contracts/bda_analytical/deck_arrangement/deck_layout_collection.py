from bda.contracts.speckle_contracts.base_objects import BridgeCollection
from bda.contracts.speckle_contracts.bda_analytical.deck_arrangement.deck_layouts.deck_layout_base import (
    DeckLayoutCollectionBase,
)
from bda.contracts.speckle_contracts.bda_analytical.deck_arrangement.deck_layouts.deck_layout_types.deck_layout_dual_carriageway import (
    DualCarriagewayDeckLayoutCollection,
)
from bda.contracts.speckle_contracts.bda_analytical.deck_arrangement.deck_layouts.deck_layout_types.deck_layout_single_carriageway import (
    SingleCarriagewayDeckLayoutCollection,
)
from typing import Annotated, ClassVar, Literal, Union
import re
from pydantic  import Field, field_validator

DeckLayouts = Annotated[
    Union[
        SingleCarriagewayDeckLayoutCollection,
        DualCarriagewayDeckLayoutCollection,
    ],
    Field(discriminator="name"),
]

class DeckLayoutCollection(BridgeCollection):
    COLLECTION_ID_PATTERN: ClassVar[re.Pattern] = re.compile(
            r"^COL-DECK-LAYOUTS$"
        )
    applicationId: Literal["COL-DECK-LAYOUTS"] = "COL-DECK-LAYOUTS"
    name: Literal["Deck Layouts"] = "Deck Layouts"
    bda_speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection"
    ] = Field("Speckle.Core.Models.Collections.Collection", frozen=True)

    elements: list[DeckLayouts] = Field(
            default_factory=list
        )  # type: ignore[reportIncompatibleVariableOverride]
    
    @classmethod
    def create(
        cls,
        deck_layouts: list[DeckLayouts] | None = None,
    ) -> "DeckLayoutCollection":
        return cls(
            bda_speckle_type="Speckle.Core.Models.Collections.Collection",
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
