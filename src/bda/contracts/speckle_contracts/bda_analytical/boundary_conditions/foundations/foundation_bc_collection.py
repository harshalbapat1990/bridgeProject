from __future__ import annotations
import re

from typing import Annotated, ClassVar, Literal, Union
from pydantic import Field, field_validator, model_validator

from bda.contracts.paramodel.groups.enums import ElementOrientationParaModel
from bda.contracts.speckle_contracts.base_objects import BridgeCollection
from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.foundations.lumped_foundation_data_object import LumpedFoundationDataObject
from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.foundations.pile_interaction_foundation_data_object import (
    PileDefinitionInput,
    PileInteractionFoundationDataObject,
)
from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.spring_parameters import (
    BoundaryConditionSpringParameterGroup,
    BoundaryConditionTranslationalSpringParameterGroup,
)
from bda.contracts.paramodel.foundations.enums import DofTypeEnumParaModel, FoundationModelTypeParaModel, \
    FoundationApplicationTypeEnumParaModel, SoilProfileTypeEnumParaModel

FoundationBCObject = Annotated[
    Union[
        LumpedFoundationDataObject,
        PileInteractionFoundationDataObject,
    ],
    Field(
        discriminator="bda_speckle_type",
    ),
]


class FoundationBCCollection(
    BridgeCollection
):
    COLLECTION_ID_PATTERN: ClassVar[
        re.Pattern
    ] = re.compile(
        r"^COL-FOUNDATION-BC$"
    )

    applicationId: str = Field(
        pattern=r"^COL-FOUNDATION-BC$"
    )

    name: Literal[
        "Foundation Boundary Conditions"
    ] = (
        "Foundation Boundary Conditions"
    )

    bda_speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection"
    ] = "Speckle.Core.Models.Collections.Collection"

    elements: list[FoundationBCObject] = Field(
        default_factory=list
    )

    @classmethod
    def create(cls, foundations: list[
            FoundationBCObject
        ] | None = None,
        application_id: str = (
            "COL-FOUNDATION-BC"
        ),
    ) -> "FoundationBCCollection":

        return cls(
            applicationId=application_id,
            elements=(
                foundations or []
            ),
        )

    @field_validator("applicationId")
    @classmethod
    def validate_application_id(cls, value: str):
        if not (cls.COLLECTION_ID_PATTERN.match(value)):
            raise ValueError(
                "Foundation BC collection "
                "applicationId must be "
                "COL-FOUNDATION-BC"
            )

        return value
    
    @model_validator(mode="after")
    def validate_unique_support_pile_pairs(self) -> "FoundationBCCollection":
        support_types: dict[
            int,
            Literal["lumped", "pile"]
        ] = {}
        seen: set[
            tuple[int, int | None]
        ] = set()

        for foundation in self.elements:

            # Lumped Foundation
            if isinstance(
                foundation,
                LumpedFoundationDataObject,
            ):
                parameters = (
                    foundation.properties
                    .lumped_foundation_parameters
                    .group_parameters
                )

                support_index = (
                    parameters
                    .support_index
                    .provided_value
                )

                existing = support_types.get(
                    support_index
                )

                if (
                    existing is not None
                    and existing != "lumped"
                ):
                    raise ValueError(
                        f"Support {support_index} "
                        "can not contain both lumped and pile interaction foundations."
                    )

                support_types[
                    support_index
                ] = "lumped"

                key = (
                    support_index,
                    None,
                )

                if key in seen:
                    raise ValueError(
                        "Duplicate lumped foundation "
                        f"for support_index="
                        f"{support_index}"
                    )

                seen.add(key)

            # Pile Interaction Foundation
            elif isinstance(
                foundation,
                PileInteractionFoundationDataObject,
            ):
                parameters = (
                    foundation.properties
                )

                support_index = (
                    parameters
                    .support_index
                    .provided_value
                )

                existing = support_types.get(
                    support_index
                )

                if (
                    existing is not None
                    and existing != "pile"
                ):
                    raise ValueError(
                        f"Support {support_index} "
                        "contains both lumped and "
                        "pile interaction foundations."
                    )

                support_types[
                    support_index
                ] = "pile"

                pile_definitions = (
                    parameters
                    .pile_definitions
                    .group_parameters
                )

                for pile in (
                    pile_definitions.values()
                ):
                    pile_index = (
                        pile.group_parameters
                        .pile_index
                        .provided_value
                    )

                    key = (
                        support_index,
                        pile_index,
                    )

                    if key in seen:
                        raise ValueError(
                            "Duplicate pile definition "
                            f"for support_index="
                            f"{support_index} "
                            f"and pile_index="
                            f"{pile_index}"
                        )

                    seen.add(key)

        return self


if __name__ == "__main__":
    spring_definition = BoundaryConditionSpringParameterGroup.create(
        sdx_dof_type=DofTypeEnumParaModel.FREE,
        sdy_dof_type=DofTypeEnumParaModel.FREE,
        sdz_dof_type=DofTypeEnumParaModel.FIXED,
        srx_dof_type=DofTypeEnumParaModel.FREE,
        sry_dof_type=DofTypeEnumParaModel.FREE,
        srz_dof_type=DofTypeEnumParaModel.FIXED,
    )

    translational_spring_definition = BoundaryConditionTranslationalSpringParameterGroup.create(
        sdx_dof_type=DofTypeEnumParaModel.FREE,
        sdy_dof_type=DofTypeEnumParaModel.FREE,
        sdz_dof_type=DofTypeEnumParaModel.FIXED,
    )

    lumped_foundation = LumpedFoundationDataObject.create(
        name="Lumped Foundation Example",
        application_id="BC-FOUNDATION-LUMPED-0001",
        support_index=1,
        foundation_model_type=FoundationModelTypeParaModel.LUMPED_FOUNDATION_MODEL,
        foundation_application_type=FoundationApplicationTypeEnumParaModel.BEARING_BASED,
        orientation=ElementOrientationParaModel.ORTHOGONAL,
        vertical_offset=0.5,
        vertical_offset_unit="m",
        spring_definition=spring_definition,
    )

    pile_foundation = PileInteractionFoundationDataObject.create(
        name="Pile Interaction Foundation Example",
        application_id="BC-FOUNDATION-PILE-0001",
        support_index=2,
        foundation_model_type=FoundationModelTypeParaModel.PILE_INTERACTION_MODEL,
        pile_definitions=[
            PileDefinitionInput(
                pile_index=1,
                soil_profile_type=SoilProfileTypeEnumParaModel.UNIFORM,
                top_node_spring_definition=translational_spring_definition,
                bottom_node_spring_definition=translational_spring_definition,
                intermediate_node_spring_definition=translational_spring_definition,
            )
        ],
    )

    examples = {
        "Lumped foundation": lumped_foundation,
        "Pile interaction foundation": pile_foundation,
    }

    for title, foundation in examples.items():
        print(f"\n{title}\n{'-' * len(title)}")
        print(
            foundation.model_dump_json(
                indent=4,
                by_alias=True,
            )
        )

    foundation_collection = FoundationBCCollection.create(
        foundations=[
            lumped_foundation,
            pile_foundation,
        ]
    )

    print(
        "\nCollection example\n------------------\n"
        + foundation_collection.model_dump_json(
            indent=4,
            by_alias=True,
        )
    )