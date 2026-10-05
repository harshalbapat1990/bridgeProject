from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Tuple, cast
from uuid import UUID

from pint.registry import Quantity

from bda.domain.enums import StructuralComponentType
from bda.domain.models.submodels import Element1D
from bda.domain.models.submodels.element import LinkType
from bda.domain.models.submodels.geometry_group import GeometryGroup
from bda.domain.models.submodels.geometry_group_props.shared import GroupPropertiesSegment
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import GroupPropertiesSpan
from bda.domain.models.submodels.sections import SectionStandardSolidRectangle
from bda.modules_pre.m3_geometry.helpers.tools.models import AppliedVector
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.build_context import (
    DeckSpanData,
    SpanReferenceData,
)
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.deck_boundary_builder import (
    generate_deck_boundary_elements_for_bridge_end,
)
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.deck_resolvers import (
    resolve_pouring_init_vector_for_span,
    resolve_deck_pouring_stage_for_element, resolve_deck_segment_for_element_by_node_connectivity,
)
import bda.modules_pre.m3_geometry.helpers.tools.general_tools as tools


def assign_deck_segment_groups(
    builder,
    span: GeometryGroup,
    span_props: GroupPropertiesSpan,
    span_offset: Quantity,
    span_reference_data: SpanReferenceData,
    deck_elements_by_section_uid: Dict[UUID, List[Element1D]],
    sections: List[SectionStandardSolidRectangle],
    y_offsets_girders: Dict[int, Quantity],
) -> None:
    # Segment boundaries are precomputed from deck pouring stages and deck cross-section.
    elements_by_stage_and_section_uid: Dict[Tuple[int, UUID], List[Element1D]] = defaultdict(list)

    if span_props.construction_sequence_details is None:
        for cross_section_uid, elements in deck_elements_by_section_uid.items():
            for element in elements:
                elements_by_stage_and_section_uid[0, cross_section_uid].append(element)
    else:
        pouring_init_vector = resolve_pouring_init_vector_for_span(
            builder=builder,
            span_props=span_props,
            span_offset=span_offset,
            span_reference_data=span_reference_data,
        )

        for cross_section_uid, elements in deck_elements_by_section_uid.items():
            for element in elements:
                pouring_stage: int = resolve_deck_pouring_stage_for_element(
                    builder=builder,
                    element=element,
                    construction_stages=span_props.construction_sequence_details,
                    pouring_init_vector=pouring_init_vector,
                )
                elements_by_stage_and_section_uid[pouring_stage, cross_section_uid].append(element)

    deck_group = builder._require_deck_group_for_span(span)

    segment_entries: list[tuple[float, int, UUID, List[Element1D]]] = []
    for (stage_idx, section_uid), elements in elements_by_stage_and_section_uid.items():
        x_anchor = min(element.mid_point.X.to_base_units().magnitude for element in elements)
        segment_entries.append((x_anchor, stage_idx, section_uid, elements))

    for idx, (_, stage_idx, section_uid, elements) in enumerate(
        sorted(segment_entries, key=lambda entry: (entry[1], entry[0]))
    ):
        segment = GeometryGroup(
            component_type=StructuralComponentType.SEGMENT,
            name=f"Span_{span_props.span_index}_DeckSegment_{idx}_PouringStage_{stage_idx}",
            properties=GroupPropertiesSegment(
                segment_index=idx,
                construction_sequence_stage_index=stage_idx,
            ),
        )
        segment.section = next((section for section in sections if section.guid == section_uid), None)
        segment.analytical_typology.add_elements(elements)

        add_deck_to_girder_links_for_elements(
            builder=builder,
            segment=segment,
            elements=elements,
            girder_y_values=y_offsets_girders.values(),
        )

        deck_group.add_nested_group(segment)


def assign_deck_boundary_elements_group_for_bridge_end(
    builder,
    span_data: DeckSpanData,
    is_bridge_start: bool,
) -> None:
    deck_group = builder._require_deck_group_for_span(span_data.span)
    deck_vertical_offset = cast(
        Quantity,
        builder._require_deck_base_section(deck_group).dimensions.height_h / 2,
    )

    boundary_elements, strip_extension_elements = generate_deck_boundary_elements_for_bridge_end(
        builder=builder,
        span_reference_data=span_data.span_reference_data,
        transverse_deck_strips=span_data.transverse_deck_strips,
        deck_vertical_offset=deck_vertical_offset,
        is_bridge_start=is_bridge_start,
    )
    if not boundary_elements and not strip_extension_elements:
        return

    boundary_elements_by_stage: Dict[int, List[Element1D]] = defaultdict(list)
    strip_extension_elements_by_stage: Dict[int, List[Element1D]] = defaultdict(list)
    if span_data.span_props.construction_sequence_details is None:
        boundary_elements_by_stage[0].extend(boundary_elements)
        strip_extension_elements_by_stage[0].extend(strip_extension_elements)
    else:
        pouring_init_vector = resolve_pouring_init_vector_for_span(
            builder=builder,
            span_props=span_data.span_props,
            span_offset=span_data.span_offset,
            span_reference_data=span_data.span_reference_data,
        )
        stage_pouring_vector = cast(AppliedVector, pouring_init_vector)
        for element in boundary_elements:
            stage = resolve_deck_pouring_stage_for_element(
                builder=builder,
                element=element,
                construction_stages=span_data.span_props.construction_sequence_details,
                pouring_init_vector=stage_pouring_vector,
            )
            boundary_elements_by_stage[stage].append(element)
        for element in strip_extension_elements:
            stage = resolve_deck_pouring_stage_for_element(
                builder=builder,
                element=element,
                construction_stages=span_data.span_props.construction_sequence_details,
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

    for stage_idx, elements in sorted(strip_extension_elements_by_stage.items(), key=lambda item: item[0]):
        stage_segments = [
            segment
            for segment in existing_segments
            if segment.properties.construction_sequence_stage_index == stage_idx
        ]
        if not stage_segments:
            stage_segments = existing_segments

        target_segment_fallback = min(
            stage_segments,
            key=lambda segment: segment.properties.segment_index,
        ) if is_bridge_start else max(
            stage_segments,
            key=lambda segment: segment.properties.segment_index,
        )

        normalized_elements = [
            normalize_element_to_vertical_offset(builder, element, deck_vertical_offset)
            for element in elements
        ]

        for e in normalized_elements:
            target_segment = resolve_deck_segment_for_element_by_node_connectivity(e, stage_segments)
            if target_segment is None:
                target_segment = target_segment_fallback

            target_segment.analytical_typology.add_element(e)
            add_deck_to_girder_links_for_elements(
                builder=builder,
                segment=target_segment,
                elements=[e],
                girder_y_values=[
                    girder.node_start.Y
                    for girder in span_data.span_reference_data.girder_ref_elements.values()
                ],
            )

    for stage_idx, elements in sorted(boundary_elements_by_stage.items(), key=lambda item: item[0]):
        stage_segments = [
            segment
            for segment in existing_segments
            if segment.properties.construction_sequence_stage_index == stage_idx
        ]
        if not stage_segments:
            stage_segments = existing_segments

        target_segment_fallback = min(
            stage_segments,
            key=lambda segment: segment.properties.segment_index,
        ) if is_bridge_start else max(
            stage_segments,
            key=lambda segment: segment.properties.segment_index,
        )

        normalized_elements = [
            normalize_element_to_vertical_offset(builder, element, deck_vertical_offset)
            for element in elements
        ]

        for e in normalized_elements:
            target_segment = resolve_deck_segment_for_element_by_node_connectivity(e, stage_segments)
            if target_segment is None:
                target_segment = target_segment_fallback

            target_segment.analytical_typology.add_element(e)

            add_deck_to_girder_links_for_elements(
                builder=builder,
                segment=target_segment,
                elements=[e],
                girder_y_values=[
                    girder.node_start.Y
                    for girder in span_data.span_reference_data.girder_ref_elements.values()
                ],
            )

def add_deck_to_girder_links_for_elements(
    builder,
    segment: GeometryGroup,
    elements: Iterable[Element1D],
    girder_y_values: Iterable[Quantity],
) -> None:
    """Attach rigid links for deck nodes that lie directly above girders."""
    y_tol = builder._tolerance
    y_values = list(girder_y_values)

    for element in elements:
        for node in (element.node_start, element.node_end):
            if not any(tools.is_close(node.Y, girder_y, y_tol) for girder_y in y_values):
                continue

            girder_node = builder.nodes_manager.get_or_create_node(node.X, node.Y, builder.zero_length)
            if builder._are_same_node(node, girder_node):
                continue

            segment.analytical_typology.add_link(
                builder.elements_manager.get_or_create_link(node, girder_node, LinkType.RIGID)
            )


def normalize_element_to_vertical_offset(
    builder,
    element: Element1D,
    vertical_offset: Quantity,
) -> Element1D:
    """Rebuild element so both end nodes are guaranteed on deck vertical offset."""
    node_start = builder.nodes_manager.get_or_create_node(
        element.node_start.X,
        element.node_start.Y,
        vertical_offset,
    )
    node_end = builder.nodes_manager.get_or_create_node(
        element.node_end.X,
        element.node_end.Y,
        vertical_offset,
    )
    return builder.elements_manager.get_or_create_beam(node_start, node_end)


