"""Assignment of deck finite elements into SEGMENT groups (per pouring stage
and cross-section) plus deck-to-girder rigid links."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Tuple, cast
from uuid import UUID

from pint.registry import Quantity

from bda.domain.enums import StructuralComponentType
from bda.domain.models.submodels import Element1D, GeometryGroup
from bda.domain.models.submodels.element import LinkType
from bda.domain.models.submodels.geometry_group_props.shared import GroupPropertiesSegment
from bda.domain.models.submodels.sections import SectionStandardSolidRectangle
import bda.modules_pre.m3_geometry.helpers.tools.general_tools as tools
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.context import (
    BuildContext,
    SpanState,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.deck.boundary import (
    generate_deck_boundary_elements_for_bridge_end,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.deck.resolvers import (
    resolve_deck_pouring_stage_for_element,
    resolve_deck_segment_for_element_by_node_connectivity,
    resolve_pouring_init_vector_for_span,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.group_property_getters import (
    require_deck_base_section,
    require_deck_group_for_span,
    require_segment_properties,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.node_utils import are_same_node


def assign_deck_segment_groups(
    ctx: BuildContext,
    state: SpanState,
    deck_elements_by_section_uid: Dict[UUID, List[Element1D]],
    sections: List[SectionStandardSolidRectangle],
) -> None:
    # Segment boundaries are precomputed from deck pouring stages and deck cross-section.
    elements_by_stage_and_section_uid: Dict[Tuple[int, UUID], List[Element1D]] = defaultdict(list)

    construction_sequence = state.span_props.construction_sequence_details
    if construction_sequence is None:
        for cross_section_uid, elements in deck_elements_by_section_uid.items():
            for element in elements:
                if not ctx.claim_deck_element(element):
                    continue
                elements_by_stage_and_section_uid[0, cross_section_uid].append(element)
    else:
        pouring_init_vector = resolve_pouring_init_vector_for_span(ctx, state)

        for cross_section_uid, elements in deck_elements_by_section_uid.items():
            for element in elements:
                if not ctx.claim_deck_element(element):
                    continue
                pouring_stage: int = resolve_deck_pouring_stage_for_element(
                    ctx,
                    element=element,
                    construction_stages=construction_sequence,
                    pouring_init_vector=pouring_init_vector,
                )
                elements_by_stage_and_section_uid[pouring_stage, cross_section_uid].append(element)

    deck_group = require_deck_group_for_span(ctx, state.span)

    segment_entries: List[Tuple[float, int, UUID, List[Element1D]]] = []
    for (stage_idx, section_uid), elements in elements_by_stage_and_section_uid.items():
        x_anchor = min(element.mid_point.X.to_base_units().magnitude for element in elements)
        segment_entries.append((x_anchor, stage_idx, section_uid, elements))

    # Order segments by pouring stage first, then by X anchor within the stage.
    for idx, (_, stage_idx, section_uid, elements) in enumerate(
        sorted(segment_entries, key=lambda entry: (entry[1], entry[0]))
    ):
        segment = GeometryGroup(
            component_type=StructuralComponentType.SEGMENT,
            name=f"Span_{state.span_props.span_index}_DeckSegment_{idx}_PouringStage_{stage_idx}",
            properties=GroupPropertiesSegment(
                segment_index=idx,
                construction_sequence_stage_index=stage_idx,
            ),
        )

        segment.section = next((section for section in sections if section.guid == section_uid), None)
        for element in elements:
            ctx.amm.add_element(segment, element)

        add_deck_to_girder_links_for_elements(
            ctx,
            segment=segment,
            elements=elements,
            girder_y_values=ctx.y_offsets_girders.values(),
        )

        deck_group.add_nested_group(segment)


def assign_deck_boundary_elements_group_for_bridge_end(
    ctx: BuildContext,
    state: SpanState,
    is_bridge_start: bool,
) -> None:
    deck_group = require_deck_group_for_span(ctx, state.span)
    deck_vertical_offset = cast(
        Quantity,
        require_deck_base_section(deck_group).dimensions.height_h / 2,
    )

    boundary_elements, strip_extension_elements = generate_deck_boundary_elements_for_bridge_end(
        ctx,
        span_reference_data=state.reference_data,
        transverse_deck_strips=state.transverse_deck_strips,
        deck_vertical_offset=deck_vertical_offset,
        is_bridge_start=is_bridge_start,
    )
    if not boundary_elements and not strip_extension_elements:
        return

    boundary_elements_by_stage: Dict[int, List[Element1D]] = defaultdict(list)
    strip_extension_elements_by_stage: Dict[int, List[Element1D]] = defaultdict(list)
    construction_sequence = state.span_props.construction_sequence_details
    if construction_sequence is None:
        boundary_elements_by_stage[0].extend(boundary_elements)
        strip_extension_elements_by_stage[0].extend(strip_extension_elements)
    else:
        stage_pouring_vector = resolve_pouring_init_vector_for_span(ctx, state)
        for element in boundary_elements:
            stage = resolve_deck_pouring_stage_for_element(
                ctx,
                element=element,
                construction_stages=construction_sequence,
                pouring_init_vector=stage_pouring_vector,
            )
            boundary_elements_by_stage[stage].append(element)
        for element in strip_extension_elements:
            stage = resolve_deck_pouring_stage_for_element(
                ctx,
                element=element,
                construction_stages=construction_sequence,
                pouring_init_vector=stage_pouring_vector,
            )
            strip_extension_elements_by_stage[stage].append(element)

    existing_segments = [
        segment
        for segment in deck_group.get_groups_by_component_type(StructuralComponentType.SEGMENT)
        if isinstance(segment.properties, GroupPropertiesSegment)
    ]
    if not existing_segments:
        return

    girder_y_values = [
        girder.node_start.Y
        for girder in state.reference_data.girder_ref_elements.values()
    ]

    _assign_end_elements_to_segments(
        ctx,
        elements_by_stage=strip_extension_elements_by_stage,
        existing_segments=existing_segments,
        deck_vertical_offset=deck_vertical_offset,
        girder_y_values=girder_y_values,
        is_bridge_start=is_bridge_start,
    )
    _assign_end_elements_to_segments(
        ctx,
        elements_by_stage=boundary_elements_by_stage,
        existing_segments=existing_segments,
        deck_vertical_offset=deck_vertical_offset,
        girder_y_values=girder_y_values,
        is_bridge_start=is_bridge_start,
    )


def _assign_end_elements_to_segments(
    ctx: BuildContext,
    elements_by_stage: Dict[int, List[Element1D]],
    existing_segments: List[GeometryGroup],
    deck_vertical_offset: Quantity,
    girder_y_values: List[Quantity],
    is_bridge_start: bool,
) -> None:
    """Attach bridge-end elements to matching deck segments (by stage, then connectivity)."""
    for stage_idx, elements in sorted(elements_by_stage.items(), key=lambda item: item[0]):
        stage_segments = [
            segment
            for segment in existing_segments
            if require_segment_properties(segment).construction_sequence_stage_index == stage_idx
        ]
        if not stage_segments:
            stage_segments = existing_segments

        target_segment_fallback = min(
            stage_segments,
            key=lambda segment: require_segment_properties(segment).segment_index,
        ) if is_bridge_start else max(
            stage_segments,
            key=lambda segment: require_segment_properties(segment).segment_index,
        )

        normalized_elements = [
            normalize_element_to_vertical_offset(ctx, element, deck_vertical_offset)
            for element in elements
        ]

        for e in normalized_elements:
            if not ctx.claim_deck_element(e):
                continue

            target_segment = resolve_deck_segment_for_element_by_node_connectivity(e, stage_segments)
            if target_segment is None:
                target_segment = target_segment_fallback

            ctx.amm.add_element(target_segment, e)
            add_deck_to_girder_links_for_elements(
                ctx,
                segment=target_segment,
                elements=[e],
                girder_y_values=girder_y_values,
            )


def add_deck_to_girder_links_for_elements(
    ctx: BuildContext,
    segment: GeometryGroup,
    elements: Iterable[Element1D],
    girder_y_values: Iterable[Quantity],
) -> None:
    """Attach rigid links for deck nodes that lie directly above girders."""
    y_tol = ctx.tolerance
    y_values = list(girder_y_values)

    for element in elements:
        for node in (element.node_start, element.node_end):
            if not any(tools.is_close(node.Y, girder_y, y_tol) for girder_y in y_values):
                continue

            girder_node = ctx.amm.get_or_create_node(node.X, node.Y, ctx.zero_length)
            if are_same_node(node, girder_node):
                continue

            ctx.amm.create_and_add_link(segment, node, girder_node, LinkType.RIGID)


def normalize_element_to_vertical_offset(
    ctx: BuildContext,
    element: Element1D,
    vertical_offset: Quantity,
) -> Element1D:
    """Rebuild element so both end nodes are guaranteed on deck vertical offset."""
    node_start = ctx.amm.get_or_create_node(
        element.node_start.X,
        element.node_start.Y,
        vertical_offset,
    )
    node_end = ctx.amm.get_or_create_node(
        element.node_end.X,
        element.node_end.Y,
        vertical_offset,
    )
    return ctx.amm.get_or_create_beam(node_start, node_end)
