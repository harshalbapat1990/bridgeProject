from __future__ import annotations

from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import ElementOrientation
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.build_context import (
    GeometrySteelCompositeBuildContext,
)
from bda.modules_pre.m3_geometry.helpers.steel_composite_builder.constants import SKEW_MESH_ANGLE_LIMIT_ABS_DEG


class BuildStep:
    def execute(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        raise NotImplementedError


class CollectGeometryRoot(BuildStep):
    def execute(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        geometry = ctx.amm.geometry_group
        if geometry is None:
            raise ValueError("AnalyticalMultiModel has no geometry_group.")
        ctx.geometry = geometry


class CollectSpans(BuildStep):
    def execute(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        if ctx.geometry is None:
            raise ValueError("Build context has no geometry.")

        spans = ctx.builder._collect_spans(ctx.geometry)
        if not spans:
            raise ValueError("No SPAN groups were found.")

        ctx.spans = spans


class CollectSupportAngles(BuildStep):
    def execute(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        if ctx.geometry is None:
            raise ValueError("Build context has no geometry.")

        support_angles = ctx.builder._collect_support_angles(ctx.geometry)
        if not support_angles:
            raise ValueError("No SUPPORT groups were found.")
        ctx.support_angles = support_angles


class ResolveBridgeLayout(BuildStep):
    def execute(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        if ctx.geometry is None:
            raise ValueError("Build context has no geometry.")

        builder = ctx.builder
        bridge_properties = builder._require_bridge_properties(ctx.geometry)
        mesh_divisor = bridge_properties.analysis_settings.girder_mesh_divisor
        if mesh_divisor < 1:
            raise ValueError(f"Invalid girder mesh divisor {mesh_divisor}. Value must be >= 1.")

        y_offsets_girders = builder._resolve_girder_yoffsets(ctx.geometry)
        y_offsets_edge_beams = builder._resolve_edge_beams_yoffsets(ctx.geometry)

        ctx.y_offsets_girders = y_offsets_girders
        ctx.y_offsets_edge_beams = y_offsets_edge_beams
        ctx.all_x_values_girders = {k: [] for k in y_offsets_girders}
        ctx.bridge_properties = bridge_properties
        ctx.girder_mesh_divisor = mesh_divisor


class ResolveGrillageType(BuildStep):
    def execute(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        first_sup_skew_angle = ctx.builder._require_support_angle(ctx.support_angles, 0)
        ctx.grillage_type = (
            ElementOrientation.ORTHOGONAL
            if abs(first_sup_skew_angle.to("deg").magnitude) > SKEW_MESH_ANGLE_LIMIT_ABS_DEG
            else ElementOrientation.SKEWED
        )


class InitializeSpanStates(BuildStep):
    def execute(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        ctx.builder._initialize_span_states(ctx)


class ProcessSpanBracingBreakpointsStep(BuildStep):
    def execute(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        ctx.builder._resolve_span_bracing_breakpoints(ctx)


class ProcessSpanDeckStripsStep(BuildStep):
    def execute(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        ctx.builder._resolve_span_deck_strips(ctx)


class ProcessSpanIncludeSpliceStep(BuildStep):
    def execute(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        ctx.builder._resolve_span_include_splice(ctx)


class ProcessSpanCrackExtentsStep(BuildStep):
    def execute(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        ctx.builder._resolve_span_crack_extents(ctx)


class ProcessSpanGirderSegmentsStep(BuildStep):
    def execute(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        ctx.builder._resolve_span_girder_segments(ctx)


class ProcessSpanGirderFiniteElementsStep(BuildStep):
    def execute(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        ctx.builder._generate_span_girder_finite_elements(ctx)


class ProcessSpanBracingsStep(BuildStep):
    def execute(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        ctx.builder._generate_span_bracings(ctx)


class ProcessSpanDiaphragmsStep(BuildStep):
    def execute(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        ctx.builder._generate_span_diaphragms(ctx)

class ProcessSpanPlanBracingsStep(BuildStep):
    def execute(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        ctx.builder._generate_span_plan_bracings(ctx)

class ProcessSpanFinalizeGirderSegmentsStep(BuildStep):
    def execute(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        ctx.builder._finalize_span_girder_segments(ctx)


class ProcessEntireBridgeDeckStep(BuildStep):
    def execute(self, ctx: GeometrySteelCompositeBuildContext) -> None:
        ctx.builder._process_deck_for_entire_bridge(ctx)

