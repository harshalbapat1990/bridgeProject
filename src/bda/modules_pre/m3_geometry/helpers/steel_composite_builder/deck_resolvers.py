from __future__ import annotations

from copy import deepcopy
from typing import Dict, Iterable, List, cast

from pint.registry import Quantity

from bda.domain.enums import OffsetReference
from bda.domain.models.submodels import Element1D, GeometryGroup
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import ElementOrientation
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import (
    ConstrSequenceDetails,
    GroupPropertiesSpan,
)
from bda.domain.models.submodels.section_base import Offset
from bda.domain.models.submodels.sections import SectionStandardSolidRectangle
from bda.modules_pre.m3_geometry.helpers.tools.models import AppliedVector
from bda.modules_pre.m3_geometry.helpers.tools.models import Point
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.build_context import (
    DeckSpanData,
    SpanReferenceData,
)
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.split_span_into_transverse_elements import (
    DeckStripResult,
)
import bda.modules_pre.m3_geometry.helpers.tools.general_tools as tools


def resolve_pouring_init_vector_for_span(
    builder,
    span_props: GroupPropertiesSpan,
    span_offset: Quantity,
    span_reference_data: SpanReferenceData,
) -> AppliedVector:
    if span_props.construction_sequence_details is None:
        # Keep default behaviour consistent with deck logic without construction sequence (single stage = 0).
        return AppliedVector(
            start_point=Point(span_offset, builder.zero_length, builder.zero_length),
            vector=builder._bridge_direction_vector.perpendicular(),
        )

    match span_props.construction_sequence_details.pouring_orientation:
        case ElementOrientation.ORTHOGONAL:
            return AppliedVector(
                start_point=Point(span_offset, builder.zero_length, builder.zero_length),
                vector=builder._bridge_direction_vector.perpendicular(),
            )
        case ElementOrientation.SKEWED:
            return span_reference_data.support_i_vector
        case _:
            raise ValueError(
                f"Unrecognized type of orientation "
                f"'{span_props.construction_sequence_details.pouring_orientation}' "
                f"for deck pouring orientation."
            )


def resolve_bridge_edge_beam_segments(
    builder,
    span_deck_data: Iterable[DeckSpanData],
    y_offsets_edge_beams: Dict[int, Quantity],
) -> Dict[int, AppliedVector]:
    span_deck_data = list(span_deck_data)
    if not span_deck_data:
        return {}

    bridge_start_x = min(
        [data.span_offset for data in span_deck_data],
        key=lambda q: q.to_base_units().magnitude,
    )
    bridge_end_x = max(
        [cast(Quantity, data.span_offset + data.span_reference_data.span_length) for data in span_deck_data],
        key=lambda q: q.to_base_units().magnitude,
    )

    bridge_edge_beam_segments: Dict[int, AppliedVector] = {}
    for edge_idx in sorted(y_offsets_edge_beams.keys()):
        points: List[Point] = []
        for data in span_deck_data:
            edge_element = data.span_reference_data.edge_beam_ref_elements.get(edge_idx)
            if edge_element is None:
                continue
            points.append(Point(edge_element.node_start.X, edge_element.node_start.Y, edge_element.node_start.Z))
            points.append(Point(edge_element.node_end.X, edge_element.node_end.Y, edge_element.node_end.Z))

        if points:
            points.sort(key=lambda p: p.x.to_base_units().magnitude)
            bridge_edge_beam_segments[edge_idx] = AppliedVector.from_points(points[0], points[-1])
            continue

        # Fallback: virtual full-bridge edge beam when reference elements are unavailable.
        y = y_offsets_edge_beams[edge_idx]
        bridge_edge_beam_segments[edge_idx] = AppliedVector.from_points(
            Point(bridge_start_x, y, builder.zero_length),
            Point(bridge_end_x, y, builder.zero_length),
        )

    return bridge_edge_beam_segments


def resolve_sections_for_entire_bridge(
    builder,
    span_deck_data: Iterable[DeckSpanData],
    transverse_deck_strips: Iterable[DeckStripResult],
    deck_tolerance: Quantity,
) -> Iterable[SectionStandardSolidRectangle]:
    span_deck_data = list(span_deck_data)
    if not span_deck_data:
        return []

    deck_group = builder._require_deck_group_for_span(span_deck_data[0].span)
    deck_base_section = builder._require_deck_base_section(deck_group)

    unique_deck_widths = tools.to_sorted_unique_collection(
        [s.strip_width for s in transverse_deck_strips],
        tolerance=deck_tolerance,
    )

    sections: List[SectionStandardSolidRectangle] = []
    for idx, width in enumerate(unique_deck_widths):
        section = deepcopy(deck_base_section)
        section.dimensions.width_b = width
        section.offset = Offset(offset_reference=OffsetReference.CENTER_CENTER)
        section.name = section.name + f"_{idx+1}"
        sections.append(section)

    return sections


def resolve_deck_pouring_stage_for_element(
    builder,
    element: Element1D,
    construction_stages: ConstrSequenceDetails,
    pouring_init_vector: AppliedVector,
) -> int:
    x_elem = element.mid_point.X
    y_elem = element.mid_point.Y

    stages = sorted(
        construction_stages.segments,
        key=lambda segment: segment.x_start.to_base_units().magnitude,
    )

    def projected_x(y_point: Quantity, vector: AppliedVector) -> Quantity:
        v0 = vector.start_point
        vx = vector.vector.x
        vy = vector.vector.y

        t = (y_point - v0.y) / vy
        return v0.x + t * vx

    for idx, stage in enumerate(stages):
        # Segment starts are span-local; convert to global X using span start from pouring_init_vector.
        stage_global_x = cast(Quantity, pouring_init_vector.start_point.x + stage.x_start)
        pouring_vector = pouring_init_vector.move_to(
            Point(stage_global_x, builder.zero_length, builder.zero_length)
        )
        proj_elem_x = projected_x(y_elem, pouring_vector)
        if x_elem <= proj_elem_x:
            return idx

    return len(stages)


def resolve_deck_segment_for_element_by_node_connectivity(
    element: Element1D,
    segments: Iterable[GeometryGroup]) -> GeometryGroup | None:
    segments = list(segments)

    for segment in segments:
        elements = segment.analytical_typology.elements
        for seg_elem in elements:
            if not isinstance(seg_elem, Element1D):
                continue
            if (element.node_start == seg_elem.node_start
                    or element.node_start == seg_elem.node_end
                    or element.node_end == seg_elem.node_start
                    or element.node_end == seg_elem.node_end):
                return segment

    return None