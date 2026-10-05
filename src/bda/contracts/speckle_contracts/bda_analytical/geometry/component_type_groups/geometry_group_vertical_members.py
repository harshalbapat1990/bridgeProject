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
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_pier import (
    GeometryGroupPier,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_pile import (
    GeometryGroupPile,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_wall import (
    GeometryGroupWall,
)


class VerticalMembersGroupPropertiesParameters(BaseModel):
    pass


class VerticalMembersGroupProperties(GeometryGroupParameterProperties):
    group_parameters: VerticalMembersGroupPropertiesParameters

    @classmethod
    def create(
        cls,
        isUser: bool = True,
    ) -> "VerticalMembersGroupProperties":
        return cls(
            isUser=isUser,
            group_parameters=VerticalMembersGroupPropertiesParameters(),
        )


class VerticalMembersStructureComponentGroupType(StructureComponentGroupType):
    provided_value: Literal[
        StructuralComponentTypeParaModel.VERTICAL_MEMBERS
    ] = StructuralComponentTypeParaModel.VERTICAL_MEMBERS


class GeometryGroupPropertiesVerticalMembers(GeometryGroupProperties):
    structural_component_type: VerticalMembersStructureComponentGroupType = Field(
        alias="Structural Component Type"
    )

    group_properties: VerticalMembersGroupProperties = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersVerticalMembers(GeometryGroupParameters):
    name: Literal["Geometry Group Properties"] = "Geometry Group Properties"

    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Vertical_Members"
    ] = Field(
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Vertical_Members",
        frozen=True,
    )

    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Vertical_Members"
    ] = Field(..., frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = (
        r"^GEOMGROUP-PROPS-\d{4}-VERTICAL-MEMBERS$"
    )
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: GeometryGroupPropertiesVerticalMembers


class GeometryGroupVerticalMembers(GeometryGroupBase):
    """Shared metadata for above-ground and below-ground vertical members."""

    speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection:"
        "BDA_Geometry_Group_Vertical_Members"
    ] = Field(
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Vertical_Members",
        frozen=True,
    )

    bda_speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection:"
        "BDA_Geometry_Group_Vertical_Members"
    ] = Field(..., frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = (
        r"^COL-GEOMGROUP-\d{4}-VERTICAL-MEMBERS$"
    )
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    name: Literal["Vertical Members"] = "Vertical Members"


def _create_vertical_members_properties(
    application_id: str,
    isUser: bool,
) -> GeometryGroupParametersVerticalMembers:
    return GeometryGroupParametersVerticalMembers(
        id=None,
        applicationId=application_id.replace(
            "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
        ),
        bda_speckle_type=(
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_Vertical_Members"
        ),
        properties=GeometryGroupPropertiesVerticalMembers(
            **{
                "Structural Component Type":
                    VerticalMembersStructureComponentGroupType(),
                "Geometry Group Properties":
                    VerticalMembersGroupProperties.create(isUser=isUser),
            }
        ),
    )


AboveGroundVerticalMembersGroupElements = Annotated[
    Union[
        GeometryGroupParametersVerticalMembers,
        GeometryGroupPier,
        GeometryGroupWall,
    ],
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupVerticalMembersAboveGround(GeometryGroupVerticalMembers):
    elements: list[AboveGroundVerticalMembersGroupElements] = Field(
        default_factory=list,
        json_schema_extra={
            "minItems": 1,
            "allOf": [
                {
                    "contains": {
                        "type": "object",
                        "properties": {
                            "speckle_type": {
                                "const": (
                                    "Objects.Data.DataObject:"
                                    "BDA_Geometry_Group_Properties_"
                                    "Vertical_Members"
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
    def validate_vertical_members_elements(
        self,
    ) -> "GeometryGroupVerticalMembersAboveGround":
        properties_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_Vertical_Members"
        )
        properties_count = sum(
            element.speckle_type == properties_type
            for element in self.elements
        )
        if properties_count != 1:
            raise ValueError(
                "GeometryGroupVerticalMembersAboveGround.elements must "
                "contain exactly one properties object."
            )
        return self

    @classmethod
    def create(
        cls,
        piers: list[GeometryGroupPier] | None = None,
        walls: list[GeometryGroupWall] | None = None,
        application_id: str = "COL-GEOMGROUP-0001-VERTICAL-MEMBERS",
        isUser: bool = True,
    ) -> "GeometryGroupVerticalMembersAboveGround":
        return cls(
            id=None,
            applicationId=application_id,
            bda_speckle_type=(
                "Speckle.Core.Models.Collections.Collection:"
                "BDA_Geometry_Group_Vertical_Members"
            ),
            elements=[
                _create_vertical_members_properties(application_id, isUser),
                *(piers or []),
                *(walls or []),
            ],
        )


BelowGroundVerticalMembersGroupElements = Annotated[
    Union[
        GeometryGroupParametersVerticalMembers,
        GeometryGroupPile,
    ],
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupVerticalMembersBelowGround(GeometryGroupVerticalMembers):
    elements: list[BelowGroundVerticalMembersGroupElements] = Field(
        default_factory=list,
        json_schema_extra={
            "minItems": 1,
            "allOf": [
                {
                    "contains": {
                        "type": "object",
                        "properties": {
                            "speckle_type": {
                                "const": (
                                    "Objects.Data.DataObject:"
                                    "BDA_Geometry_Group_Properties_"
                                    "Vertical_Members"
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
    def validate_vertical_members_elements(
        self,
    ) -> "GeometryGroupVerticalMembersBelowGround":
        properties_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_Vertical_Members"
        )
        properties_count = sum(
            element.speckle_type == properties_type
            for element in self.elements
        )
        if properties_count != 1:
            raise ValueError(
                "GeometryGroupVerticalMembersBelowGround.elements must "
                "contain exactly one properties object."
            )
        return self

    @classmethod
    def create(
        cls,
        piles: list[GeometryGroupPile] | None = None,
        application_id: str = "COL-GEOMGROUP-0001-VERTICAL-MEMBERS",
        isUser: bool = True,
    ) -> "GeometryGroupVerticalMembersBelowGround":
        return cls(
            id=None,
            applicationId=application_id,
            bda_speckle_type=(
                "Speckle.Core.Models.Collections.Collection:"
                "BDA_Geometry_Group_Vertical_Members"
            ),
            elements=[
                _create_vertical_members_properties(application_id, isUser),
                *(piles or []),
            ],
        )
