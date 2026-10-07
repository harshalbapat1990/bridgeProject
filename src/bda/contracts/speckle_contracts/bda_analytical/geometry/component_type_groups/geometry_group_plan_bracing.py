from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes
from typing import Annotated, ClassVar, Literal

from pydantic import BaseModel, Field, model_validator

from bda.contracts.paramodel.groups.enums import (
    StructuralComponentTypeParaModel,
    PlanBracingTypeParaModel,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.geometry_group_base import (
    GeometryGroupBase,
    GeometryGroupParameters,
    GeometryGroupProperties,
    GeometryGroupParameterProperties,
    StructureComponentGroupType,
    SectionIdString,
    MaterialIdString,
)

from bda.contracts.speckle_contracts.base_objects import (
    UnitlessParameter,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_transverse_bracing import (
    LeftGirderIndexParameter,
    RightGirderIndexParameter,
)


# =============================================================================
# PLAN BRACING PARAMETERS
# =============================================================================


class PlanBracingTypeParameter(UnitlessParameter[PlanBracingTypeParaModel]):
    name: Literal["Plan Bracing Type"] = "Plan Bracing Type"

    description: Literal[
        "Type of bracing (e.g., Warren, Pratt or X bracing)"
    ] = "Type of bracing (e.g., Warren, Pratt or X bracing)"

    symbol: None = None

    provided_value: PlanBracingTypeParaModel


# =============================================================================
# PLAN BRACING PROPERTY SET
# =============================================================================


class PlanBracingGroupPropertiesParameters(BaseModel):
    plan_bracing_type: PlanBracingTypeParameter = Field(
        alias="Plan Bracing Type"
    )

    left_girder_index: LeftGirderIndexParameter = Field(
        alias="Left Girder Index"
    )

    right_girder_index: RightGirderIndexParameter = Field(
        alias="Right Girder Index"
    )


class PlanBracingGroupProperties(GeometryGroupParameterProperties):
    group_parameters: PlanBracingGroupPropertiesParameters

    @classmethod
    def create(
        cls,
        plan_bracing_type: PlanBracingTypeParaModel,
        left_girder_index: int,
        right_girder_index: int,
        isUser: bool = True,
    ) -> "PlanBracingGroupProperties":
        return cls(
            isUser=isUser,
            group_parameters=PlanBracingGroupPropertiesParameters(
                **{
                    "Plan Bracing Type": PlanBracingTypeParameter(
                        isUser=isUser,
                        provided_value=plan_bracing_type,
                    ),
                    "Left Girder Index": LeftGirderIndexParameter(
                        isUser=isUser,
                        provided_value=left_girder_index,
                    ),
                    "Right Girder Index": RightGirderIndexParameter(
                        isUser=isUser,
                        provided_value=right_girder_index,
                    ),
                }
            ),
        )


# =============================================================================
# GROUP TYPE IDENTIFICATION
# =============================================================================


class PlanBracingStructureComponentGroupType(StructureComponentGroupType):
    provided_value: Literal[
        StructuralComponentTypeParaModel.PLAN_BRACING
    ] = StructuralComponentTypeParaModel.PLAN_BRACING


# =============================================================================
# PLAN BRACING METADATA
# =============================================================================


class GeometryGroupPropertiesPlanBracing(GeometryGroupProperties):
    structural_component_type: PlanBracingStructureComponentGroupType = Field(
        alias="Structural Component Type"
    )

    material_id: MaterialIdString = Field(
        alias="Material ID",
    )

    section_id: SectionIdString = Field(
        alias="Section ID",
    )

    group_properties: PlanBracingGroupProperties = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersPlanBracing(GeometryGroupParameters):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_PLANBRACING
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_PLANBRACING.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-PLAN-BRACING$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: GeometryGroupPropertiesPlanBracing


# =============================================================================
# PLAN BRACING GROUP
# =============================================================================

PlanBracingGroupElements = Annotated[
    GeometryGroupParametersPlanBracing, 
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupPlanBracing(GeometryGroupBase):
    bda_speckle_type: Literal[
        SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_PLANBRACING
    ] = Field(SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_PLANBRACING.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-PLAN-BRACING$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    elements: list[PlanBracingGroupElements] = Field(
        default_factory=list,
        json_schema_extra={
            "minItems": 1,
            "allOf": [
                {
                    "contains": {
                        "type": "object",
                        "properties": {
                            "bda_speckle_type": {
                                "const": (
                                    "Objects.Data.DataObject:"
                                    "BDA_Geometry_Group_Properties_PlanBracing"
                                )
                            }
                        },
                        "required": ["bda_speckle_type"],
                    },
                    "minContains": 1,
                    "maxContains": 1,
                }
            ],
        },
    )

    @model_validator(mode="after")
    def validate_plan_bracing_elements(self) -> "GeometryGroupPlanBracing":
        plan_bracing_properties_speckle_type = (
            "Objects.Data.DataObject:"
            "BDA_Geometry_Group_Properties_PlanBracing"
        )

        plan_bracing_properties_count = sum(
            1
            for element in self.elements
            if element.bda_speckle_type == plan_bracing_properties_speckle_type
        )

        if plan_bracing_properties_count != 1:
            raise ValueError(
                "GeometryGroupPlanBracing.elements must contain exactly one "
                f"{plan_bracing_properties_speckle_type} object. "
                f"Found {plan_bracing_properties_count}."
            )

        return self

    @classmethod
    def create(
        cls,
        material_id: str,
        section_id: str,
        plan_bracing_type: PlanBracingTypeParaModel,
        left_girder_index: int,
        right_girder_index: int,
        application_id: str = "COL-GEOMGROUP-0001-PLAN-BRACING",
        name: str|None = None,
        isUser: bool = True,
    ) -> "GeometryGroupPlanBracing":
        return cls(
            id=None,
            applicationId=application_id,
            name=name if name is not None else f"Plan Bracing_{left_girder_index}_{right_girder_index}", #TODO: Improve Autonaming
            elements=[
                GeometryGroupParametersPlanBracing(
                    **{
                        "id": None,
                        "applicationId": application_id.replace(
                            "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                        ),
                        "properties": GeometryGroupPropertiesPlanBracing(
                            **{
                                "Structural Component Type": PlanBracingStructureComponentGroupType(),
                                "Material ID": MaterialIdString(
                                    isUser=False,
                                    provided_value=material_id,
                                ),
                                "Section ID": SectionIdString(
                                    isUser=False,
                                    provided_value=section_id,
                                ),
                                "Geometry Group Properties": PlanBracingGroupProperties.create(
                                    plan_bracing_type=plan_bracing_type,
                                    left_girder_index=left_girder_index,
                                    right_girder_index=right_girder_index,
                                    isUser=isUser,
                                ),
                            }
                        ),
                    }
                )
            ],
        )


if __name__ == "__main__":
    plan_bracing_group = GeometryGroupPlanBracing.create(
        material_id="M1",
        section_id="S1",
        plan_bracing_type=PlanBracingTypeParaModel.WARREN,
        left_girder_index=1,
        right_girder_index=2,
        application_id="COL-GEOMGROUP-0001-PLAN-BRACING",
        name="plan_bracing_1",
        isUser=True,
    )

    print(plan_bracing_group.model_dump_json(indent=4))