"""Deck phase: weightless deck materials, bridge-wide deck cross-sections and
per-span deck finite elements, segment assignment, bridge-end boundary and
bridge-long edge beams."""
from __future__ import annotations

import bda.domain.units.registry as units
from bda.domain.enums import StructuralComponentType
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.context import BuildContext
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.deck.assignment import (
    assign_deck_boundary_elements_group_for_bridge_end,
    assign_deck_segment_groups,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.deck.edge_beams import (
    generate_finite_elements_for_edge_beams_for_bridge,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.deck.finite_elements import (
    generate_finite_elements_for_deck,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.deck.resolvers import (
    resolve_bridge_edge_beam_segments,
    resolve_sections_for_entire_bridge,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.group_property_getters import (
    require_weightless_material,
)


def run(ctx: BuildContext) -> None:
    if not ctx.span_states:
        return

    _apply_weightless_deck_materials(ctx)

    deck_tol = 0.1 * units.mm
    all_transverse_deck_strips = [
        strip
        for state in ctx.span_states
        for strip in state.transverse_deck_strips
    ]

    sections = resolve_sections_for_entire_bridge(
        ctx,
        span_states=ctx.span_states,
        transverse_deck_strips=all_transverse_deck_strips,
        deck_tolerance=deck_tol,
    )
    bridge_edge_beam_segments = resolve_bridge_edge_beam_segments(ctx, ctx.span_states)

    sorted_by_offset = sorted(ctx.span_states, key=lambda s: s.span_offset.to_base_units().magnitude)
    first_span_state = sorted_by_offset[0]
    last_span_state = max(
        ctx.span_states,
        key=lambda s: s.span_end_offset.to_base_units().magnitude,
    )

    # Ascending span order matters: deck elements shared by two spans at a skewed
    # support are claimed by the earlier span (see BuildContext.claim_deck_element).
    for state in sorted_by_offset:
        deck_elements_by_section_uid = generate_finite_elements_for_deck(
            ctx,
            transverse_deck_strips=state.transverse_deck_strips,
            bridge_edge_beam_segments=bridge_edge_beam_segments,
            deck_cross_sections=sections,
            deck_tol=deck_tol,
        )

        assign_deck_segment_groups(
            ctx,
            state=state,
            deck_elements_by_section_uid=deck_elements_by_section_uid,
            sections=sections,
        )

        if state is first_span_state:
            assign_deck_boundary_elements_group_for_bridge_end(
                ctx,
                state=state,
                is_bridge_start=True,
            )

        if state is last_span_state:
            assign_deck_boundary_elements_group_for_bridge_end(
                ctx,
                state=state,
                is_bridge_start=False,
            )

    generate_finite_elements_for_edge_beams_for_bridge(
        ctx,
        span_states=ctx.span_states,
        bridge_edge_beam_segments=bridge_edge_beam_segments,
    )


def _apply_weightless_deck_materials(ctx: BuildContext) -> None:
    """Replace deck materials with weightless copies (deck self-weight is applied separately)."""
    deck_groups = ctx.require_geometry().get_groups_by_component_type(StructuralComponentType.DECK_SLAB)
    for dg in deck_groups:
        dg.material = require_weightless_material(ctx, dg.get_material())
