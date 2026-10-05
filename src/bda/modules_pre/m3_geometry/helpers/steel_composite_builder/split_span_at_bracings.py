from collections import defaultdict
from typing import Dict, List, Tuple

from pint.registry import Quantity

from bda.domain.models.submodels import Element1D



def split_span_at_bracings(
    bracings: Dict[Tuple[int, int], List[Element1D]],
) -> Dict[int, List[Quantity]]:

    points_at_girders: Dict[int, List[Quantity]] = defaultdict(list)

    for (idx_gi, idx_gj), b_elements in bracings.items():
        points_at_girders[idx_gi].extend(e.node_start.X for e in b_elements)
        points_at_girders[idx_gj].extend(e.node_end.X for e in b_elements)

    sort_key = lambda p: p.to_base_units().magnitude

    for idx, points in points_at_girders.items():
        points_at_girders[idx] = sorted(set(points_at_girders[idx]), key=sort_key)

    return points_at_girders