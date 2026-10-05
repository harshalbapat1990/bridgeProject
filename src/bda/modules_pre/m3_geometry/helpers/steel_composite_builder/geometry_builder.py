from __future__ import annotations

import uuid
from collections import defaultdict
from copy import deepcopy
from typing import Iterable, Dict, List, cast, Tuple
from uuid import UUID

from pint.registry import Quantity

from bda.application.interfaces.logging import IAppLogger, NullLogger
from bda.domain import AnalyticalMultiModel
from bda.domain.enums import StructuralComponentType, OffsetReference
from bda.domain.models.submodels import Element1D, Node
from bda.domain.models.submodels.element import LinkType, ElementLink
from bda.domain.models.submodels.geometry_group import GeometryGroup
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import (
    ElementOrientation,
    SpacingType, BracingType,
)
from bda.domain.models.submodels.geometry_group_props.shared import GroupPropertiesSegment
from bda.domain.models.submodels.geometry_group_props.substructure_properties import (
    GroupPropertiesSupport,
)
from bda.domain.models.submodels.geometry_group_props.bridge_properties import GroupPropertiesBridge
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import (
    GroupPropertiesGirder,
    GroupPropertiesSpan,
    GroupPropertiesSuperstructure,
    GroupPropertiesEdgeBeam,
    GroupPropertiesDiaphragm,
    DiaphragmBracingEncasedDetails,
    DiaphragmSteelGirderDetails,
    GroupPropertiesTransverseBracing,
    GroupPropertiesBrace,
    GroupPropertiesChord,
    BracingBraceXtypeDetails, GroupPropertiesPlanBracing,
)
import bda.domain.units.registry as units
from bda.domain.models.submodels.material import Material
from bda.domain.models.submodels.section_base import Section, Offset
from bda.domain.models.submodels.sections import SectionStandardSolidRectangle, DimensionsSolidRectangle, \
    SectionCompositeBase, SectionCompositeSteelIAsymmetric, SectionTapered, SectionCompositeSteelISymmetric, \
    DimensionsCompositeSteelISymmetric, DimensionsCompositeSteelIAsymmetric
from bda.domain.units.quantities import Length
from bda.modules_pre.m3_geometry.helpers.tools.geometry_tools import GeometryTools
from bda.modules_pre.m3_geometry.helpers.tools.managers import NodesManager, ElementsManager
from bda.modules_pre.m3_geometry.helpers.tools.models import AppliedVector
from bda.modules_pre.m3_geometry.helpers.tools.models import Point
from bda.modules_pre.m3_geometry.helpers.tools.models import UnitVector
from bda.modules_pre.m3_geometry.helpers.tools.models import Vector
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder import constants as CONSTANTS
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.split_span_into_transverse_elements import (
    DeckStripResult)
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.build_context import (
    GeometrySteelCompositeBuildContext,
    SpanReferenceData,
    DeckSpanData,
)
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.build_steps import (
    CollectGeometryRoot,
    CollectSpans,
    CollectSupportAngles,
    InitializeSpanStates,
    ProcessSpanBracingBreakpointsStep,
    ProcessSpanDeckStripsStep,
    ProcessSpanIncludeSpliceStep,
    ProcessSpanCrackExtentsStep,
    ProcessSpanGirderSegmentsStep,
    ProcessSpanGirderFiniteElementsStep,
    ProcessSpanBracingsStep,
    ProcessSpanDiaphragmsStep,
    ProcessSpanFinalizeGirderSegmentsStep,
    ProcessEntireBridgeDeckStep,
    ResolveBridgeLayout,
    ResolveGrillageType, ProcessSpanPlanBracingsStep,
)
import bda.modules_pre.m3_geometry.helpers.tools.general_tools as tools
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.split_span_into_girder_segments_ import \
    GirderSegmentResult
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.bracing_and_diaphragm_builder import (
    generate_finite_elements_for_bracings_for_span,
    generate_finite_elements_for_diaphragms_for_span, generate_finite_elements_for_plan_bracings_for_span,
)
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.span_pipeline_orchestrators import (
    initialize_span_states,
    resolve_span_bracing_breakpoints,
    resolve_span_deck_strips,
    resolve_span_include_splice,
    resolve_span_crack_extents,
    resolve_span_girder_segments,
    generate_span_girder_finite_elements,
    finalize_span_girder_segments,
    generate_span_bracings,
    generate_span_diaphragms, generate_span_plan_bracings,
)
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.deck_builder_orchestrator import (
    process_deck_for_entire_bridge,
)
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.edge_beam_deck_matching import (
    resolve_connected_deck_segment_for_edge_element,
)


class GeometrySteelCompositeBuilder:
    """Builds steel-composite geometry and keeps a working ModelSpace context."""

    def __init__(
        self,
        amm: AnalyticalMultiModel,
        logger: IAppLogger | None = None,
    ):
        self._tolerance = 0.1 * units.mm
        self._amm = amm
        self._logger = logger or NullLogger()
        self.nodes_manager = NodesManager(self._tolerance)
        self.elements_manager = ElementsManager()
        self._next_element_id = 1

        if self._amm.geometry_group is None:
            raise ValueError(
                "AnalyticalMultiModel has no geometry_group. "
                "Add geometry to AMM before creating GeometrySteelCompositeBuilder."
            )

        self.dummy_section: Section | None = None

        self._weightless_materials: Dict[uuid.UUID, Material] = {}

        self.zero_length = 0.0 * units.m
        self._bridge_direction_vector = Vector.from_unit_vector_and_length(UnitVector(1, 0, 0), 1 * units.m)

    def _build_pipeline_steps(self) -> list:
        return [
            CollectGeometryRoot(),
            CollectSpans(),
            CollectSupportAngles(),
            ResolveBridgeLayout(),
            ResolveGrillageType(),
            InitializeSpanStates(),
            ProcessSpanBracingBreakpointsStep(),
            ProcessSpanDeckStripsStep(),
            ProcessSpanIncludeSpliceStep(),
            ProcessSpanCrackExtentsStep(),
            ProcessSpanGirderSegmentsStep(),
            ProcessSpanGirderFiniteElementsStep(),
            ProcessSpanBracingsStep(),
            ProcessSpanDiaphragmsStep(),
            ProcessSpanPlanBracingsStep(),
            ProcessSpanFinalizeGirderSegmentsStep(),
            ProcessEntireBridgeDeckStep(),
        ]

    def build(self) -> GeometrySteelCompositeBuildContext:
        ctx = GeometrySteelCompositeBuildContext(
            amm=self._amm,
            logger=self._logger,
            nodes_manager=self.nodes_manager,
            elements_manager=self.elements_manager,
            builder=self,
        )

        for step in self._build_pipeline_steps():
            step.execute(ctx)

        self.nodes_manager = ctx.nodes_manager
        return ctx


    def _initialize_span_states(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        initialize_span_states(self, ctx)

    def _resolve_span_bracing_breakpoints(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        resolve_span_bracing_breakpoints(self, ctx)

    def _resolve_span_deck_strips(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        resolve_span_deck_strips(self, ctx)

    def _resolve_span_include_splice(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        resolve_span_include_splice(self, ctx)

    def _resolve_span_crack_extents(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        resolve_span_crack_extents(self, ctx)

    def _resolve_span_girder_segments(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        resolve_span_girder_segments(self, ctx)

    def _generate_span_girder_finite_elements(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        generate_span_girder_finite_elements(self, ctx)

    def _finalize_span_girder_segments(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        finalize_span_girder_segments(self, ctx)

    def _generate_span_bracings(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        generate_span_bracings(self, ctx)

    def _generate_span_diaphragms(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        generate_span_diaphragms(self, ctx)

    def _generate_span_plan_bracings(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        generate_span_plan_bracings(self, ctx)

    def _process_deck_for_entire_bridge(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        process_deck_for_entire_bridge(self, ctx)

    def _generate_finite_elements_for_bracings_for_span(
        self,
        span: GeometryGroup,
    ) -> None:
        generate_finite_elements_for_bracings_for_span(self, span)

    def _generate_finite_elements_for_diaphragms_for_span(self, span: GeometryGroup) -> None:
        generate_finite_elements_for_diaphragms_for_span(self, span)

    def _generate_finite_elements_for_plan_bracings_for_span(
            self,
            span: GeometryGroup,
            reference_data: SpanReferenceData) -> None:
        generate_finite_elements_for_plan_bracings_for_span(self, span, reference_data)

    def _model_single_bracing(
        self,
        bracing_group: GeometryGroup,
        reference_element: Element1D,
        bracing_index: int,
    ) -> None:
        bracing_props = self._require_transverse_bracing_properties(bracing_group)
        brace_groups = self._collect_brace_groups(bracing_group)
        chord_groups = self._collect_chord_groups(bracing_group)

        if not brace_groups and not chord_groups:
            self._logger.warning(
                "Bracing group has no BRACE/CHORD nested groups | group=%s | index=%s",
                bracing_group.name,
                bracing_index,
            )
            return

        ref_start = reference_element.node_start
        ref_end = reference_element.node_end
        ref_vector = Vector.from_points(
            Point(ref_start.X, ref_start.Y, ref_start.Z),
            Point(ref_end.X, ref_end.Y, ref_end.Z),
        )
        ref_unit = ref_vector.normalize()

        projected_chord_target: tuple[GeometryGroup, Node] | None = None

        for brace_group in brace_groups:
            brace_props = self._require_brace_properties(brace_group)
            left_brace_nodes = self._resolve_bracing_member_nodes(
                reference_start=ref_start,
                reference_end=ref_end,
                reference_unit=ref_unit,
                left_horizontal_offset=bracing_props.bracing_details.horizontal_offset_at_left,
                right_horizontal_offset=(
                    bracing_props.bracing_details.horizontal_offset_at_right
                    if isinstance(brace_props.geometry_details, BracingBraceXtypeDetails)
                    else brace_props.geometry_details.horizontal_offset_left_brace),
                left_vertical_offset=brace_props.geometry_details.vertical_offset_left_top,
                right_vertical_offset=brace_props.geometry_details.vertical_offset_right_bottom
            )
            if self._are_same_node(left_brace_nodes[0], left_brace_nodes[1]):
                self._logger.warning(
                    "[GeometryBuilder] skipping degenerate left brace with identical nodes"
                    " | bracing_group=%s | brace_group=%s | bracing_index=%s",
                    bracing_group.name,
                    brace_group.name,
                    bracing_index,
                )
                continue
            right_brace_nodes = self._resolve_bracing_member_nodes(
                reference_start=ref_start,
                reference_end=ref_end,
                reference_unit=ref_unit,
                left_horizontal_offset=(
                    bracing_props.bracing_details.horizontal_offset_at_left
                    if isinstance(brace_props.geometry_details, BracingBraceXtypeDetails)
                    else brace_props.geometry_details.horizontal_offset_right_brace),
                right_horizontal_offset=bracing_props.bracing_details.horizontal_offset_at_right,
                left_vertical_offset=brace_props.geometry_details.vertical_offset_left_bottom,
                right_vertical_offset=brace_props.geometry_details.vertical_offset_right_top,
            )
            if self._are_same_node(right_brace_nodes[0], right_brace_nodes[1]):
                self._logger.warning(
                    "[GeometryBuilder] skipping degenerate right brace with identical nodes"
                    " | bracing_group=%s | brace_group=%s | bracing_index=%s",
                    bracing_group.name,
                    brace_group.name,
                    bracing_index,
                )
                continue
            left_brace_element = self.elements_manager.get_or_create_beam(left_brace_nodes[0], left_brace_nodes[1])
            right_brace_element = self.elements_manager.get_or_create_beam(right_brace_nodes[0], right_brace_nodes[1])
            brace_group.analytical_typology.add_element(left_brace_element)
            brace_group.analytical_typology.add_element(right_brace_element)

            if brace_props.geometry_details.bracing_type == BracingType.X_TYPE:
                brace_group.analytical_typology.add_links(self._create_member_end_links(reference_element, left_brace_nodes))
                brace_group.analytical_typology.add_links(self._create_member_end_links(reference_element, right_brace_nodes))
            else:
                # For K-type, avoid rigid links at left-end/right-start nodes.
                if not self._are_same_node(reference_element.node_start, left_brace_nodes[0]):
                    brace_group.analytical_typology.add_link(
                        self.elements_manager.get_or_create_link(
                            reference_element.node_start,
                            left_brace_nodes[0],
                            LinkType.RIGID,
                        )
                    )
                if not self._are_same_node(reference_element.node_end, right_brace_nodes[1]):
                    brace_group.analytical_typology.add_link(
                        self.elements_manager.get_or_create_link(
                            reference_element.node_end,
                            right_brace_nodes[1],
                            LinkType.RIGID,
                        )
                    )

            if brace_props.geometry_details.bracing_type == BracingType.K_TYPE:
                midpoint_node = self.nodes_manager.get_or_create_node(
                    cast(Quantity, (left_brace_nodes[1].X + right_brace_nodes[0].X) / 2),
                    cast(Quantity, (left_brace_nodes[1].Y + right_brace_nodes[0].Y) / 2),
                    cast(Quantity, (left_brace_nodes[1].Z + right_brace_nodes[0].Z) / 2),
                )

                projected_chord_node = self._project_midpoint_to_first_lower_chord(
                    midpoint_node=midpoint_node,
                    chord_groups=chord_groups,
                    bracing_props=bracing_props,
                    reference_start=ref_start,
                    reference_end=ref_end,
                    reference_unit=ref_unit,
                )
                if projected_chord_node is None:
                    self._logger.warning(
                        "[GeometryBuilder] K-type brace midpoint projection failed | bracing_group=%s | brace_group=%s | bracing_index=%s",
                        bracing_group.name,
                        brace_group.name,
                        bracing_index,
                    )
                else:
                    projected_chord_target = projected_chord_node

                    # Brace ends are tied to the node that lies on the projected chord.
                    projected_node = projected_chord_node[1]
                    if not self._are_same_node(left_brace_nodes[1], projected_node):
                        brace_group.analytical_typology.add_link(
                            self.elements_manager.get_or_create_link(left_brace_nodes[1], projected_node, LinkType.RIGID)
                        )
                    if not self._are_same_node(right_brace_nodes[0], projected_node):
                        brace_group.analytical_typology.add_link(
                            self.elements_manager.get_or_create_link(right_brace_nodes[0], projected_node, LinkType.RIGID)
                        )

        for chord_group in chord_groups:
            chord_props = self._require_chord_properties(chord_group)
            chord_nodes = self._resolve_bracing_member_nodes(
                reference_start=ref_start,
                reference_end=ref_end,
                reference_unit=ref_unit,
                left_horizontal_offset=bracing_props.bracing_details.horizontal_offset_at_left,
                right_horizontal_offset=bracing_props.bracing_details.horizontal_offset_at_right,
                left_vertical_offset=chord_props.vertical_offset_at_left,
                right_vertical_offset=chord_props.vertical_offset_at_right,
            )

            if self._are_same_node(chord_nodes[0], chord_nodes[1]):
                self._logger.warning(
                    "[GeometryBuilder] skipping degenerate chord with identical nodes | bracing_group=%s | chord_group=%s | bracing_index=%s",
                    bracing_group.name,
                    chord_group.name,
                    bracing_index,
                )
                continue

            if projected_chord_target is not None and projected_chord_target[0].guid == chord_group.guid:
                projected_node = projected_chord_target[1]

                # For K-type, split the projected chord into two finite elements.
                if not self._are_same_node(chord_nodes[0], projected_node):
                    chord_group.analytical_typology.add_element(
                        self.elements_manager.get_or_create_beam(chord_nodes[0], projected_node)
                    )
                if not self._are_same_node(projected_node, chord_nodes[1]):
                    chord_group.analytical_typology.add_element(
                        self.elements_manager.get_or_create_beam(projected_node, chord_nodes[1])
                    )
            else:
                chord_element = self.elements_manager.get_or_create_beam(chord_nodes[0], chord_nodes[1])
                chord_group.analytical_typology.add_element(chord_element)

            chord_group.analytical_typology.add_links(
                self._create_member_end_links(reference_element, chord_nodes))

    def _collect_brace_groups(self, bracing_group: GeometryGroup) -> Iterable[GeometryGroup]:
        return [
            g
            for g in bracing_group.get_groups_by_component_type(StructuralComponentType.BRACE)
            if isinstance(g.properties, GroupPropertiesBrace)
        ]

    def _collect_chord_groups(self, bracing_group: GeometryGroup) -> Iterable[GeometryGroup]:
        return [
            g
            for g in bracing_group.get_groups_by_component_type(StructuralComponentType.CHORD)
            if isinstance(g.properties, GroupPropertiesChord)
        ]

    def _require_brace_properties(self, brace_group: GeometryGroup) -> GroupPropertiesBrace:
        if not isinstance(brace_group, GeometryGroup):
            raise TypeError("Brace group should be a GeometryGroup object.")
        if brace_group.component_type != StructuralComponentType.BRACE:
            raise TypeError(f"Group {brace_group.name} should have BRACE component type.")
        if not isinstance(brace_group.properties, GroupPropertiesBrace):
            raise TypeError(f"Brace group {brace_group.name} should have GroupPropertiesBrace properties.")
        return brace_group.properties

    def _require_chord_properties(self, chord_group: GeometryGroup) -> GroupPropertiesChord:
        if not isinstance(chord_group, GeometryGroup):
            raise TypeError("Chord group should be a GeometryGroup object.")
        if chord_group.component_type != StructuralComponentType.CHORD:
            raise TypeError(f"Group {chord_group.name} should have CHORD component type.")
        if not isinstance(chord_group.properties, GroupPropertiesChord):
            raise TypeError(f"Chord group {chord_group.name} should have GroupPropertiesChord properties.")
        return chord_group.properties

    def _resolve_bracing_member_nodes(
        self,
        reference_start: Node,
        reference_end: Node,
        reference_unit: UnitVector,
        left_horizontal_offset: Quantity,
        right_horizontal_offset: Quantity,
        left_vertical_offset: Quantity,
        right_vertical_offset: Quantity,
    ) -> tuple[Node, Node]:
        """Resolve start/end FE nodes of a single brace/chord member.

        The returned nodes are *member nodes* (not the bracing reference nodes).
        They represent actual finite-element end nodes for a brace/chord nested
        inside one transverse-bracing location.

        Node positions are derived from the bracing reference element by:
        1) moving from each reference end along the reference direction in XY
           using transverse-bracing/chord/brace horizontal offsets,
        2) applying vertical Z offsets from brace/chord properties,
        3) resolving/reusing final nodes through ``NodesManager`` tolerance.

        Returns
        -------
        tuple[Node, Node]
            ``(node_start, node_end)`` for the finite member to be created.
        """
        start_shift = cast(Quantity, left_horizontal_offset)
        end_shift = cast(Quantity, right_horizontal_offset)

        start_point = Point(reference_start.X, reference_start.Y, reference_start.Z).translate(
            Vector.from_unit_vector_and_length(reference_unit, start_shift)
        )
        end_point = Point(reference_end.X, reference_end.Y, reference_end.Z).translate(
            Vector.from_unit_vector_and_length(reference_unit, -end_shift)
        )

        start_point = start_point.translate(Vector(self.zero_length, self.zero_length, -left_vertical_offset))
        end_point = end_point.translate(Vector(self.zero_length, self.zero_length, -right_vertical_offset))
        return (
            self.nodes_manager.get_or_create_node(start_point.x, start_point.y, start_point.z),
            self.nodes_manager.get_or_create_node(end_point.x, end_point.y, end_point.z),
        )

    def _create_member_end_links(self, reference_element: Element1D, member_nodes: tuple[Node, Node]) -> list[ElementLink]:
        return [
            self.elements_manager.get_or_create_link(reference_element.node_start, member_nodes[0], LinkType.RIGID),
            self.elements_manager.get_or_create_link(reference_element.node_end, member_nodes[1], LinkType.RIGID),
        ]

    def _project_midpoint_to_first_lower_chord(
        self,
        midpoint_node: Node,
        chord_groups: Iterable[GeometryGroup],
        bracing_props: GroupPropertiesTransverseBracing,
        reference_start: Node,
        reference_end: Node,
        reference_unit: UnitVector,
    ) -> tuple[GeometryGroup, Node] | None:
        vertical_projection_line = AppliedVector(
            start_point=Point(midpoint_node.X, midpoint_node.Y, midpoint_node.Z),
            vector=Vector(self.zero_length, self.zero_length, -1 * units.m),
        )

        for chord_group in chord_groups:
            chord_props = self._require_chord_properties(chord_group)
            chord_nodes = self._resolve_bracing_member_nodes(
                reference_start=reference_start,
                reference_end=reference_end,
                reference_unit=reference_unit,
                left_horizontal_offset=bracing_props.bracing_details.horizontal_offset_at_left,
                right_horizontal_offset=bracing_props.bracing_details.horizontal_offset_at_right,
                left_vertical_offset=chord_props.vertical_offset_at_left,
                right_vertical_offset=chord_props.vertical_offset_at_right,
            )
            chord_avg_z = cast(Quantity, (chord_nodes[0].Z + chord_nodes[1].Z) / 2)
            if chord_avg_z >= midpoint_node.Z:
                continue

            chord_segment = AppliedVector.from_points(
                Point(chord_nodes[0].X, chord_nodes[0].Y, chord_nodes[0].Z),
                Point(chord_nodes[1].X, chord_nodes[1].Y, chord_nodes[1].Z),
            )
            projected_point = GeometryTools.project_node_on_segment(
                line=vertical_projection_line,
                segment=chord_segment,
                tol=self._tolerance,
            )
            if projected_point is None:
                continue

            projected_node = self.nodes_manager.get_or_create_node(projected_point.x, projected_point.y, projected_point.z)
            return chord_group, projected_node

        return None

    def _are_same_node(self, node_a: Node, node_b: Node) -> bool:
        return node_a.node_id == node_b.node_id

    def _generate_finite_elements_for_edge_beams_for_span(
        self,
        span_data: DeckSpanData,
    ) -> None:
        deck_group = self._require_deck_group_for_span(span_data.span)
        deck_segments = [
            segment
            for segment in deck_group.get_groups_by_component_type(StructuralComponentType.SEGMENT)
            if isinstance(segment.properties, GroupPropertiesSegment)
        ]
        if not deck_segments:
            return

        edge_beam_groups = [
            group
            for group in self._collect_or_create_edge_beams_for_span(span_data.span)
            if isinstance(group.properties, GroupPropertiesEdgeBeam)
        ]
        edge_beam_group_by_index = {
            group.properties.edge_beam_index: group
            for group in edge_beam_groups
        }

        deck_vertical_offset = cast(
            Quantity,
            self._require_deck_base_section(deck_group).dimensions.height_h / 2,
        )

        for edge_beam_index, edge_reference_element in span_data.span_reference_data.edge_beam_ref_elements.items():
            edge_beam_group = edge_beam_group_by_index.get(edge_beam_index)
            if edge_beam_group is None:
                continue

            edge_reference_segment = tools.element_to_applied_vector(edge_reference_element)
            edge_start_node = self.nodes_manager.get_or_create_node(
                edge_reference_element.node_start.X,
                edge_reference_element.node_start.Y,
                deck_vertical_offset,
            )
            edge_end_node = self.nodes_manager.get_or_create_node(
                edge_reference_element.node_end.X,
                edge_reference_element.node_end.Y,
                deck_vertical_offset,
            )

            edge_nodes_by_id: Dict[int, Node] = {
                edge_start_node.node_id: edge_start_node,
                edge_end_node.node_id: edge_end_node,
            }

            for strip in span_data.transverse_deck_strips:
                intersection = GeometryTools.project_node_on_segment(
                    line=strip.strip_vector,
                    segment=edge_reference_segment,
                    tol=self._tolerance,
                )
                if intersection is None:
                    continue

                edge_node = self.nodes_manager.get_or_create_node(
                    intersection.x,
                    intersection.y,
                    deck_vertical_offset,
                )
                edge_nodes_by_id[edge_node.node_id] = edge_node

            edge_axis = AppliedVector.from_points(
                Point(edge_start_node.X, edge_start_node.Y, edge_start_node.Z),
                Point(edge_end_node.X, edge_end_node.Y, edge_end_node.Z),
            )

            def _projection_along_edge(node: Node) -> float:
                delta = Vector.from_points(
                    edge_axis.start_point,
                    Point(node.X, node.Y, node.Z),
                )
                return (
                    delta.x.to_base_units().magnitude * edge_axis.vector.x.to_base_units().magnitude
                    + delta.y.to_base_units().magnitude * edge_axis.vector.y.to_base_units().magnitude
                    + delta.z.to_base_units().magnitude * edge_axis.vector.z.to_base_units().magnitude
                )

            ordered_nodes = sorted(edge_nodes_by_id.values(), key=_projection_along_edge)

            edge_elements: List[Element1D] = []
            for i in range(len(ordered_nodes) - 1):
                if self._are_same_node(ordered_nodes[i], ordered_nodes[i + 1]):
                    continue
                edge_elements.append(
                    self.elements_manager.get_or_create_beam(ordered_nodes[i], ordered_nodes[i + 1])
                )

            if not edge_elements:
                continue

            existing_edge_segments = [
                segment
                for segment in edge_beam_group.get_groups_by_component_type(StructuralComponentType.SEGMENT)
                if isinstance(segment.properties, GroupPropertiesSegment)
            ]
            edge_segment_groups_by_key: Dict[int, GeometryGroup] = {
                segment.properties.construction_sequence_stage_index: segment
                for segment in existing_edge_segments
            }

            for edge_element in edge_elements:
                target_deck_segment = resolve_connected_deck_segment_for_edge_element(self, edge_element, deck_segments)
                target_props = cast(GroupPropertiesSegment, target_deck_segment.properties)
                segment_key = target_props.construction_sequence_stage_index

                edge_segment_group = edge_segment_groups_by_key.get(segment_key)
                if edge_segment_group is None:
                    edge_segment_group = GeometryGroup(
                        component_type=StructuralComponentType.SEGMENT,
                        name=(
                            f"Span_{span_data.span_props.span_index}_EdgeBeam_{edge_beam_index}_"
                            f"Segment_{target_props.construction_sequence_stage_index}_"
                            f"PouringStage_{target_props.construction_sequence_stage_index}"
                        ),
                        properties=GroupPropertiesSegment(
                            segment_index=target_props.construction_sequence_stage_index,
                            construction_sequence_stage_index=target_props.construction_sequence_stage_index,
                        ),
                    )
                    edge_segment_group.material = target_deck_segment.get_material()
                    # Keep section inheritance from edge-beam/parent group.
                    edge_beam_group.add_nested_group(edge_segment_group)
                    edge_segment_groups_by_key[segment_key] = edge_segment_group

                edge_segment_group.analytical_typology.add_element(edge_element)

    def _generate_finite_elements_for_edge_beams_for_bridge(
        self,
        span_deck_data: Iterable[DeckSpanData],
        bridge_edge_beam_segments: Dict[int, AppliedVector],
    ) -> None:
        span_deck_data = sorted(
            list(span_deck_data),
            key=lambda d: d.span_props.span_index,
        )
        if not span_deck_data:
            return

        first_deck_group = self._require_deck_group_for_span(span_deck_data[0].span)
        deck_vertical_offset = cast(
            Quantity,
            self._require_deck_base_section(first_deck_group).dimensions.height_h / 2,
        )

        all_transverse_deck_strips = [
            strip
            for data in span_deck_data
            for strip in data.transverse_deck_strips
        ]

        ordered_deck_segments: List[GeometryGroup] = []
        edge_beam_group_by_span_and_index: Dict[Tuple[int, int], GeometryGroup] = {}

        for data in span_deck_data:
            span_index = data.span_props.span_index

            deck_group = self._require_deck_group_for_span(data.span)
            deck_segments = [
                segment
                for segment in deck_group.get_groups_by_component_type(StructuralComponentType.SEGMENT)
                if isinstance(segment.properties, GroupPropertiesSegment)
            ]
            deck_segments.sort(key=lambda segment: segment.properties.segment_index)
            ordered_deck_segments.extend(deck_segments)

            edge_beam_groups = [
                group
                for group in self._collect_or_create_edge_beams_for_span(data.span)
                if isinstance(group.properties, GroupPropertiesEdgeBeam)
            ]
            for edge_group in edge_beam_groups:
                edge_beam_group_by_span_and_index[(span_index, edge_group.properties.edge_beam_index)] = edge_group

        if not ordered_deck_segments:
            return

        for edge_beam_index, bridge_edge_beam_segment in sorted(bridge_edge_beam_segments.items()):
            edge_start_node = self.nodes_manager.get_or_create_node(
                bridge_edge_beam_segment.start_point.x,
                bridge_edge_beam_segment.start_point.y,
                deck_vertical_offset,
            )
            edge_end_node = self.nodes_manager.get_or_create_node(
                cast(Quantity, bridge_edge_beam_segment.start_point.x + bridge_edge_beam_segment.vector.x),
                cast(Quantity, bridge_edge_beam_segment.start_point.y + bridge_edge_beam_segment.vector.y),
                deck_vertical_offset,
            )

            edge_nodes_by_id: Dict[int, Node] = {
                edge_start_node.node_id: edge_start_node,
                edge_end_node.node_id: edge_end_node,
            }

            for strip in all_transverse_deck_strips:
                intersection = GeometryTools.project_node_on_segment(
                    line=strip.strip_vector,
                    segment=bridge_edge_beam_segment,
                    tol=self._tolerance,
                )
                if intersection is None:
                    continue

                edge_node = self.nodes_manager.get_or_create_node(
                    intersection.x,
                    intersection.y,
                    deck_vertical_offset,
                )
                edge_nodes_by_id[edge_node.node_id] = edge_node

            edge_axis = AppliedVector.from_points(
                Point(edge_start_node.X, edge_start_node.Y, edge_start_node.Z),
                Point(edge_end_node.X, edge_end_node.Y, edge_end_node.Z),
            )

            def _projection_along_edge(node: Node) -> float:
                delta = Vector.from_points(
                    edge_axis.start_point,
                    Point(node.X, node.Y, node.Z),
                )
                return (
                    delta.x.to_base_units().magnitude * edge_axis.vector.x.to_base_units().magnitude
                    + delta.y.to_base_units().magnitude * edge_axis.vector.y.to_base_units().magnitude
                    + delta.z.to_base_units().magnitude * edge_axis.vector.z.to_base_units().magnitude
                )

            ordered_nodes = sorted(edge_nodes_by_id.values(), key=_projection_along_edge)

            edge_elements: List[Element1D] = []
            for i in range(len(ordered_nodes) - 1):
                if self._are_same_node(ordered_nodes[i], ordered_nodes[i + 1]):
                    continue
                edge_elements.append(
                    self.elements_manager.get_or_create_beam(ordered_nodes[i], ordered_nodes[i + 1])
                )

            if not edge_elements:
                continue

            edge_segment_groups_by_span_and_edge: Dict[Tuple[int, int], Dict[int, GeometryGroup]] = {}

            for edge_element in edge_elements:
                target_deck_segment = resolve_connected_deck_segment_for_edge_element(
                    self,
                    edge_element,
                    ordered_deck_segments,
                )
                target_props = cast(GroupPropertiesSegment, target_deck_segment.properties)

                target_span = target_deck_segment.get_parent_group_by_component_type(StructuralComponentType.SPAN)
                if target_span is None:
                    continue
                target_span_props = self._require_span_properties(target_span)
                target_span_index = target_span_props.span_index

                edge_beam_group = edge_beam_group_by_span_and_index.get((target_span_index, edge_beam_index))
                if edge_beam_group is None:
                    continue

                cache_key = (target_span_index, edge_beam_index)
                edge_segment_groups_by_key = edge_segment_groups_by_span_and_edge.get(cache_key)
                if edge_segment_groups_by_key is None:
                    existing_edge_segments = [
                        segment
                        for segment in edge_beam_group.get_groups_by_component_type(StructuralComponentType.SEGMENT)
                        if isinstance(segment.properties, GroupPropertiesSegment)
                    ]
                    edge_segment_groups_by_key = {
                        segment.properties.construction_sequence_stage_index: segment
                        for segment in existing_edge_segments
                    }
                    edge_segment_groups_by_span_and_edge[cache_key] = edge_segment_groups_by_key

                segment_key = target_props.construction_sequence_stage_index

                edge_segment_group = edge_segment_groups_by_key.get(segment_key)
                if edge_segment_group is None:
                    edge_segment_group = GeometryGroup(
                        component_type=StructuralComponentType.SEGMENT,
                        name=(
                            f"Span_{target_span_index}_EdgeBeam_{edge_beam_index}_"
                            f"Segment_{target_props.construction_sequence_stage_index}_"
                            f"PouringStage_{target_props.construction_sequence_stage_index}"
                        ),
                        properties=GroupPropertiesSegment(
                            segment_index=target_props.construction_sequence_stage_index,
                            construction_sequence_stage_index=target_props.construction_sequence_stage_index,
                        ),
                    )
                    edge_segment_group.material = target_deck_segment.get_material()
                    edge_beam_group.add_nested_group(edge_segment_group)
                    edge_segment_groups_by_key[segment_key] = edge_segment_group

                edge_segment_group.analytical_typology.add_element(edge_element)

    def _build_span_reference_data(
        self,
        span: GeometryGroup,
        span_props: GroupPropertiesSpan,
        span_offset: Quantity,
        support_angles: Dict[int, Quantity],
        grillage_type: ElementOrientation,
        y_offsets_girders: Dict[int, Quantity],
        y_offsets_edge_beams: Dict[int, Quantity],
    ) -> SpanReferenceData:
        span_start_point = Point(span_offset, self.zero_length)
        support_i_vector, support_j_vector = self._resolve_support_vectors_for_span(
            span,
            span_start_point,
            span_props.span_length,
            support_angles,
            grillage_type,
        )

        girders = self._collect_girders_for_span(span)
        edge_beams = self._collect_or_create_edge_beams_for_span(span)

        self._logger.debug(
            "[GeometryBuilder] generate reference girder elements for span | span=%s | span_index=%s",
            span.name,
            span_props.span_index,
        )

        girder_ref_elements: Dict[int, Element1D] = self._generate_reference_longitudinal_elements_for_span(
            girders,
            y_offsets_girders,
            support_i_vector,
            support_j_vector,
        )

        edge_beam_ref_elements: Dict[int, Element1D] = self._generate_reference_longitudinal_elements_for_span(
            edge_beams,
            y_offsets_edge_beams,
            support_i_vector,
            support_j_vector
        )

        transverse_bracings: Dict[Tuple[int, int], List[Element1D]] = (
            self._generate_reference_elements_for_transverse_bracings_for_span(
                bracing_groups=self._collect_bracings_for_span(span),
                girders_ref_elements=girder_ref_elements
            ))

        diaphragms: Dict[int, List[Element1D]] = self._generate_reference_elements_for_diaphragms_for_span(
            diaphragm_groups=self._collect_diaphragms_for_span(span),
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

    def _collect_spans(self, root_group: GeometryGroup) -> Iterable[GeometryGroup]:
        self._logger.debug(
            "[GeometryBuilder] collect spans | root_group=%s",
            root_group.name,
        )
        spans = [
            s
            for s in root_group.iter_groups(
                lambda g: g.component_type == StructuralComponentType.SPAN
                and isinstance(g.properties, GroupPropertiesSpan)
            )
        ]
        spans.sort(key=lambda s: s.properties.span_index)
        return spans

    def _collect_girders_for_span(self, span: GeometryGroup) -> Iterable[GeometryGroup]:
        self._logger.debug(
            "[GeometryBuilder] collect girders for span | span=%s | span_index=%s",
            span.name,
            span.properties.span_index if isinstance(span.properties, GroupPropertiesSpan) else "unknown",
        )
        girders = [
            g
            for g in span.iter_groups()
            if g.component_type == StructuralComponentType.GIRDER
            and isinstance(g.properties, GroupPropertiesGirder)
        ]
        girders.sort(key=lambda g: g.properties.girder_index)
        return girders

    def _collect_bracings_for_span(self, span: GeometryGroup) -> Iterable[GeometryGroup]:
        self._logger.debug(
            "[GeometryBuilder] collect transverse bracings for span | span=%s | span_index=%s",
            span.name,
            span.properties.span_index if isinstance(span.properties, GroupPropertiesSpan) else "unknown",
        )
        return [
            b
            for b in span.get_groups_by_component_type(StructuralComponentType.TRANSVERSE_BRACING)
            if isinstance(b.properties, GroupPropertiesTransverseBracing)
        ]

    def _collect_transverse_bracings_for_entire_bridge(self) -> Iterable[GeometryGroup]:
        self._logger.debug(
            "[GeometryBuilder] collect all transverse bracings for entire bridge",
        )
        return [
            tb
            for tb in self._amm.geometry_group.get_groups_by_component_type(StructuralComponentType.TRANSVERSE_BRACING)
            if isinstance(tb.properties, GroupPropertiesTransverseBracing)
        ]

    def _collect_plan_bracings_for_span(self, span: GeometryGroup) -> Iterable[GeometryGroup]:
        self._logger.debug(
            "[GeometryBuilder] collect transverse bracings for span | span=%s | span_index=%s",
            span.name,
            span.properties.span_index if isinstance(span.properties, GroupPropertiesSpan) else "unknown",
        )
        return [
            pb
            for pb in span.get_groups_by_component_type(StructuralComponentType.PLAN_BRACING)
            if isinstance(pb.properties, GroupPropertiesPlanBracing)
        ]

    def _collect_diaphragms_for_span(self, span: GeometryGroup) -> Iterable[GeometryGroup]:
        self._logger.debug(
            "[GeometryBuilder] collect diaphragms for span | span=%s | span_index=%s",
            span.name,
            span.properties.span_index if isinstance(span.properties, GroupPropertiesSpan) else "unknown",
        )
        diaphragms = [
            d
            for d in span.get_groups_by_component_type(StructuralComponentType.DIAPHRAGM)
            if isinstance(d.properties, GroupPropertiesDiaphragm)
        ]
        diaphragms.sort(key=lambda d: d.properties.support_index)
        return diaphragms

    def _require_longitudinal_member_for_span(self, span: GeometryGroup) -> GeometryGroup:
        longitudinal_members = span.get_groups_by_component_type(StructuralComponentType.LONGITUDINAL_MEMBERS)
        if not longitudinal_members:
            raise ValueError(f"Longitudinal members under span {span.name} not found.")
        return longitudinal_members[0]

    def _collect_or_create_edge_beams_for_span(self, span: GeometryGroup) -> Iterable[GeometryGroup]:
        self._logger.debug(
            "[GeometryBuilder] collect edge beams for span | span=%s | span_index=%s",
            span.name,
            span.properties.span_index if isinstance(span.properties, GroupPropertiesSpan) else "unknown",
        )

        edge_beams = span.get_groups_by_component_type(StructuralComponentType.EDGE_BEAM)
        deck = next(iter(span.get_groups_by_component_type(StructuralComponentType.DECK_SLAB)))

        longitudinal_member = self._require_longitudinal_member_for_span(span)

        if len(edge_beams) == 0:
            self._logger.debug(
                "[GeometryBuilder] no edge beams found for span | span=%s | creating default edge beams",
                span.name,
            )
            for i in range(2):
                edge_beam = GeometryGroup(
                        component_type=StructuralComponentType.EDGE_BEAM,
                        name=f"Edge Beam {i + 1}",
                        properties=GroupPropertiesEdgeBeam(
                            edge_beam_index = i
                        )
                    )
                edge_beam.section = self._require_dummy_section()
                edge_beam.material = self.require_weightless_material(deck.get_material())
                edge_beam.section.set_material_main(edge_beam.material)
                # this material needs to be replaced later with weightless version
                longitudinal_member.add_nested_group(edge_beam)
                edge_beams.append(edge_beam)
            return edge_beams

        edge_beams.sort(key=lambda g: g.properties.edge_beam_index)
        return edge_beams

    def _collect_support_angles(self, root_group: GeometryGroup) -> dict[int, Quantity]:
        self._logger.debug(
            "[GeometryBuilder] collect support angles | root_group=%s",
            root_group.name,
        )
        supports = [
            s
            for s in root_group.iter_groups(
                lambda g: g.component_type == StructuralComponentType.SUPPORT
                and isinstance(g.properties, GroupPropertiesSupport)
            )
        ]
        supports.sort(key=lambda s: s.properties.support_index)

        by_index: dict[int, Quantity] = {}
        for support in supports:
            support_index = support.properties.support_index
            if support_index in by_index:
                raise ValueError(f"Duplicated support index {support_index} found.")
            by_index[support_index] = support.properties.skew_angle

        return by_index

    def _require_support_angle(self, support_angles: dict[int, Quantity], support_index: int) -> Quantity:
        self._logger.debug(
            "[GeometryBuilder] require support angle | support_index=%s",
            support_index,
        )
        angle = support_angles.get(support_index)
        if angle is None:
            raise ValueError(f"Support with index {support_index} has not been found.")
        return angle

    def _resolve_support_vectors_for_span(
        self,
        span: GeometryGroup,
        span_start_point: Point,
        span_length: Quantity,
        support_angles: dict[int, Quantity],
        grillage_type: ElementOrientation,
    ) -> tuple[AppliedVector, AppliedVector]:
        span_props = self._require_span_properties(span)
        self._logger.debug(
            "[GeometryBuilder] resolve support vectors for span | span=%s | span_index=%s | span_length=%s | grillage_type=%s",
            span.name,
            span_props.span_index,
            span_length,
            grillage_type,
        )
        span_index = span_props.span_index
        n_i = span_start_point
        n_j = Point(n_i.x + span_length, self.zero_length)

        sup_i_angle = self._require_support_angle(support_angles, span_index)
        sup_j_angle = self._require_support_angle(support_angles, span_index + 1)

        if grillage_type == ElementOrientation.SKEWED and sup_i_angle != sup_j_angle:
            self._logger.warning(
                "Skew angle of supports %d and %d differs for skewed grillage. "
                "Using the start support angle %s for both.",
                span_index,
                span_index + 1,
                sup_i_angle,
            )
            sup_j_angle = sup_i_angle

        return AppliedVector(n_i, Vector.from_angle(sup_i_angle)), AppliedVector(n_j, Vector.from_angle(sup_j_angle))

    def _resolve_girder_yoffsets(self, root_group: GeometryGroup) -> dict[int, Quantity]:
        self._logger.debug(
            "[GeometryBuilder] resolve girder y-offsets | root_group=%s",
            root_group.name,
        )
        superstructure_props = self._require_superstructure_properties(root_group)

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

        y_offsets: dict[int, Quantity] = {}
        for i in range(no_of_girders):
            y_offsets[i] = cast(Quantity, total_deck_width / 2 - left_cantilever - sum(spacing[:i]))

        return y_offsets

    def _resolve_edge_beams_yoffsets(self, root_group: GeometryGroup) -> dict[int, Quantity]:
        self._logger.debug(
            "[GeometryBuilder] resolve edge beam y-offsets | root_group=%s",
            root_group.name,
        )
        superstructure_props = self._require_superstructure_properties(root_group)

        total_deck_width = superstructure_props.total_deck_width

        y_offsets: dict[int, Quantity] = {
            0: cast(Quantity, total_deck_width / 2),
            1: cast(Quantity, -total_deck_width / 2),
        }

        return y_offsets

    def _generate_reference_longitudinal_elements_for_span(
        self,
        elements: Iterable[GeometryGroup],
        y_offsets_elements: dict[int, Quantity],
        support_i_vector: AppliedVector,
        support_j_vector: AppliedVector,
    ) -> Dict[int, Element1D]:
        """
        Create one reference element for each element in the current span.

        For each element, the method builds a longitudinal element line from the
        configured Y-offset, intersects it with start/end support lines, creates
        or reuses nodes at those intersections, and appends an ``Element1D`` to
        ``element.reference_elements``.

        Parameters
        ----------
        elements : Iterable[GeometryGroup]
            Groups of edge beams or girders in the span.
        y_offsets_elements : dict[int, Quantity]
            Mapping ``element_index -> transverse offset`` used to position each
            element line.
        support_i_vector : AppliedVector
            Support line at the start side of the span.
        support_j_vector : AppliedVector
            Support line at the end side of the span.

        Returns
        -------
        Dict[int, List[Quantity]]
            Mapping ``element_index -> [x_start, x_end]`` of calculated
            intersection coordinates for each generated reference element.

        Raises
        ------
        ValueError
            If an element offset is missing or a support intersection cannot be
            resolved.
        """
        ref_elements: Dict[int, Element1D] = {}

        elements = list(elements)
        self._logger.debug(
            "[GeometryBuilder] generate reference elements for provided groups | girder_indices=%s | support_i=%s | support_j=%s",
            [
                girder.properties.girder_index
                for girder in elements
                if isinstance(girder.properties, GroupPropertiesGirder)
            ],
            support_i_vector,
            support_j_vector,
        )

        for element_group in elements:
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
                    self.zero_length,
                    y_offsets_elements[element_index],
                    self.zero_length,
                ),
                vector=self._bridge_direction_vector,
            )

            start_point = GeometryTools.intersect_lines(
                element_vector,
                support_i_vector,
                self._tolerance,
            )
            if start_point is None:
                raise ValueError(f"Could not resolve start intersection for element index {element_index}.")
            node_i = self.nodes_manager.get_or_create_node(start_point.x, start_point.y, start_point.z)

            end_point = GeometryTools.intersect_lines(
                element_vector,
                support_j_vector,
                self._tolerance,
            )
            if end_point is None:
                raise ValueError(f"Could not resolve end intersection for element index {element_index}.")
            node_j = self.nodes_manager.get_or_create_node(end_point.x, end_point.y, end_point.z)

            element = self.elements_manager.get_or_create_beam(node_i, node_j)
            element_group.add_reference_element(element)
            ref_elements[element_index] = element
        return ref_elements

    def _generate_reference_elements_for_transverse_bracings_for_span(
        self,
        bracing_groups: Iterable[GeometryGroup],
        girders_ref_elements: Dict[int, Element1D],
    ) -> Dict[Tuple[int, int], List[Element1D]]:
        """ """
        bracings: Dict[Tuple[int, int], List[Element1D]] = defaultdict(list)

        for bracing_group in bracing_groups:
            props = self._require_transverse_bracing_properties(bracing_group)
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
                n_i = self.nodes_manager.get_or_create_node(x=g_i_x, y=girder_i.node_start.Y, z=girder_i.node_start.Z)
                n_j = self.nodes_manager.get_or_create_node(x=g_j_x, y=girder_j.node_start.Y, z=girder_j.node_start.Z)
                ref_elem = self.elements_manager.get_or_create_beam(n_i, n_j)
                bracing_group.add_reference_element(ref_elem)
                bracings[(girder_i_index, girder_j_index)].append(ref_elem)

        return bracings

    def _generate_reference_elements_for_diaphragms_for_span(
        self,
        diaphragm_groups: Iterable[GeometryGroup],
        girders_ref_elements: Dict[int, Element1D],
        span_index: int,
    ) -> Dict[int, List[Element1D]]:
        diaphragms: Dict[int, List[Element1D]] = defaultdict(list)

        girder_indices = sorted(girders_ref_elements.keys())
        if len(girder_indices) < 2:
            return diaphragms

        for diaphragm_group in diaphragm_groups:
            props = self._require_diaphragm_properties(diaphragm_group)

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

                ref_elem = self.elements_manager.get_or_create_beam(node_i, node_j)
                diaphragm_group.add_reference_element(ref_elem)
                diaphragms[props.support_index].append(ref_elem)

        return diaphragms

    def _generate_finite_elements_for_girders(
            self,
            girder_y_offsets: Dict[int, Quantity],
            girders_ref_elements: Dict[int, Element1D],
            girders_segments: Dict[int, List[GirderSegmentResult]],
            transverse_deck_strips: Iterable[DeckStripResult],
            bracing_breakpoints: Dict[int, List[Quantity]]
    ) -> Dict[int, List[Element1D]]:
        """ """
        elements: Dict[int, List[Element1D]] = defaultdict(list)

        points_per_girder: Dict[int, List[Quantity]] = defaultdict(list)

        for idx, girder in girders_ref_elements.items():
            points_per_girder[idx].extend([
                cast(Quantity, girder.node_start.X),
                cast(Quantity, girder.node_end.X)])

            points_per_girder[idx].extend([
                x for s in girders_segments[idx] for x in (s.x_start, s.x_end) if idx in girders_segments.keys()
            ])

            points_per_girder[idx].extend([
                s.points_per_girder[idx] for s in transverse_deck_strips if idx in s.points_per_girder.keys()
            ])

            points_per_girder[idx].extend([
                p for p in bracing_breakpoints[idx] if idx in bracing_breakpoints.keys()
            ])

        for idx, points in points_per_girder.items():
            sorted_points = list(tools.to_sorted_unique_collection(points, self._tolerance))
            for i in range(len(sorted_points) - 1):
                ni = self.nodes_manager.get_or_create_node(
                    sorted_points[i],
                    girder_y_offsets[idx],
                    self.zero_length)
                nj = self.nodes_manager.get_or_create_node(
                    sorted_points[i+1],
                    girder_y_offsets[idx],
                    self.zero_length)
                element = self.elements_manager.get_or_create_beam(ni, nj)
                elements[idx].append(element)

        return elements

    def _generate_finite_elements_for_deck(
        self,
        transverse_deck_strips: Iterable[DeckStripResult],
        y_offsets_girders: Dict[int, Quantity],
        bridge_edge_beam_segments: Dict[int, AppliedVector],
        deck_cross_sections: List[SectionStandardSolidRectangle],
        deck_tol: Quantity
    ) -> Dict[UUID, List[Element1D]]:
        """
        Generate finite elements for deck.
        Return:
            Dictionary
        """
        elements_by_section: Dict[UUID, List[Element1D]] = defaultdict(list)

        # vertical deck offset from reference plane to deck centroid
        v_offset = cast(Quantity, deck_cross_sections[0].dimensions.height_h / 2)

        def _sort_key(point: Point, strip_axis: AppliedVector) -> float:
            delta = Vector.from_points(strip_axis.start_point, point)
            return (
                delta.x.to_base_units().magnitude * strip_axis.vector.x.to_base_units().magnitude
                + delta.y.to_base_units().magnitude * strip_axis.vector.y.to_base_units().magnitude
                + delta.z.to_base_units().magnitude * strip_axis.vector.z.to_base_units().magnitude
            )

        global_lower_girder_idx = min(
            y_offsets_girders,
            key=lambda idx: y_offsets_girders[idx].to_base_units().magnitude,
        )
        global_upper_girder_idx = max(
            y_offsets_girders,
            key=lambda idx: y_offsets_girders[idx].to_base_units().magnitude,
        )

        # iterate through deck strips and generate finite elements, group by section
        for strip in transverse_deck_strips:
            cross_section = next(
                (sec for sec in deck_cross_sections
                 if tools.is_close(strip.strip_width, sec.dimensions.width_b, deck_tol)))

            strip_points: List[Point] = []
            for idx, p in strip.points_per_girder.items():
                strip_points.append(Point(p, y_offsets_girders[idx], v_offset))

            strip_points.sort(key=lambda p: _sort_key(p, strip.strip_vector))

            nodes: List[Node] = [
                self.nodes_manager.get_or_create_node(point.x, point.y, point.z)
                for point in strip_points
            ]

            for ni in range(len(nodes) - 1):
                element = self.elements_manager.get_or_create_beam(nodes[ni], nodes[ni+1])
                elements_by_section[cross_section.guid].append(element)

            if not strip.points_per_girder:
                continue

            has_global_lower = global_lower_girder_idx in strip.points_per_girder
            has_global_upper = global_upper_girder_idx in strip.points_per_girder
            if not has_global_lower and not has_global_upper:
                continue

            lower_girder_node = (
                self.nodes_manager.get_or_create_node(
                    strip.points_per_girder[global_lower_girder_idx],
                    y_offsets_girders[global_lower_girder_idx],
                    v_offset,
                )
                if has_global_lower
                else None
            )
            upper_girder_node = (
                self.nodes_manager.get_or_create_node(
                    strip.points_per_girder[global_upper_girder_idx],
                    y_offsets_girders[global_upper_girder_idx],
                    v_offset,
                )
                if has_global_upper
                else None
            )

            edge_intersection_nodes: List[Node] = []
            for edge_beam_segment in bridge_edge_beam_segments.values():
                # Keep only intersections that lie on finite full-bridge edge-beam span.
                intersection = GeometryTools.project_node_on_segment(
                    line=strip.strip_vector,
                    segment=edge_beam_segment,
                    tol=self._tolerance,
                )
                if intersection is None:
                    continue

                edge_intersection_nodes.append(
                    self.nodes_manager.get_or_create_node(intersection.x, intersection.y, v_offset)
                )

            if not edge_intersection_nodes:
                continue

            edge_intersection_nodes.sort(key=lambda n: n.Y.to_base_units().magnitude)

            # Pair strip side-to-side: lower edge with lower outer girder, upper edge with upper outer girder.
            if len(edge_intersection_nodes) == 1:
                edge_node = edge_intersection_nodes[0]
                if lower_girder_node is not None and upper_girder_node is not None:
                    target_girder_node = (
                        lower_girder_node
                        if abs(edge_node.Y.to_base_units().magnitude - lower_girder_node.Y.to_base_units().magnitude)
                        <= abs(edge_node.Y.to_base_units().magnitude - upper_girder_node.Y.to_base_units().magnitude)
                        else upper_girder_node
                    )
                    elements_by_section[cross_section.guid].append(
                        self.elements_manager.get_or_create_beam(target_girder_node, edge_node)
                    )
                elif lower_girder_node is not None:
                    elements_by_section[cross_section.guid].append(
                        self.elements_manager.get_or_create_beam(lower_girder_node, edge_node)
                    )
                elif upper_girder_node is not None:
                    elements_by_section[cross_section.guid].append(
                        self.elements_manager.get_or_create_beam(upper_girder_node, edge_node)
                    )
            else:
                if lower_girder_node is not None:
                    elements_by_section[cross_section.guid].append(
                        self.elements_manager.get_or_create_beam(lower_girder_node, edge_intersection_nodes[0])
                    )
                if upper_girder_node is not None:
                    elements_by_section[cross_section.guid].append(
                        self.elements_manager.get_or_create_beam(upper_girder_node, edge_intersection_nodes[-1])
                    )

        return elements_by_section

    def _resolve_section_for_segment(self, segment_group: GeometryGroup):
        if not isinstance(segment_group.properties, GroupPropertiesSegment):
            raise ValueError("Segment group properties are invalid. GroupPropertiesSegment is required.")

        final_section = self._resolve_section_for_girder_segment_group(segment_group)

        if segment_group.properties.is_cracked:
            final_section = final_section #TODO: self._resolve_cracked_section(new_section, reinforcement_details)

        #assign main material to the section
        final_section.set_material_main(segment_group.get_material())

        # assign main material to belonging section if the section is tapered
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
                    self.require_weightless_material(deck_group.get_material())
                    )

        self._apply_girder_section_offset(segment_group=segment_group, section=final_section)

        return final_section

    def _resolve_section_for_girder_segment_group(self, segment_group: GeometryGroup) -> Section:
        all_sections = self._amm.get_all_sections()

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

        resolved_section: Section = deepcopy(base_section)

        origin_section = segment_group.parent_group.get_section()
        if origin_section is not None and isinstance(origin_section, SectionCompositeBase) and \
            isinstance(base_section, SectionCompositeBase):
            # replace only steel section dimensions and keep type and slab the same
            match origin_section:
                case SectionCompositeSteelISymmetric():
                    resolved_section: SectionCompositeSteelISymmetric = deepcopy(origin_section)
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
                            "This type of composite section is not supported yet: %s", type(base_section))

                case SectionCompositeSteelIAsymmetric():
                    resolved_section: SectionCompositeSteelIAsymmetric = deepcopy(origin_section)
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
                            "This type of composite section is not supported yet: %s", type(base_section))

                case _:
                        raise NotImplementedError(
                            "This type of composite section is not supported yet: %s", type(origin_section))

        segment_group.section = resolved_section
        return resolved_section

    def _apply_girder_section_offset(self, segment_group: GeometryGroup, section: Section) -> None:
        girder_group = segment_group.get_parent_group_by_component_type(StructuralComponentType.GIRDER)
        if girder_group is None:
            return

        span_group = segment_group.get_parent_group_by_component_type(StructuralComponentType.SPAN)
        if span_group is None:
            return

        deck_group = self._require_deck_group_for_span(span_group)
        deck_base_section = self._require_deck_base_section(deck_group)
        deck_thickness = deck_base_section.dimensions.height_h

        vertical_offset = deck_thickness
        if isinstance(section, SectionCompositeBase):
            composite_thickness = getattr(section.dimensions, "slab_thickness_tc", None)
            if composite_thickness is not None:
                vertical_offset = composite_thickness

        offset_reference = OffsetReference.CENTER_TOP
        horizontal_offset = self.zero_length

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

    def _apply_diaphragm_section_offset(self, diaphragm_group: GeometryGroup, section: Section) -> None:
        diaphragm_props = self._require_diaphragm_properties(diaphragm_group)

        span_group = diaphragm_group.get_parent_group_by_component_type(StructuralComponentType.SPAN)
        if span_group is None:
            return

        vertical_offset = self.zero_length
        if isinstance(diaphragm_props.geometry_details, DiaphragmBracingEncasedDetails):
            deck_group = self._require_deck_group_for_span(span_group)
            deck_base_section = self._require_deck_base_section(deck_group)
            vertical_offset = deck_base_section.dimensions.height_h
        elif not isinstance(diaphragm_props.geometry_details, DiaphragmSteelGirderDetails):
            return

        section.offset = Offset(
            offset_reference=OffsetReference.CENTER_TOP,
            horizontal_value=self.zero_length,
            vertical_value=vertical_offset,
        )

    def _require_bridge_properties(self, root_group: GeometryGroup) -> GroupPropertiesBridge:
        bridge_groups = root_group.get_groups_by_component_type(StructuralComponentType.BRIDGE)
        if not bridge_groups:
            raise ValueError("Bridge group has not been found.")

        bridge_props = bridge_groups[0].properties
        if not isinstance(bridge_props, GroupPropertiesBridge):
            raise ValueError("Bridge group properties are invalid. GroupPropertiesBridge is required.")
        return bridge_props

    def _require_superstructure_properties(self, root_group: GeometryGroup) -> GroupPropertiesSuperstructure:
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

    def _require_span_properties(self, span: GeometryGroup) -> GroupPropertiesSpan:
        if not isinstance(span, GeometryGroup):
            raise TypeError("Span group should be a GeometryGroup object.")
        if span.component_type != StructuralComponentType.SPAN:
            raise TypeError(f"Group {span.name} should have SPAN component type.")
        if not isinstance(span.properties, GroupPropertiesSpan):
            raise TypeError(f"Span group {span.name} should have GroupPropertiesSpan properties.")
        return span.properties

    def _require_transverse_bracing_properties(self, bracing_group: GeometryGroup) -> GroupPropertiesTransverseBracing:
        if not isinstance(bracing_group, GeometryGroup):
            raise TypeError("Bracing group should be a GeometryGroup object.")
        if bracing_group.component_type != StructuralComponentType.TRANSVERSE_BRACING:
            raise TypeError(f"Group {bracing_group.name} should have TRANSVERSE_BRACING component.")
        if not isinstance(bracing_group.properties, GroupPropertiesTransverseBracing):
            raise TypeError(f"Bracing group {bracing_group.name} should have "
                            f"GroupPropertiesTransverseBracing properties.")
        return bracing_group.properties

    def _require_diaphragm_properties(self, diaphragm_group: GeometryGroup) -> GroupPropertiesDiaphragm:
        if not isinstance(diaphragm_group, GeometryGroup):
            raise TypeError("Diaphragm group should be a GeometryGroup object.")
        if diaphragm_group.component_type != StructuralComponentType.DIAPHRAGM:
            raise TypeError(f"Group {diaphragm_group.name} should have DIAPHRAGM component type.")
        if not isinstance(diaphragm_group.properties, GroupPropertiesDiaphragm):
            raise TypeError(
                f"Diaphragm group {diaphragm_group.name} should have GroupPropertiesDiaphragm properties."
            )
        return diaphragm_group.properties

    def _require_plan_bracings_properties(self, plan_bracing_group: GeometryGroup) -> GroupPropertiesPlanBracing:
        if not isinstance(plan_bracing_group, GeometryGroup):
            raise TypeError("Plan bracing group should be a GeometryGroup object.")
        if plan_bracing_group.component_type != StructuralComponentType.PLAN_BRACING:
            raise TypeError(f"Group {plan_bracing_group.name} should have PLAN_BRACING component type.")
        if not isinstance(plan_bracing_group.properties, GroupPropertiesPlanBracing):
            raise TypeError(
                f"Plan bracing group {plan_bracing_group.name} should have GroupPropertiesPlanBracing properties."
            )
        return plan_bracing_group.properties

    def _require_deck_group_for_span(self, span: GeometryGroup) -> GeometryGroup:
        if not isinstance(span, GeometryGroup):
            raise TypeError("Span group should be a GeometryGroup object.")
        if span.component_type != StructuralComponentType.SPAN:
            raise TypeError(f"Group {span.name} should have SPAN component type.")
        deck_groups = span.get_groups_by_component_type(StructuralComponentType.DECK_SLAB)
        if not deck_groups:
            raise ValueError("Deck group has not been found for span %s.", span.name)
        if len(deck_groups) > 1:
            self._logger.warning(f"Deck group {span.name} has more than one group. Using first one.")
        return deck_groups[0]

    def _require_deck_base_section(self, deck_group: GeometryGroup) -> SectionStandardSolidRectangle:
        if not isinstance(deck_group, GeometryGroup):
            raise TypeError("Deck group should be a GeometryGroup object.")
        if deck_group.component_type != StructuralComponentType.DECK_SLAB:
            raise TypeError(f"Group {deck_group.name} should have DECK_SLAB component type.")
        if deck_group.section is None:
            raise ValueError(f"Deck group {deck_group.name} has no section assigned.")
        if not isinstance(deck_section := deck_group.section, SectionStandardSolidRectangle):
            raise TypeError(f"Deck group {deck_group.name} should have SectionStandardSolidRectangle section.")
        return deck_section

    def _require_dummy_section(self) -> Section:
        dummy_section = self.dummy_section
        if dummy_section is None:
            dummy_section = SectionStandardSolidRectangle(
                name="DummySection",
                dimensions=DimensionsSolidRectangle(
                    width_b= CONSTANTS.DUMMY_ELEMENT_SIZE_METERS*units.m,
                    height_h=CONSTANTS.DUMMY_ELEMENT_SIZE_METERS*units.m
                ))
            self.dummy_section = dummy_section
        return dummy_section

    def require_weightless_material(self, source_material: Material|None) -> Material|None:
        # to avoid duplicated weightless materials create a memory cache:
        if source_material is None:
            return None

        material_weightless = self._weightless_materials.get(source_material.guid, None)
        if material_weightless is None:
            material_weightless = deepcopy(source_material)
            material_weightless.name = f"{source_material.name}_weightless"
            material_weightless.general_properties.unit_weight = 0 * units.kN / units.m**3
            self._weightless_materials[source_material.guid] = material_weightless
        return material_weightless
