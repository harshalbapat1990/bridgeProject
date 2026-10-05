from typing import Annotated, ClassVar, Literal, Union

from pydantic import BaseModel, Field, model_validator

from bda.contracts.paramodel.groups.enums import (
    StructuralComponentTypeParaModel,
    ElementOrientationParaModel
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.geometry_group_base import (
    GeometryGroupBase,
    GeometryGroupParameters,
    GeometryGroupProperties,
    GeometryGroupParameterProperties,
    StructureComponentGroupType,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_support import GeometryGroupSupport

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_linkage import (
    GeometryGroupLinkage,
)
# =============================================================================
# GROUP TYPE IDENTIFICATION
# =============================================================================


class SubstructureStructureComponentGroupType(
    StructureComponentGroupType
):
    provided_value: Literal[
        StructuralComponentTypeParaModel.SUBSTRUCTURE
    ] = StructuralComponentTypeParaModel.SUBSTRUCTURE


# =============================================================================
# SUBSTRUCTURE PROPERTY SET
# =============================================================================


class SubstructureGroupPropertiesParameters(BaseModel):
    pass


class SubstructureGroupProperties(GeometryGroupParameterProperties):
    group_parameters: SubstructureGroupPropertiesParameters

    @classmethod
    def create(cls, isUser: bool = True) -> "SubstructureGroupProperties":
        return cls(
            isUser=isUser,
            group_parameters=SubstructureGroupPropertiesParameters(),
        )


# =============================================================================
# COMMON SUBSTRUCTURE METADATA
# =============================================================================


class GeometryGroupPropertiesSubstructure(GeometryGroupProperties):
    structural_component_type: (
        SubstructureStructureComponentGroupType
    ) = Field(
        alias="Structural Component Type"
    )

    group_properties: SubstructureGroupProperties = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersSubstructure(
    GeometryGroupParameters
):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Substructure"
    ] = "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Substructure"

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-SUBSTRUCTURE$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: GeometryGroupPropertiesSubstructure


# =============================================================================
# SUBSTRUCTURE GROUP
# =============================================================================


SubstructureGroupElements = Annotated[
    Union[
        GeometryGroupParametersSubstructure,
        GeometryGroupSupport,
    ],
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupSubstructure(
    GeometryGroupBase
):
    bda_speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Substructure"
    ] = "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Substructure"

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-SUBSTRUCTURE$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    name: Literal[
        "Substructure"
    ] = "Substructure"

    elements: list[SubstructureGroupElements] = Field(
        default_factory=list,
        json_schema_extra={
            "minItems": 1,
            "allOf": [
                {
                    # Exactly one substructure properties object
                    "contains": {
                        "type": "object",
                        "properties": {
                            "bda_speckle_type": {
                                "const": (
                                    "Objects.Data.DataObject:"
                                    "BDA_Geometry_Group_Properties_"
                                    "Substructure"
                                )
                            }
                        },
                        "required": ["bda_speckle_type"],
                    },
                    "minContains": 1,
                    "maxContains": 1,
                },
                {
                    # Optional supports (0..N)
                    "contains": {
                        "type": "object",
                        "properties": {
                            "bda_speckle_type": {
                                "const": (
                                    "Speckle.Core.Models.Collections.Collection:"
                                    "BDA_Geometry_Group_Support"
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
    def validate_substructure_elements(self) -> "GeometryGroupSubstructure":

        properties_speckle_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_Substructure"
        )

        properties_count = sum(
            1
            for element in self.elements
            if element.bda_speckle_type
            == properties_speckle_type
        )

        if properties_count != 1:
            raise ValueError(
                "GeometryGroupSubstructure.elements must contain "
                "exactly one "
                f"{properties_speckle_type} object. "
                f"Found {properties_count}."
            )

        return self

    @classmethod
    def create(
        cls,
        supports: list[GeometryGroupSupport] | None = None,
        application_id: str = "COL-GEOMGROUP-0001-SUBSTRUCTURE",
        isUser: bool = True,
    ) -> "GeometryGroupSubstructure":

        return cls(
            id=None,
            applicationId=application_id,
            name="Substructure",
            elements=[
                GeometryGroupParametersSubstructure(
                    **{
                        "id": None,
                        "applicationId": application_id.replace(
                            "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                        ),
                        "properties": (
                            GeometryGroupPropertiesSubstructure(
                                **{
                                    "Structural Component Type":
                                        SubstructureStructureComponentGroupType(),

                                    "Geometry Group Properties":
                                        SubstructureGroupProperties.create(
                                            isUser=isUser,
                                        ),
                                }
                            )
                        ),
                    }
                ),
                *(supports or []),
            ],
        )


if __name__ == "__main__":

    from bda.contracts.paramodel.groups.enums import (
        ElementOrientationParaModel,
        SupportTypeParaModel,
    )

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

    from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_above_ground import (
        GeometryGroupAboveGround,
    )

    from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_support import (
        GeometryGroupSupport,
    )

    # ---------------------------------------------------------------------
    # Pier
    # ---------------------------------------------------------------------

    pier = GeometryGroupPier.create(
        material_id="Concrete",
        section_id="PIER_1",
        transverse_offset=0.0,
        application_id="COL-GEOMGROUP-0001-PIER",
    )

    # ---------------------------------------------------------------------
    # Vertical Members
    # ---------------------------------------------------------------------

    vertical_members = (
        GeometryGroupVerticalMembersAboveGround.create(
            piers=[pier],
            application_id="COL-GEOMGROUP-0001-VERTICAL-MEMBERS",
        )
    )

    # ---------------------------------------------------------------------
    # Crossbeam
    # ---------------------------------------------------------------------

    crossbeam = GeometryGroupCrossbeam.create(
        material_id="Steel",
        section_id="CB_1",
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

    # ---------------------------------------------------------------------
    # Horizontal Members
    # ---------------------------------------------------------------------

    horizontal_members = (
        GeometryGroupHorizontalMembersAboveGround.create(
            crossbeam=crossbeam,
            application_id="COL-GEOMGROUP-0001-HORIZONTAL-MEMBERS",
        )
    )

    # ---------------------------------------------------------------------
    # Above Ground
    # ---------------------------------------------------------------------

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

    # ---------------------------------------------------------------------
    # Support
    # ---------------------------------------------------------------------

    support = (
        GeometryGroupSupport.create(
            support_index=1,
            skew_angle=15.0,
            bearing_underside_level=12.5,
            orientation=
            ElementOrientationParaModel.ORTHOGONAL,

            above_ground=
            above_ground,

            application_id="COL-GEOMGROUP-0001-SUPPORT",
        )
    )

    # ---------------------------------------------------------------------
    # Substructure
    # ---------------------------------------------------------------------

    substructure = (
        GeometryGroupSubstructure.create(
            supports=[
                support,
            ],
            application_id="COL-GEOMGROUP-0001-SUBSTRUCTURE",
        )
    )

    print(
        substructure.model_dump_json(
            indent=4,
            by_alias=True,
            exclude_none=True,
        )
    )