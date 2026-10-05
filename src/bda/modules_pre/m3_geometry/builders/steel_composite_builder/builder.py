"""Steel-composite grillage builder.

Fills the AnalyticalMultiModel geometry with nodes, finite elements and links
by running a fixed pipeline of build phases over a shared ``BuildContext``.
"""
from __future__ import annotations

from typing import Callable, Tuple

from bda.application.interfaces.logging import IAppLogger, NullLogger
from bda.domain import AnalyticalMultiModel
import bda.domain.units.registry as units
from bda.modules_pre.m3_geometry.helpers.tools.models import UnitVector, Vector
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.context import BuildContext
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.phases import (
    bracings,
    deck,
    diaphragms,
    girder_segment_assignment,
    girders,
    plan_bracings,
    preparations,
    bearings,
)

BuildPhase = Callable[[BuildContext], None]


class GeometrySteelCompositeBuilder:
    """Builds steel-composite grillage geometry inside the provided AMM."""

    def __init__(
        self,
        amm: AnalyticalMultiModel,
        logger: IAppLogger | None = None,
    ):
        if amm.geometry_group is None:
            raise ValueError(
                "AnalyticalMultiModel has no geometry_group. "
                "Add geometry to AMM before creating GeometrySteelCompositeBuilder."
            )

        self._amm = amm
        self._logger = logger or NullLogger()
        self._tolerance = 0.1 * units.mm

    @staticmethod
    def _pipeline() -> Tuple[BuildPhase, ...]:
        return (
            preparations.run,
            girders.run,
            bracings.run,
            diaphragms.run,
            plan_bracings.run,
            girder_segment_assignment.run,
            deck.run,
            bearings.run
        )

    def build(self) -> BuildContext:
        ctx = BuildContext(
            amm=self._amm,
            logger=self._logger,
            tolerance=self._tolerance,
            zero_length=0.0 * units.m,
            bridge_direction_vector=Vector.from_unit_vector_and_length(UnitVector(1, 0, 0), 1 * units.m),
        )

        for phase in self._pipeline():
            phase(ctx)

        return ctx
