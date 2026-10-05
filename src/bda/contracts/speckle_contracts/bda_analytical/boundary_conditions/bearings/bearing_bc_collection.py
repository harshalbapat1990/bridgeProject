from __future__ import annotations

import re

from typing import (
    ClassVar,
    Literal,
)

from pydantic import (
    Field,
    field_validator,
    model_validator,
)

from bda.contracts.speckle_contracts.base_objects import (
    BridgeCollection,
)

from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.bearings.bearing_bc_data_object import (
    BearingBCDataObject,
)
from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.bearings.bearing_parameters import BearingNodeSpringStiffnessParameterGroup



class BearingBCCollection(
    BridgeCollection
):
    COLLECTION_ID_PATTERN: ClassVar[
        re.Pattern
    ] = re.compile(
        r"^COL-BEARING-BC$"
    )

    applicationId: str = Field(
        pattern=r"^COL-BEARING-BC$"
    )

    name: Literal[
        "Bearing Boundary Conditions"
    ] = (
        "Bearing Boundary Conditions"
    )

    bda_speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection"
    ] = "Speckle.Core.Models.Collections.Collection"

    elements: list[
        BearingBCDataObject
    ] = Field(
        default_factory=list
    )

    @classmethod
    def create(
        cls,
        bearing_conditions: list[
            BearingBCDataObject
        ] | None = None,
        application_id: str = (
            "COL-BEARING-BC"
        ),
    ) -> "BearingBCCollection":

        return cls(
            applicationId=application_id,
            elements=(
                bearing_conditions or []
            ),
        )

    @field_validator(
        "applicationId"
    )
    @classmethod
    def validate_application_id(
        cls,
        value: str,
    ):

        if not (
            cls.COLLECTION_ID_PATTERN
            .match(value)
        ):
            raise ValueError(
                "Bearing BC collection "
                "applicationId must be "
                "COL-BEARING-BC"
            )

        return value

    @model_validator(mode="after")
    def validate_unique_support_girder_pairs(self) -> "BearingBCCollection":
        seen: set[
            tuple[int, int, int]
        ] = set()

        for bc in self.elements:
            properties = bc.properties
            support_index = properties.support_index.provided_value
            girder_index = properties.girder_index.provided_value
            spring_definitions = (
                properties.bearing_boundary_condition_parameters.group_parameters
                .spring_definitions.group_parameters
            )

            for name, bearing in spring_definitions.items():
                assert isinstance(
                    bearing,
                    BearingNodeSpringStiffnessParameterGroup,
                ), (
                    f"Bearing Definition {name} in {bc.name} does not contain "
                    "a valid spring instance"
                )

                bearing_index = bearing.group_parameters.bearing_index.provided_value
                key = (
                    support_index,
                    girder_index,
                    bearing_index,
                )

                if key in seen:
                    raise ValueError(
                        "Duplicate bearing boundary condition definition found for support_index="
                        f"{support_index} "
                        f", girder_index="
                        f"{girder_index} "
                        f"and bearing_index="
                        f"{bearing_index}. "
                        "Multiple definitions for the same support,girder and bearing combination are not permitted."
                    )

                seen.add(key)

        return self


from bda.contracts.paramodel.groups.enums import (
    BearingConfigurationTypeParaModel,
    ElementOrientationParaModel,
)
if __name__ == "__main__":
    import json

    examples = {
        "Single free bearing": (
            BearingBCCollection.create(
                bearing_conditions=[
                    BearingBCDataObject.create_free(
                        name="Free Bearing",
                        application_id="BC-BEARING-0001",
                        support_index=0,
                        girder_index=0,
                        bearing_index=0,
                        configuration_type=BearingConfigurationTypeParaModel.SINGULAR,
                        orientation=ElementOrientationParaModel.ORTHOGONAL,
                    )
                ]
            )
        ),
        "Single fixed bearing": (
            BearingBCCollection.create(
                bearing_conditions=[
                    BearingBCDataObject.create_fixed(
                        name="Fixed Bearing",
                        application_id="BC-BEARING-0002",
                        support_index=0,
                        girder_index=1,
                        bearing_index=1,
                        configuration_type=BearingConfigurationTypeParaModel.SINGULAR,
                        orientation=ElementOrientationParaModel.ORTHOGONAL,
                    )
                ]
            )
        ),
        "Single custom bearing": (
            BearingBCCollection.create(
                bearing_conditions=[
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
                ]
            )
        ),
        "Multiple bearings": (
            BearingBCCollection.create(
                bearing_conditions=[
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
                ]
            )
        ),
    }

    for title, collection in examples.items():
        print(f"\n{title}\n{'-' * len(title)}")
        print(json.dumps(collection.model_dump(mode="json", by_alias=True), indent=2))