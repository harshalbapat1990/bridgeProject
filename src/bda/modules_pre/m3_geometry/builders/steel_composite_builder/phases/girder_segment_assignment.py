"""Girder-segment-assignment phase: wraps girder finite elements into SEGMENT
groups (per cracking/splice/pouring state), resolves per-segment sections with
materials and offsets, and adds vertical end links."""
from __future__ import annotations

from copy import deepcopy
from typing import Iterable, cast

from pint.registry import Quantity

from bda.domain.enums import OffsetReference, StructuralComponentType
from bda.domain.models.submodels import Element1D
from bda.domain.models.submodels.element import LinkType
from bda.domain.models.submodels.geometry_group import GeometryGroup
from bda.domain.models.submodels.geometry_group_props.shared import GroupPropertiesSegment
from bda.domain.models.submodels.section_base import Offset, Section
from bda.domain.models.submodels.sections import (
    DimensionsCompositeSteelIAsymmetric,
    DimensionsCompositeSteelISymmetric,
    SectionCompositeBase,
    SectionCompositeSteelIAsymmetric,
    SectionCompositeSteelISymmetric,
    SectionTapered,
)
from bda.domain.units.quantities import Length
from bda.modules_pre.m3_geometry.builders.steel_composite_builder import node_utils
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.context import (
    BuildContext,
    SpanState,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.group_collectors import (
    collect_girders_for_span, collect_sup_to_sup_groups_for_span_index,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.group_property_getters import (
    require_deck_base_section,
    require_deck_group_for_span,
    require_girder_group_for_index,
    require_segment_properties,
    require_weightless_material,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.node_utils import are_same_node


def run(ctx: BuildContext) -> None:
    for state in ctx.span_states:
        _assign_girder_segment_groups(ctx, state)


def _assign_girder_segment_groups(ctx: BuildContext, state: SpanState) -> None:
    # Segment boundaries are precomputed from cracking extents, deck pouring stages, and splice locations.
    girder_groups = collect_girders_for_span(state.span)
    span_index = state.span_props.span_index

    for idx, elements in state.elements_per_girder.items():
        girder_group = require_girder_group_for_index(
            girder_groups=girder_groups,
            girder_index=idx,
            span_index=span_index,
        )

        _add_vertical_links_at_girder_ends(
            ctx,
            girder_group=girder_group,
            elements=elements,
            span_index=span_index
        )

        for seg_index, segment in enumerate(state.girder_segments[idx]):
            segment_elements = [
                e for e in elements
                if segment.x_start <= e.mid_point.X <= segment.x_end
            ]

            segment_group = GeometryGroup(
                name=f"Span{span_index}_Girder{idx}_Segment{seg_index}",
                component_type=StructuralComponentType.SEGMENT,
                section_uid=segment.splice_sectionId,
                properties=GroupPropertiesSegment(
                    segment_index=seg_index,
                    is_cracked=segment.cracked_section,
                    construction_sequence_stage_index=segment.deck_pouring_index,
                ),
            )
            girder_group.add_nested_group(segment_group)
            ctx.amm.add_elements(segment_group, segment_elements)
            section = resolve_section_for_segment(ctx, segment_group)
            section.name = f"Sp{span_index}_G{idx}_Seg{seg_index}_{section.name}"


def _add_vertical_links_at_girder_ends(
    ctx: BuildContext,
    girder_group: GeometryGroup,
    elements: Iterable[Element1D],
    span_index: int,
) -> None:
    """Attach rigid links at girder start/end nodes down by section total height."""
    elements = list(elements)
    if not elements:
        return

    root_group = girder_group.get_parent_group_by_component_type(StructuralComponentType.BRIDGE)
    if root_group is None:
        raise ValueError(
            f"Failed to find root bridge group for girder group {girder_group.name}."
        )

    girder_index = girder_group.properties.girder_index

    section_total_height = _resolve_section_total_height_for_group(girder_group)
    all_nodes = [
        node
        for element in elements
        for node in (element.node_start, element.node_end)
    ]
    start_node = min(all_nodes, key=lambda node: node.X.to_base_units().magnitude)
    end_node = max(all_nodes, key=lambda node: node.X.to_base_units().magnitude)

    end_nodes = [end_node] if node_utils.are_same_node(start_node, end_node) or span_index>0 else [end_node, start_node]

    sup_to_sub_linkage_groups = collect_sup_to_sup_groups_for_span_index(span_index, root_group)

    for idx, node in enumerate(end_nodes):
        lowered_node = ctx.amm.get_or_create_node(
            node.X,
            node.Y,
            cast(Quantity, node.Z - section_total_height),
        )
        if are_same_node(node, lowered_node):
            continue

        ctx.amm.create_and_add_link(girder_group, node,
                lowered_node,
                LinkType.RIGID)

        linkage_group = sup_to_sub_linkage_groups[1 - idx]
        ctx.amm.add_bearing_nodes(linkage_group, 
            girder_index=girder_index,
            bearing_index=0,
            node_start=lowered_node,
            node_end=None,
        )


def _resolve_section_total_height_for_group(group: GeometryGroup) -> Quantity:
    section = group.get_section()
    if section is None:
        raise ValueError(f"Group {group.name} has no section assigned.")

    if section.dimensions is None:
        raise TypeError(f"Section for group {group.name} does not expose dimensions.")

    return section.dimensions.total_height


def resolve_section_for_segment(ctx: BuildContext, segment_group: GeometryGroup) -> Section:
    """Resolve the per-segment section copy with materials and section offset."""
    segment_props = require_segment_properties(segment_group)

    final_section = _resolve_section_for_girder_segment_group(ctx, segment_group)

    if segment_props.is_cracked:
        final_section = final_section  # TODO: cracked-section resolution to be implemented later

    # assign main material to the section
    final_section.set_material_main(segment_group.get_material())

    # assign main material to belonging sections if the section is tapered
    if isinstance(final_section, SectionTapered):
        if final_section.section_start is not None:
            final_section.section_start.set_material_main(final_section.material_main)
        if final_section.section_end is not None:
            final_section.section_end.set_material_main(final_section.material_main)

    # assign materials to the section if it is a composite section
    # deck material is concluded from the nearest deck group
    if isinstance(final_section, SectionCompositeBase):
        span_group = segment_group.get_parent_group_by_component_type(StructuralComponentType.SPAN)
        deck_group = next(iter(span_group.get_groups_by_component_type(StructuralComponentType.DECK_SLAB)), None)
        if deck_group is not None:
            final_section.set_material_composite(
                require_weightless_material(ctx, deck_group.get_material())
            )

    _apply_girder_section_offset(ctx, segment_group=segment_group, section=final_section)

    return final_section


def _resolve_section_for_girder_segment_group(ctx: BuildContext, segment_group: GeometryGroup) -> Section:
    """Deep-copy the group/parent/splice section; for composite girders keep the
    parent composite type and slab, replacing only the steel-girder dimensions."""
    all_sections = ctx.amm.get_all_sections()

    base_section: Section
    if (section := segment_group.section) is not None:
        base_section = section
    elif segment_group.section_uid is not None:
        found_section = next((s for s in all_sections if s.guid == segment_group.section_uid), None)
        if found_section is None:
            raise ValueError(f"Section with ID {segment_group.section_uid} not found.")
        base_section = found_section
    else:
        parent_section = segment_group.get_section()
        if parent_section is None:
            parent_name = segment_group.parent_group.name if segment_group.parent_group is not None else segment_group.name
            raise ValueError(f"Section for group {parent_name} not found.")
        base_section = next((s for s in all_sections if s.guid == parent_section.guid), parent_section)

    origin_section = segment_group.parent_group.get_section()
    if origin_section is not None and isinstance(origin_section, SectionCompositeBase) and \
            isinstance(base_section, SectionCompositeBase):
        # replace only steel section dimensions and keep type and slab the same
        match origin_section:
            case SectionCompositeSteelISymmetric():
                resolved_section = deepcopy(origin_section)
                base_dims = base_section.dimensions
                new_dims = resolved_section.dimensions

                if isinstance(base_dims, DimensionsCompositeSteelISymmetric):
                    new_dims.girder_web_thickness_tw = base_dims.girder_web_thickness_tw
                    new_dims.girder_top_flange_width_b1 = base_dims.girder_top_flange_width_b1
                    new_dims.girder_bottom_flange_thickness_tf2 = base_dims.girder_bottom_flange_thickness_tf2
                    new_dims.girder_bottom_flange_width_b2 = base_dims.girder_bottom_flange_width_b2
                    new_dims.girder_top_flange_thickness_tf1 = base_dims.girder_top_flange_thickness_tf1
                    new_dims.girder_web_height_hw = base_dims.girder_web_height_hw

                elif isinstance(base_dims, DimensionsCompositeSteelIAsymmetric):
                    new_dims.girder_web_thickness_tw = base_dims.girder_web_thickness_tw
                    new_dims.girder_top_flange_width_b1 = (base_dims.girder_top_flange_left_width_b1
                                                           + base_dims.girder_top_flange_right_width_b2)
                    new_dims.girder_bottom_flange_thickness_tf2 = base_dims.girder_bottom_flange_thickness_t2
                    new_dims.girder_bottom_flange_width_b2 = (base_dims.girder_bottom_flange_left_width_b3
                                                              + base_dims.girder_bottom_flange_right_width_b4)
                    new_dims.girder_top_flange_thickness_tf1 = base_dims.girder_top_flange_thickness_t1
                    new_dims.girder_web_height_hw = base_dims.girder_web_height_h

                else:
                    raise NotImplementedError(
                        f"This type of composite section is not supported yet: {type(base_section)}")

            case SectionCompositeSteelIAsymmetric():
                resolved_section = deepcopy(origin_section)
                base_dims = base_section.dimensions
                new_dims = resolved_section.dimensions

                if isinstance(base_dims, DimensionsCompositeSteelISymmetric):
                    new_dims.girder_web_thickness_tw = base_dims.girder_web_thickness_tw
                    new_dims.girder_web_height_h = base_dims.girder_web_height_hw
                    new_dims.girder_top_flange_thickness_t1 = base_dims.girder_top_flange_thickness_tf1
                    new_dims.girder_bottom_flange_thickness_t2 = base_dims.girder_bottom_flange_thickness_tf2
                    new_dims.girder_top_flange_left_width_b1 = cast(
                        Length, 0.5 * base_dims.girder_top_flange_width_b1)
                    new_dims.girder_top_flange_right_width_b2 = cast(
                        Length, 0.5 * base_dims.girder_top_flange_width_b1)
                    new_dims.girder_bottom_flange_left_width_b3 = cast(
                        Length, 0.5 * base_dims.girder_bottom_flange_width_b2)
                    new_dims.girder_bottom_flange_right_width_b4 = cast(
                        Length, 0.5 * base_dims.girder_bottom_flange_width_b2)

                elif isinstance(base_dims, DimensionsCompositeSteelIAsymmetric):
                    new_dims.girder_web_thickness_tw = base_dims.girder_web_thickness_tw
                    new_dims.girder_web_height_h = base_dims.girder_web_height_h
                    new_dims.girder_top_flange_thickness_t1 = base_dims.girder_top_flange_thickness_t1
                    new_dims.girder_bottom_flange_thickness_t2 = base_dims.girder_bottom_flange_thickness_t2
                    new_dims.girder_top_flange_left_width_b1 = base_dims.girder_top_flange_left_width_b1
                    new_dims.girder_top_flange_right_width_b2 = base_dims.girder_top_flange_right_width_b2
                    new_dims.girder_bottom_flange_left_width_b3 = base_dims.girder_bottom_flange_left_width_b3
                    new_dims.girder_bottom_flange_right_width_b4 = base_dims.girder_bottom_flange_right_width_b4

                else:
                    raise NotImplementedError(
                        f"This type of composite section is not supported yet: {type(base_section)}")

            case _:
                raise NotImplementedError(
                    f"This type of composite section is not supported yet: {type(origin_section)}")
    else:
        resolved_section = deepcopy(base_section)

    segment_group.section = resolved_section
    return resolved_section


def _apply_girder_section_offset(ctx: BuildContext, segment_group: GeometryGroup, section: Section) -> None:
    """Offset the girder section so its reference point sits on the deck plane."""
    girder_group = segment_group.get_parent_group_by_component_type(StructuralComponentType.GIRDER)
    if girder_group is None:
        return

    span_group = segment_group.get_parent_group_by_component_type(StructuralComponentType.SPAN)
    if span_group is None:
        return

    deck_group = require_deck_group_for_span(ctx, span_group)
    deck_base_section = require_deck_base_section(deck_group)
    deck_thickness = deck_base_section.dimensions.height_h

    vertical_offset = deck_thickness
    if isinstance(section, SectionCompositeBase) and isinstance(
        section.dimensions,
        (DimensionsCompositeSteelISymmetric, DimensionsCompositeSteelIAsymmetric),
    ):
        vertical_offset = section.dimensions.slab_thickness_tc

    offset_reference = OffsetReference.CENTER_TOP
    horizontal_offset = ctx.zero_length

    if isinstance(section, SectionCompositeSteelIAsymmetric):
        dims = section.dimensions
        offset_reference = OffsetReference.LEFT_TOP
        horizontal_offset = cast(
            Quantity,
            dims.top_flange_distance_rf_top
            + dims.girder_top_flange_left_width_b1
            + 0.5 * dims.girder_web_thickness_tw,
        )

    section.offset = Offset(
        offset_reference=offset_reference,
        horizontal_value=horizontal_offset,
        vertical_value=vertical_offset,
    )
