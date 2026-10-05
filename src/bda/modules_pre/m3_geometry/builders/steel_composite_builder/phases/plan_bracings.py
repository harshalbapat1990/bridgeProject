"""Plan-bracings phase: horizontal bracing elements spanning between the top
chords of transverse bracings."""
from __future__ import annotations

from typing import List

from bda.domain.enums import StructuralComponentType
from bda.domain.models.submodels import Element1D, Node
from bda.domain.models.submodels.geometry_group import GeometryGroup
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import PlanBracingType
from bda.modules_pre.m3_geometry.helpers.tools.geometry_tools import GeometryTools
from bda.modules_pre.m3_geometry.helpers.tools.models import Point
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.context import (
    BuildContext,
    SpanReferenceData,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.group_collectors import (
    collect_plan_bracings_for_span,
    collect_transverse_bracings_for_bridge,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.group_property_getters import (
    require_chord_properties,
    require_plan_bracing_properties,
    require_transverse_bracing_properties,
)


def run(ctx: BuildContext) -> None:
    for state in ctx.span_states:
        _generate_finite_elements_for_span(ctx, state.span, state.reference_data)


def _generate_finite_elements_for_span(
    ctx: BuildContext,
    span: GeometryGroup,
    reference_data: SpanReferenceData,
) -> None:
    """Build all plan bracings finite elements for a single span."""
    plan_bracings = collect_plan_bracings_for_span(span)
    all_transverse_bracings = collect_transverse_bracings_for_bridge(ctx.require_geometry())

    for plan_bracing in plan_bracings:
        props = require_plan_bracing_properties(plan_bracing)

        start_girder_index = props.left_girder_index
        end_girder_index = props.right_girder_index

        # find all transverse bracings that are connected to this plan bracing
        transv_bracings = [
            tb
            for tb in all_transverse_bracings
            if _is_bracing_between_girders(tb, start_girder_index, end_girder_index)
        ]

        if len(transv_bracings) < 1:
            continue

        top_chord_groups = _collect_top_chords(transv_bracings)

        # collect all nodes
        all_left_nodes: List[Node] = []
        all_right_nodes: List[Node] = []

        for top_chord in top_chord_groups:
            for e in iter(top_chord.analytical_typology.elements):
                if not isinstance(e, Element1D):
                    continue
                all_left_nodes.append(e.node_start)
                all_right_nodes.append(e.node_end)

        # filter nodes only in the current span
        left_nodes = _filter_nodes_within_span(ctx, all_left_nodes, reference_data)
        right_nodes = _filter_nodes_within_span(ctx, all_right_nodes, reference_data)

        if len(left_nodes) < 2 or len(right_nodes) < 2:
            continue

        match props.plan_bracing_type:
            case PlanBracingType.PRATT:
                for i in range(len(left_nodes) - 1):
                    element = ctx.amm.create_and_add_beam(plan_bracing, right_nodes[i], left_nodes[i + 1])

            case PlanBracingType.WARREN:
                for i in range(len(left_nodes) - 1):
                    if i % 2 == 0:
                        element = ctx.amm.create_and_add_beam(plan_bracing, right_nodes[i], left_nodes[i + 1])
                    else:
                        element = ctx.amm.create_and_add_beam(plan_bracing, left_nodes[i], right_nodes[i + 1])

            case PlanBracingType.X_TYPE:
                for i in range(len(left_nodes) - 1):
                    e1 = ctx.amm.create_and_add_beam(plan_bracing, right_nodes[i], left_nodes[i + 1])
                    e2 = ctx.amm.create_and_add_beam(plan_bracing, left_nodes[i], right_nodes[i + 1])


def _is_bracing_between_girders(
    transverse_bracing: GeometryGroup,
    start_girder_index: int,
    end_girder_index: int,
) -> bool:
    props = require_transverse_bracing_properties(transverse_bracing)
    return (
        props.left_girder_index in (start_girder_index, end_girder_index)
        and props.right_girder_index in (start_girder_index, end_girder_index)
    )


def _collect_top_chords(transverse_bracings: List[GeometryGroup]) -> List[GeometryGroup]:
    """For each bracing pick the chord with the smallest left vertical offset (the top one)."""
    top_chord_groups: List[GeometryGroup] = []

    for tr_br in transverse_bracings:
        chords = tr_br.get_groups_by_component_type(StructuralComponentType.CHORD)
        if chords:
            top_chord: GeometryGroup = chords[0]
            for chord in chords:
                ch_props = require_chord_properties(chord)
                t_ch_props = require_chord_properties(top_chord)
                if ch_props.vertical_offset_at_left < t_ch_props.vertical_offset_at_left:
                    top_chord = chord
            top_chord_groups.append(top_chord)

    return top_chord_groups


def _filter_nodes_within_span(
    ctx: BuildContext,
    nodes: List[Node],
    reference_data: SpanReferenceData,
) -> List[Node]:
    start_vector = reference_data.support_i_vector
    end_vector = reference_data.support_j_vector

    return [
        node
        for node in nodes
        if GeometryTools.project_node_on_line_along_x_asix(
            line=start_vector,
            point=Point(node.X, node.Y),
            tol=ctx.tolerance,
        ).x - ctx.tolerance < node.X
        and GeometryTools.project_node_on_line_along_x_asix(
            line=end_vector,
            point=Point(node.X, node.Y),
            tol=ctx.tolerance,
        ).x + ctx.tolerance > node.X
    ]
