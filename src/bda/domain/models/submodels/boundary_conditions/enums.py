from enum import Enum


class DofTypeEnum(str, Enum):
    FREE = "free"
    FIXED = "fixed"
    CUSTOM = "custom"


class FoundationModelType(str, Enum):
    LUMPED_FOUNDATION_MODEL = "lumped_foundation_model"
    PILE_INTERACTION_MODEL = "pile_interaction_model"


class FoundationApplicationType(str, Enum):
    BEARING_BASED = "bearing_based"
    SUBSTRUCTURE_ELEMENT_BASED = "substructure_element_based"


class SoilProfileType(str, Enum):
    UNIFORM = "uniform"
    LAYERED = "layered"
