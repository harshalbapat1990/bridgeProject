from bda.contracts.paramodel.shared.case_insensitive_enum import CaseInsensitiveEnum

class DofTypeEnumParaModel(CaseInsensitiveEnum):
    FREE = "free"
    FIXED = "fixed"
    CUSTOM = "custom"


class FoundationModelTypeParaModel(CaseInsensitiveEnum):
    LUMPED_FOUNDATION_MODEL = "lumped_foundation_model"
    PILE_INTERACTION_MODEL = "pile_interaction_model"


class FoundationApplicationTypeEnumParaModel(CaseInsensitiveEnum):
    BEARING_BASED = "bearing_based"
    SUBSTRUCTURE_ELEMENT_BASED = "substructure_element_based"


class SoilProfileTypeEnumParaModel(CaseInsensitiveEnum):
    UNIFORM = "uniform"
    LAYERED = "layered"
