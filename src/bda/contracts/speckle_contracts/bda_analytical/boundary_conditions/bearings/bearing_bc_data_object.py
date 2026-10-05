from __future__ import annotations

from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes

from typing import Annotated, Literal, ClassVar, TypeAlias

from pydantic import BaseModel, Field, StringConstraints, TypeAdapter

from bda.contracts.speckle_contracts.base_objects import (
    BridgeDataObject,
    BridgeDataObjectProperties,
    ParameterGroup,
)

from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.bearings.bearing_parameters import (
    SupportIndexParameter,
    BearingIndexParameter,
    GirderIndexParameter,
    BearingOrientationParameter,
    BearingConfigurationTypeParameter,
    BearingNodeSpringStiffnessParameterGroup,
    BearingBCDefinition,
)

from bda.contracts.paramodel.groups.enums import (
    BearingConfigurationTypeParaModel,
    ElementOrientationParaModel,
)
from bda.contracts.paramodel.foundations.enums import DofTypeEnumParaModel

from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.spring_parameters import (
    BoundaryConditionSpringParameterGroup,
)


BearingGroupKey = Annotated[
    str,
    StringConstraints(pattern=r"^bearing-\d{4}$"),
]

class BearingSpringDefinitionsGroup(
    ParameterGroup
):
    name: Literal[
        "Bearing Spring Definitions"
    ] = "Bearing Spring Definitions"

    group_parameters: dict[
        BearingGroupKey,
        BearingNodeSpringStiffnessParameterGroup
    ]


class BearingSpringDefinitionsGroup_Singular(
    ParameterGroup
):
    name: Literal[
        "Bearing Spring Definitions"
    ] = "Bearing Spring Definitions"

    group_parameters: dict[
        BearingGroupKey,
        BearingNodeSpringStiffnessParameterGroup
    ] = Field(
        min_length=1,
        max_length=1,
    )


class BearingSpringDefinitionsGroup_Multiple(
    ParameterGroup
):
    name: Literal[
        "Bearing Spring Definitions"
    ] = "Bearing Spring Definitions"

    group_parameters: dict[
        BearingGroupKey,
        BearingNodeSpringStiffnessParameterGroup
    ] = Field(
        min_length=2
    )

class BearingConfigurationTypeParameter_Singular(
    BearingConfigurationTypeParameter
):
    provided_value: Literal[
        BearingConfigurationTypeParaModel.SINGULAR
    ] = BearingConfigurationTypeParaModel.SINGULAR


class BearingConfigurationTypeParameter_Multiple(
    BearingConfigurationTypeParameter
):
    provided_value: Literal[
        BearingConfigurationTypeParaModel.MULTIPLE
    ] = BearingConfigurationTypeParaModel.MULTIPLE


class BearingBCParameters_Singular(BaseModel):
    model_config = {
        "populate_by_name": True
    }

    bearing_configuration_type: BearingConfigurationTypeParameter_Singular = Field(
        alias="Bearing Configuration Type"
    )

    spring_definitions: BearingSpringDefinitionsGroup_Singular = Field(
        alias="Bearing Spring Definitions"
    )


class BearingBCParameters_Multiple(BaseModel):
    model_config = {
        "populate_by_name": True
    }

    bearing_configuration_type: BearingConfigurationTypeParameter_Multiple = Field(
        alias="Bearing Configuration Type"
    )

    spring_definitions: BearingSpringDefinitionsGroup_Multiple = Field(
        alias="Bearing Spring Definitions"
    )


BearingBCParameters: TypeAlias = (
    BearingBCParameters_Singular | BearingBCParameters_Multiple
)


class BearingBCParameterGroup(
    ParameterGroup
):
    name: Literal[
        "Bearing Boundary Condition Parameters"
    ] = (
        "Bearing Boundary Condition Parameters"
    )

    group_parameters: BearingBCParameters


class BearingBCDataObjectProperties(
    BridgeDataObjectProperties
):
    support_index: SupportIndexParameter = Field(
        alias="Support Index"
    )
    
    girder_index: GirderIndexParameter = Field(
        alias="Girder Index"
    )

    bearing_boundary_condition_parameters: (
        BearingBCParameterGroup
    ) = Field(
        alias="Bearing Boundary Condition Parameters"
    )


class BearingBCDataObject(
    BridgeDataObject
):
    APPLICATION_ID_PATTERN: ClassVar[str] = (r"^BC-BEARING-\d{4}$")
    applicationId: str = Field(
        pattern=APPLICATION_ID_PATTERN,
    )
    name: str

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_BEARING_BOUNDARY_CONDITION
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_BEARING_BOUNDARY_CONDITION.value, frozen=True)

    properties: (
        BearingBCDataObjectProperties
    )

    @staticmethod
    def _dof(
        dof_type: str,
        stiffness=None,
    ):
        return {
            "DOF Type": {
                "isUser": True,
                "provided_value": dof_type,
            },
            "Stiffness": stiffness,
        }

    @staticmethod
    def _build_single_spring_definition(
        bearing_index: int,
        orientation: ElementOrientationParaModel,
        spring_definitions,
    ) -> dict[str, BearingNodeSpringStiffnessParameterGroup]:
        if isinstance(spring_definitions, BoundaryConditionSpringParameterGroup):
            stiffness_definition = spring_definitions
        elif isinstance(spring_definitions, dict) and all(
            key in {"SDX", "SDY", "SDZ", "SRX", "SRY", "SRZ"}
            for key in spring_definitions
        ):
            axis_values: dict[str, tuple[DofTypeEnumParaModel, float | None]] = {}

            for axis in ("SDX", "SDY", "SDZ", "SRX", "SRY", "SRZ"):
                definition = spring_definitions[axis]
                if not isinstance(definition, dict):
                    raise TypeError(
                        f"Spring definition for axis '{axis}' must be a dict."
                    )

                dof_type = DofTypeEnumParaModel(
                    definition["DOF Type"]["provided_value"]
                )
                stiffness = definition.get("Stiffness")
                stiffness_value = (
                    None if stiffness is None else stiffness.get("provided_value")
                )
                axis_values[axis] = (dof_type, stiffness_value)

            stiffness_definition = BoundaryConditionSpringParameterGroup.create(
                sdx_dof_type=axis_values["SDX"][0],
                sdx_stiffness=axis_values["SDX"][1],
                sdy_dof_type=axis_values["SDY"][0],
                sdy_stiffness=axis_values["SDY"][1],
                sdz_dof_type=axis_values["SDZ"][0],
                sdz_stiffness=axis_values["SDZ"][1],
                srx_dof_type=axis_values["SRX"][0],
                srx_stiffness=axis_values["SRX"][1],
                sry_dof_type=axis_values["SRY"][0],
                sry_stiffness=axis_values["SRY"][1],
                srz_dof_type=axis_values["SRZ"][0],
                srz_stiffness=axis_values["SRZ"][1],
            )
        else:
            raise TypeError(
                "spring_definitions must be either a BoundaryConditionSpringParameterGroup or a six-axis dictionary."
            )

        return {
            f"bearing-{bearing_index:04d}": BearingNodeSpringStiffnessParameterGroup(
                isUser=True,
                group_parameters=BearingBCDefinition.model_validate(
                    {
                        "Bearing Index": BearingIndexParameter(
                            isUser=True,
                            provided_value=bearing_index,
                        ),
                        "Bearing Stiffness Definition": stiffness_definition,
                        "Orientation": BearingOrientationParameter(
                            isUser=True,
                            provided_value=orientation,
                        ),
                    }
                ),
            )
        }

    @classmethod
    def create_free(
        cls,
        name: str,
        application_id: str,
        support_index: int,
        girder_index: int,
        bearing_index: int,
        configuration_type: BearingConfigurationTypeParaModel,
        orientation: ElementOrientationParaModel,
    ):
        return cls.create(
            name=name,
            application_id=application_id,
            support_index=support_index,
            girder_index=girder_index,
            bearing_index=bearing_index,
            configuration_type=configuration_type,
            orientation=orientation,
            spring_definitions=BoundaryConditionSpringParameterGroup.create(
                sdx_dof_type=DofTypeEnumParaModel.FREE,
                sdy_dof_type=DofTypeEnumParaModel.FREE,
                sdz_dof_type=DofTypeEnumParaModel.FREE,
                srx_dof_type=DofTypeEnumParaModel.FREE,
                sry_dof_type=DofTypeEnumParaModel.FREE,
                srz_dof_type=DofTypeEnumParaModel.FREE,
            ),
        )

    @classmethod
    def create_fixed(
        cls,
        name: str,
        application_id: str,
        support_index: int,
        girder_index: int,
        bearing_index: int,
        configuration_type: BearingConfigurationTypeParaModel,
        orientation: ElementOrientationParaModel,
    ):
        return cls.create(
            name=name,
            application_id=application_id,
            support_index=support_index,
            girder_index=girder_index,
            bearing_index=bearing_index,
            configuration_type=configuration_type,
            orientation=orientation,
            spring_definitions=BoundaryConditionSpringParameterGroup.create(
                sdx_dof_type=DofTypeEnumParaModel.FIXED,
                sdy_dof_type=DofTypeEnumParaModel.FIXED,
                sdz_dof_type=DofTypeEnumParaModel.FIXED,
                srx_dof_type=DofTypeEnumParaModel.FIXED,
                sry_dof_type=DofTypeEnumParaModel.FIXED,
                srz_dof_type=DofTypeEnumParaModel.FIXED,
            ),
        )

    @classmethod
    def create_user_defined(
        cls,
        name: str,
        application_id: str,
        support_index: int,
        girder_index: int,
        bearing_index: int,
        configuration_type: BearingConfigurationTypeParaModel,
        orientation: ElementOrientationParaModel,
        sdx_value: float,
        sdy_value: float,
        sdz_value: float,
        srx_value: float,
        sry_value: float,
        srz_value: float,
    ):
        return cls.create(
            name=name,
            application_id=application_id,
            support_index=support_index,
            girder_index=girder_index,
            bearing_index=bearing_index,
            configuration_type=configuration_type,
            orientation=orientation,
            spring_definitions=BoundaryConditionSpringParameterGroup.create(
                sdx_dof_type=DofTypeEnumParaModel.CUSTOM,
                sdx_stiffness=sdx_value,
                sdy_dof_type=DofTypeEnumParaModel.CUSTOM,
                sdy_stiffness=sdy_value,
                sdz_dof_type=DofTypeEnumParaModel.CUSTOM,
                sdz_stiffness=sdz_value,
                srx_dof_type=DofTypeEnumParaModel.CUSTOM,
                srx_stiffness=srx_value,
                sry_dof_type=DofTypeEnumParaModel.CUSTOM,
                sry_stiffness=sry_value,
                srz_dof_type=DofTypeEnumParaModel.CUSTOM,
                srz_stiffness=srz_value,
            ),
        )

    @classmethod
    def create(
        cls,
        name: str,
        application_id: str,
        support_index: int,
        girder_index: int,
        bearing_index: int,
        configuration_type:
            BearingConfigurationTypeParaModel,
        orientation:
            ElementOrientationParaModel,
        spring_definitions,
    ):
        spring_group_type = (
            BearingSpringDefinitionsGroup_Singular
            if configuration_type == BearingConfigurationTypeParaModel.SINGULAR
            else BearingSpringDefinitionsGroup_Multiple
        )

        if isinstance(spring_definitions, dict) and all(
            key in {"SDX", "SDY", "SDZ", "SRX", "SRY", "SRZ"}
            for key in spring_definitions
        ):
            spring_definitions = cls._build_single_spring_definition(
                bearing_index=bearing_index,
                orientation=orientation,
                spring_definitions=spring_definitions,
            )
        elif isinstance(spring_definitions, BoundaryConditionSpringParameterGroup):
            spring_definitions = cls._build_single_spring_definition(
                bearing_index=bearing_index,
                orientation=orientation,
                spring_definitions=spring_definitions,
            )
        elif not (
            isinstance(spring_definitions, dict)
            and all(
                isinstance(key, str) and key.startswith("bearing-")
                for key in spring_definitions
            )
        ):
            raise TypeError(
                "spring_definitions must either be a six-axis DOF dict, a spring definition group, or a bearing-indexed mapping."
            )

        return cls(
            applicationId=application_id,
            name=name,
            properties=(
                BearingBCDataObjectProperties(
                    **{
                        "Support Index": SupportIndexParameter(
                            isUser=True,
                            provided_value=support_index,
                        ),
                        "Girder Index": GirderIndexParameter(
                            isUser=True,
                            provided_value=girder_index,
                        ),
                        "Bearing Boundary Condition Parameters":
                            BearingBCParameterGroup(
                                isUser=True,
                                group_parameters=TypeAdapter(
                                    BearingBCParameters
                                ).validate_python(
                                    {
                                            "Bearing Configuration Type":
                                                {
                                                    "name": "Bearing Configuration Type",
                                                    "isUser": True,
                                                    "provided_value": configuration_type,
                                                },

                                            "Bearing Spring Definitions":
                                                spring_group_type(
                                                    isUser=True,
                                                    group_parameters=spring_definitions,
                                                ),
                                    }
                                )
                        )
                    }
                )
            )
        )


if __name__ == "__main__":
    import json

    examples = {
        "Free bearing": (
            BearingBCDataObject.create_free(
                name="Free Bearing",
                application_id="BC-BEARING-0001",
                support_index=0,
                girder_index=0,
                bearing_index=0,
                configuration_type=BearingConfigurationTypeParaModel.SINGULAR,
                orientation=ElementOrientationParaModel.ORTHOGONAL,
            )
        ),
        "Fixed bearing": (
            BearingBCDataObject.create_fixed(
                name="Fixed Bearing",
                application_id="BC-BEARING-0002",
                support_index=0,
                girder_index=1,
                bearing_index=1,
                configuration_type=BearingConfigurationTypeParaModel.SINGULAR,
                orientation=ElementOrientationParaModel.ORTHOGONAL,
            )
        ),
        "Custom bearing": (
            BearingBCDataObject.create_user_defined(
                name="Custom Bearing",
                application_id="BC-BEARING-0003",
                support_index=1,
                girder_index=2,
                bearing_index=2,
                configuration_type=BearingConfigurationTypeParaModel.SINGULAR,
                orientation=ElementOrientationParaModel.SKEWED,
                sdx_value=100000,
                sdy_value=110000,
                sdz_value=120000,
                srx_value=25000,
                sry_value=27500,
                srz_value=30000,
            )
        ),
        "Multiple bearings": (
            BearingBCDataObject.create(
                name="Multiple Bearings",
                application_id="BC-BEARING-0004",
                support_index=1,
                girder_index=0,
                bearing_index=0,
                configuration_type=BearingConfigurationTypeParaModel.MULTIPLE,
                orientation=ElementOrientationParaModel.ORTHOGONAL,
                spring_definitions={
                    "bearing-0000": BearingBCDataObject.create_free(
                        name="Example Spring A",
                        application_id="BC-BEARING-0005",
                        support_index=1,
                        girder_index=0,
                        bearing_index=0,
                        configuration_type=BearingConfigurationTypeParaModel.SINGULAR,
                        orientation=ElementOrientationParaModel.ORTHOGONAL,
                    ).properties.bearing_boundary_condition_parameters.group_parameters.spring_definitions.group_parameters[
                        "bearing-0000"
                    ],
                    "bearing-0001": BearingBCDataObject.create_user_defined(
                        name="Example Spring B",
                        application_id="BC-BEARING-0006",
                        support_index=1,
                        girder_index=0,
                        bearing_index=1,
                        configuration_type=BearingConfigurationTypeParaModel.SINGULAR,
                        orientation=ElementOrientationParaModel.ORTHOGONAL,
                        sdx_value=90000,
                        sdy_value=95000,
                        sdz_value=100000,
                        srx_value=20000,
                        sry_value=22000,
                        srz_value=24000,
                    ).properties.bearing_boundary_condition_parameters.group_parameters.spring_definitions.group_parameters[
                        "bearing-0001"
                    ],
                },
            )
        ),
    }

    for title, bearing in examples.items():
        print(f"\n{title}\n{'-' * len(title)}")
        print(json.dumps(bearing.model_dump(mode="json", by_alias=True), indent=2))