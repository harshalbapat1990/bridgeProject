from __future__ import annotations

from typing import Iterable

from bda.domain.models.submodels import Element1D
from bda.domain.models.submodels.geometry_group import GeometryGroup


def resolve_connected_deck_segment_for_edge_element(
    builder,
    element: Element1D,
    segments: Iterable[GeometryGroup],
) -> GeometryGroup:
    segments = list(segments)
    if not segments:
        raise ValueError("No deck segments provided for edge-beam assignment.")

    node_end = element.node_end

    # Classify by edge-element end node, so boundary membership follows
    # the transverse strip element that reaches this edge node.
    for segment in segments:
        for seg_element in segment.analytical_typology.elements:
            if not isinstance(seg_element, Element1D):
                continue
            if seg_element.node_start == node_end or seg_element.node_end == node_end:
                return segment

    # Keep previous fallback behavior when no connectivity match is found.
    return segments[-1]

