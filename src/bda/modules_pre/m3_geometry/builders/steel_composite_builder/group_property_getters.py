"""Typed, isinstance-checked access to geometry-group properties and sections.

Every ``require_*`` function validates the group/component/properties types and
returns the strongly-typed object, raising ``TypeError``/``ValueError`` when the
model is malformed.
"""
from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Dict, List, Type, TypeVar

from pint.registry import Quantity

import bda.domain.units.registry as units
from bda.domain.enums import StructuralComponentType
from bda.domain.models.submodels.geometry_group import GeometryGroup
from bda.domain.models.submodels.geometry_group_props.bridge_properties import GroupPropertiesBridge
from bda.domain.models.submodels.geometry_group_props.linkage_properties import GroupPropertiesLinkageSupToSub
from bda.domain.models.submodels.geometry_group_props.shared import GroupPropertiesSegment
from bda.domain.models.submodels.geometry_group_props.substructure_properties import GroupPropertiesSupport
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import (
    GroupPropertiesBrace,
    GroupPropertiesChord,
    GroupPropertiesDiaphragm,
    GroupPropertiesEdgeBeam,
    GroupPropertiesGirder,
    GroupPropertiesPlanBracing,
    GroupPropertiesSpan,
    GroupPropertiesSuperstructure,
    GroupPropertiesTransverseBracing,
)
from bda.domain.models.submodels.material import Material
from bda.domain.models.submodels.section_base import Section
from bda.domain.models.submodels.sections import (
    DimensionsSolidRectangle,
    SectionStandardSolidRectangle,
)
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.constants import (
    DUMMY_ELEMENT_SIZE_METERS,
)

if TYPE_CHECKING:
    from bda.modules_pre.m3_geometry.builders.steel_composite_builder.context import BuildContext

TProps = TypeVar("TProps")


def _require_properties(
    group: GeometryGroup,
    component_type: StructuralComponentType,
    props_type: Type[TProps],
) -> TProps:
    if not isinstance(group, GeometryGroup):
        raise TypeError(f"{component_type.name.capitalize()} group should be a GeometryGroup object.")
    if group.component_type != component_type:
        raise TypeError(f"Group {group.name} should have {component_type.name} component type.")
    if not isinstance(group.properties, props_type):
        raise TypeError(
            f"Group {group.name} should have {props_type.__name__} properties."
        )
    return group.properties


def require_span_properties(span: GeometryGroup) -> GroupPropertiesSpan:
    return _require_properties(span, StructuralComponentType.SPAN, GroupPropertiesSpan)


def require_girder_properties(girder: GeometryGroup) -> GroupPropertiesGirder:
    return _require_properties(girder, StructuralComponentType.GIRDER, GroupPropertiesGirder)


def require_edge_beam_properties(edge_beam: GeometryGroup) -> GroupPropertiesEdgeBeam:
    return _require_properties(edge_beam, StructuralComponentType.EDGE_BEAM, GroupPropertiesEdgeBeam)


def require_segment_properties(segment: GeometryGroup) -> GroupPropertiesSegment:
    return _require_properties(segment, StructuralComponentType.SEGMENT, GroupPropertiesSegment)


def require_transverse_bracing_properties(bracing_group: GeometryGroup) -> GroupPropertiesTransverseBracing:
    return _require_properties(
        bracing_group,
        StructuralComponentType.TRANSVERSE_BRACING,
        GroupPropertiesTransverseBracing,
    )


def require_brace_properties(brace_group: GeometryGroup) -> GroupPropertiesBrace:
    return _require_properties(brace_group, StructuralComponentType.BRACE, GroupPropertiesBrace)


def require_chord_properties(chord_group: GeometryGroup) -> GroupPropertiesChord:
    return _require_properties(chord_group, StructuralComponentType.CHORD, GroupPropertiesChord)


def require_diaphragm_properties(diaphragm_group: GeometryGroup) -> GroupPropertiesDiaphragm:
    return _require_properties(diaphragm_group, StructuralComponentType.DIAPHRAGM, GroupPropertiesDiaphragm)


def require_plan_bracing_properties(plan_bracing_group: GeometryGroup) -> GroupPropertiesPlanBracing:
    return _require_properties(
        plan_bracing_group,
        StructuralComponentType.PLAN_BRACING,
        GroupPropertiesPlanBracing,
    )


def require_bridge_properties(root_group: GeometryGroup) -> GroupPropertiesBridge:
    bridge_groups = root_group.get_groups_by_component_type(StructuralComponentType.BRIDGE)
    if not bridge_groups:
        raise ValueError("Bridge group has not been found.")

    bridge_props = bridge_groups[0].properties
    if not isinstance(bridge_props, GroupPropertiesBridge):
        raise ValueError("Bridge group properties are invalid. GroupPropertiesBridge is required.")
    return bridge_props


def require_support_properties(group: GeometryGroup) -> GroupPropertiesSupport:
    if not isinstance(group, GeometryGroup):
        raise TypeError("Support group should be a GeometryGroup object.")
    if group.component_type != StructuralComponentType.SUPPORT:
        raise TypeError(f"Group {group.name} should have SUPPORT component type.")
    if not isinstance(group.properties, GroupPropertiesSupport):
        raise TypeError(f"Span group {group.name} should have GroupPropertiesSupport properties.")
    return group.properties


def require_superstructure_properties(root_group: GeometryGroup) -> GroupPropertiesSuperstructure:
    superstructure = next(
        root_group.iter_groups(
            lambda g: g.component_type == StructuralComponentType.SUPERSTRUCTURE
            and isinstance(g.properties, GroupPropertiesSuperstructure)
        ),
        None,
    )

    if superstructure is None:
        raise ValueError("Superstructure group has not been found.")

    if not isinstance(superstructure.properties, GroupPropertiesSuperstructure):
        raise TypeError(
            f"Superstructure group '{superstructure.name}' should have GroupPropertiesSuperstructure properties."
        )

    return superstructure.properties


def require_linkage_sup_to_sup_properties(group: GeometryGroup) -> GroupPropertiesLinkageSupToSub:
    linkage = next(
        group.iter_groups(
            lambda g: g.component_type == StructuralComponentType.SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS
                      and isinstance(g.properties, GroupPropertiesLinkageSupToSub)
        ),
        None,
    )

    if linkage is None:
        raise ValueError("Linkage Superstructure to Substructure group has not been found.")

    if not isinstance(linkage.properties, GroupPropertiesLinkageSupToSub):
        raise TypeError(
            f"Linkage Superstructure to Substructure group '{linkage.name}' "
            f"should have GroupPropertiesLinkageSupToSub properties."
        )

    return linkage.properties


def require_support_angle(support_angles: Dict[int, Quantity], support_index: int) -> Quantity:
    angle = support_angles.get(support_index)
    if angle is None:
        raise ValueError(f"Support with index {support_index} has not been found.")
    return angle


def require_girder_group_for_index(
    girder_groups: List[GeometryGroup],
    girder_index: int,
    span_index: int,
) -> GeometryGroup:
    girder_group = next(
        (
            g
            for g in girder_groups
            if (
                isinstance(props := g.properties, GroupPropertiesGirder)
                and props.girder_index == girder_index
            )
        ),
        None,
    )

    if girder_group is None:
        raise ValueError(
            f"Group for girder index {girder_index} not found "
            f"under span index {span_index}."
        )

    return girder_group


def require_longitudinal_member_for_span(span: GeometryGroup) -> GeometryGroup:
    longitudinal_members = span.get_groups_by_component_type(StructuralComponentType.LONGITUDINAL_MEMBERS)
    if not longitudinal_members:
        raise ValueError(f"Longitudinal members under span {span.name} not found.")
    return longitudinal_members[0]


def require_deck_group_for_span(ctx: BuildContext, span: GeometryGroup) -> GeometryGroup:
    if not isinstance(span, GeometryGroup):
        raise TypeError("Span group should be a GeometryGroup object.")
    if span.component_type != StructuralComponentType.SPAN:
        raise TypeError(f"Group {span.name} should have SPAN component type.")
    deck_groups = span.get_groups_by_component_type(StructuralComponentType.DECK_SLAB)
    if not deck_groups:
        raise ValueError(f"Deck group has not been found for span {span.name}.")
    if len(deck_groups) > 1:
        ctx.logger.warning(f"Deck group {span.name} has more than one group. Using first one.")
    return deck_groups[0]


def require_deck_base_section(deck_group: GeometryGroup) -> SectionStandardSolidRectangle:
    if not isinstance(deck_group, GeometryGroup):
        raise TypeError("Deck group should be a GeometryGroup object.")
    if deck_group.component_type != StructuralComponentType.DECK_SLAB:
        raise TypeError(f"Group {deck_group.name} should have DECK_SLAB component type.")
    if deck_group.section is None:
        raise ValueError(f"Deck group {deck_group.name} has no section assigned.")
    if not isinstance(deck_section := deck_group.section, SectionStandardSolidRectangle):
        raise TypeError(f"Deck group {deck_group.name} should have SectionStandardSolidRectangle section.")
    return deck_section


def require_dummy_section(ctx: BuildContext) -> Section:
    """Lazily create and cache the weightless placeholder section for default edge beams."""
    if ctx.dummy_section is None:
        ctx.dummy_section = SectionStandardSolidRectangle(
            name="DummySection",
            dimensions=DimensionsSolidRectangle(
                width_b=DUMMY_ELEMENT_SIZE_METERS * units.m,
                height_h=DUMMY_ELEMENT_SIZE_METERS * units.m,
            ))
    return ctx.dummy_section


def require_weightless_material(ctx: BuildContext, source_material: Material | None) -> Material | None:
    """Return a cached weightless copy of the material (one per source material)."""
    if source_material is None:
        return None

    material_weightless = ctx.weightless_materials.get(source_material.guid)
    if material_weightless is None:
        material_weightless = deepcopy(source_material)
        material_weightless.name = f"{source_material.name}_weightless"
        material_weightless.general_properties.unit_weight = 0 * units.kN / units.m**3
        ctx.weightless_materials[source_material.guid] = material_weightless
    return material_weightless
