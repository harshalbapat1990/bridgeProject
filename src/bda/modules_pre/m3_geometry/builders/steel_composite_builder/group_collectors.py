"""Collectors of geometry groups by structural component type.

Every ``collect_*`` function filters nested groups with isinstance-checked
properties and returns them in a deterministic order.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Tuple

from pint.registry import Quantity

from bda.domain import units
from bda.domain.enums import StructuralComponentType
from bda.domain.models.submodels.geometry_group import GeometryGroup
from bda.domain.models.submodels.geometry_group_props.bridge_properties import GroupPropertiesBridge
from bda.domain.models.submodels.geometry_group_props.linkage_properties import GroupPropertiesLinkageSupToSub
from bda.domain.models.submodels.geometry_group_props.substructure_properties import (
    GroupPropertiesSupport,
)
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import (
    GroupPropertiesBrace,
    GroupPropertiesChord,
    GroupPropertiesDiaphragm,
    GroupPropertiesEdgeBeam,
    GroupPropertiesGirder,
    GroupPropertiesPlanBracing,
    GroupPropertiesSpan,
    GroupPropertiesTransverseBracing,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.group_property_getters import (
    require_diaphragm_properties,
    require_dummy_section,
    require_edge_beam_properties,
    require_girder_properties,
    require_longitudinal_member_for_span,
    require_span_properties,
    require_weightless_material, require_support_properties,
)
from bda.modules_pre.m3_geometry.helpers.tools.models import Vector, AppliedVector, Point

if TYPE_CHECKING:
    from bda.modules_pre.m3_geometry.builders.steel_composite_builder.context import BuildContext, SupportBuildState


def collect_spans(root_group: GeometryGroup) -> List[GeometryGroup]:
    spans = [
        s
        for s in root_group.iter_groups(
            lambda g: g.component_type == StructuralComponentType.SPAN
            and isinstance(g.properties, GroupPropertiesSpan)
        )
    ]
    spans.sort(key=lambda s: require_span_properties(s).span_index)
    return spans


def collect_support_angles(root_group: GeometryGroup) -> Dict[int, Quantity]:
    supports = [
        s
        for s in root_group.iter_groups(
            lambda g: g.component_type == StructuralComponentType.SUPPORT
            and isinstance(g.properties, GroupPropertiesSupport)
        )
    ]
    supports.sort(key=lambda s: s.properties.support_index)

    by_index: Dict[int, Quantity] = {}
    for support in supports:
        support_properties = support.properties
        if not isinstance(support_properties, GroupPropertiesSupport):
            continue
        support_index = support_properties.support_index
        if support_index in by_index:
            raise ValueError(f"Duplicated support index {support_index} found.")
        by_index[support_index] = support_properties.skew_angle

    return by_index


def collect_girders_for_span(span: GeometryGroup) -> List[GeometryGroup]:
    girders = [
        g
        for g in span.iter_groups()
        if g.component_type == StructuralComponentType.GIRDER
        and isinstance(g.properties, GroupPropertiesGirder)
    ]
    girders.sort(key=lambda g: require_girder_properties(g).girder_index)
    return girders


def collect_bracings_for_span(span: GeometryGroup) -> List[GeometryGroup]:
    return [
        b
        for b in span.get_groups_by_component_type(StructuralComponentType.TRANSVERSE_BRACING)
        if isinstance(b.properties, GroupPropertiesTransverseBracing)
    ]


def collect_transverse_bracings_for_bridge(root_group: GeometryGroup) -> List[GeometryGroup]:
    return [
        tb
        for tb in root_group.get_groups_by_component_type(StructuralComponentType.TRANSVERSE_BRACING)
        if isinstance(tb.properties, GroupPropertiesTransverseBracing)
    ]


def collect_plan_bracings_for_span(span: GeometryGroup) -> List[GeometryGroup]:
    return [
        pb
        for pb in span.get_groups_by_component_type(StructuralComponentType.PLAN_BRACING)
        if isinstance(pb.properties, GroupPropertiesPlanBracing)
    ]


def collect_diaphragms_for_span(span: GeometryGroup) -> List[GeometryGroup]:
    diaphragms = [
        d
        for d in span.get_groups_by_component_type(StructuralComponentType.DIAPHRAGM)
        if isinstance(d.properties, GroupPropertiesDiaphragm)
    ]
    diaphragms.sort(key=lambda d: require_diaphragm_properties(d).support_index)
    return diaphragms


def collect_brace_groups(bracing_group: GeometryGroup) -> List[GeometryGroup]:
    return [
        g
        for g in bracing_group.get_groups_by_component_type(StructuralComponentType.BRACE)
        if isinstance(g.properties, GroupPropertiesBrace)
    ]


def collect_chord_groups(bracing_group: GeometryGroup) -> List[GeometryGroup]:
    return [
        g
        for g in bracing_group.get_groups_by_component_type(StructuralComponentType.CHORD)
        if isinstance(g.properties, GroupPropertiesChord)
    ]


def collect_or_create_edge_beams_for_span(ctx: BuildContext, span: GeometryGroup) -> List[GeometryGroup]:
    """Return span edge-beam groups, creating two weightless defaults when absent."""
    edge_beams = span.get_groups_by_component_type(StructuralComponentType.EDGE_BEAM)
    deck = next(iter(span.get_groups_by_component_type(StructuralComponentType.DECK_SLAB)))

    longitudinal_member = require_longitudinal_member_for_span(span)

    if len(edge_beams) == 0:
        ctx.logger.debug(
            "[SteelCompositeBuilder] no edge beams found for span | span=%s | creating default edge beams",
            span.name,
        )
        for i in range(2):
            edge_beam = GeometryGroup(
                component_type=StructuralComponentType.EDGE_BEAM,
                name=f"Edge Beam {i + 1}",
                properties=GroupPropertiesEdgeBeam(
                    edge_beam_index=i
                )
            )
            edge_beam.section = require_dummy_section(ctx)
            edge_beam.material = require_weightless_material(ctx, deck.get_material())
            edge_beam.section.set_material_main(edge_beam.material)
            longitudinal_member.add_nested_group(edge_beam)
            edge_beams.append(edge_beam)
        return edge_beams

    edge_beams.sort(key=lambda g: require_edge_beam_properties(g).edge_beam_index)
    return edge_beams


def collect_sup_to_sup_groups_for_span_index(
    span_index: int,
    root_group: GeometryGroup,
) -> Tuple[GeometryGroup, GeometryGroup]:

    linkage_group = root_group.get_first_group_by_component_type(StructuralComponentType.LINKAGE)
    if linkage_group is None:
        raise ValueError(
            f"Failed to find linkage group under root bridge group {root_group.name}."
        )

    sup_to_sup_groups = (linkage_group.
                         get_groups_by_component_type(
        StructuralComponentType.SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS
    ))

    matching_groups = [
        g
        for g in sup_to_sup_groups
        if (
                isinstance(props := g.properties, GroupPropertiesLinkageSupToSub)
                and (
                        props.support_index == span_index
                        or props.support_index == span_index + 1
                )
        )
    ]

    if len(matching_groups) != 2:
        raise ValueError(
            f"Expected 2 superstructure-to-substructure groups "
            f"for span index {span_index}, found {len(matching_groups)}."
        )

    return matching_groups[0], matching_groups[1]

def collect_supports_data(ctx: BuildContext) -> dict[int, SupportBuildState]:

    support_states: Dict[int, SupportBuildState] = {}

    root_group = ctx.geometry

    if root_group is None:
        raise ValueError("Root group is not defined in the context.")

    supports = [
        s
        for s in root_group.iter_groups(
            lambda g: g.component_type == StructuralComponentType.SUPPORT
                      and isinstance(g.properties, GroupPropertiesSupport)
        )
    ]
    supports.sort(key=lambda s: s.properties.support_index)

    bridge_group = root_group
    if (bridge_group.component_type != StructuralComponentType.BRIDGE
            or not isinstance(bridge_group.properties, GroupPropertiesBridge)):
        raise ValueError(f"Root group {bridge_group.name} is not a bridge group.")

    bridge_absolute_level = bridge_group.properties.top_deck_level

    for support in supports:
        sup_props = require_support_properties(support)
        support_index = support.properties.support_index
        bearing_level = support.properties.bearing_underside_level

        supp_offset: Quantity

        if support_index == 0:
            diff = 0 * units.registry.m
            supp_offset = 0 * units.registry.m
        else:
            span = next(s.span for s in ctx.span_states if s.span_props.span_index == support_index - 1)
            props = require_span_properties(span)
            diff = bridge_absolute_level - props.top_deck_level_at_end
            span_state = next((ss for ss in ctx.span_states if ss.span_props.span_index == support_index - 1))
            span_length = span_state.span_props.span_length
            supp_offset = span_state.span_offset + span_length

        bearing_underside_level = bearing_level - bridge_absolute_level + diff
        sup_vector = Vector.from_angle(sup_props.skew_angle)
        sup_applied_vector = AppliedVector(
            start_point=Point(supp_offset, 0 * units.registry.m, bearing_underside_level),
            vector=sup_vector
        )

        from bda.modules_pre.m3_geometry.builders.steel_composite_builder.context import SupportBuildState

        support_states[support_index] = SupportBuildState(
            support=support,
            support_properties=sup_props,
            support_vector=sup_applied_vector,
            bearing_underside_relative_level=bearing_underside_level,
            angle=sup_props.skew_angle,
        )
    return support_states