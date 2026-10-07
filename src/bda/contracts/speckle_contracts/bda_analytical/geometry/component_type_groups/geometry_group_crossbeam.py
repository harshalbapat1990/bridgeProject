from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes
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

from bda.contracts.speckle_contracts.bda_analytical.geometry.shared_parameters.geometry_group_taper_details import (
    TaperedDetailsParameterGroup,
)
from bda.contracts.speckle_contracts.unit_parameters import LengthParameter

# =============================================================================
# CROSSBEAM PARAMETERS
# =============================================================================


class ElementLengthParameter(LengthParameter):
    name: Literal[
        "Element Length"
    ] = "Element Length"

    description: Literal[
        "Crossbeam element length"
    ] = "Crossbeam element length"

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
# CROSSBEAM PROPERTY SET
# =============================================================================


class CrossbeamGroupPropertiesParameters(
    BaseModel
):
    element_length: (
        ElementLengthParameter
    ) = Field(
        alias="Element Length"
    )

    tapered_details: (
        TaperedDetailsParameterGroup
    ) = Field(
        alias="Tapered Details"
    )


class CrossbeamGroupProperties(
    GeometryGroupParameterProperties
):
    group_parameters: (
        CrossbeamGroupPropertiesParameters
    )

    @classmethod
    def create(
        cls,
        element_length: float,
        tapers: list[
            tuple[
                float,
                float,
                str,
            ]
        ],
        length_unit: Literal[
            "m",
            "ft",
        ] = "m",
        isUser: bool = True,
    ) -> "CrossbeamGroupProperties":

        return cls(
            isUser=isUser,
            group_parameters=(
                CrossbeamGroupPropertiesParameters(
                    **{
                        "Element Length":
                            ElementLengthParameter(
                                isUser=isUser,
                                provided_value=
                                    element_length,
                                provided_unit=
                                    length_unit,
                                base_value=
                                    element_length,
                            ),

                        "Tapered Details":
                            TaperedDetailsParameterGroup.create(
                                tapers=tapers,
                                taper_units=
                                    length_unit,
                                isUser=isUser,
                            ),
                    }
                )
            ),
        )


# =============================================================================
# GROUP TYPE IDENTIFICATION
# =============================================================================


class CrossbeamStructureComponentGroupType(
    StructureComponentGroupType
):
    provided_value: Literal[
        StructuralComponentTypeParaModel.CROSSBEAM
    ] = (
        StructuralComponentTypeParaModel.CROSSBEAM
    )


# =============================================================================
# CROSSBEAM METADATA
# =============================================================================


class GeometryGroupPropertiesCrossbeam(
    GeometryGroupProperties
):
    structural_component_type: (
        CrossbeamStructureComponentGroupType
    ) = Field(
        alias="Structural Component Type"
    )

    material_id: MaterialIdString = Field(
        alias="Material ID"
    )

    section_id: SectionIdString = Field(
        alias="Section ID"
    )

    group_properties: (
        CrossbeamGroupProperties
    ) = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersCrossbeam(
    GeometryGroupParameters
):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_CROSSBEAM
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_CROSSBEAM.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-CROSSBEAM$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: (
        GeometryGroupPropertiesCrossbeam
    )


# =============================================================================
# CROSSBEAM GROUP
# =============================================================================


CrossbeamGroupElements = Annotated[
    GeometryGroupParametersCrossbeam,
    Field(
        discriminator="bda_speckle_type"
    ),
]


class GeometryGroupCrossbeam(
    GeometryGroupBase
):
    bda_speckle_type: Literal[
        SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_CROSSBEAM
    ] = Field(SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_CROSSBEAM.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-CROSSBEAM$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    elements: list[
        CrossbeamGroupElements
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
                                    "BDA_Geometry_Group_Properties_Crossbeam"
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
    def validate_crossbeam_elements(self) -> "GeometryGroupCrossbeam":

        crossbeam_properties_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_Crossbeam"
        )

        crossbeam_properties_count = sum(
            1
            for element in self.elements
            if element.bda_speckle_type
            == crossbeam_properties_type
        )

        if crossbeam_properties_count != 1:
            raise ValueError(
                "GeometryGroupCrossbeam.elements "
                "must contain exactly one "
                f"{crossbeam_properties_type} object. "
                f"Found {crossbeam_properties_count}."
            )

        return self

    @classmethod
    def create(
        cls,
        material_id: str,
        section_id: str,
        element_length: float,
        tapers: list[
            tuple[
                float,
                float,
                str,
            ]
        ],
        length_unit: Literal[
            "m",
            "ft",
        ] = "m",
        application_id: str = "COL-GEOMGROUP-0001-CROSSBEAM",
        name: str | None = None,
        isUser: bool = True,
    ) -> "GeometryGroupCrossbeam":

        return cls(
            id=None,
            applicationId=application_id,
            name=name if name is not None else application_id,
            elements=[
                GeometryGroupParametersCrossbeam(
                    **{
                        "id": None,
                        "applicationId": application_id.replace(
                            "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                        ),

                        "properties":
                            GeometryGroupPropertiesCrossbeam(
                                **{
                                    "Structural Component Type":
                                        (
                                            CrossbeamStructureComponentGroupType()
                                        ),

                                    "Material ID":
                                        (
                                            MaterialIdString(
                                                isUser=False,
                                                provided_value=
                                                    material_id,
                                            )
                                        ),

                                    "Section ID":
                                        (
                                            SectionIdString(
                                                isUser=False,
                                                provided_value=
                                                    section_id,
                                            )
                                        ),

                                    "Geometry Group Properties":
                                        (
                                            CrossbeamGroupProperties.create(
                                                element_length=
                                                    element_length,
                                                tapers=
                                                    tapers,
                                                length_unit=
                                                    length_unit,
                                                isUser=
                                                    isUser,
                                            )
                                        ),
                                }
                            ),
                    }
                )
            ],
        )


if __name__ == "__main__":

    crossbeam = (
        GeometryGroupCrossbeam.create(
            material_id="Steel",
            section_id="CB_01",
            element_length=12.0,
            tapers=[
                (
                    0.0,
                    4.0,
                    "CB_SEC_1",
                ),
                (
                    4.0,
                    8.0,
                    "CB_SEC_2",
                ),
                (
                    8.0,
                    12.0,
                    "CB_SEC_3",
                ),
            ],
            application_id="COL-GEOMGROUP-0001-CROSSBEAM",
        )
    )

    print(
        crossbeam.model_dump_json(
            indent=4
        )
    )