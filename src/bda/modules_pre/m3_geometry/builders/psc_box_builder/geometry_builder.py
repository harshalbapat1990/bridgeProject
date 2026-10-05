from __future__ import annotations

from bda.application.interfaces import IAppLogger, NullLogger
from bda.domain import AnalyticalMultiModel
from bda.domain.enums import StructuralComponentType
from bda.domain.models.submodels import GeometryGroup
from bda.domain.models.submodels.geometry_group_props.bridge_properties import GroupPropertiesBridge
from bda.modules_pre.m3_geometry.builders.psc_box_builder.build_context import GeometryPSCBoxBuildContext
from bda.modules_pre.m3_geometry.builders.psc_box_builder.build_steps import (
    AssignSpanFiniteElementsToSegmentsGroups,
    CollectBridgeProperties,
    CollectGeometryRoot,
    CollectSpans,
    CollectSupportsData,
    CreateSpanReferenceElements,
    GenerateSpanFiniteElements,
    GenerateVerticalRigidLinkage,
    InitializeSpanStates,
    ResolveSpanBoundarySegmentSections,
    ResolveSpanTaperedSegments, CollectPiles, CollectPiers, CreatePierReferenceElements, CollectPilecaps,
    CreatePilecapReferenceElements, CreateVerticalPilecapReferenceElements, CreatePileReferenceElements,
    CollectCrossheads,
    CreateCrossheadReferenceElement, CreateVerticalPilecapFiniteElements, CreatePileFiniteElements,
    CreateHorizontalPilecapElements, CreatePierFiniteElements, GeneratePileLinks, CollectSupToSub,
    CreateSupportBearingTopTopology,
    CreateCrossheadTaperedSegments, CollectGirders, CreateSupportBearingBottomTopology,
    CollectNodesForCrosshead, GenerateCrossheadFiniteElements, AssignCrossheadFiniteElementsToSegmentsGroups,
)
import bda.domain.units.registry as units


class GeometryPSCBoxBuilder:
    def __init__(
        self,
        amm: AnalyticalMultiModel,
        logger: IAppLogger | None = None,
    ):
        self._tolerance = 0.1 * units.mm
        self._amm = amm
        self._logger = logger or NullLogger()

        if self._amm.geometry_group is None:
            raise ValueError(
                "AnalyticalMultiModel has no geometry_group. "
                "Add geometry to AMM before creating GeometryPSCBoxBuilder."
            )

    def _build_pipeline_steps(self) -> list:
        return [
            # ----- collecting groups ----- #
            CollectGeometryRoot(),
            CollectBridgeProperties(),

            CollectSpans(),
            InitializeSpanStates(),
            ResolveSpanTaperedSegments(),
            ResolveSpanBoundarySegmentSections(),

            CollectSupportsData(),

            CollectSupToSub(),
            CollectCrossheads(),
            CollectPilecaps(),
            CollectPiers(),
            CollectPiles(),
            CollectGirders(),

            # ----- reference geometry ----- #
            CreateSpanReferenceElements(),
            CreateCrossheadReferenceElement(),
            CreatePilecapReferenceElements(),
            CreatePierReferenceElements(),
            CreatePileReferenceElements(),

            # ----- span FE ----- #
            GenerateSpanFiniteElements(),
            AssignSpanFiniteElementsToSegmentsGroups(),

            # ----- support linkage ----- #
            GenerateVerticalRigidLinkage(),
            CreateSupportBearingTopTopology(),
            CreateSupportBearingBottomTopology(),

            # ----- pilecap/pier/pile FE ----- #
            CreateHorizontalPilecapElements(),
            CreatePierFiniteElements(),
            CreatePileFiniteElements(),

            # ----- pilecap vertical members ----- #
            CreateVerticalPilecapReferenceElements(),
            CreateVerticalPilecapFiniteElements(),

            # ----- crosshead -----
            CollectNodesForCrosshead(),
            CreateCrossheadTaperedSegments(),
            GenerateCrossheadFiniteElements(),
            AssignCrossheadFiniteElementsToSegmentsGroups(),

            # ----- rigid links ----- #
            GeneratePileLinks(),
        ]

    def build(self) -> GeometryPSCBoxBuildContext:
        ctx = GeometryPSCBoxBuildContext(
            amm=self._amm,
            logger=self._logger,
            builder=self,
        )

        for step in self._build_pipeline_steps():
            step.execute(ctx)
        return ctx

    def _get_bridge_properties(self, root_group: GeometryGroup) -> GroupPropertiesBridge:
        bridge_groups = root_group.get_groups_by_component_type(StructuralComponentType.BRIDGE)
        if not bridge_groups:
            raise ValueError("Bridge group has not been found.")

        bridge_props = bridge_groups[0].properties
        if not isinstance(bridge_props, GroupPropertiesBridge):
            raise ValueError("Bridge group properties are invalid. GroupPropertiesBridge is required.")
        return bridge_props