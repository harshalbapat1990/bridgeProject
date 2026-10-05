"""Deck boundary elements closing the deck outline at bridge start/end."""
from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from pint.registry import Quantity

from bda.domain.models.submodels import Element1D, Node
from bda.modules_pre.m3_geometry.helpers.tools.geometry_tools import GeometryTools
from bda.modules_pre.m3_geometry.helpers.tools.models import AppliedVector, Point, Vector
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.context import (
    BuildContext,
    SpanReferenceData,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.meshing.transverse_strips import (
    DeckStripResult,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.node_utils import are_same_node

def generate_deck_boundary_elements_for_bridge_end(
    ctx: BuildContext,
    span_reference_data: SpanReferenceData,
    transverse_deck_strips: Iterable[DeckStripResult],
    deck_vertical_offset: Quantity,
    is_bridge_start: bool,
) -> Tuple[List[Element1D], List[Element1D]]:
    boundary_elements: List[Element1D] = []
    strip_extension_elements: List[Element1D] = []

    girder_ref_elements = span_reference_data.girder_ref_elements
    edge_beam_ref_elements = span_reference_data.edge_beam_ref_elements
    if not girder_ref_elements or not edge_beam_ref_elements:
        return boundary_elements, strip_extension_elements

    for edge_beam in edge_beam_ref_elements.values():
        edge_node = edge_beam.node_start if is_bridge_start else edge_beam.node_end

        closest_girder_idx, closest_girder = min(
            girder_ref_elements.items(),
            key=lambda entry: abs(
                (
                    (entry[1].node_start.Y if is_bridge_start else entry[1].node_end.Y)
                    - edge_node.Y
                ).to_base_units().magnitude
            ),
        )

        girder_node = closest_girder.node_start if is_bridge_start else closest_girder.node_end

        edge_node = ctx.amm.get_or_create_node(
            edge_node.X,
            edge_node.Y,
            deck_vertical_offset,
        )
        girder_node = ctx.amm.get_or_create_node(
            girder_node.X,
            girder_node.Y,
            deck_vertical_offset,
        )

        boundary_for_edge, strip_extensions_for_edge = _build_boundary_elements_split_by_strip_intersections(
            ctx,
            girder_node=girder_node,
            edge_node=edge_node,
            girder_reference_element=closest_girder,
            girder_index=closest_girder_idx,
            transverse_deck_strips=transverse_deck_strips,
            deck_vertical_offset=deck_vertical_offset,
        )
        boundary_elements.extend(boundary_for_edge)
        strip_extension_elements.extend(strip_extensions_for_edge)

    return boundary_elements, strip_extension_elements


def _build_boundary_elements_split_by_strip_intersections(
    ctx: BuildContext,
    girder_node: Node,
    edge_node: Node,
    girder_reference_element: Element1D,
    girder_index: int,
    transverse_deck_strips: Iterable[DeckStripResult],
    deck_vertical_offset: Quantity,
) -> Tuple[List[Element1D], List[Element1D]]:
    boundary_segment = AppliedVector.from_points(
        Point(girder_node.X, girder_node.Y, girder_node.Z),
        Point(edge_node.X, edge_node.Y, edge_node.Z),
    )
    girder_segment = AppliedVector.from_points(
        Point(girder_reference_element.node_start.X, girder_reference_element.node_start.Y, deck_vertical_offset),
        Point(girder_reference_element.node_end.X, girder_reference_element.node_end.Y, deck_vertical_offset),
    )

    split_nodes: Dict[int, Node] = {}
    strip_extension_elements: List[Element1D] = []
    for strip in transverse_deck_strips:
        strip_line = AppliedVector(
            start_point=Point(
                strip.strip_vector.start_point.x,
                strip.strip_vector.start_point.y,
                deck_vertical_offset,
            ),
            vector=strip.strip_vector.vector,
        )

        # Use strip line extension, but keep only intersections lying on finite boundary segment.
        intersection = GeometryTools.project_node_on_segment(
            line=strip_line,
            segment=boundary_segment,
            tol=ctx.tolerance,
        )
        if intersection is None:
            continue

        split_node = ctx.amm.get_or_create_node(intersection.x, intersection.y, intersection.z)
        if are_same_node(split_node, girder_node) or are_same_node(split_node, edge_node):
            continue
        split_nodes[split_node.node_id] = split_node

        # Add missing strip extension from the corresponding girder crossing to boundary crossing.
        if girder_index not in strip.points_per_girder:
            continue
        girder_intersection = GeometryTools.project_node_on_segment(
            line=strip_line,
            segment=girder_segment,
            tol=ctx.tolerance,
        )
        if girder_intersection is None:
            continue

        girder_split_node = ctx.amm.get_or_create_node(
            girder_intersection.x,
            girder_intersection.y,
            deck_vertical_offset,
        )
        if are_same_node(girder_split_node, split_node):
            continue
        strip_extension_elements.append(
            ctx.amm.get_or_create_beam(girder_split_node, split_node)
        )

    start_point = Point(girder_node.X, girder_node.Y, girder_node.Z)
    boundary_vector = boundary_segment.vector

    def projection_along_boundary(node: Node) -> float:
        delta = Vector.from_points(start_point, Point(node.X, node.Y, node.Z))
        return (
            delta.x.to_base_units().magnitude * boundary_vector.x.to_base_units().magnitude
            + delta.y.to_base_units().magnitude * boundary_vector.y.to_base_units().magnitude
            + delta.z.to_base_units().magnitude * boundary_vector.z.to_base_units().magnitude
        )

    interior_nodes = sorted(
        split_nodes.values(),
        key=projection_along_boundary,
    )

    ordered_nodes = [girder_node, *interior_nodes, edge_node]
    output: List[Element1D] = []
    for i in range(len(ordered_nodes) - 1):
        if are_same_node(ordered_nodes[i], ordered_nodes[i + 1]):
            continue
        output.append(ctx.amm.get_or_create_beam(ordered_nodes[i], ordered_nodes[i + 1]))

    return output, strip_extension_elements
