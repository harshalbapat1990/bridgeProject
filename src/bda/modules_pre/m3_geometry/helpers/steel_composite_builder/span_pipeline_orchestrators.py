from __future__ import annotations

from typing import cast

from pint.registry import Quantity

from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.build_context import (
    GeometrySteelCompositeBuildContext,
    SpanBuildState,
    DeckSpanData,
)
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.split_span_at_bracings import (
    split_span_at_bracings,
)
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.split_span_into_girder_segments_ import (
    split_span_into_girder_segments,
)
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.split_span_into_transverse_elements import (
    split_span_into_transverse_elements,
)
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.girder_segment_assignment import (
    assign_girder_segment_groups,
)


def initialize_span_states(builder, ctx: GeometrySteelCompositeBuildContext) -> None:
    if ctx.geometry is None:
        raise ValueError("Build context has no geometry.")
    if ctx.girder_mesh_divisor is None:
        raise ValueError("Build context has no girder mesh divisor.")

    ctx.span_states.clear()
    span_offset: Quantity = builder.zero_length

    for span in ctx.spans:
        span_props = builder._require_span_properties(span)
        span_reference_data = builder._build_span_reference_data(
            span=span,
            span_props=span_props,
            span_offset=span_offset,
            support_angles=ctx.support_angles,
            grillage_type=ctx.grillage_type,
            y_offsets_girders=ctx.y_offsets_girders,
            y_offsets_edge_beams=ctx.y_offsets_edge_beams,
        )
        ctx.span_states.append(
            SpanBuildState(
                span=span,
                span_props=span_props,
                span_offset=span_offset,
                span_reference_data=span_reference_data,
                construction_sequence_details=span_props.construction_sequence_details,
            )
        )
        span_offset = cast(Quantity, span_offset + span_reference_data.span_length)


def resolve_span_bracing_breakpoints(builder, ctx: GeometrySteelCompositeBuildContext) -> None:
    for state in ctx.span_states:
        state.bracing_breakpoints = split_span_at_bracings(
            state.span_reference_data.transverse_bracings_ref_elements
        )


def resolve_span_deck_strips(builder, ctx: GeometrySteelCompositeBuildContext) -> None:
    if ctx.girder_mesh_divisor is None:
        raise ValueError("Build context has no girder mesh divisor.")

    for state in ctx.span_states:
        state.transverse_deck_strips = list(
            split_span_into_transverse_elements(
                span_length=state.span_props.span_length,
                girders=state.span_reference_data.girder_ref_elements,
                mesh_divisor=ctx.girder_mesh_divisor,
                mesh_type=ctx.grillage_type,
                bridge_main_direction=builder._bridge_direction_vector,
                support_i_vector=state.span_reference_data.support_i_vector,
            )
        )


def resolve_span_include_splice(builder, ctx: GeometrySteelCompositeBuildContext) -> None:
    for state in ctx.span_states:
        state.include_splice = True
        state.splices = list(state.span_props.splices or [])


def resolve_span_crack_extents(builder, ctx: GeometrySteelCompositeBuildContext) -> None:
    for state in ctx.span_states:
        state.cracked_extents = list(state.span_props.cracked_extends or [])


def resolve_span_girder_segments(builder, ctx: GeometrySteelCompositeBuildContext) -> None:
    for state in ctx.span_states:
        splices = state.splices if state.include_splice else []
        state.girder_segments = split_span_into_girder_segments(
            girders=state.span_reference_data.girder_ref_elements,
            span_offset=state.span_offset,
            splices=splices,
            cracked_extents=state.cracked_extents,
            construction_sequence_details=state.construction_sequence_details,
            tolerance=builder._tolerance,
        )


def generate_span_girder_finite_elements(builder, ctx: GeometrySteelCompositeBuildContext) -> None:
    for state in ctx.span_states:
        state.elements_per_girder = builder._generate_finite_elements_for_girders(
            girder_y_offsets=ctx.y_offsets_girders,
            girders_ref_elements=state.span_reference_data.girder_ref_elements,
            girders_segments=state.girder_segments,
            transverse_deck_strips=state.transverse_deck_strips,
            bracing_breakpoints=state.bracing_breakpoints,
        )


def finalize_span_girder_segments(builder, ctx: GeometrySteelCompositeBuildContext) -> None:
    for state in ctx.span_states:
        girder_groups = builder._collect_girders_for_span(state.span)
        assign_girder_segment_groups(
            builder=builder,
            span_props=state.span_props,
            girder_groups=girder_groups,
            elements_per_girder=state.elements_per_girder,
            girder_segments=state.girder_segments,
        )

        ctx.deck_spans_data.append(
            DeckSpanData(
                span=state.span,
                span_props=state.span_props,
                span_offset=state.span_offset,
                span_reference_data=state.span_reference_data,
                transverse_deck_strips=state.transverse_deck_strips,
            )
        )


def generate_span_bracings(builder, ctx: GeometrySteelCompositeBuildContext) -> None:
    for state in ctx.span_states:
        builder._generate_finite_elements_for_bracings_for_span(span=state.span)


def generate_span_diaphragms(builder, ctx: GeometrySteelCompositeBuildContext) -> None:
    for state in ctx.span_states:
        builder._generate_finite_elements_for_diaphragms_for_span(span=state.span)


def generate_span_plan_bracings(builder, ctx: GeometrySteelCompositeBuildContext) -> None:
    for state in ctx.span_states:
        builder._generate_finite_elements_for_plan_bracings_for_span(
            span=state.span,
            reference_data=state.span_reference_data)