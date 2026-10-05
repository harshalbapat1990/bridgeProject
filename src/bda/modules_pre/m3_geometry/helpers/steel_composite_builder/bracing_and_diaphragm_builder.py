from __future__ import annotations

from typing import Iterable, cast, List, TYPE_CHECKING

from bda.domain.enums import StructuralComponentType
from bda.domain.models.submodels import Element1D, Node
from bda.domain.models.submodels.geometry_group import GeometryGroup
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import PlanBracingType
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import (
    DiaphragmConcreteNonModelledDetails, GroupPropertiesTransverseBracing,
)
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.build_context import \
    GeometrySteelCompositeBuildContext, SpanReferenceData
from bda.modules_pre.m3_geometry.helpers.tools.geometry_tools import GeometryTools
from bda.modules_pre.m3_geometry.helpers.tools.models import Point

if TYPE_CHECKING:
    from bda.modules_pre.m3_geometry.helpers.steel_composite_builder import GeometrySteelCompositeBuilder


def generate_finite_elements_for_bracings_for_span(builder, span: GeometryGroup) -> None:
    """Build all bracing finite elements for a single span."""
    for bracing_group in builder._collect_bracings_for_span(span):
        ref_elements = [
            element
            for element in bracing_group.reference_elements
            if isinstance(element, Element1D)
        ]

        for bracing_index, reference_element in enumerate(ref_elements):
            builder._model_single_bracing(
                bracing_group=bracing_group,
                reference_element=reference_element,
                bracing_index=bracing_index,
            )


def generate_finite_elements_for_diaphragms_for_span(builder, span: GeometryGroup) -> None:
    """Build all diaphragm finite elements for a single span."""
    for diaphragm_group in builder._collect_diaphragms_for_span(span):
        diaphragm_props = builder._require_diaphragm_properties(diaphragm_group)

        # Non-modelled concrete diaphragms stay as metadata/reference only.
        if isinstance(diaphragm_props.geometry_details, DiaphragmConcreteNonModelledDetails):
            continue

        diaphragm_section = cast(GeometryGroup, diaphragm_group).get_section()
        builder._apply_diaphragm_section_offset(diaphragm_group, diaphragm_section)

        for reference_element in diaphragm_group.reference_elements:
            if not isinstance(reference_element, Element1D):
                continue

            diaphragm_group.analytical_typology.add_element(
                builder.elements_manager.get_or_create_beam(
                    reference_element.node_start,
                    reference_element.node_end,
                )
            )



def generate_finite_elements_for_plan_bracings_for_span(
        builder: GeometrySteelCompositeBuilder,
        span: GeometryGroup,
        span_reference_data: SpanReferenceData,
        ) -> None:
    """Build all plan bracings finite elements for a single span."""
    plan_bracings = builder._collect_plan_bracings_for_span(span)
    all_transverse_bracings = builder._collect_transverse_bracings_for_entire_bridge()

    for plan_bracing in plan_bracings:
        props = builder._require_plan_bracings_properties(plan_bracing)

        start_girder_index = props.left_girder_index
        end_girder_index = props.right_girder_index

        # find all transverse bracings that are connected to this plan bracing
        transv_bracings = [
            tb
            for tb in all_transverse_bracings
            if (isinstance(tb.properties, GroupPropertiesTransverseBracing) and
                (tb.properties.left_girder_index == start_girder_index
                 or tb.properties.left_girder_index == end_girder_index)
                and
                (tb.properties.right_girder_index == start_girder_index
                 or tb.properties.right_girder_index == end_girder_index))
        ]

        if len(transv_bracings) < 1:
            continue

        # collect all top chords for bracings
        top_chord_groups: List[GeometryGroup] = []

        for tr_br in transv_bracings:
            chords = tr_br.get_groups_by_component_type(StructuralComponentType.CHORD)
            if chords:
                top_chord: GeometryGroup = chords[0]
                for chord in chords:
                    ch_props = builder._require_chord_properties(chord)
                    t_ch_props = builder._require_chord_properties(top_chord)
                    if ch_props.vertical_offset_at_left < t_ch_props.vertical_offset_at_left:
                        top_chord = chord
                top_chord_groups.append(top_chord)

        # collect all nodes
        all_left_nodes: List[Node] = []
        all_right_nodes: List[Node] = []

        for top_chord in top_chord_groups:
            for e in iter(top_chord.analytical_typology.elements):
                if not isinstance(e, Element1D):
                    continue
                all_left_nodes.append(e.node_start)
                all_right_nodes.append(e.node_end)

        # filter nodes only in the current span
        start_vector = span_reference_data.support_i_vector
        end_vector = span_reference_data.support_j_vector

        left_nodes: List[Node] = []
        right_nodes: List[Node] = []

        left_nodes = [
            node
            for node in all_left_nodes
            if GeometryTools.project_node_on_line_along_x_asix(
                line=start_vector,
                point=Point(node.X, node.Y),
                tol=builder._tolerance
            ).x - builder._tolerance < node.X
               and GeometryTools.project_node_on_line_along_x_asix(
                line=end_vector,
                point=Point(node.X, node.Y),
                tol=builder._tolerance
            ).x + builder._tolerance > node.X
        ]

        right_nodes = [
            node
            for node in all_right_nodes
            if GeometryTools.project_node_on_line_along_x_asix(
                line=start_vector,
                point=Point(node.X, node.Y),
                tol=builder._tolerance
            ).x - builder._tolerance < node.X
               and GeometryTools.project_node_on_line_along_x_asix(
                line=end_vector,
                point=Point(node.X, node.Y),
                tol=builder._tolerance
            ).x + builder._tolerance > node.X
        ]

        if len(left_nodes) < 2 or len(right_nodes) < 2:
            continue

        match (props.plan_bracing_type):
            case PlanBracingType.PRATT:
                for i in range(len(left_nodes)-1):
                    element = builder.elements_manager.get_or_create_beam(right_nodes[i], left_nodes[i+1])
                    plan_bracing.analytical_typology.add_element(element)

            case PlanBracingType.WARREN:
                for i in range(len(left_nodes)-1):
                    if i%2==0:
                        element = builder.elements_manager.get_or_create_beam(right_nodes[i], left_nodes[i+1])
                    else:
                        element = builder.elements_manager.get_or_create_beam(left_nodes[i], right_nodes[i+1])
                    plan_bracing.analytical_typology.add_element(element)

            case PlanBracingType.X_TYPE:
                for i in range(len(left_nodes)-1):
                    e1 = builder.elements_manager.get_or_create_beam(right_nodes[i], left_nodes[i+1])
                    e2 = builder.elements_manager.get_or_create_beam(left_nodes[i], right_nodes[i+1])
                    plan_bracing.analytical_typology.add_elements([e1, e2])










