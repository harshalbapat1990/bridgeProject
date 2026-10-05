from bda.contracts.paramodel.groups.component_properties.properties_base import PropertiesBaseParaModel, SegmentDetailsParaModel

from .groups_para_model import (
    GeometryGroupParaModel,
)
from .geometry_elements import ParaNode, ParaElement
from .component_properties.bridge_properties import PropertiesBridgeParaModel, AnalysisSettingsParaModel

from bda.contracts.paramodel.groups.component_properties.substructure_properties import (
    SupportTypeParaModel,
    FoundationTypeParaModel,
    PropertiesSupportParaModel,
    PropertiesAboveGroundParaModel,
    PropertiesPierParaModel,
    PropertiesWallParaModel,
    PropertiesCrossbeamParaModel,
    PropertiesBelowGroundParaModel,
    PropertiesPileParaModel,
    PropertiesPileCapParaModel,
    AboveGroundDetailsBaseParaModel,
    FoundationDetailsBaseParaModel,
    AboveGroundDetailsSolidTypeParaModel,
    AboveGroundDetailsColumnTypeParaModel,
    TaperedDetailsParaModel,
    DeepFoundationDetailsParaModel,
    ShallowFoundationDetailsParaModel,
    ElementOrientationParaModel,
)

from bda.contracts.paramodel.groups.component_properties.superstructure_properties import (
    PropertiesSuperstructureParaModel,
    PlanBracingTypeParaModel,
    DiaphragmTypeParaModel,
    DiaphragmConcreteNonModelled,
    DiaphragmSteelGirderParaModel,
    DiaphragmBracingEncasedParaModel,
    BracingBraceXtypeDetailsParaModel,
    BracingBraceKtypeDetailsBraceParaModel,
    BracingTypeParaModel,
    PropertiesBracingBraceParaModel,
    PropertiesBracingChordParaModel,
    PropertiesPlanBracingParaModel,
    DiaphragmDetailsBaseParaModel,
    CrackedExtentsDetailsParaModel,
    ConstrSequenceDetailsParaModel,
    TransverseBracingDetailsParaModel,
    PropertiesGirderParaModel,
    PropertiesDiaphragmParaModel,
    PropertiesTransverseBracingParaModel,
    PropertiesSpanParaModel,
)

from bda.contracts.paramodel.groups.component_properties.linkage_properties import (
    PropertiesLinkageSupToSubParaModel,
    BearingConfigurationDetailsBaseParaModel,
    MultipleBearingConfigurationDetailsParaModel,
    SingleBearingConfigurationDetailsParaModel,
)

__all__ = [
    #geometry_elements
    "ParaNode",
    "ParaElement",

    # groups_para_model
    "PropertiesBridgeParaModel",
    "AnalysisSettingsParaModel",
    "GeometryGroupParaModel",

    # substructure_properties
    "SupportTypeParaModel",
    "FoundationTypeParaModel",
    "PropertiesSupportParaModel",
    "PropertiesAboveGroundParaModel",
    "PropertiesPierParaModel",
    "PropertiesWallParaModel",
    "PropertiesCrossbeamParaModel",
    "PropertiesBelowGroundParaModel",
    "PropertiesPileParaModel",
    "PropertiesPileCapParaModel",
    "AboveGroundDetailsBaseParaModel",
    "FoundationDetailsBaseParaModel",
    "AboveGroundDetailsSolidTypeParaModel",
    "AboveGroundDetailsColumnTypeParaModel",
    "TaperedDetailsParaModel",
    "DeepFoundationDetailsParaModel",
    "ShallowFoundationDetailsParaModel",
    "ElementOrientationParaModel",

    # superstructure_properties
    "PropertiesSuperstructureParaModel",
    "PlanBracingTypeParaModel",
    "DiaphragmTypeParaModel",
    "BracingBraceKtypeDetailsBraceParaModel",
    "BracingBraceXtypeDetailsParaModel",
    "DiaphragmConcreteNonModelled",
    "DiaphragmSteelGirderParaModel",
    "DiaphragmBracingEncasedParaModel",
    "BracingBraceXtypeDetailsParaModel",
    "BracingTypeParaModel",
    "PropertiesBracingBraceParaModel",
    "PropertiesBracingChordParaModel",
    "PropertiesPlanBracingParaModel",
    "DiaphragmDetailsBaseParaModel",
    "CrackedExtentsDetailsParaModel",
    "ConstrSequenceDetailsParaModel",
    "TransverseBracingDetailsParaModel",
    "PropertiesGirderParaModel",
    "PropertiesDiaphragmParaModel",
    "PropertiesTransverseBracingParaModel",
    "PropertiesSpanParaModel",

    # linkage_properties
    "PropertiesLinkageSupToSubParaModel",
    "BearingConfigurationDetailsBaseParaModel",
    "MultipleBearingConfigurationDetailsParaModel",
    "SingleBearingConfigurationDetailsParaModel",
]