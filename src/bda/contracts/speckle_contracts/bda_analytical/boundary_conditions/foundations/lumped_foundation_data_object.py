from __future__ import annotations

from typing import (
    Literal,
    ClassVar,
    TypeAlias
)

from pydantic import (
    BaseModel,
    Field,
    ConfigDict
)

from bda.contracts.speckle_contracts.base_objects import (
    BridgeDataObject,
    BridgeDataObjectProperties,
    ParameterGroup,
)

from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.foundations.foundation_parameters import (
    FoundationOrientationParameter,
    SupportIndexParameter,
    LumpedFoundationFoundationModelTypeParameter,
    FoundationApplicationTypeParameter,
    VerticalOffsetParameter,
    BearingBasedFoundationApplicationTypeParameter,
    SubstructureElementBasedFoundationApplicationTypeParameter
)

from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.spring_parameters import (
    BoundaryConditionSpringParameterGroup,
)

from bda.contracts.paramodel.groups.enums import (
    ElementOrientationParaModel,
)
from bda.contracts.paramodel.foundations.enums import FoundationModelTypeParaModel, \
    FoundationApplicationTypeEnumParaModel


class LumpedFoundationParameters_General(
    BaseModel
):
    model_config = ConfigDict(
        populate_by_name=True
    )
    
    support_index: (
        SupportIndexParameter
    ) = Field(
        alias="Support Index"
    )

    orientation : (
        FoundationOrientationParameter
    ) = Field(
        alias="Lumped Foundation Orientation"
    )

    foundation_model_type: (
        LumpedFoundationFoundationModelTypeParameter
    ) = Field(
        alias="Foundation Model Type"
    )

    foundation_application_type: (
        FoundationApplicationTypeParameter
    ) = Field(
        alias="Foundation Application Type"
    )

    spring_definition: (
        BoundaryConditionSpringParameterGroup
    ) = Field(
        alias="Foundation Spring Definition"
    )

class LumpedFoundationParameters_BearingBased(
    LumpedFoundationParameters_General
):
    foundation_application_type: (
        BearingBasedFoundationApplicationTypeParameter
    ) = Field(
        alias="Foundation Application Type"
    )

    vertical_offset: VerticalOffsetParameter = Field(
        alias="Vertical Offset"
    )

class LumpedFoundationParameters_SubstructureElementBased(
    LumpedFoundationParameters_General
):
    foundation_application_type: (
        SubstructureElementBasedFoundationApplicationTypeParameter
    ) = Field(
        alias="Foundation Application Type"
    )
  
LumpedFoundationParameterOptions: TypeAlias = (
    LumpedFoundationParameters_SubstructureElementBased | LumpedFoundationParameters_BearingBased
)

class LumpedFoundationParameterGroup(
    ParameterGroup
):
    name: Literal[
        "Lumped Foundation Parameters"
    ] = (
        "Lumped Foundation Parameters"
    )

    group_parameters: (
        LumpedFoundationParameterOptions
    )


class LumpedFoundationDataObjectProperties(
    BridgeDataObjectProperties
):
    lumped_foundation_parameters: (
        LumpedFoundationParameterGroup
    ) = Field(
        alias="Lumped Foundation Parameters"
    )


class LumpedFoundationDataObject(
    BridgeDataObject
):

    APPLICATION_ID_PATTERN: ClassVar[str] = (
        r"^BC-FOUNDATION-LUMPED-\d{4}$"
    )

    applicationId: str = Field(
        pattern=APPLICATION_ID_PATTERN
    )

    name: str

    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Lumped_Foundation"
    ] = "Objects.Data.DataObject:BDA_Lumped_Foundation"

    properties: (
        LumpedFoundationDataObjectProperties
    )

    @classmethod
    def create(
        cls,
        name: str,
        application_id: str,
        support_index: int,
        foundation_model_type: str,
        foundation_application_type: str,
        orientation: ElementOrientationParaModel = ElementOrientationParaModel.ORTHOGONAL,
        spring_definition=None,
        vertical_offset: float | None = None,
        vertical_offset_unit: str = "m",
    ):
        foundation_application_type_enum = (
            FoundationApplicationTypeEnumParaModel(
                foundation_application_type
            )
        )

        if spring_definition is None:
            spring_definition_group = BoundaryConditionSpringParameterGroup.create()
        elif isinstance(spring_definition, BoundaryConditionSpringParameterGroup):
            spring_definition_group = spring_definition
        elif isinstance(spring_definition, dict):
            spring_definition_group = (
                BoundaryConditionSpringParameterGroup.create(
                    sdx_dof_type=spring_definition.get("SDX", {}).get("DOF Type", {}).get("provided_value", "free"),
                    sdx_stiffness=spring_definition.get("SDX", {}).get("Stiffness", {}).get("provided_value") if isinstance(spring_definition.get("SDX", {}).get("Stiffness"), dict) else None,
                    sdy_dof_type=spring_definition.get("SDY", {}).get("DOF Type", {}).get("provided_value", "free"),
                    sdy_stiffness=spring_definition.get("SDY", {}).get("Stiffness", {}).get("provided_value") if isinstance(spring_definition.get("SDY", {}).get("Stiffness"), dict) else None,
                    sdz_dof_type=spring_definition.get("SDZ", {}).get("DOF Type", {}).get("provided_value", "free"),
                    sdz_stiffness=spring_definition.get("SDZ", {}).get("Stiffness", {}).get("provided_value") if isinstance(spring_definition.get("SDZ", {}).get("Stiffness"), dict) else None,
                    srx_dof_type=spring_definition.get("SRX", {}).get("DOF Type", {}).get("provided_value", "free"),
                    srx_stiffness=spring_definition.get("SRX", {}).get("Stiffness", {}).get("provided_value") if isinstance(spring_definition.get("SRX", {}).get("Stiffness"), dict) else None,
                    sry_dof_type=spring_definition.get("SRY", {}).get("DOF Type", {}).get("provided_value", "free"),
                    sry_stiffness=spring_definition.get("SRY", {}).get("Stiffness", {}).get("provided_value") if isinstance(spring_definition.get("SRY", {}).get("Stiffness"), dict) else None,
                    srz_dof_type=spring_definition.get("SRZ", {}).get("DOF Type", {}).get("provided_value", "free"),
                    srz_stiffness=spring_definition.get("SRZ", {}).get("Stiffness", {}).get("provided_value") if isinstance(spring_definition.get("SRZ", {}).get("Stiffness"), dict) else None,
                )
            )
        else:
            raise TypeError(
                "spring_definition must be a BoundaryConditionSpringParameterGroup or a six-axis DOF dictionary."
            )

        payload = {
            "Support Index": SupportIndexParameter(
                isUser=True,
                provided_value=support_index,
            ),
            "Lumped Foundation Orientation": FoundationOrientationParameter(
                isUser=True,
                provided_value=orientation,
            ),
            "Foundation Model Type": LumpedFoundationFoundationModelTypeParameter(
                isUser=True,
                provided_value=foundation_model_type,
            ),
            "Foundation Application Type": (
                BearingBasedFoundationApplicationTypeParameter(
                    isUser=True,
                    provided_value=FoundationApplicationTypeEnumParaModel.BEARING_BASED,
                )
                if foundation_application_type_enum
                == FoundationApplicationTypeEnumParaModel.BEARING_BASED
                else SubstructureElementBasedFoundationApplicationTypeParameter(
                    isUser=True,
                    provided_value=FoundationApplicationTypeEnumParaModel.SUBSTRUCTURE_ELEMENT_BASED,
                )
            ),
            "Foundation Spring Definition": spring_definition_group,
        }

        if foundation_application_type_enum == FoundationApplicationTypeEnumParaModel.BEARING_BASED:
            if vertical_offset is None:
                raise ValueError(
                    "vertical_offset is required when foundation_application_type is bearing_based"
                )
            payload["Vertical Offset"] = VerticalOffsetParameter(
                isUser=True,
                provided_value=vertical_offset,
                provided_unit=vertical_offset_unit,
                base_unit="m",
            )
            parameter_model = LumpedFoundationParameters_BearingBased
        else:
            parameter_model = LumpedFoundationParameters_SubstructureElementBased

        return cls(
            applicationId=application_id,
            name=name,
            properties=LumpedFoundationDataObjectProperties(
                **{
                    "Lumped Foundation Parameters": LumpedFoundationParameterGroup(
                        isUser=False,
                        group_parameters=parameter_model(**payload),
                    )
                },
            ),
        )


import json


if __name__ == "__main__":
    examples = {
        "Bearing-based foundation": (
            LumpedFoundationDataObject.create(
                name="Lumped Foundation Example",
                application_id="BC-FOUNDATION-LUMPED-0001",
                support_index=0,
                foundation_model_type=FoundationModelTypeParaModel.LUMPED_FOUNDATION_MODEL,
                foundation_application_type=FoundationApplicationTypeEnumParaModel.BEARING_BASED,
                orientation=ElementOrientationParaModel.ORTHOGONAL,
                vertical_offset=0.5,
                vertical_offset_unit="m",
                spring_definition=BoundaryConditionSpringParameterGroup.create(
                    sdx_dof_type="free",
                    sdy_dof_type="free",
                    sdz_dof_type="fixed",
                    srx_dof_type="free",
                    sry_dof_type="free",
                    srz_dof_type="fixed",
                ),
            )
        ),
        "Substructure-element-based foundation": (
            LumpedFoundationDataObject.create(
                name="Substructure Foundation Example",
                application_id="BC-FOUNDATION-LUMPED-0002",
                support_index=1,
                foundation_model_type=FoundationModelTypeParaModel.LUMPED_FOUNDATION_MODEL,
                foundation_application_type=FoundationApplicationTypeEnumParaModel.SUBSTRUCTURE_ELEMENT_BASED,
                orientation=ElementOrientationParaModel.SKEWED,
                spring_definition=BoundaryConditionSpringParameterGroup.create(
                    sdx_dof_type="free",
                    sdy_dof_type="fixed",
                    sdz_dof_type="custom",
                    sdz_stiffness=1500.0,
                    srx_dof_type="free",
                    sry_dof_type="free",
                    srz_dof_type="fixed",
                ),
            )
        ),
    }

    print(json.dumps(LumpedFoundationDataObject.model_json_schema(), indent=4))

    for title, foundation in examples.items():
        print(f"\n{title}\n{'-' * len(title)}")
        print(json.dumps(foundation.model_dump(mode="json", by_alias=True), indent=2))