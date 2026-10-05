from abc import ABC, abstractmethod
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from typing import cast, Optional, Dict, Sequence

import math
from uuid import UUID

import bda.domain.units.registry as units
from bda.domain.enums import StructuralComponentType, OffsetReference
from bda.domain.models.submodels import Element1D, GeometryGroup
from bda.domain.models.submodels.element import ElementLink, LinkType
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import SupportType, \
    BearingConfigurationType, SpacingType
from bda.domain.models.submodels.geometry_group_props.linkage_properties import GroupPropertiesLinkageSupToSub
from bda.domain.models.submodels.material import Material
from bda.domain.models.submodels.node import Node
from bda.domain.models.submodels.geometry_group_props.shared import GroupPropertiesSegment, TaperedDetails, \
    SymmetricPlaneType
from bda.domain.models.submodels.geometry_group_props.substructure_properties import GroupPropertiesSupport, \
    GroupPropertiesPile, GroupPropertiesPier, GroupPropertiesPileCap, GroupPropertiesCrossbeam
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import (
    GroupPropertiesGirder,
    GroupPropertiesSpan,
)
from pint.registry import Quantity

from bda.domain.models.submodels.section_base import Offset
from bda.domain.units import ureg
from bda.infrastructure.utils import AppLogger
from bda.modules_pre.m3_geometry.builders.psc_box_builder.build_context import (
    GeometryPSCBoxBuildContext,
    SpanBuildState,
    SpanReferenceData, SupportBuildState, PierBuildState, PileBuildState, PilecapBuildState, CrossheadBuildState,
    TributaryRegion, SupToSubBuildState, CrossheadSegmentResult, GirderBuildState,
)
from bda.modules_pre.m3_geometry.builders.psc_box_builder.group_property_getters import GroupPropertyGetter
from bda.modules_pre.m3_geometry.builders.psc_box_builder.split_span_into_segments_ import split_span_into_segments
from bda.modules_pre.m3_geometry.helpers.tools import general_tools
from bda.domain.models.submodels.sections import SectionStandardSolidRectangle, \
    DimensionsSolidRectangle, SectionTapered, SectionStandardSolidRound
from bda.modules_pre.m3_geometry.helpers.tools.general_tools import is_close
from bda.modules_pre.m3_geometry.helpers.tools.geometry_tools import GeometryTools
from bda.modules_pre.m3_geometry.helpers.tools.models import Vector, AppliedVector, Point

#
#   Base classes
#

class BuildStep(ABC):
    def __init__(self) -> None:
        self._logger = AppLogger()

    def execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        self._logger.debug(">>> Executing: '%s'.", self.__class__.__name__)
        self._execute(ctx)

    @abstractmethod
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None: ...


#
#   Collecting groups
#

class CollectGeometryRoot(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        geometry = ctx.amm.geometry_group
        if geometry is None:
            raise ValueError("AnalyticalMultiModel has no geometry_group.")
        ctx.geometry = geometry


class CollectBridgeProperties(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        if ctx.geometry is None:
            raise ValueError("Build context has no geometry.")
        if ctx.builder is None:
            raise ValueError("Build context has no builder instance.")

        bridge_props = ctx.builder._get_bridge_properties(ctx.geometry)
        ctx.bridge_properties = bridge_props

        mesh_divisor = bridge_props.analysis_settings.girder_mesh_divisor
        if not isinstance(mesh_divisor, int) or mesh_divisor < 1:
            raise ValueError(
                "Invalid bridge analysis settings: 'girder_mesh_divisor' must be an integer >= 1. "
                f"Got: {mesh_divisor!r}."
            )

        ctx.girder_mesh_divisor = mesh_divisor


class CollectSpans(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        if ctx.geometry is None:
            raise ValueError("Build context has no geometry.")

        spans = sorted(
            (
                group for group in ctx.geometry.iter_groups()
                if group.component_type == StructuralComponentType.SPAN
                and isinstance(group.properties, GroupPropertiesSpan)
            ),
            key=lambda span: span.properties.span_index,
        )

        ctx.spans = {s.properties.span_index: s for s in spans}

        if not ctx.spans:
            raise ValueError("No SPAN groups found.")


class InitializeSpanStates(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        ctx.span_states.clear()
        span_offset = 0.0 * units.m

        for span in ctx.spans.values():
            span_props = GroupPropertyGetter.get_span_properties(span)
            ctx.span_states.append(
                SpanBuildState(
                    span=span,
                    span_props=span_props,
                    span_offset=span_offset,
                    span_reference_data=SpanReferenceData(
                        span_length=span_props.span_length,
                        x_offset=span_offset,
                    ),
                )
            )
            span_offset = cast(Quantity, span_offset + span_props.span_length)


class ResolveSpanTaperedSegments(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        if ctx.builder is None:
            raise ValueError("Build context has no builder instance.")
        if ctx.geometry is None:
            raise ValueError("Build context has no geometry.")

        sections_by_guid = {section.guid: section for section in ctx.amm.get_all_sections()}

        # Seed the running section from the bridge root group.
        current_section_id = ctx.geometry.section_uid

        for state in ctx.span_states:
            segments, current_section_id = split_span_into_segments(
                span_length=state.span_props.span_length,
                tapered_details=list(state.span_props.tapered_details or []),
                tolerance=ctx.builder._tolerance,
                span_offset=state.span_offset,
                span_index=state.span_props.span_index,
                span_name=state.span.name,
                initial_section_id=current_section_id,
                sections_by_guid=sections_by_guid,
            )
            state.tapered_segments = segments


class ResolveSpanBoundarySegmentSections(BuildStep):
    """Resolve start_section and end_section from first and last segments of each span."""

    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        sections_by_guid = {section.guid: section for section in ctx.amm.get_all_sections()}

        for state in ctx.span_states:
            if not state.tapered_segments:
                continue

            first_segment = state.tapered_segments[0]
            last_segment = state.tapered_segments[-1]

            state.start_section = _get_section_or_none(sections_by_guid, first_segment.start_id) #type: ignore
            state.end_section = _get_section_or_none(sections_by_guid, last_segment.end_id) #type: ignore

            girder = next(
                g for g in state.span.iter_groups()
                if g.component_type == StructuralComponentType.GIRDER
            )
            if state.start_section is None:
                state.start_section = girder.get_section() #type: ignore
            if state.end_section is None:
                state.end_section = girder.get_section() #type: ignore


class CollectSupportsData(BuildStep):
    """Collect support bearing_underside_level values keyed by support_index."""

    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        if ctx.geometry is None:
            raise ValueError("Build context has no geometry.")

        supports = [
            s
            for s in ctx.geometry.iter_groups(
                lambda g: g.component_type == StructuralComponentType.SUPPORT
                and isinstance(g.properties, GroupPropertiesSupport)
            )
        ]
        supports.sort(key=lambda s: s.properties.support_index)

        bridge_absolute_level = ctx.bridge_properties.top_deck_level

        for support in supports:
            sup_props = GroupPropertyGetter.get_support_properties(support)
            support_index = support.properties.support_index
            bearing_level = support.properties.bearing_underside_level

            pile_caps = support.get_groups_by_component_type(StructuralComponentType.PILE_CAP)
            is_abutment = self._is_abutment(support)

            if not support.has_children() or not pile_caps:
                is_modelled = False
                pilecap_level = None
            else:
                is_modelled = True
                pilecap_group = next(iter(pile_caps))
                pilecap_level = (
                    GroupPropertyGetter
                    .get_pilecap_properties(pilecap_group)
                    .top_of_pile_cap_level
                )

            supp_offset: Quantity

            if support_index == 0:
                diff = 0 * units.m
                supp_offset = 0 * units.m
            else:
                span = ctx.spans[support_index - 1]
                props = GroupPropertyGetter.get_span_properties(span)
                diff = bridge_absolute_level - props.top_deck_level_at_end
                span_state = next((ss for ss in ctx.span_states if ss.span_props.span_index == support_index - 1))
                span_length = span_state.span_props.span_length
                supp_offset = span_state.span_offset + span_length

            bearing_underside_level = bearing_level - bridge_absolute_level + diff
            sup_vector = Vector.from_angle(sup_props.skew_angle)
            sup_applied_vector = AppliedVector(
                start_point = Point(supp_offset, 0 * units.m, bearing_underside_level),
                vector = sup_vector
            )

            ctx.support_states[support_index] = SupportBuildState(
                support=support,
                support_properties= sup_props,
                support_vector= sup_applied_vector,
                bearing_underside_relative_level= bearing_underside_level,
                pilecap_top_relative_level= None if not is_modelled else pilecap_level - bridge_absolute_level + diff,
                angle= sup_props.skew_angle,
                is_modelled = is_modelled,
                is_abutment = is_abutment
            )

    def _is_abutment(self, support: GeometryGroup) -> bool:
        above_ground_group = support.get_first_group_by_component_type(StructuralComponentType.ABOVE_GROUND)

        if above_ground_group is None:
            self._logger.error(f"No ABOVE GROUND group found under support '{support.name}' "
                         f"Skipping the support.")
            return True

        if ag_props := GroupPropertyGetter.get_above_ground_properties(above_ground_group):
            if ag_props.details.support_type != SupportType.COLUMN_TYPE:
                self._logger.info(f"Support {support.name} (index={support.properties.support_index} "
                               f"is not column-type.")
                return True

        return False


class CollectSupToSub(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        ctx.sup_to_sub_states.clear()
        sup_to_sub = sorted(
            (
                g for g in ctx.geometry.iter_groups()
                if g.component_type == StructuralComponentType.SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS
                and isinstance(g.properties, GroupPropertiesLinkageSupToSub)
            ), key= lambda g: g.properties.support_index
        )

        for b in sup_to_sub:
            idx = b.properties.support_index
            props = b.properties
            assert isinstance(props, GroupPropertiesLinkageSupToSub), f"Expected {GroupPropertiesLinkageSupToSub} but got {type(props)}"

            ctx.sup_to_sub_states[idx] = SupToSubBuildState(
                support_index= idx,
                sup_to_sub_group= b,
                sup_to_sub_properties= props
            )


class CollectCrossheads(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        if ctx.geometry is None:
            raise ValueError("Build context has no geometry.")

        ctx.crosshead_states.clear()
        crossheads_by_support_index: defaultdict[int, CrossheadBuildState]

        for idx, support in ctx.support_states.items():
            crosshead = support.support.get_first_group_by_component_type(StructuralComponentType.CROSSBEAM)

            if not crosshead:
                self._logger.warning(f"No CROSSBEAM group found under support '{support.support.name}' (index={idx}).")
                continue

            crosshead_properties = GroupPropertyGetter.get_crosshead_properties(crosshead)
            support_vector = support.support_vector

            ctx.crosshead_states[idx] = CrossheadBuildState(
                support_index= idx,
                crosshead= crosshead,
                crosshead_properties= crosshead_properties,
                support_vector= support_vector,
            )


class CollectPilecaps(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        if ctx.geometry is None:
            raise ValueError("Build context has no geometry.")

        ctx.pilecap_states.clear()
        # pilecaps_by_support_index: defaultdict[int, list[PilecapBuildState]] = defaultdict(list)
        pilecaps_by_support_index: defaultdict[int, PilecapBuildState] = defaultdict()

        for sup_id, support_state in ctx.support_states.items():

            above_ground_group = (
                support_state
                .support
                .get_first_group_by_component_type(
                    StructuralComponentType.ABOVE_GROUND
                )
            )

            if above_ground_group is None:
                self._logger.warning(f"No ABOVE GROUND group found under support '{support_state.support.name}' ")
                continue

            if above_ground_group.properties.details.support_type != SupportType.COLUMN_TYPE:
                self._logger.info(f"Support {support_state.support.name} (index={support_state.support.name}) is not column-type."
                            f"Skipping the support.")
                continue

            # -----------------------------------------
            below_ground_group = (
                support_state
                .support
                .get_first_group_by_component_type(
                StructuralComponentType.BELOW_GROUND
            ))

            if below_ground_group is None:
                self._logger.warning(f"No BELOW GROUND group found under support '{support_state.support.name}' ")
                continue
            # -----------------------------------------

            vertical_member_group = (
                below_ground_group
                .get_groups_by_component_type(
                    StructuralComponentType.VERTICAL_MEMBERS
            ))

            if vertical_member_group is None:
                self._logger.warning(f"No VERTICAL_MEMBERS group found under support '{support_state.support.name}' ")
                continue
            #--------------------------------------------

            horizontal_members = (
                below_ground_group
                .get_first_group_by_component_type(
                    StructuralComponentType.HORIZONTAL_MEMBERS
            ))

            if horizontal_members is None:
                self._logger.warning(f"No HORIZONTAL_MEMBERS group found under support '{support_state.support.name}' ")
                continue
            #--------------------------------------------

            horizontal_pilecap = (
                horizontal_members
                .get_first_group_by_component_type(
                StructuralComponentType.PILE_CAP
            ))

            if horizontal_pilecap is None:
                self._logger.warning(f"No PILE_CAP group found under HORIZONTAL_MEMBERS of support '{support_state.support.name}' ")
                continue
            #--------------------------------------------

            horizontal_pilecap_section = horizontal_pilecap.get_section()

            if horizontal_pilecap_section is None:
                self._logger.warning(f"No section found for horizontal pilecap under support '{support_state.support.name}' ")
                horizontal_pilecap_height = 0.0 * units.m
            else:
                horizontal_pilecap_height = cast(Quantity, horizontal_pilecap_section.dimensions.total_height)

            assert isinstance(support_state.pilecap_top_relative_level, Quantity)

            pilecap_bottom_relative_level = cast(Quantity, support_state.pilecap_top_relative_level - horizontal_pilecap_height)

            pilecap_build_state = PilecapBuildState(
                    support_index=sup_id,
                    horizontal_pilecap= horizontal_pilecap,
                    pilecap_properties= cast(GroupPropertiesPileCap, horizontal_pilecap.properties),
                    pilecap_bottom_relative_level= pilecap_bottom_relative_level,
                    vertical_members_group=None
            )

            pilecaps_by_support_index[sup_id] = pilecap_build_state
            ctx.pilecap_states = pilecaps_by_support_index


class CollectPiers(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        if ctx.geometry is None:
            raise ValueError("Build context has no geometry.")

        if ctx.sup_to_sub_states is None:
            raise ValueError("Build context: Linkage -> superstructure-to-substructure-connections "
                             "has not been collected yet.")

        ctx.pier_states.clear()
        piers_by_support_index: defaultdict[int, list[PierBuildState]] = defaultdict(list)

        for sup_id, support_state in ctx.support_states.items():

            if not support_state.is_modelled:
                self._logger.info(f"Support {support_state.support.name} (index={support_state.support.properties.support_index}) "
                            f"is not modelled; skipping pier collection.")
                continue

            above_ground_group = next(
                iter(
                    support_state.support.get_groups_by_component_type(
                        StructuralComponentType.ABOVE_GROUND)
                ), None)

            if above_ground_group is None:
                self._logger.error(f"No ABOVE GROUND group found under support '{support_state.support.name}' "
                             f"Skipping the support.")
                continue

            if ag_props:=GroupPropertyGetter.get_above_ground_properties(above_ground_group):
                if ag_props.details.support_type != SupportType.COLUMN_TYPE:
                    self._logger.warning(f"Support {support_state.support.name} (index={support_state.support.name} "
                                   f"is not column-type; skipping pier collection.")
                    continue

            if support_state.pilecap_top_relative_level is None:
                self._logger.warning(f"Support '{support_state.support.name}' (index={sup_id}) has no pilecap top level."
                               f"Skipping the support.")
                continue

            crosshead_group = next(
                iter(
                    support_state.support.get_groups_by_component_type(
                        StructuralComponentType.CROSSBEAM)
                ),
                None
            )

            crosshead_soffit_relative_level = (
                self._get_pier_top_relative_level(
                    support_state=support_state,
                    crosshead_group=crosshead_group,
                )
            )

            piers = support_state.support.get_groups_by_component_type(StructuralComponentType.PIER)

            if crosshead_group is None:

                no_of_piers = len(piers)

                no_of_bearings = (
                    ctx.sup_to_sub_states[sup_id]
                    .sup_to_sub_properties
                    .bearing_configuration_details
                    .no_of_bearings
                )

                if no_of_piers != no_of_bearings:
                    self._logger.warning(
                        f"Support {sup_id}: "
                        f"{no_of_piers} piers and "
                        f"{no_of_bearings} bearings "
                        f"without crosshead."
                    )

            pier_built_states = [
                PierBuildState(
                    support_index=sup_id,
                    pier=pier,
                    pier_properties=cast(GroupPropertiesPier, pier.properties),
                    crosshead_soffit_relative_level=cast(Quantity, crosshead_soffit_relative_level),
                    pilecap_top_relative_level=support_state.pilecap_top_relative_level
                )
                for pier in piers
                if isinstance(pier.properties, GroupPropertiesPier)
            ]

            piers_by_support_index[sup_id].extend(pier_built_states)
        ctx.pier_states = piers_by_support_index

    def _get_pier_top_relative_level(
            self,
            support_state: SupportBuildState,
            crosshead_group: GeometryGroup | None,
    ) -> Quantity:

        if crosshead_group is None:
            self._logger.info(
                f"No CROSSBEAM group found under support '{support_state.support.name}' "
                f"(index={support_state.support.name})."
                f"Using bearing underside relative level as pier top level.")
            return support_state.bearing_underside_relative_level

        crosshead_section = crosshead_group.get_section()

        if crosshead_section is None:
            self._logger.warning(f"No crosshead section found. "
                           f"Crosshead height assumed to be 0.")
            crosshead_height = 0 * units.m
        else:
            crosshead_height = crosshead_section.dimensions.total_height

        crosshead_soffit_relative_level = cast(Quantity,
                                               support_state.bearing_underside_relative_level - crosshead_height
                                               )
        return crosshead_soffit_relative_level


class CollectPiles(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        if ctx.geometry is None:
            raise ValueError("Build context has no geometry.")

        ctx.pile_states.clear()
        piles_by_support_index: defaultdict[int, list[PileBuildState]] = defaultdict(list)

        for sup_id, support_state in ctx.support_states.items():

            if not support_state.is_modelled:
                self._logger.info(f"Support {support_state.support.name} (index={support_state.support.name}) "
                            f"is not modelled; skipping pile collection.")
                continue

            above_ground_group = support_state.support.get_first_group_by_component_type(StructuralComponentType.ABOVE_GROUND)
            # self._logger.debug(f"Above ground group: {above_ground_group.properties.details.support_type}")

            if above_ground_group is None:
                raise ValueError(f"No ABOVE GROUND group found under support '{support_state.support.name}'.")

            if above_ground_group.properties.details.support_type != SupportType.COLUMN_TYPE:
               self._logger.warning(f"Support {support_state.support.name} (index={support_state.support.name}) is not COLUMN-TYPE. "
                           f"Skipping pile collection for this support.")
               continue

            piles = support_state.support.get_groups_by_component_type(StructuralComponentType.PILE)

            if not piles:
                self._logger.info(f"Support {support_state.support.name} has no piles.")
                continue

            piles_built_states = [
                PileBuildState(
                    support_index=sup_id,
                    pile= pile,
                    pile_properties= cast(GroupPropertiesPile, pile.properties)
                )
                for pile in piles
                if isinstance(pile.properties, GroupPropertiesPile)
            ]
            piles_by_support_index[sup_id].extend(piles_built_states)
            ctx.pile_states = piles_by_support_index

        self._validate_piles_inside_pilecap_perimeter(ctx)

    def _validate_piles_inside_pilecap_perimeter(self, ctx: GeometryPSCBoxBuildContext) -> None:
        for sup_id, pile_states in ctx.pile_states.items():
            support_state = ctx.support_states.get(sup_id)
            pilecap_state = ctx.pilecap_states.get(sup_id)

            if support_state is None or pilecap_state is None:
                self._logger.warning(f"Support {sup_id} has no support or pilecap state. Skipping pile validation.")
                continue

            pilecap_section = pilecap_state.horizontal_pilecap.get_section()
            if not isinstance(pilecap_section, SectionStandardSolidRectangle):
                self._logger.warning(f"Support {sup_id} has no valid horizontal pilecap section. Skipping pile validation.")
                continue

            pilecap_width = pilecap_section.dimensions.total_width
            pilecap_length = pilecap_state.pilecap_properties.element_length

            for pile_state in pile_states:
                pile_section = pile_state.pile.get_section()
                if pile_section is None:
                    self._logger.warning(f"Pile {pile_state.pile.name} has no valid section. Skipping validation.")
                    continue

                if isinstance(pile_section, SectionStandardSolidRectangle):

                    _h = pile_section.dimensions.total_height # TODO - this raises an error for solid-circle
                    _b = pile_section.dimensions.total_width

                    # Assuming the piles are centered on the support's centerline
                    transverse_max = pilecap_width / 2 - _h / 2
                    longitudinal_max = pilecap_length / 2 - _b / 2

                elif isinstance(pile_section, SectionStandardSolidRound):

                    _d = pile_section.dimensions.diameter_d

                    # Assuming the piles are centered on the support's centerline
                    transverse_max = pilecap_width / 2 - _d / 2
                    longitudinal_max = pilecap_length / 2 - _d / 2

                else:
                    raise NotImplementedError(f"Support: {sup_id}, section: {pile_section} is not implemented."
                                              f"Please use SectionStandardSolidRectangle or SectionStandardSolidRound.")

                pile_transverse_offset = _abs(pile_state.pile_properties.offset_normal_to_support_line)
                pile_longitudinal_offset = _abs(pile_state.pile_properties.offset_along_support_line)

                if pile_transverse_offset > transverse_max :
                    self._logger.warning(f"Pile {pile_state.pile.name} is outside the horizontal bounds of the pilecap. "
                                   f"pilecap width: {pilecap_width}, pile transverse offset: {pile_transverse_offset}.")

                if pile_longitudinal_offset > longitudinal_max:
                    self._logger.warning(f"Pile {pile_state.pile.name} is outside the longitudinal bounds of the pilecap. "
                                   f"pilecap length: {pilecap_length}, pile longitudinal offset: {pile_longitudinal_offset}.")


class CollectGirders(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        for span in ctx.span_states:
            idx = span.span_props.span_index
            girder_group = _require_single_girder(span)

            ctx.girder_states[idx] = GirderBuildState(
                span_index= idx,
                girder_group= girder_group,
            )


#
#   Reference geometry
#

class CreateSpanReferenceElements(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        for state in ctx.span_states:
            girder = _require_single_girder(state)

            _clear_girder_generated_data(girder)

            y = 0.0 * units.m
            z = 0.0 * units.m
            x_start = state.span_offset
            x_end = cast(Quantity, state.span_offset + state.span_props.span_length)

            node_start = ctx.amm.get_or_create_node(x=x_start, y=y, z=z)
            node_end = ctx.amm.get_or_create_node(x=x_end, y=y, z=z)

            reference_element = ctx.amm.create_and_add_reference_element(girder, node_start=node_start, node_end=node_end)
            state.reference_element = reference_element


class CreateCrossheadReferenceElement(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        for idx, crosshead in ctx.crosshead_states.items():

            skew_angle = ctx.support_states.get(idx).angle.to(units.ureg.rad).magnitude
            crosshead_length = crosshead.crosshead_properties.element_length

            x_center = ctx.support_states.get(idx).support_vector.start_point.x
            y_center = ctx.support_states.get(idx).support_vector.start_point.y

            dx = crosshead_length / 2 * math.sin(skew_angle)
            dy = crosshead_length / 2 * math.cos(skew_angle)
            z = ctx.support_states.get(idx).bearing_underside_relative_level

            start_node = ctx.amm.get_or_create_node(
                x= cast(Quantity, x_center - dx),
                y=  cast(Quantity, y_center - dy),
                z= z
            )

            end_node = ctx.amm.get_or_create_node(
                x= cast(Quantity, x_center + dx),
                y= cast(Quantity, y_center + dy),
                z= z
            )

            reference_element = ctx.amm.create_and_add_reference_element(crosshead.crosshead, node_start=start_node, node_end=end_node)


class CreatePilecapReferenceElements(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        for idx, pilecap_state in ctx.pilecap_states.items():
            pilecap = pilecap_state

            if pilecap is None:
                raise ValueError(f"No pilecap state found for pilecap_index={idx}. ")

            x_center = ctx.support_states.get(idx).support_vector.start_point.x
            y_center = ctx.support_states.get(idx).support_vector.start_point.y

            pilecap_length = pilecap.pilecap_properties.element_length
            skew_angle = ctx.support_states.get(idx).angle.to(units.ureg.rad).magnitude

            dx = cast(Quantity, pilecap_length /2 * math.sin(skew_angle))
            dy = cast(Quantity, pilecap_length /2 * math.cos(skew_angle))
            z = pilecap.pilecap_bottom_relative_level

            start_node = ctx.amm.get_or_create_node(
                x= x_center - dx,
                y= y_center - dy,
                z= z
            )

            end_node = ctx.amm.get_or_create_node(
                x = x_center + dx,
                y= y_center + dy,
                z= z
            )

            reference_element = ctx.amm.create_and_add_reference_element(pilecap.horizontal_pilecap, node_start=start_node, node_end=end_node)
            ctx.amm.add_reference_nodes(pilecap.horizontal_pilecap, [start_node, end_node])


class CreatePierReferenceElements(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        for support_index, pier_states in ctx.pier_states.items():

            support_state = ctx.support_states.get(support_index)

            if support_state is None:
                raise ValueError(f"No support state found for support_index={support_index}. "
                                 f"Cannot create pier reference elements.")

            support_skew_angle = support_state.support_properties.skew_angle

            for pier_state in pier_states:
                idx = pier_state.support_index
                pier_group = pier_state.pier
                pier_props = pier_state.pier_properties

                y_offset = cast(Quantity, pier_props.transverse_offset)
                x_offset = cast(Quantity, y_offset * math.tan(support_skew_angle.to(units.ureg.rad)))

                x_pier = support_state.support_vector.start_point.x + x_offset
                y_pier = support_state.support_vector.start_point.y + y_offset
                z_pier_upper = pier_state.crosshead_soffit_relative_level
                z_pier_lower = pier_state.pilecap_top_relative_level

                upper_node = ctx.amm.get_or_create_node(
                    x=x_pier,
                    y=y_pier,
                    z=z_pier_upper,
                )

                lower_node = ctx.amm.get_or_create_node(
                    x=x_pier,
                    y=y_pier,
                    z=z_pier_lower,
                )
                reference_element = ctx.amm.create_and_add_reference_element(pier_group, node_start=upper_node, node_end=lower_node)


class CreatePileReferenceElements(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        if ctx.pilecap_states is None:
            raise ValueError(f"Build context: No pilecap states found. ")

        for idx, pile_state in ctx.pile_states.items():
            support_state = ctx.support_states.get(idx)
            if support_state is None:
                raise ValueError(f"No support state found for support_index={idx}. "
                                 f"Cannot create pile reference elements.")

            pilecap_bottom_relative_level = ctx.pilecap_states.get(idx).pilecap_bottom_relative_level
            skew = ctx.support_states.get(idx).angle
            _sin = math.sin(skew.to(units.ureg.rad).magnitude)
            _cos = math.cos(skew.to(units.ureg.rad).magnitude)

            for pile in pile_state:
                pile_props = pile.pile_properties

                x_local = cast(Quantity, pile_props.offset_normal_to_support_line)
                y_local = cast(Quantity, pile_props.offset_along_support_line)

                x_pile = support_state.support_vector.start_point.x + x_local * _cos + y_local * _sin
                y_pile = support_state.support_vector.start_point.y - x_local * _sin + y_local * _cos
                z_pile_upper = pilecap_bottom_relative_level
                z_pile_lower = z_pile_upper - cast(Quantity, pile_props.pile_length)

                # projected point on pilecap reference element
                prf = cast(Element1D, ctx.pilecap_states[idx].horizontal_pilecap.reference_elements[0])
                prf_s = prf.node_start
                prf_e = prf.node_end
                line = AppliedVector.from_points(_node_to_point(prf_s), _node_to_point(prf_e))

                projected_point = (
                    GeometryTools
                    .project_point_on_line(
                    line=line,
                    point=Point(
                        x= cast(Quantity, x_pile),
                        y= cast(Quantity, y_pile),
                        z= z_pile_upper)
                    )
                )

                upper_node = ctx.amm.get_or_create_node(
                    x=cast(Quantity, x_pile),
                    y=cast(Quantity, y_pile),
                    z=z_pile_upper,
                )

                lower_node = ctx.amm.get_or_create_node(
                    x=cast(Quantity, x_pile),
                    y=cast(Quantity, y_pile),
                    z=z_pile_lower,
                )

                projected_node = ctx.amm.get_or_create_node(
                    x= projected_point.x,
                    y= projected_point.y,
                    z= projected_point.z,
                )

                reference_element = ctx.amm.create_and_add_reference_element(pile.pile, node_start=upper_node, node_end=lower_node)
                reference_element.beta_angle = ctx.support_states[idx].angle
                ctx.amm.add_reference_node(ctx.pilecap_states[idx].horizontal_pilecap, projected_node)


#
#   span FE
#

class GenerateSpanFiniteElements(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        mesh_divisor = ctx.girder_mesh_divisor
        if mesh_divisor is None:
            raise ValueError("Build context has no girder mesh divisor.")

        tolerance = ctx.builder._tolerance if ctx.builder is not None else 0.1 * units.mm

        for state in ctx.span_states:
            span_length = state.span_props.span_length
            delta = cast(Quantity, span_length / mesh_divisor)

            x_positions = {
                cast(Quantity, state.span_offset + i * delta)
                for i in range(mesh_divisor + 1)
            }

            for segment in state.tapered_segments:
                x_positions.add(segment.x_start)
                x_positions.add(segment.x_end)

            sorted_positions = list(general_tools.to_sorted_unique_collection(x_positions, tolerance))

            y = 0.0 * units.m
            z = 0.0 * units.m

            finite_elements: list[Element1D] = []
            for idx in range(len(sorted_positions) - 1):
                ni = ctx.amm.get_or_create_node(x=sorted_positions[idx], y=y, z=z)
                nj = ctx.amm.get_or_create_node(x=sorted_positions[idx + 1], y=y, z=z)
                finite_elements.append(ctx.amm.get_or_create_beam(node_start=ni, node_end=nj))

            state.finite_elements = finite_elements


class AssignSpanFiniteElementsToSegmentsGroups(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        sections_by_guid = {section.guid: section for section in ctx.amm.get_all_sections()}

        for state in ctx.span_states:
            girder = _require_single_girder(state)
            girder_props = cast(GroupPropertiesGirder, girder.properties)

            _remove_nested_segment_groups(girder)
            _remove_generated_finite_elements_from_girder(girder, state.finite_elements)

            for segment in state.tapered_segments:
                segment_elements = [
                    element
                    for element in state.finite_elements
                    if segment.x_start <= element.mid_point.X <= segment.x_end
                ]

                section = (
                        _get_section_or_none(sections_by_guid, segment.section_id)
                        or _get_section_or_none(sections_by_guid, segment.start_id)
                        or _get_section_or_none(sections_by_guid, segment.end_id)
                        or girder.get_section()
                )

                symmetric_plane: SymmetricPlaneType | None = None

                if isinstance(section, SectionTapered):
                    start_h = section.section_start.dimensions.total_height
                    end_h = section.section_end.dimensions.total_height

                    symmetric_plane = SymmetricPlaneType.START if start_h < end_h else SymmetricPlaneType.END

                segment_group = GeometryGroup(
                    component_type=StructuralComponentType.SEGMENT,
                    name=(
                        f"Span_{state.span_props.span_index}"
                        f"_Girder_{girder_props.girder_index}"
                        f"_Segment_{segment.segment_index}"
                    ),
                    properties=GroupPropertiesSegment(
                        segment_index=segment.segment_index,
                        is_tapered=segment.is_tapered,
                        symmetric_plane= symmetric_plane,
                    ),
                )


                segment_group.section = section
                ctx.amm.add_elements(segment_group, segment_elements)
                girder.add_nested_group(segment_group)


#
#   support linkage
#

class GenerateVerticalRigidLinkage(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        self.process_span_boundary(ctx)

    def _get_section_heights_for_support(self,
                                         support_idx: int,
                                         ctx: GeometryPSCBoxBuildContext
                                         ) -> Quantity:
        support_ref = _resolve_support_ref(support_idx)
        span_state = ctx.span_states[support_ref.span_idx]

        if support_idx == 0:
            return span_state.start_section.dimensions.total_height

        return span_state.end_section.dimensions.total_height

    def process_span_boundary(self, ctx: GeometryPSCBoxBuildContext) -> None:

        # establish section heights at supports
        section_heights_by_support_index: defaultdict[int, Quantity] = defaultdict(Quantity)

        for support_idx in range(len(ctx.spans) + 1):
            section_heights_by_support_index[support_idx] = (
                self._get_section_heights_for_support(
                    support_idx= support_idx,
                    ctx = ctx,
                )
            )

        # main loop: vertical rigid -> GIRDER geometry group -> analytical typology -> link
        for idx, state in ctx.support_states.items():
            x = state.support_vector.start_point.x
            y = 0.0 * ureg.m
            z_top = 0 * ureg.m
            z_bottom = -section_heights_by_support_index[idx]

            node_start = ctx.amm.get_or_create_node(x, y, z_top)
            node_end = ctx.amm.get_or_create_node(x, y, z_bottom)

            # assign rigid links to the GIRDER geometry group
            support_ref = _resolve_support_ref(idx)
            span_idx = support_ref.span_idx

            group = ctx.girder_states[span_idx].girder_group

            link = ctx.amm.create_and_add_link(group, node_start, node_end, LinkType.RIGID)
            link.beta_angle = state.angle


class CreateSupportBearingTopTopology(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:

        # creating side nodes -> connect with vertical rigid link bottom node (master) -> add to GIRDER group as a link
        for idx, state in ctx.sup_to_sub_states.items():

            details = (
                state
                .sup_to_sub_properties
                .bearing_configuration_details
            )

            bearing_type = details.bearing_configuration_type

            # single bearing -> no new nodes #TODO
            if bearing_type == BearingConfigurationType.SINGULAR:
                self._generate_single_bearing_link(support_idx=  idx, ctx=ctx)

            # multiple bearings -> create side nodes -> add bearing nodes (top only)
            elif bearing_type == BearingConfigurationType.MULTIPLE:
                if details.bearing_spacing_type == SpacingType.UNIFORM:
                    self._generate_multiple_uniform_links(support_idx= idx, ctx=ctx)
                else:
                    raise NotImplementedError(f"Non-uniform bearing spacing is not implemented yet for support index {idx}.")
            else:
                raise NotImplementedError(f"Bearing configuration type '{bearing_type}' is not implemented yet for support index {idx}.")

    def _get_support_nodes(self,
                           support_idx: int,
                           ctx: GeometryPSCBoxBuildContext,
                           ) -> tuple[Node, Node]:

        # establish GIRDER group and analytical typology for the support index
        support_ref = _resolve_support_ref(support_idx)
        span_idx = support_ref.span_idx
        link_idx = support_ref.link_idx
        rigid_link = ctx.girder_states[span_idx].girder_group.analytical_typology.links[link_idx]

        if rigid_link is None:
            raise ValueError(f"No rigid link found for support index {support_idx}, span {span_idx}, link {link_idx}. ")

        return rigid_link.node_start, rigid_link.node_end

    def _get_bearing_spacing_config(
            self,
            support_idx: int,
            ctx: GeometryPSCBoxBuildContext,
    ) -> BearingSpacingConfig:

        is_crosshead = support_idx in ctx.crosshead_states
        bearing_state = ctx.sup_to_sub_states[support_idx]

        # establish spacing of the bearings
        spacing: list[Quantity] = (bearing_state
                                   .sup_to_sub_properties
                                   .bearing_configuration_details
                                   .bearing_spacing)

        no_of_bearings = (bearing_state
                          .sup_to_sub_group
                          .properties.bearing_configuration_details
                          .no_of_bearings)

        #
        #   validation block
        #
        if spacing is None:
            raise ValueError(f"Spacing is not defined for support index {bearing_state.support_index}.")

        # check whether the spacing list is uniform
        if not all(s == spacing[0] for s in spacing):
            self._logger.warning(f"Spacing is not uniform for support index {bearing_state.support_index}. "
                           f"Spacing of {spacing[0]} has been assumed. ")

        dx = spacing[0]
        total_spacing = sum(spacing)

        if is_crosshead:
            length: Quantity = (ctx.crosshead_states[support_idx]
                                .crosshead_properties
                                .element_length
                                )

            if total_spacing > length:
                raise ValueError(
                    f"The sum of spacing is greater than crosshead length for support index {support_idx}. ")

            if len(spacing) != no_of_bearings - 1:
                raise ValueError(f"The no_of_bearings: {no_of_bearings} and the length of list of bearing spacings: "
                                 f"{spacing} should be consistent - for support index {support_idx}. ")

        self._logger.info(f"Support index {support_idx}: Bearing spacing configuration: "
                    f"no_of_bearings={no_of_bearings}, spacing={spacing}, dx={dx}. ")

        return BearingSpacingConfig(
            spacing=spacing,
            no_of_bearings=no_of_bearings,
            dx=dx,
        )

    def _get_master_node(
            self,
            support_idx: int,
            ctx: GeometryPSCBoxBuildContext,
    ) -> Node:

        node_start, node_end = self._get_support_nodes(
            support_idx= support_idx,
            ctx= ctx,
        )

        return min(
            node_start,
            node_end,
            key=lambda node: node.Z.to_base_units().magnitude,
        )

    def _calculate_bearing_positions(
            self,
            support_idx: int,
            ctx: GeometryPSCBoxBuildContext,
            dx: Quantity,
            no_of_bearings: int,
            spacing: list[Quantity],
    ) -> list[tuple[Quantity, Quantity]]:

        support_state = ctx.support_states[support_idx]

        skew = support_state.angle
        total_spacing = sum(spacing)
        x0 = support_state.support_vector.start_point.x
        y0 = support_state.support_vector.start_point.y

        _sin = math.sin(skew.to(units.ureg.rad).magnitude)
        _cos = math.cos(skew.to(units.ureg.rad).magnitude)

        x_local = [(n * dx) - total_spacing/2 for n in range(no_of_bearings)]
        y_global = [
            cast(Quantity, y0 + _x * _cos)
            for _x in x_local
        ]

        x_global = [
            cast(Quantity, x0 + _x * _sin)
            for _x in x_local
        ]

        positions =  [
            (x, y)
            for (x, y) in zip(x_global, y_global)
        ]

        sorted_positions = sorted(
            positions,
            key=lambda p: p[1].to_base_units().magnitude,
            reverse=True
        )

        return sorted_positions

    def _create_support_rigid_link(
            self,
            support_idx: int,
            ctx: GeometryPSCBoxBuildContext,
            node: Node,
            master_node: Node,
    ) -> ElementLink:

        girder_state = ctx.girder_states[support_idx]

        link = (
            ctx.amm.get_or_create_link(
                node_start=node,
                node_end=master_node,
                link_type=LinkType.RIGID,
            )
        )

        ctx.amm.add_element(girder_state.girder_group, link)

        return link

    def _add_bearing_top_nodes(
            self,
            support_idx: int,
            ctx: GeometryPSCBoxBuildContext,
            node: Node,
            bearing_index: int,
    ) -> None:

        ctx.amm.add_bearing_nodes(ctx.sup_to_sub_states[support_idx].sup_to_sub_group, 
            girder_index=0,
            bearing_index= bearing_index,
            node_start= node,
        )

    def _generate_single_bearing_link(
            self,
            support_idx: int,
            ctx: GeometryPSCBoxBuildContext,
    ) -> None:
        """
        Generates a rigid-link assembly for supports with a single bearing.
        """
        master_node = self._get_master_node(
            support_idx= support_idx,
            ctx= ctx,
        )

        # bearing top node: SUP-TO-SUB group
        self._add_bearing_top_nodes(
            support_idx=support_idx,
            ctx=ctx,
            bearing_index=0,
            node=master_node,
        )

    def _generate_multiple_uniform_links(
            self,
            support_idx: int,
            ctx: GeometryPSCBoxBuildContext
    ) -> None:
        """
        Generates a rigid-link assembly for supports with uniformly spaced multiple bearings.
        """
        config = self._get_bearing_spacing_config(
            support_idx= support_idx,
            ctx= ctx
        )

        master_node = self._get_master_node(
            support_idx= support_idx,
            ctx= ctx
        )

        positions = self._calculate_bearing_positions(
            support_idx= support_idx,
            ctx= ctx,
            dx = config.dx,
            no_of_bearings= config.no_of_bearings,
            spacing= config.spacing,
        )

        for i, (x, y) in enumerate(positions):
            node = ctx.amm.get_or_create_node(
                x= x,
                y= y,
                z= master_node.Z,
            )

            # horizontal rigid link: GIRDER group
            if node.node_id != master_node.node_id:
                self._create_support_rigid_link(
                    support_idx= support_idx,
                    ctx = ctx,
                    node = node,
                    master_node = master_node,
                )

            # bearing top node: SUP-TO-SUB group
            self._add_bearing_top_nodes(
                support_idx= support_idx,
                ctx=ctx,
                bearing_index= i,
                node= node,
            )

class CreateSupportBearingBottomTopology(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:

        for idx, sup_to_sub in ctx.sup_to_sub_states.items():

            analytical_typology = sup_to_sub.sup_to_sub_group.analytical_typology

            if analytical_typology.bearing_nodes is None:
                raise ValueError(f"No bearing nodes found for support index {idx}. Cannot create bottom topology.")

            for bearing_key, bearing_nodes in analytical_typology.bearing_nodes.items():

                bottom_node = ctx.amm.get_or_create_node(
                    x= bearing_nodes.node_top.X,
                    y= bearing_nodes.node_top.Y,
                    z= ctx.support_states[idx].bearing_underside_relative_level,
                )

                ctx.amm.update_bearing_nodes(sup_to_sub.sup_to_sub_group, 
                    key= bearing_key,
                    node_end= bottom_node,
                )


class CollectNodesForCrosshead(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        """
        -> get bearing and pier nodes
        -> project at crosshead level
        -> add as crosshead reference nodes
        """

        self._add_crosshead_reference_nodes(ctx= ctx)
        self._add_rigid_links_crosshead_piers(ctx= ctx)

    def _add_rigid_links_crosshead_piers(self, ctx: GeometryPSCBoxBuildContext) -> None:

        for idx in ctx.support_states.keys():

            if idx not in ctx.crosshead_states:
                continue

            if idx not in ctx.pier_states:
                continue

            z = ctx.support_states[idx].bearing_underside_relative_level

            pier_state = ctx.pier_states[idx]

            for pier in pier_state:
                ref = pier.pier.reference_elements[0]
                assert isinstance(ref, Element1D)

                bottom_node = max(
                    ref.node_start,
                    ref.node_end,
                    key= lambda node: node.Z,
                )

                top_node = ctx.amm.get_or_create_node(
                    x= bottom_node.X,
                    y= bottom_node.Y,
                    z= z,
                )

                link = ctx.amm.create_and_add_link(pier.pier, node_start= top_node,
                    node_end= bottom_node,
                    link_type= LinkType.RIGID)


    def _add_crosshead_reference_nodes(self, ctx: GeometryPSCBoxBuildContext) -> None:
        for idx in ctx.sup_to_sub_states.keys():
            bottom_support_nodes = self._collect_bearing_bottom_nodes(
                support_idx= idx,
                ctx= ctx,
            )

            top_pier_nodes = self._collect_pier_top_nodes(
                support_idx= idx,
                ctx= ctx,
            )

            projected_top_pier_nodes = _copy_nodes_at_z(
                source_nodes=top_pier_nodes,
                ctx= ctx,
                reference= ctx.support_states[idx].bearing_underside_relative_level,
            )

            if idx in ctx.crosshead_states:
                crosshead = ctx.crosshead_states[idx].crosshead
                ctx.amm.add_reference_nodes(crosshead, 
                    nodes= bottom_support_nodes  + projected_top_pier_nodes
                )

    def _collect_pier_top_nodes(
            self,
            support_idx: int,
            ctx: GeometryPSCBoxBuildContext
    ) -> list[Node]:

        if support_idx not in ctx.pier_states:
            return []

        if support_idx not in ctx.crosshead_states:
            return []


        nodes: list[Node] = []
        piers = ctx.pier_states[support_idx]

        for pier in piers:

            ref = pier.pier.reference_elements[0]
            if ref is None:
                raise ValueError(f"No reference element found for support index {support_idx}.")

            assert isinstance(ref, Element1D)

            top_node = max(
                ref.node_start,
                ref.node_end,
                key=lambda node: node.Z.to_base_units().magnitude,
            )
            nodes.append(top_node)

        return nodes

    def _collect_bearing_bottom_nodes(
            self,
            support_idx: int,
            ctx: GeometryPSCBoxBuildContext,
    ) -> list[Node]:

        if support_idx not in ctx.crosshead_states:
            return []

        bearings_nodes = (
            ctx
            .sup_to_sub_states[support_idx]
            .sup_to_sub_group
            .analytical_typology
            .bearing_nodes
            .items()
        )

        bottom_support_nodes = [
            pair.node_bottom
            for _, pair in bearings_nodes
            if pair.node_bottom is not None
        ]

        return bottom_support_nodes


#
#   pilecap/pier/pile FE
#

class CreateHorizontalPilecapElements(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        for idx, pilecap_state in ctx.pilecap_states.items():
            ref_nodes = pilecap_state.horizontal_pilecap.reference_nodes
            ref_nodes_sorted = sorted(ref_nodes, key=lambda node: node.Y)

            for i in range(len(ref_nodes_sorted) - 1):
                node_start = ref_nodes_sorted[i]
                node_end = ref_nodes_sorted[i + 1]
                element = ctx.amm.create_and_add_beam(
                    pilecap_state.horizontal_pilecap,
                    node_start=node_start,
                    node_end=node_end)


class CreatePierFiniteElements(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        for idx, pier_state in ctx.pier_states.items():

            angle = ctx.support_states[idx].angle
            
            for pier in pier_state:
                ref = pier.pier.reference_elements[0]
                assert isinstance(ref, Element1D)
                pier_length = cast(Quantity, ref.node_start.Z - ref.node_end.Z)

                # _N is an arbitrary value,
                #  to be confirmed how much finite elements should pier have

                if pier_length >= 2.0 * pier_length.units:
                    _N = int(pier_length.to(units.ureg.m).magnitude / 2.0)
                else:
                    _N = 1

                dz = cast(Quantity, pier_length / _N)

                x = ref.node_start.X
                y = ref.node_start.Y
                z = ref.node_start.Z
                start_node = ctx.amm.get_or_create_node(x, y, z)

                for i in range(_N):
                    end_node = ctx.amm.get_or_create_node(x, y, cast(Quantity, start_node.Z - dz))
                    beam = ctx.amm.create_and_add_reference_element(pier.pier, node_start=start_node, node_end=end_node)
                    beam.beta_angle = angle
                    ctx.amm.add_element(pier.pier, beam)
                    start_node = end_node


class CreatePileFiniteElements(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        for _, pile_states in ctx.pile_states.items():

            for pile_state in pile_states:
                finite_elements: list[Element1D] = []

                pile_ref = pile_state.pile.reference_elements[0]
                assert isinstance(pile_ref, Element1D)

                node_start = pile_ref.node_start
                node_end = pile_ref.node_end

                # Determine pile head and pile toe
                if node_start.Z >= node_end.Z:
                    top_node = node_start
                    bottom_node = node_end
                else:
                    top_node = node_end
                    bottom_node = node_start

                pile_props = pile_state.pile_properties
                pile_length = pile_props.pile_length

                current_node = top_node
                current_depth = 0 * units.m

                for spacing in pile_props.spring_spacing:

                    if spacing <= 0 * units.m:
                        self._logger.warning(
                            f"Pile '{pile_state.pile.name}' contains "
                            f"non-positive spring spacing: {spacing}"
                        )
                        continue

                    current_depth += spacing

                    # Do not create a node below the pile toe
                    if current_depth >= pile_length:
                        break

                    next_node = ctx.amm.get_or_create_node(
                        x=top_node.X,
                        y=top_node.Y,
                        z=cast(Quantity, top_node.Z - current_depth),
                    )

                    beam = ctx.amm.get_or_create_beam(
                        node_start=current_node,
                        node_end=next_node,
                    )

                    finite_elements.append(beam)
                    current_node = next_node

                # Final segment to pile toe
                final_beam = ctx.amm.get_or_create_beam(
                    node_start=current_node,
                    node_end=bottom_node,
                )

                finite_elements.append(final_beam)
                ctx.amm.add_elements(pile_state.pile, finite_elements)


#
#   pilecap vertical members
#

class CreateVerticalPilecapReferenceElements(BuildStep):
    def _find_below_ground_vertical_members_group(self, ctx: GeometryPSCBoxBuildContext, idx: int) -> GeometryGroup:
        below_ground = (
            ctx.support_states[idx]
            .support
            .get_first_group_by_component_type(
                StructuralComponentType.BELOW_GROUND
            )
        )

        if below_ground is None:
            raise RuntimeError(
                f"BELOW_GROUND group not found for support {idx}"
            )

        vertical_members = (
            below_ground.get_first_group_by_component_type(
                StructuralComponentType.VERTICAL_MEMBERS
            )
        )

        if vertical_members is None:
            raise RuntimeError(
                f"VERTICAL_MEMBERS group not found for support {idx}"
            )

        return vertical_members

    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        for idx, pier_state in ctx.pier_states.items():

            beta_angle = ctx.support_states[idx].angle

            for i, pier in enumerate(pier_state):
                ref = pier.pier.reference_elements[0]

                if not isinstance(ref, Element1D):
                    continue

                vertical_members_pilecap_group = GeometryGroup(
                    name=f"pilecap_vertical_{idx}_{i}",
                    component_type=StructuralComponentType.PILE_CAP
                )

                # geometry
                x = ref.node_end.X
                y = ref.node_end.Y

                z_start = ref.node_start.Z
                z_end = ref.node_end.Z

                z_top = min(z_start, z_end) #type: ignore

                z_bottom = (
                    ctx.pilecap_states[idx]
                    .pilecap_bottom_relative_level
                )

                node_start = ctx.amm.get_or_create_node(
                    x=x,
                    y=y,
                    z=z_top
                )

                node_end = ctx.amm.get_or_create_node(
                    x=x,
                    y=y,
                    z=z_bottom
                )

                beam = ctx.amm.get_or_create_beam(
                    node_start=node_start,
                    node_end=node_end,
                )

                beam.beta_angle = beta_angle

                ctx.amm.add_reference_element(vertical_members_pilecap_group, beam)
                below_ground_vertical_members_group = self._find_below_ground_vertical_members_group(ctx, idx)
                below_ground_vertical_members_group.add_nested_group(vertical_members_pilecap_group)
                ctx.pilecap_states[idx].vertical_members_group = below_ground_vertical_members_group


class CreateVerticalPilecapFiniteElements(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:

        for idx, pilecap_state in ctx.pilecap_states.items():

            if pilecap_state.vertical_members_group is None:
                raise ValueError(f"Build context: Pilecap state {idx} has no vertical members.")

            boundary_nodes: list[Node] = self.collect_nodes(pilecap_state)
            internal_nodes: list[Node] = self.collect_vertical_pilecap_nodes(ctx.support_states[idx])
            collected_nodes: list[Node] = boundary_nodes + internal_nodes
            collected_nodes.sort(key=lambda n: n.Y)
            regions = self._tributary_regions(collected_nodes)
            pilecap_vertical_members = (pilecap_state
                                        .vertical_members_group
                                        .get_groups_by_component_type(StructuralComponentType.PILE_CAP))

            pilecap_sorted = sorted(
                pilecap_vertical_members,
                key=lambda n: n.reference_elements[0].node_end.Y
            )

            if len(pilecap_sorted) != len(regions):
                raise ValueError(f"The number of tributary regions is different from the number of vertical pilecap elements: support {idx}")

            for i, vertical_pilecap in enumerate(pilecap_sorted):
                offset = Offset(
                    horizontal_value=cast(Quantity, regions[i].width / 2 - regions[i].offset),
                    vertical_value= cast(Quantity, 0 * units.m),
                    offset_reference=OffsetReference.LEFT_CENTER
                )
                h = pilecap_state.horizontal_pilecap.section.dimensions.total_width
                b = regions[i].width

                section = SectionStandardSolidRectangle(
                    name=vertical_pilecap.name + str(i),
                    offset= offset,
                    dimensions= DimensionsSolidRectangle(height_h= h, width_b= b)
                )
                vertical_pilecap.section = section

                weightless_material = self._require_weightless_material(
                    ctx= ctx,
                    source_material= pilecap_state.horizontal_pilecap.get_material()
                )

                if weightless_material is not None:
                    vertical_pilecap.material = weightless_material

                section.set_material_main(weightless_material)
                ctx.amm.add_element(vertical_pilecap, vertical_pilecap.reference_elements[0])

    def _require_weightless_material(
            self,
            ctx: GeometryPSCBoxBuildContext,
            source_material: Material | None,
    ) -> Material | None:
        # to avoid duplicated weightless materials create a memory cache:

        if source_material is None:
            return None

        material_weightless = ctx.weightless_materials.get(source_material.guid, None)

        if material_weightless is None:
            material_weightless = deepcopy(source_material)
            material_weightless.name = f"{source_material.name}_weightless"
            material_weightless.general_properties.unit_weight = 0 * units.kN / units.m**3
            ctx.weightless_materials[source_material.guid] = material_weightless

        return material_weightless

    def collect_vertical_pilecap_nodes(self, support_state: SupportBuildState) -> list[Node]:
        nodes: list[Node] = []

        below_ground = support_state.support.get_first_group_by_component_type(StructuralComponentType.BELOW_GROUND)
        vertical_members = below_ground.get_first_group_by_component_type(StructuralComponentType.VERTICAL_MEMBERS)
        vertical_pilecaps = vertical_members.get_groups_by_component_type(StructuralComponentType.PILE_CAP)

        for _ in vertical_pilecaps:
            ref = cast(Element1D, _.reference_elements[0])
            nodes.append(ref.node_end)
        return nodes

    def collect_nodes(self, pilecap_state: PilecapBuildState) -> list[Node]:
        nodes: list[Node] = []
        pilecap_reference_element = cast(Element1D, pilecap_state.horizontal_pilecap.reference_elements[0])

        node_start = pilecap_reference_element.node_start
        node_end = pilecap_reference_element.node_end

        nodes.extend([node_start, node_end])

        return nodes

    @staticmethod
    def _tributary_regions(nodes: list[Node]) -> list[TributaryRegion]:
        """
        Calculates tributary regions for all interior nodes.

        Nodes must be sorted along the element axis.

        Returns:
            One tributary region for each interior node.
        """

        if len(nodes) < 3:
            return []

        nodes = sorted(nodes, key=lambda node: node.Y)

        origin = nodes[0]

        axis = Vector.from_nodes(nodes[0], nodes[-1]).normalize()

        positions = [
            Vector.from_nodes(origin, node)
            .dot(axis) #type: ignore
            for node in nodes
        ]

        regions: list[TributaryRegion] = []

        for idx in range(1, len(nodes) - 1):
            s_prev = positions[idx - 1]
            s_curr = positions[idx]
            s_next = positions[idx + 1]

            if idx == 1:
                left_boundary = s_prev
            else:
                left_boundary = (s_prev + s_curr) / 2

            if idx == len(nodes) - 2:
                right_boundary = s_next
            else:
                right_boundary = (s_curr + s_next) / 2

            width = right_boundary - left_boundary
            center = (left_boundary + right_boundary) / 2
            offset = center - s_curr

            regions.append(
                TributaryRegion(
                    node=nodes[idx],
                    left_boundary=left_boundary,
                    right_boundary=right_boundary,
                    width=cast(Quantity, width),
                    offset=cast(Quantity, offset),
                )
            )

        return regions


#
#   Crosshead
#

class CreateCrossheadTaperedSegments(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        sections_by_guid = {
            section.guid: section
            for section in ctx.amm.get_all_sections()
        }

        for idx, state in ctx.crosshead_states.items():
            crossbeam_length = state.crosshead_properties.element_length
            tapered_details = state.crosshead_properties.tapered_details
            tol = ctx.builder._tolerance
            base_section_id = state.crosshead.get_section().guid

            if base_section_id is None:
                raise ValueError(f"No section assigned to the crosshead over support index: {idx}. ")

            sorted_tapered_details = self._validate_tapered_details(
                tapered_details=tapered_details,
                crossbeam_length=crossbeam_length,
                support_idx=idx,
                tol=tol,
            )

            state.tapered_details = sorted_tapered_details

            segments: list[CrossheadSegmentResult] = []
            support_vector = state.support_vector.vector # z value ????
            support_point = state.support_vector.start_point

            #------------------------------------------------
            #   tapered segments
            #------------------------------------------------

            for tapered in sorted_tapered_details:

                start_id, end_id = self._resolve_taper_transition_ids(
                    tapered=tapered,
                    sections_by_guid= sections_by_guid,
                    support_idx=idx
                )

                if start_id is None:
                    raise ValueError(f"Missing start_id for {tapered} section. ")
                elif end_id is None:
                    raise ValueError(f"Missing end_id for {tapered} section. ")

                segment_start_point = support_point.translate(
                    support_vector,
                    tapered.x_start
                )
                segment_end_point = support_point.translate(
                    support_vector,
                    tapered.x_end
                )

                section = _get_section_or_none(sections_by_guid, tapered.section_id)

                segments.append(
                    CrossheadSegmentResult(
                        point_start=segment_start_point,
                        point_end=segment_end_point,
                        x_start=tapered.x_start,
                        x_end=tapered.x_end,
                        section_id=tapered.section_id,
                        start_id=start_id,
                        end_id=end_id,
                        is_tapered=True,
                        section=section,
                    )
                )

                # mirrored:
                segment_start_point = support_point.translate(
                    support_vector,
                    -tapered.x_end
                )
                segment_end_point = support_point.translate(
                    support_vector,
                    -tapered.x_start
                )

                tapered_section = sections_by_guid[tapered.section_id]
                assert isinstance(tapered_section, SectionTapered)

                section_mirrored = SectionTapered(
                    name= f"{tapered_section.name}_mirrored",
                    section_start_id= tapered_section.section_end_id,
                    section_end_id= tapered_section.section_start_id,
                    offset= tapered_section.offset,
                    taper_z_variation= tapered_section.taper_z_variation,
                    taper_y_variation= tapered_section.taper_y_variation,
                )

                section_mirrored.set_section_start(tapered_section.section_end)
                section_mirrored.set_section_end(tapered_section.section_start)

                segments.append(
                    CrossheadSegmentResult(
                        point_start=segment_start_point,
                        point_end=segment_end_point,
                        section_id=section_mirrored.guid,
                        x_start=-tapered.x_end,
                        x_end=-tapered.x_start,
                        start_id=end_id,
                        end_id=start_id,
                        is_tapered=True,
                        section= section_mirrored,
                    )
                )

            # add non tapered segments
            sorted_segments = sorted(
                segments,
                key=lambda x: x.x_start.to_base_units().magnitude,
            )

            crosshead_start = cast(Quantity, -crossbeam_length / 2)
            crosshead_end = cast(Quantity, crossbeam_length / 2)

            all_segments: list[CrossheadSegmentResult] = []

            # -----------------------------------------------------------------
            # no tapers at all
            # -----------------------------------------------------------------

            if not sorted_segments:
                section = _get_section_or_none(sections_by_guid, base_section_id)

                state.crosshead_segments = [
                    CrossheadSegmentResult(
                        point_start=support_point.translate(
                            support_vector,
                            crosshead_start,
                        ),
                        point_end=support_point.translate(
                            support_vector,
                            crosshead_end,
                        ),
                        x_start=crosshead_start,
                        x_end=crosshead_end,
                        section_id= base_section_id,
                        start_id=base_section_id,
                        end_id=base_section_id,
                        is_tapered=False,
                        section=section,
                    )
                ]
                continue

            # -----------------------------------------------------------------
            # segment before first taper
            # -----------------------------------------------------------------

            first_segment = sorted_segments[0]

            if (first_segment.x_start - crosshead_start) > tol:
                section = _get_section_or_none(sections_by_guid, first_segment.start_id)

                all_segments.append(
                    CrossheadSegmentResult(
                        point_start=support_point.translate(
                            support_vector,
                            crosshead_start,
                        ),
                        point_end=support_point.translate(
                            support_vector,
                            first_segment.x_start,
                        ),
                        x_start=crosshead_start,
                        x_end=first_segment.x_start,
                        section_id=first_segment.section_id,
                        start_id=first_segment.start_id,
                        end_id=first_segment.start_id,
                        is_tapered=False,
                        section= section,
                    )
                )

            # -----------------------------------------------------------------
            # segment after last taper
            # -----------------------------------------------------------------

            last_segment = sorted_segments[-1]

            if (crosshead_end - last_segment.x_end) > tol:
                section = _get_section_or_none(sections_by_guid, last_segment.end_id)

                all_segments.append(
                    CrossheadSegmentResult(
                        point_start=support_point.translate(
                            support_vector,
                            last_segment.x_end,
                        ),
                        point_end=support_point.translate(
                            support_vector,
                            crosshead_end,
                        ),
                        x_start=last_segment.x_end,
                        x_end=crosshead_end,
                        section_id=last_segment.end_id,
                        start_id=last_segment.end_id,
                        end_id=last_segment.end_id,
                        is_tapered=False,
                        section= section,
                    )
                )

            # -----------------------------------------------------------------
            # tapered segments + gaps between them
            # -----------------------------------------------------------------

            for seg_idx, segment in enumerate(sorted_segments):

                all_segments.append(segment)

                if seg_idx == len(sorted_segments) - 1:
                    continue

                next_segment = sorted_segments[seg_idx + 1]

                if (next_segment.x_start - segment.x_end) > tol:
                    section = _get_section_or_none(sections_by_guid, segment.end_id)

                    all_segments.append(
                        CrossheadSegmentResult(
                            point_start=support_point.translate(
                                support_vector,
                                segment.x_end,
                            ),
                            point_end=support_point.translate(
                                support_vector,
                                next_segment.x_start,
                            ),
                            x_start=segment.x_end,
                            x_end=next_segment.x_start,
                            section_id=segment.end_id,
                            start_id=segment.end_id,
                            end_id=segment.end_id,
                            is_tapered=False,
                            section= section,
                        )
                    )
            all_segments.sort(key=lambda x: x.x_start.to_base_units().magnitude)
            state.crosshead_segments = all_segments


    @staticmethod
    def _validate_tapered_details(
            tapered_details: list[TaperedDetails],
            crossbeam_length: Quantity,
            support_idx: Optional[int],
            tol: Quantity,
    ) -> list[TaperedDetails]:

        sorted_tapered_details = sorted(
            tapered_details,
            key=lambda x: x.x_start.to_base_units().magnitude
        )

        for tapered in sorted_tapered_details:
            if is_close(tapered.x_start, tapered.x_end, tol) or tapered.x_end < tapered.x_start:
                raise ValueError(
                    f"Invalid tapered range for support_index={support_idx}."
                    f"x_start={tapered.x_start}, x_end={tapered.x_end} tol={tol}"
                )

            if tapered.x_start < -tol or tapered.x_end > crossbeam_length / 2 + tol:
                raise ValueError(
                    f"Tapered range outside span bounds for support_index={support_idx}."
                    f"x_start={tapered.x_start}, x_end={tapered.x_end}, crossbeam_length={crossbeam_length}, tol={tol}"
                )

        return sorted_tapered_details

    @staticmethod
    def _resolve_taper_transition_ids(
            tapered: TaperedDetails,
            sections_by_guid: Dict[UUID, object],
            support_idx: Optional[int]
    ) -> tuple[UUID, UUID]:

        tapered_section = sections_by_guid.get(tapered.section_id)

        if tapered_section is None:
            raise ValueError(
                f"Tapered section id {tapered.section_id} not found - support index = {support_idx}."
            )

        if not isinstance(tapered_section, SectionTapered):
            raise ValueError(
                f"Section {tapered.section_id} is not SectionTapered - support index = {support_idx}."
            )

        return tapered_section.section_start_id, tapered_section.section_end_id


class GenerateCrossheadFiniteElements(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        for support_idx, crosshead_state in ctx.crosshead_states.items():
            finite_elements: list[Element1D] = []

            reference_nodes = crosshead_state.crosshead.reference_nodes
            reference_points = [_node_to_point(node) for node in reference_nodes]

            points = {
                (p.x, p.y, p.z) for p in reference_points
            }

            for segment in crosshead_state.crosshead_segments:
                points.add((segment.point_start.x, segment.point_start.y, segment.point_start.z))
                points.add((segment.point_end.x, segment.point_end.y, segment.point_end.z))

            sorted_y_positions = sorted(points,
                                        key= lambda p: p[1],
                                        )

            for i in range(len(sorted_y_positions) - 1):
                point_start = sorted_y_positions[i]
                point_end = sorted_y_positions[i + 1]

                ni = ctx.amm.get_or_create_node(
                    x=point_start[0],
                    y=point_start[1],
                    z=point_start[2],
                )

                nj = ctx.amm.get_or_create_node(
                    x=point_end[0],
                    y=point_end[1],
                    z=point_end[2],
                )

                finite_elements.append(
                    ctx.amm.get_or_create_beam(
                        node_start= ni,
                        node_end= nj,
                    )
                )

            crosshead_state.finite_elements = finite_elements


class AssignCrossheadFiniteElementsToSegmentsGroups(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        sections_by_guid = {section.guid: section for section in ctx.amm.get_all_sections()}

        for idx, state in ctx.crosshead_states.items():
            crosshead = state.crosshead
            crosshead_properties = cast(GroupPropertiesCrossbeam, crosshead.properties)

            _remove_nested_segment_groups(crosshead)

            for segment_idx, segment in enumerate(state.crosshead_segments):

                segment_elements = [
                    element
                    for element in state.finite_elements
                    if segment.point_start.y <= element.mid_point.Y <= segment.point_end.y
                ]

                symmetric_plane: SymmetricPlaneType | None = None

                if isinstance(segment.section, SectionTapered):
                    start_h = segment.section.section_start.dimensions.total_height
                    end_h = segment.section.section_end.dimensions.total_height

                    symmetric_plane = SymmetricPlaneType.START if start_h < end_h else SymmetricPlaneType.END

                segment_group = GeometryGroup(
                    component_type=StructuralComponentType.SEGMENT,
                    name=(
                        f"Crossbeam_{idx}"
                        f"_Segment_{segment_idx}"
                    ),
                    properties=GroupPropertiesSegment(
                        segment_index=segment_idx,
                        is_tapered=segment.is_tapered,
                        symmetric_plane= symmetric_plane,
                    ),
                )

                segment_group.section = segment.section
                ctx.amm.add_elements(segment_group, segment_elements)
                crosshead.add_nested_group(segment_group)


#
#   rigid links
#

class GeneratePileLinks(BuildStep):
    def _execute(self, ctx: GeometryPSCBoxBuildContext) -> None:
        for idx, pile_states in ctx.pile_states.items():
            for pile in pile_states:

                ref_pile = pile.pile.reference_elements[0]
                assert isinstance(ref_pile, Element1D)

                ref_pilecap = ctx.pilecap_states[idx].horizontal_pilecap.reference_elements[0]
                assert isinstance(ref_pilecap, Element1D)

                x = ref_pile.node_start.X
                y = ref_pile.node_start.Y
                z = ref_pile.node_start.Z

                # projected point on pilecap reference element
                prf_s = ref_pilecap.node_start
                prf_e = ref_pilecap.node_end
                line = AppliedVector.from_points(_node_to_point(prf_s), _node_to_point(prf_e))
                projected_point: Point = GeometryTools.project_point_on_line(
                    line=line,
                    point=Point(x, y, z),
                    clamp= True
                )

                projected_node = ctx.amm.get_or_create_node(*projected_point.to_array())

                if projected_node.uid == ref_pile.node_start.uid:
                    continue

                link = ctx.amm.create_and_add_link(pile.pile, node_start= ref_pile.node_start,
                    node_end= projected_node,
                    link_type= LinkType.RIGID)


#
#   HELPERS
#

def _require_single_girder(state: SpanBuildState) -> GeometryGroup:
    girder_groups = state.span.get_groups_by_component_type(StructuralComponentType.GIRDER)
    if len(girder_groups) != 1:
        raise ValueError(
            "PSC span must contain exactly one GIRDER group. "
            f"Span '{state.span.name}' (index={state.span_props.span_index}) has {len(girder_groups)} girders."
        )
    return girder_groups[0]


def _clear_girder_generated_data(girder: GeometryGroup) -> None:
    # Keep only one regenerated reference element per build.
    girder._reference_elements.clear()


def _remove_nested_segment_groups(girder: GeometryGroup) -> None:
    girder._nested_groups[:] = [
        group
        for group in girder.nested_groups
        if group.component_type != StructuralComponentType.SEGMENT
    ]


def _remove_generated_finite_elements_from_girder(girder: GeometryGroup, finite_elements: list[Element1D]) -> None:
    if not finite_elements:
        return

    generated_ids = {id(element) for element in finite_elements}
    girder.analytical_typology._elements[:] = [
        element
        for element in girder.analytical_typology.elements
        if id(element) not in generated_ids
    ]


def _get_section_or_none(sections_by_guid: dict, section_id):
    """
    Retrieves a section by its identifier.

    Returns None if the section identifier is not provided or the section
    cannot be found.
    """

    if section_id is None:
        return None
    return sections_by_guid.get(section_id)


def _node_to_point(node: Node) -> Point:
    """
    Converts a Node object into a Point with identical coordinates.
    """
    return Point(x=node.X, y=node.Y, z=node.Z)


def _copy_nodes_at_z(
        ctx: GeometryPSCBoxBuildContext,
        source_nodes: list[Node] | Sequence[Node],
        reference: Node | Quantity,
) -> list[Node]:
    """
    Creates copies of the source nodes at the elevation of the reference node.
    The X and Y coordinates are preserved while the Z coordinate is replaced
    with the reference node elevation.
    """

    if isinstance(reference, Node):
        z = cast(Quantity, reference.Z)
    else:
        z = reference

    translated_nodes: list[Node] = []

    for node in source_nodes:
        new_node = (
            ctx.amm.get_or_create_node(
                x=node.X,
                y=node.Y,
                z=z,
            )
        )
        translated_nodes.append(new_node)

    return translated_nodes

def _deduplicate_nodes(
        source_nodes: list[Node] | Sequence[Node],
) -> list[Node]:
    """
    Removes duplicate nodes while preserving their original order.

    Nodes are considered duplicates if they share the same node_id.
    """

    deduplicated_nodes: list[Node] = []

    for node in source_nodes:
        if any(n.node_id == node.node_id for n in deduplicated_nodes):
            continue
        deduplicated_nodes.append(node)

    return deduplicated_nodes


def _filter_nodes_by_z(
        source_nodes: list[Node] | Sequence[Node],
        reference_node: Node,
) -> list[Node]:
    """
    Filters nodes located at the same elevation as the reference node.
    """

    filtered_nodes: list[Node] = []

    for node in source_nodes:
        if node.Z == reference_node.Z:
            filtered_nodes.append(node)

    return filtered_nodes


def _find_group_by_node(
        groups: list[GeometryGroup],
        node: Node
) -> GeometryGroup | None:
    """
    Finds the geometry group containing the specified node.

    Returns None if no matching group is found.
    """

    for group in groups:

        nodes: list[Node] = []

        nodes.extend(
            n
            for element in group.reference_elements
            for n in [element.node_start, element.node_end] #type: ignore
        )
        nodes.extend(group.reference_nodes)
        nodes = _deduplicate_nodes(nodes)

        if any(n.node_id == node.node_id for n in nodes):
            return group
    return None


def _abs(x: Quantity) -> Quantity:
    """
    Returns the absolute value of a quantity while preserving its units.
    """
    return x if x >= 0 * x.units else -x

def _links_to_nodes(lst: list[ElementLink]) -> list[Node]:
    """Extracts all unique nodes referenced by a collection of link elements.

    For each link, both the start and end nodes are added to the result.
    Duplicate nodes are removed before returning the final list.

    Args:
         lst (list[ElementLink]): Collection of link elements.

    Returns:
        list[Node]: List of unique nodes referenced by the provided links.
    """
    result: list[Node] = []

    for e in lst:
        result.append(e.node_start)
        result.append(e.node_end)
    _deduplicate_nodes(result)

    return result

@dataclass(frozen=True)
class SpanSupportRef:
    """Reference to a support location within a span.

    Attributes:
        span_idx: Index of the span associated with the support.
        link_idx: Index of the support position within the span.
    """
    span_idx: int
    link_idx: int

def _resolve_support_ref(support_idx: int) -> SpanSupportRef:
    """Maps a global support index to a span support reference.

    The first support is assigned to span 0, support position 0.
    The second support is assigned to span 0, support position 1.
    All subsequent supports are assigned to the start position
    (link_idx = 0) of the following spans.

    Args:
        support_idx: Global support index.

    Returns:
        SpanSupportRef describing the corresponding span and support
        position within that span.
    """
    if support_idx == 0:
        return SpanSupportRef(span_idx=0, link_idx= 0)

    if support_idx == 1:
        return SpanSupportRef(span_idx=0, link_idx= 1)

    return SpanSupportRef(span_idx=support_idx - 1, link_idx= 0)

@dataclass(frozen=True)
class BearingSpacingConfig:
    no_of_bearings: int
    spacing: list[Quantity]
    dx: Quantity