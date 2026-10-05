from enum import Enum

__all__ = ["OffsetReference", "SectionFamily", "SectionType", "TaperVariation"]

class SectionType(str, Enum):
    ANGLE = "angle"
    I_SECTION = "i-section"
    BOX = "box"
    CHANNEL = "channel"
    SOLID_RECTANGLE = "solid rectangle"
    SOLID_ROUND = "solid circle"
    PIPE = "pipe"
    STEEL_I_SYMMETRIC = "composite I symmetric"
    STEEL_I_ASYMMETRIC = "composite I asymmetric"
    PSC_VALUE = "psc value"
    PSC_1CELL = "psc 1cell"
    PSC_2CELL = "psc 2cell"

class SectionFamily(str, Enum):
    DB = "db"
    STANDARD_SHAPE = "standard shape"
    COMPOSITE = "composite"
    PSC = "psc"
    TAPERED = "tapered"

class OffsetReference(str, Enum):
    CENTER_TOP = "center-top"
    LEFT_TOP = "left-top"
    RIGHT_TOP = "right-top"
    CENTER_CENTER = "center-center"
    LEFT_CENTER = "left-center"
    RIGHT_CENTER = "right-center"
    CENTER_BOTTOM = "center-bottom"
    LEFT_BOTTOM = "left-bottom"
    RIGHT_BOTTOM = "right-bottom"

class TaperVariation(str, Enum):
    LINEAR = "linear"
    PARABOLIC = "parabolic"
    CUBIC = "cubic"