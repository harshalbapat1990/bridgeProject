from __future__ import annotations

from copy import deepcopy
from typing import cast

from pint.registry import Quantity

import bda.domain.units.registry as units
from bda.domain.enums import StructuralComponentType
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.build_context import (
    GeometrySteelCompositeBuildContext,
)
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.deck_assignment import (
    assign_deck_segment_groups,
    assign_deck_boundary_elements_group_for_bridge_end,
)
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.deck_resolvers import (
    resolve_sections_for_entire_bridge,
    resolve_bridge_edge_beam_segments,
)


def process_deck_for_entire_bridge(builder, ctx: GeometrySteelCompositeBuildContext) -> None:
    if not ctx.deck_spans_data:
        return

    deck_groups = ctx.geometry.get_groups_by_component_type(StructuralComponentType.DECK_SLAB)

    for dg in deck_groups:
        original_material = dg.get_material()
        new_material = builder.require_weightless_material(original_material)
        dg.material = new_material

    deck_tol = 0.1 * units.mm
    all_transverse_deck_strips = [
        strip
        for data in ctx.deck_spans_data
        for strip in data.transverse_deck_strips
    ]

    sections = list(resolve_sections_for_entire_bridge(
        builder=builder,
        span_deck_data=ctx.deck_spans_data,
        transverse_deck_strips=all_transverse_deck_strips,
        deck_tolerance=deck_tol,
    ))
    bridge_edge_beam_segments = resolve_bridge_edge_beam_segments(
        builder=builder,
        span_deck_data=ctx.deck_spans_data,
        y_offsets_edge_beams=ctx.y_offsets_edge_beams,
    )
    sorted_by_offset = sorted(ctx.deck_spans_data, key=lambda d: d.span_offset.to_base_units().magnitude)
    first_span_data = sorted_by_offset[0]
    last_span_data = max(
        ctx.deck_spans_data,
        key=lambda d: cast(Quantity, d.span_offset + d.span_reference_data.span_length).to_base_units().magnitude,
    )

    for data in ctx.deck_spans_data:
        deck_elements_by_section_uid = builder._generate_finite_elements_for_deck(
            transverse_deck_strips=data.transverse_deck_strips,
            y_offsets_girders=ctx.y_offsets_girders,
            bridge_edge_beam_segments=bridge_edge_beam_segments,
            deck_cross_sections=sections,
            deck_tol=deck_tol,
        )

        assign_deck_segment_groups(
            builder=builder,
            span=data.span,
            span_props=data.span_props,
            span_offset=data.span_offset,
            span_reference_data=data.span_reference_data,
            deck_elements_by_section_uid=deck_elements_by_section_uid,
            sections=sections,
            y_offsets_girders=ctx.y_offsets_girders,
        )

        if data is first_span_data:
            assign_deck_boundary_elements_group_for_bridge_end(
                builder=builder,
                span_data=data,
                is_bridge_start=True,
            )

        if data is last_span_data:
            assign_deck_boundary_elements_group_for_bridge_end(
                builder=builder,
                span_data=data,
                is_bridge_start=False,
            )

    builder._generate_finite_elements_for_edge_beams_for_bridge(
        span_deck_data=ctx.deck_spans_data,
        bridge_edge_beam_segments=bridge_edge_beam_segments,
    )

    ctx.deck_spans_data.clear()


