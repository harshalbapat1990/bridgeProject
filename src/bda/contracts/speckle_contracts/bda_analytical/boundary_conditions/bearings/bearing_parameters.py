from typing import Literal

from bda.contracts.speckle_contracts.base_objects import UnitlessParameter, ParameterGroup
from pydantic import BaseModel, Field
from bda.contracts.paramodel.groups.enums import (
    BearingConfigurationTypeParaModel,
    ElementOrientationParaModel,
)

from bda.contracts.speckle_contracts.bda_analytical.common_parameters import SupportIndexParameter, BearingIndexParameter
from bda.contracts.speckle_contracts.bda_analytical.boundary_conditions.spring_parameters import BoundaryConditionSpringParameterGroup
class GirderIndexParameter(
    UnitlessParameter[int]
):
    name: Literal["Girder Index"] = (
        "Girder Index"
    )

    description: Literal[
        "Index of the girder to which the bearing is attached"
    ] = (
        "Index of the girder to which the bearing is attached"
    )


class BearingOrientationParameter(
    UnitlessParameter[
        ElementOrientationParaModel
    ]
):
    name: Literal[
        "Bearing Orientation"
    ] = (
        "Bearing Orientation"
    )
    description: Literal[
        "Orientation of the bearing relative to the girder"
    ] = (
        "Orientation of the bearing relative to the girder"
    )


class BearingConfigurationTypeParameter(
    UnitlessParameter[
        BearingConfigurationTypeParaModel
    ]
):
    name: Literal[
        "Bearing Configuration Type"
    ] = (
        "Bearing Configuration Type"
    )

    description: Literal[
        "Configuration type of the bearing"
    ] = (
        "Configuration type of the bearing"
    )

class BearingBCDefinition(BaseModel):
    bearing_index: BearingIndexParameter = Field(alias="Bearing Index")
    bearing_stiffness_definition: BoundaryConditionSpringParameterGroup = Field(alias="Bearing Stiffness Definition")
    element_orientation: BearingOrientationParameter = Field(alias="Orientation")


class BearingNodeSpringStiffnessParameterGroup(
    ParameterGroup
):
    name: str = "Bearing Boundary Condition Definition"
    group_parameters: BearingBCDefinition