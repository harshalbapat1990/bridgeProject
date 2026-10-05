from dataclasses import dataclass
from typing import List, Optional, Dict, cast
from uuid import UUID

from pint.registry import Quantity

from bda.domain.models.submodels import Element1D
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import ElementOrientation
from bda.domain.models.submodels.geometry_group_props.shared import SegmentDetails
from bda.domain.models.submodels.geometry_group_props.superstructure_properties import CrackedExtentsDetails, \
    SpliceDetails, ConstrSequenceDetails
from bda.modules_pre.m3_geometry.helpers.tools import general_tools
from bda.modules_pre.m3_geometry.helpers.tools.general_tools import is_close


@dataclass
class GirderSegmentResult(SegmentDetails):
    x_start: Quantity
    x_end: Quantity
    cracked_section: bool
    splice_sectionId: Optional[UUID]
    deck_pouring_index: int


def _q_to_float(q: Quantity) -> float:
    """Convert Quantity to float in base units."""
    return q.to_base_units().magnitude



def _girder_x_range(reference_element: Element1D) -> tuple[Quantity, Quantity]:
    """
    Returns girder range in global X coordinates.
    """
    x1 = reference_element.node_start.X
    x2 = reference_element.node_end.X

    if _q_to_float(x1) <= _q_to_float(x2):
        return x1, x2

    return x2, x1


def _clip_extent(
    x_start: Quantity,
    x_end: Quantity,
    girder_x_start: Quantity,
    girder_x_end: Quantity,
) -> Optional[tuple[Quantity, Quantity]]:
    """
    Clips interval to girder global X range.
    """
    start = x_start if x_start > girder_x_start else girder_x_start
    end = x_end if x_end < girder_x_end else girder_x_end

    if end <= start:
        return None

    return start, end


def _project_cracked_extents(
    cracked_extents: List[CrackedExtentsDetails],
    girder: Element1D,
    girder_x_start: Quantity,
    girder_x_end: Quantity,
) -> List[CrackedExtentsDetails]:
    """
    Cracked extents are always measured from girder start.
    """

    result: List[CrackedExtentsDetails] = []

    girder_start = girder.node_start.X

    for crack in cracked_extents:

        global_start = girder_start + crack.x_start
        global_end = girder_start + crack.x_end

        clipped = _clip_extent(
            global_start,
            global_end,
            girder_x_start,
            girder_x_end,
        )

        if clipped is None:
            continue

        result.append(
            CrackedExtentsDetails(
                x_start=clipped[0],
                x_end=clipped[1]))
    return result


def _project_splices(
    splices: List[SpliceDetails],
    girder: Element1D,
    girder_x_start: Quantity,
    girder_x_end: Quantity,
) -> List[SpliceDetails]:
    """
    Splices are always measured from girder start.
    """
    result: List[SpliceDetails] = []

    girder_start = girder.node_start.X

    for splice in splices:

        global_x = girder_start + splice.x_start

        if global_x < girder_x_start:
            continue

        if global_x > girder_x_end:
            continue

        result.append(
            SpliceDetails(
                x_start=global_x,
                section_id=splice.section_id))
    return result


def _project_construction_sequence(
    details: Optional[ConstrSequenceDetails],
    girder: Element1D,
    girder_x_start: Quantity,
    girder_x_end: Quantity,
    span_offset: Quantity,
) -> Optional[ConstrSequenceDetails]:
    """
    Construction sequence interpretation depends on pouring orientation.
    """
    if details is None:
        return None

    segments: List[SegmentDetails] = []

    girder_start = girder.node_start.X

    for seg in details.segments:

        if details.pouring_orientation == ElementOrientation.ORTHOGONAL:
            global_x = span_offset + seg.x_start
        else:
            global_x = girder_start + seg.x_start

        if global_x < girder_x_start:
            continue

        if global_x > girder_x_end:
            continue

        segments.append(
            SegmentDetails(
                x_start=global_x))

    return ConstrSequenceDetails(
        segments=segments,
        pouring_orientation=details.pouring_orientation)


def _split_girder_into_segments(
    x_start: Quantity,
    x_end: Quantity,
    cracked_extents: Optional[List[CrackedExtentsDetails]] = None,
    splices: Optional[List[SpliceDetails]] = None,
    construction_sequence_details: Optional[ConstrSequenceDetails] = None,
    tolerance: Optional[Quantity] = None,
) -> List[GirderSegmentResult]:
    """
    Splits single girder into homogeneous segments.
    All coordinates are expected in global X system.
    """
    cracked_extents = cracked_extents or []
    splices = splices or []

    tol = cast(Quantity, tolerance if tolerance else 0.01 * x_start.units)

    split_points = {x_start, x_end}

    for crack in cracked_extents:
        split_points.add(crack.x_start)
        split_points.add(crack.x_end)

    for splice in splices:
        split_points.add(splice.x_start)

    if construction_sequence_details:
        for seg in construction_sequence_details.segments:
            split_points.add(seg.x_start)

    sorted_points = sorted(
        general_tools.to_sorted_unique_collection(split_points, tol),
        key=lambda q: q.to_base_units().magnitude,
    )

    filtered_points: List[Quantity] = []

    for point in sorted_points:

        if not filtered_points:
            filtered_points.append(point)
            continue

        if not is_close(point, filtered_points[-1], tol):
            filtered_points.append(point)

    raw_segments: List[GirderSegmentResult] = []

    sorted_splices = sorted(
        splices,
        key=lambda s: s.x_start.to_base_units().magnitude,
    )

    sorted_sequence = (sorted(
                              construction_sequence_details.segments,
                              key=lambda s: s.x_start.to_base_units().magnitude)
                       if construction_sequence_details else [])

    for i in range(len(filtered_points) - 1):

        seg_start = filtered_points[i]
        seg_end = filtered_points[i + 1]

        if is_close(seg_start, seg_end, tol):
            continue

        mid = cast(Quantity, (seg_start + seg_end) / 2)

        cracked = any(
            c.x_start - tol
            <= mid
            <= c.x_end + tol
            for c in cracked_extents
        )

        active_splice = None

        for splice in sorted_splices:
            if splice.x_start <= mid + tol:
                active_splice = splice.section_id
            else:
                break

        pouring_index = 0

        if construction_sequence_details:
            for idx, segment in enumerate(sorted_sequence):
                if segment.x_start <= mid + tol:
                    pouring_index = idx+1
                else:
                    break

        raw_segments.append(
            GirderSegmentResult(
                x_start=seg_start,
                x_end=seg_end,
                cracked_section=cracked,
                splice_sectionId=active_splice,
                deck_pouring_index=pouring_index,
            )
        )

    merged: List[GirderSegmentResult] = []

    for seg in raw_segments:

        if not merged:
            merged.append(seg)
            continue

        prev = merged[-1]

        if (
            prev.cracked_section == seg.cracked_section
            and prev.splice_sectionId == seg.splice_sectionId
            and prev.deck_pouring_index == seg.deck_pouring_index
            and is_close(prev.x_end, seg.x_start, tol,
            )
        ):
            merged[-1] = GirderSegmentResult(
                x_start=prev.x_start,
                x_end=seg.x_end,
                cracked_section=prev.cracked_section,
                splice_sectionId=prev.splice_sectionId,
                deck_pouring_index=prev.deck_pouring_index,
            )
        else:
            merged.append(seg)

    return merged


def split_span_into_girder_segments(
    girders: Dict[int, Element1D],
    span_offset: Quantity,
    cracked_extents: Optional[List[CrackedExtentsDetails]] = None,
    splices: Optional[List[SpliceDetails]] = None,
    construction_sequence_details: Optional[ConstrSequenceDetails] = None,
    tolerance: Optional[Quantity] = None,
) -> Dict[int, List[GirderSegmentResult]]:
    """
    Converts span-local data into global coordinates and
    returns segments for each girder.

    Result:
        {girder_index: List[GirderSegmentResult]}
    """

    result: Dict[int, List[GirderSegmentResult]] = {}

    cracked_extents = cracked_extents or []
    splices = splices or []

    for girder_index, reference_element in girders.items():

        girder_x_start, girder_x_end = _girder_x_range(reference_element)

        girder_cracks = _project_cracked_extents(
            cracked_extents,
            reference_element,
            girder_x_start,
            girder_x_end)

        girder_splices = _project_splices(
            splices,
            reference_element,
            girder_x_start,
            girder_x_end)

        girder_sequence = _project_construction_sequence(
            construction_sequence_details,
            reference_element,
            girder_x_start,
            girder_x_end,
            span_offset)

        result[girder_index] = _split_girder_into_segments(
            x_start=girder_x_start,
            x_end=girder_x_end,
            cracked_extents=girder_cracks,
            splices=girder_splices,
            construction_sequence_details=girder_sequence,
            tolerance=tolerance)

    return result