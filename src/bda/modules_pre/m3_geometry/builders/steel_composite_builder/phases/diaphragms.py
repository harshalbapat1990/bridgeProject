"""Diaphragms phase: finite elements for modelled diaphragms at span supports."""
from __future__ import annotations

from bda.domain.enums import OffsetReference, StructuralComponentType
from bda.domain.models.submodels import Element1D
from bda.domain.models.submodels.geometry_group import GeometryGroup
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import (
    DiaphragmBracingEncasedDetails,
    DiaphragmConcreteNonModelledDetails,
    DiaphragmSteelGirderDetails,
)
from bda.domain.models.submodels.section_base import Offset, Section
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.context import BuildContext
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.group_collectors import (
    collect_diaphragms_for_span,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.group_property_getters import (
    require_deck_base_section,
    require_deck_group_for_span,
    require_diaphragm_properties,
)


def run(ctx: BuildContext) -> None:
    for state in ctx.span_states:
        _generate_finite_elements_for_span(ctx, state.span)


def _generate_finite_elements_for_span(ctx: BuildContext, span: GeometryGroup) -> None:
    """Build all diaphragm finite elements for a single span."""
    for diaphragm_group in collect_diaphragms_for_span(span):
        diaphragm_props = require_diaphragm_properties(diaphragm_group)

        # Non-modelled concrete diaphragms stay as metadata/reference only.
        if isinstance(diaphragm_props.geometry_details, DiaphragmConcreteNonModelledDetails):
            continue

        diaphragm_section = diaphragm_group.get_section()
        _apply_diaphragm_section_offset(ctx, diaphragm_group, diaphragm_section)

        for reference_element in diaphragm_group.reference_elements:
            if not isinstance(reference_element, Element1D):
                continue

            ctx.amm.create_and_add_beam(diaphragm_group, reference_element.node_start,
                    reference_element.node_end)


def _apply_diaphragm_section_offset(
    ctx: BuildContext,
    diaphragm_group: GeometryGroup,
    section: Section,
) -> None:
    """Offset the diaphragm section to hang below the deck according to its type."""
    diaphragm_props = require_diaphragm_properties(diaphragm_group)

    span_group = diaphragm_group.get_parent_group_by_component_type(StructuralComponentType.SPAN)
    if span_group is None:
        return

    vertical_offset = ctx.zero_length
    if isinstance(diaphragm_props.geometry_details, DiaphragmBracingEncasedDetails):
        deck_group = require_deck_group_for_span(ctx, span_group)
        deck_base_section = require_deck_base_section(deck_group)
        vertical_offset = deck_base_section.dimensions.height_h
    elif not isinstance(diaphragm_props.geometry_details, DiaphragmSteelGirderDetails):
        return

    section.offset = Offset(
        offset_reference=OffsetReference.CENTER_TOP,
        horizontal_value=ctx.zero_length,
        vertical_value=vertical_offset,
    )
