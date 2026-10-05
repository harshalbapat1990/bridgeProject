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
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_girder import (
    GeometryGroupGirder,
)


# =============================================================================
# LONGITUDINAL MEMBERS PROPERTY SET
# =============================================================================


class LongitudinalMembersGroupPropertiesParameters(
    BaseModel
):
    """
    Longitudinal Members currently has no component-specific
    parameters.

    This intentionally remains empty, but keeps the same
    group_parameters structure as other geometry group property sets.
    """

    pass


class LongitudinalMembersGroupProperties(
    GeometryGroupParameterProperties
):
    group_parameters: (
        LongitudinalMembersGroupPropertiesParameters
    )

    @classmethod
    def create(
        cls,
        isUser: bool = True,
    ) -> "LongitudinalMembersGroupProperties":

        return cls(
            isUser=isUser,
            group_parameters=(
                LongitudinalMembersGroupPropertiesParameters()
            ),
        )


# =============================================================================
# GROUP TYPE IDENTIFICATION
# =============================================================================


class LongitudinalMembersStructureComponentGroupType(
    StructureComponentGroupType
):
    provided_value: Literal[
        StructuralComponentTypeParaModel.LONGITUDINAL_MEMBERS
    ] = StructuralComponentTypeParaModel.LONGITUDINAL_MEMBERS


# =============================================================================
# COMMON LONGITUDINAL MEMBERS METADATA
# =============================================================================


class GeometryGroupPropertiesLongitudinalMembers(
    GeometryGroupProperties
):
    structural_component_type: (
        LongitudinalMembersStructureComponentGroupType
    ) = Field(
        alias="Structural Component Type"
    )

    group_properties: LongitudinalMembersGroupProperties = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersLongitudinalMembers(
    GeometryGroupParameters
):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_LONGITUDINAL_MEMBERS
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_LONGITUDINAL_MEMBERS.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-LONGITUDINAL-MEMBERS$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: GeometryGroupPropertiesLongitudinalMembers


# =============================================================================
# LONGITUDINAL MEMBERS GROUP
# =============================================================================


LongitudinalMembersGroupElements = Annotated[
    Union[
        GeometryGroupParametersLongitudinalMembers,
        GeometryGroupGirder,
    ],
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupLongitudinalMembers(
    GeometryGroupBase
):
    bda_speckle_type: Literal[
        SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_LONGITUDINAL_MEMBERS
    ] = Field(SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_LONGITUDINAL_MEMBERS.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-LONGITUDINAL-MEMBERS$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    name: Literal[
        "Longitudinal Members"
    ] = "Longitudinal Members"

    elements: list[LongitudinalMembersGroupElements] = Field(
        default_factory=list,
        json_schema_extra={
            "minItems": 1,
            "allOf": [
                {
                    # Exactly one longitudinal members properties object
                    "contains": {
                        "type": "object",
                        "properties": {
                            "bda_speckle_type": {
                                "const": (
                                    "Objects.Data.DataObject:"
                                    "BDA_Geometry_Group_Properties_"
                                    "Longitudinal_Members"
                                )
                            }
                        },
                        "required": ["bda_speckle_type"],
                    },
                    "minContains": 1,
                    "maxContains": 1,
                },
                {
                    # Optional girders (0..N)
                    "contains": {
                        "type": "object",
                        "properties": {
                            "bda_speckle_type": {
                                "const": (
                                    "Speckle.Core.Models.Collections.Collection:"
                                    "BDA_Geometry_Group_Girder"
                                )
                            }
                        },
                        "required": ["bda_speckle_type"],
                    },
                    "minContains": 0,
                },
            ],
        },
    )

    @model_validator(mode="after")
    def validate_longitudinal_members_elements(self) -> "GeometryGroupLongitudinalMembers":

        properties_speckle_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_Longitudinal_Members"
        )

        properties_count = sum(
            1
            for element in self.elements
            if element.bda_speckle_type == properties_speckle_type
        )

        if properties_count != 1:
            raise ValueError(
                "GeometryGroupLongitudinalMembers.elements must contain "
                "exactly one "
                f"{properties_speckle_type} object. "
                f"Found {properties_count}."
            )

        return self

    @classmethod
    def create(
        cls,
        girders: list[GeometryGroupGirder] | None = None,
        application_id: str = "COL-GEOMGROUP-0001-LONGITUDINAL-MEMBERS",
        isUser: bool = True,
    ) -> "GeometryGroupLongitudinalMembers":

        elements: list[
            LongitudinalMembersGroupElements
        ] = [
            GeometryGroupParametersLongitudinalMembers(
                id=None,
                applicationId=application_id.replace(
                    "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                ),
                properties=(
                    GeometryGroupPropertiesLongitudinalMembers(
                        **{
                            "Structural Component Type":
                                (
                                    LongitudinalMembersStructureComponentGroupType()
                                ),

                            "Geometry Group Properties":
                                (
                                    LongitudinalMembersGroupProperties.create(
                                        isUser=isUser,
                                    )
                                ),
                        }
                    )
                ),
            )
        ]

        elements.extend(girders or [])

        return cls(
            id=None,
            applicationId=application_id,
            elements=elements,
        )


if __name__ == "__main__":

    girder_1 = GeometryGroupGirder.create(
        material_id="steel",
        section_id="G1",
        girder_index=1,
        application_id="COL-GEOMGROUP-0001-GIRDER",
    )

    girder_2 = GeometryGroupGirder.create(
        material_id="steel",
        section_id="G1",
        girder_index=2,
        application_id="COL-GEOMGROUP-0002-GIRDER",
    )

    # -----------------------------------------------------------------
    # 0 girders
    # -----------------------------------------------------------------

    longitudinal_members_0 = (
        GeometryGroupLongitudinalMembers.create(
            application_id="COL-GEOMGROUP-0001-LONGITUDINAL-MEMBERS",
        )
    )

    print("\n=== 0 GIRDERS ===")
    print(
        longitudinal_members_0.model_dump_json(
            indent=4,
            by_alias=True,
            exclude_none=True,
        )
    )

    # -----------------------------------------------------------------
    # 1 girder
    # -----------------------------------------------------------------

    longitudinal_members_1 = (
        GeometryGroupLongitudinalMembers.create(
            girders=[
                girder_1,
            ],
            application_id="COL-GEOMGROUP-0002-LONGITUDINAL-MEMBERS",
        )
    )

    print("\n=== 1 GIRDER ===")
    print(
        longitudinal_members_1.model_dump_json(
            indent=4,
            by_alias=True,
            exclude_none=True,
        )
    )

    # -----------------------------------------------------------------
    # 2 girders
    # -----------------------------------------------------------------

    longitudinal_members_2 = (
        GeometryGroupLongitudinalMembers.create(
            girders=[
                girder_1,
                girder_2,
            ],
            application_id="COL-GEOMGROUP-0003-LONGITUDINAL-MEMBERS",
        )
    )

    print("\n=== 2 GIRDERS ===")
    print(
        longitudinal_members_2.model_dump_json(
            indent=4,
            by_alias=True,
            exclude_none=True,
        )
    )