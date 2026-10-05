from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes
from typing import Annotated, ClassVar, Literal, Union

from pydantic import BaseModel, Field, model_validator

from bda.contracts.paramodel.groups.enums import (
    StructuralComponentTypeParaModel,
    BracingTypeParaModel,
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

from bda.contracts.speckle_contracts.base_objects import (
    ParameterGroup,
    UnitlessParameter,
)

from bda.contracts.speckle_contracts.unit_parameters import (
    LengthParameter
)


# =============================================================================
# BRACE PARAMETERS
# =============================================================================


class BraceTypeParameter(UnitlessParameter[BracingTypeParaModel]):
    name: Literal["Brace Type"] = "Brace Type"

    description: Literal[
        "Type of bracing (e.g., K or X bracing)"
    ] = "Type of bracing (e.g., K or X bracing)"

    symbol: None = None

    isUser: bool = False

    provided_value: BracingTypeParaModel


class VerticalOffsetAtLeftBottom(LengthParameter):
    name: Literal["Vertical Offset at Left Bottom"] = "Vertical Offset at Left Bottom"

    description: Literal[
        "Vertical offset at the left bottom end of the brace"
    ] = "Vertical offset at the left bottom end of the brace"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"

class VerticalOffsetAtLeftTop(LengthParameter):
    name: Literal["Vertical Offset at Left Top"] = "Vertical Offset at Left Top"

    description: Literal[
        "Vertical offset at the left top end of the brace"
    ] = "Vertical offset at the left top end of the brace"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


class VerticalOffsetAtRightBottom(LengthParameter):
    name: Literal["Vertical Offset at Right Bottom"] = "Vertical Offset at Right Bottom"

    description: Literal[
        "Vertical offset at the right bottom end of the brace"
    ] = "Vertical offset at the right bottom end of the brace"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"

class VerticalOffsetAtRightTop(LengthParameter):
    name: Literal["Vertical Offset at Right Top"] = "Vertical Offset at Right Top"

    description: Literal[
        "Vertical offset at the right top end of the brace"
    ] = "Vertical offset at the right top end of the brace"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


class HorizontalOffsetAtLeft(LengthParameter):
    name: Literal["Horizontal Offset at Left"] = "Horizontal Offset at Left"

    description: Literal[
        "Horizontal offset at the left end of the brace"
    ] = "Horizontal offset at the left end of the brace"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


class HorizontalOffsetAtRight(LengthParameter):
    name: Literal["Horizontal Offset at Right"] = "Horizontal Offset at Right"

    description: Literal[
        "Horizontal offset at the right end of the brace"
    ] = "Horizontal offset at the right end of the brace"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


# =============================================================================
# FIXED BRACE TYPE PARAMETERS
# =============================================================================


class BraceTypeXBracing(BraceTypeParameter):
    provided_value: Literal[
        BracingTypeParaModel.X_TYPE
    ] = BracingTypeParaModel.X_TYPE


class BraceTypeKBracing(BraceTypeParameter):
    provided_value: Literal[
        BracingTypeParaModel.K_TYPE
    ] = BracingTypeParaModel.K_TYPE


# =============================================================================
# GEOMETRY DETAILS PARAMETER GROUPS
# =============================================================================


class GeometryDetailsGroupParameters_XBracing(BaseModel):
    bracing_type: BraceTypeXBracing = Field(
        alias="Brace Type"
    )

    vertical_offset_left_btm: VerticalOffsetAtLeftBottom = Field(
        alias="Vertical Offset at Left Bottom"
    )

    vertical_offset_left_top: VerticalOffsetAtLeftTop = Field(
        alias="Vertical Offset at Left Top"
    )


    vertical_offset_right_btm: VerticalOffsetAtRightBottom = Field(
        alias="Vertical Offset at Right Bottom"
    )

    vertical_offset_right_top: VerticalOffsetAtRightTop = Field(
        alias="Vertical Offset at Right Top"
    )


class GeometryDetailsGroupParameters_KBracing(BaseModel):
    bracing_type: BraceTypeKBracing = Field(
        alias="Brace Type"
    )

    vertical_offset_left_btm: VerticalOffsetAtLeftBottom = Field(
        alias="Vertical Offset at Left Bottom"
    )

    vertical_offset_left_top: VerticalOffsetAtLeftTop = Field(
        alias="Vertical Offset at Left Top"
    )


    vertical_offset_right_btm: VerticalOffsetAtRightBottom = Field(
        alias="Vertical Offset at Right Bottom"
    )

    vertical_offset_right_top: VerticalOffsetAtRightTop = Field(
        alias="Vertical Offset at Right Top"
    )

    horizontal_offset_at_left: HorizontalOffsetAtLeft = Field(
        alias="Horizontal Offset at Left"
    )

    horizontal_offset_at_right: HorizontalOffsetAtRight = Field(
        alias="Horizontal Offset at Right"
    )


BracingGeometryDetailsGroupParameters = Union[
    GeometryDetailsGroupParameters_XBracing,
    GeometryDetailsGroupParameters_KBracing,
]


# =============================================================================
# GEOMETRY DETAILS PARAMETER GROUP
# =============================================================================


class GeometryDetailsParameterGroup(ParameterGroup):
    name: Literal["Geometry Details"] = "Geometry Details"

    description: Literal[
        "Geometry details of brace"
    ] = "Geometry details of brace"

    symbol: None = None

    group_parameters: BracingGeometryDetailsGroupParameters

    @classmethod
    def create(
        cls,
        brace_type: BracingTypeParaModel,
        vertical_offset_left_bottom: float = 0.0,
        vertical_offset_left_top: float = 0.0,
        vertical_offset_right_bottom: float = 0.0,
        vertical_offset_right_top: float = 0.0,
        horizontal_offset_left: float | None = None,
        horizontal_offset_right: float | None = None,
        vertical_offset_left_bottom_unit: Literal["m", "ft"] = "m",
        vertical_offset_left_top_unit: Literal["m", "ft"] = "m",
        vertical_offset_right_bottom_unit: Literal["m", "ft"] = "m",
        vertical_offset_right_top_unit: Literal["m", "ft"] = "m",
        horizontal_offset_left_unit: Literal["m", "ft"] = "m",
        horizontal_offset_right_unit: Literal["m", "ft"] = "m",
        isUser: bool = True,
    ) -> "GeometryDetailsParameterGroup":

        if brace_type == BracingTypeParaModel.X_TYPE:
            return cls(
                isUser=isUser,
                group_parameters=GeometryDetailsGroupParameters_XBracing(
                    **{
                        "Brace Type": BraceTypeXBracing(),
                        "Vertical Offset at Left Bottom": VerticalOffsetAtLeftBottom(
                            isUser=isUser,
                            provided_value=vertical_offset_left_bottom,
                            provided_unit=vertical_offset_left_bottom_unit,
                            base_value=vertical_offset_left_bottom,
                        ),
                        "Vertical Offset at Left Top": VerticalOffsetAtLeftTop(
                            isUser=isUser,
                            provided_value=vertical_offset_left_top,
                            provided_unit=vertical_offset_left_top_unit,
                            base_value=vertical_offset_left_top,
                        ),
                        "Vertical Offset at Right Bottom": VerticalOffsetAtRightBottom(
                            isUser=isUser,
                            provided_value=vertical_offset_right_bottom,
                            provided_unit=vertical_offset_right_bottom_unit,
                            base_value=vertical_offset_right_bottom,
                        ),
                        "Vertical Offset at Right Top": VerticalOffsetAtRightTop(
                            isUser=isUser,
                            provided_value=vertical_offset_right_top,
                            provided_unit=vertical_offset_right_top_unit,
                            base_value=vertical_offset_right_top,
                        ),
                    }
                ),
            )

        if brace_type == BracingTypeParaModel.K_TYPE:
            if (
                horizontal_offset_left is None
                or horizontal_offset_right is None
            ):
                raise ValueError(
                    "K-type bracing requires horizontal offsets."
                )

            return cls(
                isUser=isUser,
                group_parameters=GeometryDetailsGroupParameters_KBracing(
                    **{
                        "Brace Type": BraceTypeKBracing(),
                        "Vertical Offset at Left Bottom": VerticalOffsetAtLeftBottom(
                            isUser=isUser,
                            provided_value=vertical_offset_left_bottom,
                            provided_unit=vertical_offset_left_bottom_unit,
                            base_value=vertical_offset_left_bottom,
                        ),
                        "Vertical Offset at Left Top": VerticalOffsetAtLeftTop(
                            isUser=isUser,
                            provided_value=vertical_offset_left_top,
                            provided_unit=vertical_offset_left_top_unit,
                            base_value=vertical_offset_left_top,
                        ),
                        "Vertical Offset at Right Bottom": VerticalOffsetAtRightBottom(
                            isUser=isUser,
                            provided_value=vertical_offset_right_bottom,
                            provided_unit=vertical_offset_right_bottom_unit,
                            base_value=vertical_offset_right_bottom,
                        ),
                        "Vertical Offset at Right Top": VerticalOffsetAtRightTop(
                            isUser=isUser,
                            provided_value=vertical_offset_right_top,
                            provided_unit=vertical_offset_right_top_unit,
                            base_value=vertical_offset_right_top,
                        ),
                        "Horizontal Offset at Left": HorizontalOffsetAtLeft(
                            isUser=isUser,
                            provided_value=horizontal_offset_left,
                            provided_unit=horizontal_offset_left_unit,
                            base_value=horizontal_offset_left,
                        ),
                        "Horizontal Offset at Right": HorizontalOffsetAtRight(
                            isUser=isUser,
                            provided_value=horizontal_offset_right,
                            provided_unit=horizontal_offset_right_unit,
                            base_value=horizontal_offset_right,
                        ),
                    }
                ),
            )

        raise ValueError(
            f"Unsupported brace type: {brace_type}"
        )


# =============================================================================
# BRACE PROPERTY SET
# =============================================================================


class BraceGroupPropertiesParameters(BaseModel):
    geometry_details: GeometryDetailsParameterGroup = Field(
        alias="Geometry Details"
    )


class BraceGroupProperties(GeometryGroupParameterProperties):
    group_parameters: BraceGroupPropertiesParameters

    @classmethod
    def create(
        cls,
        brace_type: BracingTypeParaModel,
        vertical_offset_left_bottom: float = 0.0,
        vertical_offset_left_top: float = 0.0,
        vertical_offset_right_bottom: float = 0.0,
        vertical_offset_right_top: float = 0.0,
        horizontal_offset_left: float | None = None,
        horizontal_offset_right: float | None = None,
        vertical_offset_left_bottom_unit: Literal["m", "ft"] = "m",
        vertical_offset_left_top_unit: Literal["m", "ft"] = "m",
        vertical_offset_right_bottom_unit: Literal["m", "ft"] = "m",
        vertical_offset_right_top_unit: Literal["m", "ft"] = "m",
        horizontal_offset_left_unit: Literal["m", "ft"] = "m",
        horizontal_offset_right_unit: Literal["m", "ft"] = "m",
        isUser: bool = True,
    ) -> "BraceGroupProperties":

        return cls(
            isUser=isUser,
            group_parameters=BraceGroupPropertiesParameters(
                **{
                    "Geometry Details": GeometryDetailsParameterGroup.create(
                        brace_type=brace_type,
                        vertical_offset_left_bottom=vertical_offset_left_bottom,
                        vertical_offset_left_top=vertical_offset_left_top,
                        vertical_offset_right_bottom=vertical_offset_right_bottom,
                        vertical_offset_right_top=vertical_offset_right_top,
                        horizontal_offset_left=horizontal_offset_left,
                        horizontal_offset_right=horizontal_offset_right,
                        vertical_offset_left_bottom_unit=vertical_offset_left_bottom_unit,
                        vertical_offset_left_top_unit=vertical_offset_left_top_unit,
                        vertical_offset_right_bottom_unit=vertical_offset_right_bottom_unit,
                        vertical_offset_right_top_unit=vertical_offset_right_top_unit,
                        horizontal_offset_left_unit=horizontal_offset_left_unit,
                        horizontal_offset_right_unit=horizontal_offset_right_unit,
                        isUser=isUser,
                    )
                }
            ),
        )


# =============================================================================
# GROUP TYPE IDENTIFICATION
# =============================================================================


class BraceStructureComponentGroupType(StructureComponentGroupType):
    provided_value: Literal[
        StructuralComponentTypeParaModel.BRACE
    ] = StructuralComponentTypeParaModel.BRACE


# =============================================================================
# BRACE METADATA
# =============================================================================


class GeometryGroupPropertiesBrace(GeometryGroupProperties):
    structural_component_type: BraceStructureComponentGroupType = Field(
        alias="Structural Component Type"
    )

    material_id: MaterialIdString = Field(
        alias="Material ID",
    )

    section_id: SectionIdString = Field(
        alias="Section ID",
    )

    group_properties: BraceGroupProperties = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersBrace(GeometryGroupParameters):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_BRACE
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_BRACE.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-BRACE$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: GeometryGroupPropertiesBrace


# =============================================================================
# BRACE GROUP
# =============================================================================

BraceGroupElements = Annotated[
    GeometryGroupParametersBrace,
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupBrace(GeometryGroupBase):
    bda_speckle_type: Literal[
        SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_BRACE
    ] = Field(SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_BRACE.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-BRACE$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    elements: list[BraceGroupElements] = Field(
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
                                    "BDA_Geometry_Group_Properties_Brace"
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
    def validate_brace_elements(self) -> "GeometryGroupBrace":
        brace_properties_speckle_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_Brace"
        )

        brace_properties_count = sum(
            1
            for element in self.elements
            if element.bda_speckle_type == brace_properties_speckle_type
        )

        if brace_properties_count != 1:
            raise ValueError(
                "GeometryGroupBrace.elements must contain exactly one "
                f"{brace_properties_speckle_type} object. "
                f"Found {brace_properties_count}."
            )

        return self

    @classmethod
    def create(
        cls,
        material_id: str,
        section_id: str,
        brace_type: BracingTypeParaModel,
        application_id: str = "COL-GEOMGROUP-0001-BRACE",
        name: str|None = None,
        vertical_offset_left_bottom: float = 0.0,
        vertical_offset_left_top: float = 0.0,
        vertical_offset_right_bottom: float = 0.0,
        vertical_offset_right_top: float = 0.0,
        horizontal_offset_left: float | None = None,
        horizontal_offset_right: float | None = None,
        vertical_offset_left_bottom_unit: Literal["m", "ft"] = "m",
        vertical_offset_left_top_unit: Literal["m", "ft"] = "m",
        vertical_offset_right_bottom_unit: Literal["m", "ft"] = "m",
        vertical_offset_right_top_unit: Literal["m", "ft"] = "m",
        horizontal_offset_left_unit: Literal["m", "ft"] = "m",
        horizontal_offset_right_unit: Literal["m", "ft"] = "m",
        isUser: bool = True,
    ) -> "GeometryGroupBrace":

        return cls(
            id=None,
            applicationId=application_id,
            name=name if name is not None else f"Brace", #TODO: Improve Autonaming
            elements=[
                GeometryGroupParametersBrace(
                    **{
                        "id": None,
                        "applicationId": application_id.replace(
                            "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                        ),
                        "properties": GeometryGroupPropertiesBrace(
                            **{
                                "Structural Component Type": (
                                    BraceStructureComponentGroupType()
                                ),
                                "Material ID": MaterialIdString(
                                    isUser=False,
                                    provided_value=material_id,
                                ),
                                "Section ID": SectionIdString(
                                    isUser=False,
                                    provided_value=section_id,
                                ),
                                "Geometry Group Properties": (
                                    BraceGroupProperties.create(
                                        brace_type=brace_type,
                                        vertical_offset_left_bottom=(
                                            vertical_offset_left_bottom
                                        ),
                                        vertical_offset_left_top=(
                                            vertical_offset_left_top
                                        ),
                                        vertical_offset_right_bottom=(
                                            vertical_offset_right_bottom
                                        ),
                                        vertical_offset_right_top=(
                                            vertical_offset_right_top
                                        ),
                                        horizontal_offset_left=(
                                            horizontal_offset_left
                                        ),
                                        horizontal_offset_right=(
                                            horizontal_offset_right
                                        ),
                                        vertical_offset_left_bottom_unit=(
                                            vertical_offset_left_bottom_unit
                                        ),
                                        vertical_offset_left_top_unit=(
                                            vertical_offset_left_top_unit
                                        ),
                                        vertical_offset_right_bottom_unit=(
                                            vertical_offset_right_bottom_unit
                                        ),
                                        vertical_offset_right_top_unit=(
                                            vertical_offset_right_top_unit
                                        ),
                                        horizontal_offset_left_unit=(
                                            horizontal_offset_left_unit
                                        ),
                                        horizontal_offset_right_unit=(
                                            horizontal_offset_right_unit
                                        ),
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
    x_brace_group = GeometryGroupBrace.create(
        material_id="material_1",
        section_id="section_1",
        brace_type=BracingTypeParaModel.X_TYPE,
        application_id="brace_1",
        vertical_offset_left_bottom=0.0,
        vertical_offset_left_top=0.0,
        vertical_offset_right_bottom=0.0,
        vertical_offset_right_top=0.0,
    )

    print(
        x_brace_group.model_dump_json(
            indent=4
        )
    )

    k_brace_group = GeometryGroupBrace.create(
        material_id="material_2",
        section_id="section_2",
        brace_type=BracingTypeParaModel.K_TYPE,
        application_id="brace_2",
        vertical_offset_left_bottom=0.0,
        vertical_offset_left_top=0.0,
        vertical_offset_right_bottom=0.0,
        vertical_offset_right_top=0.0,
        horizontal_offset_left=0.5,
        horizontal_offset_right=0.5,
    )

    print(
        k_brace_group.model_dump_json(
            indent=4
        )
    )