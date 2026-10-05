from typing import Annotated, ClassVar, Literal, Union

from pydantic import BaseModel, Field, model_validator

from bda.contracts.paramodel.groups.enums import (
    StructuralComponentTypeParaModel,
    ElementOrientationParaModel,
    SpacingTypeParaModel,
    BracingTypeParaModel,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.geometry_group_base import (
    GeometryGroupBase,
    GeometryGroupParameters,
    GeometryGroupProperties,
    GeometryGroupParameterProperties,
    StructureComponentGroupType,
)

from bda.contracts.speckle_contracts.base_objects import (
    ParameterGroup,
    UnitlessParameter,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_brace import (
    GeometryGroupBrace,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_chord import (
    GeometryGroupChord,
)
from bda.contracts.speckle_contracts.unit_parameters import LengthParameter


# =============================================================================
# TRANSVERSE BRACING PARAMETERS
# =============================================================================


class BracingOrientationParameter(
    UnitlessParameter[ElementOrientationParaModel]
):
    name: Literal["Bracing Orientation"] = "Bracing Orientation"

    description: Literal[
        "Orientation of the bracing"
    ] = "Orientation of the bracing"

    symbol: None = None

    provided_value: ElementOrientationParaModel


class BracingSpacingParameter(
    UnitlessParameter[SpacingTypeParaModel]
):
    name: Literal["Bracing Spacing"] = "Bracing Spacing"

    description: Literal[
        "Spacing of the bracing"
    ] = "Spacing of the bracing"

    symbol: None = None

    provided_value: SpacingTypeParaModel


class NumberOfBracingsParameter(UnitlessParameter[int]):
    name: Literal["Number of Bracings"] = "Number of Bracings"

    description: Literal[
        "Number of bracings"
    ] = "Number of bracings"

    symbol: None = None

    provided_value: int


class GirderSpacingValuesParameter(LengthParameter[list[float]]):
    name: Literal[
        "Bracing Spacing Distances"
    ] = "Bracing Spacing Distances"

    description: Literal[
        "Spacing values between adjacent bracings"
    ] = "Spacing values between adjacent bracings"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


class X_StartFirstBracingParameter(LengthParameter):
    name: Literal[
        "Start Position of First Bracing"
    ] = "Start Position of First Bracing"

    description: Literal[
        "Start position of the first bracing along girder x axis"
    ] = "Start position of the first bracing along girder x axis"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


class GirderIndexParameter(UnitlessParameter[int]):
    name: Literal["Girder Index"] = "Girder Index"

    description: Literal[
        "Index of the girder"
    ] = "Index of the girder"

    symbol: None = None

    provided_value: int


class LeftGirderIndexParameter(GirderIndexParameter):
    name: Literal["Left Girder Index"] = "Left Girder Index"

    description: Literal[
        "Index of the left girder"
    ] = "Index of the left girder"


class RightGirderIndexParameter(GirderIndexParameter):
    name: Literal["Right Girder Index"] = "Right Girder Index"

    description: Literal[
        "Index of the right girder"
    ] = "Index of the right girder"


class HorzOffsetLeftGirderParameter(LengthParameter):
    name: Literal[
        "Horizontal Offset to Left Girder"
    ] = "Horizontal Offset to Left Girder"

    description: Literal[
        "Horizontal offset to the left girder"
    ] = "Horizontal offset to the left girder"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


class HorzOffsetRightGirderParameter(LengthParameter):
    name: Literal[
        "Horizontal Offset to Right Girder"
    ] = "Horizontal Offset to Right Girder"

    description: Literal[
        "Horizontal offset to the right girder"
    ] = "Horizontal offset to the right girder"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


# =============================================================================
# BRACING DETAILS PARAMETER GROUP
# =============================================================================


class BracingDetailsParameterGroupParameters(BaseModel):
    horizontal_offset_left_girder: (
        HorzOffsetLeftGirderParameter
    ) = Field(
        alias="Horizontal Offset to Left Girder"
    )

    horizontal_offset_right_girder: (
        HorzOffsetRightGirderParameter
    ) = Field(
        alias="Horizontal Offset to Right Girder"
    )


class BracingDetailsParameterGroup(ParameterGroup):
    name: Literal["Bracing Details"] = "Bracing Details"

    description: Literal[
        "Details about the bracing configuration"
    ] = "Details about the bracing configuration"

    symbol: None = None

    group_parameters: BracingDetailsParameterGroupParameters

    @classmethod
    def create(
        cls,
        horizontal_offset_left_girder: float,
        horizontal_offset_right_girder: float,
        horizontal_offset_left_girder_unit: Literal["m", "ft"] = "m",
        horizontal_offset_right_girder_unit: Literal["m", "ft"] = "m",
        isUser: bool = True,
    ) -> "BracingDetailsParameterGroup":

        return cls(
            isUser=isUser,
            group_parameters=(
                BracingDetailsParameterGroupParameters(
                    **{
                        "Horizontal Offset to Left Girder":
                            HorzOffsetLeftGirderParameter(
                                isUser=isUser,
                                provided_value=horizontal_offset_left_girder,
                                provided_unit=horizontal_offset_left_girder_unit,
                                base_value=horizontal_offset_left_girder,
                            ),

                        "Horizontal Offset to Right Girder":
                            HorzOffsetRightGirderParameter(
                                isUser=isUser,
                                provided_value=horizontal_offset_right_girder,
                                provided_unit=horizontal_offset_right_girder_unit,
                                base_value=horizontal_offset_right_girder,
                            ),
                    }
                )
            ),
        )


# =============================================================================
# TRANSVERSE BRACING PROPERTY SET
# =============================================================================


class TransverseBracingGroupPropertiesParameters(BaseModel):
    bracing_orientation: BracingOrientationParameter = Field(
        alias="Bracing Orientation"
    )

    x_start_first_bracing: X_StartFirstBracingParameter = Field(
        alias="Start Position of First Bracing"
    )

    spacing_type: BracingSpacingParameter = Field(
        alias="Bracing Spacing"
    )

    spacing_values: GirderSpacingValuesParameter = Field(
        alias="Bracing Spacing Distances"
    )

    no_of_bracings: NumberOfBracingsParameter = Field(
        alias="Number of Bracings"
    )

    left_girder_index: LeftGirderIndexParameter = Field(
        alias="Left Girder Index"
    )

    right_girder_index: RightGirderIndexParameter = Field(
        alias="Right Girder Index"
    )

    bracing_details: BracingDetailsParameterGroup = Field(
        alias="Bracing Details"
    )


class TransverseBracingGroupProperties(
    GeometryGroupParameterProperties
):
    group_parameters: TransverseBracingGroupPropertiesParameters

    @classmethod
    def create(
        cls,
        bracing_orientation: ElementOrientationParaModel,
        x_start_first_bracing: float,
        spacing_type: SpacingTypeParaModel,
        spacing_values: list[float],
        number_of_bracings: int,
        left_girder_index: int,
        right_girder_index: int,
        horizontal_offset_left_girder: float,
        horizontal_offset_right_girder: float,
        x_start_first_bracing_unit: Literal["m", "ft"] = "m",
        spacing_values_unit: Literal["m", "ft"] = "m",
        horizontal_offset_left_girder_unit: Literal["m", "ft"] = "m",
        horizontal_offset_right_girder_unit: Literal["m", "ft"] = "m",
        isUser: bool = True,
    ) -> "TransverseBracingGroupProperties":

        return cls(
            isUser=isUser,
            group_parameters=(
                TransverseBracingGroupPropertiesParameters(
                    **{
                        "Bracing Orientation":
                            BracingOrientationParameter(
                                isUser=isUser,
                                provided_value=bracing_orientation,
                            ),

                        "Start Position of First Bracing":
                            X_StartFirstBracingParameter(
                                isUser=isUser,
                                provided_value=x_start_first_bracing,
                                provided_unit=x_start_first_bracing_unit,
                                base_value=x_start_first_bracing,
                            ),

                        "Bracing Spacing":
                            BracingSpacingParameter(
                                isUser=isUser,
                                provided_value=spacing_type,
                            ),

                        "Bracing Spacing Distances":
                            GirderSpacingValuesParameter(
                                isUser=isUser,
                                provided_value=spacing_values,
                                provided_unit=spacing_values_unit,
                                base_value=spacing_values,
                            ),

                        "Number of Bracings":
                            NumberOfBracingsParameter(
                                isUser=isUser,
                                provided_value=number_of_bracings,
                            ),

                        "Left Girder Index":
                            LeftGirderIndexParameter(
                                isUser=isUser,
                                provided_value=left_girder_index,
                            ),

                        "Right Girder Index":
                            RightGirderIndexParameter(
                                isUser=isUser,
                                provided_value=right_girder_index,
                            ),

                        "Bracing Details":
                            BracingDetailsParameterGroup.create(
                                horizontal_offset_left_girder=(
                                    horizontal_offset_left_girder
                                ),
                                horizontal_offset_right_girder=(
                                    horizontal_offset_right_girder
                                ),
                                horizontal_offset_left_girder_unit=(
                                    horizontal_offset_left_girder_unit
                                ),
                                horizontal_offset_right_girder_unit=(
                                    horizontal_offset_right_girder_unit
                                ),
                                isUser=isUser,
                            ),
                    }
                )
            ),
        )


# =============================================================================
# GROUP TYPE IDENTIFICATION
# =============================================================================


class TransverseBracingStructureComponentGroupType(
    StructureComponentGroupType
):
    provided_value: Literal[
        StructuralComponentTypeParaModel.TRANSVERSE_BRACING
    ] = StructuralComponentTypeParaModel.TRANSVERSE_BRACING


# =============================================================================
# TRANSVERSE BRACING METADATA
# =============================================================================


class GeometryGroupPropertiesTransverseBracing(
    GeometryGroupProperties
):
    structural_component_type: (
        TransverseBracingStructureComponentGroupType
    ) = Field(
        alias="Structural Component Type"
    )

    group_properties: TransverseBracingGroupProperties = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersTransverseBracing(
    GeometryGroupParameters
):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Transverse_Bracing"
    ] = Field(
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Transverse_Bracing",
        frozen=True
    )

    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Transverse_Bracing"
    ] = Field(
        ...,
        frozen=True
    )

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-TRANSVERSE-BRACING$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: GeometryGroupPropertiesTransverseBracing


# =============================================================================
# TRANSVERSE BRACING GROUP
# =============================================================================


TransverseBracingGroupElements = Annotated[
    Union[
        GeometryGroupParametersTransverseBracing,
        GeometryGroupBrace,
        GeometryGroupChord,
    ],
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupTransverseBracing(
    GeometryGroupBase
):
    speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Transverse_Bracing"
    ] = Field(
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Transverse_Bracing",
        frozen=True
    )

    bda_speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Transverse_Bracing"
    ] = Field(
        ...,
        frozen=True
    )

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-TRANSVERSE-BRACING$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    elements: list[TransverseBracingGroupElements] = Field(
        default_factory=list,
        json_schema_extra={
            "minItems": 1,
            "allOf": [
                {
                    # Exactly one transverse bracing properties object
                    "contains": {
                        "type": "object",
                        "properties": {
                            "speckle_type": {
                                "const": (
                                    "Objects.Data.DataObject:"
                                    "BDA_Geometry_Group_Properties_Transverse_Bracing"
                                )
                            }
                        },
                        "required": ["speckle_type"],
                    },
                    "minContains": 1,
                    "maxContains": 1,
                }
            ],
        },
    )

    @model_validator(mode="after")
    def validate_transverse_bracing_elements(self) -> "GeometryGroupTransverseBracing":

        transverse_bracing_properties_speckle_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_Transverse_Bracing"
        )

        transverse_bracing_properties_count = sum(
            1
            for element in self.elements
            if element.speckle_type
            == transverse_bracing_properties_speckle_type
        )

        if transverse_bracing_properties_count != 1:
            raise ValueError(
                "GeometryGroupTransverseBracing.elements must contain "
                "exactly one "
                f"{transverse_bracing_properties_speckle_type} object. "
                f"Found {transverse_bracing_properties_count}."
            )

        return self

    @classmethod
    def create(
        cls,
        bracing_orientation: ElementOrientationParaModel,
        x_start_first_bracing: float,
        spacing_type: SpacingTypeParaModel,
        spacing_values: list[float],
        number_of_bracings: int,
        left_girder_index: int,
        right_girder_index: int,
        horizontal_offset_left_girder: float,
        horizontal_offset_right_girder: float,
        braces: list[GeometryGroupBrace] | None = None,
        chords: list[GeometryGroupChord] | None = None,
        x_start_first_bracing_unit: Literal["m", "ft"] = "m",
        spacing_values_unit: Literal["m", "ft"] = "m",
        horizontal_offset_left_girder_unit: Literal["m", "ft"] = "m",
        horizontal_offset_right_girder_unit: Literal["m", "ft"] = "m",
        application_id: str = "COL-GEOMGROUP-0001-TRANSVERSE-BRACING",
        name: str|None = None,
        isUser: bool = True,
    ) -> "GeometryGroupTransverseBracing":

        elements: list[TransverseBracingGroupElements] = [
            GeometryGroupParametersTransverseBracing(
                **{
                    "id": None,
                    "applicationId": application_id.replace(
                        "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                    ),
                    "bda_speckle_type": (
                        "Objects.Data.DataObject:"
                        "BDA_Geometry_Group_Properties_Transverse_Bracing"
                    ),
                    "properties": GeometryGroupPropertiesTransverseBracing(
                        **{
                            "Structural Component Type":
                                TransverseBracingStructureComponentGroupType(),

                            "Geometry Group Properties":
                                TransverseBracingGroupProperties.create(
                                    bracing_orientation=(
                                        bracing_orientation
                                    ),
                                    x_start_first_bracing=(
                                        x_start_first_bracing
                                    ),
                                    spacing_type=spacing_type,
                                    spacing_values=spacing_values,
                                    number_of_bracings=(
                                        number_of_bracings
                                    ),
                                    left_girder_index=(
                                        left_girder_index
                                    ),
                                    right_girder_index=(
                                        right_girder_index
                                    ),
                                    horizontal_offset_left_girder=(
                                        horizontal_offset_left_girder
                                    ),
                                    horizontal_offset_right_girder=(
                                        horizontal_offset_right_girder
                                    ),
                                    x_start_first_bracing_unit=(
                                        x_start_first_bracing_unit
                                    ),
                                    spacing_values_unit=(
                                        spacing_values_unit
                                    ),
                                    horizontal_offset_left_girder_unit=(
                                        horizontal_offset_left_girder_unit
                                    ),
                                    horizontal_offset_right_girder_unit=(
                                        horizontal_offset_right_girder_unit
                                    ),
                                    isUser=isUser,
                                ),
                        }
                    ),
                }
            )
        ]

        elements.extend(braces or [])
        elements.extend(chords or [])

        return cls(
            id=None,
            applicationId=application_id,
            name=name if name is not None else f"transverse_bracing_{left_girder_index}_{right_girder_index}",
            bda_speckle_type=(
                "Speckle.Core.Models.Collections.Collection:"
                "BDA_Geometry_Group_Transverse_Bracing"
            ),
            elements=elements,
        )


if __name__ == "__main__":

    transverse_bracing = GeometryGroupTransverseBracing.create(
        bracing_orientation=ElementOrientationParaModel.SKEWED,
        x_start_first_bracing=0.0,
        spacing_type=SpacingTypeParaModel.UNIFORM,
        spacing_values=[3.0, 3.0, 3.0],
        number_of_bracings=4,
        left_girder_index=1,
        right_girder_index=2,
        horizontal_offset_left_girder=0.0,
        horizontal_offset_right_girder=0.0,
        application_id="COL-GEOMGROUP-0001-TRANSVERSE-BRACING",
    )

    print(
        transverse_bracing.model_dump_json(
            indent=4
        )
    )