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
# PIER PARAMETERS
# =============================================================================


class TransverseOffsetParameter(LengthParameter):
    name: Literal[
        "Transverse Offset"
    ] = "Transverse Offset"

    description: Literal[
        "Transverse offset of the pier"
    ] = "Transverse offset of the pier"

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
# PIER PROPERTY SET
# =============================================================================


class PierGroupPropertiesParameters(
    BaseModel
):
    transverse_offset: (
        TransverseOffsetParameter
    ) = Field(
        alias="Transverse Offset"
    )


class PierGroupProperties(
    GeometryGroupParameterProperties
):
    group_parameters: (
        PierGroupPropertiesParameters
    )

    @classmethod
    def create(
        cls,
        transverse_offset: float,
        transverse_offset_unit: Literal[
            "m",
            "ft",
        ] = "m",
        isUser: bool = True,
    ) -> "PierGroupProperties":

        return cls(
            isUser=isUser,
            group_parameters=(
                PierGroupPropertiesParameters(
                    **{
                        "Transverse Offset":
                            TransverseOffsetParameter(
                                isUser=isUser,
                                provided_value=(
                                    transverse_offset
                                ),
                                provided_unit=(
                                    transverse_offset_unit
                                ),
                                base_value=(
                                    transverse_offset
                                )
                            ),
                    }
                )
            ),
        )


# =============================================================================
# GROUP TYPE IDENTIFICATION
# =============================================================================


class PierStructureComponentGroupType(
    StructureComponentGroupType
):
    provided_value: Literal[
        StructuralComponentTypeParaModel.PIER
    ] = (
        StructuralComponentTypeParaModel.PIER
    )


# =============================================================================
# PIER METADATA
# =============================================================================


class GeometryGroupPropertiesPier(
    GeometryGroupProperties
):
    structural_component_type: (
        PierStructureComponentGroupType
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
        PierGroupProperties
    ) = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersPier(
    GeometryGroupParameters
):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Pier"
    ] = "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Pier"

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-PIER$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: (
        GeometryGroupPropertiesPier
    )


# =============================================================================
# PIER GROUP
# =============================================================================


PierGroupElements = Annotated[
    GeometryGroupParametersPier,
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupPier(
    GeometryGroupBase
):
    bda_speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Pier"
    ] = "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Pier"

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-PIER$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    elements: list[
        PierGroupElements
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
                                    "BDA_Geometry_Group_Properties_Pier"
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
    def validate_pier_elements(self) -> "GeometryGroupPier":

        pier_properties_speckle_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_Pier"
        )

        pier_properties_count = sum(
            1
            for element in self.elements
            if element.bda_speckle_type
            == pier_properties_speckle_type
        )

        if pier_properties_count != 1:
            raise ValueError(
                "GeometryGroupPier.elements must contain "
                "exactly one "
                f"{pier_properties_speckle_type} object. "
                f"Found {pier_properties_count}."
            )

        return self

    @classmethod
    def create(
        cls,
        material_id: str = "concrete",
        section_id: str = "pier_section",
        transverse_offset: float = 0.0,
        transverse_offset_unit: Literal[
            "m",
            "ft",
        ] = "m",
        application_id: str = "COL-GEOMGROUP-0001-PIER",
        name: str | None = None,
        isUser: bool = True,
    ) -> "GeometryGroupPier":

        return cls(
            id=None,
            applicationId=application_id,
            name=name if name is not None else application_id,
            elements=[
                GeometryGroupParametersPier(
                    **{
                        "id": None,
                        "applicationId": application_id.replace(
                            "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                        ),
                        "properties":
                            GeometryGroupPropertiesPier(
                                **{
                                    "Structural Component Type":
                                        (
                                            PierStructureComponentGroupType()
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
                                            PierGroupProperties.create(
                                                transverse_offset=
                                                    transverse_offset,
                                                transverse_offset_unit=
                                                    transverse_offset_unit,
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

    pier = GeometryGroupPier.create(
        material_id="M_Pier",
        section_id="S_Pier",
        transverse_offset=5.5,
        transverse_offset_unit="m",
        application_id="COL-GEOMGROUP-0001-PIER",
    )

    print(
        pier.model_dump_json(
            indent=4
        )
    )