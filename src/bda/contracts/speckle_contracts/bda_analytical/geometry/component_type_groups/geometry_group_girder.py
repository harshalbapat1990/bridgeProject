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
    SectionIdString,
    MaterialIdString,
)

from bda.contracts.speckle_contracts.base_objects import (
    UnitlessParameter,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_tendon_group import (
    GeometryGroupTendonGroup,
)


# =============================================================================
# GIRDER PARAMETERS
# =============================================================================


class GirderIndexParameter(UnitlessParameter[int]):
    name: Literal["Girder Index"] = "Girder Index"

    description: Literal[
        "Index of the girder"
    ] = "Index of the girder"

    symbol: None = None

    provided_value: int


# =============================================================================
# GIRDER PROPERTY SET
# =============================================================================


class GirderGroupPropertiesParameters(BaseModel):
    girder_index: GirderIndexParameter = Field(
        alias="Girder Index"
    )


class GirderGroupProperties(
    GeometryGroupParameterProperties
):
    group_parameters: GirderGroupPropertiesParameters

    @classmethod
    def create(
        cls,
        girder_index: int,
        isUser: bool = True,
    ) -> "GirderGroupProperties":

        return cls(
            isUser=isUser,
            group_parameters=(
                GirderGroupPropertiesParameters(
                    **{
                        "Girder Index":
                            GirderIndexParameter(
                                isUser=isUser,
                                provided_value=girder_index,
                            ),
                    }
                )
            ),
        )


# =============================================================================
# GROUP TYPE IDENTIFICATION
# =============================================================================


class GirderStructureComponentGroupType(
    StructureComponentGroupType
):
    provided_value: Literal[
        StructuralComponentTypeParaModel.GIRDER
    ] = StructuralComponentTypeParaModel.GIRDER


# =============================================================================
# GIRDER METADATA
# =============================================================================


class GeometryGroupPropertiesGirder(
    GeometryGroupProperties
):
    structural_component_type: (
        GirderStructureComponentGroupType
    ) = Field(
        alias="Structural Component Type"
    )

    material_id: MaterialIdString = Field(
        alias="Material ID",
    )

    section_id: SectionIdString = Field(
        alias="Section ID",
    )

    group_properties: GirderGroupProperties = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersGirder(
    GeometryGroupParameters
):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_GIRDER
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_GIRDER.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-GIRDER$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: GeometryGroupPropertiesGirder


# =============================================================================
# GIRDER GROUP
# =============================================================================


GirderGroupElements = Annotated[
    Union[
        GeometryGroupParametersGirder,
        GeometryGroupTendonGroup,
    ],
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupGirder(
    GeometryGroupBase
):
    bda_speckle_type: Literal[
        SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_GIRDER
    ] = Field(SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_GIRDER.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-GIRDER$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    elements: list[GirderGroupElements] = Field(
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
                                    "BDA_Geometry_Group_Properties_Girder"
                                )
                            }
                        },
                        "required": ["bda_speckle_type"],
                    },
                    "minContains": 1,
                    "maxContains": 1,
                },
                {
                    # Optional tendon groups (0..N)
                    "contains": {
                        "type": "object",
                        "properties": {
                            "bda_speckle_type": {
                                "const": (
                                    "Speckle.Core.Models.Collections.Collection:"
                                    "BDA_Geometry_Group_Tendon_Group"
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
    def validate_girder_elements(self) -> "GeometryGroupGirder":
        girder_properties_speckle_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_Girder"
        )

        girder_properties_count = sum(
            1
            for element in self.elements
            if element.bda_speckle_type
            == girder_properties_speckle_type
        )

        if girder_properties_count != 1:
            raise ValueError(
                "GeometryGroupGirder.elements must contain "
                "exactly one "
                f"{girder_properties_speckle_type} object. "
                f"Found {girder_properties_count}."
            )

        return self

    @classmethod
    def create(
        cls,
        material_id: str = "steel",
        section_id: str = "girder_section",
        girder_index: int = 0,
        application_id: str = "COL-GEOMGROUP-0001-GIRDER",
        name: str = None,
        tendon_groups: list[GeometryGroupTendonGroup] | None = None,
        isUser: bool = True,
    ) -> "GeometryGroupGirder":

        elements: list[GirderGroupElements] = [
            GeometryGroupParametersGirder(
                **{
                    "id": None,
                    "applicationId": application_id.replace(
                        "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                    ),
                    "bda_speckle_type": (
                        "Objects.Data.DataObject:"
                        "BDA_Geometry_Group_Properties_Girder"
                    ),
                    "properties": GeometryGroupPropertiesGirder(
                        **{
                            "Structural Component Type":
                                GirderStructureComponentGroupType(),

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
                                GirderGroupProperties.create(
                                    girder_index=girder_index,
                                    isUser=isUser,
                                ),
                        }
                    ),
                }
            )
        ]

        elements.extend(tendon_groups or [])

        return cls(
            id=None,
            applicationId=application_id,
            name=name if name is not None else f"girder_{girder_index}",
            elements=elements,
        )


if __name__ == "__main__":
    girder = GeometryGroupGirder.create(
        material_id="M_Girder",
        section_id="S_Girder",
        girder_index=1,
        application_id="COL-GEOMGROUP-0001-GIRDER",
    )

    print(
        girder.model_dump_json(
            indent=4
        )
    )