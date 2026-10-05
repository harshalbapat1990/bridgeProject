"""Loads - container of load cases and FE-level loads owned by the multimodel.

NOTE: do not add ``from __future__ import annotations`` to modules in this
package (see ``load_components.py``).
"""
from dataclasses import dataclass, field

from bda.domain.models.submodels.loads.static_loads import StaticLoads


@dataclass
class Loads:
    """Container for all load cases and loads of an ``AnalyticalMultiModel``.

    Follows the ``AnalyticalTypology`` pattern: private lists, read-only tuple
    views and explicit ``add_*`` mutators. The container owns id assignment:
    ``LoadCase.model_id`` and ``LoadBase.load_id`` are set on registration and
    each form a single increasing sequence (``load_id`` is shared across point,
    line and area loads).

    Rules enforced on registration:
        - load case names are unique (exact, case-sensitive match),
        - a load may only be added if its load case is already registered,
        - objects are deduplicated by ``guid``.

    The container does not verify that a load's node/element belongs to the
    multimodel's geometry; it has no knowledge of the topology.
    """

    static: StaticLoads = field(default_factory=StaticLoads)