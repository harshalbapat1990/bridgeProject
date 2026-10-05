"""Bridge-long edge-beam finite elements on the deck plane, split at deck-strip
crossings and assigned to per-span SEGMENT groups matching the connected deck
segments' pouring stages."""
from __future__ import annotations

from typing import Dict, Iterable, List, Tuple, cast

from pint.registry import Quantity

from bda.domain.enums import StructuralComponentType
from bda.domain.models.submodels import Element1D, Node
from bda.domain.models.submodels.geometry_group import GeometryGroup
from bda.domain.models.submodels.geometry_group_props.shared import GroupPropertiesSegment
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import (
    GroupPropertiesEdgeBeam,
)
from bda.modules_pre.m3_geometry.helpers.tools.geometry_tools import GeometryTools
from bda.modules_pre.m3_geometry.helpers.tools.models import AppliedVector, Point, Vector
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.context import (
    BuildContext,
    SpanState,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.group_collectors import (
    collect_or_create_edge_beams_for_span,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.group_property_getters import (
    require_deck_base_section,
    require_deck_group_for_span,
    require_edge_beam_properties,
    require_segment_properties,
    require_span_properties,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.node_utils import are_same_node


def generate_finite_elements_for_edge_beams_for_bridge(
    ctx: BuildContext,
    span_states: Iterable[SpanState],
    bridge_edge_beam_segments: Dict[int, AppliedVector],
) -> None:
    """Generate continuous edge beams for the entire bridge and assign their
    elements to per-span segment groups by deck-segment connectivity."""
    span_states = sorted(
        list(span_states),
        key=lambda s: s.span_props.span_index,
    )
    if not span_states:
        return

    first_deck_group = require_deck_group_for_span(ctx, span_states[0].span)
    deck_vertical_offset = cast(
        Quantity,
        require_deck_base_section(first_deck_group).dimensions.height_h / 2,
    )

    all_transverse_deck_strips = [
        strip
        for state in span_states
        for strip in state.transverse_deck_strips
    ]

    ordered_deck_segments: List[GeometryGroup] = []
    edge_beam_group_by_span_and_index: Dict[Tuple[int, int], GeometryGroup] = {}

    for state in span_states:
        span_index = state.span_props.span_index

        deck_group = require_deck_group_for_span(ctx, state.span)
        deck_segments = [
            segment
            for segment in deck_group.get_groups_by_component_type(StructuralComponentType.SEGMENT)
            if isinstance(segment.properties, GroupPropertiesSegment)
        ]
        deck_segments.sort(key=lambda segment: require_segment_properties(segment).segment_index)
        ordered_deck_segments.extend(deck_segments)

        edge_beam_groups = [
            group
            for group in collect_or_create_edge_beams_for_span(ctx, state.span)
            if isinstance(group.properties, GroupPropertiesEdgeBeam)
        ]
        for edge_group in edge_beam_groups:
            edge_index = require_edge_beam_properties(edge_group).edge_beam_index
            edge_beam_group_by_span_and_index[(span_index, edge_index)] = edge_group

    if not ordered_deck_segments:
        return

    for edge_beam_index, bridge_edge_beam_segment in sorted(bridge_edge_beam_segments.items()):
        edge_elements = _generate_bridge_edge_beam_elements(
            ctx,
            bridge_edge_beam_segment=bridge_edge_beam_segment,
            all_transverse_deck_strips=all_transverse_deck_strips,
            deck_vertical_offset=deck_vertical_offset,
        )
        if not edge_elements:
            continue

        _assign_edge_elements_to_segment_groups(
            ctx,
            edge_beam_index=edge_beam_index,
            edge_elements=edge_elements,
            ordered_deck_segments=ordered_deck_segments,
            edge_beam_group_by_span_and_index=edge_beam_group_by_span_and_index,
        )


def _generate_bridge_edge_beam_elements(
    ctx: BuildContext,
    bridge_edge_beam_segment: AppliedVector,
    all_transverse_deck_strips: Iterable,
    deck_vertical_offset: Quantity,
) -> List[Element1D]:
    """Create full-bridge edge-beam elements split at every deck-strip crossing."""
    edge_start_node = ctx.amm.get_or_create_node(
        bridge_edge_beam_segment.start_point.x,
        bridge_edge_beam_segment.start_point.y,
        deck_vertical_offset,
    )
    edge_end_node = ctx.amm.get_or_create_node(
        cast(Quantity, bridge_edge_beam_segment.start_point.x + bridge_edge_beam_segment.vector.x),
        cast(Quantity, bridge_edge_beam_segment.start_point.y + bridge_edge_beam_segment.vector.y),
        deck_vertical_offset,
    )

    edge_nodes_by_id: Dict[int, Node] = {
        edge_start_node.node_id: edge_start_node,
        edge_end_node.node_id: edge_end_node,
    }

    for strip in all_transverse_deck_strips:
        intersection = GeometryTools.project_node_on_segment(
            line=strip.strip_vector,
            segment=bridge_edge_beam_segment,
            tol=ctx.tolerance,
        )
        if intersection is None:
            continue

        edge_node = ctx.amm.get_or_create_node(
            intersection.x,
            intersection.y,
            deck_vertical_offset,
        )
        edge_nodes_by_id[edge_node.node_id] = edge_node

    edge_axis = AppliedVector.from_points(
        Point(edge_start_node.X, edge_start_node.Y, edge_start_node.Z),
        Point(edge_end_node.X, edge_end_node.Y, edge_end_node.Z),
    )

    def _projection_along_edge(node: Node) -> float:
        delta = Vector.from_points(
            edge_axis.start_point,
            Point(node.X, node.Y, node.Z),
        )
        return (
            delta.x.to_base_units().magnitude * edge_axis.vector.x.to_base_units().magnitude
            + delta.y.to_base_units().magnitude * edge_axis.vector.y.to_base_units().magnitude
            + delta.z.to_base_units().magnitude * edge_axis.vector.z.to_base_units().magnitude
        )

    ordered_nodes = sorted(edge_nodes_by_id.values(), key=_projection_along_edge)

    edge_elements: List[Element1D] = []
    for i in range(len(ordered_nodes) - 1):
        if are_same_node(ordered_nodes[i], ordered_nodes[i + 1]):
            continue
        edge_elements.append(
            ctx.amm.get_or_create_beam(ordered_nodes[i], ordered_nodes[i + 1])
        )

    return edge_elements


def _assign_edge_elements_to_segment_groups(
    ctx: BuildContext,
    edge_beam_index: int,
    edge_elements: List[Element1D],
    ordered_deck_segments: List[GeometryGroup],
    edge_beam_group_by_span_and_index: Dict[Tuple[int, int], GeometryGroup],
) -> None:
    """Group edge elements per span/pouring stage of the connected deck segment."""
    edge_segment_groups_by_span_and_edge: Dict[Tuple[int, int], Dict[int, GeometryGroup]] = {}

    for edge_element in edge_elements:
        target_deck_segment = resolve_connected_deck_segment_for_edge_element(
            edge_element,
            ordered_deck_segments,
        )
        target_props = require_segment_properties(target_deck_segment)

        target_span = target_deck_segment.get_parent_group_by_component_type(StructuralComponentType.SPAN)
        if target_span is None:
            continue
        target_span_index = require_span_properties(target_span).span_index

        edge_beam_group = edge_beam_group_by_span_and_index.get((target_span_index, edge_beam_index))
        if edge_beam_group is None:
            continue

        cache_key = (target_span_index, edge_beam_index)
        edge_segment_groups_by_key = edge_segment_groups_by_span_and_edge.get(cache_key)
        if edge_segment_groups_by_key is None:
            existing_edge_segments = [
                segment
                for segment in edge_beam_group.get_groups_by_component_type(StructuralComponentType.SEGMENT)
                if isinstance(segment.properties, GroupPropertiesSegment)
            ]
            edge_segment_groups_by_key = {
                require_segment_properties(segment).construction_sequence_stage_index: segment
                for segment in existing_edge_segments
            }
            edge_segment_groups_by_span_and_edge[cache_key] = edge_segment_groups_by_key

        segment_key = target_props.construction_sequence_stage_index

        edge_segment_group = edge_segment_groups_by_key.get(segment_key)
        if edge_segment_group is None:
            edge_segment_group = GeometryGroup(
                component_type=StructuralComponentType.SEGMENT,
                name=(
                    f"Span_{target_span_index}_EdgeBeam_{edge_beam_index}_"
                    f"Segment_{target_props.construction_sequence_stage_index}_"
                    f"PouringStage_{target_props.construction_sequence_stage_index}"
                ),
                properties=GroupPropertiesSegment(
                    segment_index=target_props.construction_sequence_stage_index,
                    construction_sequence_stage_index=target_props.construction_sequence_stage_index,
                ),
            )
            edge_segment_group.material = target_deck_segment.get_material()
            # Keep section inheritance from edge-beam/parent group.
            edge_beam_group.add_nested_group(edge_segment_group)
            edge_segment_groups_by_key[segment_key] = edge_segment_group

        ctx.amm.add_element(edge_segment_group, edge_element)


def resolve_connected_deck_segment_for_edge_element(
    element: Element1D,
    segments: List[GeometryGroup],
) -> GeometryGroup:
    """Pick the deck segment sharing the element's end node; fall back to the last one."""
    if not segments:
        raise ValueError("No deck segments provided for edge-beam assignment.")

    node_end = element.node_end

    # Classify by edge-element end node, so boundary membership follows
    # the transverse strip element that reaches this edge node.
    for segment in segments:
        for seg_element in segment.analytical_typology.elements:
            if not isinstance(seg_element, Element1D):
                continue
            if seg_element.node_start == node_end or seg_element.node_end == node_end:
                return segment

    # Keep previous fallback behavior when no connectivity match is found.
    return segments[-1]
