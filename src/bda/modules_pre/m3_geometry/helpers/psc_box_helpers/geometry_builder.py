from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, TypeGuard, cast

from pint.registry import Quantity

from bda.application.interfaces import IAppLogger, NullLogger
from bda.domain import AnalyticalMultiModel
from bda.domain.enums import StructuralComponentType
from bda.domain.models.submodels import GeometryGroup, Node
from bda.domain.models.submodels.element import Element, Element1D
from bda.domain.models.submodels.geometry_group_props.bridge_properties import GroupPropertiesBridge
from bda.domain.models.submodels.geometry_group_props.shared import TaperedDetails
from bda.domain.models.submodels.geometry_group_props.substructure_properties import GroupPropertiesSupport
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import GroupPropertiesGirder, \
    GroupPropertiesSpan
from bda.domain.models.submodels.sections import SectionTapered
from bda.modules_pre.m3_geometry.helpers.tools.managers.nodes_manager import NodesManager
import bda.domain.units.registry as units
from bda.modules_pre.m3_geometry.helpers.psc_box_helpers.split_span_into_segments_ import split_span_into_segments


# =========================
# Helper functions
# =========================

def _require_support_angle(self, support_angles: dict[int, Quantity], support_index: int) -> Quantity:
    self._logger.debug(
        "[GeometryBuilder] require support angle | support_index=%s",
        support_index,
    )
    angle = support_angles.get(support_index)
    if angle is None:
        raise ValueError(f"Support with index {support_index} has not been found.")
    return angle


# =========================
# 🧠 Shared build context
# =========================

@dataclass
class GeometryBuildContext:
    amm: AnalyticalMultiModel
    logger: IAppLogger

    girder_mesh_divisor: int = field(default_factory=int)
    spans: List[GeometryGroup] = field(default_factory=list)
    support_sections: Dict[int, str] = field(default_factory=dict)
    support_angles: Dict[int, Quantity] = field(default_factory=dict)

    girder_offsets: Dict[int, Quantity] = field(default_factory=dict)
    girder_nodes: Dict[int, List[Node]] = field(default_factory=dict)

    elements: List[Element] = field(default_factory=list)

    nodes_manager: NodesManager = field(default_factory=NodesManager)
    next_element_id = 1

    zero: Quantity = 0.0 * units.m
    eps = 1e-6 * units.m
    section_by_guid = {}


# =========================
# 🧩 Builder steps
# =========================

class BuildStep:
    def execute(self, ctx: GeometryBuildContext) -> None:
        raise NotImplementedError


class CollectBridge(BuildStep):
    @staticmethod
    def _is_bridge(g: GeometryGroup) -> bool:
        return (
            g.component_type == StructuralComponentType.BRIDGE
            and isinstance(g.properties, GroupPropertiesBridge)
        )

    def execute(self, ctx: GeometryBuildContext) -> None:
        geometry = ctx.amm.geometry_group
        ctx.girder_mesh_divisor = geometry.properties.analysis_settings.girder_mesh_divisor


class CollectSpans(BuildStep):
    @staticmethod
    def _is_span(g: GeometryGroup) -> bool:
        return (
            g.component_type == StructuralComponentType.SPAN
            and isinstance(g.properties, GroupPropertiesSpan)
        )

    def execute(self, ctx: GeometryBuildContext) -> None:
        geometry = ctx.amm.geometry_group
        if geometry is None:
            raise ValueError("AnalyticalMultiModel has no geometry_group.")

        ctx.logger.debug(f"[GeometryBuilder] collect spans | geometry=%s", geometry)

        ctx.spans = sorted(
            (
                g for g in geometry.iter_groups()
                if self._is_span(g)
            ),
            key=lambda s: s.properties.span_index
        )


class CollectSupportAngles(BuildStep):
    @staticmethod
    def _is_support(g: GeometryGroup) -> bool:
        return (
            g.component_type == StructuralComponentType.SUPPORT
            and isinstance(g.properties, GroupPropertiesSupport)
        )

    def execute(self, ctx: GeometryBuildContext) -> None:
        geometry = ctx.amm.geometry_group

        ctx.logger.debug("[Builder] Collect support angles")

        supports = sorted(
            (
                g for g in geometry.iter_groups()
                if self._is_support(g)
            ),
            key=lambda s: s.properties.support_index
        )

        mapping: Dict[int, Quantity] = {}
        for s in supports:
            idx = s.properties.support_index
            if idx in mapping:
                raise ValueError(f"Duplicate support index: {idx}")
            mapping[idx] = s.properties.skew_angle

        ctx.support_angles = mapping

class ProcessSpans(BuildStep):
    @staticmethod
    def _is_girder(g: GeometryGroup) -> bool:
        return (
            g.component_type == StructuralComponentType.GIRDER
            and isinstance(g.properties, GroupPropertiesGirder)
        )

    @staticmethod
    def _is_tapered(g: GeometryGroup) -> TypeGuard[GeometryGroup]:
        details = g.properties.tapered_details
        return (
                g.component_type == StructuralComponentType.SPAN
                and isinstance(g.properties, GroupPropertiesSpan)
                and isinstance(details, list)
                and any(isinstance(e, TaperedDetails) for e in details)
        )

    @staticmethod
    def _is_tapered_section(section) -> bool:
        return isinstance(section, SectionTapered)

    def execute(self, ctx: GeometryBuildContext) -> None:
        if not ctx.spans:
            raise ValueError("No SPANS group found.")

        offset = ctx.zero

        for span in ctx.spans:
            offset = self._process_single_span(ctx, span, offset)

    def _process_single_span(
            self,
            ctx: GeometryBuildContext,
            span: GeometryGroup,
            offset: Quantity,
    ):
        if span.name == "Span_3":
            print(span.properties)
        span_length = span.properties.span_length
        mesh_divisor = ctx.girder_mesh_divisor

        all_sections = ctx.amm.get_all_sections()
        sections_by_guid = {s.guid: s for s in all_sections}

        try:
            delta = cast(Quantity, span_length / mesh_divisor)
        except ZeroDivisionError:
            raise ValueError("Span length cannot be zero.")

        girder: GeometryGroup = span.get_groups_by_component_type(StructuralComponentType.GIRDER)[0]

        # ✅ collect taper zones
        tapered = span.properties.tapered_details if self._is_tapered(span) else None
        y = 0.0 * units.m

        #todo delete
        if tapered:
            for t in tapered:
                ctx.logger.debug(
                    "SPAN=%s TAPER section_id=%s start=%s end=%s",
                    span.name,
                    t.section_id,
                    t.x_start,
                    t.x_end,
                )

        # todo delete
        for t in tapered:
            ctx.logger.debug(
                "SPAN=%s section_id=%s",
                span.name,
                t.section_id
            )

        # ---------------------------
        # 1. Generate base mesh
        # ---------------------------
        x_positions: List[Quantity] = [
            offset + i * delta for i in range(mesh_divisor + 1)
        ]

        # ---------------------------
        # 2. Generate reference elements
        # ---------------------------
        node_start = ctx.nodes_manager.get_or_create_node(x= offset,
                                                          y= ctx.zero,
                                                          z= ctx.zero)
        node_end = ctx.nodes_manager.get_or_create_node(x= offset + span_length,
                                                        y=ctx.zero,
                                                        z=ctx.zero)
        reference_element = Element1D(node_start= node_start, node_end= node_end)
        girder.add_reference_element(element=reference_element)

        ctx.logger.debug(f"[GeometryBuilder] Reference element {reference_element}")
        # ---------------------------
        # 3. Inject taper boundaries
        # ---------------------------

        segments = split_span_into_segments(span_length, tapered, tolerance=1 * units.mm)

        ctx.logger.debug("SPAN = %s", span.name)

        for seg in segments:
            ctx.logger.debug(
                "RESULT idx=%s start=%s end=%s section=%s",
                seg.segment_index,
                seg.x_start,
                seg.x_end,
                seg.section_id,
            )

        current_section_id = span.section_uid
        current_section = span.section

        for s in segments:
            x_start = offset + s.x_start
            x_end = offset + s.x_end

            x_positions.append(x_start)
            x_positions.append(x_end)

        # ✅ sort and deduplicate
        x_positions = sorted(
            {x.magnitude: x for x in x_positions}.values(),
            key= lambda x: x.magnitude
        )
        elements: List[Element1D] = []

        for i in range(len(x_positions) - 1):
            ni = ctx.nodes_manager.get_or_create_node(x_positions[i], y, ctx.zero)
            nj = ctx.nodes_manager.get_or_create_node(x_positions[i + 1], y, ctx.zero)
            element = Element1D(ni, nj)
            elements.append(element)

        for segment in segments:
            ctx.logger.debug(
                "SEGMENT idx=%s start=%s end=%s section_id=%s",
                segment.segment_index,
                segment.x_start,
                segment.x_end,
                segment.section_id,
            )
            included_elements: List[Element1D] = []

            for e in elements:
                mid_x = (e.node_end.X + e.node_start.X) / 2

                if segment.x_start + offset <= mid_x <= segment.x_end + offset:
                    included_elements.append(e)

            if segment.section_id is None:
                section = current_section
            else:
                section = sections_by_guid.get(segment.section_id)

                if isinstance(section, SectionTapered):
                    current_section = section.section_end

                for sec in all_sections:
                    if str(sec.guid) == str(segment.section_id):
                        ctx.logger.debug(
                            "section guid=%s type=%s",
                            sec.guid,
                            type(sec.guid),
                        )

                if section is None:
                    raise ValueError(
                        f"Section {segment.section_id} not found."
                    )

            sub_group = GeometryGroup(
                    guid=uuid.uuid4(),
                    component_type=StructuralComponentType.SEGMENT,
                    name=f'Subgroup girder {segment.segment_index}'
                )
            sub_group.section = section

            sub_group.analytical_typology.add_elements(included_elements)
            girder.add_nested_group(sub_group)

            if isinstance(section, SectionTapered):
                current_section = section.section_end

        return offset + span_length

    def _resolve_section(self, span, x_global, offset):
        local_x = x_global - offset

        #todo
        tapered = getattr(span.properties, "tapered_details", [])

        for t in tapered:
            if t.x_start <= local_x < t.x_end:
                return t.section_uid

        # fallback
        return span.section_uid

class ExtractSupportNodes(BuildStep):
    def execute(self, ctx: GeometryBuildContext) -> None:
        ctx.logger.debug("[Builder] Extract support nodes")

        offset = ctx.zero
        support_index = 0

        support_nodes = {}

        for span in ctx.spans:
            span_length = span.properties.span_length

            support_positions = [
                offset,
                offset + span_length,
            ]


# =========================
# 🏗️ Main Builder
# =========================

class GeometryPSCBoxBuilder:
    """Builds PSC Box geometry"""

    def __init__(
        self,
        amm: AnalyticalMultiModel,
        logger: IAppLogger | None = None,
    ):
        self._ctx = GeometryBuildContext(
            amm=amm,
            logger=logger or NullLogger(),
        )
        self._steps: List[BuildStep] = []

    # --- API ---

    def with_bridge(self) -> GeometryPSCBoxBuilder:
        self._steps.append(CollectBridge())
        return self

    def with_spans(self) -> GeometryPSCBoxBuilder:
        self._steps.append(CollectSpans())
        return self

    def with_support_angles(self) -> GeometryPSCBoxBuilder:
        self._steps.append(CollectSupportAngles())
        return self

    def with_span_processing(self) -> GeometryPSCBoxBuilder:
        self._steps.append(ProcessSpans())
        return self

    def build(self) -> GeometryBuildContext:
        if self._ctx.amm.geometry_group is None:
            raise ValueError("AnalyticalMultiModel has no geometry_group.")

        for step in self._steps:
            step.execute(self._ctx)

        return self._ctx