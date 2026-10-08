from typing import Annotated, ClassVar, Literal, Union

from pydantic import BaseModel, Field

from bda.contracts.paramodel.groups.enums import (
    StructuralComponentTypeParaModel,
    BearingConfigurationTypeParaModel,
    SpacingTypeParaModel,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.geometry_group_base import (
    GeometryGroupBase,
    GeometryGroupParameters,
    GeometryGroupProperties,
    GeometryGroupParameterProperties,
    StructureComponentGroupType,
)

from bda.contracts.speckle_contracts.base_objects import (
    UnitlessParameter
)
from bda.contracts.speckle_contracts.unit_parameters import LengthParameter
from bda.contracts.speckle_contracts.bda_analytical.common_parameters import SupportIndexParameter
# =============================================================================
# TYPE SPECIFIC PARAMETERS
# =============================================================================


class NumberOfBearingsParameter(
    UnitlessParameter[int]
):
    name: Literal[
        "Number Of Bearings"
    ] = "Number Of Bearings"

    description: Literal[
        "Number of bearings"
    ] = "Number of bearings"

    symbol: None = None

    provided_value: int


class BearingConfigurationType(
    UnitlessParameter[
        BearingConfigurationTypeParaModel
    ]
):
    name: Literal[
        "Bearing Configuration Type"
    ] = "Bearing Configuration Type"

    description: Literal[
        "Bearing configuration arrangement"
    ] = "Bearing configuration arrangement"

    symbol: None = None

    provided_value: (
        BearingConfigurationTypeParaModel
    )


class BearingConfigurationTypeSingularParameter(
    BearingConfigurationType
):
    provided_value: Literal[
        BearingConfigurationTypeParaModel.SINGULAR
    ] = (
        BearingConfigurationTypeParaModel.SINGULAR
    )


class BearingConfigurationTypeMultipleParameter(
    BearingConfigurationType
):
    provided_value: Literal[
        BearingConfigurationTypeParaModel.MULTIPLE
    ] = (
        BearingConfigurationTypeParaModel.MULTIPLE
    )


class BearingSpacingType(
    UnitlessParameter[
        SpacingTypeParaModel
    ]
):
    name: Literal[
        "Bearing Spacing Type"
    ] = "Bearing Spacing Type"

    description: Literal[
        "Bearing spacing type"
    ] = "Bearing spacing type"

    symbol: None = None

    provided_value: (
        SpacingTypeParaModel
    )


class BearingSpacingTypeUniformParameter(
    BearingSpacingType
):
    provided_value: Literal[
        SpacingTypeParaModel.UNIFORM
    ] = (
        SpacingTypeParaModel.UNIFORM
    )


class BearingSpacingTypeCustomParameter(
    BearingSpacingType
):
    provided_value: Literal[
        SpacingTypeParaModel.VARIABLE
    ] = (
        SpacingTypeParaModel.VARIABLE
    )


class BearingSpacingParameter(LengthParameter[list[float]]):
    name: Literal[
        "Bearing Spacing"
    ] = "Bearing Spacing"

    description: Literal[
        "Spacing between bearings"
    ] = "Spacing between bearings"

    symbol: None = None

    provided_unit: Literal[
        "m",
        "ft",
    ]

    base_unit: Literal[
        "m"
    ] = "m"

    provided_value: list[float]


# =============================================================================
# BEARING Configuration DETAILS
# =============================================================================


class BearingConfigurationDetails_Singular(
    BaseModel
):
    bearing_configuration_type: (
        BearingConfigurationTypeSingularParameter
    ) = Field(
        alias="Bearing Configuration Type"
    )

    number_of_bearings: (
        NumberOfBearingsParameter
    ) = Field(
        alias="Number Of Bearings"
    )


class BearingConfigurationDetails_Multiple(
    BaseModel
):
    bearing_configuration_type: (
        BearingConfigurationTypeMultipleParameter
    ) = Field(
        alias="Bearing Configuration Type"
    )

    number_of_bearings: (
        NumberOfBearingsParameter
    ) = Field(
        alias="Number Of Bearings"
    )

    bearing_spacing_type: (
        BearingSpacingType
    ) = Field(
        alias="Bearing Spacing Type"
    )

    bearing_spacing: (
        BearingSpacingParameter
    ) = Field(
        alias="Bearing Spacing"
    )


BearingConfigurationDetailsParameters = Union[
    BearingConfigurationDetails_Singular,
    BearingConfigurationDetails_Multiple,
]


class BearingConfigurationDetailsParameterGroup(
    GeometryGroupParameterProperties
):
    name: Literal[
        "Bearing Configuration Details"
    ] = "Bearing Configuration Details"

    description: Literal[
        "Bearing configuration details"
    ] = "Bearing configuration details"

    symbol: None = None

    group_parameters: (
        BearingConfigurationDetailsParameters
    )

    @classmethod
    def create(
        cls,
        bearing_configuration_type:
        BearingConfigurationTypeParaModel,
        number_of_bearings:
        int | None = None,
        spacing_type:
        SpacingTypeParaModel | None = None,
        bearing_spacing:
        list[float] | None = None,
        spacing_unit:
        Literal["m", "ft"] = "m",
        isUser: bool = True,
    ) -> "BearingConfigurationDetailsParameterGroup":

        if (
            bearing_configuration_type
            == BearingConfigurationTypeParaModel.SINGULAR
        ):
            return cls(
                isUser=isUser,
                group_parameters=
                BearingConfigurationDetails_Singular(
                    **{
                        "Bearing Configuration Type":
                            (
                                BearingConfigurationTypeSingularParameter(
                                    isUser=isUser
                                )
                            ),

                        "Number Of Bearings":
                            (
                                NumberOfBearingsParameter(
                                    provided_value=1,
                                    isUser=isUser,
                                )
                            ),
                    }
                )
            )

        if (
            bearing_configuration_type
            == BearingConfigurationTypeParaModel.MULTIPLE
        ):

            if number_of_bearings is None:
                raise ValueError(
                    "number_of_bearings "
                    "is required for "
                    "MULTIPLE configuration."
                )

            if spacing_type is None:
                raise ValueError(
                    "spacing_type is "
                    "required for "
                    "MULTIPLE configuration."
                )

            if bearing_spacing is None:
                raise ValueError(
                    "bearing_spacing is "
                    "required for "
                    "MULTIPLE configuration."
                )

            spacing_type_parameter = (
                BearingSpacingTypeUniformParameter(
                    isUser=isUser
                )
                if spacing_type
                == SpacingTypeParaModel.UNIFORM
                else
                BearingSpacingTypeCustomParameter(
                    isUser=isUser
                )
            )

            return cls(
                isUser=isUser,
                group_parameters=
                BearingConfigurationDetails_Multiple(
                    **{
                        "Bearing Configuration Type":
                            (
                                BearingConfigurationTypeMultipleParameter(
                                    isUser=isUser
                                )
                            ),

                        "Number Of Bearings":
                            (
                                NumberOfBearingsParameter(
                                    provided_value=
                                        number_of_bearings,
                                    isUser=isUser,
                                )
                            ),

                        "Bearing Spacing Type":
                            (
                                spacing_type_parameter
                            ),

                        "Bearing Spacing":
                            (
                                BearingSpacingParameter(
                                    provided_value=
                                        bearing_spacing,
                                    base_value=
                                        bearing_spacing,
                                    provided_unit=
                                        spacing_unit,
                                    isUser=isUser,
                                )
                            ),
                    }
                )
            )

        raise ValueError(
            f"Unsupported bearing configuration "
            f"type: {bearing_configuration_type}"
        )


# =============================================================================
# CONNECTION GROUP PROPERTY SET
# =============================================================================


class SuperstructureToSubstructureConnectionsGroupPropertiesParameters(
    BaseModel
):
    support_index: (
        SupportIndexParameter
    ) = Field(
        alias="Support Index"
    )

    bearing_configuration_details: (
        BearingConfigurationDetailsParameterGroup
    ) = Field(
        alias="Bearing Configuration Details"
    )


class SuperstructureToSubstructureConnectionsGroupProperties(
    GeometryGroupParameterProperties
):
    group_parameters: (
        SuperstructureToSubstructureConnectionsGroupPropertiesParameters
    )


# =============================================================================
# GROUP TYPE IDENTIFICATION
# =============================================================================


class SuperstructureToSubstructureConnectionsStructureComponentGroupType(
    StructureComponentGroupType
):
    provided_value: Literal[
        StructuralComponentTypeParaModel.
        SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS
    ] = (
        StructuralComponentTypeParaModel.
        SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS
    )


# =============================================================================
# COMMON METADATA
# =============================================================================


class GeometryGroupPropertiesSuperstructureToSubstructureConnections(
    GeometryGroupProperties
):
    structural_component_type: (
        SuperstructureToSubstructureConnectionsStructureComponentGroupType
    ) = Field(
        alias="Structural Component Type"
    )

    group_properties: (
        SuperstructureToSubstructureConnectionsGroupProperties
    ) = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersSuperstructureToSubstructureConnections(
    GeometryGroupParameters
):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    speckle_type: Literal[
        "Objects.Data.DataObject:"
        "BDA_Geometry_Group_Properties_"
        "Superstructure_To_Substructure_Connections"
    ] = Field(
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Superstructure_To_Substructure_Connections",
        frozen=True
    )

    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Superstructure_To_Substructure_Connections"
    ] = Field(
        ...,
        frozen=True
    )

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-SUPERSTRUCTURE-TO-SUBSTRUCTURE-CONNECTIONS$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: (
        GeometryGroupPropertiesSuperstructureToSubstructureConnections
    )


# =============================================================================
# GROUP
# =============================================================================


SuperstructureToSubstructureConnectionsGroupElements = Annotated[
    Union[
        GeometryGroupParametersSuperstructureToSubstructureConnections,
    ],
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupSuperstructureToSubstructureConnections(
    GeometryGroupBase
):
    speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection:"
        "BDA_Geometry_Group_"
        "Superstructure_To_Substructure_Connections"
    ] = Field(
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Superstructure_To_Substructure_Connections",
        frozen=True
    )

    bda_speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Superstructure_To_Substructure_Connections"
    ] = Field(
        ...,
        frozen=True
    )

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-SUPERSTRUCTURE-TO-SUBSTRUCTURE-CONNECTIONS$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    elements: list[
        SuperstructureToSubstructureConnectionsGroupElements
    ] = Field(
        default_factory=list,
        json_schema_extra={
            "minItems": 1,
            "allOf": [
                {
                    "contains": {
                        "type": "object",
                        "properties": {
                            "speckle_type": {
                                "const":
                                "Objects.Data.DataObject:"
                                "BDA_Geometry_Group_Properties_"
                                "Superstructure_To_Substructure_Connections"
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

    @classmethod
    def create(
        cls,
        support_index: int,
        bearing_configuration_type:
        BearingConfigurationTypeParaModel,
        number_of_bearings:
        int | None = None,
        spacing_type:
        SpacingTypeParaModel | None = None,
        bearing_spacing:
        list[float] | None = None,
        spacing_unit:
        Literal["m", "ft"] = "m",
        isUser: bool = True,
        application_id: str = "COL-GEOMGROUP-0001-SUPERSTRUCTURE-TO-SUBSTRUCTURE-CONNECTIONS",
        name: str | None = None
    ) -> (
        "GeometryGroupSuperstructureToSubstructureConnections"
    ):

        configuration_details = (
            BearingConfigurationDetailsParameterGroup.create(
                bearing_configuration_type=
                    bearing_configuration_type,
                number_of_bearings=
                    number_of_bearings,
                spacing_type=
                    spacing_type,
                bearing_spacing=
                    bearing_spacing,
                spacing_unit=
                    spacing_unit,
                isUser=isUser,
            )
        )

        return cls(
            applicationId = application_id,
            name=name if name is not None else f"Superstructure to Substructure Connections_{support_index}",  # TODO: Improve Autonaming
            bda_speckle_type=(
                "Speckle.Core.Models.Collections.Collection:"
                "BDA_Geometry_Group_Superstructure_To_Substructure_Connections"
            ),
            elements=[
                GeometryGroupParametersSuperstructureToSubstructureConnections(
                    applicationId=application_id.replace(
                        "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                    ),
                    bda_speckle_type=(
                        "Objects.Data.DataObject:"
                        "BDA_Geometry_Group_Properties_Superstructure_To_Substructure_Connections"
                    ),
                    properties=
                    GeometryGroupPropertiesSuperstructureToSubstructureConnections(
                        **{
                            "Structural Component Type":
                                (
                                    SuperstructureToSubstructureConnectionsStructureComponentGroupType()
                                ),

                            "Geometry Group Properties":
                                (
                                    SuperstructureToSubstructureConnectionsGroupProperties(
                                        isUser=isUser,
                                        group_parameters=
                                        SuperstructureToSubstructureConnectionsGroupPropertiesParameters(
                                            **{
                                                "Support Index":
                                                    (
                                                        SupportIndexParameter(
                                                            provided_value=
                                                                support_index,
                                                            isUser=isUser,
                                                        )
                                                    ),

                                                "Bearing Configuration Details":
                                                    configuration_details,
                                            }
                                        )
                                    )
                                ),
                        }
                    )
                )
            ]
        )
    
if __name__ == "__main__":

    singular_connection = (
        GeometryGroupSuperstructureToSubstructureConnections.create(
            support_index=1,
            bearing_configuration_type=
            BearingConfigurationTypeParaModel.SINGULAR,
        )
    )

    print(
        singular_connection.model_dump_json(
            indent=2,
            by_alias=True,
            exclude_none=True,
        )
    )

    multiple_uniform_connection = (
        GeometryGroupSuperstructureToSubstructureConnections.create(
            support_index=2,
            bearing_configuration_type=
            BearingConfigurationTypeParaModel.MULTIPLE,

            number_of_bearings=4,

            spacing_type=
            SpacingTypeParaModel.UNIFORM,

            bearing_spacing=[
                3.0,
                3.0,
                3.0,
            ],

            spacing_unit="m",
        )
    )

    print(
        multiple_uniform_connection.model_dump_json(
            indent=2,
            by_alias=True,
            exclude_none=True,
        )
    )

    multiple_custom_connection = (
        GeometryGroupSuperstructureToSubstructureConnections.create(
            support_index=3,
            bearing_configuration_type=
            BearingConfigurationTypeParaModel.MULTIPLE,

            number_of_bearings=4,

            spacing_type=
            SpacingTypeParaModel.VARIABLE,

            bearing_spacing=[
                2.5,
                3.0,
                4.0,
            ],

            spacing_unit="m",
        )
    )

    print(
        multiple_custom_connection.model_dump_json(
            indent=2,
            by_alias=True,
            exclude_none=True,
        )
    )