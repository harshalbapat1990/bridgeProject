from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes
from typing import Annotated, ClassVar, Literal, Union

from pydantic import BaseModel, Field, model_validator

from bda.contracts.paramodel.groups.enums import (
    StructuralComponentTypeParaModel,
    BearingConfigurationTypeParaModel
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.geometry_group_base import (
    GeometryGroupBase,
    GeometryGroupParameters,
    GeometryGroupProperties,
    GeometryGroupParameterProperties,
    StructureComponentGroupType,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_superstructure_to_substructure_connections import (
    GeometryGroupSuperstructureToSubstructureConnections,
)

# =============================================================================
# LINKAGE PROPERTY SET
# =============================================================================


class LinkageGroupPropertiesParameters(
    BaseModel
):
    """
    Linkage currently has no component-specific
    parameters.
    """

    pass


class LinkageGroupProperties(
    GeometryGroupParameterProperties
):
    group_parameters: (
        LinkageGroupPropertiesParameters
    )

    @classmethod
    def create(
        cls,
        isUser: bool = True,
    ) -> "LinkageGroupProperties":

        return cls(
            isUser=isUser,
            group_parameters=(
                LinkageGroupPropertiesParameters()
            ),
        )


# =============================================================================
# GROUP TYPE IDENTIFICATION
# =============================================================================


class LinkageStructureComponentGroupType(
    StructureComponentGroupType
):
    provided_value: Literal[
        StructuralComponentTypeParaModel.LINKAGE
    ] = (
        StructuralComponentTypeParaModel.LINKAGE
    )


# =============================================================================
# COMMON LINKAGE METADATA
# =============================================================================


class GeometryGroupPropertiesLinkage(
    GeometryGroupProperties
):
    structural_component_type: (
        LinkageStructureComponentGroupType
    ) = Field(
        alias="Structural Component Type"
    )

    group_properties: (
        LinkageGroupProperties
    ) = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersLinkage(
    GeometryGroupParameters
):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_LINKAGE
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_LINKAGE.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-LINKAGE$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: (
        GeometryGroupPropertiesLinkage
    )


# =============================================================================
# LINKAGE GROUP
# =============================================================================


LinkageGroupElements = Annotated[
    Union[
        GeometryGroupParametersLinkage,
        GeometryGroupSuperstructureToSubstructureConnections,
    ],
    Field(discriminator="bda_speckle_type"),
]
    
class GeometryGroupLinkage(
    GeometryGroupBase
):
    bda_speckle_type: Literal[
        SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_LINKAGE
    ] = Field(SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_LINKAGE.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-LINKAGE$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    name: Literal[
        "Linkage"
    ] = "Linkage"

    elements: list[
        LinkageGroupElements
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
                                    "BDA_Geometry_Group_Properties_Linkage"
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
    def validate_linkage_elements(self) -> "GeometryGroupLinkage":

        properties_speckle_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_Linkage"
        )

        properties_count = sum(
            1
            for element in self.elements
            if element.bda_speckle_type
            == properties_speckle_type
        )

        if properties_count != 1:
            raise ValueError(
                "GeometryGroupLinkage.elements must contain "
                "exactly one "
                f"{properties_speckle_type} object. "
                f"Found {properties_count}."
            )

        return self

    @classmethod
    def create(
        cls,
        connections: list[
            GeometryGroupSuperstructureToSubstructureConnections
        ] | None = None,
        application_id: str = "COL-GEOMGROUP-0001-LINKAGE",
        isUser: bool = True,
    ) -> "GeometryGroupLinkage":

        elements: list[
            LinkageGroupElements
        ] = [
            GeometryGroupParametersLinkage(
                id=None,
                applicationId=application_id.replace(
                    "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                ),
                properties=(
                    GeometryGroupPropertiesLinkage(
                        **{
                            "Structural Component Type":
                                (
                                    LinkageStructureComponentGroupType()
                                ),

                            "Geometry Group Properties":
                                (
                                    LinkageGroupProperties.create(
                                        isUser=isUser,
                                    )
                                ),
                        }
                    )
                ),
            )
        ]

        elements.extend(connections or [])

        return cls(
            id=None,
            applicationId=application_id,
            elements=elements,
        )

if __name__ == "__main__":

    connection = (
        GeometryGroupSuperstructureToSubstructureConnections.create(
            support_index=1,
            bearing_configuration_type=
            BearingConfigurationTypeParaModel.SINGULAR,
        )
    )

    linkage = (
        GeometryGroupLinkage.create(
            connections=[
                connection,
            ],
            application_id="COL-GEOMGROUP-0001-LINKAGE",
        )
    )

    print(
        linkage.model_dump_json(
            indent=4
        )
    )