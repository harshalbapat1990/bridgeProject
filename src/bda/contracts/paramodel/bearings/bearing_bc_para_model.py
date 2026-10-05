from __future__ import annotations

from typing import Annotated, Literal, List, Union

from pydantic import Field, AliasChoices, AliasPath

from bda.contracts.paramodel.foundations.foundation_bc_para_model import NodeSpringStiffnessParaModel
from bda.contracts.paramodel.groups.enums import BearingConfigurationTypeParaModel, ElementOrientationParaModel
from bda.contracts.paramodel.shared.base_model_para_model import BaseModelParaModel


class BearingItemParaModel(BaseModelParaModel):
    bearing_index: int = Field(validation_alias=AliasChoices("bearing_index", AliasPath("Bearing Index", "provided_value")))
    orientation: ElementOrientationParaModel = Field(validation_alias=AliasChoices("orientation", AliasPath("Orientation", "provided_value")))
    bearing_stiffness_definition: NodeSpringStiffnessParaModel = Field(validation_alias=AliasChoices("bearing_stiffness_definition", AliasPath("Bearing Stiffness Definition", "group_parameters")))


class BearingBCsGirderBaseParaModel(BaseModelParaModel):
    girder_index: int = Field(validation_alias=AliasChoices("girder_index", AliasPath("properties", "Girder Index", "provided_value")))
    bearing_configuration_type: BearingConfigurationTypeParaModel


class SingleBearingBCsParaModel(BearingBCsGirderBaseParaModel):
    bearing_configuration_type: Literal[BearingConfigurationTypeParaModel.SINGULAR]
    bearing_definition: BearingItemParaModel


class MultipleBearingsBCsParaModel(BearingBCsGirderBaseParaModel):
    bearing_configuration_type: Literal[BearingConfigurationTypeParaModel.MULTIPLE]
    bearing_definitions: List[BearingItemParaModel]


BearingBCsGirderParaModel = Annotated[
    Union[
        SingleBearingBCsParaModel,
        MultipleBearingsBCsParaModel,
    ],
    Field(discriminator="bearing_configuration_type"),
]


class BearingBCsSupportParaModel(BaseModelParaModel):
    support_index: int
    bearings_by_girder: List[BearingBCsGirderParaModel]
