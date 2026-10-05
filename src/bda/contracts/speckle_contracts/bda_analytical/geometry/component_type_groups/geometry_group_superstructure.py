from typing import Annotated, ClassVar, Literal, Union

from pydantic import Field, BaseModel, model_validator

from bda.contracts.paramodel.groups.enums import (
    StructuralComponentTypeParaModel,
    SpacingTypeParaModel,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.geometry_group_base import (
    GeometryGroupBase,
    GeometryGroupParameters,
    GeometryGroupProperties,
    GeometryGroupParameterProperties,
    StructureComponentGroupType,
)

from bda.contracts.speckle_contracts.base_objects import (
    UnitlessParameter
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_span import GeometryGroupSpan
from bda.contracts.speckle_contracts.unit_parameters import LengthParameter

# =============================================================================
# TYPE SPECIFIC PARAMETERS
# =============================================================================


class TotalDeckWidthParameter(LengthParameter):
    name: Literal["Total Deck Width"] = "Total Deck Width"

    description: Literal[
        "Total width of deck"
    ] = "Total width of deck"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


class NumberOfGirdersParameter(UnitlessParameter[int]):
    name: Literal["Number of Girders"] = "Number of Girders"

    description: Literal[
        "Number of girders"
    ] = "Number of girders"

    symbol: None = None

    provided_value: int


class GirderSpacingTypeParameter(
    UnitlessParameter[SpacingTypeParaModel]
):
    name: Literal["Girder Spacing Type"] = "Girder Spacing Type"

    description: Literal[
        "Type of girder spacing definition"
    ] = "Type of girder spacing definition"

    symbol: None = None

    provided_value: SpacingTypeParaModel


class GirderSpacingValuesParameter(LengthParameter[list[float]]): #TODO: Implement Base Transformation for unit parameters
    name: Literal["Girder Spacing Values"] = "Girder Spacing Values"

    description: Literal[
        "Spacing values between adjacent girders"
    ] = "Spacing values between adjacent girders"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


class StringcourseLeftBarrierWidthParameter(LengthParameter):
    name: Literal[
        "Stringcourse Left Barrier Width"
    ] = "Stringcourse Left Barrier Width"

    description: Literal[
        "Left barrier width"
    ] = "Left barrier width"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


class StringcourseRightBarrierWidthParameter(
LengthParameter):
    name: Literal[
        "Stringcourse Right Barrier Width"
    ] = "Stringcourse Right Barrier Width"

    description: Literal[
        "Right barrier width"
    ] = "Right barrier width"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


class CantileverLeftWidthParameter(LengthParameter):
    name: Literal[
        "Cantilever Left Width"
    ] = "Cantilever Left Width"

    description: Literal[
        "Left cantilever width"
    ] = "Left cantilever width"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


class CantileverRightWidthParameter(LengthParameter):
    name: Literal[
        "Cantilever Right Width"
    ] = "Cantilever Right Width"

    description: Literal[
        "Right cantilever width"
    ] = "Right cantilever width"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


# =============================================================================
# SUPERSTRUCTURE PROPERTY SET
# =============================================================================


class SuperstructureGroupPropertiesParameters(
    BaseModel
):
    total_deck_width: TotalDeckWidthParameter = Field(
        alias="Total Deck Width"
    )

    number_of_girders: NumberOfGirdersParameter = Field(
        alias="Number of Girders"
    )

    girder_spacing_type: GirderSpacingTypeParameter = Field(
        alias="Girder Spacing Type"
    )

    girder_spacing_values: GirderSpacingValuesParameter = Field(
        alias="Girder Spacing Values"
    )

    stringcourse_left_barrier_width: (
        StringcourseLeftBarrierWidthParameter
    ) = Field(
        alias="Stringcourse Left Barrier Width"
    )

    stringcourse_right_barrier_width: (
        StringcourseRightBarrierWidthParameter
    ) = Field(
        alias="Stringcourse Right Barrier Width"
    )

    cantilever_left_width: CantileverLeftWidthParameter = Field(
        alias="Cantilever Left Width"
    )

    cantilever_right_width: CantileverRightWidthParameter = Field(
        alias="Cantilever Right Width"
    )

class SuperstructureGroupProperties(
    GeometryGroupParameterProperties
):
    group_parameters: (
        SuperstructureGroupPropertiesParameters
    )

    @classmethod
    def create(
        cls,
        total_deck_width: float,
        number_of_girders: int,
        girder_spacing_type: SpacingTypeParaModel,
        girder_spacing_values: list[float],
        stringcourse_left_barrier_width: float,
        stringcourse_right_barrier_width: float,
        cantilever_left_width: float,
        cantilever_right_width: float,
        total_deck_width_unit: Literal["m", "ft"] = "m",
        girder_spacing_values_unit: Literal["m", "ft"] = "m",
        stringcourse_left_barrier_width_unit: Literal["m", "ft"] = "m",
        stringcourse_right_barrier_width_unit: Literal["m", "ft"] = "m",
        cantilever_left_width_unit: Literal["m", "ft"] = "m",
        cantilever_right_width_unit: Literal["m", "ft"] = "m",
        isUser: bool = True,
    ) -> "SuperstructureGroupProperties":

        return cls(
            isUser=isUser,
            group_parameters=(
                SuperstructureGroupPropertiesParameters(
                    **{
                        "Total Deck Width":
                            TotalDeckWidthParameter(
                                isUser=isUser,
                                provided_value=total_deck_width,
                                provided_unit=total_deck_width_unit,
                                base_value=total_deck_width,
                            ),
                        "Number of Girders":
                            NumberOfGirdersParameter(
                                isUser=isUser,
                                provided_value=number_of_girders,
                            ),
                        "Girder Spacing Type":
                            GirderSpacingTypeParameter(
                                isUser=isUser,
                                provided_value=girder_spacing_type,
                            ),
                        "Girder Spacing Values":
                            GirderSpacingValuesParameter(
                                isUser=isUser,
                                provided_value=girder_spacing_values,
                                provided_unit=girder_spacing_values_unit,
                                base_value=girder_spacing_values,
                            ),
                        "Stringcourse Left Barrier Width":
                            StringcourseLeftBarrierWidthParameter(
                                isUser=isUser,
                                provided_value=(
                                    stringcourse_left_barrier_width
                                ),
                                provided_unit=(
                                    stringcourse_left_barrier_width_unit
                                ),
                                base_value=(
                                    stringcourse_left_barrier_width
                                ),
                            ),
                        "Stringcourse Right Barrier Width":
                            StringcourseRightBarrierWidthParameter(
                                isUser=isUser,
                                provided_value=(
                                    stringcourse_right_barrier_width
                                ),
                                provided_unit=(
                                    stringcourse_right_barrier_width_unit
                                ),
                                base_value=(
                                    stringcourse_right_barrier_width
                                ),
                            ),
                        "Cantilever Left Width":
                            CantileverLeftWidthParameter(
                                isUser=isUser,
                                provided_value=cantilever_left_width,
                                provided_unit=(
                                    cantilever_left_width_unit
                                ),
                                base_value=cantilever_left_width,
                            ),
                        "Cantilever Right Width":
                            CantileverRightWidthParameter(
                                isUser=isUser,
                                provided_value=cantilever_right_width,
                                provided_unit=(
                                    cantilever_right_width_unit
                                ),
                                base_value=cantilever_right_width,
                            ),
                    }
                )
            ),
        )

# =============================================================================
# GROUP TYPE IDENTIFICATION
# =============================================================================


class SuperstructureStructureComponentGroupType(
    StructureComponentGroupType
):
    provided_value: Literal[
        StructuralComponentTypeParaModel.SUPERSTRUCTURE
    ] = StructuralComponentTypeParaModel.SUPERSTRUCTURE


# =============================================================================
# COMMON SUPERSTRUCTURE METADATA
# =============================================================================


class GeometryGroupPropertiesSuperstructure(
    GeometryGroupProperties
):
    structural_component_type: (
        SuperstructureStructureComponentGroupType
    ) = Field(
        alias="Structural Component Type"
    )

    group_properties: SuperstructureGroupProperties = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersSuperstructure(
    GeometryGroupParameters
):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Superstructure"
    ] = "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Superstructure"

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-SUPERSTRUCTURE$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: GeometryGroupPropertiesSuperstructure


# =============================================================================
# SUPERSTRUCTURE GROUP
# =============================================================================


SuperstructureGroupElements = Annotated[
    Union[
        GeometryGroupParametersSuperstructure,
        GeometryGroupSpan,
        # GeometryGroupGirder
        # GeometryGroupDeck
    ],
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupSuperstructure(
    GeometryGroupBase
):
    bda_speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Superstructure"
    ] = "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Superstructure"

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-SUPERSTRUCTURE$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    elements: list[SuperstructureGroupElements] = Field(
        default_factory=list,
        json_schema_extra={
            "minItems": 1,
            "allOf": [
                {
                    "contains": {
                        "type": "object",
                        "properties": {
                            "bda_speckle_type": {
                                "const":
                                "Objects.Data.DataObject:"
                                "BDA_Geometry_Group_Properties_Superstructure"
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
    def validate_superstructure_elements(self) -> "GeometryGroupSuperstructure":

        properties_count = sum(
            1
            for element in self.elements
            if element.bda_speckle_type
            == (
                "Objects.Data.DataObject:"
                "BDA_Geometry_Group_Properties_Superstructure"
            )
        )

        if properties_count != 1:
            raise ValueError(
                "GeometryGroupSuperstructure.elements must contain "
                "exactly one "
                "BDA_Geometry_Group_Properties_Superstructure object. "
                f"Found {properties_count}."
            )

        return self

    @classmethod
    def create(
        cls,
        total_deck_width: float,
        number_of_girders: int,
        girder_spacing_type: SpacingTypeParaModel,
        girder_spacing_values: list[float],
        stringcourse_left_barrier_width: float,        
        stringcourse_right_barrier_width: float,        
        cantilever_left_width: float,        
        cantilever_right_width: float,
        total_deck_width_unit: Literal["m", "ft"] = "m",
        girder_spacing_values_unit: Literal["m", "ft"] = "m",
        stringcourse_left_barrier_width_unit: Literal["m", "ft"] = "m",
        stringcourse_right_barrier_width_unit: Literal["m", "ft"] = "m",
        cantilever_left_width_unit: Literal["m", "ft"] = "m",
        cantilever_right_width_unit: Literal["m", "ft"] = "m",
        spans: list[GeometryGroupSpan] | None = None,
        name: str = "Superstructure",
        application_id: str = "COL-GEOMGROUP-0001-SUPERSTRUCTURE",
        isUser: bool = True,
    ) -> "GeometryGroupSuperstructure":

        return cls(
            id=None,
            applicationId=application_id,
            name=name,
            elements=[
                GeometryGroupParametersSuperstructure(
                    **{
                        "id": None,
                        "applicationId": application_id.replace(
                            "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                        ),
                        "properties": (
                            GeometryGroupPropertiesSuperstructure(
                                **{
                                    "Structural Component Type":
                                        SuperstructureStructureComponentGroupType(),

                                    "Geometry Group Properties":
                                        SuperstructureGroupProperties.create(
                                            total_deck_width=total_deck_width,
                                            number_of_girders=number_of_girders,
                                            girder_spacing_type=girder_spacing_type,
                                            girder_spacing_values=girder_spacing_values,
                                            stringcourse_left_barrier_width=(
                                                stringcourse_left_barrier_width
                                            ),
                                            stringcourse_right_barrier_width=(
                                                stringcourse_right_barrier_width
                                            ),
                                            cantilever_left_width=cantilever_left_width,
                                            cantilever_right_width=cantilever_right_width,
                                            total_deck_width_unit=total_deck_width_unit,
                                            girder_spacing_values_unit=(
                                                girder_spacing_values_unit
                                            ),
                                            stringcourse_left_barrier_width_unit=(
                                                stringcourse_left_barrier_width_unit
                                            ),
                                            stringcourse_right_barrier_width_unit=(
                                                stringcourse_right_barrier_width_unit
                                            ),
                                            cantilever_left_width_unit=(
                                                cantilever_left_width_unit
                                            ),
                                            cantilever_right_width_unit=(
                                                cantilever_right_width_unit
                                            ),
                                            isUser=isUser,
                                    ),
                                }
                            )
                        ),
                    }
                ),
                *(spans or [])
            ],
        )
    

if __name__ == "__main__":
    superstructure = GeometryGroupSuperstructure.create(
    total_deck_width=12.5,
    number_of_girders=4,
    girder_spacing_type=SpacingTypeParaModel.UNIFORM,
    girder_spacing_values=[3.0, 3.0, 3.0],
    stringcourse_left_barrier_width=0.5,
    stringcourse_right_barrier_width=0.5,
    cantilever_left_width=1.0,
    cantilever_right_width=1.0,
    application_id="COL-GEOMGROUP-0001-SUPERSTRUCTURE"
    )
    print(superstructure.model_dump_json(indent=4))

