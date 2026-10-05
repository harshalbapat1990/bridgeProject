"""Reference-element generation for a span (girders, edge beams, bracings, diaphragms).

Reference elements describe the idealized layout lines the finite-element mesh
is later built upon.
"""
from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Dict, Iterable, List, Tuple, cast

from pint.registry import Quantity

from bda.domain.models.submodels import Element1D
from bda.domain.models.submodels.geometry_group import GeometryGroup
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import ElementOrientation
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import (
    GroupPropertiesEdgeBeam,
    GroupPropertiesGirder,
    GroupPropertiesSpan,
)
import bda.modules_pre.m3_geometry.helpers.tools.general_tools as tools
from bda.modules_pre.m3_geometry.helpers.tools.geometry_tools import GeometryTools
from bda.modules_pre.m3_geometry.helpers.tools.models import AppliedVector, Point, Vector
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.context import SpanReferenceData
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.group_collectors import (
    collect_bracings_for_span,
    collect_diaphragms_for_span,
    collect_girders_for_span,
    collect_or_create_edge_beams_for_span,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.group_property_getters import (
    require_diaphragm_properties,
    require_support_angle,
    require_transverse_bracing_properties,
)

if TYPE_CHECKING:
    from bda.modules_pre.m3_geometry.builders.steel_composite_builder.context import BuildContext


def build_span_reference_data(
    ctx: BuildContext,
    span: GeometryGroup,
    span_props: GroupPropertiesSpan,
    span_offset: Quantity,
) -> SpanReferenceData:
    span_start_point = Point(span_offset, ctx.zero_length)
    support_i_vector, support_j_vector = resolve_support_vectors_for_span(
        ctx,
        span_props,
        span_start_point,
        span_props.span_length,
    )

    girders = collect_girders_for_span(span)
    edge_beams = collect_or_create_edge_beams_for_span(ctx, span)

    ctx.logger.debug(
        "[SteelCompositeBuilder] generate reference girder elements for span | span=%s | span_index=%s",
        span.name,
        span_props.span_index,
    )

    girder_ref_elements = generate_reference_longitudinal_elements_for_span(
        ctx,
        girders,
        ctx.y_offsets_girders,
        support_i_vector,
        support_j_vector,
    )

    edge_beam_ref_elements = generate_reference_longitudinal_elements_for_span(
        ctx,
        edge_beams,
        ctx.y_offsets_edge_beams,
        support_i_vector,
        support_j_vector,
    )

    transverse_bracings = generate_reference_elements_for_transverse_bracings_for_span(
        ctx,
        bracing_groups=collect_bracings_for_span(span),
        girders_ref_elements=girder_ref_elements,
    )

    diaphragms = generate_reference_elements_for_diaphragms_for_span(
        ctx,
        diaphragm_groups=collect_diaphragms_for_span(span),
        girders_ref_elements=girder_ref_elements,
        span_index=span_props.span_index,
    )

    return SpanReferenceData(
        span_length=span_props.span_length,
        support_i_vector=support_i_vector,
        support_j_vector=support_j_vector,
        girder_ref_elements=girder_ref_elements,
        edge_beam_ref_elements=edge_beam_ref_elements,
        transverse_bracings_ref_elements=transverse_bracings,
        diaphragms_ref_elements=diaphragms,
    )


def resolve_support_vectors_for_span(
    ctx: BuildContext,
    span_props: GroupPropertiesSpan,
    span_start_point: Point,
    span_length: Quantity,
) -> Tuple[AppliedVector, AppliedVector]:
    span_index = span_props.span_index
    n_i = span_start_point
    n_j = Point(n_i.x + span_length, ctx.zero_length)

    sup_i_angle = require_support_angle(ctx.support_angles, span_index)
    sup_j_angle = require_support_angle(ctx.support_angles, span_index + 1)

    if ctx.grillage_type == ElementOrientation.SKEWED and sup_i_angle != sup_j_angle:
        ctx.logger.warning(
            "Skew angle of supports %d and %d differs for skewed grillage. "
            "Using the start support angle %s for both.",
            span_index,
            span_index + 1,
            sup_i_angle,
        )
        sup_j_angle = sup_i_angle

    return AppliedVector(n_i, Vector.from_angle(sup_i_angle)), AppliedVector(n_j, Vector.from_angle(sup_j_angle))


def generate_reference_longitudinal_elements_for_span(
    ctx: BuildContext,
    element_groups: Iterable[GeometryGroup],
    y_offsets_elements: Dict[int, Quantity],
    support_i_vector: AppliedVector,
    support_j_vector: AppliedVector,
) -> Dict[int, Element1D]:
    """Create one reference element per girder/edge-beam group in the span.

    For each group, the method builds a longitudinal element line from the
    configured Y-offset, intersects it with start/end support lines, creates
    or reuses nodes at those intersections, and appends an ``Element1D`` to
    the group's ``reference_elements``.

    Returns
    -------
    Dict[int, Element1D]
        Mapping ``element_index -> reference element``.

    Raises
    ------
    ValueError
        If an element offset is missing or a support intersection cannot be
        resolved.
    """
    ref_elements: Dict[int, Element1D] = {}

    for element_group in element_groups:
        if not isinstance(element_group, GeometryGroup):
            raise TypeError(f"Element group {element_group.name} should be a GeometryGroup object")

        if isinstance(element_group.properties, GroupPropertiesGirder):
            element_index = element_group.properties.girder_index
        elif isinstance(element_group.properties, GroupPropertiesEdgeBeam):
            element_index = element_group.properties.edge_beam_index
        else:
            raise TypeError(f"Girder group {element_group.name} has invalid properties type."
                            f"Should be a GroupPropertiesEdgeBeam or GroupPropertiesGirder object.")

        if element_index not in y_offsets_elements:
            raise ValueError(f"Missing y-offset for element index {element_index}.")

        element_vector = AppliedVector(
            start_point=Point(
                ctx.zero_length,
                y_offsets_elements[element_index],
                ctx.zero_length,
            ),
            vector=ctx.bridge_direction_vector,
        )

        start_point = GeometryTools.intersect_lines(
            element_vector,
            support_i_vector,
            ctx.tolerance,
        )
        if start_point is None:
            raise ValueError(f"Could not resolve start intersection for element index {element_index}.")
        node_i = ctx.amm.get_or_create_node(start_point.x, start_point.y, start_point.z)

        end_point = GeometryTools.intersect_lines(
            element_vector,
            support_j_vector,
            ctx.tolerance,
        )
        if end_point is None:
            raise ValueError(f"Could not resolve end intersection for element index {element_index}.")
        node_j = ctx.amm.get_or_create_node(end_point.x, end_point.y, end_point.z)

        element = ctx.amm.create_and_add_reference_element(element_group, node_i, node_j)
        ref_elements[element_index] = element
    return ref_elements


def generate_reference_elements_for_transverse_bracings_for_span(
    ctx: BuildContext,
    bracing_groups: Iterable[GeometryGroup],
    girders_ref_elements: Dict[int, Element1D],
) -> Dict[Tuple[int, int], List[Element1D]]:
    bracings: Dict[Tuple[int, int], List[Element1D]] = defaultdict(list)

    for bracing_group in bracing_groups:
        props = require_transverse_bracing_properties(bracing_group)
        girder_i_index = props.left_girder_index
        girder_j_index = props.right_girder_index

        girder_i = girders_ref_elements[girder_i_index]
        girder_j = girders_ref_elements[girder_j_index]

        girder_i_x_start = girder_i.node_start.X
        girder_j_x_start = girder_j.node_start.X

        spacing_values = tools.resolve_spacing(
            spacing_type=props.spacing_type,
            spacing_values=props.spacing_values,
            number_of_elements=props.no_of_bracings
        )

        for i in range(props.no_of_bracings):
            g_i_x = cast(Quantity, girder_i_x_start +
                         props.x_position_at_start_girder + sum(spacing_values[:i]))
            match props.bracing_orientation:
                case ElementOrientation.ORTHOGONAL:
                    g_j_x = g_i_x
                case ElementOrientation.SKEWED:
                    g_j_x = cast(Quantity, girder_j_x_start +
                                 props.x_position_at_start_girder + sum(spacing_values[:i]))
            n_i = ctx.amm.get_or_create_node(x=g_i_x, y=girder_i.node_start.Y, z=girder_i.node_start.Z)
            n_j = ctx.amm.get_or_create_node(x=g_j_x, y=girder_j.node_start.Y, z=girder_j.node_start.Z)
            ref_elem = ctx.amm.create_and_add_reference_element(bracing_group, n_i, n_j)
            bracings[(girder_i_index, girder_j_index)].append(ref_elem)

    return bracings


def generate_reference_elements_for_diaphragms_for_span(
    ctx: BuildContext,
    diaphragm_groups: Iterable[GeometryGroup],
    girders_ref_elements: Dict[int, Element1D],
    span_index: int,
) -> Dict[int, List[Element1D]]:
    diaphragms: Dict[int, List[Element1D]] = defaultdict(list)

    girder_indices = sorted(girders_ref_elements.keys())
    if len(girder_indices) < 2:
        return diaphragms

    for diaphragm_group in diaphragm_groups:
        props = require_diaphragm_properties(diaphragm_group)

        if props.support_index == span_index:
            use_span_start = True
        elif props.support_index == span_index + 1:
            use_span_start = False
        else:
            raise ValueError(
                f"Diaphragm group {diaphragm_group.name} has support index {props.support_index}, "
                f"but span {span_index} expects {span_index} or {span_index + 1}."
            )

        for i in range(len(girder_indices) - 1):
            left_girder = girders_ref_elements[girder_indices[i]]
            right_girder = girders_ref_elements[girder_indices[i + 1]]

            if use_span_start:
                node_i = left_girder.node_start
                node_j = right_girder.node_start
            else:
                node_i = left_girder.node_end
                node_j = right_girder.node_end

            ref_elem = ctx.amm.create_and_add_reference_element(diaphragm_group, node_i, node_j)
            diaphragms[props.support_index].append(ref_elem)

    return diaphragms
