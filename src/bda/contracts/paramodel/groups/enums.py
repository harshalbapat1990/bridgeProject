from enum import Enum

class StructuralComponentTypeParaModel(str, Enum):
    BRIDGE = "bridge"
    SUPERSTRUCTURE = "superstructure"
    SPAN = "span"
    LONGITUDINAL_MEMBERS = "longitudinal-members"
    GIRDER = "girder"
    REINFORCEMENT_GROUP = "reinforcement-group"
    PRIMARY_REINFORCEMENT = "primary-reinforcement"
    SECONDARY_REINFORCEMENT = "secondary-reinforcement"
    SHEAR_REINFORCEMENT = "shear-reinforcement"
    TENDON_GROUP = "tendon-group"
    INDIVIDUAL_TENDON = "individual-tendon"
    EDGE_BEAM = "edge-beam"
    TRANSVERSE_MEMBERS = "transverse-members"
    DECK_SLAB = "deck-slab"
    DIAPHRAGM = "diaphragm"
    TRANSVERSE_BRACING = "transverse-bracing"
    BRACE = "brace"
    CHORD = "chord"
    PLAN_BRACING = "plan-bracing"
    SUBSTRUCTURE = "substructure"
    SUPPORT = "support"
    ABOVE_GROUND = "above-ground"
    VERTICAL_MEMBERS = "vertical-members"
    PIER = "pier"
    WALL = "wall"
    HORIZONTAL_MEMBERS = "horizontal-members"
    CROSSBEAM = "crossbeam"
    BELOW_GROUND = "below-ground"
    PILE = "pile"
    PILE_CAP = "pile-cap"
    GROUND_BEAM = "ground-beam"
    SPREAD_FOOTING = "spread-footing"
    LINKAGE = "linkage"
    SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS = "superstructure-to-substructure-connections"
    SUBSTRUCTURE_CONNECTIONS = "substructure-connections"
    SUPERSTRUCTURE_CONNECTIONS = "superstructure-connections"
    DECK_SLAB_CONNECTIONS = "deck-slab-connections"
    BRACING_CONNECTIONS = "bracing-connections"
    PLAN_BRACING_CONNECTIONS = "plan-bracing-connections"
    TRANSVERSE_BRACING_CONNECTIONS = "transverse-bracing-connections"

class BridgeTypeParaModel(str, Enum):
    STEEL_COMPOSITE = "Steel Composite"
    PSC_BOX = "PSC Box"

class BridgeIdealisationParaModel(str, Enum):
    GRILLAGE = "grillage"
    LINE_BEAM = "line-beam"

class ElementOrientationParaModel(str, Enum):
    ORTHOGONAL = "orthogonal"
    SKEWED = "skewed"

class SpacingTypeParaModel(str, Enum):
    UNIFORM = "uniform"
    VARIABLE = "variable"

class BearingConfigurationTypeParaModel(str, Enum):
    SINGULAR = "singular"
    MULTIPLE = "multiple"

class SupportTypeParaModel(str, Enum):
    SOLID_TYPE = "solid-type"
    COLUMN_TYPE = "column-type"

class FoundationTypeParaModel(str, Enum):
    DEEP = "deep"
    SHALLOW = "shallow"

class BracingTypeParaModel(str, Enum):
    X_TYPE = "x-type"
    K_TYPE = "k-type"

class PlanBracingTypeParaModel(str, Enum):
    WARREN = "warren"
    PRATT = "pratt"
    X_TYPE = "x-type"

class DiaphragmTypeParaModel(str, Enum):
    BRACING_ENCASED = "bracing-encased"
    STEEL_GIRDER = "steel-girder"
    CONCRETE_NON_MODELLED = "concrete-non-modelled"