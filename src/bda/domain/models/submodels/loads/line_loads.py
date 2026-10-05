"""Distributed line loads applied to beam elements.

NOTE: do not add ``from __future__ import annotations`` to modules in this
package (see ``load_components.py``).
"""
from dataclasses import dataclass, field

from bda.domain.enums.load_enums import LoadTargetType
from bda.domain.models.submodels.element import Element1D
from bda.domain.models.submodels.loads.load_base import LineLoadElementBase
from bda.domain.models.submodels.loads.load_components import LoadOffset
from bda.domain.models.submodels.loads.point_loads import _validate_beam_element, _validate_offset


@dataclass(kw_only=True, repr=False)
class BeamLineLoad(LineLoadElementBase):
    """Uniformly distributed load acting along the whole length of a beam element.

    Attributes:
        element (Element1D): Beam element the load acts on (links are rejected).
        offset (LoadOffset | None): Optional eccentricity in the element's
            local ``y`` or ``z`` axis.
    """

    target_type: LoadTargetType = field(default=LoadTargetType.BEAM, init=False)
    element: Element1D
    offset: LoadOffset | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        _validate_beam_element(self.element)
        _validate_offset(self.offset)

    @property
    def target(self) -> Element1D:
        return self.element
