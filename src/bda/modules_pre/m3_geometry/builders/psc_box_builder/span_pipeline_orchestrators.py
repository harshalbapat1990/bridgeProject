import uuid
from typing import cast, List

from pint.registry import Quantity

import bda.domain.units.registry as units
from bda.domain.models.submodels import GeometryGroup
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import GroupPropertiesSpan
from bda.modules_pre.m3_geometry.builders.psc_box_builder.build_context import SpanReferenceData, SpanBuildState, \
    GeometryPSCBoxBuildContext
from bda.modules_pre.m3_geometry.builders.psc_box_builder.group_property_getters import GroupPropertyGetter
from bda.modules_pre.m3_geometry.helpers.psc_box_helpers import split_span_into_segments
from bda.domain.enums import StructuralComponentType
from bda.domain.models.submodels import Element1D
from bda.domain.models.submodels.sections import SectionTapered


def initialize_span_states(ctx: GeometryPSCBoxBuildContext) -> None:
    """
    Step 1: Initialize build states for all spans.

    Iterates through all spans, determines their global offset
    along the bridge axis, and creates a SpanBuildState instance
    containing the span reference data.
    """
    if ctx.geometry is None:
        raise ValueError("Build context has no geometry.")
    if ctx.girder_mesh_divisor is None:
        raise ValueError("Build context has no girder mesh divisor.")

    ctx.span_states.clear()
    span_offset: Quantity = 0.0 * units.m

    for span in ctx.spans.values():
        span_props: GroupPropertiesSpan = GroupPropertyGetter.get_span_properties(span)
        span_length = span_props.span_length

        span_reference_data = SpanReferenceData(
            span_length=span_length,
            x_offset=span_offset,
        )

        ctx.span_states.append(
            SpanBuildState(
                span=span,
                span_props=span_props,
                span_offset=span_offset,
                span_reference_data=span_reference_data,
            )
        )

        span_offset = cast(Quantity, span_offset + span_length)


def split_spans_into_segments(ctx: GeometryPSCBoxBuildContext) -> None:
    """
    Step 2: Split each span into geometric segments.

    Creates segments representing regions with constant cross-sections
    and tapered transition zones, and stores them in the build state
    of each span.
    """
    for state in ctx.span_states:
        tapered_details = state.span_props.tapered_details or []

        state.segments = split_span_into_segments(
            span_length=state.span_props.span_length,
            tapered_details=tapered_details,
            tolerance=1 * units.mm,
        )

        ctx.logger.debug(
            "[PSCBoxBuilder] Split span '%s' into %d segments",
            state.span.name,
            len(state.segments),
        )


def generate_span_finite_elements(ctx: GeometryPSCBoxBuildContext) -> None:
    """
    Step 3: Generate finite elements for all spans.

    Creates nodes and beam elements based on the specified mesh
    subdivision. The generated elements are temporarily stored
    for later assignment to segment groups.
    """
    if ctx.girder_mesh_divisor is None:
        raise ValueError("Build context has no girder mesh divisor.")

    all_sections = ctx.amm.get_all_sections()
    sections_by_guid = {s.guid: s for s in all_sections}

    for state in ctx.span_states:
        _generate_elements_for_span(ctx, state, sections_by_guid)


def _generate_elements_for_span(
    ctx: GeometryPSCBoxBuildContext,
    state: SpanBuildState,
    sections_by_guid: dict,
) -> None:
    span = state.span
    span_props = state.span_props
    offset = state.span_offset
    span_length = span_props.span_length
    mesh_divisor = ctx.girder_mesh_divisor

    try:
        delta = cast(Quantity, span_length / mesh_divisor)
    except ZeroDivisionError:
        raise ValueError(f"Span '{span.name}': mesh_divisor cannot be zero.")

    # PSC Box has 1 GIRDER group per span
    girder_groups = span.get_groups_by_component_type(StructuralComponentType.GIRDER)
    if not girder_groups:
        raise ValueError(f"No GIRDER group found under span '{span.name}'.")
    girder: GeometryGroup = girder_groups[0]

    y = 0.0 * units.m

    # 1. Reference element for the whole span
    node_start = ctx.amm.get_or_create_node(x=offset, y=y, z=0.0 * units.m)
    node_end = ctx.amm.get_or_create_node(x=offset + span_length, y=y, z=0.0 * units.m)
    reference_element = ctx.amm.create_and_add_reference_element(girder, node_start, node_end)

    # 2. Base mesh determined from: mesh_divisor
    x_positions: List[Quantity] = [
        offset + i * delta for i in range(mesh_divisor + 1)
    ]

    # 3. Append segment boundaries
    for seg in state.segments:
        x_positions.append(offset + seg.x_start)
        x_positions.append(offset + seg.x_end)

    # 4. Sort and deduplicate
    x_positions = sorted(
        {x.to_base_units().magnitude: x for x in x_positions}.values(),
        key=lambda x: x.to_base_units().magnitude,
    )

    # 5. Create finite elements
    elements: List[Element1D] = []
    for i in range(len(x_positions) - 1):
        ni = ctx.amm.get_or_create_node(x_positions[i], y, 0.0 * units.m)
        nj = ctx.amm.get_or_create_node(x_positions[i + 1], y, 0.0 * units.m)
        element = ctx.amm.get_or_create_beam(ni, nj)
        elements.append(element)

    # Save elements to the state (it will be used in: finalize_span_segment_groups)
    state._elements = elements


def finalize_span_segment_groups(ctx: GeometryPSCBoxBuildContext) -> None:
    """
    Step 4: Assign finite elements to SEGMENT subgroups under each GIRDER group.

    Creates segment subgroups, assigns the corresponding finite elements,
    and resolves the appropriate section for each segment, including
    tapered section transitions.
    """
    all_sections = ctx.amm.get_all_sections()
    sections_by_guid = {s.guid: s for s in all_sections}

    for state in ctx.span_states:
        girder_groups = state.span.get_groups_by_component_type(StructuralComponentType.GIRDER)
        if not girder_groups:
            continue
        girder: GeometryGroup = girder_groups[0]

        elements: List[Element1D] = getattr(state, "_elements", [])
        offset = state.span_offset
        current_section = state.span.section

        for segment in state.segments:
            included_elements = [
                e for e in elements
                if segment.x_start + offset <= (e.node_start.X + e.node_end.X) / 2 <= segment.x_end + offset
            ]

            if segment.section_id is None:
                section = current_section
            else:
                section = sections_by_guid.get(segment.section_id)
                if section is None:
                    raise ValueError(
                        f"Span '{state.span.name}': section {segment.section_id} not found."
                    )

            sub_group = GeometryGroup(
                guid=uuid.uuid4(),
                component_type=StructuralComponentType.SEGMENT,
                name=f"Span_{state.span_props.span_index}_Segment_{segment.segment_index}",
                section_uid=section.guid if section else None,
                section=section,
            )
            sub_group.add_analytical_elements(included_elements)
            girder.add_nested_group(sub_group)

            # If the segment uses a tapered section, update the current section
            # to the end section after the transition.
            if isinstance(section, SectionTapered):
                current_section = section.section_end

        ctx.logger.debug(
            "[PSCBoxBuilder] Finalized span '%s': %d sub-groups created under girder '%s'",
            state.span.name,
            len(state.segments),
            girder.name,
        )