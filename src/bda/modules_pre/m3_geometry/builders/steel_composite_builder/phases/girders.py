"""Girders phase: mesh breakpoints, deck strips, splice/crack data,
segment resolution and girder finite elements for every span."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, cast

from pint.registry import Quantity

from bda.domain.models.submodels import Element1D
import bda.modules_pre.m3_geometry.helpers.tools.general_tools as tools
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.context import (
    BuildContext,
    SpanState,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.meshing.bracing_breakpoints import (
    split_span_at_bracings,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.meshing.girder_segments import (
    split_span_into_girder_segments,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.meshing.transverse_strips import (
    split_span_into_transverse_elements,
)


def run(ctx: BuildContext) -> None:
    _resolve_bracing_breakpoints(ctx)
    _resolve_deck_strips(ctx)
    _resolve_splices(ctx)
    _resolve_cracked_extents(ctx)
    _resolve_girder_segments(ctx)
    _generate_finite_elements(ctx)


def _resolve_bracing_breakpoints(ctx: BuildContext) -> None:
    for state in ctx.span_states:
        state.bracing_breakpoints = split_span_at_bracings(
            state.reference_data.transverse_bracings_ref_elements
        )


def _resolve_deck_strips(ctx: BuildContext) -> None:
    mesh_divisor = ctx.require_girder_mesh_divisor()

    for state in ctx.span_states:
        state.transverse_deck_strips = list(
            split_span_into_transverse_elements(
                span_length=state.span_props.span_length,
                girders=state.reference_data.girder_ref_elements,
                mesh_divisor=mesh_divisor,
                mesh_type=ctx.grillage_type,
                bridge_main_direction=ctx.bridge_direction_vector,
                support_i_vector=state.reference_data.support_i_vector,
            )
        )


def _resolve_splices(ctx: BuildContext) -> None:
    for state in ctx.span_states:
        state.include_splice = True
        state.splices = list(state.span_props.splices or [])


def _resolve_cracked_extents(ctx: BuildContext) -> None:
    for state in ctx.span_states:
        state.cracked_extents = list(state.span_props.cracked_extends or [])


def _resolve_girder_segments(ctx: BuildContext) -> None:
    for state in ctx.span_states:
        splices = state.splices if state.include_splice else []
        state.girder_segments = split_span_into_girder_segments(
            girders=state.reference_data.girder_ref_elements,
            span_offset=state.span_offset,
            splices=splices,
            cracked_extents=state.cracked_extents,
            construction_sequence_details=state.construction_sequence_details,
            tolerance=ctx.tolerance,
        )


def _generate_finite_elements(ctx: BuildContext) -> None:
    for state in ctx.span_states:
        state.elements_per_girder = _generate_finite_elements_for_span(ctx, state)


def _generate_finite_elements_for_span(ctx: BuildContext, state: SpanState) -> Dict[int, List[Element1D]]:
    """Split each girder at segment/strip/bracing breakpoints and create beam elements."""
    elements: Dict[int, List[Element1D]] = defaultdict(list)

    points_per_girder: Dict[int, List[Quantity]] = defaultdict(list)

    for idx, girder in state.reference_data.girder_ref_elements.items():
        points_per_girder[idx].extend([
            cast(Quantity, girder.node_start.X),
            cast(Quantity, girder.node_end.X)])

        points_per_girder[idx].extend([
            x for s in state.girder_segments[idx] for x in (s.x_start, s.x_end)
        ])

        points_per_girder[idx].extend([
            s.points_per_girder[idx]
            for s in state.transverse_deck_strips
            if idx in s.points_per_girder
        ])

        points_per_girder[idx].extend(state.bracing_breakpoints.get(idx, []))

    for idx, points in points_per_girder.items():
        sorted_points = list(tools.to_sorted_unique_collection(points, ctx.tolerance))
        for i in range(len(sorted_points) - 1):
            ni = ctx.amm.get_or_create_node(
                sorted_points[i],
                ctx.y_offsets_girders[idx],
                ctx.zero_length)
            nj = ctx.amm.get_or_create_node(
                sorted_points[i + 1],
                ctx.y_offsets_girders[idx],
                ctx.zero_length)
            elements[idx].append(ctx.amm.get_or_create_beam(ni, nj))

    return elements
