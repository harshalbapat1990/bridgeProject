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

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_diaphragm import GeometryGroupDiaphragm
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_transverse_bracing import GeometryGroupTransverseBracing
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_plan_bracing import GeometryGroupPlanBracing
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_deck_slab import GeometryGroupDeckSlab

# GROUP TYPE IDENTIFICATION
# =============================================================================


class TransverseMembersStructureComponentGroupType(
    StructureComponentGroupType
):
    provided_value: Literal[
        StructuralComponentTypeParaModel.TRANSVERSE_MEMBERS
    ] = StructuralComponentTypeParaModel.TRANSVERSE_MEMBERS


# =============================================================================
# TRANSVERSE MEMBERS PROPERTY SET
# =============================================================================


class TransverseMembersGroupPropertiesParameters(BaseModel):
    pass


class TransverseMembersGroupProperties(GeometryGroupParameterProperties):
    group_parameters: TransverseMembersGroupPropertiesParameters

    @classmethod
    def create(cls, isUser: bool = True) -> "TransverseMembersGroupProperties":
        return cls(
            isUser=isUser,
            group_parameters=TransverseMembersGroupPropertiesParameters(),
        )


# =============================================================================
# COMMON TRANSVERSE MEMBERS METADATA
# =============================================================================


class GeometryGroupPropertiesTransverseMembers(GeometryGroupProperties):
    structural_component_type: (
        TransverseMembersStructureComponentGroupType
    ) = Field(
        alias="Structural Component Type"
    )

    group_properties: TransverseMembersGroupProperties = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersTransverseMembers(
    GeometryGroupParameters
):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_TRANSVERSE_MEMBERS
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_TRANSVERSE_MEMBERS.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-TRANSVERSE-MEMBERS$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: GeometryGroupPropertiesTransverseMembers


# =============================================================================
# TRANSVERSE MEMBERS GROUP
# =============================================================================


TransverseMembersGroupElements = Annotated[
    Union[
        GeometryGroupParametersTransverseMembers,
        GeometryGroupDiaphragm,
        GeometryGroupTransverseBracing,
        GeometryGroupPlanBracing,
        GeometryGroupDeckSlab,
    ],
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupTransverseMembers(
    GeometryGroupBase
):
    bda_speckle_type: Literal[
        SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_TRANSVERSE_MEMBERS
    ] = Field(SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_TRANSVERSE_MEMBERS.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-TRANSVERSE-MEMBERS$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    name: Literal[
        "Transverse Members"
    ] = "Transverse Members"

    elements: list[TransverseMembersGroupElements] = Field(
        default_factory=list,
        json_schema_extra={
            "minItems": 1,
            "allOf": [
                {
                    # Exactly one transverse members properties object
                    "contains": {
                        "type": "object",
                        "properties": {
                            "bda_speckle_type": {
                                "const": (
                                    "Objects.Data.DataObject:"
                                    "BDA_Geometry_Group_Properties_"
                                    "Transverse_Members"
                                )
                            }
                        },
                        "required": ["bda_speckle_type"],
                    },
                    "minContains": 1,
                    "maxContains": 1,
                },
                {
                    # 0..2 diaphragms
                    "contains": {
                        "type": "object",
                        "properties": {
                            "bda_speckle_type": {
                                "const": (
                                    "Speckle.Core.Models.Collections.Collection:"
                                    "BDA_Geometry_Group_Diaphragm"
                                )
                            }
                        },
                        "required": ["bda_speckle_type"],
                    },
                    "minContains": 0,
                    "maxContains": 2,
                },
                {
                    # 0..N transverse bracing groups
                    "contains": {
                        "type": "object",
                        "properties": {
                            "bda_speckle_type": {
                                "const": (
                                    "Speckle.Core.Models.Collections.Collection:"
                                    "BDA_Geometry_Group_Transverse_Bracing"
                                )
                            }
                        },
                        "required": ["bda_speckle_type"],
                    },
                    "minContains": 0,
                },
                {
                    # 0..1 plan bracing group
                    "contains": {
                        "type": "object",
                        "properties": {
                            "bda_speckle_type": {
                                "const": (
                                    "Speckle.Core.Models.Collections.Collection:"
                                    "BDA_Geometry_Group_PlanBracing"
                                )
                            }
                        },
                        "required": ["bda_speckle_type"],
                    },
                    "minContains": 0,
                    "maxContains": 1,
                },
                {
                    # 0..1 deck slab group
                    "contains": {
                        "type": "object",
                        "properties": {
                            "bda_speckle_type": {
                                "const": (
                                    "Speckle.Core.Models.Collections.Collection:"
                                    "BDA_Geometry_Group_Deck_Slab"
                                )
                            }
                        },
                        "required": ["bda_speckle_type"],
                    },
                    "minContains": 0,
                    "maxContains": 1,
                },
            ],
        },
    )

    @model_validator(mode="after")
    def validate_transverse_members_elements(self) -> "GeometryGroupTransverseMembers":

        properties_speckle_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_Transverse_Members"
        )

        diaphragm_speckle_type = (
            "Speckle.Core.Models.Collections.Collection:"
            "BDA_Geometry_Group_Diaphragm"
        )

        plan_bracing_speckle_type = (
            "Speckle.Core.Models.Collections.Collection:"
            "BDA_Geometry_Group_PlanBracing"
        )

        deck_slab_speckle_type = (
            "Speckle.Core.Models.Collections.Collection:"
            "BDA_Geometry_Group_Deck_Slab"
        )

        properties_count = sum(
            1
            for element in self.elements
            if element.bda_speckle_type == properties_speckle_type
        )

        diaphragm_count = sum(
            1
            for element in self.elements
            if element.bda_speckle_type == diaphragm_speckle_type
        )

        plan_bracing_count = sum(
            1
            for element in self.elements
            if element.bda_speckle_type == plan_bracing_speckle_type
        )

        deck_slab_count = sum(
            1
            for element in self.elements
            if element.bda_speckle_type == deck_slab_speckle_type
        )

        if properties_count != 1:
            raise ValueError(
                "GeometryGroupTransverseMembers.elements must contain "
                "exactly one "
                f"{properties_speckle_type} object. "
                f"Found {properties_count}."
            )

        if diaphragm_count > 2:
            raise ValueError(
                "GeometryGroupTransverseMembers.elements may contain "
                "at most 2 "
                f"{diaphragm_speckle_type} collections. "
                f"Found {diaphragm_count}."
            )

        if plan_bracing_count > 1:
            raise ValueError(
                "GeometryGroupTransverseMembers.elements may contain "
                "at most 1 "
                f"{plan_bracing_speckle_type} collection. "
                f"Found {plan_bracing_count}."
            )

        if deck_slab_count > 1:
            raise ValueError(
                "GeometryGroupTransverseMembers.elements may contain "
                "at most 1 "
                f"{deck_slab_speckle_type} collection. "
                f"Found {deck_slab_count}."
            )

        return self

    @classmethod
    def create(
        cls,
        plan_bracing: GeometryGroupPlanBracing | None = None,
        deck_slab: GeometryGroupDeckSlab | None = None,
        diaphragms: list[GeometryGroupDiaphragm] | None = None,
        transverse_bracings: (
            list[GeometryGroupTransverseBracing] | None
        ) = None,
        application_id: str = "COL-GEOMGROUP-0001-TRANSVERSE-MEMBERS",
        isUser: bool = True,
    ) -> "GeometryGroupTransverseMembers":

        if diaphragms and len(diaphragms) > 2:
            raise ValueError(
                "A maximum of 2 diaphragm groups is permitted."
            )

        elements: list[TransverseMembersGroupElements] = [
            GeometryGroupParametersTransverseMembers(
                id=None,
                applicationId=application_id.replace(
                    "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                ),
                properties=(
                    GeometryGroupPropertiesTransverseMembers(
                        **{
                            "Structural Component Type":
                                TransverseMembersStructureComponentGroupType(),

                            "Geometry Group Properties":
                                TransverseMembersGroupProperties.create(
                                    isUser=isUser,
                                ),
                        }
                    )
                ),
            )
        ]

        if diaphragms:
            elements.extend(diaphragms)

        if transverse_bracings:
            elements.extend(transverse_bracings)

        if plan_bracing is not None:
            elements.append(plan_bracing)

        if deck_slab is not None:
            elements.append(deck_slab)

        return cls(
            id=None,
            applicationId=application_id,
            elements=elements,
        )

if __name__ == "__main__":

    transverse_members = (
        GeometryGroupTransverseMembers.create(
            application_id="COL-GEOMGROUP-0001-TRANSVERSE-MEMBERS"
        )
    )

    print(
        transverse_members.model_dump_json(
            indent=4
        )
    )