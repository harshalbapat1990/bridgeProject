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


# =============================================================================
# WALL PARAMETERS
# =============================================================================


class ElementThicknessParameter(LengthParameter):
    name: Literal[
        "Element Thickness"
    ] = "Element Thickness"

    description: Literal[
        "Thickness of the wall element"
    ] = "Thickness of the wall element"

    symbol: None = None

    provided_unit: Literal[
        "m",
        "ft",
    ]

    base_unit: Literal[
        "m"
    ] = "m"

    provided_value: float


# =============================================================================
# WALL PROPERTY SET
# =============================================================================


class WallGroupPropertiesParameters(
    BaseModel
):
    element_thickness: (
        ElementThicknessParameter
    ) = Field(
        alias="Element Thickness"
    )


class WallGroupProperties(
    GeometryGroupParameterProperties
):
    group_parameters: (
        WallGroupPropertiesParameters
    )

    @classmethod
    def create(
        cls,
        element_thickness: float,
        element_thickness_unit: Literal[
            "m",
            "ft",
        ] = "m",
        isUser: bool = True,
    ) -> "WallGroupProperties":

        return cls(
            isUser=isUser,
            group_parameters=(
                WallGroupPropertiesParameters(
                    **{
                        "Element Thickness":
                            ElementThicknessParameter(
                                isUser=isUser,
                                provided_value=(
                                    element_thickness
                                ),
                                provided_unit=(
                                    element_thickness_unit
                                ),
                                base_value=(
                                    element_thickness
                                ),
                            ),
                    }
                )
            ),
        )


# =============================================================================
# GROUP TYPE IDENTIFICATION
# =============================================================================


class WallStructureComponentGroupType(
    StructureComponentGroupType
):
    provided_value: Literal[
        StructuralComponentTypeParaModel.WALL
    ] = (
        StructuralComponentTypeParaModel.WALL
    )


# =============================================================================
# WALL METADATA
# =============================================================================


class GeometryGroupPropertiesWall(
    GeometryGroupProperties
):
    structural_component_type: (
        WallStructureComponentGroupType
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
        WallGroupProperties
    ) = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersWall(
    GeometryGroupParameters
):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Wall"
    ] = "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Wall"

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-WALL$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: (
        GeometryGroupPropertiesWall
    )


# =============================================================================
# WALL GROUP
# =============================================================================


WallGroupElements = Annotated[
    GeometryGroupParametersWall,
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupWall(
    GeometryGroupBase
):
    bda_speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Wall"
    ] = "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Wall"

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-WALL$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    elements: list[
        WallGroupElements
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
                                    "BDA_Geometry_Group_Properties_Wall"
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
    def validate_wall_elements(self) -> "GeometryGroupWall":

        wall_properties_speckle_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_Wall"
        )

        wall_properties_count = sum(
            1
            for element in self.elements
            if element.bda_speckle_type
            == wall_properties_speckle_type
        )

        if wall_properties_count != 1:
            raise ValueError(
                "GeometryGroupWall.elements must contain "
                "exactly one "
                f"{wall_properties_speckle_type} object. "
                f"Found {wall_properties_count}."
            )

        return self

    @classmethod
    def create(
        cls,
        material_id: str = "concrete",
        section_id: str = "wall_section",
        element_thickness: float = 0.0,
        element_thickness_unit: Literal[
            "m",
            "ft",
        ] = "m",
        application_id: str = "COL-GEOMGROUP-0001-WALL",
        name: str | None = None,
        isUser: bool = True,
    ) -> "GeometryGroupWall":

        return cls(
            id=None,
            applicationId=application_id,
            name=name if name is not None else application_id,
            elements=[
                GeometryGroupParametersWall(
                    **{
                        "id": None,
                        "applicationId": application_id.replace(
                            "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                        ),
                        "properties":
                            GeometryGroupPropertiesWall(
                                **{
                                    "Structural Component Type":
                                        (
                                            WallStructureComponentGroupType()
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
                                            WallGroupProperties.create(
                                                element_thickness=
                                                    element_thickness,
                                                element_thickness_unit=
                                                    element_thickness_unit,
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

    wall = GeometryGroupWall.create(
        material_id="M_Wall",
        section_id="S_Wall",
        element_thickness=0.6,
        element_thickness_unit="m"
    )

    print(
        wall.model_dump_json(
            indent=4
        )
    )

