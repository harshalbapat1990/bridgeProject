import uuid
from dataclasses import dataclass
from enum import Enum

from bda.domain.models.submodels.geometry_group_props.bridge_properties import GroupPropertiesBase
from bda.domain.units.quantities import Length


# -------------------------
# DETAIL CLASSES
# -------------------------

class SymmetricPlaneType(str, Enum):
    START = "start"
    END = "end"

@dataclass
class SegmentDetails:
    x_start: Length


@dataclass
class TaperedDetails(SegmentDetails):
    x_end: Length
    section_id: uuid.UUID


@dataclass
class GroupPropertiesSegment(GroupPropertiesBase):
    segment_index: int
    is_tapered: bool = False
    is_cracked: bool = False
    construction_sequence_stage_index: int = 0
    symmetric_plane: SymmetricPlaneType | None = None