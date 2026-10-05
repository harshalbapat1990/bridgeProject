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
from bda.contracts.speckle_contracts.base_objects import UnitlessParameter

# =============================================================================
# PILE PARAMETERS
# =============================================================================
class PileIndexParameter(
    UnitlessParameter[int]
):
    name: Literal[
        "Pile Index"
    ] = "Pile Index"

    description: Literal[
        "Index of the pile"
    ] = "Index of the pile"

    symbol: None = None

class PileLengthParameter(LengthParameter):
    name: Literal[
        "Pile Length"
    ] = "Pile Length"

    description: Literal[
        "Length of the pile"
    ] = "Length of the pile"

    symbol: None = None

    provided_unit: Literal[
        "m",
        "ft",
    ]

    base_unit: Literal[
        "m"
    ] = "m"

    provided_value: float


class OffsetAlongSupportLineParameter(LengthParameter):
    name: Literal[
        "Offset Along Support Line"
    ] = "Offset Along Support Line"

    description: Literal[
        "Offset along support line"
    ] = "Offset along support line"

    symbol: None = None

    provided_unit: Literal[
        "m",
        "ft",
    ]

    base_unit: Literal[
        "m"
    ] = "m"

    provided_value: float


class OffsetNormalToSupportLineParameter(LengthParameter):
    name: Literal[
        "Offset Normal To Support Line"
    ] = "Offset Normal To Support Line"

    description: Literal[
        "Offset normal to support line"
    ] = "Offset normal to support line"

    symbol: None = None

    provided_unit: Literal[
        "m",
        "ft",
    ]

    base_unit: Literal[
        "m"
    ] = "m"

    provided_value: float


class SpringSpacingParameter(LengthParameter[list[float]]):
    name: Literal[
        "Spring Spacing"
    ] = "Spring Spacing"

    description: Literal[
        "Pile spring spacings"
    ] = "Pile spring spacings"

    symbol: None = None

    provided_unit: Literal[
        "m",
        "ft",
    ]

    base_unit: Literal[
        "m"
    ] = "m"

    provided_value: list[float]


# =============================================================================
# PILE PROPERTY SET
# =============================================================================


class PileGroupPropertiesParameters(
    BaseModel
):
    pile_index: (
        PileIndexParameter
    ) = Field(
        alias="Pile Index"
    )
    pile_length: (
        PileLengthParameter
    ) = Field(
        alias="Pile Length"
    )

    offset_along_support_line: (
        OffsetAlongSupportLineParameter
    ) = Field(
        alias="Offset Along Support Line"
    )

    offset_normal_to_support_line: (
        OffsetNormalToSupportLineParameter
    ) = Field(
        alias="Offset Normal To Support Line"
    )

    spring_spacing: (
        SpringSpacingParameter
    ) = Field(
        alias="Spring Spacing"
    )


class PileGroupProperties(
    GeometryGroupParameterProperties
):
    group_parameters: (
        PileGroupPropertiesParameters
    )

    @classmethod
    def create(
        cls,
        pile_index: float,
        pile_length: float,
        offset_along_support_line: float,
        offset_normal_to_support_line: float,
        spring_spacing: list[float],
        unit: Literal[
            "m",
            "ft",
        ] = "m",
        isUser: bool = True,
    ) -> "PileGroupProperties":

        return cls(
            isUser=isUser,
            group_parameters=(
                PileGroupPropertiesParameters(
                    **{ 
                        "Pile Index":
                            PileIndexParameter(
                                isUser=isUser,
                                provided_value=pile_index
                            ),
                        "Pile Length":
                            PileLengthParameter(
                                isUser=isUser,
                                provided_value=
                                    pile_length,
                                base_value=
                                    pile_length,
                                provided_unit=unit,
                            ),

                        "Offset Along Support Line":
                            OffsetAlongSupportLineParameter(
                                isUser=isUser,
                                provided_value=
                                    offset_along_support_line,
                                base_value=
                                    offset_along_support_line,
                                provided_unit=unit,
                            ),

                        "Offset Normal To Support Line":
                            OffsetNormalToSupportLineParameter(
                                isUser=isUser,
                                provided_value=
                                    offset_normal_to_support_line,
                                base_value=
                                    offset_normal_to_support_line,
                                provided_unit=unit,
                            ),

                        "Spring Spacing":
                            SpringSpacingParameter(
                                isUser=isUser,
                                provided_value=
                                    spring_spacing,
                                base_value=
                                    spring_spacing,
                                provided_unit=unit,
                            ),
                    }
                )
            ),
        )


# =============================================================================
# GROUP TYPE IDENTIFICATION
# =============================================================================


class PileStructureComponentGroupType(
    StructureComponentGroupType
):
    provided_value: Literal[
        StructuralComponentTypeParaModel.PILE
    ] = (
        StructuralComponentTypeParaModel.PILE
    )


# =============================================================================
# PILE METADATA
# =============================================================================


class GeometryGroupPropertiesPile(
    GeometryGroupProperties
):
    structural_component_type: (
        PileStructureComponentGroupType
    ) = Field(
        alias="Structural Component Type"
    )

    material_id: MaterialIdString = Field(
        alias="Material ID",
    )

    section_id: SectionIdString = Field(
        alias="Section ID",
    )

    group_properties: (
        PileGroupProperties
    ) = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersPile(
    GeometryGroupParameters
):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Pile"
    ] = "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Pile"

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-PILE$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: (
        GeometryGroupPropertiesPile
    )


# =============================================================================
# PILE GROUP
# =============================================================================


PileGroupElements = Annotated[
    GeometryGroupParametersPile,
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupPile(
    GeometryGroupBase
):
    bda_speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Pile"
    ] = "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Pile"

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-PILE$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    elements: list[
        PileGroupElements
    ] = Field(
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
                                    "BDA_Geometry_Group_Properties_Pile"
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
    def validate_pile_elements(self) -> "GeometryGroupPile":

        pile_properties_speckle_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_Pile"
        )

        pile_properties_count = sum(
            1
            for element in self.elements
            if element.bda_speckle_type
            == pile_properties_speckle_type
        )

        if pile_properties_count != 1:
            raise ValueError(
                "GeometryGroupPile.elements must contain "
                "exactly one "
                f"{pile_properties_speckle_type} object. "
                f"Found {pile_properties_count}."
            )

        return self

    @classmethod
    def create(
        cls,
        material_id: str = "concrete",
        section_id: str = "pile_section",
        pile_index: int = 1,
        pile_length: float = 10.0,
        offset_along_support_line: float = 0.0,
        offset_normal_to_support_line: float = 0.0,
        spring_spacing: list[float] | None = None,
        unit: Literal[
            "m",
            "ft",
        ] = "m",
        application_id: str = "COL-GEOMGROUP-0001-PILE",
        name: str | None = None,
        isUser: bool = True,
    ) -> "GeometryGroupPile":

        if spring_spacing is None:
            spring_spacing = []

        return cls(
            id=None,
            applicationId=application_id,
            name=name if name is not None else application_id,
            elements=[
                GeometryGroupParametersPile(
                    **{
                        "id": None,
                        "applicationId": application_id.replace(
                            "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                        ),
                        "properties":
                            GeometryGroupPropertiesPile(
                                **{
                                    "Structural Component Type":
                                        (
                                            PileStructureComponentGroupType()
                                        ),

                                    "Material ID":
                                        MaterialIdString(
                                            isUser=False,
                                            provided_value=material_id,
                                        ),

                                    "Section ID":
                                        SectionIdString(
                                            isUser=False,
                                            provided_value=section_id,
                                        ),

                                    "Geometry Group Properties":
                                        (
                                            PileGroupProperties.create(
                                                pile_index=pile_index,
                                                pile_length=
                                                    pile_length,
                                                offset_along_support_line=
                                                    offset_along_support_line,
                                                offset_normal_to_support_line=
                                                    offset_normal_to_support_line,
                                                spring_spacing=
                                                    spring_spacing,
                                                unit=unit,
                                                isUser=isUser,
                                            )
                                        ),
                                }
                            ),
                    }
                )
            ],
        )


if __name__ == "__main__":

    pile = GeometryGroupPile.create(
        material_id="M_Pile",
        section_id="S_Pile",
        pile_index=1,
        pile_length=20.0,
        offset_along_support_line=1.0,
        offset_normal_to_support_line=0.5,
        spring_spacing=[2.0, 2.0, 2.0, 2.0],
        unit="m",
        application_id="COL-GEOMGROUP-0001-PILE",
    )

    print(
        pile.model_dump_json(
            indent=4
        )
    )