from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes
from typing import Annotated, ClassVar, Literal

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
    SectionIdString,
    MaterialIdString,
)

from bda.contracts.speckle_contracts.unit_parameters import LengthParameter


class VerticalOffsetAtLeft(LengthParameter):
    name: Literal["Vertical Offset at Left"] = "Vertical Offset at Left"

    description: Literal[
        "Vertical offset at the left end of the chord"
    ] = "Vertical offset at the left end of the chord"

    symbol: None = None

    provided_unit: Literal["m", "ft"]
    base_unit: Literal["m"] = "m"


class VerticalOffsetAtRight(LengthParameter):
    name: Literal["Vertical Offset at Right"] = "Vertical Offset at Right"

    description: Literal[
        "Vertical offset at the right end of the chord"
    ] = "Vertical offset at the right end of the chord"

    symbol: None = None

    provided_unit: Literal["m", "ft"]
    base_unit: Literal["m"] = "m"


# =============================================================================
# CHORD PROPERTY SET
# =============================================================================


class ChordGroupPropertiesParameters(BaseModel):
    vertical_offset_at_left: VerticalOffsetAtLeft = Field(
        alias="Vertical Offset at Left"
    )

    vertical_offset_at_right: VerticalOffsetAtRight = Field(
        alias="Vertical Offset at Right"
    )


class ChordGroupProperties(GeometryGroupParameterProperties):
    group_parameters: ChordGroupPropertiesParameters

    @classmethod
    def create(
        cls,
        vertical_offset_left: float,
        vertical_offset_right: float,
        vertical_offset_left_unit: Literal["m", "ft"] = "m",
        vertical_offset_right_unit: Literal["m", "ft"] = "m",
        isUser: bool = True,
    ) -> "ChordGroupProperties":
        return cls(
            isUser=isUser,
            group_parameters=ChordGroupPropertiesParameters(
                **{
                    "Vertical Offset at Left": VerticalOffsetAtLeft(
                        isUser=isUser,
                        provided_value=vertical_offset_left,
                        provided_unit=vertical_offset_left_unit,
                        base_value=vertical_offset_left,
                    ),
                    "Vertical Offset at Right": VerticalOffsetAtRight(
                        isUser=isUser,
                        provided_value=vertical_offset_right,
                        provided_unit=vertical_offset_right_unit,
                        base_value=vertical_offset_right,
                    ),
                }
            ),
        )


# =============================================================================
# GROUP TYPE IDENTIFICATION
# =============================================================================


class ChordStructureComponentGroupType(StructureComponentGroupType):
    provided_value: Literal[
        StructuralComponentTypeParaModel.CHORD
    ] = StructuralComponentTypeParaModel.CHORD


# =============================================================================
# CHORD METADATA
# =============================================================================


class GeometryGroupPropertiesChord(GeometryGroupProperties):
    structural_component_type: ChordStructureComponentGroupType = Field(
        alias="Structural Component Type"
    )

    material_id: MaterialIdString = Field(
        alias="Material ID",
    )

    section_id: SectionIdString = Field(
        alias="Section ID",
    )

    group_properties: ChordGroupProperties = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersChord(GeometryGroupParameters):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_CHORD
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_CHORD.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-CHORD$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: GeometryGroupPropertiesChord


# =============================================================================
# CHORD GROUP
# =============================================================================


ChordGroupElements = Annotated[
    GeometryGroupParametersChord,
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupChord(GeometryGroupBase):
    bda_speckle_type: Literal[
        SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_CHORD
    ] = Field(SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_CHORD.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-CHORD$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    elements: list[ChordGroupElements] = Field(
        default_factory=list,
        json_schema_extra={
            "minItems": 1,
            "allOf": [
                {
                    "contains": {
                        "type": "object",
                        "properties": {
                            "bda_speckle_type": {
                                "const": (
                                    "Objects.Data.DataObject:"
                                    "BDA_Geometry_Group_Properties_Chord"
                                )
                            }
                        },
                        "required": ["bda_speckle_type"],
                    },
                    "minContains": 1,
                    "maxContains": 1,
                }
            ],
        },
    )

    @model_validator(mode="after")
    def validate_chord_elements(self) -> "GeometryGroupChord":
        chord_properties_speckle_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_Chord"
        )

        chord_properties_count = sum(
            1
            for element in self.elements
            if element.bda_speckle_type == chord_properties_speckle_type
        )

        if chord_properties_count != 1:
            raise ValueError(
                "GeometryGroupChord.elements must contain exactly one "
                f"{chord_properties_speckle_type} object. "
                f"Found {chord_properties_count}."
            )

        return self

    @classmethod
    def create(
        cls,
        material_id: str,
        section_id: str,
        vertical_offset_left: float,
        vertical_offset_right: float,
        application_id: str = "COL-GEOMGROUP-0001-CHORD",
        name: str|None = None,
        isUser: bool = True,
        vertical_offset_left_unit: Literal["m", "ft"] = "m",
        vertical_offset_right_unit: Literal["m", "ft"] = "m",
    ) -> "GeometryGroupChord":
        return cls(
            id=None,
            applicationId=application_id,
            name=name if name is not None else f"Chord", #TODO: Improve Autonaming
            elements=[
                GeometryGroupParametersChord(
                    **{
                        "id": None,
                        "applicationId": application_id.replace(
                            "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                        ),
                        "properties": GeometryGroupPropertiesChord(
                            **{
                                "Structural Component Type": ChordStructureComponentGroupType(),
                                "Material ID": MaterialIdString(
                                    isUser=False,
                                    provided_value=material_id,
                                ),
                                "Section ID": SectionIdString(
                                    isUser=False,
                                    provided_value=section_id,
                                ),
                                "Geometry Group Properties": ChordGroupProperties.create(
                                    vertical_offset_left=vertical_offset_left,
                                    vertical_offset_right=vertical_offset_right,
                                    vertical_offset_left_unit=vertical_offset_left_unit,
                                    vertical_offset_right_unit=vertical_offset_right_unit,
                                    isUser=isUser,
                                ),
                            }
                        ),
                    }
                )
            ],
        )


if __name__ == "__main__":
    chord = GeometryGroupChord.create(
        material_id="M1",
        section_id="S1",
        vertical_offset_left=0.5,
        vertical_offset_right=0.5,
        application_id="COL-GEOMGROUP-0001-CHORD",
    )

    print(chord.model_dump_json(indent=4))