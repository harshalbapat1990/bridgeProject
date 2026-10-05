
from typing import List, Union, Literal, Annotated

from pydantic import Field, BaseModel, AliasChoices, AliasPath

from bda.contracts.paramodel.groups.enums import BearingConfigurationTypeParaModel, SpacingTypeParaModel
from bda.contracts.paramodel.groups.component_properties.properties_base import PropertiesBaseParaModel

from bda.contracts.shared import QuantityParaModel

# -------------------------
# Abstract base classes
# -------------------------

class BearingConfigurationDetailsBaseParaModel(BaseModel):
    bearing_configuration_type: BearingConfigurationTypeParaModel
    no_of_bearings: int = Field(validation_alias=AliasChoices("no_of_bearings", AliasPath("Number Of Bearings", "provided_value")))

# --------------------------------------------------
# Main Properties of the Linkage group
# --------------------------------------------------

class PropertiesLinkageSupToSubParaModel(PropertiesBaseParaModel):
    support_index: int = Field(validation_alias=AliasChoices("support_index", AliasPath("Support Index", "provided_value")))
    bearing_configuration_details: Annotated[Union[
        SingleBearingConfigurationDetailsParaModel,
        MultipleBearingConfigurationDetailsParaModel
    ], Field(discriminator="bearing_configuration_type")] = Field(validation_alias=AliasChoices("bearing_configuration_details", AliasPath("Bearing Configuration Details", "group_parameters")))

# --------------------------------------------------
# Other Properties
# --------------------------------------------------

class MultipleBearingConfigurationDetailsParaModel(BearingConfigurationDetailsBaseParaModel):
    bearing_configuration_type: Literal[BearingConfigurationTypeParaModel.MULTIPLE]
    bearing_spacing_type: SpacingTypeParaModel = Field(validation_alias=AliasChoices("bearing_spacing_type", AliasPath("Bearing Spacing Type", "provided_value")))
    bearing_spacing: List[QuantityParaModel] = Field(validation_alias=AliasChoices("bearing_spacing", AliasPath("Bearing Spacing", "provided_value")))


class SingleBearingConfigurationDetailsParaModel(BearingConfigurationDetailsBaseParaModel):
    model_config = {"extra": "forbid"}
    bearing_configuration_type: Literal[BearingConfigurationTypeParaModel.SINGULAR]
    no_of_bearings: int = Field(default=1, validation_alias=AliasChoices("no_of_bearings", AliasPath("Number Of Bearings", "provided_value")))
