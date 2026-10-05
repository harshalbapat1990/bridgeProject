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


# =============================================================================
# TENDON GROUP PROPERTY SET
# =============================================================================


class TendonGroupPropertiesParameters(BaseModel):
    """
    Tendon Group has no component-specific parameters beyond
    material and section — this intentionally remains empty.
    """

    pass


class TendonGroupProperties(
    GeometryGroupParameterProperties
):
    group_parameters: TendonGroupPropertiesParameters

    @classmethod
    def create(
        cls,
        isUser: bool = True,
    ) -> "TendonGroupProperties":

        return cls(
            isUser=isUser,
            group_parameters=TendonGroupPropertiesParameters(),
        )


# =============================================================================
# GROUP TYPE IDENTIFICATION
# =============================================================================


class TendonGroupStructureComponentGroupType(
    StructureComponentGroupType
):
    provided_value: Literal[
        StructuralComponentTypeParaModel.TENDON_GROUP
    ] = StructuralComponentTypeParaModel.TENDON_GROUP


# =============================================================================
# TENDON GROUP METADATA
# =============================================================================


class GeometryGroupPropertiesTendonGroup(
    GeometryGroupProperties
):
    structural_component_type: (
        TendonGroupStructureComponentGroupType
    ) = Field(
        alias="Structural Component Type"
    )

    material_id: MaterialIdString = Field(
        alias="Material ID",
    )

    section_id: SectionIdString = Field(
        alias="Section ID",
    )

    group_properties: TendonGroupProperties = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersTendonGroup(
    GeometryGroupParameters
):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Tendon_Group"
    ] = Field(
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Tendon_Group",
        frozen=True
    )

    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Tendon_Group"
    ] = Field(
        ...,
        frozen=True
    )

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-TENDON-GROUP$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: GeometryGroupPropertiesTendonGroup


# =============================================================================
# TENDON GROUP
# =============================================================================


TendonGroupElements = Annotated[
    GeometryGroupParametersTendonGroup,
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupTendonGroup(
    GeometryGroupBase
):
    speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Tendon_Group"
    ] = Field(
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Tendon_Group",
        frozen=True
    )

    bda_speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Tendon_Group"
    ] = Field(
        ...,
        frozen=True
    )

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-TENDON-GROUP$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    elements: list[TendonGroupElements] = Field(
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
                                    "BDA_Geometry_Group_Properties_Tendon_Group"
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
    def validate_tendon_group_elements(self) -> "GeometryGroupTendonGroup":
        properties_speckle_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_Tendon_Group"
        )

        properties_count = sum(
            1
            for element in self.elements
            if element.speckle_type == properties_speckle_type
        )

        if properties_count != 1:
            raise ValueError(
                "GeometryGroupTendonGroup.elements must contain "
                "exactly one "
                f"{properties_speckle_type} object. "
                f"Found {properties_count}."
            )

        return self

    @classmethod
    def create(
        cls,
        material_id: str,
        section_id: str,
        application_id: str = "COL-GEOMGROUP-0001-TENDON-GROUP",
        name: str = "tendon_group",
        isUser: bool = True,
    ) -> "GeometryGroupTendonGroup":

        return cls(
            id=None,
            applicationId=application_id,
            name=name,
            bda_speckle_type=(
                "Speckle.Core.Models.Collections.Collection:"
                "BDA_Geometry_Group_Tendon_Group"
            ),
            elements=[
                GeometryGroupParametersTendonGroup(
                    **{
                        "id": None,
                        "applicationId": application_id.replace(
                            "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                        ),
                        "bda_speckle_type": (
                            "Objects.Data.DataObject:"
                            "BDA_Geometry_Group_Properties_Tendon_Group"
                        ),
                        "properties": GeometryGroupPropertiesTendonGroup(
                            **{
                                "Structural Component Type":
                                    TendonGroupStructureComponentGroupType(),

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
                                    TendonGroupProperties.create(
                                        isUser=isUser,
                                    ),
                            }
                        ),
                    }
                )
            ],
        )


if __name__ == "__main__":
    tendon_group = GeometryGroupTendonGroup.create(
        material_id="M_Tendon",
        section_id="S_Tendon",
        application_id="COL-GEOMGROUP-0001-TENDON-GROUP",
    )

    print(
        tendon_group.model_dump_json(
            indent=4,
            by_alias=True,
            exclude_none=True,
        )
    )
