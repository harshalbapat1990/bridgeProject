from __future__ import annotations

from bda.contracts.paramodel.shared.case_insensitive_enum import CaseInsensitiveEnum


class LoadContextEnum(CaseInsensitiveEnum):
    DESIGN = "design"
    ASSESSMENT = "assessment"


class MainCodeEnum(CaseInsensitiveEnum):
    AASHTO = "AASHTO"
    EUROCODE = "Eurocode"


class SecondaryCodeEnum(CaseInsensitiveEnum):
    NONE = "None"
    UAE = "UAE"


class LoadApplicationDomainEnum(CaseInsensitiveEnum):
    STRUCTURE = "Structure"
    ANCILLARY_WORKS = "Ancillary works"
    LIVE_LOAD = "Live load"
    ENVIRONMENT = "Environment"
    CONSTRUCTION = "Construction"


class LoadServiceStateEnum(CaseInsensitiveEnum):
    IN_SERVICE = "In Service"
    CONSTRUCTION = "Construction"
    ACCIDENTAL = "Accidental"
    TEMPORARY = "Temporary"


class StructuralLoadTypeEnum(CaseInsensitiveEnum):
    DEAD_LOAD = "dead load"
    PRESTRESSING = "prestressing"


class DefinitionTypeEnum(CaseInsensitiveEnum):
    STANDARD = "standard"
    CUSTOM = "custom"


class TrafficLoadTypeEnum(CaseInsensitiveEnum):
    BRAKING = "braking"
    VERTICAL_TRAFFIC_DIRECT = "vertical traffic direct"


class DeadLoadingMethodEnum(CaseInsensitiveEnum):
    DENSITY_ENHANCEMENT = "density enhancement"
    DIRECT_VALUE = "direct value"


class StructuralApplicationTypeEnum(CaseInsensitiveEnum):
    STRUCTURAL_GROUP_ID = "structural group id"
    STRUCTURAL_COMPONENT_TYPE = "structural component type"


class LoadApplicationTypeEnum(CaseInsensitiveEnum):
    DECK_APPURTENANCE_ID = "deck appurtenance id"


class EnvironmentLoadTypeEnum(CaseInsensitiveEnum):
    WIND = "wind"
    TEMPERATURE = "temperature"
    EARTHQUAKE = "earthquake"
    SETTLEMENT = "settlement"


class TemperatureEffectTypeEnum(CaseInsensitiveEnum):
    UNIFORM = "uniform"
    GRADIENT = "gradient"


class ModalAnalysisTypeEnum(CaseInsensitiveEnum):
    EIGEN_VECTORS_LANCZOS = "Eigen Vectors (Lanczos)"
    RITZ_VECTORS = "Ritz Vectors"