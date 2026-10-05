from abc import ABC
from dataclasses import dataclass
from enum import Enum

from bda.domain.enums import *
from bda.domain.units.quantities import *


# -------------------------
# ENUMS
# -------------------------


class BridgeIdealisation(str, Enum):
    GRILLAGE = "grillage"
    LINE_BEAM = "line-beam"


# -------------------------
# DETAIL CLASSES
# -------------------------


@dataclass
class AnalysisSettings:
    girder_mesh_divisor: int


# -------------------------
# PROPERTIES CLASSES
# -------------------------


@dataclass
class GroupPropertiesBase(ABC):
    """
    Base class for all group properties. Implementation per StructuralComponentType.
    Discriminator is defined in the parent GeometryGroupBase.
    """
    pass


@dataclass
class GroupPropertiesBridge(GroupPropertiesBase):
    type: BridgeType
    idealisation: BridgeIdealisation
    no_of_spans: int
    analysis_settings: AnalysisSettings
    top_deck_level: Length