from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Union, cast

from pint.registry import Quantity

from bda.domain.models.submodels import Element1D
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import ElementOrientation
from bda.modules_pre.m3_geometry.helpers.tools.models import AppliedVector
from bda.modules_pre.m3_geometry.helpers.tools.models import Point
from bda.modules_pre.m3_geometry.helpers.tools.models import Vector


@dataclass
class DeckStripResult:
    strip_width: Quantity
    points_per_girder: Dict[int, Quantity]
    strip_vector: AppliedVector


def _build_deck_strip_vector(
    girders: Dict[int, Element1D],
    points_per_girder: Dict[int, Quantity],
    strip_direction_vector: Vector,
) -> AppliedVector:
    sorted_girder_indices = sorted(girders.keys())
    left_idx = sorted_girder_indices[0]

    # Near skewed span ends not all girders can intersect a strip; then use the outermost available pair.
    if left_idx not in points_per_girder:
        available = sorted(points_per_girder.keys())
        left_idx = available[0]

    application_point = Point(
        x=points_per_girder[left_idx],
        y=girders[left_idx].node_start.Y,
        z=girders[left_idx].node_start.Z,
    )

    return AppliedVector(start_point=application_point, vector=strip_direction_vector)


def _is_within_range(
        x_start: Quantity,
        x_end: Quantity,
        x: Quantity,
        tolerance: Union[Quantity, float] = 0.001,
) -> bool:
    if isinstance(tolerance, float):
        tolerance = tolerance * x.units
    return (x_start - tolerance) <= x <= (x_end + tolerance)


def split_span_into_transverse_elements(
    span_length: Quantity,
    girders: Dict[int, Element1D],
    mesh_divisor: int,
    mesh_type: ElementOrientation,
    bridge_main_direction: Vector,
    support_i_vector: AppliedVector,
) -> Iterable[DeckStripResult]:
    deck_strips: List[DeckStripResult] = []
    # Deck strip points are tracked only on girders; edge beams are intentionally excluded.
    long_elements = dict(sorted(girders.items()))

    strip_direction_vector = (
        bridge_main_direction.perpendicular()
        if mesh_type == ElementOrientation.ORTHOGONAL
        else support_i_vector.vector
    )

    match mesh_type:
        case ElementOrientation.SKEWED:
            mesh_spacing: Quantity = cast(Quantity, span_length / mesh_divisor)
            delta_x = girders[0].node_start.X - girders[1].node_start.X
            delta_y = girders[0].node_start.Y - girders[1].node_start.Y
            skew_angle = math.atan(delta_y / delta_x)
            deck_strip_width: Quantity = cast(Quantity, mesh_spacing * math.cos(skew_angle))

            for i in range(mesh_divisor):
                offset = cast(Quantity, mesh_spacing * i)
                points_per_girder: Dict[int, Quantity] = {
                    idx: cast(Quantity, g.node_start.X + 0.5 * mesh_spacing + offset)
                    for idx, g in long_elements.items()
                }
                deck_strip_vector = _build_deck_strip_vector(
                    girders=girders,
                    points_per_girder=points_per_girder,
                    strip_direction_vector=strip_direction_vector,
                )
                deck_strips.append(
                    DeckStripResult(
                        strip_width=deck_strip_width,
                        points_per_girder=points_per_girder,
                        strip_vector=deck_strip_vector,
                    )
                )

        case ElementOrientation.ORTHOGONAL:
            sort_key = lambda p: p.to_base_units().magnitude

            start_x = sorted({
                g.node_start.X
                for g in girders.values()
            }, key=sort_key)

            end_x = sorted({
                g.node_end.X
                for g in girders.values()
            }, key=sort_key)

            edge_points = sorted(set(start_x) | set(end_x), key=sort_key)

            mesh_spacing_start = cast(Quantity, start_x[-1] - start_x[-2])
            mesh_spacing_end = cast(Quantity, end_x[1] - end_x[0])

            x_start_square_span = start_x[-1]
            x_end_square_span = end_x[0]

            # square span length minus half of the width of side transverse elements at each side of the span
            refined_span_length = cast(
                Quantity,
                x_end_square_span - x_start_square_span - 0.5 * mesh_spacing_start - 0.5 * mesh_spacing_end)

            refined_mesh_spacing = refined_span_length / mesh_divisor
            x_first_element_of_refined_span = cast(
                Quantity,
                x_start_square_span + 0.5 * mesh_spacing_start + 0.5 * refined_mesh_spacing)

            mid_points: List[Quantity] = []
            for i in range(mesh_divisor):
                mid_points.append(cast(Quantity, x_first_element_of_refined_span + i * refined_mesh_spacing))

            all_points = sorted(set(edge_points) | set(mid_points), key=sort_key)

            for p in all_points:
                # calculate widths of deck strips for triangle areas at the start and at the end
                # the main assumption here is that girder's spacing is regular
                if p in start_x:
                    strip_width = start_x[1] - start_x[0]
                elif p in end_x:
                    strip_width = end_x[1] - end_x[0]
                else:
                    strip_width = refined_mesh_spacing

                points_per_girder: Dict[int, Quantity] = {}
                for idx, el in long_elements.items():
                    if _is_within_range(el.node_start.X, el.node_end.X, p):
                        points_per_girder[idx] = p

                if len(points_per_girder) > 0:
                    deck_strip_vector = _build_deck_strip_vector(
                        girders=girders,
                        points_per_girder=points_per_girder,
                        strip_direction_vector=strip_direction_vector,
                    )
                    deck_strips.append(
                        DeckStripResult(
                            strip_width=cast(Quantity, strip_width),
                            points_per_girder=points_per_girder,
                            strip_vector=deck_strip_vector,
                        )
                    )

    return deck_strips
