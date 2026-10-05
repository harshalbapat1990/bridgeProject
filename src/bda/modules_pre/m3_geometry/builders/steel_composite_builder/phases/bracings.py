"""Transverse-bracings phase: braces and chords finite elements with rigid links
to the bracing reference elements."""
from __future__ import annotations

from typing import Iterable, List, Tuple, cast

from pint.registry import Quantity

import bda.domain.units.registry as units
from bda.domain.models.submodels import Element1D, Node
from bda.domain.models.submodels.boundary_conditions.beam_end_release import (
    BeamEndRelease,
    DirectionalRelease,
    NodeRelease,
    StiffnessType,
)
from bda.domain.models.submodels.element import ElementLink, LinkType
from bda.domain.models.submodels.geometry_group import GeometryGroup
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import BracingType
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import (
    BracingBraceXtypeDetails,
    GroupPropertiesTransverseBracing,
)
from bda.modules_pre.m3_geometry.helpers.tools.geometry_tools import GeometryTools
from bda.modules_pre.m3_geometry.helpers.tools.models import (
    AppliedVector,
    Point,
    UnitVector,
    Vector,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.context import BuildContext
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.group_collectors import (
    collect_brace_groups,
    collect_bracings_for_span,
    collect_chord_groups,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.group_property_getters import (
    require_brace_properties,
    require_chord_properties,
    require_transverse_bracing_properties,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.node_utils import are_same_node


def run(ctx: BuildContext) -> None:
    for state in ctx.span_states:
        _generate_finite_elements_for_span(ctx, state.span)


def _generate_finite_elements_for_span(ctx: BuildContext, span: GeometryGroup) -> None:
    """Build all bracing finite elements for a single span."""
    for bracing_group in collect_bracings_for_span(span):
        ref_elements = [
            element
            for element in bracing_group.reference_elements
            if isinstance(element, Element1D)
        ]

        for bracing_index, reference_element in enumerate(ref_elements):
            _model_single_bracing(
                ctx,
                bracing_group=bracing_group,
                reference_element=reference_element,
                bracing_index=bracing_index,
            )


def _model_single_bracing(
    ctx: BuildContext,
    bracing_group: GeometryGroup,
    reference_element: Element1D,
    bracing_index: int,
) -> None:
    bracing_props = require_transverse_bracing_properties(bracing_group)
    brace_groups = collect_brace_groups(bracing_group)
    chord_groups = collect_chord_groups(bracing_group)

    if not brace_groups and not chord_groups:
        ctx.logger.warning(
            "Bracing group has no BRACE/CHORD nested groups | group=%s | index=%s",
            bracing_group.name,
            bracing_index,
        )
        return

    ref_start = reference_element.node_start
    ref_end = reference_element.node_end
    ref_vector = Vector.from_points(
        Point(ref_start.X, ref_start.Y, ref_start.Z),
        Point(ref_end.X, ref_end.Y, ref_end.Z),
    )
    ref_unit = ref_vector.normalize()

    projected_chord_target: tuple[GeometryGroup, Node] | None = None

    for brace_group in brace_groups:
        brace_props = require_brace_properties(brace_group)
        left_brace_nodes = _resolve_bracing_member_nodes(
            ctx,
            reference_start=ref_start,
            reference_end=ref_end,
            reference_unit=ref_unit,
            left_horizontal_offset=bracing_props.bracing_details.horizontal_offset_at_left,
            right_horizontal_offset=(
                bracing_props.bracing_details.horizontal_offset_at_right
                if isinstance(brace_props.geometry_details, BracingBraceXtypeDetails)
                else brace_props.geometry_details.horizontal_offset_left_brace),
            left_vertical_offset=brace_props.geometry_details.vertical_offset_left_top,
            right_vertical_offset=brace_props.geometry_details.vertical_offset_right_bottom
        )
        if are_same_node(left_brace_nodes[0], left_brace_nodes[1]):
            ctx.logger.warning(
                "[SteelCompositeBuilder] skipping degenerate left brace with identical nodes"
                " | bracing_group=%s | brace_group=%s | bracing_index=%s",
                bracing_group.name,
                brace_group.name,
                bracing_index,
            )
            continue
        right_brace_nodes = _resolve_bracing_member_nodes(
            ctx,
            reference_start=ref_start,
            reference_end=ref_end,
            reference_unit=ref_unit,
            left_horizontal_offset=(
                bracing_props.bracing_details.horizontal_offset_at_left
                if isinstance(brace_props.geometry_details, BracingBraceXtypeDetails)
                else brace_props.geometry_details.horizontal_offset_right_brace),
            right_horizontal_offset=bracing_props.bracing_details.horizontal_offset_at_right,
            left_vertical_offset=brace_props.geometry_details.vertical_offset_left_bottom,
            right_vertical_offset=brace_props.geometry_details.vertical_offset_right_top,
        )
        if are_same_node(right_brace_nodes[0], right_brace_nodes[1]):
            ctx.logger.warning(
                "[SteelCompositeBuilder] skipping degenerate right brace with identical nodes"
                " | bracing_group=%s | brace_group=%s | bracing_index=%s",
                bracing_group.name,
                brace_group.name,
                bracing_index,
            )
            continue
        left_brace_element = ctx.amm.create_and_add_beam(brace_group, left_brace_nodes[0], left_brace_nodes[1])
        right_brace_element = ctx.amm.get_or_create_beam(right_brace_nodes[0], right_brace_nodes[1])
        left_brace_ends_release = _create_beam_end_moments_yx_release(left_brace_element)
        right_brace_ends_release = _create_beam_end_moments_yx_release(right_brace_element)
        ctx.amm.add_element(brace_group, right_brace_element)
        ctx.amm.add_beam_end_release(brace_group, left_brace_ends_release)
        ctx.amm.add_beam_end_release(brace_group, right_brace_ends_release)

        if brace_props.geometry_details.bracing_type == BracingType.X_TYPE:
            ctx.amm.add_elements(brace_group, 
                _create_member_end_links(ctx, reference_element, left_brace_nodes))
            ctx.amm.add_elements(brace_group, 
                _create_member_end_links(ctx, reference_element, right_brace_nodes))
        else:
            # For K-type, avoid rigid links at left-end/right-start nodes.
            if not are_same_node(reference_element.node_start, left_brace_nodes[0]):
                ctx.amm.create_and_add_link(brace_group, reference_element.node_start,
                        left_brace_nodes[0],
                        LinkType.RIGID)
            if not are_same_node(reference_element.node_end, right_brace_nodes[1]):
                ctx.amm.create_and_add_link(brace_group, reference_element.node_end,
                        right_brace_nodes[1],
                        LinkType.RIGID)

        if brace_props.geometry_details.bracing_type == BracingType.K_TYPE:
            midpoint_node = ctx.amm.get_or_create_node(
                cast(Quantity, (left_brace_nodes[1].X + right_brace_nodes[0].X) / 2),
                cast(Quantity, (left_brace_nodes[1].Y + right_brace_nodes[0].Y) / 2),
                cast(Quantity, (left_brace_nodes[1].Z + right_brace_nodes[0].Z) / 2),
            )

            projected_chord_node = _project_midpoint_to_first_lower_chord(
                ctx,
                midpoint_node=midpoint_node,
                chord_groups=chord_groups,
                bracing_props=bracing_props,
                reference_start=ref_start,
                reference_end=ref_end,
                reference_unit=ref_unit,
            )
            if projected_chord_node is None:
                ctx.logger.warning(
                    "[SteelCompositeBuilder] K-type brace midpoint projection failed"
                    " | bracing_group=%s | brace_group=%s | bracing_index=%s",
                    bracing_group.name,
                    brace_group.name,
                    bracing_index,
                )
            else:
                projected_chord_target = projected_chord_node

                # Brace ends are tied to the node that lies on the projected chord.
                projected_node = projected_chord_node[1]
                if not are_same_node(left_brace_nodes[1], projected_node):
                    ctx.amm.create_and_add_link(brace_group, left_brace_nodes[1], projected_node, LinkType.RIGID)
                if not are_same_node(right_brace_nodes[0], projected_node):
                    ctx.amm.create_and_add_link(brace_group, right_brace_nodes[0], projected_node, LinkType.RIGID)

    for chord_group in chord_groups:
        chord_props = require_chord_properties(chord_group)
        chord_nodes = _resolve_bracing_member_nodes(
            ctx,
            reference_start=ref_start,
            reference_end=ref_end,
            reference_unit=ref_unit,
            left_horizontal_offset=bracing_props.bracing_details.horizontal_offset_at_left,
            right_horizontal_offset=bracing_props.bracing_details.horizontal_offset_at_right,
            left_vertical_offset=chord_props.vertical_offset_at_left,
            right_vertical_offset=chord_props.vertical_offset_at_right,
        )

        if are_same_node(chord_nodes[0], chord_nodes[1]):
            ctx.logger.warning(
                "[SteelCompositeBuilder] skipping degenerate chord with identical nodes"
                " | bracing_group=%s | chord_group=%s | bracing_index=%s",
                bracing_group.name,
                chord_group.name,
                bracing_index,
            )
            continue

        if projected_chord_target is not None and projected_chord_target[0].guid == chord_group.guid:
            projected_node = projected_chord_target[1]

            # For K-type, split the projected chord into two finite elements.
            if not are_same_node(chord_nodes[0], projected_node):
                element = ctx.amm.create_and_add_beam(chord_group, chord_nodes[0], projected_node)
                ctx.amm.add_beam_end_release(chord_group, _create_beam_end_moments_yx_release(element))
            if not are_same_node(projected_node, chord_nodes[1]):
                element = ctx.amm.create_and_add_beam(chord_group, projected_node, chord_nodes[1])
                ctx.amm.add_beam_end_release(chord_group, _create_beam_end_moments_yx_release(element))
        else:
            chord_element = ctx.amm.create_and_add_beam(chord_group, chord_nodes[0], chord_nodes[1])
            ctx.amm.add_beam_end_release(chord_group, _create_beam_end_moments_yx_release(chord_element))

        ctx.amm.add_elements(chord_group, 
            _create_member_end_links(ctx, reference_element, chord_nodes))


def _resolve_bracing_member_nodes(
    ctx: BuildContext,
    reference_start: Node,
    reference_end: Node,
    reference_unit: UnitVector,
    left_horizontal_offset: Quantity,
    right_horizontal_offset: Quantity,
    left_vertical_offset: Quantity,
    right_vertical_offset: Quantity,
) -> Tuple[Node, Node]:
    """Resolve start/end FE nodes of a single brace/chord member.

    The returned nodes are *member nodes* (not the bracing reference nodes).
    They represent actual finite-element end nodes for a brace/chord nested
    inside one transverse-bracing location.

    Node positions are derived from the bracing reference element by:
    1) moving from each reference end along the reference direction in XY
       using transverse-bracing/chord/brace horizontal offsets,
    2) applying vertical Z offsets from brace/chord properties,
    3) resolving/reusing final nodes through ``NodesManager`` tolerance.

    Returns
    -------
    tuple[Node, Node]
        ``(node_start, node_end)`` for the finite member to be created.
    """
    start_shift = cast(Quantity, left_horizontal_offset)
    end_shift = cast(Quantity, right_horizontal_offset)

    start_point = Point(reference_start.X, reference_start.Y, reference_start.Z).translate(
        Vector.from_unit_vector_and_length(reference_unit, start_shift)
    )
    end_point = Point(reference_end.X, reference_end.Y, reference_end.Z).translate(
        Vector.from_unit_vector_and_length(reference_unit, -end_shift)
    )

    start_point = start_point.translate(Vector(ctx.zero_length, ctx.zero_length, -left_vertical_offset))
    end_point = end_point.translate(Vector(ctx.zero_length, ctx.zero_length, -right_vertical_offset))
    return (
        ctx.amm.get_or_create_node(start_point.x, start_point.y, start_point.z),
        ctx.amm.get_or_create_node(end_point.x, end_point.y, end_point.z),
    )


def _create_member_end_links(
    ctx: BuildContext,
    reference_element: Element1D,
    member_nodes: Tuple[Node, Node],
) -> List[ElementLink]:
    return [
        ctx.amm.get_or_create_link(reference_element.node_start, member_nodes[0], LinkType.RIGID),
        ctx.amm.get_or_create_link(reference_element.node_end, member_nodes[1], LinkType.RIGID),
    ]


def _create_beam_end_moments_yx_release(element: Element1D) -> BeamEndRelease:
    return BeamEndRelease(
        element_reference=element,
        stiffness_type=StiffnessType.ABSOLUTE_VALUE,
        start_node_release=NodeRelease(
            M_y=DirectionalRelease(enabled=True, value=0.0 * units.kN * units.m / units.rad),
            M_z=DirectionalRelease(enabled=True, value=0.0 * units.kN * units.m / units.rad),
        ),
        end_node_release=NodeRelease(
            M_y=DirectionalRelease(enabled=True, value=0.0 * units.kN * units.m / units.rad),
            M_z=DirectionalRelease(enabled=True, value=0.0 * units.kN * units.m / units.rad),
        )
    )

def _project_midpoint_to_first_lower_chord(
    ctx: BuildContext,
    midpoint_node: Node,
    chord_groups: Iterable[GeometryGroup],
    bracing_props: GroupPropertiesTransverseBracing,
    reference_start: Node,
    reference_end: Node,
    reference_unit: UnitVector,
) -> Tuple[GeometryGroup, Node] | None:
    vertical_projection_line = AppliedVector(
        start_point=Point(midpoint_node.X, midpoint_node.Y, midpoint_node.Z),
        vector=Vector(ctx.zero_length, ctx.zero_length, -1 * units.m),
    )

    for chord_group in chord_groups:
        chord_props = require_chord_properties(chord_group)
        chord_nodes = _resolve_bracing_member_nodes(
            ctx,
            reference_start=reference_start,
            reference_end=reference_end,
            reference_unit=reference_unit,
            left_horizontal_offset=bracing_props.bracing_details.horizontal_offset_at_left,
            right_horizontal_offset=bracing_props.bracing_details.horizontal_offset_at_right,
            left_vertical_offset=chord_props.vertical_offset_at_left,
            right_vertical_offset=chord_props.vertical_offset_at_right,
        )
        chord_avg_z = cast(Quantity, (chord_nodes[0].Z + chord_nodes[1].Z) / 2)
        if chord_avg_z >= midpoint_node.Z:
            continue

        chord_segment = AppliedVector.from_points(
            Point(chord_nodes[0].X, chord_nodes[0].Y, chord_nodes[0].Z),
            Point(chord_nodes[1].X, chord_nodes[1].Y, chord_nodes[1].Z),
        )
        projected_point = GeometryTools.project_node_on_segment(
            line=vertical_projection_line,
            segment=chord_segment,
            tol=ctx.tolerance,
        )
        if projected_point is None:
            continue

        projected_node = ctx.amm.get_or_create_node(
            projected_point.x, projected_point.y, projected_point.z)
        return chord_group, projected_node

    return None
