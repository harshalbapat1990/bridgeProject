from typing import Annotated, ClassVar, Literal, Union

from pydantic import Field, BaseModel, model_validator

from bda.contracts.paramodel.groups.enums import (
    StructuralComponentTypeParaModel,
    SupportTypeParaModel,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.geometry_group_base import (
    GeometryGroupBase,
    GeometryGroupParameters,
    GeometryGroupProperties,
    GeometryGroupParameterProperties,
    StructureComponentGroupType,
)

from bda.contracts.speckle_contracts.base_objects import (
    UnitlessParameter,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_vertical_members import (
    GeometryGroupVerticalMembersAboveGround,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_horizontal_members import (
    GeometryGroupHorizontalMembersAboveGround,
)

# =============================================================================
# TYPE SPECIFIC PARAMETERS
# =============================================================================


class NumberOfPiersParameter(UnitlessParameter[int]):
    name: Literal["Number Of Piers"] = "Number Of Piers"

    description: Literal[
        "Number of piers in the above ground structure"
    ] = "Number of piers in the above ground structure"

    symbol: None = None

    provided_value: int


class NumberOfWallsParameter(UnitlessParameter[int]):
    name: Literal["Number Of Walls"] = "Number Of Walls"

    description: Literal[
        "Number of walls in the above ground structure"
    ] = "Number of walls in the above ground structure"

    symbol: None = None

    provided_value: int


class SupportType(UnitlessParameter[SupportTypeParaModel]):
    name: Literal["Support Type"] = "Support Type"

    description: Literal[
        "Type of support structure"
    ] = "Type of support structure"

    symbol: None = None

    provided_value: SupportTypeParaModel


class SupportTypeColumnParameter(SupportType):
    provided_value: Literal[
        SupportTypeParaModel.COLUMN_TYPE
    ] = SupportTypeParaModel.COLUMN_TYPE


class SupportTypeSolidParameter(SupportType):
    provided_value: Literal[
        SupportTypeParaModel.SOLID_TYPE
    ] = SupportTypeParaModel.SOLID_TYPE

# =============================================================================
# ABOVE GROUND DETAILS PROPERTY SET
# =============================================================================


class ColumnDetailsProperties(GeometryGroupParameterProperties):
    """Properties specific to column-type above ground structures."""

    name: Literal["Column Type"] = "Column Type"

    description: Literal[
        "Column type properties"
    ] = "Column type properties"

    symbol: None = None

    number_of_piers: NumberOfPiersParameter = Field(
        alias="Number Of Piers"
    )


class AboveGroundDetails_Column(BaseModel):
    support_type: SupportTypeColumnParameter = Field(
        alias="Support Type"
    )

    number_of_piers: NumberOfPiersParameter = Field(
        alias="Number Of Piers"
    )


class AboveGroundDetails_Solid(BaseModel):
    support_type: SupportTypeSolidParameter = Field(
        alias="Support Type"
    )

    number_of_walls: NumberOfWallsParameter = Field(
        alias="Number Of Walls"
    )

AboveGroundDetailsParameters = Union[
    AboveGroundDetails_Column,
    AboveGroundDetails_Solid,
]

class AboveGroundDetailsParameterGroup(
    GeometryGroupParameterProperties
):
    name: Literal["Details"] = "Details"

    description: Literal[
        "Details of the above ground structure"
    ] = "Details of the above ground structure"

    symbol: None = None

    group_parameters: AboveGroundDetailsParameters

    @classmethod
    def create(
        cls,
        support_type: SupportTypeParaModel,
        number_of_piers: int | None = None,
        number_of_walls: int | None = None,
        isUser: bool = True,
    ) -> "AboveGroundDetailsParameterGroup":

        if support_type == SupportTypeParaModel.COLUMN_TYPE:

            if number_of_piers is None:
                raise ValueError(
                    "number_of_piers is required "
                    "for COLUMN support type."
                )

            return cls(
                isUser=isUser,
                group_parameters=
                AboveGroundDetails_Column(
                    **{
                        "Support Type":
                            SupportTypeColumnParameter(isUser=isUser),

                        "Number Of Piers":
                            NumberOfPiersParameter(
                                provided_value=number_of_piers,
                                isUser=isUser,
                            ),
                    }
                )
            )

        if support_type == SupportTypeParaModel.SOLID_TYPE:

            if number_of_walls is None:
                raise ValueError(
                    "number_of_walls is required "
                    "for SOLID support type."
                )

            return cls(
                isUser=isUser,
                group_parameters=
                AboveGroundDetails_Solid(
                    **{
                        "Support Type":
                            SupportTypeSolidParameter(
                                isUser=isUser
                            ),

                        "Number Of Walls":
                            NumberOfWallsParameter(
                                provided_value=number_of_walls,
                                isUser=isUser,
                            ),
                    }
                )
            )

        raise ValueError(
            f"Unsupported support type: {support_type}"
        )


class AboveGroundGroupPropertiesParameters(
    BaseModel
):
    details: AboveGroundDetailsParameterGroup = Field(
        alias="Details"
    )


class AboveGroundGroupProperties(
    GeometryGroupParameterProperties
):
    group_parameters: (
        AboveGroundGroupPropertiesParameters
    )


# =============================================================================
# GROUP TYPE IDENTIFICATION
# =============================================================================


class AboveGroundStructureComponentGroupType(
    StructureComponentGroupType
):
    provided_value: Literal[
        StructuralComponentTypeParaModel.ABOVE_GROUND
    ] = StructuralComponentTypeParaModel.ABOVE_GROUND


# =============================================================================
# COMMON ABOVE GROUND METADATA
# =============================================================================


class GeometryGroupPropertiesAboveGround(
    GeometryGroupProperties
):
    structural_component_type: (
        AboveGroundStructureComponentGroupType
    ) = Field(
        alias="Structural Component Type"
    )

    group_properties: AboveGroundGroupProperties = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersAboveGround(
    GeometryGroupParameters
):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_AboveGround"
    ] = Field(
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_AboveGround",
        frozen=True
    )

    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_AboveGround"
    ] = Field(
        ...,
        frozen=True
    )

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-ABOVE-GROUND$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: GeometryGroupPropertiesAboveGround


# =============================================================================
# ABOVE GROUND GROUP
# =============================================================================


AboveGroundGroupElements = Annotated[
    Union[
        GeometryGroupParametersAboveGround,
        GeometryGroupVerticalMembersAboveGround,
        GeometryGroupHorizontalMembersAboveGround,
    ],
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupAboveGround(
    GeometryGroupBase
):
    speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_AboveGround"
    ] = Field(
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_AboveGround",
        frozen=True
    )

    bda_speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_AboveGround"
    ] = Field(
        ...,
        frozen=True
    )

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-ABOVE-GROUND$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    name: Literal[
        "Above Ground"
    ] = "Above Ground"

    elements: list[AboveGroundGroupElements] = Field(
        default_factory=list,
        json_schema_extra={
            "minItems": 1,
            "allOf": [
                {
                    # Exactly one properties object
                    "contains": {
                        "type": "object",
                        "properties": {
                            "speckle_type": {
                                "const": (
                                    "Objects.Data.DataObject:"
                                    "BDA_Geometry_Group_Properties_AboveGround"
                                )
                            }
                        },
                        "required": ["speckle_type"],
                    },
                    "minContains": 1,
                    "maxContains": 1,
                },
                {
                    # 0..1 Vertical Members
                    "contains": {
                        "type": "object",
                        "properties": {
                            "speckle_type": {
                                "const": (
                                    "Speckle.Core.Models.Collections.Collection:"
                                    "BDA_Geometry_Group_Vertical_Members"
                                )
                            }
                        },
                        "required": ["speckle_type"],
                    },
                    "minContains": 0,
                    "maxContains": 1,
                },
                {
                    # 0..1 Horizontal Members
                    "contains": {
                        "type": "object",
                        "properties": {
                            "speckle_type": {
                                "const": (
                                    "Speckle.Core.Models.Collections.Collection:"
                                    "BDA_Geometry_Group_Horizontal_Members"
                                )
                            }
                        },
                        "required": ["speckle_type"],
                    },
                    "minContains": 0,
                    "maxContains": 1,
                },
            ],
        },
    )

    @model_validator(mode="after")
    def validate_above_ground_elements(self) -> "GeometryGroupAboveGround":

        properties_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_AboveGround"
        )

        vertical_type = (
            "Speckle.Core.Models.Collections.Collection:"
            "BDA_Geometry_Group_Vertical_Members"
        )

        horizontal_type = (
            "Speckle.Core.Models.Collections.Collection:"
            "BDA_Geometry_Group_Horizontal_Members"
        )

        properties_count = sum(
            1
            for element in self.elements
            if element.speckle_type == properties_type
        )

        vertical_count = sum(
            1
            for element in self.elements
            if element.speckle_type == vertical_type
        )

        horizontal_count = sum(
            1
            for element in self.elements
            if element.speckle_type == horizontal_type
        )

        if properties_count != 1:
            raise ValueError(
                "AboveGround must contain exactly one "
                "properties object."
            )

        if vertical_count > 1:
            raise ValueError(
                "AboveGround may contain at most one "
                "Vertical Members group."
            )

        if horizontal_count > 1:
            raise ValueError(
                "AboveGround may contain at most one "
                "Horizontal Members group."
            )

        return self

    @classmethod
    def create(
        cls,
        support_type: SupportTypeParaModel,
        vertical_members: (
            GeometryGroupVerticalMembersAboveGround | None
        ) = None,
        horizontal_members: (
            GeometryGroupHorizontalMembersAboveGround | None
        ) = None,
        number_of_piers: int | None = None,
        number_of_walls: int | None = None,
        isUser: bool = True,
        application_id: str = "COL-GEOMGROUP-0001-ABOVE-GROUND",
    ) -> "GeometryGroupAboveGround":

        details = (
            AboveGroundDetailsParameterGroup.create(
                support_type=support_type,
                number_of_piers=number_of_piers,
                number_of_walls=number_of_walls,
                isUser=isUser,
            )
        )

        elements: list[AboveGroundGroupElements] = [
            GeometryGroupParametersAboveGround(
                id=None,
                applicationId=application_id.replace(
                    "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                ),
                bda_speckle_type=(
                    "Objects.Data.DataObject:"
                    "BDA_Geometry_Group_Properties_AboveGround"
                ),
                properties=(
                    GeometryGroupPropertiesAboveGround(
                        **{
                            "Structural Component Type":
                                (
                                    AboveGroundStructureComponentGroupType()
                                ),

                            "Geometry Group Properties":
                                (
                                    AboveGroundGroupProperties(
                                        isUser=isUser,
                                        group_parameters=
                                        AboveGroundGroupPropertiesParameters(
                                            **{
                                                "Details":
                                                    details
                                            }
                                        )
                                    )
                                ),
                        }
                    )
                )
            )
        ]

        if vertical_members is not None:
            elements.append(vertical_members)

        if horizontal_members is not None:
            elements.append(horizontal_members)

        return cls(
            applicationId=application_id,
            bda_speckle_type=(
                "Speckle.Core.Models.Collections.Collection:"
                "BDA_Geometry_Group_AboveGround"
            ),
            elements=elements,
        )

if __name__ == "__main__":
    from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_pier import (
        GeometryGroupPier,
    )

    from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_crossbeam import (
        GeometryGroupCrossbeam,
    )

    from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_vertical_members import (
        GeometryGroupVerticalMembersAboveGround,
    )

    from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_horizontal_members import (
        GeometryGroupHorizontalMembersAboveGround,
    )

    # -------------------------------------------------------------------------
    # Crossbeams
    # -------------------------------------------------------------------------

    crossbeam_1 = GeometryGroupCrossbeam.create(
        material_id="Steel",
        section_id="CB1",
        element_length=12.0,
        tapers=[
            (
                0.0,
                12.0,
                "CB_SEC_1",
            ),
        ],
        application_id="COL-GEOMGROUP-0001-CROSSBEAM",
    )

    horizontal_members = (
        GeometryGroupHorizontalMembersAboveGround.create(
            crossbeam=crossbeam_1,
            application_id="COL-GEOMGROUP-0001-HORIZONTAL-MEMBERS",
        )
    )

    # -------------------------------------------------------------------------
    # Vertical Members
    # -------------------------------------------------------------------------

    pier_1 = GeometryGroupPier.create(
        material_id="Concrete",
        section_id="Pier_1",
        transverse_offset=0.0,
        application_id="COL-GEOMGROUP-0001-PIER",
    )

    vertical_members = (
        GeometryGroupVerticalMembersAboveGround.create(
            piers=[
                pier_1,
            ],
            application_id="COL-GEOMGROUP-0001-VERTICAL-MEMBERS",
        )
    )

    # -------------------------------------------------------------------------
    # Above Ground
    # -------------------------------------------------------------------------

    above_ground = (
        GeometryGroupAboveGround.create(
            support_type=
            SupportTypeParaModel.COLUMN_TYPE,

            number_of_piers=1,

            vertical_members=
            vertical_members,

            horizontal_members=
            horizontal_members,

            isUser=True,
        )
    )

    print(
        above_ground.model_dump_json(
            indent=4,
        )
    )