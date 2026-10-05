from __future__ import annotations

from pydantic import BaseModel, Field, AliasChoices, AliasPath

from bda.contracts.paramodel.groups import PropertiesBaseParaModel
from bda.contracts.paramodel.groups.enums import *
from bda.contracts.shared import QuantityParaModel


# --------------------------------------------------
# Main Properties of the Bridge
# --------------------------------------------------

class PropertiesBridgeParaModel(PropertiesBaseParaModel):
    bridge_type: BridgeTypeParaModel = Field(validation_alias=AliasChoices("bridge_type", AliasPath("Bridge Type", "provided_value")))
    bridge_idealisation: BridgeIdealisationParaModel = Field(validation_alias=AliasChoices("bridge_idealisation", AliasPath("Bridge Idealisation", "provided_value")))
    no_of_spans: int = Field(validation_alias=AliasChoices("no_of_spans", AliasPath("Number of Spans", "provided_value")))
    analysis_settings: AnalysisSettingsParaModel = Field(validation_alias=AliasChoices("analysis_settings", AliasPath("Analysis Settings", "group_parameters")))
    top_deck_level: QuantityParaModel = Field(validation_alias=AliasChoices("top_deck_level", AliasPath("Top Deck Level")))


# --------------------------------------------------
# Other Properties
# --------------------------------------------------

class AnalysisSettingsParaModel(BaseModel):
    mesh_divisor: int = Field(validation_alias=AliasChoices("mesh_divisor", AliasPath("Girder Mesh Divisor", "provided_value")))
