from __future__ import annotations

from pydantic import BaseModel

from bda.contracts.paramodel.groups import PropertiesBaseParaModel
from bda.contracts.paramodel.groups.enums import *
from bda.contracts.shared import QuantityParaModel


# --------------------------------------------------
# Main Properties of the Bridge
# --------------------------------------------------

class PropertiesBridgeParaModel(PropertiesBaseParaModel):
    bridge_type: BridgeTypeParaModel
    bridge_idealisation: BridgeIdealisationParaModel
    no_of_spans: int
    analysis_settings: AnalysisSettingsParaModel
    top_deck_level: QuantityParaModel


# --------------------------------------------------
# Other Properties
# --------------------------------------------------

class AnalysisSettingsParaModel(BaseModel):
    mesh_divisor: int
