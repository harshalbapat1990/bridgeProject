"""Preparations phase: collect input groups, resolve bridge layout and
initialize per-span working states with reference geometry."""
from __future__ import annotations

from typing import Dict, cast

from pint.registry import Quantity

from bda.domain.models.submodels.geometry_group import GeometryGroup
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import (
    ElementOrientation,
    SpacingType,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.constants import (
    SKEW_MESH_ANGLE_LIMIT_ABS_DEG,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.context import (
    BuildContext,
    SpanState,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.group_collectors import (
    collect_spans,
    collect_support_angles,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.group_property_getters import (
    require_bridge_properties,
    require_span_properties,
    require_superstructure_properties,
    require_support_angle,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.reference_geometry import (
    build_span_reference_data,
)


def run(ctx: BuildContext) -> None:
    _collect_geometry_root(ctx)
    _collect_spans(ctx)
    _collect_support_angles(ctx)
    _resolve_bridge_layout(ctx)
    _resolve_grillage_type(ctx)
    _initialize_span_states(ctx)


def _collect_geometry_root(ctx: BuildContext) -> None:
    geometry = ctx.amm.geometry_group
    if geometry is None:
        raise ValueError("AnalyticalMultiModel has no geometry_group.")
    ctx.geometry = geometry


def _collect_spans(ctx: BuildContext) -> None:
    geometry = ctx.require_geometry()

    ctx.logger.debug(
        "[SteelCompositeBuilder] collect spans | root_group=%s",
        geometry.name,
    )
    spans = collect_spans(geometry)
    if not spans:
        raise ValueError("No SPAN groups were found.")

    ctx.spans = spans


def _collect_support_angles(ctx: BuildContext) -> None:
    geometry = ctx.require_geometry()

    ctx.logger.debug(
        "[SteelCompositeBuilder] collect support angles | root_group=%s",
        geometry.name,
    )
    support_angles = collect_support_angles(geometry)
    if not support_angles:
        raise ValueError("No SUPPORT groups were found.")
    ctx.support_angles = support_angles


def _resolve_bridge_layout(ctx: BuildContext) -> None:
    geometry = ctx.require_geometry()

    bridge_properties = require_bridge_properties(geometry)
    mesh_divisor = bridge_properties.analysis_settings.girder_mesh_divisor
    if mesh_divisor < 1:
        raise ValueError(f"Invalid girder mesh divisor {mesh_divisor}. Value must be >= 1.")

    ctx.bridge_properties = bridge_properties
    ctx.girder_mesh_divisor = mesh_divisor
    ctx.y_offsets_girders = _resolve_girder_yoffsets(ctx, geometry)
    ctx.y_offsets_edge_beams = _resolve_edge_beams_yoffsets(geometry)


def _resolve_grillage_type(ctx: BuildContext) -> None:
    first_sup_skew_angle = require_support_angle(ctx.support_angles, 0)
    ctx.grillage_type = (
        ElementOrientation.ORTHOGONAL
        if abs(first_sup_skew_angle.to("deg").magnitude) > SKEW_MESH_ANGLE_LIMIT_ABS_DEG
        else ElementOrientation.SKEWED
    )


def _initialize_span_states(ctx: BuildContext) -> None:
    ctx.require_girder_mesh_divisor()

    ctx.span_states.clear()
    span_offset: Quantity = ctx.zero_length

    for span in ctx.spans:
        span_props = require_span_properties(span)
        reference_data = build_span_reference_data(
            ctx,
            span=span,
            span_props=span_props,
            span_offset=span_offset,
        )
        ctx.span_states.append(
            SpanState(
                span=span,
                span_props=span_props,
                span_offset=span_offset,
                reference_data=reference_data,
                construction_sequence_details=span_props.construction_sequence_details,
            )
        )
        span_offset = cast(Quantity, span_offset + reference_data.span_length)


def _resolve_girder_yoffsets(ctx: BuildContext, root_group: GeometryGroup) -> Dict[int, Quantity]:
    ctx.logger.debug(
        "[SteelCompositeBuilder] resolve girder y-offsets | root_group=%s",
        root_group.name,
    )
    superstructure_props = require_superstructure_properties(root_group)

    no_of_girders = superstructure_props.no_of_girders
    spacing_values = superstructure_props.girder_spacing_values
    spacing_type = superstructure_props.girder_spacing_type

    match spacing_type:
        case SpacingType.UNIFORM:
            spacing = (no_of_girders - 1) * [spacing_values[0]]
        case SpacingType.VARIABLE:
            spacing = spacing_values
        case _:
            raise ValueError(f"Girder spacing type {spacing_type} is not supported.")

    if no_of_girders - 1 != len(spacing):
        raise ValueError(
            "Invalid number of girder spacings. "
            f"Expected {no_of_girders - 1}, got {len(spacing)}."
        )

    total_deck_width = superstructure_props.total_deck_width
    left_cantilever = superstructure_props.cantilever_left_width

    y_offsets: Dict[int, Quantity] = {}
    for i in range(no_of_girders):
        y_offsets[i] = cast(Quantity, total_deck_width / 2 - left_cantilever - sum(spacing[:i]))

    return y_offsets


def _resolve_edge_beams_yoffsets(root_group: GeometryGroup) -> Dict[int, Quantity]:
    superstructure_props = require_superstructure_properties(root_group)

    total_deck_width = superstructure_props.total_deck_width

    return {
        0: cast(Quantity, total_deck_width / 2),
        1: cast(Quantity, -total_deck_width / 2),
    }
