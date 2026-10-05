from __future__ import annotations

from typing import Dict, Iterable, List, cast

from pint.registry import Quantity

from bda.domain.enums import StructuralComponentType
from bda.domain.models.submodels import Element1D
from bda.domain.models.submodels.element import LinkType
from bda.domain.models.submodels.geometry_group import GeometryGroup
from bda.domain.models.submodels.geometry_group_props.shared import GroupPropertiesSegment
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import (
    GroupPropertiesGirder,
    GroupPropertiesSpan,
)
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.split_span_into_girder_segments_ import (
    GirderSegmentResult,
)


def assign_girder_segment_groups(
    builder,
    span_props: GroupPropertiesSpan,
    girder_groups: list[GeometryGroup],
    elements_per_girder: Dict[int, List[Element1D]],
    girder_segments: Dict[int, List[GirderSegmentResult]],
) -> None:
    # Segment boundaries are precomputed from cracking extents, deck pouring stages, and splice locations.
    for idx, elements in elements_per_girder.items():
        girder_group = require_girder_group_for_index(
            girder_groups=girder_groups,
            girder_index=idx,
            span_index=span_props.span_index,
        )

        add_vertical_links_at_girder_ends(
            builder=builder,
            girder_group=girder_group,
            elements=elements,
        )

        for seg_index, segment in enumerate(girder_segments[idx]):
            segment_elements = [
                e for e in elements
                if segment.x_start <= e.mid_point.X <= segment.x_end
            ]

            segment_group = GeometryGroup(
                name=f"Span{span_props.span_index}_Girder{idx}_Segment{seg_index}",
                component_type=StructuralComponentType.SEGMENT,
                section_uid=segment.splice_sectionId,
                properties=GroupPropertiesSegment(
                    segment_index=seg_index,
                    is_cracked=segment.cracked_section,
                    construction_sequence_stage_index=segment.deck_pouring_index,
                ),
            )
            girder_group.add_nested_group(segment_group)
            segment_group.analytical_typology.add_elements(segment_elements)
            section = builder._resolve_section_for_segment(segment_group)
            section.name = f"Sp{span_props.span_index}_G{idx}_Seg{seg_index}_{section.name}"


def add_vertical_links_at_girder_ends(
    builder,
    girder_group: GeometryGroup,
    elements: Iterable[Element1D],
) -> None:
    """Attach rigid links at girder start/end nodes down by section total height."""
    elements = list(elements)
    if not elements:
        return

    section_total_height = resolve_section_total_height_for_group(girder_group)
    all_nodes = [
        node
        for element in elements
        for node in (element.node_start, element.node_end)
    ]
    start_node = min(all_nodes, key=lambda node: node.X.to_base_units().magnitude)
    end_node = max(all_nodes, key=lambda node: node.X.to_base_units().magnitude)

    end_nodes = [start_node] if builder._are_same_node(start_node, end_node) else [start_node, end_node]

    for node in end_nodes:
        lowered_node = builder.nodes_manager.get_or_create_node(
            node.X,
            node.Y,
            cast(Quantity, node.Z - section_total_height),
        )
        if builder._are_same_node(node, lowered_node):
            continue

        girder_group.analytical_typology.add_link(
            builder.elements_manager.get_or_create_link(
                node,
                lowered_node,
                LinkType.RIGID,
            )
        )


def resolve_section_total_height_for_group(group: GeometryGroup) -> Quantity:
    section = group.get_section()
    if section is None:
        raise ValueError(f"Group {group.name} has no section assigned.")

    if section.dimensions is None:
        raise TypeError(f"Section for group {group.name} does not expose dimensions.")

    return section.dimensions.total_height


def require_girder_group_for_index(
    girder_groups: list[GeometryGroup],
    girder_index: int,
    span_index: int,
) -> GeometryGroup:
    girder_group = next(
        (
            g
            for g in girder_groups
            if (
                isinstance(props := g.properties, GroupPropertiesGirder)
                and props.girder_index == girder_index
            )
        ),
        None,
    )

    if girder_group is None:
        raise ValueError(
            f"Group for girder index {girder_index} not found "
            f"under span index {span_index}."
        )

    return girder_group
