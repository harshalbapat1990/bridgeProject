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

from bda.contracts.speckle_contracts.unit_parameters import LengthParameter


# =============================================================================
# PILE CAP PARAMETERS
# =============================================================================


class TopOfPileCapLevelParameter(LengthParameter):
    name: Literal[
        "Top Of Pile Cap Level"
    ] = "Top Of Pile Cap Level"

    description: Literal[
        "Top level of the pile cap"
    ] = "Top level of the pile cap"

    symbol: None = None

    provided_unit: Literal[
        "m",
        "ft",
    ]

    base_unit: Literal[
        "m"
    ] = "m"

    provided_value: float


class ElementLengthParameter(LengthParameter):
    name: Literal[
        "Element Length"
    ] = "Element Length"

    description: Literal[
        "Length of the pile cap element"
    ] = "Length of the pile cap element"

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
# PILE CAP PROPERTY SET
# =============================================================================


class PileCapGroupPropertiesParameters(
    BaseModel
):
    top_of_pile_cap_level: (
        TopOfPileCapLevelParameter
    ) = Field(
        alias="Top Of Pile Cap Level"
    )

    element_length: (
        ElementLengthParameter
    ) = Field(
        alias="Element Length"
    )


class PileCapGroupProperties(
    GeometryGroupParameterProperties
):
    group_parameters: (
        PileCapGroupPropertiesParameters
    )

    @classmethod
    def create(
        cls,
        top_of_pile_cap_level: float,
        element_length: float,
        unit: Literal[
            "m",
            "ft",
        ] = "m",
        isUser: bool = True,
    ) -> "PileCapGroupProperties":

        return cls(
            isUser=isUser,
            group_parameters=(
                PileCapGroupPropertiesParameters(
                    **{
                        "Top Of Pile Cap Level":
                            TopOfPileCapLevelParameter(
                                isUser=isUser,
                                provided_value=
                                    top_of_pile_cap_level,
                                base_value=
                                    top_of_pile_cap_level,
                                provided_unit=unit,
                            ),

                        "Element Length":
                            ElementLengthParameter(
                                isUser=isUser,
                                provided_value=
                                    element_length,
                                base_value=
                                    element_length,
                                provided_unit=unit,
                            ),
                    }
                )
            ),
        )


# =============================================================================
# GROUP TYPE IDENTIFICATION
# =============================================================================


class PileCapStructureComponentGroupType(
    StructureComponentGroupType
):
    provided_value: Literal[
        StructuralComponentTypeParaModel.PILE_CAP
    ] = (
        StructuralComponentTypeParaModel.PILE_CAP
    )


# =============================================================================
# PILE CAP METADATA
# =============================================================================


class GeometryGroupPropertiesPileCap(
    GeometryGroupProperties
):
    structural_component_type: (
        PileCapStructureComponentGroupType
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
        PileCapGroupProperties
    ) = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersPileCap(
    GeometryGroupParameters
):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_PILE_CAP
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_PILE_CAP.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-PILE-CAP$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: (
        GeometryGroupPropertiesPileCap
    )


# =============================================================================
# PILE CAP GROUP
# =============================================================================


PileCapGroupElements = Annotated[
    GeometryGroupParametersPileCap,
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupPileCap(
    GeometryGroupBase
):
    bda_speckle_type: Literal[
        SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_PILE_CAP
    ] = Field(SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_PILE_CAP.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-PILE-CAP$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    elements: list[
        PileCapGroupElements
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
                                    "BDA_Geometry_Group_Properties_Pile_Cap"
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
    def validate_pile_cap_elements(self) -> "GeometryGroupPileCap":

        pile_cap_properties_speckle_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_Pile_Cap"
        )

        pile_cap_properties_count = sum(
            1
            for element in self.elements
            if element.bda_speckle_type
            == pile_cap_properties_speckle_type
        )

        if pile_cap_properties_count != 1:
            raise ValueError(
                "GeometryGroupPileCap.elements must contain "
                "exactly one "
                f"{pile_cap_properties_speckle_type} object. "
                f"Found {pile_cap_properties_count}."
            )

        return self

    @classmethod
    def create(
        cls,
        material_id: str = "concrete",
        section_id: str = "pile_cap_section",
        top_of_pile_cap_level: float = 0.0,
        element_length: float = 1.0,
        unit: Literal[
            "m",
            "ft",
        ] = "m",
        application_id: str = "COL-GEOMGROUP-0001-PILE-CAP",
        name: str | None = None,
        isUser: bool = True,
    ) -> "GeometryGroupPileCap":

        return cls(
            id=None,
            applicationId=application_id,
            name=name if name is not None else application_id,
            elements=[
                GeometryGroupParametersPileCap(
                    **{
                        "id": None,
                        "applicationId": application_id.replace(
                            "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                        ),
                        "properties":
                            GeometryGroupPropertiesPileCap(
                                **{
                                    "Structural Component Type":
                                        (
                                            PileCapStructureComponentGroupType()
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
                                            PileCapGroupProperties.create(
                                                top_of_pile_cap_level=
                                                    top_of_pile_cap_level,
                                                element_length=
                                                    element_length,
                                                unit=unit,
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

    pile_cap = GeometryGroupPileCap.create(
        material_id="M_PileCap",
        section_id="S_PileCap",
        top_of_pile_cap_level=102.5,
        element_length=8.0,
        unit="m",
        application_id="COL-GEOMGROUP-0001-PILE-CAP",
    )

    print(
        pile_cap.model_dump_json(
            indent=4
        )
    )