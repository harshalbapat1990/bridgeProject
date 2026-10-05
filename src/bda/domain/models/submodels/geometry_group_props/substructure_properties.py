from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import List, Union

from bda.domain.models.submodels.geometry_group_props.shared import TaperedDetails
from bda.domain.models.submodels.geometry_group import GroupPropertiesBase
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import (
    SupportType,
    FoundationType,
    ElementOrientation,
)
from bda.domain.units.quantities import Length, Angle


# -------------------------
# DETAIL CLASSES
# -------------------------

@dataclass
class AboveGroundDetailsBase(ABC):
    support_type: SupportType


@dataclass
class AboveGroundDetailsSolid:
    support_type: SupportType = field(
        init=False,
        default=SupportType.SOLID_TYPE
    )
    no_of_walls: int


@dataclass
class AboveGroundDetailsColumn:
    support_type: SupportType = field(
        init=False,
        default=SupportType.COLUMN_TYPE
    )
    no_of_piers: int


AboveGroundDetails = Union[AboveGroundDetailsSolid, AboveGroundDetailsColumn]


@dataclass
class FoundationDetailsBase(ABC):
    foundation_type: FoundationType


@dataclass
class DeepFoundationDetails(FoundationDetailsBase):
    foundation_type: FoundationType = field(
        init=False,
        default=FoundationType.DEEP
    )
    no_of_piles: int


@dataclass
class ShallowFoundationDetails(FoundationDetailsBase):
    foundation_type: FoundationType = field(
        init=False,
        default=FoundationType.SHALLOW
    )


FoundationDetails = Union[DeepFoundationDetails, ShallowFoundationDetails]


# -------------------------
# PROPERTIES CLASSES
# -------------------------

@dataclass
class GroupPropertiesSupport(GroupPropertiesBase):
    support_index: int
    skew_angle: Angle
    bearing_underside_level: Length
    orientation: ElementOrientation


@dataclass
class GroupPropertiesAboveGround(GroupPropertiesBase):
    details: AboveGroundDetails


@dataclass
class GroupPropertiesPier(GroupPropertiesBase):
    transverse_offset: Length


@dataclass
class GroupPropertiesWall(GroupPropertiesBase):
    element_thickness: Length


@dataclass
class GroupPropertiesCrossbeam(GroupPropertiesBase):
    element_length: Length
    tapered_details: List[TaperedDetails]


@dataclass
class GroupPropertiesBelowGround(GroupPropertiesBase):
    foundation_details: FoundationDetails


@dataclass
class GroupPropertiesPile(GroupPropertiesBase):
    pile_index: int
    pile_length: Length
    offset_along_support_line: Length
    offset_normal_to_support_line: Length
    spring_spacing: List[Length]


@dataclass
class GroupPropertiesPileCap(GroupPropertiesBase):
    top_of_pile_cap_level: Length
    element_length: Length
