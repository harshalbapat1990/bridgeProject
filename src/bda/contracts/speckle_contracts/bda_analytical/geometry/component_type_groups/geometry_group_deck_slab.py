from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes
from typing import Annotated, ClassVar, Literal, Union

from pydantic import BaseModel, Field, model_validator

from bda.contracts.paramodel.groups.enums import (
    StructuralComponentTypeParaModel,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.geometry_group_base import (
    GeometryGroupBase,
    GeometryGroupParameters,
    GeometryGroupProperties,
    GeometryGroupParameterProperties,
    StructureComponentGroupType,
    MaterialIdString,
    SectionIdString,
)

# =============================================================================
# GROUP TYPE IDENTIFICATION
# =============================================================================


class DeckSlabStructureComponentGroupType(
    StructureComponentGroupType
):
    provided_value: Literal[
        StructuralComponentTypeParaModel.DECK_SLAB
    ] = StructuralComponentTypeParaModel.DECK_SLAB


# =============================================================================
# DECK SLAB PROPERTY SET
# =============================================================================


class DeckSlabGroupPropertiesParameters(BaseModel):
    pass


class DeckSlabGroupProperties(GeometryGroupParameterProperties):
    group_parameters: DeckSlabGroupPropertiesParameters

    @classmethod
    def create(cls, isUser: bool = True) -> "DeckSlabGroupProperties":
        return cls(
            isUser=isUser,
            group_parameters=DeckSlabGroupPropertiesParameters(),
        )


# =============================================================================
# COMMON DECK SLAB METADATA
# =============================================================================


class GeometryGroupPropertiesDeckSlab(GeometryGroupProperties):
    structural_component_type: (
        DeckSlabStructureComponentGroupType
    ) = Field(
        alias="Structural Component Type"
    )

    material_id: MaterialIdString = Field(
        alias="Material ID",
    )

    section_id: SectionIdString = Field(
        alias="Section ID",
    )

    group_properties: DeckSlabGroupProperties = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersDeckSlab(
    GeometryGroupParameters
):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_DECK_SLAB
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_DECK_SLAB.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-DECK-SLAB$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: GeometryGroupPropertiesDeckSlab


# =============================================================================
# DECK SLAB GROUP
# =============================================================================


DeckSlabGroupElements = Annotated[
    Union[
        GeometryGroupParametersDeckSlab
    ],
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupDeckSlab(
    GeometryGroupBase
):
    bda_speckle_type: Literal[
        SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_DECK_SLAB
    ] = Field(SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_DECK_SLAB.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-DECK-SLAB$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    elements: list[DeckSlabGroupElements] = Field(
        default_factory=list,
        json_schema_extra={
            "minItems": 1,
            "allOf": [
                {
                    # Exactly one deck slab properties object
                    "contains": {
                        "type": "object",
                        "properties": {
                            "bda_speckle_type": {
                                "const": (
                                    "Objects.Data.DataObject:"
                                    "BDA_Geometry_Group_Properties_"
                                    "Deck_Slab"
                                )
                            }
                        },
                        "required": ["bda_speckle_type"],
                    },
                    "minContains": 1,
                    "maxContains": 1,
                },
            ],
        },
    )

    @model_validator(mode="after")
    def validate_deck_slab_elements(self) -> "GeometryGroupDeckSlab":
        properties_speckle_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_Deck_Slab"
        )

        properties_count = sum(
            1
            for element in self.elements
            if element.bda_speckle_type == properties_speckle_type
        )

        if properties_count != 1:
            raise ValueError(
                "GeometryGroupDeckSlab.elements must contain "
                "exactly one "
                f"{properties_speckle_type} object. "
                f"Found {properties_count}."
            )

        return self
    
    @classmethod
    def create(
        cls,
        material_id: str,
        section_id: str,
        application_id: str = "COL-GEOMGROUP-0001-DECK-SLAB",
        name: str|None = None,
        isUser: bool = True,
    ) -> "GeometryGroupDeckSlab":

        return cls(
            id=None,
            name=name if name is not None else "Deck Slab",  # TODO: Improve Autonaming
            applicationId=application_id,
            elements=[
                GeometryGroupParametersDeckSlab(
                    **{
                        "id": None,
                        "applicationId": application_id.replace(
                            "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                        ),
                        "properties": GeometryGroupPropertiesDeckSlab(
                            **{
                                "Structural Component Type":
                                    DeckSlabStructureComponentGroupType(),

                                "Material ID":
                                    MaterialIdString(
                                        provided_value=material_id
                                    ),

                                "Section ID":
                                    SectionIdString(
                                        provided_value=section_id
                                    ),

                                "Geometry Group Properties":
                                    DeckSlabGroupProperties.create(
                                        isUser=isUser,
                                    ),
                            }
                        )
                    }
                )
            ],
        )
    
if __name__ == "__main__":
    # Example usage
    deck_slab_group = GeometryGroupDeckSlab.create(
        material_id="MATERIAL_1",
        section_id="SECTION_1",
        application_id="COL-GEOMGROUP-0001-DECK-SLAB"
    )

    print(deck_slab_group.model_dump_json(indent=4))