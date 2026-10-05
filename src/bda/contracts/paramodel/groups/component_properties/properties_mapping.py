from typing import Dict, Type

from bda.contracts.paramodel.groups.enums import StructuralComponentTypeParaModel

from .properties_base import PropertiesBaseParaModel

from .superstructure_properties import (
    PropertiesSuperstructureParaModel,
    PropertiesSpanParaModel,
    PropertiesGirderParaModel,
    PropertiesDiaphragmParaModel,
    PropertiesTransverseBracingParaModel,
    PropertiesBracingBraceParaModel,
    PropertiesBracingChordParaModel,
    PropertiesPlanBracingParaModel,
)

from .substructure_properties import (
    PropertiesSupportParaModel,
    PropertiesAboveGroundParaModel,
    PropertiesPierParaModel,
    PropertiesWallParaModel,
    PropertiesCrossbeamParaModel,
    PropertiesBelowGroundParaModel,
    PropertiesPileParaModel,
    PropertiesPileCapParaModel,
)

from bda.contracts.paramodel.groups.component_properties.linkage_properties import (
    PropertiesLinkageSupToSubParaModel
)
from bda.contracts.paramodel.groups.component_properties.bridge_properties import PropertiesBridgeParaModel

_PROPERTIES_BY_GROUP_TYPE: Dict[StructuralComponentTypeParaModel, Type[PropertiesBaseParaModel]] = {
    StructuralComponentTypeParaModel.BRIDGE: PropertiesBridgeParaModel,
    StructuralComponentTypeParaModel.SUPERSTRUCTURE: PropertiesSuperstructureParaModel,
    StructuralComponentTypeParaModel.SPAN: PropertiesSpanParaModel,
    StructuralComponentTypeParaModel.GIRDER: PropertiesGirderParaModel,
    StructuralComponentTypeParaModel.DIAPHRAGM: PropertiesDiaphragmParaModel,
    StructuralComponentTypeParaModel.TRANSVERSE_BRACING: PropertiesTransverseBracingParaModel,
    StructuralComponentTypeParaModel.BRACE: PropertiesBracingBraceParaModel,
    StructuralComponentTypeParaModel.CHORD: PropertiesBracingChordParaModel,
    StructuralComponentTypeParaModel.PLAN_BRACING: PropertiesPlanBracingParaModel,
    StructuralComponentTypeParaModel.SUPPORT: PropertiesSupportParaModel,
    StructuralComponentTypeParaModel.ABOVE_GROUND: PropertiesAboveGroundParaModel,
    StructuralComponentTypeParaModel.PIER: PropertiesPierParaModel,
    StructuralComponentTypeParaModel.WALL: PropertiesWallParaModel,
    StructuralComponentTypeParaModel.CROSSBEAM: PropertiesCrossbeamParaModel,
    StructuralComponentTypeParaModel.BELOW_GROUND: PropertiesBelowGroundParaModel,
    StructuralComponentTypeParaModel.PILE: PropertiesPileParaModel,
    StructuralComponentTypeParaModel.PILE_CAP: PropertiesPileCapParaModel,
    StructuralComponentTypeParaModel.SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS: PropertiesLinkageSupToSubParaModel
}