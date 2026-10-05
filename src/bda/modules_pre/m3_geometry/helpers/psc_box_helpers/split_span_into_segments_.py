from dataclasses import dataclass, field
from typing import List, Optional
from uuid import UUID

from pint.registry import Quantity

from bda.domain.models.submodels.geometry_group_props.shared import TaperedDetails



@dataclass
class SpanSegmentResult:
    segment_index: int
    x_start: Quantity
    x_end: Quantity
    section_id: Optional[UUID]


def _q_to_float(q: Quantity) -> float:
    """Convert Quantity to float in base units."""
    return q.to_base_units().magnitude

def _float_to_q(value: float, template: Quantity) -> Quantity:
    """Convert float back to Quantity with same units as template."""
    return template.__class__(value, template.units)

def _is_close(a: float, b: float, tol: float) -> bool:
    """Float comparison with tolerance."""
    return abs(a - b) <= tol


def split_span_into_segments(
    span_length: Quantity,
    tapered_details: Optional[List[TaperedDetails]] = None,
    tolerance: Optional[Quantity] = None,
) -> List[SpanSegmentResult]:
    """
    Split span into segments with tapered sections.

    Supports tolerance and merging of adjacent segments.
    """

    tol = _q_to_float(tolerance) if tolerance else 0.001

    span_len_f = _q_to_float(span_length)

    # ---- STEP 1: collect split points ----
    split_points = {0.0, span_len_f}

    if tapered_details:
        for seg in tapered_details:
            split_points.add(_q_to_float(seg.x_start))
            split_points.add(_q_to_float(seg.x_end))

    # ---- STEP 2: sort & deduplicate with tolerance ----
    sorted_points = sorted(split_points)

    filtered_points = []
    for p in sorted_points:
        if not filtered_points:
            filtered_points.append(p)
        elif not _is_close(p, filtered_points[-1], tol):
            filtered_points.append(p)

    # ---- STEP 3: create raw segments ----
    raw_segments: List[SpanSegmentResult] = []

    segment_index = 0

    for i in range(len(filtered_points) - 1):
        x0 = filtered_points[i]
        x1 = filtered_points[i + 1]

        if _is_close(x0, x1, tol):
            continue

        mid = (x0 + x1) / 2.0

        # ---- tapered sections ----
        segment_section_id = None
        if tapered_details:
            for seg in tapered_details:
                start = _q_to_float(seg.x_start)
                end = _q_to_float(seg.x_end)

                if (start - tol) <= mid <= (end + tol):
                    segment_section_id = seg.section_id
                    break

        raw_segments.append(
            SpanSegmentResult(
                x_start=_float_to_q(x0, span_length),
                x_end=_float_to_q(x1, span_length),
                segment_index=segment_index,
                section_id=segment_section_id,
            )
        )
        segment_index += 1

    # ---- STEP 4: merge adjacent segments ----
    merged: List[SpanSegmentResult] = []

    for seg in raw_segments:
        if not merged:
            merged.append(seg)
            continue

        prev = merged[-1]

        # check if properties identical and boundaries match (with tolerance)
        if (
            prev.section_id == seg.section_id
            and _is_close(
                _q_to_float(prev.x_end),
                _q_to_float(seg.x_start),
                tol,
            )
        ):
            # merge
            merged[-1] = SpanSegmentResult(
                x_start=prev.x_start,
                x_end=seg.x_end,
                segment_index=prev.segment_index,
                section_id=prev.section_id,
            )
        else:
            merged.append(seg)

    return merged