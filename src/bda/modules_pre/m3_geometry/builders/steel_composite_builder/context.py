from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID

from pint.registry import Quantity

from bda.application.interfaces.logging import IAppLogger
from bda.domain import AnalyticalMultiModel
from bda.domain.models.submodels import Element1D
from bda.domain.models.submodels.geometry_group import GeometryGroup
from bda.domain.models.submodels.geometry_group_props.bridge_properties import GroupPropertiesBridge
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import ElementOrientation
from bda.domain.models.submodels.geometry_group_props.substructure_properties import GroupPropertiesSupport
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import (
    ConstrSequenceDetails,
    CrackedExtentsDetails,
    GroupPropertiesSpan,
    SpliceDetails,
)
from bda.domain.models.submodels.material import Material
from bda.domain.models.submodels.section_base import Section
from bda.modules_pre.m3_geometry.helpers.tools.models import AppliedVector, Vector
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.meshing.girder_segments import (
    GirderSegmentResult,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.meshing.transverse_strips import (
    DeckStripResult,
)


@dataclass
class SpanReferenceData:
    """Reference geometry of a single span resolved before FE generation."""

    span_length: Quantity
    support_i_vector: AppliedVector
    support_j_vector: AppliedVector
    girder_ref_elements: Dict[int, Element1D]
    edge_beam_ref_elements: Dict[int, Element1D]
    transverse_bracings_ref_elements: Dict[Tuple[int, int], List[Element1D]]
    diaphragms_ref_elements: Dict[int, List[Element1D]]


@dataclass
class SpanState:
    """Per-span working data shared and enriched by consecutive build phases."""

    span: GeometryGroup
    span_props: GroupPropertiesSpan
    span_offset: Quantity
    reference_data: SpanReferenceData
    construction_sequence_details: Optional[ConstrSequenceDetails] = None
    include_splice: bool = True
    splices: List[SpliceDetails] = field(default_factory=list)
    cracked_extents: List[CrackedExtentsDetails] = field(default_factory=list)
    transverse_deck_strips: List[DeckStripResult] = field(default_factory=list)
    bracing_breakpoints: Dict[int, List[Quantity]] = field(default_factory=dict)
    girder_segments: Dict[int, List[GirderSegmentResult]] = field(default_factory=dict)
    elements_per_girder: Dict[int, List[Element1D]] = field(default_factory=dict)

    @property
    def span_end_offset(self) -> Quantity:
        return self.span_offset + self.reference_data.span_length

@dataclass
class SupportBuildState:
    support: GeometryGroup
    support_properties: GroupPropertiesSupport
    support_vector: AppliedVector
    angle: Quantity
    bearing_underside_relative_level: Quantity

@dataclass
class BuildContext:
    """State shared by all build phases; topology is created via ``amm``."""

    amm: AnalyticalMultiModel
    logger: IAppLogger
    tolerance: Quantity
    zero_length: Quantity
    bridge_direction_vector: Vector

    geometry: GeometryGroup | None = None
    spans: List[GeometryGroup] = field(default_factory=list)
    support_angles: Dict[int, Quantity] = field(default_factory=dict)
    bridge_properties: GroupPropertiesBridge | None = None
    girder_mesh_divisor: int | None = None
    grillage_type: ElementOrientation = ElementOrientation.SKEWED
    y_offsets_girders: Dict[int, Quantity] = field(default_factory=dict)
    y_offsets_edge_beams: Dict[int, Quantity] = field(default_factory=dict)
    span_states: List[SpanState] = field(default_factory=list)
    dummy_section: Section | None = None
    weightless_materials: Dict[UUID, Material] = field(default_factory=dict)

    # Deck elements shared by two spans (skewed supports) belong to the span claiming them first.
    assigned_deck_element_uids: Set[UUID] = field(default_factory=set)

    def claim_deck_element(self, element: Element1D) -> bool:
        """Return True when the element is not owned by any deck segment group yet."""
        if element.uid in self.assigned_deck_element_uids:
            return False
        self.assigned_deck_element_uids.add(element.uid)
        return True

    def require_geometry(self) -> GeometryGroup:
        if self.geometry is None:
            raise ValueError("Build context has no geometry.")
        return self.geometry

    def require_girder_mesh_divisor(self) -> int:
        if self.girder_mesh_divisor is None:
            raise ValueError("Build context has no girder mesh divisor.")
        return self.girder_mesh_divisor
