from enum import Enum


class SpacingType(str, Enum):
    UNIFORM = "uniform"
    VARIABLE = "variable"


class ElementOrientation(str, Enum):
    ORTHOGONAL = "orthogonal"
    SKEWED = "skewed"


class DiaphragmType(str, Enum):
    BRACING_ENCASED = "bracing-encased"
    STEEL_GIRDER = "steel-girder"
    CONCRETE_NON_MODELLED = "concrete-non-modelled"


class BracingType(str, Enum):
    X_TYPE = "x-type"
    K_TYPE = "k-type"


class PlanBracingType(str, Enum):
    WARREN = "warren"
    PRATT = "pratt"
    X_TYPE = "x-type"


class SupportType(str, Enum):
    SOLID_TYPE = "solid-type"
    COLUMN_TYPE = "column-type"


class FoundationType(str, Enum):
    DEEP = "deep"
    SHALLOW = "shallow"


class BearingConfigurationType(str, Enum):
    SINGULAR = "singular"
    MULTIPLE = "multiple"

