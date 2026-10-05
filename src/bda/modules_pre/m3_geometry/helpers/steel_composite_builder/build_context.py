from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, Tuple, List, Optional, Iterable

from pint.registry import Quantity

from bda.application.interfaces.logging import IAppLogger
from bda.domain import AnalyticalMultiModel
from bda.domain.models.submodels import Element1D
from bda.domain.models.submodels.geometry_group import GeometryGroup
from bda.domain.models.submodels.geometry_group_props.bridge_properties import GroupPropertiesBridge
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import ElementOrientation
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import (
    GroupPropertiesSpan,
    CrackedExtentsDetails,
    SpliceDetails,
    ConstrSequenceDetails,
)
from bda.modules_pre.m3_geometry.helpers.tools.models import AppliedVector
from bda.modules_pre.m3_geometry.helpers.tools.managers import ElementsManager
from bda.modules_pre.m3_geometry.helpers.tools.managers.nodes_manager import NodesManager
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.split_span_into_transverse_elements import DeckStripResult

if TYPE_CHECKING:
    from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.geometry_builder import (
        GeometrySteelCompositeBuilder,
    )
    from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.split_span_into_girder_segments_ import (
        GirderSegmentResult,
    )


@dataclass
class GeometrySteelCompositeBuildContext:
    amm: AnalyticalMultiModel
    logger: IAppLogger
    nodes_manager: NodesManager
    elements_manager: ElementsManager
    builder: GeometrySteelCompositeBuilder

    geometry: GeometryGroup | None = None
    spans: Iterable[GeometryGroup] = field(default_factory=list)
    support_angles: Dict[int, Quantity] = field(default_factory=dict)
    y_offsets_girders: Dict[int, Quantity] = field(default_factory=dict)
    y_offsets_edge_beams: Dict[int, Quantity] = field(default_factory=dict)
    grillage_type: ElementOrientation = ElementOrientation.SKEWED
    all_x_values_girders: Dict[int, list[Quantity]] = field(default_factory=dict)
    bridge_properties: GroupPropertiesBridge | None = None
    girder_mesh_divisor: int | None = None
    span_states: list[SpanBuildState] = field(default_factory=list)
    deck_spans_data: list[DeckSpanData] = field(default_factory=list)


@dataclass
class SpanReferenceData:
    span_length: Quantity
    support_i_vector: AppliedVector
    support_j_vector: AppliedVector
    girder_ref_elements: Dict[int, Element1D]
    edge_beam_ref_elements: Dict[int, Element1D]
    transverse_bracings_ref_elements: Dict[Tuple[int, int], List[Element1D]]
    diaphragms_ref_elements: Dict[int, List[Element1D]]


@dataclass
class DeckSpanData:
    span: GeometryGroup
    span_props: GroupPropertiesSpan
    span_offset: Quantity
    span_reference_data: SpanReferenceData
    transverse_deck_strips: List[DeckStripResult]


@dataclass
class SpanBuildState:
    span: GeometryGroup
    span_props: GroupPropertiesSpan
    span_offset: Quantity
    span_reference_data: SpanReferenceData
    cracked_extents: List[CrackedExtentsDetails] = field(default_factory=list)
    include_splice: bool = True
    splices: List[SpliceDetails] = field(default_factory=list)
    construction_sequence_details: Optional[ConstrSequenceDetails] = None
    transverse_deck_strips: List[DeckStripResult] = field(default_factory=list)
    bracing_breakpoints: Dict[int, List[Quantity]] = field(default_factory=dict)
    girder_segments: Dict[int, List["GirderSegmentResult"]] = field(default_factory=dict)
    elements_per_girder: Dict[int, List[Element1D]] = field(default_factory=dict)


