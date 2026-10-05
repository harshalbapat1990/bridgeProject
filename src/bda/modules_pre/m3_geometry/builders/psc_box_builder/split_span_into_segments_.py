from dataclasses import dataclass
from typing import Dict, List, Optional, cast
from uuid import UUID

from pint.registry import Quantity

from bda.domain.models.submodels.geometry_group_props.shared import TaperedDetails
from bda.domain.models.submodels.sections.tapered import SectionTapered
from bda.modules_pre.m3_geometry.helpers.tools.general_tools import is_close



@dataclass
class SpanSegmentResult:
    segment_index: int
    x_start: Quantity
    x_end: Quantity
    section_id: Optional[UUID]
    start_id: Optional[UUID]
    end_id: Optional[UUID]
    is_tapered: bool


def _q_to_float(q: Quantity) -> float:
    """Convert Quantity to float in base units."""
    return q.to_base_units().magnitude

def _shift_to_global(local_x: Quantity, span_offset: Quantity) -> Quantity:
    return cast(Quantity, span_offset + local_x)

def _validate_tapered_details(
    tapered_details: List[TaperedDetails],
    span_length: Quantity,
    tol: Quantity,
    span_index: Optional[int],
    span_name: Optional[str],
) -> List[TaperedDetails]:
    sorted_tapered = sorted(
        tapered_details,
        key=lambda s: s.x_start.to_base_units().magnitude,
    )

    for tapered in sorted_tapered:
        if is_close(tapered.x_start, tapered.x_end, tol) or tapered.x_end < tapered.x_start:
            raise ValueError(
                f"Invalid tapered range in span '{span_name}' (index={span_index}): "
                f"x_start={tapered.x_start}, x_end={tapered.x_end}."
            )

        if tapered.x_start < -tol or tapered.x_end > span_length + tol:
            raise ValueError(
                f"Tapered range outside span bounds in span '{span_name}' (index={span_index}): "
                f"range=[{tapered.x_start}, {tapered.x_end}], span_length={span_length}."
            )

    for prev, curr in zip(sorted_tapered, sorted_tapered[1:]):
        if curr.x_start < prev.x_end - tol:
            raise ValueError(
                "Overlapping tapered ranges are not allowed. "
                f"Span '{span_name}' (index={span_index}) conflict: "
                f"[{prev.x_start}, {prev.x_end}] (section={prev.section_id}) overlaps "
                f"[{curr.x_start}, {curr.x_end}] (section={curr.section_id})."
            )

    return sorted_tapered


def _resolve_taper_transition_ids(
    tapered: TaperedDetails,
    sections_by_guid: Optional[Dict[UUID, object]],
    span_index: Optional[int],
    span_name: Optional[str],
) -> tuple[Optional[UUID], Optional[UUID]]:
    if sections_by_guid is None:
        return None, None

    tapered_section = sections_by_guid.get(tapered.section_id)

    if tapered_section is None:
        raise ValueError(
            f"Tapered section {tapered.section_id} not found for span '{span_name}' (index={span_index})."
        )

    if not isinstance(tapered_section, SectionTapered):
        raise ValueError(
            f"Section {tapered.section_id} is not SectionTapered for span '{span_name}' (index={span_index})."
        )

    return tapered_section.section_start_id, tapered_section.section_end_id


def split_span_into_segments(
    span_length: Quantity,
    tapered_details: Optional[List[TaperedDetails]] = None,
    tolerance: Optional[Quantity] = None,
    *,
    span_offset: Optional[Quantity] = None,
    span_index: Optional[int] = None,
    span_name: Optional[str] = None,
    initial_section_id: Optional[UUID] = None,
    sections_by_guid: Optional[Dict[UUID, object]] = None,
) -> tuple[List[SpanSegmentResult], Optional[UUID]]:
    """
    Split a single span into homogeneous segments in global X coordinates.

    Tracks a running ``current_section_id`` that starts at ``initial_section_id``
    and advances to ``section_end_id`` whenever a tapered zone is passed.
    This enables full cross-span continuity when the caller chains the returned
    ``final_section_id`` as the ``initial_section_id`` of the next span.

    Returns:
        (segments, final_section_id)
    """

    tapered_details = tapered_details or []
    tol = cast(Quantity, tolerance if tolerance else 0.001 * span_length.units)
    global_offset = cast(Quantity, span_offset if span_offset is not None else 0.0 * span_length.units)
    sorted_tapered = _validate_tapered_details(
        tapered_details=tapered_details,
        span_length=span_length,
        tol=tol,
        span_index=span_index,
        span_name=span_name,
    )

    # ---- STEP 1: collect split points ----
    split_points = {0.0 * span_length.units, span_length}
    for tapered in sorted_tapered:
        split_points.add(tapered.x_start)
        split_points.add(tapered.x_end)

    # ---- STEP 2: sort & deduplicate with tolerance ----
    sorted_points = sorted(split_points, key=lambda q: q.to_base_units().magnitude)

    filtered_points: List[Quantity] = []
    for point in sorted_points:
        if not filtered_points:
            filtered_points.append(point)
            continue

        if not is_close(point, filtered_points[-1], tol):
            filtered_points.append(point)

    # ---- STEP 3: create raw segments with running section tracker ----
    raw_segments: List[SpanSegmentResult] = []

    # current_section_id flows through the span (and across spans via chaining).
    current_section_id: Optional[UUID] = initial_section_id

    for i in range(len(filtered_points) - 1):
        local_start = filtered_points[i]
        local_end = filtered_points[i + 1]

        if is_close(local_start, local_end, tol):
            continue

        mid = cast(Quantity, (local_start + local_end) / 2)

        active_tapered: Optional[TaperedDetails] = None
        for tapered in sorted_tapered:
            if tapered.x_start - tol <= mid <= tapered.x_end + tol:
                active_tapered = tapered
                break

        if active_tapered is not None:
            taper_start_id, taper_end_id = _resolve_taper_transition_ids(
                tapered=active_tapered,
                sections_by_guid=sections_by_guid,
                span_index=span_index,
                span_name=span_name,
            )
            raw_segments.append(
                SpanSegmentResult(
                    x_start=_shift_to_global(local_start, global_offset),
                    x_end=_shift_to_global(local_end, global_offset),
                    segment_index=len(raw_segments),
                    section_id=active_tapered.section_id,
                    start_id=taper_start_id,
                    end_id=taper_end_id,
                    is_tapered=True,
                )
            )
            # Advance running section to what comes after the tapered zone.
            current_section_id = taper_end_id
        else:
            # Non-tapered: section is uniform → start_id == end_id == current.
            raw_segments.append(
                SpanSegmentResult(
                    x_start=_shift_to_global(local_start, global_offset),
                    x_end=_shift_to_global(local_end, global_offset),
                    segment_index=len(raw_segments),
                    section_id=current_section_id,
                    start_id=current_section_id,
                    end_id=current_section_id,
                    is_tapered=False,
                )
            )

    # ---- STEP 4: merge adjacent identical segments ----
    merged: List[SpanSegmentResult] = []

    for seg in raw_segments:
        if not merged:
            merged.append(seg)
            continue

        prev = merged[-1]

        if (
            prev.section_id == seg.section_id
            and prev.start_id == seg.start_id
            and prev.end_id == seg.end_id
            and prev.is_tapered == seg.is_tapered
            and is_close(prev.x_end, seg.x_start, tol)
        ):
            merged[-1] = SpanSegmentResult(
                x_start=prev.x_start,
                x_end=seg.x_end,
                segment_index=prev.segment_index,
                section_id=prev.section_id,
                start_id=prev.start_id,
                end_id=prev.end_id,
                is_tapered=prev.is_tapered,
            )
        else:
            merged.append(seg)

    for index, segment in enumerate(merged):
        segment.segment_index = index

    return merged, current_section_id
