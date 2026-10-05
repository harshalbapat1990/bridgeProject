"""Deck resolvers: pouring vectors, deck cross-sections, bridge-long edge-beam
segments and pouring-stage classification of elements."""
from __future__ import annotations

from copy import deepcopy
from typing import Dict, Iterable, List, cast

from pint.registry import Quantity

from bda.domain.enums import OffsetReference
from bda.domain.models.submodels import Element1D, GeometryGroup
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import ElementOrientation
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import (
    ConstrSequenceDetails,
)
from bda.domain.models.submodels.section_base import Offset
from bda.domain.models.submodels.sections import SectionStandardSolidRectangle
import bda.modules_pre.m3_geometry.helpers.tools.general_tools as tools
from bda.modules_pre.m3_geometry.helpers.tools.models import AppliedVector, Point
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.context import (
    BuildContext,
    SpanState,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.group_property_getters import (
    require_deck_base_section,
    require_deck_group_for_span,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.meshing.transverse_strips import (
    DeckStripResult,
)


def resolve_pouring_init_vector_for_span(ctx: BuildContext, state: SpanState) -> AppliedVector:
    construction_sequence = state.span_props.construction_sequence_details
    if construction_sequence is None:
        # Keep default behaviour consistent with deck logic without construction sequence (single stage = 0).
        return AppliedVector(
            start_point=Point(state.span_offset, ctx.zero_length, ctx.zero_length),
            vector=ctx.bridge_direction_vector.perpendicular(),
        )

    match construction_sequence.pouring_orientation:
        case ElementOrientation.ORTHOGONAL:
            return AppliedVector(
                start_point=Point(state.span_offset, ctx.zero_length, ctx.zero_length),
                vector=ctx.bridge_direction_vector.perpendicular(),
            )
        case ElementOrientation.SKEWED:
            return state.reference_data.support_i_vector
        case _:
            raise ValueError(
                f"Unrecognized type of orientation "
                f"'{construction_sequence.pouring_orientation}' "
                f"for deck pouring orientation."
            )


def resolve_bridge_edge_beam_segments(
    ctx: BuildContext,
    span_states: Iterable[SpanState],
) -> Dict[int, AppliedVector]:
    span_states = list(span_states)
    if not span_states:
        return {}

    bridge_start_x = min(
        [state.span_offset for state in span_states],
        key=lambda q: q.to_base_units().magnitude,
    )
    bridge_end_x = max(
        [cast(Quantity, state.span_end_offset) for state in span_states],
        key=lambda q: q.to_base_units().magnitude,
    )

    bridge_edge_beam_segments: Dict[int, AppliedVector] = {}
    for edge_idx in sorted(ctx.y_offsets_edge_beams.keys()):
        points: List[Point] = []
        for state in span_states:
            edge_element = state.reference_data.edge_beam_ref_elements.get(edge_idx)
            if edge_element is None:
                continue
            points.append(Point(edge_element.node_start.X, edge_element.node_start.Y, edge_element.node_start.Z))
            points.append(Point(edge_element.node_end.X, edge_element.node_end.Y, edge_element.node_end.Z))

        if points:
            points.sort(key=lambda p: p.x.to_base_units().magnitude)
            bridge_edge_beam_segments[edge_idx] = AppliedVector.from_points(points[0], points[-1])
            continue

        # Fallback: virtual full-bridge edge beam when reference elements are unavailable.
        y = ctx.y_offsets_edge_beams[edge_idx]
        bridge_edge_beam_segments[edge_idx] = AppliedVector.from_points(
            Point(bridge_start_x, y, ctx.zero_length),
            Point(bridge_end_x, y, ctx.zero_length),
        )

    return bridge_edge_beam_segments


def resolve_sections_for_entire_bridge(
    ctx: BuildContext,
    span_states: Iterable[SpanState],
    transverse_deck_strips: Iterable[DeckStripResult],
    deck_tolerance: Quantity,
) -> List[SectionStandardSolidRectangle]:
    span_states = list(span_states)
    if not span_states:
        return []

    deck_group = require_deck_group_for_span(ctx, span_states[0].span)
    deck_base_section = require_deck_base_section(deck_group)

    unique_deck_widths = tools.to_sorted_unique_collection(
        [s.strip_width for s in transverse_deck_strips],
        tolerance=deck_tolerance,
    )

    sections: List[SectionStandardSolidRectangle] = []
    for idx, width in enumerate(unique_deck_widths):
        section = deepcopy(deck_base_section)
        section.dimensions.width_b = width
        section.offset = Offset(offset_reference=OffsetReference.CENTER_CENTER)
        section.name = section.name + f"_{idx + 1}"
        sections.append(section)

    return sections


def resolve_deck_pouring_stage_for_element(
    ctx: BuildContext,
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
            Point(stage_global_x, ctx.zero_length, ctx.zero_length)
        )
        proj_elem_x = projected_x(y_elem, pouring_vector)
        if x_elem <= proj_elem_x:
            return idx

    return len(stages)


def resolve_deck_segment_for_element_by_node_connectivity(
    element: Element1D,
    segments: Iterable[GeometryGroup],
) -> GeometryGroup | None:
    for segment in segments:
        for seg_elem in segment.analytical_typology.elements:
            if not isinstance(seg_elem, Element1D):
                continue
            if (element.node_start == seg_elem.node_start
                    or element.node_start == seg_elem.node_end
                    or element.node_end == seg_elem.node_start
                    or element.node_end == seg_elem.node_end):
                return segment

    return None
