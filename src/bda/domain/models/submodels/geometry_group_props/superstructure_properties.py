from __future__ import annotations

import uuid
from abc import ABC
from dataclasses import dataclass, field
from typing import List, Optional, Union

from bda.domain.models.submodels.geometry_group_props.shared import SegmentDetails, TaperedDetails
from bda.domain.models.submodels.geometry_group import GroupPropertiesBase
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import (
    SpacingType,
    ElementOrientation,
    DiaphragmType,
    BracingType,
    PlanBracingType,
)
from bda.domain.units.quantities import Length


# -------------------------
# DETAIL CLASSES
# -------------------------

@dataclass
class CrackedExtentsDetails:
    x_start: Length
    x_end: Length


@dataclass
class SpliceDetails:
    x_start: Length
    section_id: uuid.UUID


@dataclass
class ConstrSequenceDetails:
    segments: List[SegmentDetails]
    pouring_orientation: ElementOrientation


@dataclass
class TransverseBracingDetails:
    horizontal_offset_at_left: Length
    horizontal_offset_at_right: Length


@dataclass
class DiaphragmDetailsBase(ABC):
    diaphragm_type: DiaphragmType


@dataclass
class DiaphragmConcreteNonModelledDetails(DiaphragmDetailsBase):
    diaphragm_type: DiaphragmType = field(
        init=False,
        default=DiaphragmType.CONCRETE_NON_MODELLED
    )
    diaphragm_thickness: Length


@dataclass
class DiaphragmSteelGirderDetails:
    diaphragm_type: DiaphragmType = field(
        init=False,
        default=DiaphragmType.STEEL_GIRDER
    )


@dataclass
class DiaphragmBracingEncasedDetails:
    diaphragm_type: DiaphragmType = field(
        init=False,
        default=DiaphragmType.BRACING_ENCASED
    )


DiaphragmDetails = Union[
    DiaphragmConcreteNonModelledDetails,
    DiaphragmSteelGirderDetails,
    DiaphragmBracingEncasedDetails,
]


@dataclass
class BracingBraceDetailsBase(ABC):
    bracing_type: BracingType
    vertical_offset_left_top: Length
    vertical_offset_right_top: Length
    vertical_offset_left_bottom: Length
    vertical_offset_right_bottom: Length

@dataclass
class BracingBraceXtypeDetails(BracingBraceDetailsBase):
    bracing_type: BracingType = field(
        init=False,
        default=BracingType.X_TYPE
    )

@dataclass
class BracingBraceKtypeDetails(BracingBraceDetailsBase):
    bracing_type: BracingType = field(
        init=False,
        default=BracingType.K_TYPE
    )
    horizontal_offset_right_brace: Length
    horizontal_offset_left_brace: Length


BracingBraceDetails = Union[BracingBraceXtypeDetails, BracingBraceKtypeDetails]


# -------------------------
# PROPERTIES CLASSES
# -------------------------

@dataclass
class GroupPropertiesSuperstructure(GroupPropertiesBase):
    total_deck_width: Length
    no_of_girders: int
    girder_spacing_type: SpacingType
    girder_spacing_values: List[Length]
    stringcourse_left_barrier_width: Length
    stringcourse_right_barrier_width: Length
    cantilever_left_width: Length
    cantilever_right_width: Length


@dataclass
class GroupPropertiesSpan(GroupPropertiesBase):
    span_index: int
    span_length: Length
    top_deck_level_at_end: Length
    cracked_extends: Optional[List[CrackedExtentsDetails]]
    tapered_details: Optional[List[TaperedDetails]]
    splices: Optional[List[SpliceDetails]]
    construction_sequence_details: Optional[ConstrSequenceDetails]


@dataclass
class GroupPropertiesGirder(GroupPropertiesBase):
    girder_index: int

@dataclass
class GroupPropertiesEdgeBeam(GroupPropertiesBase):
    edge_beam_index: int


@dataclass
class GroupPropertiesDiaphragm(GroupPropertiesBase):
    support_index: int
    geometry_details: DiaphragmDetails


@dataclass
class GroupPropertiesTransverseBracing(GroupPropertiesBase):
    bracing_orientation: ElementOrientation
    x_position_at_start_girder: Length
    spacing_type: SpacingType
    spacing_values: List[Length]
    no_of_bracings: int
    left_girder_index: int
    right_girder_index: int
    bracing_details: TransverseBracingDetails


@dataclass
class GroupPropertiesBrace(GroupPropertiesBase):
    geometry_details: BracingBraceDetails


@dataclass
class GroupPropertiesChord(GroupPropertiesBase):
    vertical_offset_at_left: Length
    vertical_offset_at_right: Length


@dataclass
class GroupPropertiesPlanBracing(GroupPropertiesBase):
    plan_bracing_type: PlanBracingType
    left_girder_index: int
    right_girder_index: int
