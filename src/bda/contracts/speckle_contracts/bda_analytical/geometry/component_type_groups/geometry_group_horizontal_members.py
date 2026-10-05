from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes
from typing import Annotated, ClassVar, Literal, Union

from pydantic import BaseModel, Field, model_validator

from bda.contracts.paramodel.groups.enums import StructuralComponentTypeParaModel
from bda.contracts.speckle_contracts.bda_analytical.geometry.geometry_group_base import (
    GeometryGroupBase,
    GeometryGroupParameters,
    GeometryGroupProperties,
    GeometryGroupParameterProperties,
    StructureComponentGroupType,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_crossbeam import (
    GeometryGroupCrossbeam,
)
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_pile_cap import (
    GeometryGroupPileCap,
)


class HorizontalMembersGroupPropertiesParameters(BaseModel):
    pass


class HorizontalMembersGroupProperties(GeometryGroupParameterProperties):
    group_parameters: HorizontalMembersGroupPropertiesParameters

    @classmethod
    def create(
        cls,
        isUser: bool = True,
    ) -> "HorizontalMembersGroupProperties":
        return cls(
            isUser=isUser,
            group_parameters=HorizontalMembersGroupPropertiesParameters(),
        )


class HorizontalMembersStructureComponentGroupType(StructureComponentGroupType):
    provided_value: Literal[
        StructuralComponentTypeParaModel.HORIZONTAL_MEMBERS
    ] = StructuralComponentTypeParaModel.HORIZONTAL_MEMBERS


class GeometryGroupPropertiesHorizontalMembers(GeometryGroupProperties):
    structural_component_type: HorizontalMembersStructureComponentGroupType = Field(
        alias="Structural Component Type"
    )
    group_properties: HorizontalMembersGroupProperties = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersHorizontalMembers(GeometryGroupParameters):
    name: Literal["Geometry Group Properties"] = "Geometry Group Properties"

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_HORIZONTAL_MEMBERS
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_HORIZONTAL_MEMBERS.value, frozen=True)
    APPLICATION_ID_PATTERN: ClassVar[str] = (
        r"^GEOMGROUP-PROPS-\d{4}-HORIZONTAL-MEMBERS$"
    )
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)
    properties: GeometryGroupPropertiesHorizontalMembers


class GeometryGroupHorizontalMembers(GeometryGroupBase):
    """Shared metadata for above-ground and below-ground horizontal members."""

    bda_speckle_type: Literal[
        SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_HORIZONTAL_MEMBERS
    ] = Field(SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_HORIZONTAL_MEMBERS.value, frozen=True)
    APPLICATION_ID_PATTERN: ClassVar[str] = (
        r"^COL-GEOMGROUP-\d{4}-HORIZONTAL-MEMBERS$"
    )
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)
    name: Literal["Horizontal Members"] = "Horizontal Members"


def _create_horizontal_members_properties(
    application_id: str,
    isUser: bool,
) -> GeometryGroupParametersHorizontalMembers:
    return GeometryGroupParametersHorizontalMembers(
        id=None,
        applicationId=application_id.replace(
            "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
        ),
        properties=GeometryGroupPropertiesHorizontalMembers(
            **{
                "Structural Component Type":
                    HorizontalMembersStructureComponentGroupType(),
                "Geometry Group Properties":
                    HorizontalMembersGroupProperties.create(isUser=isUser),
            }
        ),
    )


AboveGroundHorizontalMembersGroupElements = Annotated[
    Union[
        GeometryGroupParametersHorizontalMembers,
        GeometryGroupCrossbeam,
    ],
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupHorizontalMembersAboveGround(GeometryGroupHorizontalMembers):
    elements: list[AboveGroundHorizontalMembersGroupElements] = Field(
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
                                    "BDA_Geometry_Group_Properties_"
                                    "Horizontal_Members"
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
    def validate_horizontal_members_elements(
        self,
    ) -> "GeometryGroupHorizontalMembersAboveGround":
        properties_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_Horizontal_Members"
        )
        if sum(element.bda_speckle_type == properties_type for element in self.elements) != 1:
            raise ValueError(
                "GeometryGroupHorizontalMembersAboveGround.elements must "
                "contain exactly one properties object."
            )
        return self

    @classmethod
    def create(
        cls,
        crossbeam: GeometryGroupCrossbeam | None = None,
        application_id: str = "COL-GEOMGROUP-0001-HORIZONTAL-MEMBERS",
        isUser: bool = True,
    ) -> "GeometryGroupHorizontalMembersAboveGround":
        return cls(
            id=None,
            applicationId=application_id,
            bda_speckle_type=(
                "Speckle.Core.Models.Collections.Collection:"
                "BDA_Geometry_Group_Horizontal_Members"
            ),
            elements=[
                _create_horizontal_members_properties(application_id, isUser),
                *([crossbeam] if crossbeam is not None else []),
            ],
        )


BelowGroundHorizontalMembersGroupElements = Annotated[
    Union[
        GeometryGroupParametersHorizontalMembers,
        GeometryGroupPileCap,
    ],
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupHorizontalMembersBelowGround(GeometryGroupHorizontalMembers):
    elements: list[BelowGroundHorizontalMembersGroupElements] = Field(
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
                                    "BDA_Geometry_Group_Properties_"
                                    "Horizontal_Members"
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
    def validate_horizontal_members_elements(
        self,
    ) -> "GeometryGroupHorizontalMembersBelowGround":
        properties_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_Horizontal_Members"
        )
        if sum(element.bda_speckle_type == properties_type for element in self.elements) != 1:
            raise ValueError(
                "GeometryGroupHorizontalMembersBelowGround.elements must "
                "contain exactly one properties object."
            )
        return self

    @classmethod
    def create(
        cls,
        pile_cap: GeometryGroupPileCap | None = None,
        application_id: str = "COL-GEOMGROUP-0001-HORIZONTAL-MEMBERS",
        isUser: bool = True,
    ) -> "GeometryGroupHorizontalMembersBelowGround":
        return cls(
            id=None,
            applicationId=application_id,
            bda_speckle_type=(
                "Speckle.Core.Models.Collections.Collection:"
                "BDA_Geometry_Group_Horizontal_Members"
            ),
            elements=[
                _create_horizontal_members_properties(application_id, isUser),
                *([pile_cap] if pile_cap is not None else []),
            ],
        )
