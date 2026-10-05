from typing import Dict, Type

from bda.contracts.paramodel.groups.enums import StructuralComponentTypeParaModel

from .properties_base import PropertiesBaseParaModel, PropertiesIndividualTendonParaModel

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
    # These Speckle component groups carry common group metadata but do not
    # define component-specific fields in the current ParaModel schema.
    StructuralComponentTypeParaModel.LONGITUDINAL_MEMBERS: PropertiesBaseParaModel,
    StructuralComponentTypeParaModel.REINFORCEMENT_GROUP: PropertiesBaseParaModel,
    StructuralComponentTypeParaModel.PRIMARY_REINFORCEMENT: PropertiesBaseParaModel,
    StructuralComponentTypeParaModel.SECONDARY_REINFORCEMENT: PropertiesBaseParaModel,
    StructuralComponentTypeParaModel.SHEAR_REINFORCEMENT: PropertiesBaseParaModel,
    StructuralComponentTypeParaModel.TENDON_GROUP: PropertiesBaseParaModel,
    StructuralComponentTypeParaModel.EDGE_BEAM: PropertiesBaseParaModel,
    StructuralComponentTypeParaModel.TRANSVERSE_MEMBERS: PropertiesBaseParaModel,
    StructuralComponentTypeParaModel.DECK_SLAB: PropertiesBaseParaModel,
    StructuralComponentTypeParaModel.SUBSTRUCTURE: PropertiesBaseParaModel,
    StructuralComponentTypeParaModel.VERTICAL_MEMBERS: PropertiesBaseParaModel,
    StructuralComponentTypeParaModel.HORIZONTAL_MEMBERS: PropertiesBaseParaModel,
    StructuralComponentTypeParaModel.GROUND_BEAM: PropertiesBaseParaModel,
    StructuralComponentTypeParaModel.SPREAD_FOOTING: PropertiesBaseParaModel,
    StructuralComponentTypeParaModel.LINKAGE: PropertiesBaseParaModel,
    StructuralComponentTypeParaModel.SUBSTRUCTURE_CONNECTIONS: PropertiesBaseParaModel,
    StructuralComponentTypeParaModel.SUPERSTRUCTURE_CONNECTIONS: PropertiesBaseParaModel,
    StructuralComponentTypeParaModel.DECK_SLAB_CONNECTIONS: PropertiesBaseParaModel,
    StructuralComponentTypeParaModel.BRACING_CONNECTIONS: PropertiesBaseParaModel,
    StructuralComponentTypeParaModel.PLAN_BRACING_CONNECTIONS: PropertiesBaseParaModel,
    StructuralComponentTypeParaModel.TRANSVERSE_BRACING_CONNECTIONS: PropertiesBaseParaModel,
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
    StructuralComponentTypeParaModel.SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS: PropertiesLinkageSupToSubParaModel,
    StructuralComponentTypeParaModel.INDIVIDUAL_TENDON: PropertiesIndividualTendonParaModel,
}
