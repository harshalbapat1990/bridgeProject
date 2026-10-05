from bda.contracts.paramodel.shared.case_insensitive_enum import CaseInsensitiveEnum

class ModelUnitSystemEnum(CaseInsensitiveEnum):
    METRIC = "Metric"
    US_CUSTOMARY = "US Customary"

class OutputSoftwareEnum(CaseInsensitiveEnum):
    MIDAS_CIVIL = "MIDAS Civil"
    CSI_BRIDGE = "CSI Bridge"

class DesignCodesEnum(CaseInsensitiveEnum):
    AASHTO = "AASHTO"
    EUROCODE = "Eurocode"

class StructureTypeEnum(CaseInsensitiveEnum):
    STEEL_COMPOSITE = "Steel Composite"
    PSC_BOX = "PSC Box"