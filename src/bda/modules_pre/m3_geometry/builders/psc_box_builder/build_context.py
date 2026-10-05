from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List
from uuid import UUID

from pint.registry import Quantity

from bda.application.interfaces import IAppLogger
from bda.domain import AnalyticalMultiModel
from bda.domain.models.submodels import GeometryGroup, Element1D, SectionBase
from bda.domain.models.submodels.geometry_group_props.linkage_properties import GroupPropertiesLinkageSupToSub
from bda.domain.models.submodels.geometry_group_props.shared import TaperedDetails
from bda.domain.models.submodels.geometry_group_props.substructure_properties import GroupPropertiesSupport, \
    GroupPropertiesPier, GroupPropertiesPile, GroupPropertiesPileCap, GroupPropertiesCrossbeam
from bda.domain.models.submodels.material import Material
from bda.domain.models.submodels.node import Node
from bda.domain.models.submodels.geometry_group_props.bridge_properties import GroupPropertiesBridge
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import GroupPropertiesSpan
from bda.modules_pre.m3_geometry.builders.psc_box_builder.split_span_into_segments_ import SpanSegmentResult
from bda.domain.models.submodels.sections import SectionPSCValue
from bda.modules_pre.m3_geometry.helpers.tools.models import AppliedVector, Point

if TYPE_CHECKING:
    from bda.modules_pre.m3_geometry.builders.psc_box_builder.geometry_builder import GeometryPSCBoxBuilder


@dataclass
class SpanReferenceData:
    span_length: Quantity
    x_offset: Quantity


@dataclass
class GirderBuildState:
    span_index: int
    girder_group: GeometryGroup


@dataclass
class SpanBuildState:
    span: GeometryGroup
    span_props: GroupPropertiesSpan
    span_offset: Quantity
    span_reference_data: SpanReferenceData
    tapered_segments: List[SpanSegmentResult] = field(default_factory=list)
    reference_element: Element1D | None = None
    finite_elements: List[Element1D] = field(default_factory=list)
    start_section: SectionPSCValue = None  # Section at x=0 of this span
    end_section: SectionPSCValue = None    # Section at x=span_length of this span
    crossbeam_nodes_by_support_index: Dict[int, List[Node]] = field(default_factory=dict)


@dataclass
class SupportBuildState:
    support: GeometryGroup
    support_properties: GroupPropertiesSupport
    support_vector: AppliedVector
    angle: Quantity
    bearing_underside_relative_level: Quantity
    is_modelled: bool
    is_abutment: bool
    pilecap_top_relative_level: Quantity | None


@dataclass
class CrossheadBuildState:
    support_index: int
    crosshead: GeometryGroup
    crosshead_properties: GroupPropertiesCrossbeam
    support_vector: AppliedVector
    tapered_details: list[TaperedDetails] = field(default_factory=list)
    tapered_segments: list[CrossheadSegmentResult] = field(default_factory=list)
    crosshead_segments: list[CrossheadSegmentResult] = field(default_factory=list)
    finite_elements: list[Element1D] = field(default_factory=list)



@dataclass
class PierBuildState:
    '''
    Represents the group of columns at each support
    '''
    support_index: int
    pier: GeometryGroup
    pier_properties: GroupPropertiesPier
    crosshead_soffit_relative_level: Quantity
    pilecap_top_relative_level: Quantity


@dataclass
class PilecapBuildState:
    '''
    Represents the pilecap under the pier support
    '''
    support_index: int
    horizontal_pilecap: GeometryGroup
    vertical_members_group: GeometryGroup | None
    pilecap_properties: GroupPropertiesPileCap
    pilecap_bottom_relative_level: Quantity


@dataclass
class PileBuildState:
    '''
    Represents the group of piles at each pier support
    '''
    support_index: int
    pile: GeometryGroup
    pile_properties: GroupPropertiesPile


@dataclass
class SupToSubBuildState:
    support_index: int
    sup_to_sub_group: GeometryGroup
    sup_to_sub_properties: GroupPropertiesLinkageSupToSub


@dataclass
class TributaryRegion:
    node: Node
    left_boundary: Quantity
    right_boundary: Quantity
    width: Quantity
    offset: Quantity


@dataclass
class CrossheadSegmentResult:
    point_start: Point #global
    point_end: Point #global
    x_start: Quantity
    x_end: Quantity
    section_id: UUID
    start_id: UUID
    end_id: UUID
    is_tapered: bool
    section: SectionBase | None


@dataclass
class GeometryPSCBoxBuildContext:
    amm: AnalyticalMultiModel
    logger: IAppLogger
    builder: GeometryPSCBoxBuilder | None = None

    geometry: GeometryGroup | None = None
    girder_mesh_divisor: int | None = None
    spans: Dict[int, GeometryGroup] = field(default_factory=dict)
    bridge_properties: GroupPropertiesBridge | None = None

    span_states: List[SpanBuildState] = field(default_factory=list)
    girder_states: Dict[int, GirderBuildState] = field(default_factory=dict)
    sup_to_sub_states: Dict[int, SupToSubBuildState] = field(default_factory=dict)
    support_states: Dict[int, SupportBuildState] = field(default_factory=dict)
    crosshead_states: Dict[int, CrossheadBuildState] = field(default_factory=dict)
    pier_states: Dict[int, List[PierBuildState]] = field(default_factory=dict)
    pilecap_states: Dict[int, PilecapBuildState] = field(default_factory=dict)
    pile_states: Dict[int, List[PileBuildState]] = field(default_factory=dict)

    weightless_materials: Dict[uuid.UUID, Material] = field(default_factory=dict)