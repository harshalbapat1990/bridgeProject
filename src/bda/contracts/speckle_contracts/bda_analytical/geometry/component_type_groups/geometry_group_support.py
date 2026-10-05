from enum import Enum
from typing import Annotated, ClassVar, Literal, Union

from pydantic import Field, BaseModel, model_validator

from bda.contracts.paramodel.groups.enums import (
    StructuralComponentTypeParaModel,
    ElementOrientationParaModel,
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

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_above_ground import (
    GeometryGroupAboveGround,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_below_ground import (
    GeometryGroupBelowGround,
)
from bda.contracts.speckle_contracts.unit_parameters import (
    AngleParameter,
    LengthParameter,
)
from bda.contracts.speckle_contracts.bda_analytical.common_parameters import SupportIndexParameter
# =============================================================================
# TYPE SPECIFIC PARAMETERS
# =============================================================================


class SkewAngleParameter(AngleParameter):
    name: Literal["Skew Angle"] = "Skew Angle"

    description: Literal[
        "Skew angle of the support"
    ] = "Skew angle of the support"

    symbol: None = None

    provided_unit: Literal["deg", "rad"]

    base_unit: Literal["deg"] = "deg"


class BearingUndersideLevelParameter(LengthParameter):
    name: Literal[
        "Bearing Underside Level"
    ] = "Bearing Underside Level"

    description: Literal[
        "Bearing underside level of the support"
    ] = "Bearing underside level of the support"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


class ElementOrientationParameter(
    UnitlessParameter[ElementOrientationParaModel]
):
    name: Literal["Element Orientation"] = "Element Orientation"

    description: Literal[
        "Orientation of the support element"
    ] = "Orientation of the support element"

    symbol: None = None

    provided_value: ElementOrientationParaModel


# =============================================================================
# SUPPORT PROPERTY SET
# =============================================================================

class SupportGroupPropertiesParameters(
    BaseModel
):
    support_index: SupportIndexParameter = Field(
        alias="Support Index"
    )

    skew_angle: SkewAngleParameter = Field(
        alias="Skew Angle"
    )

    bearing_underside_level: (
        BearingUndersideLevelParameter
    ) = Field(
        alias="Bearing Underside Level"
    )

    orientation: ElementOrientationParameter = Field(
        alias="Element Orientation"
    )

class SupportGroupProperties(
    GeometryGroupParameterProperties
):
    group_parameters: (
        SupportGroupPropertiesParameters
    )

    @classmethod
    def create(
        cls,
        support_index: int,
        skew_angle: float,
        bearing_underside_level: float,
        orientation: ElementOrientationParaModel,
        skew_angle_unit: Literal["deg", "rad"] = "deg",
        bearing_underside_level_unit: Literal["m", "ft"] = "m",
        isUser: bool = True,
    ) -> "SupportGroupProperties":

        return cls(
            isUser=isUser,
            group_parameters=(
                SupportGroupPropertiesParameters(
                    **{
                        "Support Index":
                            SupportIndexParameter(
                                isUser=isUser,
                                provided_value=support_index,
                            ),

                        "Skew Angle":
                            SkewAngleParameter(
                                isUser=isUser,
                                provided_value=skew_angle,
                                provided_unit=skew_angle_unit,
                                base_value=skew_angle,
                            ),

                        "Bearing Underside Level":
                            BearingUndersideLevelParameter(
                                isUser=isUser,
                                provided_value=(
                                    bearing_underside_level
                                ),
                                provided_unit=(
                                    bearing_underside_level_unit
                                ),
                                base_value=(
                                    bearing_underside_level
                                ),
                            ),

                        "Element Orientation":
                            ElementOrientationParameter(
                                isUser=isUser,
                                provided_value=orientation,
                            ),
                    }
                )
            ),
        )


# =============================================================================
# GROUP TYPE IDENTIFICATION
# =============================================================================


class SupportStructureComponentGroupType(
    StructureComponentGroupType
):
    provided_value: Literal[
        StructuralComponentTypeParaModel.SUPPORT
    ] = StructuralComponentTypeParaModel.SUPPORT


# =============================================================================
# COMMON SUPPORT METADATA
# =============================================================================


class GeometryGroupPropertiesSupport(
    GeometryGroupProperties
):
    structural_component_type: (
        SupportStructureComponentGroupType
    ) = Field(
        alias="Structural Component Type"
    )

    group_properties: SupportGroupProperties = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersSupport(
    GeometryGroupParameters
):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Support"
    ] = Field(
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Support",
        frozen=True
    )

    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Geometry_Group_Properties_Support"
    ] = Field(
        ...,
        frozen=True
    )

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-SUPPORT$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: GeometryGroupPropertiesSupport


# =============================================================================
# SUPPORT GROUP
# =============================================================================


SupportGroupElements = Annotated[
    Union[
        GeometryGroupParametersSupport,
        GeometryGroupAboveGround,
        GeometryGroupBelowGround
    ],
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupSupport(
    GeometryGroupBase
):
    speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection:"
        "BDA_Geometry_Group_Support"
    ] = Field(
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Support",
        frozen=True
    )

    bda_speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection:BDA_Geometry_Group_Support"
    ] = Field(
        ...,
        frozen=True
    )

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-SUPPORT$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    elements: list[SupportGroupElements] = Field(
        default_factory=list,
        json_schema_extra={
            "minItems": 1,
            "allOf": [
                {
                    # Exactly one support properties object
                    "contains": {
                        "type": "object",
                        "properties": {
                            "speckle_type": {
                                "const": (
                                    "Objects.Data.DataObject:"
                                    "BDA_Geometry_Group_Properties_Support"
                                )
                            }
                        },
                        "required": ["speckle_type"],
                    },
                    "minContains": 1,
                    "maxContains": 1,
                },
                {
                    # 0..1 Above Ground
                    "contains": {
                        "type": "object",
                        "properties": {
                            "speckle_type": {
                                "const": (
                                    "Speckle.Core.Models.Collections.Collection:"
                                    "BDA_Geometry_Group_AboveGround"
                                )
                            }
                        },
                        "required": ["speckle_type"],
                    },
                    "minContains": 0,
                    "maxContains": 1,
                },
                {
                    # 0..1 Below Ground
                    "contains": {
                        "type": "object",
                        "properties": {
                            "speckle_type": {
                                "const": (
                                    "Speckle.Core.Models.Collections.Collection:"
                                    "BDA_Geometry_Group_BelowGround"
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
    def validate_support_elements(self) -> "GeometryGroupSupport":

        properties_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_Support"
        )

        above_ground_type = (
            "Speckle.Core.Models.Collections.Collection:"
            "BDA_Geometry_Group_AboveGround"
        )

        below_ground_type = (
            "Speckle.Core.Models.Collections.Collection:"
            "BDA_Geometry_Group_BelowGround"
        )

        properties_count = sum(
            1
            for element in self.elements
            if element.speckle_type == properties_type
        )

        above_ground_count = sum(
            1
            for element in self.elements
            if element.speckle_type == above_ground_type
        )

        below_ground_count = sum(
            1
            for element in self.elements
            if element.speckle_type == below_ground_type
        )

        if properties_count != 1:
            raise ValueError(
                "GeometryGroupSupport.elements must contain "
                "exactly one Support properties object."
            )

        if above_ground_count > 1:
            raise ValueError(
                "GeometryGroupSupport.elements may contain "
                "at most one Above Ground group."
            )

        if below_ground_count > 1:
            raise ValueError(
                "GeometryGroupSupport.elements may contain "
                "at most one Below Ground group."
            )

        return self

    @classmethod
    def create(
        cls,
        support_index: int,
        skew_angle: float,
        bearing_underside_level: float,
        orientation: ElementOrientationParaModel,
        above_ground: GeometryGroupAboveGround | None = None,
        below_ground: GeometryGroupBelowGround | None = None,
        application_id: str = "COL-GEOMGROUP-0001-SUPPORT",
        name: str | None = None,
        skew_angle_unit: Literal["deg", "rad"] = "deg",
        bearing_underside_level_unit: Literal["m", "ft"] = "m",
        isUser: bool = True,
    ) -> "GeometryGroupSupport":

        elements: list[SupportGroupElements] = [
            GeometryGroupParametersSupport(
                **{
                    "id": None,
                    "applicationId": application_id.replace(
                        "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                    ),
                    "bda_speckle_type": (
                        "Objects.Data.DataObject:"
                        "BDA_Geometry_Group_Properties_Support"
                    ),
                    "properties": (
                        GeometryGroupPropertiesSupport(
                            **{
                                "Structural Component Type":
                                    SupportStructureComponentGroupType(),

                                "Geometry Group Properties":
                                    SupportGroupProperties.create(
                                        support_index=support_index,
                                        skew_angle=skew_angle,
                                        bearing_underside_level=(
                                            bearing_underside_level
                                        ),
                                        orientation=orientation,
                                        skew_angle_unit=(
                                            skew_angle_unit
                                        ),
                                        bearing_underside_level_unit=(
                                            bearing_underside_level_unit
                                        ),
                                        isUser=isUser,
                                    ),
                            }
                        )
                    ),
                }
            )
        ]

        if above_ground is not None:
            elements.append(above_ground)

        if below_ground is not None:
            elements.append(below_ground)

        return cls(
            id=None,
            applicationId=application_id,
            name=name if name is not None else f"Support_{support_index}",
            bda_speckle_type=(
                "Speckle.Core.Models.Collections.Collection:"
                "BDA_Geometry_Group_Support"
            ),
            elements=elements,
        )


if __name__ == "__main__":

    from bda.contracts.paramodel.groups.enums import (
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

    # -------------------------------------------------------------------------
    # Vertical Members
    # -------------------------------------------------------------------------

    pier = GeometryGroupPier.create(
        material_id="Concrete",
        section_id="Pier_1",
        transverse_offset=0.0,
        application_id="COL-GEOMGROUP-0001-PIER",
    )

    vertical_members = (
        GeometryGroupVerticalMembersAboveGround.create(
            piers=[pier],
            application_id="COL-GEOMGROUP-0001-VERTICAL-MEMBERS",
        )
    )

    # -------------------------------------------------------------------------
    # Horizontal Members
    # -------------------------------------------------------------------------

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

    horizontal_members = (
        GeometryGroupHorizontalMembersAboveGround.create(
            crossbeam=crossbeam,
            application_id="COL-GEOMGROUP-0001-HORIZONTAL-MEMBERS",
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

    # -------------------------------------------------------------------------
    # Support
    # -------------------------------------------------------------------------

    support = (
        GeometryGroupSupport.create(
            support_index=1,
            skew_angle=15.0,
            bearing_underside_level=12.5,
            orientation=
            ElementOrientationParaModel.ORTHOGONAL,
            above_ground=above_ground,
            application_id="COL-GEOMGROUP-0001-SUPPORT",
        )
    )

    print(
        support.model_dump_json(
            indent=4,
            by_alias=True,
            exclude_none=True,
        )
    )