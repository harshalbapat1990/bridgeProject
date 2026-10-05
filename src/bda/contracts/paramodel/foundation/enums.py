from bda.contracts.paramodel.shared.case_insensitive_enum import CaseInsensitiveEnum


class FoundationModelTypeEnumParaModel(CaseInsensitiveEnum):
    LumpedFoundationModel = "lumped_foundation_model"
    PileInteractionModel = "pile_interaction_model"

class SoilProfileTypeEnumParaModel(CaseInsensitiveEnum):
    UNIFORM = "uniform"


class DofTypeEnumParaModel(CaseInsensitiveEnum):
    FREE = "free"
    FIXED = "fixed"
    CUSTOM = "custom"

class FoundationApplicationTypeEnumParaModel(CaseInsensitiveEnum):
    BearingBased = "bearing_based"
    SubstructureElementBased = "substructure_element_based"