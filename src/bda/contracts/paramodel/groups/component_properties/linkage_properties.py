
from typing import List, Union, Literal, Annotated

from pydantic import Field, BaseModel

from bda.contracts.paramodel.groups.enums import BearingConfigurationTypeParaModel, SpacingTypeParaModel
from bda.contracts.paramodel.groups.component_properties.properties_base import PropertiesBaseParaModel

from bda.contracts.shared import QuantityParaModel

# -------------------------
# Abstract base classes
# -------------------------

class BearingConfigurationDetailsBaseParaModel(BaseModel):
    bearing_configuration_type: BearingConfigurationTypeParaModel
    no_of_bearings: int

# --------------------------------------------------
# Main Properties of the Linkage group
# --------------------------------------------------

class PropertiesLinkageSupToSubParaModel(PropertiesBaseParaModel):
    support_index: int
    bearing_configuration_details: Annotated[Union[
        SingleBearingConfigurationDetailsParaModel,
        MultipleBearingConfigurationDetailsParaModel
    ], Field(discriminator="bearing_configuration_type")]

# --------------------------------------------------
# Other Properties
# --------------------------------------------------

class MultipleBearingConfigurationDetailsParaModel(BearingConfigurationDetailsBaseParaModel):
    bearing_configuration_type: Literal[BearingConfigurationTypeParaModel.MULTIPLE]
    bearing_spacing_type: SpacingTypeParaModel
    bearing_spacing: List[QuantityParaModel]


class SingleBearingConfigurationDetailsParaModel(BearingConfigurationDetailsBaseParaModel):
    model_config = {"extra": "forbid"}
    bearing_configuration_type: Literal[BearingConfigurationTypeParaModel.SINGULAR]
    no_of_bearings: int = Field(default=1)
