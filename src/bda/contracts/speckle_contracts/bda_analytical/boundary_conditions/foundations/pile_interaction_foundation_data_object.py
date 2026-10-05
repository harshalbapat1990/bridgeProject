from __future__ import annotations

from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes

from dataclasses import dataclass, field
from typing import (
    Literal,
    ClassVar,
    Annotated,
    TypeAlias
)

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    StringConstraints
)

from bda.contracts.speckle_contracts.base_objects import (
    BridgeDataObject,
    BridgeDataObjectProperties,
    ParameterGroup,
)

from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.foundations.foundation_parameters import (
    SupportIndexParameter,
    FoundationModelTypeParameter,
    PileIndexParameter,
    SoilProfileTypeParameter,
    UniformSoilProfileTypeParameter,
    PileInteractionFoundationModelTypeParameter
)
from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.spring_parameters import (
    BoundaryConditionTranslationalSpringParameterGroup,
)
from bda.contracts.paramodel.foundations.enums import DofTypeEnumParaModel, FoundationModelTypeParaModel, \
    SoilProfileTypeEnumParaModel


@dataclass
class PileDefinitionInput:
    pile_index: int
    soil_profile_type: SoilProfileTypeEnumParaModel
    top_node_spring_definition: dict | BoundaryConditionTranslationalSpringParameterGroup
    bottom_node_spring_definition: dict | BoundaryConditionTranslationalSpringParameterGroup
    intermediate_node_spring_definition: (
        dict | BoundaryConditionTranslationalSpringParameterGroup | None
    ) = None


class PileInteractionParameters_Base(
    BaseModel
):
    model_config = ConfigDict(
        populate_by_name=True
    )

    pile_index: (
        PileIndexParameter
    ) = Field(
        alias="Pile Index"
    )

    soil_profile_type: (
        SoilProfileTypeParameter
    ) = Field(
        alias="Soil Profile Type"
    )

    top_node_spring_definition: (
        BoundaryConditionTranslationalSpringParameterGroup
    ) = Field(
        alias="Top Node Spring Definition"
    )

    bottom_node_spring_definition: (
        BoundaryConditionTranslationalSpringParameterGroup
    ) = Field(
        alias="Bottom Node Spring Definition"
    )


class UniformSoilTypePileInteractionParameters(
    PileInteractionParameters_Base
):
    soil_profile_type: (
        UniformSoilProfileTypeParameter
    ) = Field(
        alias="Soil Profile Type"
    )

    intermediate_node_spring_definition: (
        BoundaryConditionTranslationalSpringParameterGroup
    ) = Field(
        alias="Intermediate Node Spring Definition"
    )

PileInteractionParameterOptions: TypeAlias = (
    UniformSoilTypePileInteractionParameters
    # | LayeredSoilTypePileInteractionParameters
)


class PileInteractionParameterGroup(
    ParameterGroup
):
    name: Literal[
        "Pile Interaction Parameters"
    ] = (
        "Pile Interaction Parameters"
    )

    group_parameters: (
        PileInteractionParameterOptions
    )

PileDefinitionKey = Annotated[
    str,
    StringConstraints(pattern=r"^pile-\d{4}$"),
]


class PileDefinitionsGroup(
    ParameterGroup
):
    name: Literal[
        "Pile Definitions"
    ] = "Pile Definitions"

    group_parameters: dict[
        PileDefinitionKey,
        PileInteractionParameterGroup
    ]


class PileInteractionFoundationDataObjectProperties(
    BridgeDataObjectProperties
):
    model_config = ConfigDict(populate_by_name=True)

    support_index: (
        SupportIndexParameter
    ) = Field(
        alias="Support Index"
    )

    foundation_model_type: (
        PileInteractionFoundationModelTypeParameter
    ) = Field(
        alias="Foundation Model Type"
    )

    pile_definitions: (
        PileDefinitionsGroup
    ) = Field(
        alias="Pile Definitions"
    )


class PileInteractionFoundationDataObject(
    BridgeDataObject
):

    APPLICATION_ID_PATTERN: ClassVar[str] = (
        r"^BC-FOUNDATION-PILE-\d{4}$"
    )

    applicationId: str = Field(
        pattern=APPLICATION_ID_PATTERN
    )

    name: str

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_PILE_INTERACTION_FOUNDATION
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_PILE_INTERACTION_FOUNDATION.value, frozen=True)

    properties: (
        PileInteractionFoundationDataObjectProperties
    )

    @staticmethod
    def _to_translational_spring_group(
        value: dict | BoundaryConditionTranslationalSpringParameterGroup,
    ) -> BoundaryConditionTranslationalSpringParameterGroup:
        if isinstance(value, BoundaryConditionTranslationalSpringParameterGroup):
            return value

        if not isinstance(value, dict):
            raise TypeError(
                "Spring definition must be a dictionary or a BoundaryConditionTranslationalSpringParameterGroup."
            )

        return BoundaryConditionTranslationalSpringParameterGroup.create(
            sdx_dof_type=value.get("SDX", {}).get("DOF Type", {}).get("provided_value", DofTypeEnumParaModel.FREE),
            sdx_stiffness=value.get("SDX", {}).get("Stiffness", {}).get("provided_value") if isinstance(value.get("SDX", {}).get("Stiffness"), dict) else None,
            sdy_dof_type=value.get("SDY", {}).get("DOF Type", {}).get("provided_value", DofTypeEnumParaModel.FREE),
            sdy_stiffness=value.get("SDY", {}).get("Stiffness", {}).get("provided_value") if isinstance(value.get("SDY", {}).get("Stiffness"), dict) else None,
            sdz_dof_type=value.get("SDZ", {}).get("DOF Type", {}).get("provided_value", DofTypeEnumParaModel.FREE),
            sdz_stiffness=value.get("SDZ", {}).get("Stiffness", {}).get("provided_value") if isinstance(value.get("SDZ", {}).get("Stiffness"), dict) else None,
        )

    @classmethod
    def _create_pile_parameters(
        cls,
        pile: PileDefinitionInput,
    ) -> PileInteractionParameterOptions:
        if pile.soil_profile_type == SoilProfileTypeEnumParaModel.UNIFORM:
            intermediate_definition = (
                cls._to_translational_spring_group(
                    pile.intermediate_node_spring_definition
                )
                if pile.intermediate_node_spring_definition is not None
                else cls._to_translational_spring_group(
                    pile.top_node_spring_definition
                )
            )

            return UniformSoilTypePileInteractionParameters.model_validate(
                {
                    "Pile Index": PileIndexParameter(
                        isUser=True,
                        provided_value=pile.pile_index,
                    ),
                    "Soil Profile Type": UniformSoilProfileTypeParameter(
                        isUser=True,
                        provided_value=pile.soil_profile_type,
                    ),
                    "Top Node Spring Definition": (
                        cls._to_translational_spring_group(
                            pile.top_node_spring_definition
                        )
                    ),
                    "Bottom Node Spring Definition": (
                        cls._to_translational_spring_group(
                            pile.bottom_node_spring_definition
                        )
                    ),
                    "Intermediate Node Spring Definition": (
                        intermediate_definition
                    ),
                }
            )

        raise NotImplementedError(
            f"Soil profile type '{pile.soil_profile_type}' "
            "is not yet supported."
        )

    @classmethod
    def create(
        cls,
        name: str,
        application_id: str,
        support_index: int,
        foundation_model_type: FoundationModelTypeParaModel,
        pile_definitions: list[PileDefinitionInput],
    ):
        pile_groups = {}

        for pile in pile_definitions:
            pile_key = f"pile-{pile.pile_index:04d}"

            pile_groups[pile_key] = (
                PileInteractionParameterGroup(
                    isUser=True,
                    group_parameters=cls._create_pile_parameters(
                        pile
                    ),
                )
            )

        return cls(
            applicationId=application_id,
            name=name,
            properties=PileInteractionFoundationDataObjectProperties.model_validate(
                {
                    "Support Index": {
                        "isUser": True,
                        "provided_value": support_index,
                    },
                    "Foundation Model Type": {
                        "isUser": True,
                        "provided_value": foundation_model_type,
                    },
                    "Pile Definitions": {
                        "isUser": True,
                        "group_parameters": pile_groups,
                    },
                }
            ),
        )

import json
if __name__ == "__main__":

    schema = (
        PileInteractionFoundationDataObject
        .model_json_schema()
    )

    print(
        json.dumps(
            schema,
            indent=4,
        )
    )

    spring_definition = BoundaryConditionTranslationalSpringParameterGroup.create(
        sdx_dof_type=DofTypeEnumParaModel.FREE,
        sdy_dof_type=DofTypeEnumParaModel.FREE,
        sdz_dof_type=DofTypeEnumParaModel.FIXED,
    )

    pile_foundation = PileInteractionFoundationDataObject.create(
        name="Pile Interaction Example",
        application_id="BC-FOUNDATION-PILE-0001",
        support_index=0,
        foundation_model_type=FoundationModelTypeParaModel.PILE_INTERACTION_MODEL,
        pile_definitions=[
            PileDefinitionInput(
                pile_index=1,
                soil_profile_type=SoilProfileTypeEnumParaModel.UNIFORM,
                top_node_spring_definition=spring_definition,
                bottom_node_spring_definition=spring_definition,
                intermediate_node_spring_definition=spring_definition,
            )
        ],
    )

    print(
        pile_foundation.model_dump_json(
            indent=4,
            by_alias=True,
        )
    )