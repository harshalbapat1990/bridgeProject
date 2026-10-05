"""Deck strip finite elements: transverse beams over girders plus cantilever
extensions towards edge beams, grouped by strip cross-section."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, cast
from uuid import UUID

from pint.registry import Quantity

from bda.domain.models.submodels import Element1D, Node
from bda.domain.models.submodels.sections import SectionStandardSolidRectangle
import bda.modules_pre.m3_geometry.helpers.tools.general_tools as tools
from bda.modules_pre.m3_geometry.helpers.tools.geometry_tools import GeometryTools
from bda.modules_pre.m3_geometry.helpers.tools.models import AppliedVector, Point, Vector
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.context import BuildContext
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.meshing.transverse_strips import (
    DeckStripResult,
)


def generate_finite_elements_for_deck(
    ctx: BuildContext,
    transverse_deck_strips: Iterable[DeckStripResult],
    bridge_edge_beam_segments: Dict[int, AppliedVector],
    deck_cross_sections: List[SectionStandardSolidRectangle],
    deck_tol: Quantity,
) -> Dict[UUID, List[Element1D]]:
    """Generate deck finite elements grouped by cross-section UUID."""
    elements_by_section: Dict[UUID, List[Element1D]] = defaultdict(list)

    y_offsets_girders = ctx.y_offsets_girders

    # vertical deck offset from reference plane to deck centroid
    v_offset = cast(Quantity, deck_cross_sections[0].dimensions.height_h / 2)

    def _sort_key(point: Point, strip_axis: AppliedVector) -> float:
        delta = Vector.from_points(strip_axis.start_point, point)
        return (
            delta.x.to_base_units().magnitude * strip_axis.vector.x.to_base_units().magnitude
            + delta.y.to_base_units().magnitude * strip_axis.vector.y.to_base_units().magnitude
            + delta.z.to_base_units().magnitude * strip_axis.vector.z.to_base_units().magnitude
        )

    global_lower_girder_idx = min(
        y_offsets_girders,
        key=lambda idx: y_offsets_girders[idx].to_base_units().magnitude,
    )
    global_upper_girder_idx = max(
        y_offsets_girders,
        key=lambda idx: y_offsets_girders[idx].to_base_units().magnitude,
    )

    # iterate through deck strips and generate finite elements, group by section
    for strip in transverse_deck_strips:
        cross_section = next(
            (sec for sec in deck_cross_sections
             if tools.is_close(strip.strip_width, sec.dimensions.width_b, deck_tol)))

        strip_points: List[Point] = []
        for idx, p in strip.points_per_girder.items():
            strip_points.append(Point(p, y_offsets_girders[idx], v_offset))

        strip_points.sort(key=lambda p: _sort_key(p, strip.strip_vector))

        nodes: List[Node] = [
            ctx.amm.get_or_create_node(point.x, point.y, point.z)
            for point in strip_points
        ]

        for ni in range(len(nodes) - 1):
            element = ctx.amm.get_or_create_beam(nodes[ni], nodes[ni + 1])
            elements_by_section[cross_section.guid].append(element)

        if not strip.points_per_girder:
            continue

        has_global_lower = global_lower_girder_idx in strip.points_per_girder
        has_global_upper = global_upper_girder_idx in strip.points_per_girder
        if not has_global_lower and not has_global_upper:
            continue

        lower_girder_node = (
            ctx.amm.get_or_create_node(
                strip.points_per_girder[global_lower_girder_idx],
                y_offsets_girders[global_lower_girder_idx],
                v_offset,
            )
            if has_global_lower
            else None
        )
        upper_girder_node = (
            ctx.amm.get_or_create_node(
                strip.points_per_girder[global_upper_girder_idx],
                y_offsets_girders[global_upper_girder_idx],
                v_offset,
            )
            if has_global_upper
            else None
        )

        edge_intersection_nodes: List[Node] = []
        for edge_beam_segment in bridge_edge_beam_segments.values():
            # Keep only intersections that lie on finite full-bridge edge-beam span.
            intersection = GeometryTools.project_node_on_segment(
                line=strip.strip_vector,
                segment=edge_beam_segment,
                tol=ctx.tolerance,
            )
            if intersection is None:
                continue

            edge_intersection_nodes.append(
                ctx.amm.get_or_create_node(intersection.x, intersection.y, v_offset)
            )

        if not edge_intersection_nodes:
            continue

        edge_intersection_nodes.sort(key=lambda n: n.Y.to_base_units().magnitude)

        # Pair strip side-to-side: lower edge with lower outer girder, upper edge with upper outer girder.
        if len(edge_intersection_nodes) == 1:
            edge_node = edge_intersection_nodes[0]
            if lower_girder_node is not None and upper_girder_node is not None:
                target_girder_node = (
                    lower_girder_node
                    if abs(edge_node.Y.to_base_units().magnitude - lower_girder_node.Y.to_base_units().magnitude)
                    <= abs(edge_node.Y.to_base_units().magnitude - upper_girder_node.Y.to_base_units().magnitude)
                    else upper_girder_node
                )
                elements_by_section[cross_section.guid].append(
                    ctx.amm.get_or_create_beam(target_girder_node, edge_node)
                )
            elif lower_girder_node is not None:
                elements_by_section[cross_section.guid].append(
                    ctx.amm.get_or_create_beam(lower_girder_node, edge_node)
                )
            elif upper_girder_node is not None:
                elements_by_section[cross_section.guid].append(
                    ctx.amm.get_or_create_beam(upper_girder_node, edge_node)
                )
        else:
            if lower_girder_node is not None:
                elements_by_section[cross_section.guid].append(
                    ctx.amm.get_or_create_beam(lower_girder_node, edge_intersection_nodes[0])
                )
            if upper_girder_node is not None:
                elements_by_section[cross_section.guid].append(
                    ctx.amm.get_or_create_beam(upper_girder_node, edge_intersection_nodes[-1])
                )

    return elements_by_section
