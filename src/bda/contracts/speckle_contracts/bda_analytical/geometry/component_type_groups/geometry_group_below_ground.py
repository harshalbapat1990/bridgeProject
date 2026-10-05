from typing import Annotated, ClassVar, Literal, Union

from pydantic import BaseModel, Field, model_validator

from bda.contracts.paramodel.groups.enums import (
    StructuralComponentTypeParaModel,
    FoundationTypeParaModel,
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


from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_pile import (
    GeometryGroupPile,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_pile_cap import (
    GeometryGroupPileCap,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_vertical_members import (
    GeometryGroupVerticalMembersBelowGround,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_horizontal_members import (
    GeometryGroupHorizontalMembersBelowGround,
)

# =============================================================================
# TYPE SPECIFIC PARAMETERS
# =============================================================================


class NumberOfPilesParameter(
    UnitlessParameter[int]
):
    name: Literal[
        "Number Of Piles"
    ] = "Number Of Piles"

    description: Literal[
        "Number of piles in the foundation"
    ] = "Number of piles in the foundation"

    symbol: None = None

    provided_value: int


class FoundationType(
    UnitlessParameter[
        FoundationTypeParaModel
    ]
):
    name: Literal[
        "Foundation Type"
    ] = "Foundation Type"

    description: Literal[
        "Type of foundation"
    ] = "Type of foundation"

    symbol: None = None

    provided_value: FoundationTypeParaModel


class FoundationTypeDeepParameter(
    FoundationType
):
    provided_value: Literal[
        FoundationTypeParaModel.DEEP
    ] = FoundationTypeParaModel.DEEP


class FoundationTypeShallowParameter(
    FoundationType
):
    provided_value: Literal[
        FoundationTypeParaModel.SHALLOW
    ] = FoundationTypeParaModel.SHALLOW


# =============================================================================
# FOUNDATION DETAILS
# =============================================================================


class FoundationDetails_Deep(
    BaseModel
):
    foundation_type: (
        FoundationTypeDeepParameter
    ) = Field(
        alias="Foundation Type"
    )

    number_of_piles: (
        NumberOfPilesParameter
    ) = Field(
        alias="Number Of Piles"
    )


class FoundationDetails_Shallow(
    BaseModel
):
    foundation_type: (
        FoundationTypeShallowParameter
    ) = Field(
        alias="Foundation Type"
    )


FoundationDetailsParameters = Union[
    FoundationDetails_Deep,
    FoundationDetails_Shallow,
]


class FoundationDetailsParameterGroup(
    GeometryGroupParameterProperties
):
    name: Literal[
        "Foundation Details"
    ] = "Foundation Details"

    description: Literal[
        "Foundation details"
    ] = "Foundation details"

    symbol: None = None

    group_parameters: (
        FoundationDetailsParameters
    )

    @classmethod
    def create(
        cls,
        foundation_type: FoundationTypeParaModel,
        number_of_piles: int | None = None,
        isUser: bool = True,
    ) -> "FoundationDetailsParameterGroup":

        if (
            foundation_type
            == FoundationTypeParaModel.DEEP
        ):

            if number_of_piles is None:
                raise ValueError(
                    "number_of_piles is required "
                    "for DEEP foundation type."
                )

            return cls(
                isUser=isUser,
                group_parameters=
                FoundationDetails_Deep(
                    **{
                        "Foundation Type":
                            FoundationTypeDeepParameter(
                                isUser=isUser
                            ),

                        "Number Of Piles":
                            NumberOfPilesParameter(
                                provided_value=
                                    number_of_piles,
                                isUser=isUser,
                            ),
                    }
                )
            )

        if (
            foundation_type
            == FoundationTypeParaModel.SHALLOW
        ):

            return cls(
                isUser=isUser,
                group_parameters=
                FoundationDetails_Shallow(
                    **{
                        "Foundation Type":
                            FoundationTypeShallowParameter(
                                isUser=isUser
                            ),
                    }
                )
            )

        raise ValueError(
            f"Unsupported foundation type: "
            f"{foundation_type}"
        )


# =============================================================================
# BELOW GROUND PROPERTY SET
# =============================================================================


class BelowGroundGroupPropertiesParameters(
    BaseModel
):
    foundation_details: (
        FoundationDetailsParameterGroup
    ) = Field(
        alias="Foundation Details"
    )


class BelowGroundGroupProperties(
    GeometryGroupParameterProperties
):
    group_parameters: (
        BelowGroundGroupPropertiesParameters
    )


# =============================================================================
# GROUP TYPE IDENTIFICATION
# =============================================================================


class BelowGroundStructureComponentGroupType(
    StructureComponentGroupType
):
    provided_value: Literal[
        StructuralComponentTypeParaModel.BELOW_GROUND
    ] = (
        StructuralComponentTypeParaModel.BELOW_GROUND
    )


# =============================================================================
# COMMON BELOW GROUND METADATA
# =============================================================================


class GeometryGroupPropertiesBelowGround(
    GeometryGroupProperties
):
    structural_component_type: (
        BelowGroundStructureComponentGroupType
    ) = Field(
        alias="Structural Component Type"
    )

    group_properties: (
        BelowGroundGroupProperties
    ) = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersBelowGround(
    GeometryGroupParameters
):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    speckle_type: Literal[
        "Objects.Data.DataObject:"
        "BDA_Geometry_Group_Properties_BelowGround"
    ] = Field(
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_BelowGround",
        frozen=True
    )

    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_BelowGround"
    ] = Field(
        ...,
        frozen=True
    )

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-BELOW-GROUND$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: (
        GeometryGroupPropertiesBelowGround
    )


# =============================================================================
# BELOW GROUND GROUP
# =============================================================================


BelowGroundGroupElements = Annotated[
    Union[
        GeometryGroupParametersBelowGround,
        GeometryGroupVerticalMembersBelowGround,
        GeometryGroupHorizontalMembersBelowGround,
        GeometryGroupPile,
        GeometryGroupPileCap,
    ],
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupBelowGround(
    GeometryGroupBase
):
    speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection:"
        "BDA_Geometry_Group_BelowGround"
    ] = Field(
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_BelowGround",
        frozen=True
    )
    bda_speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_BelowGround"
    ] = Field(
        ...,
        frozen=True
    )

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-BELOW-GROUND$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    name: Literal[
        "Below Ground"
    ] = "Below Ground"

    elements: list[
        BelowGroundGroupElements
    ] = Field(
        default_factory=list,
        json_schema_extra={
            "minItems": 1,
            "allOf": [
                {
                    # Exactly one below ground properties object
                    "contains": {
                        "type": "object",
                        "properties": {
                            "speckle_type": {
                                "const": (
                                    "Objects.Data.DataObject:"
                                    "BDA_Geometry_Group_Properties_BelowGround"
                                )
                            }
                        },
                        "required": ["speckle_type"],
                    },
                    "minContains": 1,
                    "maxContains": 1,
                },
                {
                    # Optional vertical members (0..1)
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
                    # Optional horizontal members (0..1)
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
                {
                    # Optional piles (0..N)
                    "contains": {
                        "type": "object",
                        "properties": {
                            "speckle_type": {
                                "const": (
                                    "Speckle.Core.Models.Collections.Collection:"
                                    "BDA_Geometry_Group_Pile"
                                )
                            }
                        },
                        "required": ["speckle_type"],
                    },
                    "minContains": 0,
                },
                {
                    # Optional pile cap (0..1)
                    "contains": {
                        "type": "object",
                        "properties": {
                            "speckle_type": {
                                "const": (
                                    "Speckle.Core.Models.Collections.Collection:"
                                    "BDA_Geometry_Group_Pile_Cap"
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

    @classmethod
    def create(
        cls,
        foundation_type: FoundationTypeParaModel,
        number_of_piles: int | None = None,
        vertical_members: (
            GeometryGroupVerticalMembersBelowGround | None
        ) = None,
        horizontal_members: (
            GeometryGroupHorizontalMembersBelowGround | None
        ) = None,
        piles: list[GeometryGroupPile] | None = None,
        pile_cap: GeometryGroupPileCap | None = None,
        isUser: bool = True,
        application_id: str = "COL-GEOMGROUP-0001-BELOW-GROUND",
    ) -> "GeometryGroupBelowGround":

        foundation_details = (
            FoundationDetailsParameterGroup.create(
                foundation_type=foundation_type,
                number_of_piles=number_of_piles,
                isUser=isUser,
            )
        )

        elements: list[BelowGroundGroupElements] = [
            GeometryGroupParametersBelowGround(
                id=None,
                applicationId=application_id.replace(
                    "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                ),
                bda_speckle_type=(
                    "Objects.Data.DataObject:"
                    "BDA_Geometry_Group_Properties_BelowGround"
                ),
                properties=
                GeometryGroupPropertiesBelowGround(
                    **{
                        "Structural Component Type":
                            (
                                BelowGroundStructureComponentGroupType()
                            ),

                        "Geometry Group Properties":
                            (
                                BelowGroundGroupProperties(
                                    isUser=isUser,
                                    group_parameters=
                                    BelowGroundGroupPropertiesParameters(
                                        **{
                                            "Foundation Details":
                                                foundation_details
                                        }
                                    )
                                )
                            ),
                    }
                )
            )
        ]

        if vertical_members is not None:
            elements.append(vertical_members)

        if horizontal_members is not None:
            elements.append(horizontal_members)

        elements.extend(piles or [])

        if pile_cap is not None:
            elements.append(pile_cap)

        return cls(
            id=None,
            applicationId=application_id,
            bda_speckle_type=(
                "Speckle.Core.Models.Collections.Collection:"
                "BDA_Geometry_Group_BelowGround"
            ),
            elements=elements,
        )

    @model_validator(mode="after")
    def validate_below_ground_elements(self) -> "GeometryGroupBelowGround":

        properties_count = sum(
            1
            for element in self.elements
            if element.speckle_type
            == (
                "Objects.Data.DataObject:"
                "BDA_Geometry_Group_Properties_BelowGround"
            )
        )

        pile_cap_count = sum(
            1
            for element in self.elements
            if element.speckle_type
            == (
                "Speckle.Core.Models.Collections.Collection:"
                "BDA_Geometry_Group_Pile_Cap"
            )
        )

        vertical_members_count = sum(
            1
            for element in self.elements
            if element.speckle_type
            == (
                "Speckle.Core.Models.Collections.Collection:"
                "BDA_Geometry_Group_Vertical_Members"
            )
        )

        horizontal_members_count = sum(
            1
            for element in self.elements
            if element.speckle_type
            == (
                "Speckle.Core.Models.Collections.Collection:"
                "BDA_Geometry_Group_Horizontal_Members"
            )
        )

        if properties_count != 1:
            raise ValueError(
                "GeometryGroupBelowGround must contain "
                "exactly one BelowGround properties object."
            )

        if pile_cap_count > 1:
            raise ValueError(
                "GeometryGroupBelowGround can contain "
                "at most one Pile Cap."
            )

        if vertical_members_count > 1:
            raise ValueError(
                "GeometryGroupBelowGround can contain "
                "at most one Vertical Members group."
            )

        if horizontal_members_count > 1:
            raise ValueError(
                "GeometryGroupBelowGround can contain "
                "at most one Horizontal Members group."
            )

        return self


if __name__ == "__main__":

    pile_1 = GeometryGroupPile.create(
        material_id="Concrete",
        section_id="PILE_1",
        application_id="COL-GEOMGROUP-0001-PILE",
    )

    pile_2 = GeometryGroupPile.create(
        material_id="Concrete",
        section_id="PILE_2",
        application_id="COL-GEOMGROUP-0002-PILE",
    )

    pile_cap = GeometryGroupPileCap.create(
        material_id="Concrete",
        section_id="PILE_CAP_1",
        application_id="COL-GEOMGROUP-0001-PILE-CAP",
    )

    examples = {
        "properties_only":
            GeometryGroupBelowGround.create(
                foundation_type=
                FoundationTypeParaModel.SHALLOW,
            ),

        "piles_only":
            GeometryGroupBelowGround.create(
                foundation_type=
                FoundationTypeParaModel.DEEP,
                number_of_piles=2,
                piles=[
                    pile_1,
                    pile_2,
                ],
            ),

        "pile_cap_only":
            GeometryGroupBelowGround.create(
                foundation_type=
                FoundationTypeParaModel.SHALLOW,
                pile_cap=pile_cap,
            ),

        "piles_and_pile_cap":
            GeometryGroupBelowGround.create(
                foundation_type=
                FoundationTypeParaModel.DEEP,
                number_of_piles=2,
                piles=[
                    pile_1,
                    pile_2,
                ],
                pile_cap=pile_cap,
            ),
    }

    for name, obj in examples.items():
        print(f"\n=== {name.upper()} ===")

        print(
            obj.model_dump_json(
                indent=2,
                by_alias=True,
                exclude_none=True,
            )
        )